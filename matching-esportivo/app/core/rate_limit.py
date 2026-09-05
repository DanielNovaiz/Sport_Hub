"""Rate limiting simples via Redis (INCR/EXPIRE)."""
from __future__ import annotations

import logging

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


async def is_rate_limited(key: str, limit: int, window_seconds: int) -> bool:
    """True se o bucket ``key`` exceder ``limit`` chamadas na janela.

    Fail-open: se o Redis estiver indisponível, permite a requisição (o serviço
    segue em modo degradado sem derrubar login por dependência externa).
    """
    redis = await get_redis()
    if redis is None:
        return False
    try:
        bucket = f"ratelimit:{key}"
        count = await redis.incr(bucket)
        if count == 1:
            await redis.expire(bucket, window_seconds)
        return int(count) > int(limit)
    except Exception as error:  # pragma: no cover - depende de infra externa.
        logger.warning("rate_limit_check_failed", extra={"error": str(error)})
        return False
