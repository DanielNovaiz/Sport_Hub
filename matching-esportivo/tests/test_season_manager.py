from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.player_stats import UserAchievement
from app.models.season import Season, SeasonMilestone, SeasonRank
from app.services.season_manager import (
    _next_saturday_window,
    _season_window_for,
    award_season_progress,
    get_user_season_snapshot,
    grant_season_completion_badge,
)

from tests.conftest import FakeAsyncSession, FakeResult


def test_season_window_spans_three_months() -> None:
    code, starts_at, ends_at = _season_window_for(datetime(2026, 4, 15, tzinfo=UTC))

    assert code == "S01"
    assert starts_at == datetime(2026, 4, 1, tzinfo=UTC)
    assert ends_at == datetime(2026, 7, 1, tzinfo=UTC)


def test_next_saturday_window_points_to_upcoming_saturday() -> None:
    saturday_start, saturday_end = _next_saturday_window(datetime(2026, 4, 15, tzinfo=UTC))

    assert saturday_start.weekday() == 5
    assert saturday_start.hour == 0
    assert saturday_end > saturday_start
    assert (saturday_end - saturday_start).days == 0


@pytest.mark.asyncio
async def test_grant_season_completion_badge_creates_unique_badge() -> None:
    season = Season(id="season-1", code="S01", starts_at=datetime(2026, 4, 1, tzinfo=UTC), ends_at=datetime(2026, 7, 1, tzinfo=UTC), status="active")
    session = FakeAsyncSession(execute_results=[FakeResult(rows=[])])

    achievement = await grant_season_completion_badge(session, season=season, user_id="user-1", now=datetime(2026, 7, 2, tzinfo=UTC))

    assert achievement is not None
    assert isinstance(achievement, UserAchievement)
    assert achievement.code == "s01_elite"
    assert achievement.title == "S01 Elite"
    assert session.added[0].code == "s01_elite"


@pytest.mark.asyncio
async def test_award_season_progress_unlocks_milestones(monkeypatch) -> None:
    season = Season(id="season-1", code="S01", starts_at=datetime(2026, 4, 1, tzinfo=UTC), ends_at=datetime(2026, 7, 1, tzinfo=UTC), status="active")
    rank = SeasonRank(id="rank-1", season_id=season.id, user_id="user-1", xp_total=850, level=9, matches_played=3, wins=2, losses=1)
    milestone_frame = SeasonMilestone(
        id="milestone-10",
        season_id=season.id,
        required_level=10,
        reward_kind="cosmetic_frame",
        frame_code="s01_frame_10",
        xp_multiplier=1.0,
        title="S01 Frame 10",
        description="Frame sazonal",
    )
    milestone_weekend = SeasonMilestone(
        id="milestone-20",
        season_id=season.id,
        required_level=20,
        reward_kind="weekend_multiplier",
        frame_code=None,
        xp_multiplier=2.0,
        title="S01 Weekend Boost",
        description="2x XP no próximo sábado",
    )

    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[milestone_frame, milestone_weekend]),
            FakeResult(rows=[]),
            FakeResult(rows=[]),
            FakeResult(rows=[]),
            FakeResult(rows=[]),
        ]
    )

    async def fake_get_current_season(session_arg, now=None):
        return season

    async def fake_get_or_create_season_rank(session_arg, user_id, season=None, now=None):
        return rank

    async def fake_get_active_xp_multiplier(session_arg, user_id, now=None):
        return 1.0

    async def fake_get_current_frame_code(session_arg, user_id, season=None):
        return "s01_frame_10"

    async def fake_invalidate_user_profile_cache(user_id):
        return None

    monkeypatch.setattr("app.services.season_manager.get_current_season", fake_get_current_season)
    monkeypatch.setattr("app.services.season_manager.get_or_create_season_rank", fake_get_or_create_season_rank)
    monkeypatch.setattr("app.services.season_manager.get_active_xp_multiplier", fake_get_active_xp_multiplier)
    monkeypatch.setattr("app.services.season_manager.get_current_frame_code", fake_get_current_frame_code)
    monkeypatch.setattr("app.services.season_manager.invalidate_user_profile_cache", fake_invalidate_user_profile_cache)

    result = await award_season_progress(
        session,
        user_id="user-1",
        xp_gained=250,
        won_match=True,
        now=datetime(2026, 4, 15, tzinfo=UTC),
    )

    assert result.season_code == "S01"
    assert result.season_level >= 11
    assert result.season_xp_total == 1100
    assert result.frame_code == "s01_frame_10"
    assert len(result.unlocked_rewards) == 1
    assert result.unlocked_rewards[0].reward_kind == "cosmetic_frame"
    assert rank.xp_total == 1100
    assert rank.level == 11
    assert rank.matches_played == 4
    assert session.commits == 0
