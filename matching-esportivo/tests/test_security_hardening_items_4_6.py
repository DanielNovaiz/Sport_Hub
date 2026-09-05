"""Suíte de aceite — Itens 4–6 (Hardening de segurança).

Codifica os critérios de aceite de ``SECURITY_HARDENING_PLAN_ITEMS_4_6.md``.
Com os itens implementados, todos estes testes devem passar.
"""
from __future__ import annotations

import asyncio
import inspect

import pytest

from app.core import security
from app.core.security import SecurityError


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Item 4 — Hardening do JWT
# ---------------------------------------------------------------------------

def test_access_decode_rejects_refresh_token() -> None:
    access = security.encode_access_token("user-1")
    refresh, _ = security.encode_refresh_token("user-1")

    assert security.decode_access_token(access)["sub"] == "user-1"
    with pytest.raises(SecurityError):
        security.decode_access_token(refresh)


def test_refresh_decode_rejects_access_token() -> None:
    access = security.encode_access_token("user-1")
    refresh, _ = security.encode_refresh_token("user-1")

    assert security.decode_refresh_token(refresh)["type"] == "refresh"
    with pytest.raises(SecurityError):
        security.decode_refresh_token(access)


def test_jwt_includes_standard_claims() -> None:
    payload = security.decode_access_token(security.encode_access_token("user-1"))

    assert payload["type"] == "access"
    assert "iat" in payload
    assert "aud" in payload
    assert "iss" in payload
    assert "jti" in payload


# ---------------------------------------------------------------------------
# Item 5 — Rate limit em /api/auth/*
# ---------------------------------------------------------------------------

def test_rate_limit_blocks_after_threshold(monkeypatch) -> None:
    from app.core import rate_limit

    sig = inspect.signature(rate_limit.is_rate_limited)
    assert {"key", "limit", "window_seconds"}.issubset(set(sig.parameters))

    class FakeRedis:
        def __init__(self) -> None:
            self.counts: dict[str, int] = {}

        async def incr(self, key: str) -> int:
            self.counts[key] = self.counts.get(key, 0) + 1
            return self.counts[key]

        async def expire(self, key: str, seconds: int) -> bool:
            return True

    fake = FakeRedis()

    async def fake_get_redis():
        return fake

    monkeypatch.setattr("app.core.rate_limit.get_redis", fake_get_redis)

    # limite = 3 chamadas permitidas; a 4ª é bloqueada
    for _ in range(3):
        assert _run(rate_limit.is_rate_limited("auth-login:1.2.3.4", 3, 60)) is False
    assert _run(rate_limit.is_rate_limited("auth-login:1.2.3.4", 3, 60)) is True


# ---------------------------------------------------------------------------
# Item 6 — Healthchecks sem informação interna
# ---------------------------------------------------------------------------

def test_health_endpoints_do_not_leak_internal_error() -> None:
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    try:
        response = client.get("/health")
    finally:
        client.close()

    assert response.status_code in {200, 503}
    assert "error" not in response.json()

