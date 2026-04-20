"""Schemas de notificações persistidas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationType = Literal["invite", "match", "event_update"]


class NotificationRead(BaseModel):
    """Input: entidade Notification ORM. Output: payload serializável."""

    id: str
    user_id: str
    content: str
    type: NotificationType
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Input: lista de notificações. Output: envelope padronizado."""

    status: Literal["success"] = "success"
    message: str
    data: list[NotificationRead]
    meta: dict[str, Any] = Field(default_factory=dict)