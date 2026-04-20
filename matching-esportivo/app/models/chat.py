"""Modelos de chat e comunicação em tempo real."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class ChatRoom(SQLModel, table=True):
    """Sala de chat vinculada a um evento."""

    __tablename__ = "chat_room"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    event_id: str = Field(foreign_key="event.id", unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatMessage(SQLModel, table=True):
    """Mensagem em sala de chat."""

    __tablename__ = "chat_message"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    chat_room_id: str = Field(foreign_key="chat_room.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    content: str = Field(min_length=1, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
