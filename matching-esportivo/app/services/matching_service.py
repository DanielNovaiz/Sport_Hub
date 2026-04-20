"""Serviço de sugestões de jogadores para convites de eventos."""

from __future__ import annotations

from geoalchemy2 import Geography
from sqlalchemy import cast, exists, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventParticipant
from app.models.user import User, UserInterest
from app.schemas.event import SuggestedPlayerRead


async def suggest_players_for_event(
    event_id: str,
    session: AsyncSession,
) -> list[SuggestedPlayerRead]:
    """Input: event_id. Output: usuários no raio, com interesse, fora da inscrição.

    A filtragem espacial roda integralmente no banco via ST_DWithin/ST_Distance.
    """
    event = await session.get(Event, event_id)
    if not event:
        raise ValueError("event_not_found")
    distance_expr = (
        func.ST_Distance(
            cast(User.location, Geography),
            cast(event.location, Geography),
        )
        / literal(1000.0)
    )
    query = (
        select(User.id, User.full_name, distance_expr.label("distance_km"))
        .join(UserInterest, UserInterest.user_id == User.id)
        .where(User.location.is_not(None))
        .where(func.lower(UserInterest.sport) == event.sport_type.lower())
        .where(
            func.ST_DWithin(
                cast(User.location, Geography),
                cast(event.location, Geography),
                5000.0,
            )
        )
        .where(
            ~exists(
                select(EventParticipant.id).where(
                    EventParticipant.event_id == event_id,
                    EventParticipant.user_id == User.id,
                )
            )
        )
        .order_by(distance_expr)
        .limit(50)
    )
    result = await session.execute(query)
    return [
        SuggestedPlayerRead(id=user_id, name=full_name, distance_km=round(float(distance_km), 3))
        for user_id, full_name, distance_km in result.all()
    ]