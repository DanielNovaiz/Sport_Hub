"""Service de descoberta de eventos ativos."""

from __future__ import annotations

from datetime import UTC, datetime

from geoalchemy2.elements import WKTElement
from geoalchemy2 import Geography
from sqlalchemy import case, cast, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club, ClubMember
from app.models.event import Event, EventParticipant
from app.models.user import User, UserInterest
from app.schemas.event import (
    EventCreate,
    EventParticipantRead,
    EventRead,
    PersonalizedFeedItem,
    PersonalizedFeedResponse,
    EventSearchFilters,
    UserLocation,
)
from app.core.redis import pub_notification
from app.services.notification_service import create_notification


async def find_nearby_events(
    user_location: UserLocation,
    radius_km: float,
    filters: EventSearchFilters,
    session: AsyncSession,
) -> list[EventRead]:
    """Input: localização/raio/filtros. Output: eventos ativos próximos."""

    reference_point = func.ST_SetSRID(
        func.ST_MakePoint(user_location.longitude, user_location.latitude),
        4326,
    )
    radius_meters = radius_km * 1000.0
    now_utc = datetime.now(UTC)

    query = (
        select(Event)
        .where(
            func.ST_DWithin(
                cast(Event.location, Geography),
                cast(reference_point, Geography),
                radius_meters,
            )
        )
        .where(Event.status == "open")
        .where(Event.scheduled_time > now_utc)
    )

    if filters.sport_type:
        query = query.where(Event.sport_type == filters.sport_type.lower())

    query = query.order_by(
        func.ST_Distance(
            cast(Event.location, Geography),
            cast(reference_point, Geography),
        )
    ).limit(filters.limit)

    result = await session.execute(query)
    events = result.scalars().all()
    return [EventRead.model_validate(event) for event in events]


async def _count_confirmed_participants(session: AsyncSession, event_id: str) -> int:
    """Input: event_id. Output: quantidade de participantes confirmados."""
    count_query = select(func.count()).select_from(EventParticipant).where(
        EventParticipant.event_id == event_id,
        EventParticipant.status == "confirmed",
    )
    result = await session.execute(count_query)
    return int(result.scalar_one())


async def create_event(
    payload: EventCreate,
    session: AsyncSession,
) -> EventRead:
    """Input: EventCreate. Output: evento persistido para descoberta e join."""
    location_point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
    event = Event(
        creator_id=payload.creator_id,
        club_id=payload.club_id,
        sport_type=payload.sport_type.lower(),
        sub_type=payload.sub_type.lower() if payload.sub_type else None,
        scheduled_time=payload.scheduled_time,
        status=payload.status,
        max_participants=payload.max_participants,
        location=location_point,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return EventRead.model_validate(event)


async def join_event(
    user_id: str,
    event_id: str,
    session: AsyncSession,
) -> EventParticipantRead:
    """Input: user_id/event_id. Output: inscrição confirmada ou waitlist."""
    participant: EventParticipant | None = None
    creator_id: str | None = None
    event_identifier: str | None = None
    try:
        async with session.begin():
            event_query = select(Event).where(Event.id == event_id).with_for_update()
            event_result = await session.execute(event_query)
            event = event_result.scalars().first()
            if not event:
                raise ValueError("event_not_found")
            event_time = event.scheduled_time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=UTC)
            if event.status == "finished" or event_time <= datetime.now(UTC):
                raise ValueError("event_not_available")
            creator_id = event.creator_id
            event_identifier = event.id
            if event.club_id:
                club = await session.get(Club, event.club_id)
                if not club:
                    raise ValueError("club_not_found")
                if club.privacy_type == "private":
                    membership_query = select(ClubMember).where(
                        ClubMember.club_id == club.id,
                        ClubMember.user_id == user_id,
                        ClubMember.status.in_(["admin", "member"]),
                    )
                    membership_result = await session.execute(membership_query)
                    membership = membership_result.scalars().first()
                    if not membership:
                        raise ValueError("private_club_membership_required")
            existing_query = select(EventParticipant).where(
                EventParticipant.user_id == user_id,
                EventParticipant.event_id == event_id,
            )
            existing_result = await session.execute(existing_query)
            if existing_result.scalars().first():
                raise ValueError("user_already_joined")
            confirmed_count = await _count_confirmed_participants(session, event_id)
            participant_status = "confirmed"
            if confirmed_count >= event.max_participants or event.status == "full":
                participant_status = "waitlist"
                event.status = "full"
            elif confirmed_count + 1 >= event.max_participants:
                event.status = "full"
            participant = EventParticipant(
                user_id=user_id,
                event_id=event_id,
                status=participant_status,
            )
            session.add(participant)
            await create_notification(
                session,
                user_id=event.creator_id,
                content=f"Novo participante entrou no evento {event.id}",
                notification_type="event_update",
            )
    except IntegrityError as error:
        await session.rollback()
        raise ValueError("user_already_joined") from error

    if not participant:
        raise ValueError("join_failed")
    await session.refresh(participant)
    if creator_id and event_identifier:
        await pub_notification(
            creator_id,
            f"Novo participante entrou no seu evento {event_identifier}",
            extra={"event_id": event_identifier, "participant_id": participant.id},
        )
    return EventParticipantRead.model_validate(participant)


