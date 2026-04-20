"""Modelos de temporadas, rank sazonal e recompensas. """

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel


SeasonStatus = Literal["active", "closed"]
SeasonRewardKind = Literal["cosmetic_frame", "weekend_multiplier"]


class Season(SQLModel, table=True):
    """Janela de temporada de 3 meses."""

    __tablename__ = "season"
    __table_args__ = (
        UniqueConstraint("code", name="uq_season_code"),
        Index("idx_season_status", "status"),
        Index("idx_season_starts_at", "starts_at"),
        Index("idx_season_ends_at", "ends_at"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    code: str = Field(min_length=3, max_length=16, index=True)
    starts_at: datetime = Field(index=True)
    ends_at: datetime = Field(index=True)
    status: str = Field(default="active", min_length=6, max_length=12, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SeasonRank(SQLModel, table=True):
    """Rank sazonal do usuário com XP acumulado na temporada."""

    __tablename__ = "season_rank"
    __table_args__ = (
        UniqueConstraint("season_id", "user_id", name="uq_season_rank_season_user"),
        Index("idx_season_rank_season_id", "season_id"),
        Index("idx_season_rank_user_id", "user_id"),
        Index("idx_season_rank_xp_total", "xp_total"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    season_id: str = Field(foreign_key="season.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    xp_total: int = Field(default=0, ge=0)
    level: int = Field(default=0, ge=0)
    matches_played: int = Field(default=0, ge=0)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    last_match_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SeasonMilestone(SQLModel, table=True):
    """Marcos de temporada que liberam cosméticos ou multiplicadores."""

    __tablename__ = "season_milestone"
    __table_args__ = (
        UniqueConstraint("season_id", "required_level", name="uq_season_milestone_season_level"),
        Index("idx_season_milestone_season_id", "season_id"),
        Index("idx_season_milestone_required_level", "required_level"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    season_id: str = Field(foreign_key="season.id", index=True)
    required_level: int = Field(ge=1)
    reward_kind: str = Field(min_length=3, max_length=32)
    frame_code: str | None = Field(default=None, max_length=80)
    xp_multiplier: float = Field(default=1.0, ge=1.0)
    title: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SeasonRewardGrant(SQLModel, table=True):
    """Recompensa sazonal concedida ao usuário ao atingir um milestone."""

    __tablename__ = "season_reward_grant"
    __table_args__ = (
        UniqueConstraint("season_id", "user_id", "milestone_id", name="uq_season_reward_grant"),
        Index("idx_season_reward_grant_season_id", "season_id"),
        Index("idx_season_reward_grant_user_id", "user_id"),
        Index("idx_season_reward_grant_milestone_id", "milestone_id"),
        Index("idx_season_reward_grant_reward_kind", "reward_kind"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    season_id: str = Field(foreign_key="season.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    milestone_id: str = Field(foreign_key="season_milestone.id", index=True)
    reward_kind: str = Field(min_length=3, max_length=32)
    frame_code: str | None = Field(default=None, max_length=80)
    xp_multiplier: float = Field(default=1.0, ge=1.0)
    activation_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    claimed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
