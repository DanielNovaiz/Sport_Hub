"""Modelos de quadras e reservas (marketplace)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from geoalchemy2 import Geometry
from pydantic import ConfigDict
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class BookingStatusEnum(str, Enum):
    """Status de uma reserva."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Court(SQLModel, table=True):
    """Quadra/campo disponível para reserva."""

    __tablename__ = "court"
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner_id: str = Field(foreign_key="user.id", index=True)
    name: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    sport_type: str = Field(min_length=2, max_length=50, index=True)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    )
    price_per_hour: float = Field(default=100.0, ge=0)
    photos_url: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Booking(SQLModel, table=True):
    """Reserva de uma quadra em um período de tempo."""

    __tablename__ = "booking"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    court_id: str = Field(foreign_key="court.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    start_time: datetime = Field(index=True)
    end_time: datetime = Field(index=True)
    status: BookingStatusEnum = Field(default=BookingStatusEnum.PENDING, index=True)
    total_price: float = Field(default=0.0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
