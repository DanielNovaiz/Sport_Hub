"""Regras puras de raridade de conquistas (sem I/O, sem DB)."""

from __future__ import annotations

ACHIEVEMENT_RARITY_MULTIPLIERS: dict[str, float] = {
    "Bronze": 1.0,
    "Silver": 1.5,
    "Gold": 2.5,
}


def resolve_achievement_rarity(code_count: int, total_count: int) -> str:
    """Define a raridade com base na frequência global do evento."""
    if total_count <= 0 or code_count <= 0:
        return "Bronze"

    frequency = code_count / total_count
    if frequency <= 0.05:
        return "Gold"
    if frequency <= 0.20:
        return "Silver"
    return "Bronze"


def apply_achievement_rarity_bonus(base_bonus_value: int, tier: str) -> int:
    multiplier = ACHIEVEMENT_RARITY_MULTIPLIERS.get(tier, 1.0)
    return max(0, int(round(base_bonus_value * multiplier)))