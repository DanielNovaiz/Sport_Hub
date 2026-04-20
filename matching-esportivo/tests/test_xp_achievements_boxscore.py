from __future__ import annotations

from app.models.player_stats import MatchPerformance
from app.services.xp_service import process_match_performance, _resolve_xp_per_level


def _codes(result) -> set[str]:
    return {trigger.code for trigger in result.achievement_triggers}


def test_football_hat_trick_and_garcom_elite_and_cao_de_guarda() -> None:
    performance = MatchPerformance(
        user_id="user-1",
        sport_type="football",
        goals=3,
        assists=3,
        tackles=8,
        dribbles=6,
    )

    result = process_match_performance(performance, player_position="meia")
    codes = _codes(result)

    assert "hat_trick" in codes
    assert "garcom_de_elite" in codes
    assert "cao_de_guarda" in codes


def test_goalkeeper_exclusive_achievements() -> None:
    performance = MatchPerformance(
        user_id="user-2",
        sport_type="futebol",
        defenses=10,
        tackles=2,
    )

    result = process_match_performance(performance, player_position="goleiro")
    codes = _codes(result)

    assert "muralha" in codes
    assert "milagre" in codes


def test_volleyball_achievements() -> None:
    performance = MatchPerformance(
        user_id="user-3",
        sport_type="volleyball",
        attacks=13,
        defenses=11,
        blocks=5,
        sets=8,
    )

    result = process_match_performance(performance, player_position="libero")
    codes = _codes(result)

    assert "martelo_de_goias" in codes
    assert "aspirador_de_po" in codes
    assert "muralha_de_cristal" in codes


def test_sub_type_xp_modifiers_for_futsal_and_3x3() -> None:
    futsal_base = MatchPerformance(
        user_id="user-4-base",
        sport_type="football",
        goals=1,
        assists=1,
        dribbles=5,
    )
    futsal_base_result = process_match_performance(futsal_base, player_position="ponta")

    futsal = MatchPerformance(
        user_id="user-4",
        sport_type="football",
        sub_type="FUTSAL",
        goals=1,
        assists=1,
        dribbles=5,
    )
    futsal_result = process_match_performance(futsal, player_position="ponta")

    three_x_three_base = MatchPerformance(
        user_id="user-5-base",
        sport_type="basketball",
        field_goals_made=3,
        field_goals_attempted=6,
        points=12,
    )
    three_x_three_base_result = process_match_performance(three_x_three_base, player_position="ala")

    three_x_three = MatchPerformance(
        user_id="user-5",
        sport_type="basketball",
        sub_type="3x3",
        field_goals_made=3,
        field_goals_attempted=6,
        points=12,
    )
    three_x_three_result = process_match_performance(three_x_three, player_position="ala")

    assert futsal_result.xp_gains.get("agility", 0) >= futsal_base_result.xp_gains.get("agility", 0)
    assert futsal_result.xp_gains.get("ball_control", 0) >= futsal_base_result.xp_gains.get("ball_control", 0)
    assert three_x_three_result.xp_gains.get("shoot_long", 0) >= three_x_three_base_result.xp_gains.get("shoot_long", 0)


def test_xp_divisor_is_fixed_at_sixty() -> None:
    performance = MatchPerformance(
        user_id="user-noob",
        sport_type="football",
        goals=6,
        assists=6,
        tackles=12,
        dribbles=12,
    )

    result_low_overall = process_match_performance(performance, player_position="meia", player_overall=59)
    result_standard = process_match_performance(performance, player_position="meia", player_overall=60)

    assert _resolve_xp_per_level(59) == 60
    assert _resolve_xp_per_level(60) == 60
    assert sum(result_low_overall.level_gains.values()) == sum(result_standard.level_gains.values())


def test_process_match_performance_applies_synergy_multiplier() -> None:
    performance = MatchPerformance(
        user_id="user-synergy",
        sport_type="football",
        goals=2,
        assists=1,
        tackles=3,
        dribbles=4,
    )

    baseline = process_match_performance(performance, player_position="meia", xp_multiplier=1.0)
    boosted = process_match_performance(performance, player_position="meia", xp_multiplier=1.05)

    assert sum(boosted.xp_gains.values()) >= sum(baseline.xp_gains.values())
    assert boosted.xp_gains.get("shooting", 0) >= baseline.xp_gains.get("shooting", 0)
