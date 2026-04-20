"""Modelos de usuário e interesses com SQLModel."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from geoalchemy2 import Geometry
from pydantic import ConfigDict
from sqlalchemy import Column, Index, text
from sqlmodel import Field, Relationship, SQLModel

UserSkillLevel = Literal["beginner", "intermediate", "advanced"]


class User(SQLModel, table=True):
    """Tabela de usuários da plataforma."""

    __tablename__ = "user"
    __table_args__ = (
        Index("idx_user_location_gist", "location", postgresql_using="gist"),
        Index(
            "idx_user_location_geography_gist",
            text("(location::geography)"),
            postgresql_using="gist",
        ),
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    full_name: str = Field(min_length=3, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=500)
    location: Any | None = Field(
        default=None,
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), nullable=True),
    )
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: datetime | None = Field(default=None)

    interests: list["UserInterest"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class UserInterest(SQLModel, table=True):
    """Tabela de interesses esportivos do usuário."""

    __tablename__ = "user_interest"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    sport: str = Field(min_length=2, max_length=50, index=True)
    skill_level: str = Field(default="intermediate", min_length=5, max_length=12)
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: User | None = Relationship(back_populates="interests")
