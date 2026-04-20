"""Schemas de clubes esportivos e membership."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import sanitize_text

ClubPrivacyType = Literal["public", "private"]
ClubMemberStatus = Literal["admin", "member", "pending"]


class ClubCreate(BaseModel):
    """Input: payload de clube. Output: entidade validada para persistência."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    owner_id: str
    sport_type: str = Field(min_length=2, max_length=50)
    privacy_type: ClubPrivacyType = Field(default="public")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("name", "description", "owner_id", "sport_type", mode="before")
    @classmethod
    def sanitize_club_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        max_len = 1000 if len(value) > 120 else 120
        return sanitize_text(value, max_len=max_len)


class ClubRead(BaseModel):
    """Input: entidade Club ORM. Output: payload serializável de clube."""

    id: str
    name: str
    description: str | None
    owner_id: str
    sport_type: str
    privacy_type: ClubPrivacyType
    created_at: datetime
    active_members: int = 0

    model_config = ConfigDict(from_attributes=True)


class ClubResponse(BaseModel):
    """Input: clube persistido/lido. Output: envelope padrão de resposta."""

    status: Literal["success"] = "success"
    message: str
    data: ClubRead
    meta: dict[str, Any] = Field(default_factory=dict)


class ClubNearbyResponse(BaseModel):
    """Input: lista de clubes próximos. Output: envelope de busca geográfica."""

    status: Literal["success"] = "success"
    message: str
    data: list[ClubRead]
    meta: dict[str, Any] = Field(default_factory=dict)


class ClubJoinRequest(BaseModel):
    """Input: solicitação de entrada no clube. Output: request validado."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    user_id: str

    @field_validator("user_id", mode="before")
    @classmethod
    def sanitize_user_id(cls, value: str) -> str:
        return sanitize_text(value, max_len=64) or ""


class ClubMemberRead(BaseModel):
    """Input: entidade ClubMember ORM. Output: payload de membership."""

    id: str
    user_id: str
    club_id: str
    status: ClubMemberStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClubJoinResponse(BaseModel):
    """Input: resultado de join. Output: envelope com status da membresia."""

    status: Literal["success"] = "success"
    message: str
    data: ClubMemberRead
    meta: dict[str, Any] = Field(default_factory=dict)


class ClubMembershipReviewRequest(BaseModel):
    """Input: reviewer do clube. Output: request validado para moderação."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    reviewer_id: str

    @field_validator("reviewer_id", mode="before")
    @classmethod
    def sanitize_reviewer_id(cls, value: str) -> str:
        return sanitize_text(value, max_len=64) or ""


class ClubMembershipReviewResponse(BaseModel):
    """Input: revisão de membership. Output: envelope com resultado da moderação."""

    status: Literal["success"] = "success"
    message: str
    data: ClubMemberRead | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class TeamSynergyCardRead(BaseModel):
    """Input: status de sinergia de um usuário no clube. Output: payload visual de card."""

    user_id: str
    club_id: str
    badges: list[str] = Field(default_factory=list)
    visual_bonus: bool = False


class TeamSynergyCardResponse(BaseModel):
    """Envelope do card visual de sinergia."""

    status: Literal["success"] = "success"
    message: str
    data: TeamSynergyCardRead
    meta: dict[str, Any] = Field(default_factory=dict)