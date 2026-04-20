from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_MAINTENANCE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "maintenance_service.py"
_MAINTENANCE_SPEC = importlib.util.spec_from_file_location("maintenance_service_for_tests", _MAINTENANCE_PATH)
assert _MAINTENANCE_SPEC and _MAINTENANCE_SPEC.loader
_MAINTENANCE_MODULE = importlib.util.module_from_spec(_MAINTENANCE_SPEC)
sys.modules[_MAINTENANCE_SPEC.name] = _MAINTENANCE_MODULE
_MAINTENANCE_SPEC.loader.exec_module(_MAINTENANCE_MODULE)

INACTIVITY_DECAY_REASON = _MAINTENANCE_MODULE.INACTIVITY_DECAY_REASON
apply_common_xp_with_cap = _MAINTENANCE_MODULE.apply_common_xp_with_cap
apply_penalty_with_rollback_guard = _MAINTENANCE_MODULE.apply_penalty_with_rollback_guard
convert_xp_to_attribute_points = _MAINTENANCE_MODULE.convert_xp_to_attribute_points


def test_integer_math_guard_exact_conversion() -> None:
    converted = convert_xp_to_attribute_points(121)
    assert converted.points_gained == 2
    assert converted.residual_xp == 1


def test_apply_common_xp_with_cap_moves_overflow_to_prestige() -> None:
    result = apply_common_xp_with_cap(
        current_attribute_value=98,
        current_residual_xp=50,
        incoming_xp=80,
    )

    assert result.applied_points == 1
    assert result.reached_cap is True
    assert result.residual_xp == 0
    assert result.prestige_xp > 0


def test_apply_common_xp_when_already_capped_goes_full_prestige() -> None:
    result = apply_common_xp_with_cap(
        current_attribute_value=99,
        current_residual_xp=30,
        incoming_xp=90,
    )

    assert result.applied_points == 0
    assert result.reached_cap is True
    assert result.residual_xp == 0
    assert result.prestige_xp == 120


def test_penalty_rollback_guard_respects_base_floor() -> None:
    updated = apply_penalty_with_rollback_guard(
        current_value=52,
        penalty=10,
        reason="FG% baixo",
    )
    assert updated == 50


def test_penalty_rollback_allows_inactivity_decay_below_base() -> None:
    updated = apply_penalty_with_rollback_guard(
        current_value=52,
        penalty=10,
        reason=INACTIVITY_DECAY_REASON,
    )
    assert updated == 42
