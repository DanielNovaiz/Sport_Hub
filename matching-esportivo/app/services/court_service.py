"""Serviço de quadras e reservas (marketplace)."""

from __future__ import annotations

from datetime import datetime

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.court import Court, Booking
from app.schemas.court import BookingCreate, BookingRead, BookingWithCourtRead, CourtCreate, CourtRead


async def _to_court_read(session: AsyncSession, court: Court) -> CourtRead:
    """Build CourtRead with coordinates extracted from PostGIS point."""
    coords_query = select(func.ST_X(Court.location), func.ST_Y(Court.location)).where(Court.id == court.id)
    coords_result = await session.execute(coords_query)
    longitude, latitude = coords_result.first() or (None, None)

    return CourtRead(
        **CourtRead.model_validate(court).model_dump(),
        latitude=float(latitude) if latitude is not None else None,
        longitude=float(longitude) if longitude is not None else None,
    )


async def create_court(session: AsyncSession, payload: CourtCreate) -> CourtRead:
    """Input: CourtCreate. Output: CourtRead."""
    location_point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
    court = Court(
        owner_id=payload.owner_id,
        name=payload.name,
        description=payload.description,
        sport_type=payload.sport_type.lower(),
        location=location_point,
        price_per_hour=payload.price_per_hour,
        photos_url=payload.photos_url,
    )
    session.add(court)
    await session.commit()
    await session.refresh(court)
    return await _to_court_read(session, court)


async def list_courts(session: AsyncSession, limit: int = 100, sport_type: str | None = None) -> list[CourtRead]:
    """Input: optional sport filter. Output: courts list with coordinates."""
    query = select(Court).order_by(Court.created_at.desc()).limit(limit)
    if sport_type:
        query = query.where(Court.sport_type == sport_type.lower())

    result = await session.execute(query)
    courts = result.scalars().all()
    return [await _to_court_read(session, court) for court in courts]


async def check_booking_availability(
    session: AsyncSession,
    court_id: str,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    """Input: court + time range. Output: True if available."""
    query = select(Booking).where(
        Booking.court_id == court_id,
        Booking.start_time < end_time,
        Booking.end_time > start_time,
        Booking.status.in_(["pending", "confirmed"]),
    )
    result = await session.execute(query)
    conflicting = result.scalars().first()
    return conflicting is None


async def create_booking(session: AsyncSession, payload: BookingCreate) -> BookingRead:
    """Input: BookingCreate. Output: BookingRead com lock pessimista para evitar race condition.
    
    FASE 2: Auditoria de Concorrência
    - Usa SELECT FOR UPDATE para garantir serialução
    - Verifica disponibilidade e cria dentro da mesma transação
    - Evita double-booking mesmo com requests concorrentes
    """
    # 1. Adquirir lock pessimista em todos os bookings do court
    # SELECT FOR UPDATE garante que outros txs esperem
    lock_query = select(Booking).where(
        Booking.court_id == payload.court_id,
    ).with_for_update()
    
    await session.execute(lock_query)  # Adquire lock, não precisa do resultado
    
    # 2. Verificar disponibilidade (dentro do lock)
    available = await check_booking_availability(
        session,
        payload.court_id,
        payload.start_time,
        payload.end_time,
    )
    if not available:
        await session.rollback()
        raise ValueError("court_not_available_in_time_range")

    # 3. Buscar court (com lock)
    court = await session.get(Court, payload.court_id, with_for_update=True)
    if not court:
        await session.rollback()
        raise ValueError("court_not_found")

    # 4. Calcular total_price e criar booking
    hours = (payload.end_time - payload.start_time).total_seconds() / 3600.0
    total_price = hours * court.price_per_hour

    booking = Booking(
        court_id=payload.court_id,
        user_id=payload.user_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="confirmed",
        total_price=total_price,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return BookingRead.model_validate(booking)


async def list_user_bookings(
    session: AsyncSession,
    user_id: str,
    status_filter: str | None = None,
    limit: int = 100,
) -> list[BookingWithCourtRead]:
    """Input: user_id. Output: user bookings with court metadata."""
    query = (
        select(Booking, Court)
        .join(Court, Court.id == Booking.court_id)
        .where(Booking.user_id == user_id)
        .order_by(Booking.start_time.desc())
        .limit(limit)
    )
    if status_filter:
        query = query.where(Booking.status == status_filter)

    result = await session.execute(query)
    rows = result.all()

    bookings: list[BookingWithCourtRead] = []
    for booking, court in rows:
        court_read = await _to_court_read(session, court)
        bookings.append(
            BookingWithCourtRead(
                **BookingRead.model_validate(booking).model_dump(),
                court=court_read,
            )
        )
    return bookings
