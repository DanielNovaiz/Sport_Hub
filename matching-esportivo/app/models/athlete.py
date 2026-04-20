"""Modelo de Atleta/Usuário"""

from datetime import UTC, datetime
from typing import Optional

from pydantic import ConfigDict
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field
import uuid


class Athlete(SQLModel, table=True):
    """
    Modelo de Atleta/Usuário da plataforma.
    
    Armazena informações do perfil do usuário e suas preferências esportivas.
    """

    __tablename__ = "athlete"
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ==================== IDENTIFICAÇÃO ====================
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="ID único do atleta",
    )

    # ==================== INFORMAÇÕES PESSOAIS ====================
    email: str = Field(
        unique=True,
        index=True,
        description="Email único do atleta",
    )
    username: str = Field(
        unique=True,
        index=True,
        min_length=3,
        max_length=50,
        description="Nome de usuário único",
    )
    full_name: str = Field(
        min_length=3,
        max_length=200,
        description="Nome completo do atleta",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Telefone para contato",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        description="URL da foto de perfil",
    )

    # ==================== LOCALIZAÇÃO ====================
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude última localização conhecida",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude última localização conhecida",
    )

    # ==================== PREFERÊNCIAS ESPORTIVAS ====================
    preferred_sports: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Lista de esportes de interesse",
    )
    skill_levels: dict[str, str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Nível de habilidade por esporte (ex: {'futsal': 'advanced'})",
    )
    search_radius_km: float = Field(
        default=15.0,
        ge=1.0,
        le=100.0,
        description="Raio de busca padrão em km",
    )

    # ==================== STATUS ====================
    is_active: bool = Field(
        default=True,
        description="Se o usuário está ativo",
    )
    is_verified: bool = Field(
        default=False,
        description="Se o email foi verificado",
    )

    # ==================== TIMESTAMPS ====================
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Data de criação da conta",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Data de última atualização",
    )
    last_login: Optional[datetime] = Field(
        default=None,
        description="Data do último login",
    )
