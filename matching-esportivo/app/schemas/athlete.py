"""Schemas Pydantic para Atletas"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AthleteCreate(BaseModel):
    """Schema para criação de novo atleta"""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=3, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    preferred_sports: Optional[list[str]] = None
    search_radius_km: float = Field(default=15.0, ge=1.0, le=100.0)


class AthleteResponse(BaseModel):
    """Schema de resposta para atleta"""

    id: str
    email: str
    username: str
    full_name: str
    phone: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
