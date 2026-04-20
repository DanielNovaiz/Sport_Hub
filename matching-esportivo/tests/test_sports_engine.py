from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from app.models.player_stats import MatchPerformance


_XP_SERVICE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "xp_service.py"
_XP_SPEC = importlib.util.spec_from_file_location("xp_service_for_tests", _XP_SERVICE_PATH)
assert _XP_SPEC and _XP_SPEC.loader
_XP_MODULE = importlib.util.module_from_spec(_XP_SPEC)
sys.modules[_XP_SPEC.name] = _XP_MODULE
_XP_SPEC.loader.exec_module(_XP_MODULE)

BASKETBALL_POSITION_WEIGHTS = _XP_MODULE.BASKETBALL_POSITION_WEIGHTS
FOOTBALL_POSITION_WEIGHTS = _XP_MODULE.FOOTBALL_POSITION_WEIGHTS
VOLLEYBALL_POSITION_WEIGHTS = _XP_MODULE.VOLLEYBALL_POSITION_WEIGHTS
apply_multiplier = _XP_MODULE.apply_multiplier
calculate_basketball_overall = _XP_MODULE.calculate_basketball_overall
calculate_basketball_package_scores = _XP_MODULE.calculate_basketball_package_scores
calculate_football_overall = _XP_MODULE.calculate_football_overall
calculate_football_package_scores = _XP_MODULE.calculate_football_package_scores
calculate_precise_overall = _XP_MODULE.calculate_precise_overall
calculate_volleyball_overall = _XP_MODULE.calculate_volleyball_overall
calculate_volleyball_package_scores = _XP_MODULE.calculate_volleyball_package_scores
distribute_match_xp = _XP_MODULE.distribute_match_xp
process_match_performance = _XP_MODULE.process_match_performance


def _uniform_basketball_stats(x: int) -> dict[str, int]:
    return {
        "shoot_long": x,
        "shoot_mid": x,
        "shoot_short": x,
        "finishing": x,
        "velocity": x,
        "jump": x,
        "agility": x,
        "energy": x,
        "strength": x,
        "balance": x,
        "passing": x,
        "ball_control": x,
        "vision": x,
        "dribble": x,
        "steal": x,
        "block": x,
        "perim_def": x,
        "post_def": x,
        "rebound": x,
        "reb_predict": x,
        "combativeness": x,
    }


def _uniform_football_stats(x: int) -> dict[str, int]:
    return {
        "short_finish": x,
        "long_shot": x,
        "free_kick": x,
        "sprint": x,
        "acceleration": x,
        "agility": x,
        "stamina": x,
        "strength": x,
        "balance": x,
        "short_pass": x,
        "long_pass": x,
        "crossing": x,
        "vision": x,
        "dribbling": x,
        "ball_control": x,
        "tackle": x,
        "interception": x,
        "marking": x,
        "ball_shielding": x,
    }


def _uniform_volleyball_stats(x: int) -> dict[str, int]:
    return {
        "spike_power": x,
        "spike_accuracy": x,
        "jump": x,
        "reaction": x,
        "serve_power": x,
        "serve_tactical": x,
        "game_vision": x,
        "block": x,
        "reception": x,
        "floor_defense": x,
        "coverage": x,
        "setting": x,
        "creativity": x,
        "lateral_agility": x,
        "stamina": x,
        "coordination": x,
    }


def _uniform_beach_volleyball_stats(x: int) -> dict[str, int]:
    stats = _uniform_volleyball_stats(x)
    stats.update({
        "sand_agility": x,
        "jumping_endurance": x,
    })
    return stats


@pytest.mark.parametrize("x", [0, 12, 50, 87, 99])
def test_baseline_uniform_value_returns_same_overall_across_positions(x: int) -> None:
    """Se todos os sub-atributos forem X, overall deve ser exatamente X para qualquer posição."""
    b_stats = _uniform_basketball_stats(x)
    f_stats = _uniform_football_stats(x)
    v_stats = _uniform_volleyball_stats(x)

    for position in BASKETBALL_POSITION_WEIGHTS.keys():
        overall = calculate_basketball_overall(position, b_stats)
        assert overall == x

    for position in FOOTBALL_POSITION_WEIGHTS.keys():
        overall = calculate_football_overall(position, f_stats)
        assert overall == x

    for position in VOLLEYBALL_POSITION_WEIGHTS.keys():
        overall = calculate_volleyball_overall(position, v_stats)
        assert overall == x


def test_boundary_99_never_exceeds_even_with_excessive_stats_and_bonus() -> None:
    """Overall nunca pode ultrapassar 99 mesmo com valores excedentes."""
    overcap = 10_000

    b_overall = calculate_basketball_overall("armador", _uniform_basketball_stats(overcap))
    f_overall = calculate_football_overall("meia", _uniform_football_stats(overcap))
    v_overall = calculate_volleyball_overall("libero", _uniform_volleyball_stats(overcap))

    assert b_overall == 99
    assert f_overall == 99
    assert v_overall == 99


