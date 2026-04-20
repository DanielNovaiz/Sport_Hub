"""Tests para ranked service."""

from app.services.ranked_service import calculate_mmr_change


def test_calculate_mmr_change_winner_gains_mmr():
    """Winner deve ganhar MMR."""
    delta = calculate_mmr_change(
        winner=True,
        winner_overall=90,
        winner_mmr=1000,
        loser_mmr=900,
    )
    assert delta > 0, "Winner should gain positive MMR"
    assert delta <= 50, "MMR change should be bounded"


def test_calculate_mmr_change_loser_loses_mmr():
    """Loser deve perder MMR."""
    delta = calculate_mmr_change(
        winner=False,
        winner_overall=90,
        winner_mmr=1000,
        loser_mmr=900,
    )
    assert delta < 0, "Loser should lose negative MMR"
    assert delta >= -50, "MMR change should be bounded"


def test_calculate_mmr_change_respects_overall_multiplier():
    """Overall multiplier deve afetar delta MMR."""
    delta_high_overall = calculate_mmr_change(
        winner=True,
        winner_overall=95,
        winner_mmr=1000,
        loser_mmr=1000,
    )
    delta_low_overall = calculate_mmr_change(
        winner=True,
        winner_overall=50,
        winner_mmr=1000,
        loser_mmr=1000,
    )
    assert delta_high_overall > delta_low_overall, "Higher overall should yield more MMR"


def test_calculate_mmr_change_is_symmetric():
    """Delta do vencedor deve ser oposto ao do perdedor."""
    delta_winner = calculate_mmr_change(
        winner=True,
        winner_overall=80,
        winner_mmr=1100,
        loser_mmr=900,
    )
    delta_loser = calculate_mmr_change(
        winner=False,
        winner_overall=80,
        winner_mmr=900,  # swapped
        loser_mmr=1100,  # swapped
    )
    # Não serão exatos negações por causa da ELO assimetria, mas devem estar próximos
    assert abs(delta_winner + delta_loser) <= 5, "Winner and loser deltas should be roughly opposite"


def test_calculate_mmr_change_bounds_mmr():
    """MMR delta não deve exceder bounds."""
    for winner in [True, False]:
        for overall in [20, 50, 80, 99]:
            for mmr_diff in [-500, -100, 0, 100, 500]:
                delta = calculate_mmr_change(
                    winner=winner,
                    winner_overall=overall,
                    winner_mmr=1000 + mmr_diff,
                    loser_mmr=1000,
                )
                assert -100 <= delta <= 100, f"Delta {delta} out of bounds for overall={overall}, mmr_diff={mmr_diff}"

