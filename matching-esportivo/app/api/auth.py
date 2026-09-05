"""Endpoints canônicos de autenticação (DB-backed)."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import auth_login_rate_limit
from app.core.database import get_session
from app.core.redis import get_redis
from app.core.security import (
    SecurityError,
    decode_refresh_token,
    encode_access_token,
    encode_refresh_token,
    hash_password,
)
from app.models.user import User
from app.services.user_service import authenticate_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_REFRESH_TTL_SECONDS = 7 * 24 * 60 * 60


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenUser(BaseModel):
    id: str
    email: EmailStr
    name: str
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: TokenUser


def _serialize_user(user: User) -> TokenUser:
    return TokenUser(id=user.id, email=user.email, name=user.full_name, avatar_url=user.avatar_url)


async def _revoke_refresh_jti(payload: dict[str, Any]) -> None:
    """Revoga o refresh token (jti) no Redis pelo tempo restante (best-effort)."""
    redis = await get_redis()
    jti = payload.get("jti")
    if redis is None or not jti:
        return
    try:
        exp = payload.get("exp")
        if hasattr(exp, "timestamp"):
            ttl_seconds = max(1, int(exp.timestamp() - datetime.now(UTC).timestamp()))
        else:
            ttl_seconds = _REFRESH_TTL_SECONDS
        await redis.set(f"auth:revoked:{jti}", "1", ex=ttl_seconds)
    except Exception as error:  # pragma: no cover - depende de infra externa.
        logger.warning("refresh_revocation_failed", extra={"error": str(error)})


async def _refresh_is_revoked(payload: dict[str, Any]) -> bool:
    redis = await get_redis()
    jti = payload.get("jti")
    if redis is None or not jti:
        return False
    try:
        return bool(await redis.exists(f"auth:revoked:{jti}"))
    except Exception as error:  # pragma: no cover - depende de infra externa.
        logger.warning("refresh_revocation_check_failed", extra={"error": str(error)})
        return False


async def seed_auth_user(session: AsyncSession) -> None:
    """Garante usuário de autenticação no banco a partir do env AUTH_USER_*.

    Em dev há defaults (test@test.com / senha123). Em produção, sem as variáveis,
    o seed é ignorado (a conta é criada por fora).
    """
    email = _env("AUTH_USER_EMAIL")
    raw_password = _env("AUTH_USER_PASSWORD")
    if not email or not raw_password:
        return
    normalized_email = email.strip().lower()
    result = await session.execute(select(User).where(func.lower(User.email) == normalized_email))
    existing = result.scalars().first()
    hashed = hash_password(raw_password)
    if existing is not None:
        if existing.hashed_password != hashed:
            existing.hashed_password = hashed
            session.add(existing)
        await session.commit()
        return
    username = _env("AUTH_USER_USERNAME") or normalized_email.split("@")[0]
    user = User(
        email=normalized_email,
        username=username,
        full_name=_env("AUTH_USER_NAME") or "Platform User",
        hashed_password=hashed,
        is_verified=True,
    )
    session.add(user)
    await session.commit()


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_login_rate_limit)])
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    user = await authenticate_user(session, request.email, request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    refresh_token, _ = encode_refresh_token(user.id)
    return TokenResponse(
        access_token=encode_access_token(user.id),
        refresh_token=refresh_token,
        user=_serialize_user(user),
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(auth_login_rate_limit)])
async def refresh_token(request: RefreshTokenRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    try:
        payload = decode_refresh_token(request.refresh_token)
    except SecurityError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token") from error

    if await _refresh_is_revoked(payload):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    user = await session.get(User, payload.get("user_id", ""))
    if user is None or payload.get("sub") != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    # Rotação: revoga o refresh usado e emite novo par.
    await _revoke_refresh_jti(payload)
    new_refresh, _ = encode_refresh_token(user.id)
    return TokenResponse(
        access_token=encode_access_token(user.id),
        refresh_token=new_refresh,
        user=_serialize_user(user),
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"message": "logout_ok"}
