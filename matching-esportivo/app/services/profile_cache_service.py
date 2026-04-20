"""Cache Redis para perfis públicos."""

from __future__ import annotations

import logging

from app.core.redis import get_redis
from app.schemas.user import UserProfileCard

logger = logging.getLogger(__name__)

PROFILE_CACHE_TTL_SECONDS = 15 * 60


def build_user_profile_cache_key(user_id: str) -> str:
    return f"user_profile:{user_id}"


async def get_cached_user_profile(user_id: str) -> UserProfileCard | None:
    """Input: user_id. Output: perfil público cacheado (se disponível)."""
    try:
        redis = await get_redis()
        if redis is None:
            return None

        raw_payload = await redis.get(build_user_profile_cache_key(user_id))
        if not raw_payload:
            return None

        return UserProfileCard.model_validate_json(raw_payload)
    except Exception as error:  # pragma: no cover - cache opcional
        logger.warning("Falha ao recuperar cache de perfil público: %s", error)
        return None


async def set_cached_user_profile(user_id: str, profile: UserProfileCard) -> None:
    """Input: user_id + perfil. Side effects: grava cache com TTL de 15 min."""
    try:
        redis = await get_redis()
        if redis is None:
            return

        await redis.set(
            build_user_profile_cache_key(user_id),
            profile.model_dump_json(),
            ex=PROFILE_CACHE_TTL_SECONDS,
        )
    except Exception as error:  # pragma: no cover - cache opcional
        logger.warning("Falha ao salvar cache de perfil público: %s", error)


async def invalidate_user_profile_cache(user_id: str) -> None:
    """Input: user_id. Side effects: remove cache do perfil público."""
    try:
        redis = await get_redis()
        if redis is None:
            return

        await redis.delete(build_user_profile_cache_key(user_id))
    except Exception as error:  # pragma: no cover - cache opcional
        logger.warning("Falha ao invalidar cache de perfil público: %s", error)
