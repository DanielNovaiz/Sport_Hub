"""Motor de progressão, overall por posição e conquistas por performance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from contextlib import nullcontext
import importlib.util
import logging
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stats import MatchPerformance, PlayerStats
from app.models.player_stats import UserAchievement, UserXP
from app.services.xp_constants import ALL_PROGRESS_ATTRIBUTES
from app.services.overall_engine import OverallRequest, calculate_overall_async
from app.services.maintenance_service import sync_user_prestige_entries
from app.repositories import StructuredTelemetryRepository, SqlAlchemyXpRepository
from app.repositories.xp_repository import AchievementTriggerLike

logger = logging.getLogger(__name__)

_CALCULATIONS_MODULE = None

XP_PER_LEVEL = 60
MAX_LEVEL_GAIN_PER_MATCH = 3
MAX_XP_APPLIED_PER_MATCH = XP_PER_LEVEL * MAX_LEVEL_GAIN_PER_MATCH

BASKETBALL_PACKAGES: dict[str, tuple[str, ...]] = {
    "finalizacao": ("shoot_long", "shoot_mid", "shoot_short", "finishing"),
    "fisico": ("velocity", "jump", "agility", "energy", "strength", "balance"),
    "armacao": ("passing", "ball_control", "vision", "dribble"),
    "defesa": ("steal", "block", "perim_def", "post_def"),
    "rebote": ("rebound", "reb_predict", "combativeness"),
}

BASKETBALL_PACKAGE_SPLITS: dict[str, dict[str, float]] = {
    "finalizacao": {
        "shoot_long": 0.20,
        "shoot_mid": 0.30,
        "shoot_short": 0.30,
        "finishing": 0.20,
    },
    "fisico": {
        "velocity": 0.15,
        "jump": 0.15,
        "agility": 0.15,
        "energy": 0.20,
        "strength": 0.20,
        "balance": 0.15,
    },
    "armacao": {
        "passing": 0.30,
        "ball_control": 0.30,
        "vision": 0.20,
        "dribble": 0.20,
    },
    "defesa": {
        "steal": 0.25,
        "block": 0.25,
        "perim_def": 0.25,
        "post_def": 0.25,
    },
    "rebote": {
        "rebound": 0.40,
        "reb_predict": 0.30,
        "combativeness": 0.30,
    },
}

BASKETBALL_POSITION_WEIGHTS: dict[str, dict[str, float]] = {
    "armador": {
        "finalizacao": 2.0,
        "fisico": 1.0,
        "armacao": 3.0,
        "defesa": 1.0,
        "rebote": 1.0,
    },
    "ala": {
        "finalizacao": 2.5,
        "fisico": 2.0,
        "armacao": 1.5,
        "defesa": 2.0,
        "rebote": 1.0,
    },
    "pivo": {
        "finalizacao": 1.0,
        "fisico": 2.0,
        "armacao": 0.5,
        "defesa": 3.0,
        "rebote": 4.0,
    },
    "default": {
        "finalizacao": 1.0,
        "fisico": 1.0,
        "armacao": 1.0,
        "defesa": 1.0,
        "rebote": 1.0,
    },
}

BASKETBALL_POSITION_ALIASES: dict[str, str] = {
    "armador": "armador",
    "point_guard": "armador",
    "pg": "armador",
    "ala": "ala",
    "wing": "ala",
    "sg": "ala",
    "pivo": "pivo",
    "pivô": "pivo",
    "center": "pivo",
    "center_basket": "pivo",
    "c": "pivo",
}

FOOTBALL_PACKAGES: dict[str, tuple[str, ...]] = {
    "finalizacao": ("short_finish", "long_shot", "free_kick"),
    "mobilidade": ("sprint", "acceleration", "agility"),
    "fisico": ("stamina", "strength", "balance"),
    "criacao": ("short_pass", "long_pass", "crossing", "vision", "dribbling", "ball_control"),
    "defesa": ("tackle", "interception", "marking", "ball_shielding"),
}

FOOTBALL_POSITION_WEIGHTS: dict[str, dict[str, float]] = {
    "atacante": {
        "finalizacao": 3.0,
        "mobilidade": 2.0,
        "fisico": 1.5,
        "criacao": 0.8,
        "defesa": 0.7,
    },
    "ponta": {
        "finalizacao": 2.5,
        "mobilidade": 3.0,
        "fisico": 2.0,
        "criacao": 1.2,
        "defesa": 0.2,
    },
    "lateral": {
        "finalizacao": 0.8,
        "mobilidade": 2.0,
        "fisico": 2.5,
        "criacao": 2.0,
        "defesa": 3.0,
    },
    "meia": {
        "finalizacao": 1.5,
        "mobilidade": 2.5,
        "fisico": 1.8,
        "criacao": 3.0,
        "defesa": 1.2,
    },
    "zagueiro": {
        "finalizacao": 0.5,
        "mobilidade": 1.5,
        "fisico": 2.5,
        "criacao": 1.0,
        "defesa": 3.5,
    },
    "goleiro": {
        "finalizacao": 0.0,
        "mobilidade": 1.0,
        "fisico": 2.5,
        "criacao": 0.5,
        "defesa": 3.5,
    },
    "default": {
        "finalizacao": 1.0,
        "mobilidade": 1.0,
        "fisico": 1.0,
        "criacao": 1.0,
        "defesa": 1.0,
    },
}

FOOTBALL_POSITION_ALIASES: dict[str, str] = {
    "atacante": "atacante",
    "forward": "atacante",
    "fw": "atacante",
    "st": "atacante",
    "ponta": "ponta",
    "wing": "ponta",
    "winger": "ponta",
    "rw": "ponta",
    "lw": "ponta",
    "lateral": "lateral",
    "back": "lateral",
    "fullback": "lateral",
    "rb": "lateral",
    "lb": "lateral",
    "meia": "meia",
    "midfielder": "meia",
    "cm": "meia",
    "cdm": "meia",
    "cam": "meia",
    "zagueiro": "zagueiro",
    "defender": "zagueiro",
    "cb": "zagueiro",
    "goleiro": "goleiro",
    "goleira": "goleiro",
    "goalkeeper": "goleiro",
    "gk": "goleiro",
    "portero": "goleiro",
    "sem_posicao": "default",
    "sem_posição": "default",
    "rodiziо": "default",
    "rodizio": "default",
}

VOLLEYBALL_POSITION_ALIASES: dict[str, str] = {
    "levantador": "levantador",
    "setter": "levantador",
    "ponteiro": "ponteiro",
    "wing_spiker": "ponteiro",
    "ws": "ponteiro",
    "central": "central",
    "middle_blocker": "central",
    "mb": "central",
    "oposto": "oposto",
    "opposite": "oposto",
    "op": "oposto",
    "libero": "libero",
    "liber0": "libero",
    "libera": "libero",
    "defensive_specialist": "libero",
    "ds": "libero",
    "sem_posicao": "default",
    "sem_posição": "default",
    "rodiziо": "default",
    "rodizio": "default",
}

VOLLEYBALL_BEACH_ATTRIBUTES: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            *tuple(attr for attrs in (
                ("spike_power", "spike_accuracy", "jump", "reaction"),
                ("serve_power", "serve_tactical", "game_vision"),
                ("block", "reception", "floor_defense", "coverage"),
                ("setting", "creativity", "game_vision"),
                ("lateral_agility", "reaction", "stamina", "coordination"),
            ) for attr in attrs),
            "sand_agility",
            "jumping_endurance",
        )
    )
)

VOLLEYBALL_BEACH_WEIGHTS: dict[str, float] = {
    "sand_agility": 1.5,
    "jumping_endurance": 1.5,
}

PROFILE_SPORT_ALIASES: dict[str, str] = {
    "basquete": "BASKETBALL",
    "basketball": "BASKETBALL",
    "football": "FOOTBALL",
    "futebol": "FOOTBALL",
    "volleyball": "VOLLEYBALL",
    "volei": "VOLLEYBALL",
    "vôlei": "VOLLEYBALL",
}


@dataclass(frozen=True)
class AchievementTrigger:
    """Resumo de uma conquista disparada por uma partida."""

    code: str
    title: str
    tier: str
    execution_bonus: int
    bonus_attributes: dict[str, int]


@dataclass(frozen=True)
class MatchXpResult:
    """Resultado bruto do processamento de XP de uma partida."""

    xp_gains: dict[str, int]
    level_gains: dict[str, int]
    residual_xp: dict[str, int]
    achievement_triggers: list[AchievementTrigger]
    fg_percentage: float
    telemetry_logs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PackageXpBreakdown:
    """XP distribuído por pacotes da modalidade."""

    package_xp: dict[str, int]
    attribute_xp: dict[str, int]


def _clamp_stat(value: int) -> int:
    return max(0, min(99, int(value)))


def _resolve_xp_per_level(overall: int | None) -> int:
    """Conversão atômica: 60 XP = 1 atributo."""
    return XP_PER_LEVEL


def _normalize_position(position: str | None) -> str:
    if not position:
        return "default"
    normalized = position.strip().lower().replace(" ", "_")
    if normalized == "midfielder":
        return "meia"
    return BASKETBALL_POSITION_ALIASES.get(normalized, normalized)


def _get_stat_value(source: PlayerStats | Mapping[str, int], name: str) -> int:
    if isinstance(source, Mapping):
        return _clamp_stat(source.get(name, 0) or 0)
    return _clamp_stat(getattr(source, name, 0) or 0)


def _format_achievement_bonus(bonus_attributes: Mapping[str, int]) -> str:
    if not bonus_attributes:
        return "none"
    return ", ".join(f"{attr}:{value}" for attr, value in sorted(bonus_attributes.items()))


def _build_xp_log(
    *,
    sport: str,
    user_id: str,
    action: str,
    attr: str,
    xp_value: int,
    residual: int,
    level_divisor: int,
) -> str:
    return (
        f"[XP_LOG][{sport}][{user_id}] Action: {action} | "
        f"Attribute: {attr} | XP Gained: {xp_value} | New Residual: {residual}/{level_divisor}."
    )


def _build_achievement_log(*, user_id: str, achievement_name: str, tier: str, bonus: str) -> str:
    return (
        f"[ACHIEVEMENT][{user_id}] Unlocked: {achievement_name} | "
        f"Tier: {tier} | Bonus Applied: {bonus}."
    )


def _package_average(source: PlayerStats | Mapping[str, int], attributes: tuple[str, ...]) -> int:
    if not attributes:
        return 0
    total = sum(_get_stat_value(source, attribute) for attribute in attributes)
    return int(round(total / len(attributes)))


def calculate_precise_overall(weighted_sum: float, divisor: float) -> float:
    """Calcula overall com precisão de 2 casas decimais antes da exibição."""
    safe_divisor = divisor if divisor else 1.0
    return round(weighted_sum / safe_divisor, 2)


def calculate_basketball_package_scores(source: PlayerStats | Mapping[str, int]) -> dict[str, int]:
    """Calcula os 5 pacotes do basquete em escala 0-99."""
    return {
        package_name: _package_average(source, attributes)
        for package_name, attributes in BASKETBALL_PACKAGES.items()
    }


def calculate_basketball_overall(position: str, source: PlayerStats | Mapping[str, int]) -> int:
    """Calcula Overall de basquete usando pesos por posição e divisor específico."""
    normalized_position = _normalize_position(position)
    package_scores = calculate_basketball_package_scores(source)
    weights = BASKETBALL_POSITION_WEIGHTS.get(normalized_position, BASKETBALL_POSITION_WEIGHTS["default"])
    divisor = sum(weights.values()) or 1.0
    weighted_sum = sum(package_scores[name] * weight for name, weight in weights.items())
    overall = int(round(calculate_precise_overall(weighted_sum, divisor)))
    return max(0, min(99, overall))


def calculate_basketball_overall_by_position(
    position: str,
    source: PlayerStats | Mapping[str, int],
) -> dict[str, Any]:
    """Retorna o overall e os pacotes para renderização no mobile."""
    return {
        "position": _normalize_position(position),
        "overall": calculate_basketball_overall(position, source),
        "packages": calculate_basketball_package_scores(source),
    }


def _normalize_football_position(position: str | None) -> str:
    """Normaliza posição para futebol."""
    if not position:
        return "default"
    normalized = position.strip().lower().replace(" ", "_")
    return FOOTBALL_POSITION_ALIASES.get(normalized, normalized)


def calculate_football_package_scores(source: PlayerStats | Mapping[str, int]) -> dict[str, int]:
    """Calcula os 5 pacotes do futebol em escala 0-99."""
    return {
        package_name: _package_average(source, attributes)
        for package_name, attributes in FOOTBALL_PACKAGES.items()
    }


def calculate_football_overall(position: str, source: PlayerStats | Mapping[str, int], sub_type: str | None = None) -> int:
    """Calcula Overall de futebol usando pesos por posição e aplica multiplicadores de sub_type.
    
    Args:
        position: Posição do jogador (atacante, ponta, lateral, meia, zagueiro, goleiro)
        source: Stats do jogador
        sub_type: Variação do jogo (futsal, society, field, etc)
        
    Multiplicadores (antes da média final):
        FUTSAL: agility 1.2x, ball_control 1.2x, stamina 0.8x
        SOCIETY: long_shot 1.1x, strength 1.1x
    """
    def _load_calculations_module() -> Any:
        global _CALCULATIONS_MODULE
        if _CALCULATIONS_MODULE is None:
            calculations_path = Path(__file__).resolve().with_name("calculations.py")
            spec = importlib.util.spec_from_file_location("app.services.calculations", calculations_path)
            if spec is None or spec.loader is None:
                raise ImportError("Unable to load app.services.calculations")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _CALCULATIONS_MODULE = module
        return _CALCULATIONS_MODULE

    apply_sub_type_multipliers = _load_calculations_module().apply_sub_type_multipliers
    
    normalized_position = _normalize_football_position(position)
    package_scores = calculate_football_package_scores(source)
    weights = FOOTBALL_POSITION_WEIGHTS.get(normalized_position, FOOTBALL_POSITION_WEIGHTS["default"])
    divisor = sum(weights.values()) or 1.0
    
    # Extrair atributos relevantes para multiplicadores
    relevant_attrs = {
        "agility": _get_stat_value(source, "agility"),
        "ball_control": _get_stat_value(source, "ball_control"),
        "stamina": _get_stat_value(source, "stamina"),
        "long_shot": _get_stat_value(source, "long_shot"),
        "strength": _get_stat_value(source, "strength"),
    }
    
    # Aplicar multiplicadores de sub_type
    adjusted_packages = apply_sub_type_multipliers(
        package_scores,
        relevant_attrs,
        sub_type=sub_type,
        sport_type="football",
    )
    
    # Usar scores ajustados para weighted_sum
    weighted_sum = sum(
        adjusted_packages.get(name, float(package_scores[name])) * weight
        for name, weight in weights.items()
    )
    
    overall = int(round(calculate_precise_overall(weighted_sum, divisor)))
    return max(0, min(99, overall))



def calculate_football_overall_by_position(
    position: str,
    source: PlayerStats | Mapping[str, int],
    sub_type: str | None = None,
) -> dict[str, Any]:
    """Retorna o overall e os pacotes para renderização no mobile."""
    return {
        "position": _normalize_football_position(position),
        "overall": calculate_football_overall(position, source, sub_type),
        "packages": calculate_football_package_scores(source),
    }


def _normalize_volleyball_position(position: str | None) -> str:
    """Normaliza posição para vôlei."""
    if not position:
        return "default"
    normalized = position.strip().lower().replace(" ", "_")
    return VOLLEYBALL_POSITION_ALIASES.get(normalized, normalized)


def _normalize_volleyball_sub_type(sub_type: str | None) -> str:
    if not sub_type:
        return ""
    return sub_type.strip().lower().replace(" ", "_")


VOLLEYBALL_PACKAGES: dict[str, tuple[str, ...]] = {
    "attack": ("spike_power", "spike_accuracy", "jump", "reaction"),
    "serve": ("serve_power", "serve_tactical", "game_vision"),
    "defense": ("block", "reception", "floor_defense", "coverage"),
    "setting": ("setting", "creativity", "game_vision"),
    "movement": ("lateral_agility", "reaction", "stamina", "coordination"),
}

VOLLEYBALL_POSITION_WEIGHTS: dict[str, dict[str, float]] = {
    "levantador": {
        "attack": 2.0,
        "serve": 2.0,
        "defense": 1.5,
        "setting": 3.5,
        "movement": 1.5,
    },
    "ponteiro": {
        "attack": 3.0,
        "serve": 2.5,
        "defense": 1.5,
        "setting": 0.5,
        "movement": 2.0,
    },
    "central": {
        "attack": 2.5,
        "serve": 1.5,
        "defense": 3.0,
        "setting": 1.0,
        "movement": 2.5,
    },
    "oposto": {
        "attack": 3.0,
        "serve": 2.0,
        "defense": 1.5,
        "setting": 0.5,
        "movement": 2.0,
    },
    "libero": {
        "attack": 0.5,
        "serve": 1.0,
        "defense": 3.5,
        "setting": 1.0,
        "movement": 3.0,
    },
    "default": {
        "attack": 1.0,
        "serve": 1.0,
        "defense": 1.0,
        "setting": 1.0,
        "movement": 1.0,
    },
}


def calculate_volleyball_package_scores(source: PlayerStats | Mapping[str, int]) -> dict[str, int]:
    """Calcula os 5 pacotes do vôlei em escala 0-99."""
    return {
        package_name: _package_average(source, attributes)
        for package_name, attributes in VOLLEYBALL_PACKAGES.items()
    }


def _weighted_harmonic_mean(source: PlayerStats | Mapping[str, int], attributes: tuple[str, ...]) -> int:
    total_weight = 0.0
    inverse_sum = 0.0

    for attribute in attributes:
        weight = VOLLEYBALL_BEACH_WEIGHTS.get(attribute, 1.0)
        value = _get_stat_value(source, attribute)

        if value <= 0:
            return 0

        total_weight += weight
        inverse_sum += weight / value

    if not total_weight or not inverse_sum:
        return 0

    return int(round(total_weight / inverse_sum))


def calculate_volleyball_overall(
    position: str | None = None,
    source: PlayerStats | Mapping[str, int] | None = None,
    sub_type: str | None = None,
    **kwargs,
) -> int:
    """Calcula Overall de vôlei usando pesos por posição.
    
    Suporta duas assinaturas:
    - calculate_volleyball_overall(source) - compatibilidade com código antigo
    - calculate_volleyball_overall(position, source) - nova versão com pesos
    """
    # Compatibilidade com código antigo que chama com apenas source
    if source is None and isinstance(position, (PlayerStats, dict)):
        source = position
        position = None
    
    if source is None:
        return 0

    normalized_sub_type = _normalize_volleyball_sub_type(sub_type)

    if normalized_sub_type == "beach":
        beach_overall = _weighted_harmonic_mean(source, VOLLEYBALL_BEACH_ATTRIBUTES)
        return max(0, min(99, beach_overall))
    
    package_scores = calculate_volleyball_package_scores(source)
    
    # Se não houver posição, usa média simples
    if not position:
        overall = int(round(calculate_precise_overall(sum(package_scores.values()), float(len(package_scores)))))
        return max(0, min(99, overall))
    
    # Com posição, usa pesos específicos
    normalized_position = _normalize_volleyball_position(position)
    weights = VOLLEYBALL_POSITION_WEIGHTS.get(normalized_position, VOLLEYBALL_POSITION_WEIGHTS["default"])
    divisor = sum(weights.values()) or 1.0
    weighted_sum = sum(package_scores[name] * weight for name, weight in weights.items())
    overall = int(round(calculate_precise_overall(weighted_sum, divisor)))
    return max(0, min(99, overall))


def calculate_volleyball_overall_by_position(
    position: str,
    source: PlayerStats | Mapping[str, int],
    sub_type: str | None = None,
) -> dict[str, Any]:
    """Retorna o overall e os pacotes para renderização no mobile."""
    normalized_sub_type = _normalize_volleyball_sub_type(sub_type)
    if normalized_sub_type == "beach":
        return {
            "position": "beach",
            "overall": calculate_volleyball_overall(position, source, sub_type=sub_type),
            "packages": calculate_volleyball_package_scores(source),
        }

    return {
        "position": _normalize_volleyball_position(position),
        "overall": calculate_volleyball_overall(position, source, sub_type=sub_type),
        "packages": calculate_volleyball_package_scores(source),
    }


def calculate_attribute_overall(position: str, source: PlayerStats | Mapping[str, int]) -> int:
    """Alias poliatleta para modelos antigos que ainda usam a matriz de 6 atributos."""
    from app.services.user_service import calculate_player_overall

    return calculate_player_overall(
        position=position,
        pace=_get_stat_value(source, "pace"),
        shooting=_get_stat_value(source, "shooting"),
        passing=_get_stat_value(source, "passing"),
        defense=_get_stat_value(source, "defense"),
        physical=_get_stat_value(source, "physical"),
        technique=_get_stat_value(source, "technique"),
    )


def _package_xp_to_attributes(package_xp: dict[str, int]) -> dict[str, int]:
    attribute_xp: dict[str, int] = {attribute: 0 for attribute in ALL_PROGRESS_ATTRIBUTES}
    for package_name, xp_value in package_xp.items():
        split = BASKETBALL_PACKAGE_SPLITS[package_name]
        for attribute_name, ratio in split.items():
            attribute_xp[attribute_name] += int(round(xp_value * ratio))
    return attribute_xp


def apply_multiplier(
    attribute_xp: dict[str, int],
    sport_type: str | None,
    sub_type: str | None,
) -> dict[str, int]:
    """Aplica multiplicadores de XP por variação (sub_type) antes da conversão em pontos."""
    adjusted = dict(attribute_xp)
    normalized_sub_type = (sub_type or "").strip().upper()
    normalized_sport = (sport_type or "").strip().upper()

    if normalized_sub_type == "FUTSAL" and normalized_sport in {"FOOTBALL", "FUTEBOL"}:
        adjusted["agility"] = int(adjusted.get("agility", 0) * 1.2)
        adjusted["ball_control"] = int(adjusted.get("ball_control", 0) * 1.2)
    elif normalized_sub_type == "3X3" and normalized_sport in {"BASKETBALL", "BASQUETE"}:
        adjusted["shoot_long"] = int(adjusted.get("shoot_long", 0) * 2.0)

    return adjusted


def process_3x3_performance(performance: MatchPerformance) -> dict[str, Any]:
    """Processa performance de Basquete 3x3 com multiplicadores específicos.
    
    Regras de conversão XP para 3x3:
    1. Cestas de 2pts (fora do arco): 2.5x mais XP em shoot_long vs cestas de 1pt
    2. Clutch rebounds (último minuto): +50% XP adicional
    
    Args:
        performance: MatchPerformance data com campos 3x3 preenchidos
        
    Returns:
        Dict com detalhes de XP aplicado: {
            "base_xp": int,
            "two_point_multiplier": float,
            "two_point_bonus_xp": int,
            "clutch_bonus_xp": int,
            "total_xp": int,
            "details": str
        }
    """
    sport_type = (performance.sport_type or "").strip().lower()
    sub_type = (performance.sub_type or "").strip().lower()
    
    if sport_type not in {"basquete", "basketball"} or sub_type != "3x3":
        return {
            "base_xp": 0,
            "two_point_multiplier": 1.0,
            "two_point_bonus_xp": 0,
            "clutch_bonus_xp": 0,
            "total_xp": 0,
            "details": "Performance não é de Basquete 3x3",
        }
    
    # ===== BASELINE XP =====
    # XP base de pontos normais e assists
    base_xp = (
        (performance.points - getattr(performance, "two_point_makes", 0) * 2) * 3 +
        getattr(performance, "two_point_makes", 0) * 2 * 2 +
        performance.assists * 10 +
        performance.rebounds * 4 +
        performance.steals * 8 +
        performance.blocks * 6
    )
    
    # ===== MULTIPLICADOR DE 2-PONTOS =====
    # Cestas de 2pts recebem 2.5x mais XP em shoot_long
    # Se tem 1-ponto: X XP
    # Se tem 2-pontos (fora do arco): 2.5 * X XP
    two_point_makes = getattr(performance, "two_point_makes", 0)
    two_point_multiplier = 2.5
    
    # XP base para cestas de 2 pontos = 2 * (multiplicador de pontos)
    # Baseline: 1 cesta de 2pts = 2 * 2 = 4 XP base
    # Com multiplicador: 4 * 2.5 = 10 XP (comparado com 1pt que seria 1 * 3 = 3)
    two_point_bonus_xp = int(two_point_makes * 2 * (two_point_multiplier - 1.0))
    
    # ===== BÔNUS DE CLUTCH REBOTE =====
    # Rebotes capturados no último minuto recebem +50% XP
    clutch_rebounds = getattr(performance, "clutch_rebounds", 0)
    clutch_bonus_xp = int((base_xp + two_point_bonus_xp) * 0.5 * (clutch_rebounds / max(1, two_point_makes + performance.rebounds)))
    
    # Se não há rebotes, clutch_bonus é 0
    if performance.rebounds == 0:
        clutch_bonus_xp = 0
    
    total_xp = base_xp + two_point_bonus_xp + clutch_bonus_xp
    
    details = (
        f"3x3 Box Score Conversion | "
        f"Base XP: {base_xp} | "
        f"2-Ponto Bonus ({two_point_multiplier}x): {two_point_bonus_xp} | "
        f"Clutch Rebounds (last minute): {clutch_rebounds} → +{clutch_bonus_xp} XP | "
        f"Total: {total_xp} XP"
    )
    
    logger.info(f"[3X3_XP] {details}")
    
    return {
        "base_xp": base_xp,
        "two_point_multiplier": two_point_multiplier,
        "two_point_bonus_xp": two_point_bonus_xp,
        "clutch_bonus_xp": clutch_bonus_xp,
        "total_xp": total_xp,
        "details": details,
    }

def _fg_percentage(performance: MatchPerformance) -> float:
    attempts = max(0, performance.field_goals_attempted)
    made = max(0, performance.field_goals_made)
    if attempts <= 0:
        return 0.0
    return (made / attempts) * 100.0


def _achievement_rules(performance: MatchPerformance, player_position: str | None = None) -> list[AchievementTrigger]:
    triggers: list[AchievementTrigger] = []
    sport_type = (performance.sport_type or "").strip().lower()
    normalized_position = (player_position or "").strip().lower().replace(" ", "_")

    if sport_type in {"futebol", "football"}:
        if performance.goals >= 3:
            triggers.append(
                AchievementTrigger(
                    code="hat_trick",
                    title="Hat-Trick",
                    tier="Ouro",
                    execution_bonus=1,
                    bonus_attributes={
                        "short_finish": 2,
                        "long_shot": 1,
                        "finishing": 2,
                    },
                )
            )

        if performance.assists >= 3:
            triggers.append(
                AchievementTrigger(
                    code="garcom_de_elite",
                    title="Garçom de Elite",
                    tier="Prata",
                    execution_bonus=1,
                    bonus_attributes={
                        "short_pass": 2,
                        "long_pass": 2,
                        "vision": 2,
                        "crossing": 1,
                    },
                )
            )

        if performance.tackles >= 7:
            triggers.append(
                AchievementTrigger(
                    code="cao_de_guarda",
                    title="Cão de Guarda",
                    tier="Prata",
                    execution_bonus=1,
                    bonus_attributes={
                        "tackle": 2,
                        "interception": 2,
                        "marking": 2,
                    },
                )
            )

        if normalized_position == "goleiro":
            goalie_defensive_plays = max(performance.defenses, performance.tackles)

            if goalie_defensive_plays >= 6:
                triggers.append(
                    AchievementTrigger(
                        code="muralha",
                        title="Muralha",
                        tier="Prata",
                        execution_bonus=1,
                        bonus_attributes={
                            "reflexes": 2,
                            "box_presence": 1,
                            "elasticity": 1,
                        },
                    )
                )

            if goalie_defensive_plays >= 10:
                triggers.append(
                    AchievementTrigger(
                        code="milagre",
                        title="Milagre",
                        tier="Ouro",
                        execution_bonus=1,
                        bonus_attributes={
                            "reflexes": 2,
                            "elasticity": 2,
                            "distribution": 1,
                        },
                    )
                )

        return triggers

    if sport_type in {"volei", "vôlei", "volleyball"}:
        if performance.attacks >= 12:
            triggers.append(
                AchievementTrigger(
                    code="martelo_de_goias",
                    title="Martelo de Goiás",
                    tier="Ouro",
                    execution_bonus=1,
                    bonus_attributes={
                        "spike_power": 2,
                        "spike_accuracy": 2,
                        "jump": 1,
                    },
                )
            )

        if performance.defenses >= 10:
            triggers.append(
                AchievementTrigger(
                    code="aspirador_de_po",
                    title="Aspirador de Pó",
                    tier="Prata",
                    execution_bonus=1,
                    bonus_attributes={
                        "reception": 2,
                        "floor_defense": 2,
                        "coverage": 1,
                    },
                )
            )

        if performance.blocks >= 5:
            triggers.append(
                AchievementTrigger(
                    code="muralha_de_cristal",
                    title="Muralha de Cristal",
                    tier="Prata",
                    execution_bonus=1,
                    bonus_attributes={
                        "block": 2,
                        "reaction": 1,
                        "coordination": 1,
                    },
                )
            )

        return triggers

    if performance.assists >= 8:
        triggers.append(
            AchievementTrigger(
                code="maos_de_seda",
                title="Mãos de Seda",
                tier="Bronze",
                execution_bonus=1,
                bonus_attributes={
                    "passing": 2,
                    "ball_control": 2,
                    "vision": 1,
                    "dribble": 1,
                },
            )
        )

    if performance.blocks >= 3 and performance.rebounds >= 10:
        triggers.append(
            AchievementTrigger(
                code="muralha_do_post",
                title="Muralha do Post",
                tier="Prata",
                execution_bonus=1,
                bonus_attributes={
                    "block": 2,
                    "post_def": 2,
                    "rebound": 2,
                    "combativeness": 1,
                },
            )
        )

    if performance.points >= 25 and _fg_percentage(performance) >= 60.0:
        triggers.append(
            AchievementTrigger(
                code="diamante_ofensivo",
                title="Diamante Ofensivo",
                tier="Ouro",
                execution_bonus=1,
                bonus_attributes={
                    "shoot_short": 1,
                    "shoot_mid": 1,
                    "shoot_long": 1,
                    "finishing": 2,
                },
            )
        )

    if performance.rebounds >= 15 and performance.blocks >= 4:
        triggers.append(
            AchievementTrigger(
                code="dominio_da_tabela",
                title="Domínio da Tabela",
                tier="Hall da Fama",
                execution_bonus=1,
                bonus_attributes={
                    "rebound": 3,
                    "reb_predict": 2,
                    "combativeness": 2,
                    "strength": 1,
                },
            )
        )

    return triggers


def distribute_match_xp(performance: MatchPerformance) -> PackageXpBreakdown:
    """Distribui XP bruto por pacote a partir da performance da partida.
    
    Aplica multiplicadores de sub_type:
    - FUTSAL: 1.2x em Agilidade e Controle de Bola
    - 3x3: 2x em Arremesso Longo (apenas basket)
    """
    sport_type = (performance.sport_type or "").strip().lower()

    package_xp = {
        "finalizacao": int(
            max(0, performance.field_goals_made * 12 + performance.points * 2 + performance.goals * 10)
        ),
        "fisico": int(
            max(0, performance.rebounds * 4 + performance.blocks * 3 + performance.points // 3 + performance.tackles * 3)
        ),
        "armacao": int(max(0, performance.assists * 12 + performance.points // 4 + performance.sets * 10)),
        "defesa": int(max(0, performance.steals * 12 + performance.blocks * 12 + performance.defenses * 8)),
        "rebote": int(max(0, performance.rebounds * 10)),
    }

    # Ajustes específicos por esporte
    if sport_type in {"futebol", "football"}:
        package_xp["finalizacao"] += performance.goals * 14 + performance.dribbles * 2
        package_xp["armacao"] += performance.assists * 8 + performance.dribbles
        package_xp["defesa"] += performance.tackles * 10 + performance.defenses * 6

    if sport_type in {"volei", "vôlei", "volleyball"}:
        package_xp["finalizacao"] += performance.attacks * 8 + performance.aces * 10
        package_xp["armacao"] += performance.sets * 10
        package_xp["defesa"] += performance.blocks * 8 + performance.defenses * 10

    fg_percentage = _fg_percentage(performance)
    if 0.0 < fg_percentage < 20.0:
        package_xp["finalizacao"] = max(0, package_xp["finalizacao"] - 5)

    attribute_xp = _package_xp_to_attributes(package_xp)
    attribute_xp = apply_multiplier(
        attribute_xp,
        sport_type=getattr(performance, "sport_type", None),
        sub_type=getattr(performance, "sub_type", None),
    )

    return PackageXpBreakdown(package_xp=package_xp, attribute_xp=attribute_xp)


def process_match_performance(
    performance: MatchPerformance,
    current_levels: Mapping[str, int] | None = None,
    current_residual_xp: Mapping[str, int] | None = None,
    player_position: str | None = None,
    player_overall: int | None = None,
    xp_multiplier: float = 1.0,
) -> MatchXpResult:
    """Processa uma partida e retorna XP, níveis e conquistas disparadas."""
    current_levels = current_levels or {}
    current_residual_xp = current_residual_xp or {}
    xp_breakdown = distribute_match_xp(performance)
    achievement_triggers = _achievement_rules(performance, player_position=player_position)
    xp_per_level = _resolve_xp_per_level(player_overall)

    xp_gains: dict[str, int] = {}
    level_gains: dict[str, int] = {}
    residual_xp: dict[str, int] = {}
    telemetry_logs: list[str] = []

    sport = (getattr(performance, "sport_type", None) or "unknown").strip().lower() or "unknown"
    user_id = str(getattr(performance, "user_id", "unknown"))

    safe_multiplier = max(1.0, float(xp_multiplier or 1.0))

    for attribute_name, xp_value in xp_breakdown.attribute_xp.items():
        scaled_xp = int(round(xp_value * safe_multiplier))
        total_xp = int(current_residual_xp.get(attribute_name, 0) or 0) + scaled_xp
        applied_xp = min(total_xp, MAX_XP_APPLIED_PER_MATCH)
        level_gain = applied_xp // xp_per_level
        level_gains[attribute_name] = level_gain
        residual_xp_value = applied_xp % xp_per_level
        residual_xp[attribute_name] = residual_xp_value
        xp_gains[attribute_name] = scaled_xp

        xp_log = _build_xp_log(
            sport=sport,
            user_id=user_id,
            action="MATCH_XP_APPLIED",
            attr=attribute_name,
            xp_value=scaled_xp,
            residual=residual_xp_value,
            level_divisor=xp_per_level,
        )
        telemetry_logs.append(xp_log)
        logger.info(xp_log)

    for trigger in achievement_triggers:
        achievement_log = _build_achievement_log(
            user_id=user_id,
            achievement_name=trigger.title,
            tier=trigger.tier,
            bonus=_format_achievement_bonus(trigger.bonus_attributes),
        )
        telemetry_logs.append(achievement_log)
        logger.info(achievement_log)

    return MatchXpResult(
        xp_gains=xp_gains,
        level_gains=level_gains,
        residual_xp=residual_xp,
        achievement_triggers=achievement_triggers,
        fg_percentage=_fg_percentage(performance),
        telemetry_logs=telemetry_logs,
    )


def apply_achievement_bonuses(
    source: PlayerStats | Mapping[str, int],
    triggers: list[AchievementTrigger],
) -> dict[str, int]:
    """Aplica bônus diretos de atributos das conquistas, respeitando teto de +3 por partida."""
    values = {
        attribute: _get_stat_value(source, attribute)
        for attribute in ALL_PROGRESS_ATTRIBUTES
    }
    applied_per_attribute: dict[str, int] = {attribute: 0 for attribute in ALL_PROGRESS_ATTRIBUTES}

    for trigger in triggers:
        for attribute_name, bonus in trigger.bonus_attributes.items():
            current_gain = applied_per_attribute.get(attribute_name, 0)
            remaining_room = 3 - current_gain
            if remaining_room <= 0:
                continue
            delta = min(remaining_room, bonus)
            values[attribute_name] = _clamp_stat(values[attribute_name] + delta)
            applied_per_attribute[attribute_name] = current_gain + delta

    return values


async def upsert_user_achievements(
    session: AsyncSession,
    user_id: str,
    triggers: list[AchievementTrigger],
) -> list[UserAchievement]:
    """Persiste conquistas disparadas por uma partida com raridade global."""
    repository = SqlAlchemyXpRepository(session)
    triggers_like = [
        AchievementTriggerLike(
            code=trigger.code,
            title=trigger.title,
            execution_bonus=trigger.execution_bonus,
            bonus_attributes=dict(trigger.bonus_attributes),
        )
        for trigger in triggers
    ]
    return await repository.upsert_user_achievements(user_id, triggers_like)


async def apply_match_progression(
    session: AsyncSession,
    user_id: str,
    performance: MatchPerformance,
    stats: PlayerStats,
    xp_multiplier: float = 1.0,
    telemetry_sink: StructuredTelemetryRepository | None = None,
) -> dict[str, Any]:
    """Atualiza XP residual, aplica bônus de conquistas e retorna um resumo de evolução."""
    started_at = perf_counter()

    repository = SqlAlchemyXpRepository(session)
    transaction = nullcontext() if session.in_transaction() else session.begin()
    async with transaction:
        locked_stats_query = select(PlayerStats).where(PlayerStats.user_id == user_id).with_for_update()
        locked_stats_result = await session.execute(locked_stats_query)
        locked_stats = locked_stats_result.scalars().first()
        if locked_stats is not None:
            stats = locked_stats

        xp_rows = await repository.ensure_user_xp_rows(user_id)
        current_residual = {row.attribute_name: row.residual_xp for row in xp_rows}
        current_levels = {row.attribute_name: row.level for row in xp_rows}
        current_overall = int(getattr(stats, "overall", 0) or 0)

        result = process_match_performance(
            performance,
            current_levels=current_levels,
            current_residual_xp=current_residual,
            player_position=stats.position,
            player_overall=current_overall,
            xp_multiplier=xp_multiplier,
        )

        achievement_rows = await repository.upsert_user_achievements(user_id, result.achievement_triggers)
        bonus_stats = apply_achievement_bonuses(stats, result.achievement_triggers)

        for row in xp_rows:
            attribute_name = row.attribute_name
            row.total_xp += result.xp_gains.get(attribute_name, 0)
            row.level += result.level_gains.get(attribute_name, 0)
            row.residual_xp = result.residual_xp.get(attribute_name, row.residual_xp)
            if row.total_xp < 0:
                row.total_xp = 0

        for field_name, value in bonus_stats.items():
            if hasattr(stats, field_name):
                setattr(stats, field_name, value)

        # Aplicar cálculo de overall conforme o esporte
        sport_type_normalized = performance.sport_type.strip().lower() if performance.sport_type else ""
        sub_type = getattr(performance, 'sub_type', '').strip() if hasattr(performance, 'sub_type') else ''

        stats.overall = await calculate_overall_async(
            request=OverallRequest(
                sport_type=sport_type_normalized,
                position=stats.position,
                sub_type=sub_type,
            ),
            source=stats,
        )

        await sync_user_prestige_entries(session, user_id=user_id, stats=stats, xp_rows=xp_rows)

    processing_ms = (perf_counter() - started_at) * 1000.0
    slow_processing = processing_ms > 100.0
    performance_log = (
        f"[XP_PERF][{sport_type_normalized or 'unknown'}][{user_id}] "
        f"Box Score XP processing took {processing_ms:.2f}ms"
    )
    logger.info(performance_log)

    telemetry_logs = [*result.telemetry_logs, performance_log]

    if slow_processing:
        warning_log = (
            f"[WARNING] Slow XP Processing | user_id={user_id} "
            f"| sport={sport_type_normalized or 'unknown'} | duration_ms={processing_ms:.2f}"
        )
        logger.warning(warning_log)
        telemetry_logs.append(warning_log)

    if telemetry_sink is not None:
        telemetry_sink.emit(
            category="match_xp",
            user_id=user_id,
            entries=telemetry_logs,
            extra={
                "processing_ms": processing_ms,
                "slow_processing": slow_processing,
                "sport_type": sport_type_normalized or "unknown",
            },
        )

    return {
        "xp": result,
        "achievement_rows": achievement_rows,
        "stats": stats,
        "telemetry_logs": telemetry_logs,
        "processing_ms": processing_ms,
        "slow_processing": slow_processing,
    }


def normalize_profile_sport_type(sport_type: str | None) -> str:
    """Normaliza esporte para o frontend distinguir entre futebol e basquete."""
    if not sport_type:
        return "FOOTBALL"
    normalized = sport_type.strip().lower()
    return PROFILE_SPORT_ALIASES.get(normalized, "FOOTBALL")
