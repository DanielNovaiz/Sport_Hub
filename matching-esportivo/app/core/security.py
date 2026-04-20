"""Utilitários de segurança (JWT + sanitização)."""

from __future__ import annotations

import html
import re
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

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as error:
        raise SecurityError("invalid_jwt_token") from error

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise SecurityError("jwt_subject_missing")

    return subject.strip()


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
