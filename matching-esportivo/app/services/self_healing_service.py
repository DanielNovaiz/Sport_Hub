"""Rotinas de autocorreção (self-healing) de consistência de stats."""

from __future__ import annotations

import logging
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stats import MatchPerformance, PlayerStats
from app.services.overall_engine import OverallRequest, calculate_overall_async

logger = logging.getLogger(__name__)


def _is_invalid_overall(value: object) -> bool:
    if value is None:
        return True
    try:
        number = float(value)
    except (TypeError, ValueError):
        return True
    if math.isnan(number) or math.isinf(number):
        return True
    return number < 0 or number > 99


async def recalculate_impossible_overalls(session: AsyncSession) -> dict[str, int]:
    """Recalcula overalls inválidos com base no histórico recente de partidas."""
    query = select(PlayerStats)
    result = await session.execute(query)
    stats_rows = result.scalars().all()

    scanned = len(stats_rows)
    repaired = 0

    for stats in stats_rows:
        if not _is_invalid_overall(getattr(stats, "overall", None)):
            continue

        match_query = (
            select(MatchPerformance.sport_type, MatchPerformance.sub_type)
            .where(MatchPerformance.user_id == stats.user_id)
            .order_by(MatchPerformance.created_at.desc())
            .limit(1)
        )
        match_result = await session.execute(match_query)
        latest_match = match_result.first()

        sport_type = latest_match[0] if latest_match else None
        sub_type = latest_match[1] if latest_match else None

        recomputed = await calculate_overall_async(
            request=OverallRequest(
                sport_type=sport_type,
                position=stats.position,
                sub_type=sub_type,
            ),
            source=stats,
        )
        stats.overall = recomputed
        repaired += 1

    if repaired > 0:
        await session.commit()

    logger.info(
        "startup_self_healing_completed",
        extra={"scanned": scanned, "repaired": repaired},
    )
    return {"scanned": scanned, "repaired": repaired}
