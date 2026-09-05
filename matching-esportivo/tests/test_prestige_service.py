from __future__ import annotations

import pytest

from app.models.player_stats import UserPrestige
from tests.conftest import FakeAsyncSession, FakeResult

from app.services.maintenance_service import credit_prestige_xp


@pytest.mark.asyncio
async def test_credit_prestige_xp_creates_gold_entry_and_tracks_style_points() -> None:
    session = FakeAsyncSession(execute_results=[FakeResult(rows=[])])

    prestige_row, created = await credit_prestige_xp(
        session,
        user_id="user-99",
        attribute_name="shooting",
        xp_amount=125,
    )

    assert created is True
    assert isinstance(prestige_row, UserPrestige)
    assert prestige_row.prestige_level == 3
    assert prestige_row.style_points == 125
    assert prestige_row.total_prestige_xp == 125