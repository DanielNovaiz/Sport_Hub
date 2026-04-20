"""Motor unificado e assíncrono de cálculo de overall."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Mapping

from app.models.player_stats import PlayerStats


@dataclass(frozen=True)
class OverallRequest:
    sport_type: str | None
    position: str | None
    sub_type: str | None = None
    mode: str | None = None


def _normalize_sport(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "futebol": "football",
        "football": "football",
        "soccer": "football",
        "basquete": "basketball",
        "basketball": "basketball",
        "volei": "volleyball",
        "vôlei": "volleyball",
        "volleyball": "volleyball",
    }
    return aliases.get(normalized, normalized or "football")


def _normalize_sub_type(value: str | None, mode: str | None) -> str:
    normalized = (value or mode or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "society": "society",
        "futsal": "futsal",
        "3x3": "3x3",
        "beach": "beach",
        "praia": "beach",
        "quadra": "quadra",
        "court": "quadra",
        "flex": "flex",
        "modo_flex": "flex",
    }
    return aliases.get(normalized, normalized)


def _calculate_sync(*, request: OverallRequest, source: PlayerStats | Mapping[str, int]) -> int:
    from app.services.xp_service import (
        calculate_attribute_overall,
        calculate_basketball_overall,
        calculate_football_overall,
        calculate_volleyball_overall,
    )

    sport = _normalize_sport(request.sport_type)
    sub_type = _normalize_sub_type(request.sub_type, request.mode)
    position = request.position or "default"

    if sub_type == "flex":
        # Modo flex usa fallback poliatleta para manter consistência entre modalidades.
        return max(0, min(99, int(calculate_attribute_overall(position, source))))

    if sport == "basketball":
        return max(0, min(99, int(calculate_basketball_overall(position, source))))

    if sport == "football":
        return max(0, min(99, int(calculate_football_overall(position, source, sub_type=sub_type or None))))

    if sport == "volleyball":
        return max(0, min(99, int(calculate_volleyball_overall(position, source, sub_type=sub_type or None))))

    return max(0, min(99, int(calculate_attribute_overall(position, source))))


async def calculate_overall_async(*, request: OverallRequest, source: PlayerStats | Mapping[str, int]) -> int:
    """Executa cálculo unificado de overall sem bloquear o loop de eventos."""
    return await asyncio.to_thread(_calculate_sync, request=request, source=source)
