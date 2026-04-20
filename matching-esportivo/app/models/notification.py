"""Modelo de notificações em tempo real e persistidas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel

NotificationType = Literal["invite", "match", "event_update"]


class Notification(SQLModel, table=True):
    """Input: conteúdo de notificação. Output: registro persistido."""

    __tablename__ = "notification"
    __table_args__ = (
        Index("idx_notification_user_id", "user_id"),
        Index("idx_notification_is_read", "is_read"),
        Index("idx_notification_created_at", "created_at"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    content: str = Field(min_length=2, max_length=500)
    type: str = Field(default="event_update", index=True, min_length=5, max_length=12)
    is_read: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))