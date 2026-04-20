"""Middleware de rate limit para submissão de MatchPerformance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from sqlmodel import select

from app.models.court import Court
from app.models.player_stats import MatchPerformance
from app.core.security import SecurityError, decode_jwt_subject_from_header

RATE_LIMIT_WINDOW_MINUTES = 20
BOX_SCORE_PATH = "/api/ranked/box-score"


def is_rate_limited(
    *,
    last_submission_at: datetime | None,
    now: datetime,
    window_minutes: int = RATE_LIMIT_WINDOW_MINUTES,
) -> bool:
    """Retorna True se a última submissão estiver dentro da janela de rate limit."""
    if last_submission_at is None:
        return False

    window_delta = timedelta(minutes=window_minutes)
    return (now - last_submission_at) < window_delta


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def _is_admin_arena_owner(user_id: str) -> bool:
    from app.core.database import async_session

    async with async_session() as session:
        query = select(Court.id).where(Court.owner_id == user_id).limit(1)
        result = await session.execute(query)
        return result.first() is not None


async def _get_last_submission(user_id: str) -> datetime | None:
    from app.core.database import async_session

    async with async_session() as session:
        query = (
            select(MatchPerformance.created_at)
            .where(MatchPerformance.user_id == user_id)
            .order_by(MatchPerformance.created_at.desc())
            .limit(1)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()


def _rebind_body(request: Request, body: bytes) -> None:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive  # type: ignore[attr-defined]


class MatchPerformanceRateLimitMiddleware(BaseHTTPMiddleware):
    """Bloqueia submissões de box score dentro da janela de 20 minutos."""

    async def dispatch(self, request: Request, call_next):
        if request.method.upper() != "POST" or request.url.path != BOX_SCORE_PATH:
            return await call_next(request)

        raw_body = await request.body()
        _rebind_body(request, raw_body)

        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}") if raw_body else {}
        except json.JSONDecodeError:
            return await call_next(request)

        user_id = payload.get("user_id")
        if not isinstance(user_id, str) or not user_id.strip():
            return await call_next(request)

        user_id = user_id.strip()

        try:
            jwt_subject = decode_jwt_subject_from_header(request.headers.get("Authorization"))
        except SecurityError as error:
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": str(error)},
            )

        if jwt_subject != user_id:
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "jwt_subject_user_mismatch"},
            )

        if await _is_admin_arena_owner(user_id):
            return await call_next(request)

        last_submission = await _get_last_submission(user_id)
        if last_submission is None:
            return await call_next(request)

        now = datetime.now(UTC)
        last_submission_safe = _normalize_datetime(last_submission)
        if is_rate_limited(last_submission_at=last_submission_safe, now=now):
            retry_at = last_submission_safe + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
            retry_in_minutes = max(1, int((retry_at - now).total_seconds() // 60))
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": "rate_limit_match_performance",
                    "detail": (
                        "Aguarde antes de enviar novo MatchPerformance. "
                        f"Tente novamente em aproximadamente {retry_in_minutes} minuto(s)."
                    ),
                    "meta": {
                        "user_id": user_id,
                        "window_minutes": RATE_LIMIT_WINDOW_MINUTES,
                        "retry_at": retry_at.isoformat(),
                    },
                },
            )

        return await call_next(request)
