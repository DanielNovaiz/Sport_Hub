"""Serviço de notificações persistidas."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import NotificationRead


async def list_notifications(
    user_id: str,
    session: AsyncSession,
    limit: int = 50,
) -> list[NotificationRead]:
    """Input: user_id. Output: notificações mais recentes do usuário."""
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(query)
    notifications = result.scalars().all()
    return [NotificationRead.model_validate(notification) for notification in notifications]


async def create_notification(
    session: AsyncSession,
    user_id: str,
    content: str,
    notification_type: str = "event_update",
) -> Notification:
    """Input: conteúdo/usuário. Output: notificação persistida."""
    notification = Notification(user_id=user_id, content=content, type=notification_type)
    session.add(notification)
    await session.flush()
    return notification