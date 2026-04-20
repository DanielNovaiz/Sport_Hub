"""Endpoints do feed personalizado."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.event import PersonalizedFeedResponse
from app.services.event_service import get_personalized_feed

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("/", response_model=PersonalizedFeedResponse)
async def feed_endpoint(
    user_id: str = Query(..., min_length=1),
    radius_km: float = Query(15.0, ge=0.1, le=100.0),
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PersonalizedFeedResponse:
    """Input: user_id. Output: feed personalizado por raio e interesse."""
    return await get_personalized_feed(user_id, session, radius_km=radius_km, limit=limit)