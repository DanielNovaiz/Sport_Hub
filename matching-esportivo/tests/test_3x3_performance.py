"""Testes para process_3x3_performance() - Basquete 3x3 Box Score Conversion."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Resolver importação do pacote app no workspace local.
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from app.services.xp_service import process_3x3_performance


class MockPerformance:
    """Mock de MatchPerformance para testes sem dependência SQLModel."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", str(uuid4()))
        self.user_id = kwargs.get("user_id", "user_123")
        self.event_id = kwargs.get("event_id", None)
        self.sport_type = kwargs.get("sport_type", "basketball")
        self.sub_type = kwargs.get("sub_type", "3x3")
        self.goals = kwargs.get("goals", 0)
        self.assists = kwargs.get("assists", 0)
        self.points = kwargs.get("points", 0)
        self.rebounds = kwargs.get("rebounds", 0)
        self.field_goals_made = kwargs.get("field_goals_made", 0)
        self.field_goals_attempted = kwargs.get("field_goals_attempted", 0)
        self.steals = kwargs.get("steals", 0)
        self.blocks = kwargs.get("blocks", 0)
        self.tackles = kwargs.get("tackles", 0)
        self.dribbles = kwargs.get("dribbles", 0)
        self.aces = kwargs.get("aces", 0)
        self.attacks = kwargs.get("attacks", 0)
        self.defenses = kwargs.get("defenses", 0)
        self.sets = kwargs.get("sets", 0)
        self.two_point_makes = kwargs.get("two_point_makes", 0)
        self.clutch_rebounds = kwargs.get("clutch_rebounds", 0)
        self.last_minute_timestamp_sec = kwargs.get("last_minute_timestamp_sec", None)
        self.created_at = kwargs.get("created_at", datetime.now(UTC))


def _expected_components(perf: MockPerformance) -> tuple[int, int, int, int]:
    """Calcula expectativa exatamente como o serviço implementa hoje."""
    base_xp = (
        (perf.points - perf.two_point_makes * 2) * 3
        + perf.two_point_makes * 2 * 2
        + perf.assists * 10
        + perf.rebounds * 4
        + perf.steals * 8
        + perf.blocks * 6
    )
    two_point_bonus_xp = int(perf.two_point_makes * 2 * (2.5 - 1.0))
    clutch_ratio_denominator = max(1, perf.two_point_makes + perf.rebounds)
    clutch_bonus_xp = int(
        (base_xp + two_point_bonus_xp)
        * 0.5
        * (perf.clutch_rebounds / clutch_ratio_denominator)
    )
    if perf.rebounds == 0:
        clutch_bonus_xp = 0
    total_xp = base_xp + two_point_bonus_xp + clutch_bonus_xp
    return base_xp, two_point_bonus_xp, clutch_bonus_xp, total_xp


def test_non_3x3_performance():
    """Quando não for basquete 3x3, deve retornar XP zerado."""
    perf = MockPerformance(sport_type="football", sub_type="society", points=10, assists=4)
    result = process_3x3_performance(perf)

    assert result["base_xp"] == 0
    assert result["two_point_multiplier"] == 1.0
    assert result["two_point_bonus_xp"] == 0
    assert result["clutch_bonus_xp"] == 0
    assert result["total_xp"] == 0
    assert "não é de Basquete 3x3" in result["details"]


def test_only_base_xp_no_bonuses():
    """Sem 2-pontos e sem clutch, total deve ser só base XP."""
    perf = MockPerformance(
        sport_type="basketball",
        sub_type="3x3",
        points=10,
        assists=3,
        rebounds=3,
        steals=1,
        blocks=0,
        two_point_makes=0,
        clutch_rebounds=0,
    )
    result = process_3x3_performance(perf)
    base_expected, two_point_bonus_expected, clutch_bonus_expected, total_expected = _expected_components(perf)

    assert result["base_xp"] == base_expected
    assert result["two_point_bonus_xp"] == two_point_bonus_expected == 0
    assert result["clutch_bonus_xp"] == clutch_bonus_expected == 0
    assert result["total_xp"] == total_expected == base_expected


def test_two_point_makes_2_5x_multiplier():
    """Cestas de 2-pontos devem receber bônus com multiplicador 2.5x."""
    perf = MockPerformance(
        sport_type="basketball",
        sub_type="3x3",
        points=6,
        assists=0,
        rebounds=1,
        steals=0,
        blocks=0,
        two_point_makes=1,
        clutch_rebounds=0,
    )
    result = process_3x3_performance(perf)
    base_expected, two_point_bonus_expected, clutch_bonus_expected, total_expected = _expected_components(perf)

    assert result["two_point_multiplier"] == 2.5
    assert result["base_xp"] == base_expected
    assert result["two_point_bonus_xp"] == two_point_bonus_expected
    assert result["clutch_bonus_xp"] == clutch_bonus_expected == 0
    assert result["total_xp"] == total_expected


def test_clutch_rebound_50_percent_bonus():
    """Clutch rebounds devem aplicar bônus proporcional na regra atual."""
    perf = MockPerformance(
        sport_type="basketball",
        sub_type="3x3",
        points=10,
        assists=2,
        rebounds=3,
        steals=0,
        blocks=0,
        two_point_makes=0,
        clutch_rebounds=3,
    )
    result = process_3x3_performance(perf)
    base_expected, two_point_bonus_expected, clutch_bonus_expected, total_expected = _expected_components(perf)

    assert result["base_xp"] == base_expected
    assert result["two_point_bonus_xp"] == two_point_bonus_expected
    assert result["clutch_bonus_xp"] == clutch_bonus_expected
    assert result["total_xp"] == total_expected


def test_mixed_performance_all_bonuses():
    """Performance com 2-pontos e clutch rebounds simultâneos."""
    perf = MockPerformance(
        sport_type="basketball",
        sub_type="3x3",
        points=12,
        assists=3,
        rebounds=5,
        steals=2,
        blocks=1,
        two_point_makes=2,
        clutch_rebounds=3,
    )
    result = process_3x3_performance(perf)
    base_expected, two_point_bonus_expected, clutch_bonus_expected, total_expected = _expected_components(perf)

    assert result["base_xp"] == base_expected
    assert result["two_point_bonus_xp"] == two_point_bonus_expected
    assert result["clutch_bonus_xp"] == clutch_bonus_expected
    assert result["total_xp"] == total_expected


def test_partial_clutch_rebounds():
    """Quando só parte dos rebotes é clutch, bônus deve ser proporcional."""
    perf = MockPerformance(
        sport_type="basketball",
        sub_type="3x3",
        points=10,
        assists=1,
        rebounds=10,
        steals=0,
        blocks=0,
        two_point_makes=0,
        clutch_rebounds=2,
    )
    result = process_3x3_performance(perf)
    _, _, clutch_bonus_expected, total_expected = _expected_components(perf)

    assert result["clutch_bonus_xp"] == clutch_bonus_expected
    assert result["total_xp"] == total_expected


def test_no_rebounds_no_clutch_bonus():
    """Sem rebotes totais, clutch bonus deve ser zero por regra explícita."""
    perf = MockPerformance(
        sport_type="basketball",
        sub_type="3x3",
        points=15,
        assists=4,
        rebounds=0,
        steals=0,
        blocks=0,
        two_point_makes=0,
        clutch_rebounds=3,
    )
    result = process_3x3_performance(perf)
    base_expected, _, clutch_bonus_expected, total_expected = _expected_components(perf)

    assert result["base_xp"] == base_expected
    assert clutch_bonus_expected == 0
    assert result["clutch_bonus_xp"] == 0
    assert result["total_xp"] == total_expected
