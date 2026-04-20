"""Gerenciador de streak temporária para badge On Fire."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stats import MatchPerformance, PlayerStats


PHYSICAL_BONUS_ATTRIBUTES: tuple[str, ...] = (
    "physical",
    "stamina",
    "strength",
    "balance",
    "velocity",
    "jump",
    "agility",
    "energy",
    "lateral_agility",
    "coordination",
    "sand_agility",
    "jumping_endurance",
)

BONUS_VALUE = 5
BADGE_NAME = "On Fire"


@dataclass(frozen=True)
class StreakResult:
    badge_name: str | None
    active: bool
    streak_length: int
    recent_results: list[bool]
    bonus_attributes: dict[str, int]
    boosted_stats: dict[str, int]


async def _get_recent_matches(
    session: AsyncSession,
    user_id: str,
    limit: int = 5,
) -> list[MatchPerformance]:
    query = (
        select(MatchPerformance)
        .where(MatchPerformance.user_id == user_id)
        .order_by(MatchPerformance.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return result.scalars().all()


def _is_win(match: MatchPerformance) -> bool:
    return int(getattr(match, "team_score", 0) or 0) > int(getattr(match, "opponent_score", 0) or 0)


def _calculate_streak(matches: list[MatchPerformance]) -> tuple[int, list[bool]]:
    recent_results = [_is_win(match) for match in matches]
    streak = 0
    best_streak = 0
    for won in recent_results:
        if won:
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
    return best_streak, recent_results


def _apply_bonus(source: PlayerStats | Mapping[str, int] | None, bonus_attributes: Mapping[str, int]) -> dict[str, int]:
    if source is None:
        return dict(bonus_attributes)

    boosted: dict[str, int] = {}
    for attribute in bonus_attributes:
        if isinstance(source, Mapping):
            current_value = int(source.get(attribute, 0) or 0)
        else:
            current_value = int(getattr(source, attribute, 0) or 0)
        boosted[attribute] = min(99, current_value + int(bonus_attributes[attribute]))
    return boosted


async def evaluate_on_fire_streak(
    session: AsyncSession,
    performance: MatchPerformance,
    source: PlayerStats | Mapping[str, int] | None = None,
) -> StreakResult:
    """Verifica as últimas 5 partidas e ativa a badge temporária On Fire.

    Regra:
    - Se o time vencer 3 partidas seguidas nas últimas 5, ativa On Fire
    - Bônus temporário: +5 em todos os atributos físicos
    """
    recent_matches = await _get_recent_matches(session, str(performance.user_id), limit=5)
    streak_length, recent_results = _calculate_streak(recent_matches)
    active = streak_length >= 3
    bonus_attributes = {attribute: BONUS_VALUE for attribute in PHYSICAL_BONUS_ATTRIBUTES} if active else {}
    boosted_stats = _apply_bonus(source, bonus_attributes)

    return StreakResult(
        badge_name=BADGE_NAME if active else None,
        active=active,
        streak_length=streak_length,
        recent_results=recent_results,
        bonus_attributes=bonus_attributes,
        boosted_stats=boosted_stats,
    )
