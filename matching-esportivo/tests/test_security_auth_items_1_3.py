"""Suíte de aceite — Itens 1–3 (Autenticação e Autorização reais).

Codifica os critérios de aceite de ``SECURITY_AUTH_PLAN_ITEMS_1_3.md``.
Com os itens implementados, todos estes testes devem passar.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core import security
from app.core.config import settings


def _run(coro):
    return asyncio.run(coro)

# ---------------------------------------------------------------------------
# Item 1 — Hash de senha (nunca texto puro)
# ---------------------------------------------------------------------------

def test_hash_and_verify_password_roundtrip() -> None:
    hashed = security.hash_password("S3nh@Fort3!")
    assert hashed != "S3nh@Fort3!"  # nunca armazenar texto puro
    assert security.verify_password("S3nh@Fort3!", hashed) is True
    assert security.verify_password("senha-errada", hashed) is False


def test_hash_password_is_salted_and_non_deterministic() -> None:
    assert security.hash_password("mesma-senha") != security.hash_password("mesma-senha")
    assert len(security.hash_password("x")) > 20


# ---------------------------------------------------------------------------
# Item 2 — Login ligado ao modelo User real
# ---------------------------------------------------------------------------

def test_authenticate_user_success_and_failures() -> None:
    from app.models.user import User
    from app.services.user_service import authenticate_user
    from tests.conftest import FakeAsyncSession, FakeResult

    user = User(
        id="1",
        email="test@test.com",
        username="test",
        full_name="Test User",
        hashed_password=security.hash_password("senha123"),
        is_verified=True,
    )

    # e-mail com caixa diferente também deve autenticar
    ok = _run(authenticate_user(FakeAsyncSession(execute_results=[FakeResult(rows=[user])]), "TEST@test.com", "senha123"))
    assert ok is user

    bad = _run(authenticate_user(FakeAsyncSession(execute_results=[FakeResult(rows=[user])]), "test@test.com", "senha-errada"))
    assert bad is None

    unknown = _run(authenticate_user(FakeAsyncSession(execute_results=[FakeResult(rows=[])]), "nao-existe@test.com", "senha123"))
    assert unknown is None


# ---------------------------------------------------------------------------
# Item 3 — Dependência de autorização por rota
# ---------------------------------------------------------------------------

def test_require_user_returns_subject_for_valid_token() -> None:
    from app.api.deps import require_user

    token = security.encode_access_token("user-1")
    subject = _run(require_user(f"Bearer {token}"))
    assert subject == "user-1"


def test_require_user_rejects_missing_or_invalid_token() -> None:
    from app.api.deps import require_user

    with pytest.raises(HTTPException) as exc_info:
        _run(require_user(None))
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException):
        _run(require_user("Bearer token-invalido"))


def test_decode_rejects_missing_or_invalid_header() -> None:
    """Base real existente (decode_jwt_subject_from_header)."""
    from app.core.security import SecurityError, decode_jwt_subject_from_header

    with pytest.raises(SecurityError):
        decode_jwt_subject_from_header(None)
    with pytest.raises(SecurityError):
        decode_jwt_subject_from_header("Token sem-bearer")

