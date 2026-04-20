"""Schemas de quadras e reservas (marketplace)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.court import BookingStatusEnum


class CourtCreate(BaseModel):
    owner_id: str
    name: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    sport_type: str = Field(min_length=2, max_length=50)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    price_per_hour: float = Field(default=100.0, ge=0)
    photos_url: list[str] = Field(default_factory=list)


class CourtRead(BaseModel):
    id: str
    owner_id: str
    name: str
    description: str | None
    sport_type: str
    price_per_hour: float
    photos_url: list[str]
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourtResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: CourtRead
    meta: dict[str, Any] = Field(default_factory=dict)


class CourtListResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: list[CourtRead]
    meta: dict[str, Any] = Field(default_factory=dict)


class BookingCreate(BaseModel):
    court_id: str
    user_id: str
    start_time: datetime
    end_time: datetime


class BookingRead(BaseModel):
    id: str
    court_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    status: BookingStatusEnum
    total_price: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: BookingRead
    meta: dict[str, Any] = Field(default_factory=dict)


class BookingWithCourtRead(BookingRead):
    court: CourtRead


class BookingListResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: list[BookingWithCourtRead]
    meta: dict[str, Any] = Field(default_factory=dict)