async def get_personalized_feed(
    user_id: str,
    session: AsyncSession,
    radius_km: float = 15.0,
    limit: int = 30,
) -> PersonalizedFeedResponse:
    """Input: user_id. Output: feed de eventos descobertos com prioridade por clube membro."""
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("user_not_found")

    coords_query = select(func.ST_X(User.location), func.ST_Y(User.location)).where(User.id == user_id)
    coords_result = await session.execute(coords_query)
    longitude, latitude = coords_result.first() or (None, None)
    if longitude is None or latitude is None:
        raise ValueError("user_location_required")

    favorite_interest_query = (
        select(UserInterest.sport)
        .where(UserInterest.user_id == user_id)
        .order_by(UserInterest.is_primary.desc(), UserInterest.created_at.asc())
        .limit(1)
    )
    favorite_result = await session.execute(favorite_interest_query)
    favorite_sport = favorite_result.scalar_one_or_none()
    if not favorite_sport:
        return PersonalizedFeedResponse(message="feed_found", data=[], meta={"count": 0, "radius_km": radius_km})

    reference_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
    club_membership_exists = exists(
        select(ClubMember.id).where(
            ClubMember.club_id == Event.club_id,
            ClubMember.user_id == user_id,
            ClubMember.status.in_(["admin", "member"]),
        )
    )
    event_accessible = or_(
        Event.club_id.is_(None),
        Club.privacy_type == "public",
        club_membership_exists,
    )
    club_priority_expr = case((club_membership_exists, 1), else_=0)
    distance_expr = func.ST_Distance(cast(Event.location, Geography), cast(reference_point, Geography)) / 1000.0
    confirmed_counts_subquery = (
        select(
            EventParticipant.event_id.label("event_id"),
            func.count(EventParticipant.id).label("confirmed_participants"),
        )
        .where(EventParticipant.status == "confirmed")
        .group_by(EventParticipant.event_id)
        .subquery()
    )

    query = (
        select(
            Event,
            distance_expr.label("distance_km"),
            club_priority_expr.label("club_priority"),
            func.coalesce(confirmed_counts_subquery.c.confirmed_participants, 0).label("confirmed_participants"),
        )
        .outerjoin(Club, Club.id == Event.club_id)
        .outerjoin(confirmed_counts_subquery, confirmed_counts_subquery.c.event_id == Event.id)
        .where(Event.status == "open")
        .where(Event.scheduled_time > datetime.now(UTC))
        .where(Event.sport_type == favorite_sport.lower())
        .where(func.ST_DWithin(cast(Event.location, Geography), cast(reference_point, Geography), radius_km * 1000.0))
        .where(event_accessible)
        .order_by(club_priority_expr.desc(), distance_expr.asc(), Event.scheduled_time.asc())
        .limit(limit)
    )
    result = await session.execute(query)
    rows = result.all()
    data = []
    for row in rows:
        event = row[0]
        dist = row[1] if len(row) > 1 else 0.0
        prio = row[2] if len(row) > 2 else False
        conf = row[3] if len(row) > 3 else 0

        data.append(
            PersonalizedFeedItem(
                **EventRead.model_validate(event).model_dump(),
                title=f"{event.sport_type.title()} • {event.scheduled_time.strftime('%d/%m %H:%M')}",
                distance_km=round(float(dist), 3),
                club_priority=bool(prio),
                confirmed_participants=int(conf),
                remaining_spots=max(event.max_participants - int(conf), 0),
            )
        )
    return PersonalizedFeedResponse(
        message="feed_found",
        data=data,
        meta={"count": len(data), "radius_km": radius_km, "sport_type": favorite_sport.lower()},
    )
