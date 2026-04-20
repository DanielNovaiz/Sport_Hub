"""Gestão de temporadas, rank sazonal, milestones e recompensas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import calendar
from contextlib import nullcontext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stats import UserAchievement
from app.models.season import Season, SeasonMilestone, SeasonRank, SeasonRewardGrant
from app.services.profile_cache_service import invalidate_user_profile_cache

SEASON_START_ANCHOR = datetime(2026, 4, 1, tzinfo=UTC)
SEASON_DURATION_MONTHS = 3
SEASON_XP_PER_LEVEL = 100
WEEKEND_MULTIPLIER_DAY = 5  # Saturday
WEEKEND_MULTIPLIER_VALUE = 2.0
ELITE_BADGE_TIER = "Gold"
ELITE_BADGE_SUFFIX = "Elite"

COSMETIC_FRAME_REWARD = "cosmetic_frame"
WEEKEND_XP_REWARD = "weekend_multiplier"


@dataclass(frozen=True)
class SeasonMilestoneGrantResult:
    milestone_id: str
    required_level: int
    reward_kind: str
    frame_code: str | None
    xp_multiplier: float
    activation_at: datetime | None
    expires_at: datetime | None


@dataclass(frozen=True)
class SeasonProgressResult:
    season_code: str
    season_level: int
    season_xp_total: int
    frame_code: str | None
    unlocked_rewards: list[SeasonMilestoneGrantResult]
    active_weekend_multiplier: float


@dataclass(frozen=True)
class SeasonSnapshot:
    season_code: str | None
    season_level: int
    season_xp_total: int
    frame_code: str | None
    badges: list[str]
    active_weekend_multiplier: float


def _add_months(source: datetime, months: int) -> datetime:
    month_index = source.month - 1 + months
    year = source.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source.day, calendar.monthrange(year, month)[1])
    return source.replace(year=year, month=month, day=day)


def _season_window_for(now: datetime) -> tuple[str, datetime, datetime]:
    safe_now = now.astimezone(UTC)
    total_months = (safe_now.year - SEASON_START_ANCHOR.year) * 12 + (safe_now.month - SEASON_START_ANCHOR.month)
    season_index = max(0, total_months // SEASON_DURATION_MONTHS)
    starts_at = _add_months(SEASON_START_ANCHOR, season_index * SEASON_DURATION_MONTHS)
    ends_at = _add_months(starts_at, SEASON_DURATION_MONTHS)
    season_code = f"S{season_index + 1:02d}"
    return season_code, starts_at, ends_at


def _next_saturday_window(now: datetime) -> tuple[datetime, datetime]:
    safe_now = now.astimezone(UTC)
    days_until_saturday = WEEKEND_MULTIPLIER_DAY - safe_now.weekday()
    if days_until_saturday <= 0:
        days_until_saturday += 7
    saturday_start = datetime(
        year=safe_now.year,
        month=safe_now.month,
        day=safe_now.day,
        tzinfo=UTC,
    ) + timedelta(days=days_until_saturday)
    saturday_start = saturday_start.replace(hour=0, minute=0, second=0, microsecond=0)
    saturday_end = saturday_start + timedelta(days=1) - timedelta(microseconds=1)
    return saturday_start, saturday_end


async def _seed_default_milestones(session: AsyncSession, season: Season) -> None:
    query = select(SeasonMilestone).where(SeasonMilestone.season_id == season.id)
    result = await session.execute(query)
    existing = result.scalars().all()
    existing_levels = {milestone.required_level for milestone in existing}

    defaults = [
        SeasonMilestone(
            season_id=season.id,
            required_level=10,
            reward_kind=COSMETIC_FRAME_REWARD,
            frame_code=f"{season.code.lower()}_frame_10",
            xp_multiplier=1.0,
            title=f"{season.code} Frame 10",
            description="Desbloqueia uma moldura sazonal de card.",
        ),
        SeasonMilestone(
            season_id=season.id,
            required_level=20,
            reward_kind=WEEKEND_XP_REWARD,
            frame_code=None,
            xp_multiplier=WEEKEND_MULTIPLIER_VALUE,
            title=f"{season.code} Weekend Boost",
            description="Desbloqueia 2x XP no próximo sábado.",
        ),
    ]

    to_create = [milestone for milestone in defaults if milestone.required_level not in existing_levels]
    if to_create:
        session.add_all(to_create)
        await session.flush()


async def get_current_season(session: AsyncSession, now: datetime | None = None) -> Season:
    """Retorna a temporada ativa, criando-a sob demanda."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    await finalize_overdue_seasons(session, reference_now)

    code, starts_at, ends_at = _season_window_for(reference_now)
    query = select(Season).where(Season.code == code)
    result = await session.execute(query)
    season = result.scalars().first()

    if not season:
        season = Season(code=code, starts_at=starts_at, ends_at=ends_at, status="active")
        session.add(season)
        await session.flush()

    if season.status != "active":
        season.status = "active"
        season.starts_at = starts_at
        season.ends_at = ends_at
        season.updated_at = reference_now

    await _seed_default_milestones(session, season)
    return season


