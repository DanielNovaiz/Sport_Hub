"""Serviço de conquistas de partida."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stats import MatchPerformance, UserAchievement


@dataclass(frozen=True)
class AchievementSpec:
    code: str
    title: str
    threshold_value: int
    bonus_attribute: str
    base_bonus_value: int


ACHIEVEMENT_SPECS: tuple[AchievementSpec, ...] = (
    AchievementSpec(
        code="HAT_TRICK",
        title="Hat Trick",
        threshold_value=3,
        bonus_attribute="goals",
        base_bonus_value=3,
    ),
    AchievementSpec(
        code="WALL",
        title="Wall",
        threshold_value=5,
        bonus_attribute="blocks",
        base_bonus_value=5,
    ),
)

ACHIEVEMENT_RARITY_MULTIPLIERS: dict[str, float] = {
    "Bronze": 1.0,
    "Silver": 1.5,
    "Gold": 2.5,
}


def resolve_achievement_rarity(code_count: int, total_count: int) -> str:
    """Define a raridade com base na frequência global do evento."""
    if total_count <= 0 or code_count <= 0:
        return "Bronze"

    frequency = code_count / total_count
    if frequency <= 0.05:
        return "Gold"
    if frequency <= 0.20:
        return "Silver"
    return "Bronze"


def apply_achievement_rarity_bonus(base_bonus_value: int, tier: str) -> int:
    multiplier = ACHIEVEMENT_RARITY_MULTIPLIERS.get(tier, 1.0)
    return max(0, int(round(base_bonus_value * multiplier)))


async def _get_global_achievement_frequency(session: AsyncSession, code: str) -> tuple[int, int]:
    total_result = await session.execute(select(func.count(UserAchievement.id)))
    total_count = int(total_result.scalar_one() or 0)

    code_result = await session.execute(
        select(func.count(UserAchievement.id)).where(UserAchievement.code == code)
    )
    code_count = int(code_result.scalar_one() or 0)

    return code_count, total_count


async def award_match_achievements(
    session: AsyncSession,
    performance: MatchPerformance,
) -> list[UserAchievement]:
    """Insere conquistas de partida na tabela UserAchievement.

    Gatilhos:
    - goals >= 3 -> HAT_TRICK
    - blocks >= 5 -> WALL
    """
    user_id = str(performance.user_id)
    persisted: list[UserAchievement] = []
    inserted = False

    for spec in ACHIEVEMENT_SPECS:
        current_value = int(getattr(performance, spec.bonus_attribute, 0) or 0)
        if current_value < spec.threshold_value:
            continue

        query = select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.code == spec.code,
        )
        result = await session.execute(query)
        existing = result.scalars().first()
        if existing:
            persisted.append(existing)
            continue

        code_count, total_count = await _get_global_achievement_frequency(session, spec.code)
        tier = resolve_achievement_rarity(code_count, total_count)

        achievement = UserAchievement(
            user_id=user_id,
            code=spec.code,
            title=spec.title,
            tier=tier,
            execution_count=1,
            bonus_attribute=spec.bonus_attribute,
            bonus_value=apply_achievement_rarity_bonus(spec.base_bonus_value, tier),
            last_triggered_at=datetime.now(UTC),
        )
        session.add(achievement)
        persisted.append(achievement)
        inserted = True

    if inserted:
        await session.commit()

    return persisted
