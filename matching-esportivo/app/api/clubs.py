"""Endpoints de clubes esportivos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.club import (
    ClubCreate,
    ClubJoinRequest,
    ClubJoinResponse,
    ClubNearbyResponse,
    ClubMembershipReviewRequest,
    ClubMembershipReviewResponse,
    ClubResponse,
    TeamSynergyCardRead,
    TeamSynergyCardResponse,
)
from app.schemas.event import UserLocation
from app.services.club_service import (
    create_club,
    has_high_synergy,
    list_user_synergy_badges,
    request_club_join,
    review_club_membership,
    search_nearby_clubs,
)

router = APIRouter(prefix="/api/clubs", tags=["clubs"])


@router.post("/", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club_endpoint(
    payload: ClubCreate,
    session: AsyncSession = Depends(get_session),
) -> ClubResponse:
    """Input: ClubCreate. Output: clube criado."""
    try:
        club = await create_club(payload, session)
    except ValueError as error:
        if str(error) == "club_create_failed":
            raise HTTPException(status_code=400, detail="club_create_failed")
        raise
    return ClubResponse(message="club_created", data=club)


@router.get("/nearby", response_model=ClubNearbyResponse)
async def nearby_clubs_endpoint(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    sport_type: str | None = Query(default=None, min_length=2, max_length=50),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ClubNearbyResponse:
    """Input: localização/sport_type. Output: clubes em raio fixo de 10km."""
    location = UserLocation(latitude=latitude, longitude=longitude)
    clubs = await search_nearby_clubs(location, session, sport_type=sport_type, limit=limit)
    return ClubNearbyResponse(
        message="nearby_clubs_found",
        data=clubs,
        meta={"radius_km": 10, "count": len(clubs), "sport_type": sport_type},
    )


@router.post("/{club_id}/join", response_model=ClubJoinResponse)
async def join_club_endpoint(
    club_id: str,
    payload: ClubJoinRequest,
    session: AsyncSession = Depends(get_session),
) -> ClubJoinResponse:
    """Input: club_id/user_id. Output: membership member/pending."""
    try:
        membership = await request_club_join(club_id, payload.user_id, session)
    except ValueError as error:
        message = str(error)
        if message == "club_not_found":
            raise HTTPException(status_code=404, detail=message)
        if message == "membership_already_exists":
            raise HTTPException(status_code=409, detail=message)
        raise
    return ClubJoinResponse(
        message="club_join_requested",
        data=membership,
        meta={"club_id": club_id, "membership_status": membership.status},
    )


@router.post("/{club_id}/members/{user_id}/approve", response_model=ClubMembershipReviewResponse)
async def approve_club_member_endpoint(
    club_id: str,
    user_id: str,
    payload: ClubMembershipReviewRequest,
    session: AsyncSession = Depends(get_session),
) -> ClubMembershipReviewResponse:
    """Input: reviewer/target. Output: membership aprovada."""
    try:
        membership = await review_club_membership(club_id, user_id, payload.reviewer_id, True, session)
    except ValueError as error:
        message = str(error)
        if message == "club_not_found":
            raise HTTPException(status_code=404, detail=message)
        if message in {"reviewer_not_authorized", "membership_not_found", "membership_not_pending"}:
            raise HTTPException(status_code=403 if message == "reviewer_not_authorized" else 404, detail=message)
        raise
    return ClubMembershipReviewResponse(
        message="club_membership_approved",
        data=membership,
        meta={"club_id": club_id, "user_id": user_id, "approved": True},
    )


@router.post("/{club_id}/members/{user_id}/reject", response_model=ClubMembershipReviewResponse)
async def reject_club_member_endpoint(
    club_id: str,
    user_id: str,
    payload: ClubMembershipReviewRequest,
    session: AsyncSession = Depends(get_session),
) -> ClubMembershipReviewResponse:
    """Input: reviewer/target. Output: membership removida."""
    try:
        await review_club_membership(club_id, user_id, payload.reviewer_id, False, session)
    except ValueError as error:
        message = str(error)
        if message == "club_not_found":
            raise HTTPException(status_code=404, detail=message)
        if message in {"reviewer_not_authorized", "membership_not_found", "membership_not_pending"}:
            raise HTTPException(status_code=403 if message == "reviewer_not_authorized" else 404, detail=message)
        raise
    return ClubMembershipReviewResponse(
        message="club_membership_rejected",
        data=None,
        meta={"club_id": club_id, "user_id": user_id, "rejected": True},
    )


@router.get("/{club_id}/members/{user_id}/synergy", response_model=TeamSynergyCardResponse)
async def user_synergy_card_endpoint(
    club_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> TeamSynergyCardResponse:
    """Input: club_id/user_id. Output: badges visuais de sinergia no card do clube."""
    badges = await list_user_synergy_badges(session=session, user_id=user_id, club_id=club_id)
    visual_bonus = any(has_high_synergy(badge) for badge in badges)
    payload = TeamSynergyCardRead(
        user_id=user_id,
        club_id=club_id,
        badges=badges,
        visual_bonus=visual_bonus,
    )
    return TeamSynergyCardResponse(
        message="club_team_synergy_loaded",
        data=payload,
        meta={"badges_count": len(badges), "visual_bonus": visual_bonus},
    )