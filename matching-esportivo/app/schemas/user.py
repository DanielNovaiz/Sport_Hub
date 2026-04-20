"""Schemas Pydantic V2 para usuários e interesses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import sanitize_text

UserSkillLevel = Literal["beginner", "intermediate", "advanced"]


class UserInterestBase(BaseModel):
    sport: str = Field(min_length=2, max_length=50)
    skill_level: UserSkillLevel = Field(default="intermediate")
    is_primary: bool = Field(default=False)

    @field_validator("sport", mode="before")
    @classmethod
    def sanitize_sport(cls, value: str) -> str:
        return sanitize_text(value, max_len=50) or ""


class UserInterestCreate(UserInterestBase):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class UserInterestRead(UserInterestBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=3, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("username", "full_name", "phone", "avatar_url", "bio", mode="before")
    @classmethod
    def sanitize_profile_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        max_len = 500 if len(value) > 200 else 200
        return sanitize_text(value, max_len=max_len)


class UserCreate(UserBase):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    interests: list[UserInterestCreate] = Field(default_factory=list)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=50)
    full_name: str | None = Field(default=None, min_length=3, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    is_verified: bool | None = None
    interests: list[UserInterestCreate] | None = None

    @field_validator("username", "full_name", "phone", "avatar_url", "bio", mode="before")
    @classmethod
    def sanitize_update_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        max_len = 500 if len(value) > 200 else 200
        return sanitize_text(value, max_len=max_len)


class UserRead(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    interests: list[UserInterestRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserDeleteData(BaseModel):
    id: str


class UserResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: UserRead
    meta: dict[str, Any] = Field(default_factory=dict)


class UserListResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: list[UserRead]
    meta: dict[str, Any] = Field(default_factory=dict)


class UserDeleteResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: UserDeleteData
    meta: dict[str, Any] = Field(default_factory=dict)


class PlayerStatsBase(BaseModel):
    position: str = Field(default="meia", min_length=3, max_length=20)
    pace: int = Field(default=50, ge=0, le=99)
    shooting: int = Field(default=50, ge=0, le=99)
    passing: int = Field(default=50, ge=0, le=99)
    defense: int = Field(default=50, ge=0, le=99)
    physical: int = Field(default=50, ge=0, le=99)
    technique: int = Field(default=50, ge=0, le=99)

    short_finish: int = Field(default=50, ge=0, le=99)
    long_shot: int = Field(default=50, ge=0, le=99)
    heading: int = Field(default=50, ge=0, le=99)
    free_kick: int = Field(default=50, ge=0, le=99)
    short_pass: int = Field(default=50, ge=0, le=99)
    long_pass: int = Field(default=50, ge=0, le=99)
    crossing: int = Field(default=50, ge=0, le=99)
    dribbling: int = Field(default=50, ge=0, le=99)
    ball_shielding: int = Field(default=50, ge=0, le=99)
    sprint: int = Field(default=50, ge=0, le=99)
    acceleration: int = Field(default=50, ge=0, le=99)
    stamina: int = Field(default=50, ge=0, le=99)
    tackle: int = Field(default=50, ge=0, le=99)
    interception: int = Field(default=50, ge=0, le=99)
    marking: int = Field(default=50, ge=0, le=99)

    reflexes: int = Field(default=50, ge=0, le=99)
    elasticity: int = Field(default=50, ge=0, le=99)
    box_presence: int = Field(default=50, ge=0, le=99)
    distribution: int = Field(default=50, ge=0, le=99)

    spike_power: int = Field(default=50, ge=0, le=99)
    spike_accuracy: int = Field(default=50, ge=0, le=99)
    serve_power: int = Field(default=50, ge=0, le=99)
    serve_tactical: int = Field(default=50, ge=0, le=99)
    reception: int = Field(default=50, ge=0, le=99)
    floor_defense: int = Field(default=50, ge=0, le=99)
    coverage: int = Field(default=50, ge=0, le=99)
    setting: int = Field(default=50, ge=0, le=99)
    creativity: int = Field(default=50, ge=0, le=99)
    game_vision: int = Field(default=50, ge=0, le=99)
    lateral_agility: int = Field(default=50, ge=0, le=99)
    reaction: int = Field(default=50, ge=0, le=99)
    coordination: int = Field(default=50, ge=0, le=99)
    sand_agility: int = Field(default=50, ge=0, le=99)
    jumping_endurance: int = Field(default=50, ge=0, le=99)

    shoot_long: int = Field(default=50, ge=0, le=99)
    shoot_mid: int = Field(default=50, ge=0, le=99)
    shoot_short: int = Field(default=50, ge=0, le=99)
    finishing: int = Field(default=50, ge=0, le=99)

    velocity: int = Field(default=50, ge=0, le=99)
    jump: int = Field(default=50, ge=0, le=99)
    agility: int = Field(default=50, ge=0, le=99)
    energy: int = Field(default=50, ge=0, le=99)
    strength: int = Field(default=50, ge=0, le=99)
    balance: int = Field(default=50, ge=0, le=99)

    ball_control: int = Field(default=50, ge=0, le=99)
    vision: int = Field(default=50, ge=0, le=99)
    dribble: int = Field(default=50, ge=0, le=99)

    steal: int = Field(default=50, ge=0, le=99)
    block: int = Field(default=50, ge=0, le=99)
    perim_def: int = Field(default=50, ge=0, le=99)
    post_def: int = Field(default=50, ge=0, le=99)

    rebound: int = Field(default=50, ge=0, le=99)
    reb_predict: int = Field(default=50, ge=0, le=99)
    combativeness: int = Field(default=50, ge=0, le=99)


class PlayerStatsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    user_id: str
    position: str | None = Field(default=None, min_length=3, max_length=20)
    pace: int | None = Field(default=None, ge=0, le=99)
    shooting: int | None = Field(default=None, ge=0, le=99)
    passing: int | None = Field(default=None, ge=0, le=99)
    defense: int | None = Field(default=None, ge=0, le=99)
    physical: int | None = Field(default=None, ge=0, le=99)
    technique: int | None = Field(default=None, ge=0, le=99)

    short_finish: int | None = Field(default=None, ge=0, le=99)
    long_shot: int | None = Field(default=None, ge=0, le=99)
    heading: int | None = Field(default=None, ge=0, le=99)
    free_kick: int | None = Field(default=None, ge=0, le=99)
    short_pass: int | None = Field(default=None, ge=0, le=99)
    long_pass: int | None = Field(default=None, ge=0, le=99)
    crossing: int | None = Field(default=None, ge=0, le=99)
    dribbling: int | None = Field(default=None, ge=0, le=99)
    ball_shielding: int | None = Field(default=None, ge=0, le=99)
    sprint: int | None = Field(default=None, ge=0, le=99)
    acceleration: int | None = Field(default=None, ge=0, le=99)
    stamina: int | None = Field(default=None, ge=0, le=99)
    tackle: int | None = Field(default=None, ge=0, le=99)
    interception: int | None = Field(default=None, ge=0, le=99)
    marking: int | None = Field(default=None, ge=0, le=99)

    reflexes: int | None = Field(default=None, ge=0, le=99)
    elasticity: int | None = Field(default=None, ge=0, le=99)
    box_presence: int | None = Field(default=None, ge=0, le=99)
    distribution: int | None = Field(default=None, ge=0, le=99)

    spike_power: int | None = Field(default=None, ge=0, le=99)
    spike_accuracy: int | None = Field(default=None, ge=0, le=99)
    serve_power: int | None = Field(default=None, ge=0, le=99)
    serve_tactical: int | None = Field(default=None, ge=0, le=99)
    reception: int | None = Field(default=None, ge=0, le=99)
    floor_defense: int | None = Field(default=None, ge=0, le=99)
    coverage: int | None = Field(default=None, ge=0, le=99)
    setting: int | None = Field(default=None, ge=0, le=99)
    creativity: int | None = Field(default=None, ge=0, le=99)
    game_vision: int | None = Field(default=None, ge=0, le=99)
    lateral_agility: int | None = Field(default=None, ge=0, le=99)
    reaction: int | None = Field(default=None, ge=0, le=99)
    coordination: int | None = Field(default=None, ge=0, le=99)
    sand_agility: int | None = Field(default=None, ge=0, le=99)
    jumping_endurance: int | None = Field(default=None, ge=0, le=99)

    shoot_long: int | None = Field(default=None, ge=0, le=99)
    shoot_mid: int | None = Field(default=None, ge=0, le=99)
    shoot_short: int | None = Field(default=None, ge=0, le=99)
    finishing: int | None = Field(default=None, ge=0, le=99)

    velocity: int | None = Field(default=None, ge=0, le=99)
    jump: int | None = Field(default=None, ge=0, le=99)
    agility: int | None = Field(default=None, ge=0, le=99)
    energy: int | None = Field(default=None, ge=0, le=99)
    strength: int | None = Field(default=None, ge=0, le=99)
    balance: int | None = Field(default=None, ge=0, le=99)

    ball_control: int | None = Field(default=None, ge=0, le=99)
    vision: int | None = Field(default=None, ge=0, le=99)
    dribble: int | None = Field(default=None, ge=0, le=99)

    steal: int | None = Field(default=None, ge=0, le=99)
    block: int | None = Field(default=None, ge=0, le=99)
    perim_def: int | None = Field(default=None, ge=0, le=99)
    post_def: int | None = Field(default=None, ge=0, le=99)

    rebound: int | None = Field(default=None, ge=0, le=99)
    reb_predict: int | None = Field(default=None, ge=0, le=99)
    combativeness: int | None = Field(default=None, ge=0, le=99)

    @field_validator("user_id", "position", mode="before")
    @classmethod
    def sanitize_stats_identifiers(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return sanitize_text(value, max_len=64)


class UserXPRead(BaseModel):
    id: str
    user_id: str
    attribute_name: str
    level: int
    residual_xp: int
    total_xp: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAchievementRead(BaseModel):
    id: str
    user_id: str
    code: str
    title: str
    tier: str
    execution_count: int
    bonus_attribute: str | None = None
    bonus_value: int
    last_triggered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlayerStatsRead(PlayerStatsBase):
    id: str
    user_id: str
    overall: int
    playstyle_archetype: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlayerStatsResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: PlayerStatsRead
    meta: dict[str, Any] = Field(default_factory=dict)


class UserProfileCard(BaseModel):
    user: UserRead
    stats: PlayerStatsRead
    sport_type: str = Field(default="FOOTBALL")
    overall_by_position: int = Field(default=50, ge=0, le=99)
    season_code: str | None = None
    season_level: int = Field(default=0, ge=0)
    season_xp_total: int = Field(default=0, ge=0)
    season_frame: str | None = None
    season_badges: list[str] = Field(default_factory=list)
    xp_progress: float = Field(default=0.0, ge=0.0, le=1.0)
    xp_residual_total: int = Field(default=0, ge=0)
    synergy_badges: list[str] = Field(default_factory=list)
    xp_entries: list[UserXPRead] = Field(default_factory=list)
    achievements: list[UserAchievementRead] = Field(default_factory=list)


class UserProfileResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    data: UserProfileCard
    meta: dict[str, Any] = Field(default_factory=dict)
