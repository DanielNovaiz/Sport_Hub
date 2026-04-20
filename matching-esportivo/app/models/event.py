"""Modelos de eventos e participantes para partidas dinâmicas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import Column, UniqueConstraint
from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

EventStatus = Literal["open", "full", "finished"]
EventParticipantStatus = Literal["confirmed", "waitlist"]


class Event(SQLModel, table=True):
    """Input: atributos de evento. Output: tabela event persistente."""

    __tablename__ = "event"
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    creator_id: str = Field(foreign_key="user.id", index=True)
    club_id: str | None = Field(default=None, foreign_key="club.id", index=True)
    sport_type: str = Field(min_length=2, max_length=50, index=True)
    sub_type: str | None = Field(default=None, max_length=20, index=True)
    scheduled_time: datetime = Field(index=True)
    status: str = Field(default="open", index=True, min_length=4, max_length=8)
    max_participants: int = Field(default=10, ge=2, le=100)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    )


class EventParticipant(SQLModel, table=True):
    """Ligação entre usuário e evento com status de inscrição."""

    __tablename__ = "event_participant"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_event_participant_user_event"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    event_id: str = Field(foreign_key="event.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = Field(default="confirmed", index=True, min_length=5, max_length=9)


Match = Event
