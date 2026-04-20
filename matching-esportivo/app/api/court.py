"""Endpoints de quadras e reservas (marketplace)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.court import Court
from app.schemas.court import (
    BookingListResponse,
    BookingCreate,
    BookingResponse,
    CourtListResponse,
    CourtCreate,
    CourtRead,
    CourtResponse,
)
from app.services.court_service import (
    check_booking_availability,
    create_booking,
    create_court,
    list_courts,
    list_user_bookings,
    _to_court_read,
)

router = APIRouter(prefix="/api/courts", tags=["Courts"])


@router.get("", response_model=CourtListResponse, status_code=status.HTTP_200_OK)
async def list_available_courts(
    sport_type: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> CourtListResponse:
    """Listar quadras do marketplace."""
    courts = await list_courts(session, limit=limit, sport_type=sport_type)
    return CourtListResponse(
        message="Courts retrieved successfully",
        data=courts,
        meta={"count": len(courts), "sport_type": sport_type},
    )


@router.post("", response_model=CourtResponse, status_code=status.HTTP_201_CREATED)
async def create_new_court(
    payload: CourtCreate,
    session: AsyncSession = Depends(get_session),
) -> CourtResponse:
    """Criar nova quadra no marketplace."""
    court = await create_court(session, payload)
    return CourtResponse(
        message="Court created successfully",
        data=court,
    )


@router.get("/{court_id}", response_model=CourtResponse, status_code=status.HTTP_200_OK)
async def get_court_details(
    court_id: str,
    session: AsyncSession = Depends(get_session),
) -> CourtResponse:
    """Obter detalhes de uma quadra."""
    court = await session.get(Court, court_id)
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Court not found",
        )
    return CourtResponse(
        message="Court retrieved successfully",
        data=await _to_court_read(session, court),
    )


@router.post("/{court_id}/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_new_booking(
    court_id: str,
    payload: BookingCreate,
    session: AsyncSession = Depends(get_session),
) -> BookingResponse:
    """Reservar quadra por período de tempo (com validação de disponibilidade)."""
    if payload.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Court ID mismatch in path and payload",
        )

    if payload.start_time >= payload.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )

    try:
        booking = await create_booking(session, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    return BookingResponse(
        message="Booking created successfully",
        data=booking,
    )


@router.get("/{court_id}/availability", status_code=status.HTTP_200_OK)
async def check_availability(
    court_id: str,
    start_time: str,
    end_time: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Verificar disponibilidade de quadra em período específico."""
    from datetime import datetime

    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format (use ISO 8601)",
        )

    available = await check_booking_availability(session, court_id, start, end)
    return {
        "court_id": court_id,
        "available": available,
        "start_time": start_time,
        "end_time": end_time,
    }


@router.get("/bookings/my", response_model=BookingListResponse, status_code=status.HTTP_200_OK)
async def list_my_bookings(
    user_id: str,
    status_filter: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> BookingListResponse:
    """Listar reservas do usuário para seção 'Meus Agendamentos'."""
    bookings = await list_user_bookings(session, user_id=user_id, status_filter=status_filter, limit=limit)
    return BookingListResponse(
        message="Bookings retrieved successfully",
        data=bookings,
        meta={"count": len(bookings), "status_filter": status_filter},
    )
