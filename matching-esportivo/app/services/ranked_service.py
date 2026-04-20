"""Serviço de ranked e MMR."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from geoalchemy2 import Geography
from sqlalchemy import and_, cast, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.player_stats import MatchPerformance
from app.models.user import User, UserInterest
from app.models.player_stats import PlayerStats
from app.models.ranked import UserRank
from app.schemas.ranked import AchievementRead, BoxScoreCreate, BoxScoreResultRead, RankedUserRead, UserRankRead
from app.services.club_service import has_high_synergy, upsert_team_synergy
from app.services.profile_cache_service import invalidate_user_profile_cache
from app.services.season_manager import award_season_progress, get_active_xp_multiplier
from app.repositories import StructuredTelemetryRepository
from app.services.xp_service import apply_match_progression

DEFAULT_REGIONAL_CITY = "Goiânia"
DEFAULT_REGIONAL_RADIUS_KM = 60.0
SYNERGY_XP_MULTIPLIER = 1.05

_CITY_CENTERS: dict[str, tuple[float, float]] = {
    "goiania": (-49.2643, -16.6864),
    "goiânia": (-49.2643, -16.6864),
}


def calculate_mmr_change(
    winner: bool,
    winner_overall: int,
    winner_mmr: int,
    loser_mmr: int,
    base_mmr: int = 25,
) -> int:
    """Input: match result + overalls. Output: MMR delta (signed).
    
    Overall acts as multiplier: higher overall = more MMR gain/loss.
    Uses ELO-style calculation with k-factor adjusted by player overall.
    """
    # K-factor scales with overall: baseline 32 at overall=75
    baseline_overall = 75
    k_factor = 32 * (winner_overall / baseline_overall)
    k_factor = max(16, min(64, k_factor))  # Bound between 16-64
    
    mmr_diff = winner_mmr - loser_mmr
    expected_win_prob = 1.0 / (1.0 + 10 ** (mmr_diff / 400.0))

    if winner:
        mmr_delta = int(k_factor * (1.0 - expected_win_prob))
    else:
        mmr_delta = int(k_factor * (0.0 - expected_win_prob))

    return max(-100, min(100, mmr_delta))


async def get_or_create_user_rank(session: AsyncSession, user_id: str) -> UserRank:
    """Input: user_id. Output: UserRank (existing or newly created)."""
    query = select(UserRank).where(UserRank.user_id == user_id)
    result = await session.execute(query)
    rank = result.scalars().first()

    if not rank:
        rank = UserRank(user_id=user_id)
        session.add(rank)
        await session.commit()
        await session.refresh(rank)

    return rank


def _build_achievements(
    *,
    wins: int,
    week_goals: int,
    month_impact: int,
    win_rate: float,
) -> list[AchievementRead]:
    achievements: list[AchievementRead] = []

    if wins >= 10:
        achievements.append(
            AchievementRead(
                code="WINS_10",
                title="10 Vitórias",
                description="Conquistou 10 vitórias em partidas ranqueadas.",
                icon="emoji_events_rounded",
                rarity="common",
                progress=wins,
                target=10,
            )
        )

    if week_goals >= 7:
        achievements.append(
            AchievementRead(
                code="TOP_SCORER_WEEK",
                title="Artilheiro da Semana",
                description="Marcou 7+ gols nos últimos 7 dias.",
                icon="sports_soccer_rounded",
                rarity="rare",
                progress=week_goals,
                target=7,
            )
        )

    if month_impact >= 25 and win_rate >= 65:
        achievements.append(
            AchievementRead(
                code="MVP_MONTH",
                title="MVP do Mês",
                description="Alto impacto no mês com performance dominante.",
                icon="workspace_premium_rounded",
                rarity="legendary",
                progress=month_impact,
                target=25,
            )
        )

    return achievements


async def _get_user_performance_window(
    session: AsyncSession,
    user_id: str,
) -> tuple[int, int]:
    now = datetime.now(UTC)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    week_goals_query = select(func.coalesce(func.sum(MatchPerformance.goals), 0)).where(
        MatchPerformance.user_id == user_id,
        MatchPerformance.created_at >= week_start,
    )
    week_goals_result = await session.execute(week_goals_query)
    week_goals = int(week_goals_result.scalar_one() or 0)

    month_impact_query = select(
        func.coalesce(
            func.sum(
                MatchPerformance.goals + MatchPerformance.assists + MatchPerformance.points + MatchPerformance.rebounds
            ),
            0,
        )
    ).where(
        MatchPerformance.user_id == user_id,
        MatchPerformance.created_at >= month_start,
    )
    month_impact_result = await session.execute(month_impact_query)
    month_impact = int(month_impact_result.scalar_one() or 0)

    return week_goals, month_impact


async def get_user_rank_read(session: AsyncSession, user_id: str) -> UserRankRead:
    rank = await get_or_create_user_rank(session, user_id)
    week_goals, month_impact = await _get_user_performance_window(session, user_id)
    achievements = _build_achievements(
        wins=rank.wins,
        week_goals=week_goals,
        month_impact=month_impact,
        win_rate=rank.win_rate,
    )

    return UserRankRead(
        id=rank.id,
        user_id=rank.user_id,
        mmr=rank.mmr,
        division=rank.division,
        league=rank.league,
        wins=rank.wins,
        losses=rank.losses,
        win_rate=rank.win_rate,
        achievements=achievements,
        created_at=rank.created_at,
        updated_at=rank.updated_at,
    )


async def update_rank_after_match(
    session: AsyncSession,
    winner_id: str,
    loser_id: str,
) -> tuple[UserRankRead, UserRankRead]:
    """Input: winner/loser IDs. Output: updated ranks.
    
    FASE 2: Auditoria de Concorrência
    - Usa lock pessimista (SELECT FOR UPDATE) em ambos os ranks
    - Evita lost updates se múltiplos matches ocorrem simultaneamente
    - Garante MMR consistency
    """
    # 1. Adquirir lock pessimista em ambos os ranks (ordem fixa para evitar deadlock)
    # Ordena IDs para manter consistência de lock order
    if winner_id <= loser_id:
        first_id, second_id = winner_id, loser_id
    else:
        first_id, second_id = loser_id, winner_id
    
    await get_or_create_user_rank(session, winner_id)
    await get_or_create_user_rank(session, loser_id)
    
    # Refresh with lock
    query_winner = select(UserRank).where(
        UserRank.user_id == first_id
    ).with_for_update()
    result_winner = await session.execute(query_winner)
    winner_rank_locked = result_winner.scalars().one()
    
    query_loser = select(UserRank).where(
        UserRank.user_id == second_id
    ).with_for_update()
    result_loser = await session.execute(query_loser)
    loser_rank_locked = result_loser.scalars().one()

    # Swap references if needed
    if winner_rank_locked.user_id == loser_id:
        winner_rank_locked, loser_rank_locked = loser_rank_locked, winner_rank_locked

    # 2. Calcular MMR delta
    winner_stats = await session.get(PlayerStats, winner_id)
    if not winner_stats:
        winner_stats = PlayerStats(user_id=winner_id, overall=50)

    winner_mmr_delta = calculate_mmr_change(
        winner=True,
        winner_overall=winner_stats.overall,
        winner_mmr=winner_rank_locked.mmr,
        loser_mmr=loser_rank_locked.mmr,
    )

    loser_mmr_delta = -winner_mmr_delta

    # 3. Atualizar ranks (dentro do lock)
    winner_rank_locked.mmr = max(0, winner_rank_locked.mmr + winner_mmr_delta)
    winner_rank_locked.wins += 1
    loser_rank_locked.mmr = max(0, loser_rank_locked.mmr + loser_mmr_delta)
    loser_rank_locked.losses += 1

    total_matches_winner = winner_rank_locked.wins + winner_rank_locked.losses
    total_matches_loser = loser_rank_locked.wins + loser_rank_locked.losses

    winner_rank_locked.win_rate = (winner_rank_locked.wins / total_matches_winner * 100.0) if total_matches_winner > 0 else 0.0
    loser_rank_locked.win_rate = (loser_rank_locked.wins / total_matches_loser * 100.0) if total_matches_loser > 0 else 0.0

    # 4. Commit libera os locks
    await session.commit()
    await session.refresh(winner_rank_locked)
    await session.refresh(loser_rank_locked)

    return (
        UserRankRead.model_validate(winner_rank_locked),
        UserRankRead.model_validate(loser_rank_locked),
    )


async def list_ranked_users(
    session: AsyncSession,
    sport_type: str | None = None,
    limit: int = 100,
) -> list[RankedUserRead]:
    """Input: optional sport filter. Output: ranking list ordered by MMR."""
    primary_sport_subquery = (
        select(
            UserInterest.user_id.label("user_id"),
            UserInterest.sport.label("sport_type"),
        )
        .where(UserInterest.is_primary.is_(True))
        .subquery()
    )

    now = datetime.now(UTC)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    week_goals_subquery = (
        select(
            MatchPerformance.user_id.label("user_id"),
            func.coalesce(func.sum(MatchPerformance.goals), 0).label("week_goals"),
        )
        .where(MatchPerformance.created_at >= week_start)
        .group_by(MatchPerformance.user_id)
        .subquery()
    )

    month_impact_subquery = (
        select(
            MatchPerformance.user_id.label("user_id"),
            func.coalesce(
                func.sum(
                    MatchPerformance.goals
                    + MatchPerformance.assists
                    + MatchPerformance.points
                    + MatchPerformance.rebounds
                ),
                0,
            ).label("month_impact"),
        )
        .where(MatchPerformance.created_at >= month_start)
        .group_by(MatchPerformance.user_id)
        .subquery()
    )

    query = (
        select(
            UserRank,
            User.full_name,
            User.username,
            User.avatar_url,
            primary_sport_subquery.c.sport_type,
            PlayerStats.position,
            PlayerStats.overall,
            week_goals_subquery.c.week_goals,
            month_impact_subquery.c.month_impact,
        )
        .join(User, User.id == UserRank.user_id)
        .outerjoin(PlayerStats, PlayerStats.user_id == UserRank.user_id)
        .outerjoin(primary_sport_subquery, primary_sport_subquery.c.user_id == UserRank.user_id)
        .outerjoin(week_goals_subquery, week_goals_subquery.c.user_id == UserRank.user_id)
        .outerjoin(month_impact_subquery, month_impact_subquery.c.user_id == UserRank.user_id)
        .order_by(UserRank.mmr.desc(), UserRank.win_rate.desc(), UserRank.wins.desc())
        .limit(limit)
    )

    if sport_type and sport_type.lower() != "geral":
        sport_filter = sport_type.lower()
        query = query.where(
            exists(
                select(UserInterest.id).where(
                    and_(
                        UserInterest.user_id == UserRank.user_id,
                        func.lower(UserInterest.sport) == sport_filter,
                    )
                )
            )
        )

    result = await session.execute(query)
    rows = result.all()

    return [
        RankedUserRead(
            id=rank.id,
            user_id=rank.user_id,
            full_name=full_name,
            username=username,
            avatar_url=avatar_url,
            mmr=rank.mmr,
            division=rank.division,
            league=rank.league,
            wins=rank.wins,
            losses=rank.losses,
            win_rate=rank.win_rate,
            achievements=_build_achievements(
                wins=rank.wins,
                week_goals=int(week_goals or 0),
                month_impact=int(month_impact or 0),
                win_rate=rank.win_rate,
            ),
            sport_type=sport_type_value,
            position=position,
            overall=overall,
            created_at=rank.created_at,
            updated_at=rank.updated_at,
        )
        for rank, full_name, username, avatar_url, sport_type_value, position, overall, week_goals, month_impact in rows
    ]


def _normalize_city_key(city: str | None) -> str:
    normalized = (city or DEFAULT_REGIONAL_CITY).strip().lower()
    return normalized or DEFAULT_REGIONAL_CITY.lower()


def _resolve_city_center(city: str | None) -> tuple[str, tuple[float, float]]:
    normalized_city = _normalize_city_key(city)
    if normalized_city in _CITY_CENTERS:
        return normalized_city, _CITY_CENTERS[normalized_city]
    return _normalize_city_key(DEFAULT_REGIONAL_CITY), _CITY_CENTERS[_normalize_city_key(DEFAULT_REGIONAL_CITY)]


async def list_regional_ranked_users(
    session: AsyncSession,
    *,
    city: str = DEFAULT_REGIONAL_CITY,
    sport: str | None = None,
    position: str | None = None,
    limit: int = 50,
) -> list[RankedUserRead]:
    """Top jogadores regionais ordenados por overall (cap 50)."""
    resolved_limit = max(1, min(int(limit), 50))
    normalized_city, (longitude, latitude) = _resolve_city_center(city)
    reference_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

    primary_sport_subquery = (
        select(
            UserInterest.user_id.label("user_id"),
            UserInterest.sport.label("sport_type"),
        )
        .where(UserInterest.is_primary.is_(True))
        .subquery()
    )

    query = (
        select(
            UserRank,
            User.full_name,
            User.username,
            User.avatar_url,
            primary_sport_subquery.c.sport_type,
            PlayerStats.position,
            PlayerStats.overall.label("overall_score"),
        )
        .join(User, User.id == UserRank.user_id)
        .join(PlayerStats, PlayerStats.user_id == UserRank.user_id)
        .outerjoin(primary_sport_subquery, primary_sport_subquery.c.user_id == UserRank.user_id)
        .where(User.location.is_not(None))
        .where(
            func.ST_DWithin(
                cast(User.location, Geography),
                cast(reference_point, Geography),
                DEFAULT_REGIONAL_RADIUS_KM * 1000.0,
            )
        )
        .order_by(PlayerStats.overall.desc(), UserRank.mmr.desc())
        .limit(resolved_limit)
    )

    if sport and sport.strip():
        normalized_sport = sport.strip().lower()
        query = query.where(
            exists(
                select(UserInterest.id).where(
                    and_(
                        UserInterest.user_id == UserRank.user_id,
                        func.lower(UserInterest.sport) == normalized_sport,
                    )
                )
            )
        )

    if position and position.strip():
        normalized_position = position.strip().lower()
        query = query.where(func.lower(PlayerStats.position) == normalized_position)

    result = await session.execute(query)
    rows = result.all()

    return [
        RankedUserRead(
            id=rank.id,
            user_id=rank.user_id,
            full_name=full_name,
            username=username,
            avatar_url=avatar_url,
            mmr=rank.mmr,
            division=rank.division,
            league=rank.league,
            wins=rank.wins,
            losses=rank.losses,
            win_rate=rank.win_rate,
            achievements=[],
            sport_type=sport_type_value,
            position=position_value,
            overall=overall_score,
            created_at=rank.created_at,
            updated_at=rank.updated_at,
        )
        for rank, full_name, username, avatar_url, sport_type_value, position_value, overall_score in rows
    ]


def _normalize_sport(sport_type: str) -> str:
    normalized = (sport_type or "").strip().lower()
    if normalized in {"futebol", "football"}:
        return "football"
    if normalized in {"volei", "vôlei", "volleyball"}:
        return "volleyball"
    if normalized in {"basquete", "basketball"}:
        return "basketball"
    return normalized or "football"


async def submit_box_score(session: AsyncSession, payload: BoxScoreCreate) -> BoxScoreResultRead:
    """Persistir box score e aplicar progressão de XP/conquistas automaticamente."""
    resolved_sport = _normalize_sport(payload.sport_type)
    resolved_sub_type = payload.sub_type
    resolved_club_id = payload.club_id

    if payload.event_id:
        event = await session.get(Event, payload.event_id)
        if not event:
            raise ValueError("event_not_found")
        resolved_sport = _normalize_sport(event.sport_type)
        resolved_sub_type = event.sub_type or resolved_sub_type
        resolved_club_id = event.club_id or resolved_club_id

    synergy_status: str | None = None
    synergy_visual_bonus = False
    xp_multiplier = 1.0
    season_code: str | None = None
    season_level = 0
    season_xp_total = 0
    season_frame: str | None = None

    telemetry_sink = StructuredTelemetryRepository()

    async with session.begin():
        stats_result = await session.execute(select(PlayerStats).where(PlayerStats.user_id == payload.user_id))
        stats = stats_result.scalars().first()
        if not stats:
            stats = PlayerStats(user_id=payload.user_id)
            session.add(stats)
            await session.flush()

        performance = MatchPerformance(
            user_id=payload.user_id,
            event_id=payload.event_id,
            sport_type=resolved_sport,
            sub_type=resolved_sub_type,
            team_score=payload.team_score,
            opponent_score=payload.opponent_score,
            goals=payload.goals,
            assists=payload.assists,
            tackles=payload.tackles,
            dribbles=payload.dribbles,
            aces=payload.aces,
            blocks=payload.blocks,
            attacks=payload.attacks,
            defenses=payload.defenses,
            sets=payload.sets,
            # Compatibilidade com motor já existente
            points=payload.attacks,
            steals=payload.tackles,
        )
        session.add(performance)
        await session.flush()

        season_multiplier = await get_active_xp_multiplier(session, payload.user_id)
        if resolved_club_id and payload.teammate_ids:
            won_match = payload.team_score > payload.opponent_score
            synergy = await upsert_team_synergy(
                session=session,
                club_id=resolved_club_id,
                user_id=payload.user_id,
                teammate_ids=payload.teammate_ids,
                won_match=won_match,
                sport_type=resolved_sport,
            )
            if synergy:
                synergy_status = synergy.status
                synergy_visual_bonus = has_high_synergy(synergy.status)
                if synergy_visual_bonus:
                    xp_multiplier *= SYNERGY_XP_MULTIPLIER

        xp_multiplier *= season_multiplier

        progression = await apply_match_progression(
            session=session,
            user_id=payload.user_id,
            performance=performance,
            stats=stats,
            xp_multiplier=xp_multiplier,
            telemetry_sink=telemetry_sink,
        )

        season_progress = await award_season_progress(
            session,
            user_id=payload.user_id,
            xp_gained=sum(progression["xp"].xp_gains.values()),
            won_match=payload.team_score > payload.opponent_score,
        )
        season_code = season_progress.season_code
        season_level = season_progress.season_level
        season_xp_total = season_progress.season_xp_total
        season_frame = season_progress.frame_code

        xp_result = progression["xp"]
        achievements = [achievement.title for achievement in progression["achievement_rows"]]

    await invalidate_user_profile_cache(payload.user_id)

    return BoxScoreResultRead(
        performance_id=performance.id,
        user_id=payload.user_id,
        event_id=payload.event_id,
        sport_type=resolved_sport,
        sub_type=resolved_sub_type,
        overall=progression["stats"].overall,
        level_gains_total=sum(xp_result.level_gains.values()),
        xp_gains=xp_result.xp_gains,
        triggered_achievements=achievements,
        telemetry_logs=progression.get("telemetry_logs", []),
        processing_ms=float(progression.get("processing_ms", 0.0) or 0.0),
        slow_processing=bool(progression.get("slow_processing", False)),
        synergy_status=synergy_status,
        synergy_visual_bonus=synergy_visual_bonus,
        xp_multiplier=xp_multiplier,
        season_code=season_code,
        season_level=season_level,
        season_xp_total=season_xp_total,
        season_frame=season_frame,
    )