async def get_or_create_season_rank(
    session: AsyncSession,
    user_id: str,
    season: Season | None = None,
    now: datetime | None = None,
) -> SeasonRank:
    active_season = season or await get_current_season(session, now=now)
    query = select(SeasonRank).where(
        SeasonRank.season_id == active_season.id,
        SeasonRank.user_id == user_id,
    )
    result = await session.execute(query)
    rank = result.scalars().first()

    if not rank:
        rank = SeasonRank(season_id=active_season.id, user_id=user_id)
        session.add(rank)
        await session.flush()

    return rank


async def get_active_xp_multiplier(
    session: AsyncSession,
    user_id: str,
    now: datetime | None = None,
) -> float:
    """Retorna o maior multiplicador sazonal ativo para o usuário."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    season = await get_current_season(session, now=reference_now)

    query = select(SeasonRewardGrant).where(
        SeasonRewardGrant.season_id == season.id,
        SeasonRewardGrant.user_id == user_id,
        SeasonRewardGrant.claimed_at.is_not(None),
    )
    result = await session.execute(query)
    grants = result.scalars().all()

    active_multipliers: list[float] = []
    for grant in grants:
        if grant.reward_kind != WEEKEND_XP_REWARD:
            continue
        if grant.activation_at and grant.activation_at > reference_now:
            continue
        if grant.expires_at and grant.expires_at < reference_now:
            continue
        active_multipliers.append(float(grant.xp_multiplier or 1.0))

    return max(active_multipliers, default=1.0)


async def _grant_milestone(
    session: AsyncSession,
    season: Season,
    rank: SeasonRank,
    milestone: SeasonMilestone,
    now: datetime,
) -> SeasonMilestoneGrantResult | None:
    existing_query = select(SeasonRewardGrant).where(
        SeasonRewardGrant.season_id == season.id,
        SeasonRewardGrant.user_id == rank.user_id,
        SeasonRewardGrant.milestone_id == milestone.id,
    )
    existing_result = await session.execute(existing_query)
    existing = existing_result.scalars().first()
    if existing:
        return None

    activation_at = None
    expires_at = None
    if milestone.reward_kind == WEEKEND_XP_REWARD:
        activation_at, expires_at = _next_saturday_window(now)

    grant = SeasonRewardGrant(
        season_id=season.id,
        user_id=rank.user_id,
        milestone_id=milestone.id,
        reward_kind=milestone.reward_kind,
        frame_code=milestone.frame_code,
        xp_multiplier=milestone.xp_multiplier,
        activation_at=activation_at,
        expires_at=expires_at,
        claimed_at=now,
    )
    session.add(grant)
    await session.flush()

    return SeasonMilestoneGrantResult(
        milestone_id=milestone.id,
        required_level=milestone.required_level,
        reward_kind=milestone.reward_kind,
        frame_code=milestone.frame_code,
        xp_multiplier=milestone.xp_multiplier,
        activation_at=activation_at,
        expires_at=expires_at,
    )


async def award_season_progress(
    session: AsyncSession,
    *,
    user_id: str,
    xp_gained: int,
    won_match: bool,
    now: datetime | None = None,
) -> SeasonProgressResult:
    """Atualiza XP sazonal e concede milestones automaticamente."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    season = await get_current_season(session, now=reference_now)
    rank = await get_or_create_season_rank(session, user_id, season=season, now=reference_now)

    gained_xp = max(0, int(xp_gained))
    rank.xp_total += gained_xp
    rank.level = rank.xp_total // SEASON_XP_PER_LEVEL
    rank.matches_played += 1
    if won_match:
        rank.wins += 1
    else:
        rank.losses += 1
    rank.last_match_at = reference_now
    rank.updated_at = reference_now

    milestones_query = select(SeasonMilestone).where(SeasonMilestone.season_id == season.id)
    milestones_result = await session.execute(milestones_query)
    milestones = milestones_result.scalars().all()

    unlocked_rewards: list[SeasonMilestoneGrantResult] = []
    for milestone in sorted(milestones, key=lambda item: item.required_level):
        if rank.level < milestone.required_level:
            continue
        grant = await _grant_milestone(session, season, rank, milestone, reference_now)
        if grant:
            unlocked_rewards.append(grant)

    active_weekend_multiplier = await get_active_xp_multiplier(session, user_id, now=reference_now)
    frame_code = await get_current_frame_code(session, user_id, season=season)

    return SeasonProgressResult(
        season_code=season.code,
        season_level=rank.level,
        season_xp_total=rank.xp_total,
        frame_code=frame_code,
        unlocked_rewards=unlocked_rewards,
        active_weekend_multiplier=active_weekend_multiplier,
    )


