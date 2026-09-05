"""Módulo puro de cálculo de overall por esporte e arquétipo (sem I/O, sem DB).

Consolida as três fontes anteriores de overall:
- ``xp_service`` (calculadoras de basquete/futebol/vôlei e alias poliatleta);
- ``calculations`` (multiplicadores de sub-tipo, ex-``app/services/calculations.py``);
- ``user_service`` (overall/arquétipo por atributos).

Não deve importar de ``app.services`` nem ``app.repositories`` (guard test vigia isso).
"""

from __future__ import annotations

from typing import Any, Mapping

from app.models.player_stats import PlayerStats


# ============================================================================
# BASQUETE — PACOTES, PESOS E ALIASES
# ============================================================================

BASKETBALL_PACKAGES: dict[str, tuple[str, ...]] = {
    "finalizacao": ("shoot_long", "shoot_mid", "shoot_short", "finishing"),
    "fisico": ("velocity", "jump", "agility", "energy", "strength", "balance"),
    "armacao": ("passing", "ball_control", "vision", "dribble"),
    "defesa": ("steal", "block", "perim_def", "post_def"),
    "rebote": ("rebound", "reb_predict", "combativeness"),
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


# ============================================================================
# FUTEBOL — PACOTES, PESOS E ALIASES
# ============================================================================

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


# ============================================================================
# FUTEBOL — MULTIPLICADORES DE SUB-TIPO (ex-app/services/calculations.py)
# ============================================================================

FOOTBALL_ATTRIBUTE_TO_PACKAGE: dict[str, str] = {
    # Finalizacao
    "short_finish": "finalizacao",
    "long_shot": "finalizacao",
    "free_kick": "finalizacao",
    # Mobilidade
    "sprint": "mobilidade",
    "acceleration": "mobilidade",
    "agility": "mobilidade",
    # Fisico
    "stamina": "fisico",
    "strength": "fisico",
    "balance": "fisico",
    # Criacao
    "short_pass": "criacao",
    "long_pass": "criacao",
    "crossing": "criacao",
    "vision": "criacao",
    "dribbling": "criacao",
    "ball_control": "criacao",
    # Defesa
    "tackle": "defesa",
    "interception": "defesa",
    "marking": "defesa",
    "ball_shielding": "defesa",
}

FUTSAL_MULTIPLIERS: dict[str, float] = {
    "agility": 1.2,       # 20% aumento
    "ball_control": 1.2,  # 20% aumento
    "stamina": 0.8,       # 20% redução
}

SOCIETY_MULTIPLIERS: dict[str, float] = {
    "long_shot": 1.1,     # 10% aumento
    "strength": 1.1,      # 10% aumento
}

FOOTBALL_SUB_TYPE_MULTIPLIERS: dict[str, dict[str, float]] = {
    "futsal": FUTSAL_MULTIPLIERS,
    "society": SOCIETY_MULTIPLIERS,
    "field": {},  # Sem multiplicadores para futebol de campo (padrão)
}


# ============================================================================
# VÔLEI — PACOTES, PESOS E ALIASES
# ============================================================================

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


# ============================================================================
# HELPERS PURAS
# ============================================================================

def _clamp_stat(value: int) -> int:
    return max(0, min(99, int(value)))


def _get_stat_value(source: PlayerStats | Mapping[str, int], name: str) -> int:
    if isinstance(source, Mapping):
        return _clamp_stat(source.get(name, 0) or 0)
    return _clamp_stat(getattr(source, name, 0) or 0)


def _package_average(source: PlayerStats | Mapping[str, int], attributes: tuple[str, ...]) -> int:
    if not attributes:
        return 0
    total = sum(_get_stat_value(source, attribute) for attribute in attributes)
    return int(round(total / len(attributes)))


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


def calculate_precise_overall(weighted_sum: float, divisor: float) -> float:
    """Calcula overall com precisão de 2 casas decimais antes da exibição."""
    safe_divisor = divisor if divisor else 1.0
    return round(weighted_sum / safe_divisor, 2)


# ============================================================================
# NORMALIZAÇÃO DE POSIÇÃO
# ============================================================================

def _normalize_basketball_position(position: str | None) -> str:
    if not position:
        return "default"
    normalized = position.strip().lower().replace(" ", "_")
    if normalized == "midfielder":
        return "meia"
    return BASKETBALL_POSITION_ALIASES.get(normalized, normalized)


def _normalize_football_position(position: str | None) -> str:
    """Normaliza posição para futebol."""
    if not position:
        return "default"
    normalized = position.strip().lower().replace(" ", "_")
    return FOOTBALL_POSITION_ALIASES.get(normalized, normalized)


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


def _normalize_player_position(position: str | None) -> str:
    """Input: posição livre. Output: posição normalizada para tabela de pesos."""
    if not position:
        return "default"
    normalized = position.strip().lower()
    aliases = {
        "striker": "atacante",
        "forward": "atacante",
        "defender": "zagueiro",
        "centerback": "zagueiro",
        "midfielder": "meia",
        "center_basket": "pivo",
        "wing": "ala",
        "winger": "ala",
        "center": "pivo",
        "pivot": "pivo",
        "goalkeeper": "goleiro",
        "keeper": "goleiro",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in PLAYER_OVERALL_WEIGHTS:
        return normalized
    return "default"


# ============================================================================
# MULTIPLICADORES DE SUB-TIPO
# ============================================================================

def apply_sub_type_multipliers(
    package_scores: dict[str, float] | dict[str, int],
    available_attributes: dict[str, int],
    sub_type: str | None = None,
    sport_type: str | None = None,
) -> dict[str, float]:
    """Aplica multiplicadores de sub-tipo aos scores de pacote.

    Fluxo:
    1. Identifica multiplicadores para (sport_type, sub_type)
    2. Para cada atributo afetado, encontra seu pacote pai
    3. Ajusta o score do pacote com base no multiplicador do atributo
    4. Retorna package_scores ajustados

    Args:
        package_scores: Dict de scores por pacote
        available_attributes: Dict de atributos e seus valores
        sub_type: Variação do jogo
        sport_type: Tipo de esporte

    Returns:
        Dict de package_scores ajustados
    """
    normalized_sport = (sport_type or "").strip().lower()
    normalized_sub_type = (sub_type or "").strip().lower()

    multipliers = _get_multipliers_for_sport(normalized_sport, normalized_sub_type)
    if not multipliers:
        return {name: float(score) for name, score in package_scores.items()}

    # Copiar scores originais
    adjusted_packages = {name: float(score) for name, score in package_scores.items()}

    # Aplicar multiplicadores por atributo → pacote
    package_impacts: dict[str, list[float]] = {}  # Rastrear impactos por pacote

    for attr_name, multiplier in multipliers.items():
        attr_value = available_attributes.get(attr_name, 50)  # Default 50 se não encontrado
        package_name = FOOTBALL_ATTRIBUTE_TO_PACKAGE.get(attr_name)

        if not package_name or package_name not in adjusted_packages:
            continue

        # Calcular impacto do multiplicador neste atributo
        original_val = float(attr_value)
        adjusted_val = original_val * multiplier
        impact_delta = adjusted_val - original_val  # Ex: +10 ou -10

        if package_name not in package_impacts:
            package_impacts[package_name] = []
        package_impacts[package_name].append(impact_delta)

    # Aplicar impactos agregados aos pacotes
    for package_name, impacts in package_impacts.items():
        if impacts:
            avg_impact = sum(impacts) / len(impacts)
            adjusted_packages[package_name] = max(0, min(99, adjusted_packages[package_name] + avg_impact))

    return adjusted_packages


def _get_multipliers_for_sport(sport_type: str, sub_type: str) -> dict[str, float]:
    """Retorna o dicionário de multiplicadores para (sport, sub_type)."""
    if sport_type in {"football", "futebol", "futbol"}:
        return FOOTBALL_SUB_TYPE_MULTIPLIERS.get(sub_type, {})
    # Expandir aqui para basketball, volleyball, etc.
    return {}


# ============================================================================
# OVERALL POR ESPORTE
# ============================================================================

def calculate_basketball_package_scores(source: PlayerStats | Mapping[str, int]) -> dict[str, int]:
    """Calcula os 5 pacotes do basquete em escala 0-99."""
    return {
        package_name: _package_average(source, attributes)
        for package_name, attributes in BASKETBALL_PACKAGES.items()
    }


def calculate_basketball_overall(position: str, source: PlayerStats | Mapping[str, int]) -> int:
    """Calcula Overall de basquete usando pesos por posição e divisor específico."""
    normalized_position = _normalize_basketball_position(position)
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
        "position": _normalize_basketball_position(position),
        "overall": calculate_basketball_overall(position, source),
        "packages": calculate_basketball_package_scores(source),
    }


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


def calculate_volleyball_package_scores(source: PlayerStats | Mapping[str, int]) -> dict[str, int]:
    """Calcula os 5 pacotes do vôlei em escala 0-99."""
    return {
        package_name: _package_average(source, attributes)
        for package_name, attributes in VOLLEYBALL_PACKAGES.items()
    }


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


# ============================================================================
# OVERALL POLIATLETA (6 ATRIBUTOS) E ARQUÉTIPO
# ============================================================================

PLAYER_OVERALL_WEIGHTS: dict[str, dict[str, float]] = {
    "atacante": {
        "pace": 0.22,
        "shooting": 0.30,
        "passing": 0.12,
        "defense": 0.08,
        "physical": 0.16,
        "technique": 0.12,
    },
    "zagueiro": {
        "pace": 0.12,
        "shooting": 0.05,
        "passing": 0.13,
        "defense": 0.32,
        "physical": 0.28,
        "technique": 0.10,
    },
    "meia": {
        "pace": 0.16,
        "shooting": 0.15,
        "passing": 0.28,
        "defense": 0.12,
        "physical": 0.10,
        "technique": 0.19,
    },
    "ala": {
        "pace": 0.24,
        "shooting": 0.20,
        "passing": 0.16,
        "defense": 0.16,
        "physical": 0.12,
        "technique": 0.12,
    },
    "pivo": {
        "pace": 0.08,
        "shooting": 0.18,
        "passing": 0.10,
        "defense": 0.24,
        "physical": 0.30,
        "technique": 0.10,
    },
    "goleiro": {
        "pace": 0.08,
        "shooting": 0.02,
        "passing": 0.16,
        "defense": 0.34,
        "physical": 0.24,
        "technique": 0.16,
    },
    "default": {
        "pace": 1 / 6,
        "shooting": 1 / 6,
        "passing": 1 / 6,
        "defense": 1 / 6,
        "physical": 1 / 6,
        "technique": 1 / 6,
    },
}

ARCHETYPE_THRESHOLDS: tuple[tuple[str, str], ...] = (
    ("shooting", "Sharpshooter"),
    ("defense", "Lockdown Defender"),
    ("pace", "Speedster"),
)


def calculate_player_overall(
    position: str,
    pace: int,
    shooting: int,
    passing: int,
    defense: int,
    physical: int,
    technique: int,
) -> int:
    """Input: posição e atributos [0-99]. Output: overall [0-99] por média ponderada."""
    weights = PLAYER_OVERALL_WEIGHTS[_normalize_player_position(position)]
    attributes = {
        "pace": pace,
        "shooting": shooting,
        "passing": passing,
        "defense": defense,
        "physical": physical,
        "technique": technique,
    }
    weighted_sum = sum(attributes[name] * weight for name, weight in weights.items())
    overall = int(round(weighted_sum))
    return max(0, min(99, overall))


def calculate_playstyle_archetype(
    pace: int,
    shooting: int,
    passing: int,
    defense: int,
    physical: int,
    technique: int,
) -> str:
    """Input: atributos [0-100]. Output: arquétipo principal baseado no maior atributo."""
    attrs = {
        "pace": pace,
        "shooting": shooting,
        "passing": passing,
        "defense": defense,
        "physical": physical,
        "technique": technique,
    }
    strongest_attr = max(attrs, key=attrs.get)
    strongest_value = attrs[strongest_attr]
    if strongest_value < 85:
        return "Balanced"

    threshold_map = dict(ARCHETYPE_THRESHOLDS)
    if strongest_attr in threshold_map:
        return threshold_map[strongest_attr]
    if strongest_attr in {"passing", "technique"}:
        return "Playmaker"
    if strongest_attr == "physical":
        return "Powerhouse"
    return "Balanced"


def calculate_attribute_overall(position: str, source: PlayerStats | Mapping[str, int]) -> int:
    """Alias poliatleta para modelos antigos que ainda usam a matriz de 6 atributos."""
    return calculate_player_overall(
        position=position,
        pace=_get_stat_value(source, "pace"),
        shooting=_get_stat_value(source, "shooting"),
        passing=_get_stat_value(source, "passing"),
        defense=_get_stat_value(source, "defense"),
        physical=_get_stat_value(source, "physical"),
        technique=_get_stat_value(source, "technique"),
    )







