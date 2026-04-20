from __future__ import annotations

import pytest

from app.models.player_stats import UserAchievement, UserXP
from app.repositories.xp_repository import SqlAlchemyXpRepository
from tests.conftest import FakeAsyncSession, FakeResult


@pytest.mark.asyncio
async def test_ensure_user_xp_rows_creates_missing_rows() -> None:
    session = FakeAsyncSession(execute_results=[FakeResult(rows=[])])
    repo = SqlAlchemyXpRepository(session)

    rows = await repo.ensure_user_xp_rows("user-1")

    assert rows
    assert all(isinstance(row, UserXP) for row in rows)
    assert session.flushes == 1


@pytest.mark.asyncio
async def test_upsert_user_achievements_persists_without_commit() -> None:
    session = FakeAsyncSession(execute_results=[FakeResult(rows=[]), FakeResult(rows=[0]), FakeResult(rows=[0])])
    repo = SqlAlchemyXpRepository(session)

    triggers = [
        type("Trigger", (), {"code": "hat_trick", "title": "Hat-Trick", "bonus_attributes": {"goals": 3}, "execution_bonus": 1})()
    ]

    persisted = await repo.upsert_user_achievements("user-1", triggers)  # type: ignore[arg-type]

    assert persisted
    assert all(isinstance(item, UserAchievement) for item in persisted)
    assert session.commits == 0
