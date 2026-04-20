"""Tests do middleware de rate limit de MatchPerformance."""

from datetime import UTC, datetime, timedelta

from app.middleware.match_performance_rate_limit import is_rate_limited


def test_is_rate_limited_when_no_previous_submission() -> None:
    now = datetime.now(UTC)
    assert is_rate_limited(last_submission_at=None, now=now) is False


def test_is_rate_limited_inside_20_minute_window() -> None:
    now = datetime.now(UTC)
    last_submission = now - timedelta(minutes=10)
    assert is_rate_limited(last_submission_at=last_submission, now=now) is True


def test_is_not_rate_limited_after_20_minutes() -> None:
    now = datetime.now(UTC)
    last_submission = now - timedelta(minutes=21)
    assert is_rate_limited(last_submission_at=last_submission, now=now) is False
