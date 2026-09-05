"""Dependências FastAPI de autorização e proteção.

- ``require_user``: decodifica o header ``Authorization: Bearer <jwt>`` e devolve o
  ``subject`` (id do usuário) para uso nas rotas privadas.
- ``auth_login_rate_limit``: throttle por IP para os endpoints de autenticação.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from app.core.rate_limit import is_rate_limited
from app.core.security import SecurityError, decode_jwt_subject_from_header

_AUTH_LOGIN_LIMIT = 10
_AUTH_LOGIN_WINDOW_SECONDS = 60


async def require_user(authorization: str | None = Header(default=None)) -> str:
    """Exige token Bearer válido (access); retorna o id do usuário (subject)."""
    try:
        return decode_jwt_subject_from_header(authorization)
    except SecurityError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_or_missing_token",
        ) from error


async def auth_login_rate_limit(request: Request) -> None:
    """Limita tentativas de login/refresh por IP (resposta 429 acima do limite)."""
    client_ip = request.client.host if request.client else "unknown"
    limited = await is_rate_limited(
        key=f"auth-login:{client_ip}",
        limit=_AUTH_LOGIN_LIMIT,
        window_seconds=_AUTH_LOGIN_WINDOW_SECONDS,
    )
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too_many_attempts",
        )

