"""Endpoints canônicos de autenticação."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _env(name: str, default: str | None = None) -> str | None:
	value = os.getenv(name)
	if value is None or value.strip() == "":
		return default
	return value.strip()


@dataclass(frozen=True)
class AuthUser:
	id: str
	email: str
	name: str
	password: str
	avatar_url: str | None = None


def _bootstrap_user() -> AuthUser:
	dev_mode = settings.app_env != "production"
	email = _env("AUTH_USER_EMAIL", "test@test.com" if dev_mode else None)
	password = _env("AUTH_USER_PASSWORD", "senha123" if dev_mode else None)
	user_id = _env("AUTH_USER_ID", "1" if dev_mode else None)
	name = _env("AUTH_USER_NAME", "Test User" if dev_mode else None)
	avatar_url = _env("AUTH_USER_AVATAR_URL")

	missing = [
		field
		for field, value in {
			"AUTH_USER_EMAIL": email,
			"AUTH_USER_PASSWORD": password,
			"AUTH_USER_ID": user_id,
			"AUTH_USER_NAME": name,
		}.items()
		if not value
	]
	if missing:
		raise RuntimeError("Configuração de auth inválida. Ajuste: " + ", ".join(missing))

	return AuthUser(
		id=user_id,
		email=email,
		name=name,
		password=password,
		avatar_url=avatar_url,
	)


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


def _issue_access_token(user: AuthUser) -> str:
	payload: dict[str, Any] = {
		"sub": user.email,
		"user_id": user.id,
		"exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes),
		"type": "access",
	}
	return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _issue_refresh_token(user: AuthUser) -> str:
	payload: dict[str, Any] = {
		"sub": user.email,
		"user_id": user.id,
		"exp": datetime.now(UTC) + timedelta(days=7),
		"type": "refresh",
	}
	return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _serialize_user(user: AuthUser) -> TokenUser:
	return TokenUser(
		id=user.id,
		email=user.email,
		name=user.name,
		avatar_url=user.avatar_url,
	)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
	user = _bootstrap_user()

	if request.email.lower() != user.email.lower() or not secrets.compare_digest(request.password, user.password):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

	return TokenResponse(
		access_token=_issue_access_token(user),
		refresh_token=_issue_refresh_token(user),
		user=_serialize_user(user),
	)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
	try:
		payload = jwt.decode(request.refresh_token, settings.secret_key, algorithms=[settings.algorithm])
	except JWTError as error:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token") from error

	if payload.get("type") != "refresh":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

	user = _bootstrap_user()
	if payload.get("sub") != user.email or payload.get("user_id") != user.id:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

	return TokenResponse(
		access_token=_issue_access_token(user),
		refresh_token=request.refresh_token,
		user=_serialize_user(user),
	)


@router.post("/logout")
async def logout() -> dict[str, str]:
	return {"message": "logout_ok"}
