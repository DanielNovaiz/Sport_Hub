"""Schemas de ranking e competição."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import sanitize_text
from app.models.ranked import LeagueDivisionEnum


class AchievementRead(BaseModel):
    code: str
    title: str
    description: str
    icon: str
    rarity: str
    progress: int = 0
    target: int = 0


class UserRankRead(BaseModel):
    id: str
    user_id: str
    mmr: int
    division: LeagueDivisionEnum
    league: str
    wins: int
    losses: int
    win_rate: float
    achievements: list[AchievementRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRankResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: UserRankRead
    meta: dict[str, Any] = Field(default_factory=dict)


class RankedUserRead(BaseModel):
    id: str
    user_id: str
    full_name: str
    username: str
    avatar_url: str | None = None
    mmr: int
    division: LeagueDivisionEnum
    league: str
    wins: int
    losses: int
    win_rate: float
    achievements: list[AchievementRead] = Field(default_factory=list)
    sport_type: str | None = None
    position: str | None = None
    overall: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RankedUsersResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: list[RankedUserRead]
    meta: dict[str, Any] = Field(default_factory=dict)


class BoxScoreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    user_id: str
    event_id: str | None = None
    club_id: str | None = None
    teammate_ids: list[str] = Field(default_factory=list)
    sport_type: str = Field(min_length=2, max_length=50)
    sub_type: str | None = Field(default=None, max_length=20)
    team_score: int = Field(default=0, ge=0)
    opponent_score: int = Field(default=0, ge=0)

    # Futebol
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    tackles: int = Field(default=0, ge=0)
    dribbles: int = Field(default=0, ge=0)

    # Vôlei
    aces: int = Field(default=0, ge=0)
    blocks: int = Field(default=0, ge=0)
    attacks: int = Field(default=0, ge=0)
    defenses: int = Field(default=0, ge=0)
    sets: int = Field(default=0, ge=0)

    @field_validator("sport_type", "sub_type", mode="before")
    @classmethod
    def sanitize_sport_fields(cls, value: str | None) -> str | None:
        return sanitize_text(value, max_len=50 if isinstance(value, str) else None)

    @field_validator("user_id", "event_id", "club_id", mode="before")
    @classmethod
    def sanitize_ids(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return sanitize_text(value, max_len=64)

    @field_validator("teammate_ids", mode="before")
    @classmethod
    def sanitize_teammates(cls, values: list[str] | None) -> list[str]:
        if not values:
            return []
        return [sanitize_text(value, max_len=64) or "" for value in values if isinstance(value, str)]


class BoxScoreResultRead(BaseModel):
    performance_id: str
    user_id: str
    event_id: str | None = None
    sport_type: str
    sub_type: str | None = None
    overall: int
    level_gains_total: int
    xp_gains: dict[str, int] = Field(default_factory=dict)
    triggered_achievements: list[str] = Field(default_factory=list)
    telemetry_logs: list[str] = Field(default_factory=list)
    processing_ms: float = 0.0
    slow_processing: bool = False
    synergy_status: str | None = None
    synergy_visual_bonus: bool = False
    xp_multiplier: float = 1.0
    season_code: str | None = None
    season_level: int = 0
    season_xp_total: int = 0
    season_frame: str | None = None


class BoxScoreResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: BoxScoreResultRead
    meta: dict[str, Any] = Field(default_factory=dict)
