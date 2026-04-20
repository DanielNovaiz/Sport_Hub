"""Modelos de clubes esportivos e associação de membros."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import Column, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel
from pydantic import ConfigDict

ClubPrivacyType = Literal["public", "private"]
ClubMemberStatus = Literal["admin", "member", "pending"]
TeamSynergyStatus = Literal["none", "dynamic_duo", "perfect_synergy"]


class Club(SQLModel, table=True):
    """Input: dados de clube. Output: tabela club persistente."""

    __tablename__ = "club"
    __table_args__ = (
        Index("idx_club_location_gist", "location", postgresql_using="gist"),
        Index(
            "idx_club_location_geography_gist",
            text("(location::geography)"),
            postgresql_using="gist",
        ),
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(min_length=2, max_length=120, index=True)
    description: str | None = Field(default=None, max_length=1000)
    owner_id: str = Field(foreign_key="user.id", index=True)
    sport_type: str = Field(min_length=2, max_length=50, index=True)
    privacy_type: str = Field(default="public", index=True, min_length=6, max_length=7)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ClubMember(SQLModel, table=True):
    """Input: relação user-club. Output: status de membresia persistido."""

    __tablename__ = "club_member"
    __table_args__ = (UniqueConstraint("user_id", "club_id", name="uq_club_member_user_club"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    club_id: str = Field(foreign_key="club.id", index=True)
    status: str = Field(default="pending", index=True, min_length=6, max_length=7)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TeamSynergy(SQLModel, table=True):
    """Persistência de sinergia em grupo (duplas/trios) dentro de clubes."""

    __tablename__ = "team_synergy"
    __table_args__ = (
        UniqueConstraint("club_id", "members_key", name="uq_team_synergy_club_members"),
        Index("idx_team_synergy_club_id", "club_id"),
        Index("idx_team_synergy_members_key", "members_key"),
        Index("idx_team_synergy_status", "status"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    club_id: str = Field(foreign_key="club.id", index=True)
    members_key: str = Field(min_length=5, max_length=512, index=True)
    group_size: int = Field(ge=2, le=3)
    status: str = Field(default="none", min_length=4, max_length=16, index=True)
    matches_together: int = Field(default=0, ge=0)
    wins_together: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    sport_type: str | None = Field(default=None, min_length=2, max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))