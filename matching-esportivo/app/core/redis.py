"""Cliente Redis assíncrono e utilitários de pub/sub."""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis, from_url

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def get_redis() -> Redis | None:
    """Input: none. Output: cliente Redis singleton assíncrono."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = from_url(settings.redis_url, decode_responses=True)
            await _redis_client.ping()
        except Exception as error:  # pragma: no cover - depende de infra externa.
            logger.warning("Redis indisponível na inicialização: %s", error)
            _redis_client = None
    elif _redis_client is not None:
        try:
            await _redis_client.ping()
        except Exception as error:  # pragma: no cover - depende de infra externa.
            logger.warning("Conexão Redis perdida: %s", error)
            try:
                await _redis_client.aclose()
            except Exception:
                pass
            _redis_client = None
    return _redis_client


async def close_redis() -> None:
    """Input: none. Output: fecha cliente Redis se existir."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def pub_notification(user_id: str, message: str, extra: dict[str, Any] | None = None) -> bool:
    """Input: user_id e mensagem. Output: publica payload em canal do usuário."""
    try:
        redis_client = await get_redis()
        if redis_client is None:
            return False
        payload = {
            "user_id": user_id,
            "message": message,
            "extra": extra or {},
        }
        await redis_client.publish(f"notifications:{user_id}", json.dumps(payload, ensure_ascii=False))
        return True
    except Exception as error:  # pragma: no cover - infraestrutura opcional em testes locais.
        logger.warning("Falha ao publicar notificação no Redis: %s", error)
        return False