"""Motor de cálculos de overall com multiplicadores de sub-variações esportivas.

Sub-tipos aplicam bônus/malus a atributos específicos antes do cálculo final do overall.
"""

from __future__ import annotations

from typing import Any, Mapping


# ============================================================================
# MAPEAMENTO: ATRIBUTO -> PACOTES QUE CONTÊM O ATRIBUTO
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


# ============================================================================
# MULTIPLICADORES POR SUB-TIPO DE ESPORTE
# ============================================================================

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
# FUNÇÃO PRINCIPAL: APLICAR MULTIPLICADORES A PACOTES
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


def calculate_precise_overall(weighted_sum: float, divisor: float) -> float:
    """Calcula overall com precisão de 2 casas decimais.
    
    Deprecated: Use calculate_precise_overall_with_sub_type em xp_service.
    """
    safe_divisor = divisor if divisor else 1.0
    return round(weighted_sum / safe_divisor, 2)
