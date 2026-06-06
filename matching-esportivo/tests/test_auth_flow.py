from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from backend_auth_endpoints import router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_login_contract_returns_expected_schema() -> None:
    with _build_client() as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "test@test.com", "password": "senha123"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"access_token", "refresh_token", "user"}
    assert isinstance(payload["access_token"], str) and payload["access_token"]
    assert isinstance(payload["refresh_token"], str) and payload["refresh_token"]

    user = payload["user"]
    assert isinstance(user, dict)
    assert set(user.keys()) == {"id", "email", "name", "avatar_url"}


def test_login_invalid_credentials_returns_401() -> None:
    with _build_client() as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "test@test.com", "password": "senha-invalida"},
        )

    assert response.status_code == 401


def test_refresh_invalid_token_returns_401() -> None:
    with _build_client() as client:
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "token-invalido"},
        )

    assert response.status_code == 401


def test_refresh_expired_token_returns_401() -> None:
    expired_payload = {
        "sub": "test@test.com",
        "user_id": "1",
        "type": "refresh",
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm=settings.algorithm)

    with _build_client() as client:
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired_token},
        )

    assert response.status_code == 401
