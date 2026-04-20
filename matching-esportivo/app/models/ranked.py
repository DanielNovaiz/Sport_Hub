"""Modelos de ranking e competição."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlmodel import Field, SQLModel


class LeagueDivisionEnum(str, Enum):
    """Divisões competitivas."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    IMMORTAL = "immortal"
    GLOBAL = "global"


class UserRank(SQLModel, table=True):
    """Sistema de MMR e divisões para competição."""

    __tablename__ = "user_rank"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", unique=True, index=True)
    mmr: int = Field(default=1000, ge=0, index=True)
    division: LeagueDivisionEnum = Field(default=LeagueDivisionEnum.BRONZE, index=True)
    league: str = Field(default="bronze", min_length=5, max_length=10, index=True)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
