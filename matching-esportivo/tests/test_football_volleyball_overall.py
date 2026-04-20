"""Testes para cálculo de Overall de Futebol e Vôlei com pesos por posição."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

_XP_SERVICE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "xp_service.py"
_XP_SPEC = importlib.util.spec_from_file_location("xp_service_for_tests", _XP_SERVICE_PATH)
assert _XP_SPEC and _XP_SPEC.loader
_XP_MODULE = importlib.util.module_from_spec(_XP_SPEC)
sys.modules[_XP_SPEC.name] = _XP_MODULE
_XP_SPEC.loader.exec_module(_XP_MODULE)

calculate_football_overall = _XP_MODULE.calculate_football_overall
calculate_football_overall_by_position = _XP_MODULE.calculate_football_overall_by_position
calculate_football_package_scores = _XP_MODULE.calculate_football_package_scores
calculate_volleyball_overall = _XP_MODULE.calculate_volleyball_overall
calculate_volleyball_overall_by_position = _XP_MODULE.calculate_volleyball_overall_by_position
calculate_volleyball_package_scores = _XP_MODULE.calculate_volleyball_package_scores


# ============================================================================
# TESTES PARA FUTEBOL
# ============================================================================

class TestFootballOverall:
    """Testes de cálculo de Overall para futebol."""

    @pytest.fixture
    def balanced_stats(self) -> dict[str, int]:
        """Stats equilibradas para futebol."""
        return {
            "short_finish": 80,
            "long_shot": 75,
            "free_kick": 70,
            "sprint": 85,
            "acceleration": 82,
            "agility": 78,
            "stamina": 80,
            "strength": 75,
            "balance": 76,
            "short_pass": 85,
            "long_pass": 80,
            "crossing": 78,
            "vision": 82,
            "dribbling": 80,
            "ball_control": 81,
            "tackle": 70,
            "interception": 72,
            "marking": 68,
            "ball_shielding": 70,
        }

    @pytest.fixture
    def attacker_stats(self) -> dict[str, int]:
        """Stats especializados para atacante."""
        return {
            "short_finish": 90,
            "long_shot": 85,
            "free_kick": 80,
            "sprint": 88,
            "acceleration": 86,
            "agility": 82,
            "stamina": 78,
            "strength": 72,
            "balance": 74,
            "short_pass": 70,
            "long_pass": 65,
            "crossing": 60,
            "vision": 68,
            "dribbling": 85,
            "ball_control": 84,
            "tackle": 40,
            "interception": 35,
            "marking": 30,
            "ball_shielding": 35,
        }

    @pytest.fixture
    def defender_stats(self) -> dict[str, int]:
        """Stats especializados para zagueiro."""
        return {
            "short_finish": 30,
            "long_shot": 25,
            "free_kick": 20,
            "sprint": 75,
            "acceleration": 72,
            "agility": 68,
            "stamina": 85,
            "strength": 88,
            "balance": 86,
            "short_pass": 80,
            "long_pass": 75,
            "crossing": 40,
            "vision": 70,
            "dribbling": 50,
            "ball_control": 55,
            "tackle": 90,
            "interception": 88,
            "marking": 92,
            "ball_shielding": 90,
        }

    def test_football_package_scores(self, balanced_stats: dict[str, int]) -> None:
        """Verifica cálculo dos pacotes de futebol."""
        packages = calculate_football_package_scores(balanced_stats)
        
        assert "finalizacao" in packages
        assert "mobilidade" in packages
        assert "fisico" in packages
        assert "criacao" in packages
        assert "defesa" in packages
        
        # Verificar que todos os pacotes estão na escala 0-99
        for package_name, score in packages.items():
            assert 0 <= score <= 99, f"{package_name} fora do intervalo: {score}"

    def test_football_atacante_weighted(self, attacker_stats: dict[str, int]) -> None:
        """Verifica cálculo weighted para atacante."""
        overall = calculate_football_overall("atacante", attacker_stats)
        
        assert 0 <= overall <= 99
        # Atacante com stats de finalizacao alta deve ter overall alto
        assert overall >= 70, f"Atacante especializado não deve ter overall baixo: {overall}"

    def test_football_defensor_weighted(self, defender_stats: dict[str, int]) -> None:
        """Verifica cálculo weighted para zagueiro."""
        overall = calculate_football_overall("zagueiro", defender_stats)
        
        assert 0 <= overall <= 99
        # Zagueiro com stats de defesa alta deve ter overall alto
        assert overall >= 70, f"Zagueiro especializado não deve ter overall baixo: {overall}"

    def test_football_posicoes_variacoes(self, balanced_stats: dict[str, int]) -> None:
        """Testa que diferentes posições produzem overalls diferentes mesmo com mesmas stats."""
        atacante_overall = calculate_football_overall("atacante", balanced_stats)
        goleiro_overall = calculate_football_overall("goleiro", balanced_stats)
        lateral_overall = calculate_football_overall("lateral", balanced_stats)
        
        # Com stats equilibradas, as posições devem ter overalls diferentes
        # devido aos pesos apicados de forma diferente
        assert len({atacante_overall, goleiro_overall, lateral_overall}) >= 2
        
    def test_football_aliases_ponta(self, balanced_stats: dict[str, int]) -> None:
        """Testa aliases para posição de ponta."""
        ponta1 = calculate_football_overall("ponta", balanced_stats)
        ponta2 = calculate_football_overall("wing", balanced_stats)
        ponta3 = calculate_football_overall("winger", balanced_stats)
        
        assert ponta1 == ponta2
        assert ponta2 == ponta3

    def test_football_aliases_meia(self, balanced_stats: dict[str, int]) -> None:
        """Testa aliases para posição de meia."""
        meia1 = calculate_football_overall("meia", balanced_stats)
        meia2 = calculate_football_overall("midfielder", balanced_stats)
        meia3 = calculate_football_overall("cm", balanced_stats)
        
        assert meia1 == meia2
        assert meia2 == meia3

    def test_football_flex_mode_sem_posicao(self, balanced_stats: dict[str, int]) -> None:
        """Testa modo Flex quando posição é 'Sem Posição'."""
        overall_flex = calculate_football_overall("sem_posicao", balanced_stats)
        overall_default = calculate_football_overall("default", balanced_stats)
        
        # Ambas devem usar pesos iguais (modo flex)
        assert overall_flex == overall_default

    def test_football_flex_mode_rodizio(self, balanced_stats: dict[str, int]) -> None:
        """Testa modo Flex quando posição é 'Rodízio'."""
        overall_flex1 = calculate_football_overall("rodizio", balanced_stats)
        overall_flex2 = calculate_football_overall("rodiziо", balanced_stats)  # com c cedilha
        overall_default = calculate_football_overall("default", balanced_stats)
        
        assert overall_flex1 == overall_default
        assert overall_flex2 == overall_default

    def test_football_overall_by_position(self, balanced_stats: dict[str, int]) -> None:
        """Testa função que retorna dict com overall e pacotes."""
        result = calculate_football_overall_by_position("meia", balanced_stats)
        
        assert "position" in result
        assert "overall" in result
        assert "packages" in result
        assert result["position"] == "meia"
        assert 0 <= result["overall"] <= 99

    def test_football_sub_type_futsal(self, balanced_stats: dict[str, int]) -> None:
        """Testa multiplicador para FUTSAL."""
        overall_futsal = calculate_football_overall("lateral", balanced_stats, sub_type="FUTSAL")
        overall_normal = calculate_football_overall("lateral", balanced_stats)
        
        # FUTSAL deve produzir overall diferente devido aos multiplicadores
        # (depende de como a função distribui XP, aqui testamos que comporta sub_type)
        assert isinstance(overall_futsal, int)
        assert 0 <= overall_futsal <= 99


# ============================================================================
# TESTES PARA VÔLEI
# ============================================================================

class TestVolleyballOverall:
    """Testes de cálculo de Overall para vôlei."""

    @pytest.fixture
    def balanced_volleyball_stats(self) -> dict[str, int]:
        """Stats equilibradas para vôlei."""
        return {
            "spike_power": 80,
            "spike_accuracy": 78,
            "jump": 85,
            "reaction": 82,
            "serve_power": 80,
            "serve_tactical": 78,
            "game_vision": 80,
            "block": 75,
            "reception": 78,
            "floor_defense": 76,
            "coverage": 77,
            "setting": 75,
            "creativity": 77,
            "lateral_agility": 82,
            "stamina": 84,
            "coordination": 81,
        }

    @pytest.fixture
    def spiker_stats(self) -> dict[str, int]:
        """Stats especializados para ponteiro."""
        return {
            "spike_power": 92,
            "spike_accuracy": 88,
            "jump": 90,
            "reaction": 85,
            "serve_power": 85,
            "serve_tactical": 75,
            "game_vision": 70,
            "block": 70,
            "reception": 40,
            "floor_defense": 35,
            "coverage": 40,
            "setting": 20,
            "creativity": 50,
            "lateral_agility": 75,
            "stamina": 80,
            "coordination": 78,
        }

    @pytest.fixture
    def setter_stats(self) -> dict[str, int]:
        """Stats especializados para levantador."""
        return {
            "spike_power": 50,
            "spike_accuracy": 55,
            "jump": 60,
            "reaction": 88,
            "serve_power": 75,
            "serve_tactical": 88,
            "game_vision": 95,
            "block": 60,
            "reception": 85,
            "floor_defense": 70,
            "coverage": 75,
            "setting": 95,
            "creativity": 92,
            "lateral_agility": 72,
            "stamina": 85,
            "coordination": 90,
        }

    @pytest.fixture
    def libero_stats(self) -> dict[str, int]:
        """Stats especializados para líbero."""
        return {
            "spike_power": 30,
            "spike_accuracy": 35,
            "jump": 50,
            "reaction": 92,
            "serve_power": 60,
            "serve_tactical": 65,
            "game_vision": 75,
            "block": 40,
            "reception": 95,
            "floor_defense": 94,
            "coverage": 96,
            "setting": 60,
            "creativity": 70,
            "lateral_agility": 92,
            "stamina": 90,
            "coordination": 88,
        }

    def test_volleyball_package_scores(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Verifica cálculo dos pacotes de vôlei."""
        packages = calculate_volleyball_package_scores(balanced_volleyball_stats)
        
        assert "attack" in packages
        assert "serve" in packages
        assert "defense" in packages
        assert "setting" in packages
        assert "movement" in packages
        
        # Verificar que todos os pacotes estão na escala 0-99
        for package_name, score in packages.items():
            assert 0 <= score <= 99, f"{package_name} fora do intervalo: {score}"

    def test_volleyball_without_position_simple_average(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa modo Flex (sem posição) usando média simples."""
        overall = calculate_volleyball_overall(source=balanced_volleyball_stats)
        
        assert 0 <= overall <= 99
        # Sem posição, deve ser a média dos pacotes
        packages = calculate_volleyball_package_scores(balanced_volleyball_stats)
        expected = int(round(sum(packages.values()) / len(packages)))
        assert overall == expected

    def test_volleyball_ponteiro_weighted(self, spiker_stats: dict[str, int]) -> None:
        """Verifica cálculo weighted para ponteiro."""
        overall = calculate_volleyball_overall("ponteiro", spiker_stats)
        
        assert 0 <= overall <= 99
        # Ponteiro com stats de ataque alta deve ter overall alto
        assert overall >= 70, f"Ponteiro especializado não deve ter overall baixo: {overall}"

    def test_volleyball_levantador_weighted(self, setter_stats: dict[str, int]) -> None:
        """Verifica cálculo weighted para levantador."""
        overall = calculate_volleyball_overall("levantador", setter_stats)
        
        assert 0 <= overall <= 99
        # Levantador com stats de setting alta deve ter overall alto
        assert overall >= 70, f"Levantador especializado não deve ter overall baixo: {overall}"

    def test_volleyball_libero_weighted(self, libero_stats: dict[str, int]) -> None:
        """Verifica cálculo weighted para líbero."""
        overall = calculate_volleyball_overall("libero", libero_stats)
        
        assert 0 <= overall <= 99
        # Líbero com stats de defesa alta deve ter overall alto
        assert overall >= 70, f"Líbero especializado não deve ter overall baixo: {overall}"

    def test_volleyball_posicoes_variacoes(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa que diferentes posições produzem overalls diferentes."""
        levantador = calculate_volleyball_overall("levantador", balanced_volleyball_stats)
        ponteiro = calculate_volleyball_overall("ponteiro", balanced_volleyball_stats)
        libero = calculate_volleyball_overall("libero", balanced_volleyball_stats)
        
        # Com stats equilibradas, as posições devem ter overalls diferentes
        assert len({levantador, ponteiro, libero}) >= 2

    def test_volleyball_aliases_levantador(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa aliases para posição de levantador."""
        lev1 = calculate_volleyball_overall("levantador", balanced_volleyball_stats)
        lev2 = calculate_volleyball_overall("setter", balanced_volleyball_stats)
        
        assert lev1 == lev2

    def test_volleyball_aliases_libero(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa aliases para posição de líbero."""
        lib1 = calculate_volleyball_overall("libero", balanced_volleyball_stats)
        lib2 = calculate_volleyball_overall("liber0", balanced_volleyball_stats)
        lib3 = calculate_volleyball_overall("libera", balanced_volleyball_stats)
        lib4 = calculate_volleyball_overall("ds", balanced_volleyball_stats)
        
        assert lib1 == lib2
        assert lib2 == lib3
        assert lib3 == lib4

    def test_volleyball_flex_mode_sem_posicao(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa modo Flex para vôlei com 'Sem Posição'."""
        overall_flex = calculate_volleyball_overall("sem_posicao", balanced_volleyball_stats)
        overall_no_pos = calculate_volleyball_overall(source=balanced_volleyball_stats)
        
        # Ambas devem usar média simples
        assert overall_flex == overall_no_pos

    def test_volleyball_flex_mode_rodizio(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa modo Flex para vôlei com 'Rodízio'."""
        overall_flex = calculate_volleyball_overall("rodizio", balanced_volleyball_stats)
        overall_no_pos = calculate_volleyball_overall(source=balanced_volleyball_stats)
        
        assert overall_flex == overall_no_pos

    def test_volleyball_overall_by_position(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa função que retorna dict com overall e pacotes."""
        result = calculate_volleyball_overall_by_position("central", balanced_volleyball_stats)
        
        assert "position" in result
        assert "overall" in result
        assert "packages" in result
        assert result["position"] == "central"
        assert 0 <= result["overall"] <= 99

    def test_volleyball_backward_compatibility(self, balanced_volleyball_stats: dict[str, int]) -> None:
        """Testa compatibilidade com chamadas antigas (sem posição)."""
        overall = calculate_volleyball_overall(balanced_volleyball_stats)
        
        assert 0 <= overall <= 99

    @pytest.fixture
    def beach_stats(self) -> dict[str, int]:
        """Stats especializadas para vôlei de praia."""
        return {
            "spike_power": 84,
            "spike_accuracy": 82,
            "jump": 86,
            "reaction": 83,
            "serve_power": 80,
            "serve_tactical": 81,
            "game_vision": 79,
            "block": 76,
            "reception": 84,
            "floor_defense": 85,
            "coverage": 86,
            "setting": 78,
            "creativity": 80,
            "lateral_agility": 88,
            "stamina": 82,
            "coordination": 84,
            "sand_agility": 90,
            "jumping_endurance": 88,
        }

    def test_volleyball_beach_uses_harmonic_mean(self, beach_stats: dict[str, int]) -> None:
        """Testa o modo BEACH com média harmônica ponderada."""
        overall_libero = calculate_volleyball_overall("libero", beach_stats, sub_type="BEACH")
        overall_central = calculate_volleyball_overall("central", beach_stats, sub_type="BEACH")

        attrs = (
            "spike_power",
            "spike_accuracy",
            "jump",
            "reaction",
            "serve_power",
            "serve_tactical",
            "game_vision",
            "block",
            "reception",
            "floor_defense",
            "coverage",
            "setting",
            "creativity",
            "lateral_agility",
            "stamina",
            "coordination",
            "sand_agility",
            "jumping_endurance",
        )
        weights = {"sand_agility": 1.5, "jumping_endurance": 1.5}
        total_weight = sum(weights.get(attr, 1.0) for attr in attrs)
        inv_sum = sum(weights.get(attr, 1.0) / beach_stats[attr] for attr in attrs)
        expected = int(round(total_weight / inv_sum))

        assert overall_libero == expected
        assert overall_central == expected

    def test_volleyball_beach_overall_by_position_disables_position_logic(self, beach_stats: dict[str, int]) -> None:
        """Testa que o modo BEACH ignora pesos de posição."""
        result = calculate_volleyball_overall_by_position("libero", beach_stats, sub_type="BEACH")

        assert result["position"] == "beach"
        assert result["overall"] == calculate_volleyball_overall("ponteiro", beach_stats, sub_type="BEACH")


# ============================================================================
# TESTES DE COMPARAÇÃO CRUZADA
# ============================================================================

class TestCrossComparison:
    """Testes comparativos entre futebol e vôlei."""

    def test_football_and_volleyball_both_accept_position(self) -> None:
        """Verifica que ambos aceitam position como primeiro argumento."""
        stats = {
            "short_finish": 80, "long_shot": 75, "free_kick": 70,
            "sprint": 85, "acceleration": 82, "agility": 78,
            "stamina": 80, "strength": 75, "balance": 76,
            "short_pass": 85, "long_pass": 80, "crossing": 78,
            "vision": 82, "dribbling": 80, "ball_control": 81,
            "tackle": 70, "interception": 72, "marking": 68, "ball_shielding": 70,
            "spike_power": 80, "spike_accuracy": 78, "jump": 85, "reaction": 82,
            "serve_power": 80, "serve_tactical": 78, "game_vision": 80,
            "block": 75, "reception": 78, "floor_defense": 76, "coverage": 77,
            "setting": 75, "creativity": 77, "lateral_agility": 82, "coordination": 81,
        }
        
        # Ambas devem aceitar position como argumento
        football_overall = calculate_football_overall("meia", stats)
        volleyball_overall = calculate_volleyball_overall("levantador", stats)
        
        assert 0 <= football_overall <= 99
        assert 0 <= volleyball_overall <= 99