async def get_current_frame_code(
    session: AsyncSession,
    user_id: str,
    season: Season | None = None,
) -> str | None:
    active_season = season or await get_current_season(session)
    query = select(SeasonRewardGrant).where(
        SeasonRewardGrant.season_id == active_season.id,
        SeasonRewardGrant.user_id == user_id,
        SeasonRewardGrant.reward_kind == COSMETIC_FRAME_REWARD,
        SeasonRewardGrant.frame_code.is_not(None),
    ).order_by(SeasonRewardGrant.created_at.desc())
    result = await session.execute(query)
    grant = result.scalars().first()
    return grant.frame_code if grant else None


async def get_user_season_snapshot(
    session: AsyncSession,
    user_id: str,
    now: datetime | None = None,
) -> SeasonSnapshot:
    """Retorna resumo sazonal para o card de perfil."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    season = await get_current_season(session, now=reference_now)
    rank = await get_or_create_season_rank(session, user_id, season=season, now=reference_now)
    frame_code = await get_current_frame_code(session, user_id, season=season)

    badges: list[str] = []
    elite_query = select(UserAchievement.id).where(
        UserAchievement.user_id == user_id,
        UserAchievement.code == f"{season.code.lower()}_elite",
    )
    elite_result = await session.execute(elite_query)
    if elite_result.first() is not None:
        badges.append(f"{season.code} Elite")

    if frame_code:
        badges.append(frame_code)

    active_weekend_multiplier = await get_active_xp_multiplier(session, user_id, now=reference_now)

    return SeasonSnapshot(
        season_code=season.code,
        season_level=rank.level,
        season_xp_total=rank.xp_total,
        frame_code=frame_code,
        badges=badges,
        active_weekend_multiplier=active_weekend_multiplier,
    )


async def grant_season_completion_badge(
    session: AsyncSession,
    *,
    season: Season,
    user_id: str,
    now: datetime | None = None,
) -> UserAchievement | None:
    """Gera badge histórica de fim de temporada sem resetar overall."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    code = f"{season.code.lower()}_elite"
    query = select(UserAchievement).where(
        UserAchievement.user_id == user_id,
        UserAchievement.code == code,
    )
    result = await session.execute(query)
    existing = result.scalars().first()
    if existing:
        return existing

    achievement = UserAchievement(
        user_id=user_id,
        code=code,
        title=f"{season.code} {ELITE_BADGE_SUFFIX}",
        tier=ELITE_BADGE_TIER,
        execution_count=1,
        bonus_attribute=None,
        bonus_value=0,
        last_triggered_at=reference_now,
    )
    session.add(achievement)
    await session.flush()
    return achievement


async def finalize_season(session: AsyncSession, season: Season, now: datetime | None = None) -> None:
    """Fecha uma temporada e distribui badge histórica aos participantes."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    if season.status == "closed":
        return

    transaction = nullcontext() if session.in_transaction() else session.begin()
    async with transaction:
        ranks_query = select(SeasonRank).where(SeasonRank.season_id == season.id)
        ranks_result = await session.execute(ranks_query)
        ranks = ranks_result.scalars().all()

        for rank in ranks:
            if rank.matches_played <= 0 and rank.xp_total <= 0:
                continue
            await grant_season_completion_badge(session, season=season, user_id=rank.user_id, now=reference_now)

        season.status = "closed"
        season.updated_at = reference_now

    if not session.in_transaction():
        for rank in ranks:
            if rank.matches_played <= 0 and rank.xp_total <= 0:
                continue
            await invalidate_user_profile_cache(rank.user_id)


async def finalize_overdue_seasons(session: AsyncSession, now: datetime | None = None) -> None:
    """Fecha temporadas expiradas em ordem cronológica."""
    reference_now = (now or datetime.now(UTC)).astimezone(UTC)
    query = select(Season).where(Season.ends_at <= reference_now, Season.status == "active").order_by(Season.ends_at.asc())
    result = await session.execute(query)
    overdue_seasons = result.scalars().all()

    for season in overdue_seasons:
        await finalize_season(session, season, now=reference_now)