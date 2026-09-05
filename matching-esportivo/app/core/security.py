"""Utilitários de segurança (JWT + sanitização)."""

from __future__ import annotations

import hashlib
import html
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

_TOKEN_PREFIX = "bearer "
_ALLOWED_TEXT_PATTERN = re.compile(r"[^\w\s\-.,:;!?@()#/]+", re.UNICODE)


class SecurityError(ValueError):
    """Erro de validação de segurança para input/token."""


def decode_jwt_subject_from_header(authorization_header: str | None) -> str:
    if not authorization_header:
        raise SecurityError("missing_authorization_header")

    safe_header = authorization_header.strip()
    if not safe_header.lower().startswith(_TOKEN_PREFIX):
        raise SecurityError("invalid_authorization_scheme")

    token = safe_header[len(_TOKEN_PREFIX) :].strip()
    if not token:
        raise SecurityError("missing_bearer_token")

    payload = decode_access_token(token)
    return payload["sub"]


def sanitize_text(value: str | None, *, max_len: int | None = None) -> str | None:
    if value is None:
        return None

    trimmed = value.strip()
    if max_len is not None:
        trimmed = trimmed[:max_len]

    cleaned = _ALLOWED_TEXT_PATTERN.sub("", trimmed)
    escaped = html.escape(cleaned, quote=True)
    return escaped


def sanitize_text_dict(payload: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    sanitized = dict(payload)
    for key in keys:
        value = sanitized.get(key)
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
    return sanitized


# ============================================================================
# Hash de senha (scrypt via stdlib) — nunca armazenar/comparar texto puro.
# Formato do hash: scrypt$N$R$P$salt_hex$digest_hex
# ============================================================================

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_HASH_DIGEST_LEN = 64


def hash_password(password: str) -> str:
    """Gera hash scrypt com salt aleatório de 16 bytes."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_HASH_DIGEST_LEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Verifica senha contra hash gerado por ``hash_password``."""
    try:
        scheme, n, r, p, salt_hex, digest_hex = encoded.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=_HASH_DIGEST_LEN,
        )
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(bytes.fromhex(digest_hex), digest)


# ============================================================================
# JWT — claims padronizados (iat/aud/iss/type/jti) e decode tipado.
# ============================================================================

_TOKEN_AUDIENCE = "sport-hub-api"
_TOKEN_ISSUER = "sport-hub"
_REFRESH_TTL_MINUTES = 7 * 24 * 60  # 7 dias


def _encode_token(user_id: str, token_type: str, ttl_minutes: int) -> tuple[str, str]:
    now = datetime.now(UTC)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": user_id,
        "user_id": user_id,
        "type": token_type,
        "aud": _TOKEN_AUDIENCE,
        "iss": _TOKEN_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def encode_access_token(user_id: str) -> str:
    """Emite access token com claims padrão (type=access)."""
    token, _ = _encode_token(user_id, "access", settings.access_token_expire_minutes)
    return token


def encode_refresh_token(user_id: str) -> tuple[str, str]:
    """Emite refresh token; retorna (token, jti) para permitir revogação."""
    return _encode_token(user_id, "refresh", _REFRESH_TTL_MINUTES)


def _decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=_TOKEN_AUDIENCE,
            issuer=_TOKEN_ISSUER,
        )
    except JWTError as error:
        raise SecurityError("invalid_jwt_token") from error

    if payload.get("type") != expected_type:
        raise SecurityError(f"invalid_jwt_token_type_{expected_type}")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise SecurityError("jwt_subject_missing")
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    """Valida access token (assinatura, aud/iss, exp e type=access)."""
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Valida refresh token (assinatura, aud/iss, exp e type=refresh)."""
    return _decode_token(token, "refresh")