def test_zero_point_does_not_break_calculation_or_divide_by_zero() -> None:
    """Atributos em zero não devem quebrar o motor (sem ZeroDivisionError)."""
    b = calculate_basketball_overall("pivo", _uniform_basketball_stats(0))
    f = calculate_football_overall("goleiro", _uniform_football_stats(0))
    v = calculate_volleyball_overall("levantador", _uniform_volleyball_stats(0))

    assert b == 0
    assert f == 0
    assert v == 0


def test_beach_volleyball_uses_harmonic_mean_and_ignores_position() -> None:
    """Beach deve usar média harmônica e ignorar posição fixa."""
    stats = _uniform_beach_volleyball_stats(72)

    beach_libero = calculate_volleyball_overall("libero", stats, sub_type="BEACH")
    beach_central = calculate_volleyball_overall("central", stats, sub_type="BEACH")
    beach_no_pos = calculate_volleyball_overall(source=stats, sub_type="BEACH")

    assert beach_libero == 72
    assert beach_central == 72
    assert beach_no_pos == 72


def test_apply_multiplier_futsal_and_3x3_before_level_conversion() -> None:
    """Multiplicador de XP deve ser aplicado antes da conversão para pontos/nível."""
    base = {"agility": 50, "ball_control": 40, "shoot_long": 30}

    futsal = apply_multiplier(dict(base), sport_type="football", sub_type="FUTSAL")
    three_x_three = apply_multiplier(dict(base), sport_type="basketball", sub_type="3x3")

    # 1.2x aplicado antes de level conversion
    assert futsal["agility"] == 60
    assert futsal["ball_control"] == 48

    # 2x aplicado em 3x3
    assert three_x_three["shoot_long"] == 60

    # Integração com pipeline de nível (XP_PER_LEVEL=60)
    perf_base = MatchPerformance(user_id="u1", sport_type="football", goals=1, assists=1, dribbles=6)
    perf_futsal = MatchPerformance(user_id="u2", sport_type="football", sub_type="FUTSAL", goals=1, assists=1, dribbles=6)

    res_base = process_match_performance(perf_base)
    res_futsal = process_match_performance(perf_futsal)

    assert res_futsal.xp_gains["agility"] >= res_base.xp_gains["agility"]
    assert res_futsal.xp_gains["ball_control"] >= res_base.xp_gains["ball_control"]


def test_rounding_precision_uses_two_decimals_before_display() -> None:
    """Valida precisão com 2 casas decimais via pytest.approx antes de arredondar para exibição."""
    stats = {
        # finalizacao = 50
        "short_finish": 40,
        "long_shot": 50,
        "free_kick": 60,
        # mobilidade = 50
        "sprint": 60,
        "acceleration": 50,
        "agility": 40,
        # fisico = 50
        "stamina": 60,
        "strength": 50,
        "balance": 40,
        # criacao = 60
        "short_pass": 60,
        "long_pass": 60,
        "crossing": 60,
        "vision": 60,
        "dribbling": 60,
        "ball_control": 60,
        # defesa = 40
        "tackle": 40,
        "interception": 40,
        "marking": 40,
        "ball_shielding": 40,
    }

    packages = calculate_football_package_scores(stats)
    weights = FOOTBALL_POSITION_WEIGHTS["meia"]
    weighted_sum = sum(packages[name] * weight for name, weight in weights.items())
    divisor = sum(weights.values())

    precise = calculate_precise_overall(weighted_sum, divisor)
    expected_precise = round(weighted_sum / divisor, 2)

    assert precise == pytest.approx(expected_precise, abs=0.01)

    # E a exibição final segue o inteiro arredondado do valor preciso
    displayed = calculate_football_overall("meia", stats)
    assert displayed == int(round(precise))


def test_multiplier_is_applied_inside_distribution_flow() -> None:
    """Garante que distribute_match_xp usa apply_multiplier internamente."""
    normal = MatchPerformance(
        user_id="u3",
        sport_type="football",
        goals=1,
        assists=1,
        dribbles=8,
    )
    futsal = MatchPerformance(
        user_id="u4",
        sport_type="football",
        sub_type="FUTSAL",
        goals=1,
        assists=1,
        dribbles=8,
    )

    normal_xp = distribute_match_xp(normal)
    futsal_xp = distribute_match_xp(futsal)

    assert futsal_xp.attribute_xp["agility"] >= normal_xp.attribute_xp["agility"]
    assert futsal_xp.attribute_xp["ball_control"] >= normal_xp.attribute_xp["ball_control"]
