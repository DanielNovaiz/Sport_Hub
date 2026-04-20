from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from app.models.player_stats import UserPrestige
from tests.conftest import FakeAsyncSession, FakeResult


_MAINTENANCE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "maintenance_service.py"
_MAINTENANCE_SPEC = importlib.util.spec_from_file_location("maintenance_service_for_tests", _MAINTENANCE_PATH)
assert _MAINTENANCE_SPEC and _MAINTENANCE_SPEC.loader
_MAINTENANCE_MODULE = importlib.util.module_from_spec(_MAINTENANCE_SPEC)
sys.modules[_MAINTENANCE_SPEC.name] = _MAINTENANCE_MODULE
_MAINTENANCE_SPEC.loader.exec_module(_MAINTENANCE_MODULE)

credit_prestige_xp = _MAINTENANCE_MODULE.credit_prestige_xp


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