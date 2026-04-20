"""Endpoints de notificações do usuário."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.notification import NotificationListResponse
from app.services.notification_service import list_notifications

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def notifications_endpoint(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> NotificationListResponse:
    """Input: user_id. Output: lista de notificações do usuário."""
    notifications = await list_notifications(user_id, session, limit=limit)
    return NotificationListResponse(
        message="notifications_found",
        data=notifications,
        meta={"user_id": user_id, "count": len(notifications)},
    )