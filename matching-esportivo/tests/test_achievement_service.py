from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from app.models.player_stats import MatchPerformance, UserAchievement
from tests.conftest import FakeAsyncSession, FakeResult


_ACHIEVEMENT_SERVICE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "achievement_service.py"
_ACHIEVEMENT_SPEC = importlib.util.spec_from_file_location("achievement_service_for_tests", _ACHIEVEMENT_SERVICE_PATH)
assert _ACHIEVEMENT_SPEC and _ACHIEVEMENT_SPEC.loader
_ACHIEVEMENT_MODULE = importlib.util.module_from_spec(_ACHIEVEMENT_SPEC)
sys.modules[_ACHIEVEMENT_SPEC.name] = _ACHIEVEMENT_MODULE
_ACHIEVEMENT_SPEC.loader.exec_module(_ACHIEVEMENT_MODULE)

award_match_achievements = _ACHIEVEMENT_MODULE.award_match_achievements
resolve_achievement_rarity = _ACHIEVEMENT_MODULE.resolve_achievement_rarity


@pytest.mark.asyncio
async def test_award_match_achievements_inserts_hat_trick_and_wall() -> None:
    performance = MatchPerformance(
        user_id="user-1",
        sport_type="football",
        goals=3,
        blocks=5,
    )
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[]),
            FakeResult(scalar_value=100),
            FakeResult(scalar_value=3),
            FakeResult(rows=[]),
            FakeResult(scalar_value=100),
            FakeResult(scalar_value=10),
        ]
    )

    achievements = await award_match_achievements(session, performance)

    assert len(achievements) == 2
    assert {item.code for item in achievements} == {"HAT_TRICK", "WALL"}
    assert len(session.added) == 2
    assert session.commits == 1


@pytest.mark.asyncio
async def test_award_match_achievements_skips_when_threshold_not_met() -> None:
    performance = MatchPerformance(
        user_id="user-2",
        sport_type="football",
        goals=2,
        blocks=4,
    )
    session = FakeAsyncSession()

    achievements = await award_match_achievements(session, performance)

    assert achievements == []
    assert session.added == []
    assert session.commits == 0


@pytest.mark.asyncio
async def test_award_match_achievements_does_not_duplicate_existing_rows() -> None:
    existing = UserAchievement(
        id="ach-1",
        user_id="user-3",
        code="HAT_TRICK",
        title="Hat Trick",
        tier="Bronze",
        execution_count=1,
        bonus_attribute="goals",
        bonus_value=3,
    )
    performance = MatchPerformance(
        user_id="user-3",
        sport_type="football",
        goals=3,
        blocks=5,
    )
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[existing]),
            FakeResult(rows=[]),
            FakeResult(scalar_value=100),
            FakeResult(scalar_value=10),
        ]
    )

    achievements = await award_match_achievements(session, performance)

    assert len(achievements) == 2
    assert achievements[0].code == "HAT_TRICK"
    assert achievements[1].code == "WALL"
    assert len(session.added) == 1
    assert session.commits == 1


def test_resolve_achievement_rarity_thresholds() -> None:
    assert resolve_achievement_rarity(3, 100) == "Gold"
    assert resolve_achievement_rarity(10, 100) == "Silver"
    assert resolve_achievement_rarity(40, 100) == "Bronze"
    assert resolve_achievement_rarity(0, 100) == "Bronze"


@pytest.mark.asyncio
async def test_award_match_achievements_applies_rarity_bonus_by_frequency() -> None:
    performance = MatchPerformance(
        user_id="user-4",
        sport_type="football",
        goals=3,
        blocks=5,
    )
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[]),
            FakeResult(scalar_value=100),
            FakeResult(scalar_value=3),
            FakeResult(rows=[]),
            FakeResult(scalar_value=100),
            FakeResult(scalar_value=10),
        ]
    )

    achievements = await award_match_achievements(session, performance)

    assert len(achievements) == 2
    assert achievements[0].tier == "Gold"
    assert achievements[0].bonus_value == 8
    assert achievements[1].tier == "Silver"
    assert achievements[1].bonus_value == 8
