"""Serviço de usuários com operações CRUD e interesses."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.player_stats import PlayerStats
from app.models.player_stats import UserAchievement, UserXP
from app.models.user import User, UserInterest
from app.positions import normalize_position_input
from app.schemas.user import (
    UserAchievementRead,
    PlayerStatsRead,
    PlayerStatsUpdate,
    UserCreate,
    UserProfileCard,
    UserRead,
    UserXPRead,
    UserUpdate,
)
from app.services.xp_service import (
    ALL_PROGRESS_ATTRIBUTES,
    normalize_profile_sport_type,
)
from app.services.overall_engine import OverallRequest, calculate_overall_async
from app.services.maintenance_service import sync_user_prestige_entries
from app.services.club_service import list_user_synergy_badges
from app.services.profile_cache_service import get_cached_user_profile, set_cached_user_profile
from app.services.season_manager import get_user_season_snapshot

PLAYER_OVERALL_WEIGHTS: dict[str, dict[str, float]] = {
    "atacante": {
        "pace": 0.22,
        "shooting": 0.30,
        "passing": 0.12,
        "defense": 0.08,
        "physical": 0.16,
        "technique": 0.12,
    },
    "zagueiro": {
        "pace": 0.12,
        "shooting": 0.05,
        "passing": 0.13,
        "defense": 0.32,
        "physical": 0.28,
        "technique": 0.10,
    },
    "meia": {
        "pace": 0.16,
        "shooting": 0.15,
        "passing": 0.28,
        "defense": 0.12,
        "physical": 0.10,
        "technique": 0.19,
    },
    "ala": {
        "pace": 0.24,
        "shooting": 0.20,
        "passing": 0.16,
        "defense": 0.16,
        "physical": 0.12,
        "technique": 0.12,
    },
    "pivo": {
        "pace": 0.08,
        "shooting": 0.18,
        "passing": 0.10,
        "defense": 0.24,
        "physical": 0.30,
        "technique": 0.10,
    },
    "goleiro": {
        "pace": 0.08,
        "shooting": 0.02,
        "passing": 0.16,
        "defense": 0.34,
        "physical": 0.24,
        "technique": 0.16,
    },
    "default": {
        "pace": 1 / 6,
        "shooting": 1 / 6,
        "passing": 1 / 6,
        "defense": 1 / 6,
        "physical": 1 / 6,
        "technique": 1 / 6,
    },
}

ARCHETYPE_THRESHOLDS: tuple[tuple[str, str], ...] = (
    ("shooting", "Sharpshooter"),
    ("defense", "Lockdown Defender"),
    ("pace", "Speedster"),
)

ACHIEVEMENT_TIER_ORDER: dict[str, int] = {
    "Bronze": 0,
    "Silver": 1,
    "Gold": 2,
}


async def _load_user_with_interests(
    session: AsyncSession,
    user_id: str,
) -> User | None:
    """Input: session e user_id. Output: usuário com interesses carregados."""
    query = (
        select(User)
        .options(selectinload(User.interests))
        .where(User.id == user_id)
    )
    result = await session.execute(query)
    return result.scalars().first()


async def _get_player_stats_by_user_id(session: AsyncSession, user_id: str) -> PlayerStats | None:
    """Input: session e user_id. Output: PlayerStats atual do usuário ou None."""
    query = select(PlayerStats).where(PlayerStats.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().first()


async def _get_user_xp_rows(session: AsyncSession, user_id: str) -> list[UserXP]:
    """Input: user_id. Output: linhas de XP do usuário, criando defaults quando ausentes."""
    query = select(UserXP).where(UserXP.user_id == user_id)
    result = await session.execute(query)
    xp_rows = result.scalars().all()
    existing_attributes = {row.attribute_name for row in xp_rows}

    missing_rows = [
        UserXP(user_id=user_id, attribute_name=attribute_name)
        for attribute_name in ALL_PROGRESS_ATTRIBUTES
        if attribute_name not in existing_attributes
    ]

    if missing_rows:
        session.add_all(missing_rows)
        await session.flush()
        xp_rows.extend(missing_rows)

    xp_rows.sort(key=lambda row: ALL_PROGRESS_ATTRIBUTES.index(row.attribute_name) if row.attribute_name in ALL_PROGRESS_ATTRIBUTES else 999)
    return xp_rows


async def _get_user_achievements(session: AsyncSession, user_id: str) -> list[UserAchievement]:
    query = select(UserAchievement).where(UserAchievement.user_id == user_id)
    result = await session.execute(query)
    achievements = result.scalars().all()
    achievements.sort(key=lambda item: (ACHIEVEMENT_TIER_ORDER.get(item.tier, 99), item.execution_count, item.code))
    return achievements


def _get_primary_sport_type(user: User) -> str:
    primary_interest = next((interest for interest in user.interests if interest.is_primary), None)
    if not primary_interest and user.interests:
        primary_interest = user.interests[0]
    return normalize_profile_sport_type(primary_interest.sport if primary_interest else None)


def _active_xp_attributes(sport_type: str) -> tuple[str, ...]:
    if sport_type == "BASKETBALL":
        return (
            "shoot_long",
            "shoot_mid",
            "shoot_short",
            "finishing",
            "velocity",
            "jump",
            "agility",
            "energy",
            "strength",
            "balance",
            "passing",
            "ball_control",
            "vision",
            "dribble",
            "steal",
            "block",
            "perim_def",
            "post_def",
            "rebound",
            "reb_predict",
            "combativeness",
        )
    if sport_type == "VOLLEYBALL":
        return (
            "spike_power",
            "spike_accuracy",
            "serve_power",
            "serve_tactical",
            "block",
            "reception",
            "floor_defense",
            "coverage",
            "setting",
            "creativity",
            "game_vision",
            "jump",
            "lateral_agility",
            "reaction",
            "stamina",
            "coordination",
            "sand_agility",
            "jumping_endurance",
        )
    if sport_type == "FOOTBALL":
        return (
            "short_finish",
            "long_shot",
            "heading",
            "free_kick",
            "short_pass",
            "long_pass",
            "crossing",
            "vision",
            "dribbling",
            "ball_control",
            "agility",
            "balance",
            "tackle",
            "interception",
            "marking",
            "ball_shielding",
            "sprint",
            "acceleration",
            "stamina",
            "strength",
            "reflexes",
            "elasticity",
            "box_presence",
            "distribution",
        )
    return (
        "pace",
        "shooting",
        "passing",
        "defense",
        "physical",
        "technique",
    )


def _build_xp_summary(xp_rows: list[UserXP], sport_type: str) -> tuple[float, int, list[UserXP]]:
    active_attributes = set(_active_xp_attributes(sport_type))
    active_rows = [row for row in xp_rows if row.attribute_name in active_attributes]
    residual_total = sum(row.residual_xp for row in active_rows)
    progress_total = len(active_rows) * 60
    progress = (residual_total / progress_total) if progress_total else 0.0
    return progress, residual_total, active_rows


async def _calculate_overall_for_sport(sport_type: str, stats: PlayerStats) -> int:
    return await calculate_overall_async(
        request=OverallRequest(
            sport_type=sport_type,
            position=stats.position,
            sub_type=None,
        ),
        source=stats,
    )


def _normalize_position(position: str | None) -> str:
    """Input: posição livre. Output: posição normalizada para tabela de pesos."""
    if not position:
        return "default"
    normalized = position.strip().lower()
    aliases = {
        "striker": "atacante",
        "forward": "atacante",
        "defender": "zagueiro",
        "centerback": "zagueiro",
        "midfielder": "meia",
        "center_basket": "pivo",
        "wing": "ala",
        "winger": "ala",
        "center": "pivo",
        "pivot": "pivo",
        "goalkeeper": "goleiro",
        "keeper": "goleiro",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in PLAYER_OVERALL_WEIGHTS:
        return normalized
    return "default"


def calculate_player_overall(
    position: str,
    pace: int,
    shooting: int,
    passing: int,
    defense: int,
    physical: int,
    technique: int,
) -> int:
    """Input: posição e atributos [0-99]. Output: overall [0-99] por média ponderada."""
    weights = PLAYER_OVERALL_WEIGHTS[_normalize_position(position)]
    attributes = {
        "pace": pace,
        "shooting": shooting,
        "passing": passing,
        "defense": defense,
        "physical": physical,
        "technique": technique,
    }
    weighted_sum = sum(attributes[name] * weight for name, weight in weights.items())
    overall = int(round(weighted_sum))
    return max(0, min(99, overall))


def calculate_playstyle_archetype(
    pace: int,
    shooting: int,
    passing: int,
    defense: int,
    physical: int,
    technique: int,
) -> str:
    """Input: atributos [0-100]. Output: arquétipo principal baseado no maior atributo."""
    attrs = {
        "pace": pace,
        "shooting": shooting,
        "passing": passing,
        "defense": defense,
        "physical": physical,
        "technique": technique,
    }
    strongest_attr = max(attrs, key=attrs.get)
    strongest_value = attrs[strongest_attr]
    if strongest_value < 85:
        return "Balanced"

    threshold_map = dict(ARCHETYPE_THRESHOLDS)
    if strongest_attr in threshold_map:
        return threshold_map[strongest_attr]
    if strongest_attr in {"passing", "technique"}:
        return "Playmaker"
    if strongest_attr == "physical":
        return "Powerhouse"
    return "Balanced"


async def _assert_unique_email_username(
    session: AsyncSession,
    email: str,
    username: str,
    current_user_id: str | None = None,
) -> None:
    """Input: email/username. Output: None. Side effects: valida unicidade no banco."""
    query = select(User).where(or_(User.email == email, User.username == username))
    if current_user_id:
        query = query.where(User.id != current_user_id)
    result = await session.execute(query)
    existing_user = result.scalars().first()
    if existing_user:
        raise ValueError("email_or_username_already_exists")


async def create_user(session: AsyncSession, payload: UserCreate) -> UserRead:
    """Input: UserCreate. Output: UserRead. Side effects: insert em user e user_interest."""
    await _assert_unique_email_username(session, str(payload.email), payload.username)
    user = User(**payload.model_dump(exclude={"interests"}))
    session.add(user)
    await session.flush()
    interests = [
        UserInterest(user_id=user.id, **interest.model_dump())
        for interest in payload.interests
    ]
    if interests:
        session.add_all(interests)
    await session.commit()
    persisted_user = await _load_user_with_interests(session, user.id)
    if not persisted_user:
        raise ValueError("user_not_found_after_create")
    return UserRead.model_validate(persisted_user)


async def get_user_by_id(session: AsyncSession, user_id: str) -> UserRead | None:
    """Input: user_id. Output: UserRead ou None."""
    user = await _load_user_with_interests(session, user_id)
    if not user:
        return None
    return UserRead.model_validate(user)


async def list_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> list[UserRead]:
    """Input: paginação. Output: lista de UserRead."""
    query = select(User).options(selectinload(User.interests)).offset(skip).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()
    return [UserRead.model_validate(user) for user in users]


async def update_user(
    session: AsyncSession,
    user_id: str,
    payload: UserUpdate,
) -> UserRead | None:
    """Input: user_id e payload parcial. Output: UserRead atualizado ou None."""
    user = await _load_user_with_interests(session, user_id)
    if not user:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    interests_payload = update_data.pop("interests", None)
    target_email = update_data.get("email", user.email)
    target_username = update_data.get("username", user.username)
    await _assert_unique_email_username(session, str(target_email), target_username, user.id)
    for field_name, field_value in update_data.items():
        setattr(user, field_name, field_value)

    if interests_payload is not None:
        for existing_interest in list(user.interests):
            await session.delete(existing_interest)

        new_interests = [
            UserInterest(user_id=user_id, **interest)
            for interest in interests_payload
        ]
        if new_interests:
            session.add_all(new_interests)

    await session.commit()
    updated_user = await _load_user_with_interests(session, user_id)
    if not updated_user:
        return None
    return UserRead.model_validate(updated_user)


async def delete_user(session: AsyncSession, user_id: str) -> bool:
    """Input: user_id. Output: bool. Side effects: delete em user e cascata de interesses."""
    user = await _load_user_with_interests(session, user_id)
    if not user:
        return False
    await session.delete(user)
    await session.commit()
    return True


async def get_user_profile_card(session: AsyncSession, user_id: str) -> UserProfileCard | None:
    """Input: user_id. Output: card com UserRead + PlayerStatsRead."""
    cached_profile = await get_cached_user_profile(user_id)
    if cached_profile is not None:
        return cached_profile

    user = await _load_user_with_interests(session, user_id)
    if not user:
        return None

    sport_type = _get_primary_sport_type(user)

    stats = await _get_player_stats_by_user_id(session, user_id)
    if not stats:
        default_position = "armador" if sport_type == "BASKETBALL" else "meia"
        stats = PlayerStats(user_id=user_id, position=normalize_position_input(default_position))
        stats.overall = await _calculate_overall_for_sport(sport_type, stats)
        stats.playstyle_archetype = calculate_playstyle_archetype(
            pace=stats.pace,
            shooting=stats.shooting,
            passing=stats.passing,
            defense=stats.defense,
            physical=stats.physical,
            technique=stats.technique,
        )
        session.add(stats)
        await session.commit()
        await session.refresh(stats)
    else:
        stats.overall = await _calculate_overall_for_sport(sport_type, stats)

    xp_rows = await _get_user_xp_rows(session, user_id)
    progress, residual_total, active_xp_rows = _build_xp_summary(xp_rows, sport_type)
    achievements = await _get_user_achievements(session, user_id)
    synergy_badges = await list_user_synergy_badges(session=session, user_id=user_id)
    season_snapshot = await get_user_season_snapshot(session, user_id)

    profile_card = UserProfileCard(
        user=UserRead.model_validate(user),
        stats=PlayerStatsRead.model_validate(stats),
        sport_type=sport_type,
        overall_by_position=stats.overall,
        season_code=season_snapshot.season_code,
        season_level=season_snapshot.season_level,
        season_xp_total=season_snapshot.season_xp_total,
        season_frame=season_snapshot.frame_code,
        season_badges=season_snapshot.badges,
        xp_progress=progress,
        xp_residual_total=residual_total,
        synergy_badges=synergy_badges,
        xp_entries=[UserXPRead.model_validate(xp_row) for xp_row in active_xp_rows],
        achievements=[UserAchievementRead.model_validate(achievement) for achievement in achievements],
    )

    await set_cached_user_profile(user_id, profile_card)

    return profile_card


async def update_user_stats(session: AsyncSession, payload: PlayerStatsUpdate) -> PlayerStatsRead:
    """Input: PlayerStatsUpdate. Output: stats recalculados com overall e arquétipo."""
    user = await _load_user_with_interests(session, payload.user_id)
    if not user:
        raise ValueError("user_not_found")

    sport_type = _get_primary_sport_type(user)

    stats = await _get_player_stats_by_user_id(session, payload.user_id)
    if not stats:
        default_position = "armador" if sport_type == "BASKETBALL" else "meia"
        stats = PlayerStats(user_id=payload.user_id, position=normalize_position_input(default_position))
        session.add(stats)
        await session.flush()

    update_data = payload.model_dump(exclude_unset=True, exclude={"user_id"})
    if "position" in update_data:
        update_data["position"] = normalize_position_input(update_data["position"])
    for field_name, field_value in update_data.items():
        setattr(stats, field_name, field_value)

    stats.overall = await _calculate_overall_for_sport(sport_type, stats)
    stats.playstyle_archetype = calculate_playstyle_archetype(
        pace=stats.pace,
        shooting=stats.shooting,
        passing=stats.passing,
        defense=stats.defense,
        physical=stats.physical,
        technique=stats.technique,
    )
    stats.updated_at = datetime.now(UTC)

    await sync_user_prestige_entries(session, user_id=payload.user_id, stats=stats)

    await session.commit()
    await session.refresh(stats)
    return PlayerStatsRead.model_validate(stats)
