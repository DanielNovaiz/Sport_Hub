from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.player_stats import MatchPerformance, PlayerStats
from tests.conftest import FakeAsyncSession, FakeResult

from app.services.streak_manager import evaluate_on_fire_streak, PHYSICAL_BONUS_ATTRIBUTES


def _match(user_id: str, team_score: int, opponent_score: int, minutes_ago: int) -> MatchPerformance:
    return MatchPerformance(
        user_id=user_id,
        sport_type="football",
        team_score=team_score,
        opponent_score=opponent_score,
        created_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


@pytest.mark.asyncio
async def test_on_fire_badge_triggers_on_three_wins_within_last_five() -> None:
    performance = _match("user-1", 4, 1, 0)
    recent_matches = [
        _match("user-1", 2, 3, 0),
        _match("user-1", 5, 2, 1),
        _match("user-1", 6, 1, 2),
        _match("user-1", 7, 3, 3),
        _match("user-1", 1, 2, 4),
    ]
    session = FakeAsyncSession(execute_results=[FakeResult(rows=recent_matches)])

    result = await evaluate_on_fire_streak(session, performance)

    assert result.active is True
    assert result.badge_name == "On Fire"
    assert result.streak_length == 3
    assert len(result.recent_results) == 5
    assert result.recent_results[:4] == [False, True, True, True]


@pytest.mark.asyncio
async def test_on_fire_badge_boosts_all_physical_attributes() -> None:
    performance = _match("user-2", 3, 1, 0)
    recent_matches = [
        _match("user-2", 3, 0, 0),
        _match("user-2", 2, 1, 1),
        _match("user-2", 4, 2, 2),
        _match("user-2", 1, 4, 3),
        _match("user-2", 0, 2, 4),
    ]
    session = FakeAsyncSession(execute_results=[FakeResult(rows=recent_matches)])
    stats = PlayerStats(
        user_id="user-2",
        physical=50,
        stamina=51,
        strength=52,
        balance=53,
        velocity=54,
        jump=55,
        agility=56,
        energy=57,
        lateral_agility=58,
        coordination=59,
        sand_agility=60,
        jumping_endurance=61,
    )

    result = await evaluate_on_fire_streak(session, performance, stats)

    assert result.active is True
    for attribute in PHYSICAL_BONUS_ATTRIBUTES:
        assert result.bonus_attributes[attribute] == 5
        assert result.boosted_stats[attribute] == min(99, getattr(stats, attribute) + 5)


@pytest.mark.asyncio
async def test_on_fire_badge_remains_inactive_without_three_wins() -> None:
    performance = _match("user-3", 1, 2, 0)
    recent_matches = [
        _match("user-3", 1, 2, 0),
        _match("user-3", 2, 3, 1),
        _match("user-3", 3, 1, 2),
        _match("user-3", 0, 1, 3),
        _match("user-3", 4, 2, 4),
    ]
    session = FakeAsyncSession(execute_results=[FakeResult(rows=recent_matches)])

    result = await evaluate_on_fire_streak(session, performance)

    assert result.active is False
    assert result.badge_name is None
    assert result.bonus_attributes == {}
    assert result.boosted_stats == {}
