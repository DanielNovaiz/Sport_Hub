from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from app.positions import POSITIONS_MAP, normalize_position_input
from app.models.player_stats import PlayerStats, UserPrestige
from app.models.user import User, UserInterest
from app.schemas.user import PlayerStatsUpdate
from tests.conftest import FakeAsyncSession, FakeResult


_USER_SERVICE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "user_service.py"
_USER_SPEC = importlib.util.spec_from_file_location("user_service_for_tests", _USER_SERVICE_PATH)
assert _USER_SPEC and _USER_SPEC.loader
_USER_MODULE = importlib.util.module_from_spec(_USER_SPEC)
sys.modules[_USER_SPEC.name] = _USER_MODULE
_USER_SPEC.loader.exec_module(_USER_MODULE)

calculate_player_overall = _USER_MODULE.calculate_player_overall
calculate_playstyle_archetype = _USER_MODULE.calculate_playstyle_archetype
update_user_stats = _USER_MODULE.update_user_stats


@pytest.mark.asyncio
async def test_update_user_stats_recalculates_overall_and_archetype() -> None:
    user = User(
        id="user-1",
        email="user1@example.com",
        username="user1",
        full_name="User One",
    )
    stats = PlayerStats(
        id="stats-1",
        user_id="user-1",
        position="atacante",
        pace=80,
        shooting=82,
        passing=70,
        defense=50,
        physical=72,
        technique=74,
    )

    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[user]),
            FakeResult(rows=[stats]),
        ]
    )

    payload = PlayerStatsUpdate(user_id="user-1", shooting=92, pace=90, defense=60)
    result = await update_user_stats(session, payload)

    assert result.user_id == "user-1"
    assert 0 <= result.overall <= 99
    assert result.playstyle_archetype == "Sharpshooter"


def test_positions_map_normalizes_common_user_inputs() -> None:
    assert POSITIONS_MAP["meia"] == "MIDFIELDER"
    assert POSITIONS_MAP["cam"] == "MIDFIELDER"
    assert POSITIONS_MAP["armador (futebol)"] == "MIDFIELDER"
    assert POSITIONS_MAP["pivo (basquete)"] == "CENTER_BASKET"
    assert POSITIONS_MAP["center"] == "CENTER_BASKET"

    assert normalize_position_input("Meia") == "MIDFIELDER"
    assert normalize_position_input("CAM") == "MIDFIELDER"
    assert normalize_position_input("Armador (Futebol)") == "MIDFIELDER"
    assert normalize_position_input("Pivô (Basquete)") == "CENTER_BASKET"
    assert normalize_position_input("Center") == "CENTER_BASKET"


@pytest.mark.asyncio
async def test_update_user_stats_normalizes_position_on_profile_creation() -> None:
    user = User(
        id="user-2",
        email="user2@example.com",
        username="user2",
        full_name="User Two",
    )
    user.interests = [
        UserInterest(
            user_id="user-2",
            sport="basquete",
            skill_level="intermediate",
            is_primary=True,
        )
    ]

    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[user]),
            FakeResult(rows=[]),
        ]
    )

    payload = PlayerStatsUpdate(user_id="user-2", position="Pivô (Basquete)")
    result = await update_user_stats(session, payload)

    assert result.position == "CENTER_BASKET"
    assert session.added, "Esperava criação de PlayerStats no fluxo de criação do perfil"


@pytest.mark.asyncio
async def test_update_user_stats_creates_prestige_entry_at_cap() -> None:
    user = User(
        id="user-3",
        email="user3@example.com",
        username="user3",
        full_name="User Three",
    )
    stats = PlayerStats(
        id="stats-3",
        user_id="user-3",
        position="meia",
        pace=80,
        shooting=98,
        passing=70,
        defense=50,
        physical=72,
        technique=74,
    )

    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[user]),
            FakeResult(rows=[stats]),
            FakeResult(rows=[]),
        ]
    )

    payload = PlayerStatsUpdate(user_id="user-3", shooting=99)
    result = await update_user_stats(session, payload)

    prestige_rows = [item for item in session.added if isinstance(item, UserPrestige)]
    assert result.shooting == 99
    assert prestige_rows, "Esperava criação de UserPrestige quando o atributo bate 99"
    assert prestige_rows[0].prestige_level == 1
    assert prestige_rows[0].style_points == 0


def test_calculate_player_overall_position_weights() -> None:
    attacker_overall = calculate_player_overall(
        position="atacante",
        pace=90,
        shooting=92,
        passing=65,
        defense=40,
        physical=70,
        technique=75,
    )
    defender_overall = calculate_player_overall(
        position="zagueiro",
        pace=90,
        shooting=92,
        passing=65,
        defense=40,
        physical=70,
        technique=75,
    )

    assert attacker_overall > defender_overall


def test_calculate_playstyle_archetype_by_dominant_attribute() -> None:
    archetype = calculate_playstyle_archetype(
        pace=88,
        shooting=84,
        passing=70,
        defense=60,
        physical=62,
        technique=72,
    )
    assert archetype == "Speedster"
