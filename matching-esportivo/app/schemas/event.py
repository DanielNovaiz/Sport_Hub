"""Schemas de eventos para descoberta de ativos."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EventStatus = Literal["open", "full", "finished"]
EventParticipantStatus = Literal["confirmed", "waitlist"]


class UserLocation(BaseModel):
    """Input: latitude e longitude. Output: localização validada."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class EventSearchFilters(BaseModel):
    """Input: filtros opcionais. Output: objeto de filtros normalizado."""

    sport_type: str | None = Field(default=None, min_length=2, max_length=50)
    limit: int = Field(default=20, ge=1, le=100)


class EventCreate(BaseModel):
    """Input: payload de criação. Output: evento válido para persistência."""

    creator_id: str
    club_id: str | None = None
    sport_type: str = Field(min_length=2, max_length=50)
    sub_type: str | None = Field(default=None, max_length=20)
    scheduled_time: datetime
    status: EventStatus = Field(default="open")
    max_participants: int = Field(default=10, ge=2, le=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class EventRead(BaseModel):
    """Input: entidade Event ORM. Output: payload serializável para API."""

    id: str
    creator_id: str
    club_id: str | None = None
    sport_type: str
    sub_type: str | None = None
    scheduled_time: datetime
    status: EventStatus
    max_participants: int

    model_config = ConfigDict(from_attributes=True)


class EventSearchResponse(BaseModel):
    """Input: lista de eventos. Output: envelope JSON padronizado."""

    status: Literal["success"] = "success"
    message: str
    data: list[EventRead]
    meta: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    """Input: evento criado/lido. Output: envelope JSON padronizado."""

    status: Literal["success"] = "success"
    message: str
    data: EventRead
    meta: dict[str, Any] = Field(default_factory=dict)


class JoinEventRequest(BaseModel):
    """Input: usuário autenticado (placeholder). Output: request validado para join."""

    user_id: str


class EventParticipantRead(BaseModel):
    """Input: entidade EventParticipant. Output: payload de inscrição."""

    id: str
    user_id: str
    event_id: str
    joined_at: datetime
    status: EventParticipantStatus

    model_config = ConfigDict(from_attributes=True)


class JoinEventResponse(BaseModel):
    """Input: inscrição de evento. Output: envelope de confirmação."""

    status: Literal["success"] = "success"
    message: str
    data: EventParticipantRead
    meta: dict[str, Any] = Field(default_factory=dict)


class SuggestedPlayerRead(BaseModel):
    """Input: linha de sugestão. Output: perfil simplificado para convite."""

    id: str
    name: str
    distance_km: float


class EventSuggestionsResponse(BaseModel):
    """Input: lista de jogadores sugeridos. Output: envelope padronizado."""

    status: Literal["success"] = "success"
    message: str
    data: list[SuggestedPlayerRead]
    meta: dict[str, Any] = Field(default_factory=dict)


class PersonalizedFeedItem(EventRead):
    """Input: evento do feed. Output: item enriquecido com ranking de clube."""

    title: str
    distance_km: float
    club_priority: bool = False
    confirmed_participants: int
    remaining_spots: int


class PersonalizedFeedResponse(BaseModel):
    """Input: lista de eventos personalizados. Output: envelope do feed."""

    status: Literal["success"] = "success"
    message: str
    data: list[PersonalizedFeedItem]
    meta: dict[str, Any] = Field(default_factory=dict)
