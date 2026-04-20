"""Endpoints de descoberta de eventos ativos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.event import (
    EventCreate,
    EventResponse,
    EventSearchFilters,
    EventSearchResponse,
    EventSuggestionsResponse,
    JoinEventRequest,
    JoinEventResponse,
    UserLocation,
)
from app.services.event_service import create_event, find_nearby_events, join_event
from app.services.matching_service import suggest_players_for_event

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/", response_model=EventResponse)
async def create_event_endpoint(
    payload: EventCreate,
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    """Input: EventCreate. Output: envelope com EventRead criado."""
    event = await create_event(payload, session)
    return EventResponse(message="event_created", data=event)


@router.get("/search", response_model=EventSearchResponse)
async def search_active_events(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(15.0, ge=0.1, le=100.0),
    sport_type: str | None = Query(default=None, min_length=2, max_length=50),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> EventSearchResponse:
    """Input: query params geográficos. Output: eventos open ainda não iniciados."""

    user_location = UserLocation(latitude=latitude, longitude=longitude)
    filters = EventSearchFilters(sport_type=sport_type, limit=limit)
    events = await find_nearby_events(user_location, radius_km, filters, session)
    return EventSearchResponse(
        message="active_events_found",
        data=events,
        meta={
            "radius_km": radius_km,
            "sport_type": sport_type,
            "count": len(events),
        },
    )


@router.post("/{event_id}/join", response_model=JoinEventResponse)
async def join_event_endpoint(
    event_id: str,
    payload: JoinEventRequest,
    session: AsyncSession = Depends(get_session),
) -> JoinEventResponse:
    """Input: user_id/event_id. Output: inscrição em evento com status."""
    try:
        participant = await join_event(payload.user_id, event_id, session)
    except ValueError as error:
        message = str(error)
        if message == "event_not_found":
            raise HTTPException(status_code=404, detail=message)
        if message == "user_already_joined":
            raise HTTPException(status_code=409, detail=message)
        if message == "event_not_available":
            raise HTTPException(status_code=400, detail=message)
        if message == "private_club_membership_required":
            raise HTTPException(status_code=403, detail=message)
        raise
    return JoinEventResponse(
        message="event_joined",
        data=participant,
        meta={"event_id": event_id, "participant_status": participant.status},
    )


@router.get("/{event_id}/suggestions", response_model=EventSuggestionsResponse)
async def event_suggestions_endpoint(
    event_id: str,
    session: AsyncSession = Depends(get_session),
) -> EventSuggestionsResponse:
    """Input: event_id. Output: jogadores ideais por raio+interesse+não inscritos."""
    try:
        suggestions = await suggest_players_for_event(event_id, session)
    except ValueError as error:
        if str(error) == "event_not_found":
            raise HTTPException(status_code=404, detail="event_not_found")
        raise
    return EventSuggestionsResponse(
        message="player_suggestions_found",
        data=suggestions,
        meta={"event_id": event_id, "count": len(suggestions), "radius_km": 5},
    )
