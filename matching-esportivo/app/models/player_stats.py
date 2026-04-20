"""Modelos de Bio & Stats, progressão e conquistas esportivas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel

PlayerPosition = Literal[
    "atacante",
    "zagueiro",
    "meia",
    "ala",
    "pivo",
    "goleiro",
]


class PlayerStats(SQLModel, table=True):
    """Atributos base do jogador e overall calculado automaticamente."""

    __tablename__ = "player_stats"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", unique=True, index=True)
    position: str = Field(default="meia", min_length=3, max_length=20, index=True)
    overall: int = Field(default=50, ge=0, le=99, index=True)
    playstyle_archetype: str = Field(default="Balanced", min_length=3, max_length=50, index=True)

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

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserXP(SQLModel, table=True):
    """XP residual por atributo para o motor de progressão."""

    __tablename__ = "user_xp"
    __table_args__ = (
        UniqueConstraint("user_id", "attribute_name", name="uq_user_xp_user_attribute"),
        Index("idx_user_xp_user_id", "user_id"),
        Index("idx_user_xp_attribute_name", "attribute_name"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    attribute_name: str = Field(min_length=3, max_length=50, index=True)
    level: int = Field(default=0, ge=0)
    residual_xp: int = Field(default=0, ge=0, le=59)
    total_xp: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserAchievement(SQLModel, table=True):
    """Conquistas persistidas com tier e contagem de execuções."""

    __tablename__ = "user_achievement"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_user_achievement_user_code"),
        Index("idx_user_achievement_user_id", "user_id"),
        Index("idx_user_achievement_code", "code"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    code: str = Field(min_length=3, max_length=50, index=True)
    title: str = Field(min_length=3, max_length=100)
    tier: str = Field(default="Bronze", min_length=3, max_length=20, index=True)
    execution_count: int = Field(default=0, ge=0)
    bonus_attribute: str | None = Field(default=None, max_length=50)
    bonus_value: int = Field(default=0, ge=0, le=99)
    last_triggered_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserPrestige(SQLModel, table=True):
    """XP de prestígio acumulado quando atributo já está no cap (99)."""

    __tablename__ = "user_prestige"
    __table_args__ = (
        UniqueConstraint("user_id", "attribute_name", name="uq_user_prestige_user_attribute"),
        Index("idx_user_prestige_user_id", "user_id"),
        Index("idx_user_prestige_attribute_name", "attribute_name"),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    attribute_name: str = Field(min_length=3, max_length=50, index=True)
    prestige_level: int = Field(default=0, ge=0)
    style_points: int = Field(default=0, ge=0)
    residual_xp: int = Field(default=0, ge=0, le=59)
    total_prestige_xp: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MatchPerformance(SQLModel, table=True):
    """Estatísticas de performance por partida."""

    __tablename__ = "match_performance"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    event_id: str | None = Field(default=None, foreign_key="event.id", index=True)
    sport_type: str = Field(min_length=2, max_length=50, index=True)
    sub_type: str | None = Field(default=None, max_length=20, index=True)

    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    points: int = Field(default=0, ge=0)
    rebounds: int = Field(default=0, ge=0)
    team_score: int = Field(default=0, ge=0)
    opponent_score: int = Field(default=0, ge=0)
    field_goals_made: int = Field(default=0, ge=0)
    field_goals_attempted: int = Field(default=0, ge=0)
    steals: int = Field(default=0, ge=0)
    blocks: int = Field(default=0, ge=0)

    # Box score futebol
    tackles: int = Field(default=0, ge=0)
    dribbles: int = Field(default=0, ge=0)

    # Box score vôlei
    aces: int = Field(default=0, ge=0)
    attacks: int = Field(default=0, ge=0)
    defenses: int = Field(default=0, ge=0)
    sets: int = Field(default=0, ge=0)

    # Box score basquete 3x3 (específico)
    two_point_makes: int = Field(default=0, ge=0, description="Cestas de 2pts (fora do arco)")
    clutch_rebounds: int = Field(default=0, ge=0, description="Rebotes no último minuto")
    last_minute_timestamp_sec: int | None = Field(default=None, description="Timestamp em segundos do último minuto")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)