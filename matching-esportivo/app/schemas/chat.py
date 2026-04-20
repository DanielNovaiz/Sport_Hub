"""Schemas de chat e comunicação em tempo real."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    chat_room_id: str
    user_id: str
    content: str = Field(min_length=1, max_length=500)


class ChatMessageRead(BaseModel):
    id: str
    chat_room_id: str
    user_id: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRoomRead(BaseModel):
    id: str
    event_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRoomResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: ChatRoomRead
    meta: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: ChatMessageRead
    meta: dict[str, Any] = Field(default_factory=dict)


class ChatMessageListResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: list[ChatMessageRead]
    meta: dict[str, Any] = Field(default_factory=dict)
