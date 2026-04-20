"""Mapeamento global de posições normalizadas do atleta."""

from __future__ import annotations

import unicodedata

POSITIONS_MAP: dict[str, str] = {
    "meia": "MIDFIELDER",
    "cam": "MIDFIELDER",
    "armador (futebol)": "MIDFIELDER",
    "pivo (basquete)": "CENTER_BASKET",
    "center": "CENTER_BASKET",
}


def _normalize_key(position: str) -> str:
    normalized = unicodedata.normalize("NFKD", position)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(normalized.strip().lower().split())


def normalize_position_input(position: str | None) -> str:
    """Normaliza entrada livre do usuário para um rótulo canônico."""
    if not position:
        return ""
    normalized = _normalize_key(position)
    return POSITIONS_MAP.get(normalized, position.strip())