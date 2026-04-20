from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.services.profile_cache_service import (
    PROFILE_CACHE_TTL_SECONDS,
    build_user_profile_cache_key,
    get_cached_user_profile,
    invalidate_user_profile_cache,
    set_cached_user_profile,
)
from app.schemas.user import UserProfileCard


class _Redis:
    def __init__(self):
        self.data: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.data[key] = value
        self.set_calls.append((key, value, ex))

    async def delete(self, key: str):
        self.data.pop(key, None)


def _build_profile_card(user_id: str) -> UserProfileCard:
    now = datetime.now(UTC)
    return UserProfileCard.model_validate(
        {
            "user": {
                "id": user_id,
                "email": "user@example.com",
                "username": "user_name",
                "full_name": "User Name",
                "phone": None,
                "avatar_url": None,
                "bio": None,
                "is_active": True,
                "is_verified": False,
                "created_at": now,
                "updated_at": now,
                "last_login": None,
                "interests": [],
            },
            "stats": {
                "id": "stats-1",
                "user_id": user_id,
                "position": "meia",
                "overall": 81,
                "playstyle_archetype": "Balanced",
                "pace": 80,
                "shooting": 82,
                "passing": 85,
                "defense": 70,
                "physical": 74,
                "technique": 79,
                "created_at": now,
                "updated_at": now,
            },
            "sport_type": "FOOTBALL",
            "overall_by_position": 81,
            "xp_progress": 0.4,
            "xp_residual_total": 240,
            "xp_entries": [],
            "achievements": [],
        }
    )


@pytest.mark.asyncio
async def test_build_user_profile_cache_key_uses_required_format() -> None:
    assert build_user_profile_cache_key("abc") == "user_profile:abc"


@pytest.mark.asyncio
async def test_set_and_get_cached_user_profile(monkeypatch) -> None:
    redis = _Redis()

    async def fake_get_redis():
        return redis

    monkeypatch.setattr("app.services.profile_cache_service.get_redis", fake_get_redis)

    profile = _build_profile_card("user-1")
    await set_cached_user_profile("user-1", profile)

    cached = await get_cached_user_profile("user-1")

    assert cached is not None
    assert cached.user.id == "user-1"
    assert cached.stats.overall == 81
    assert redis.set_calls[0][0] == "user_profile:user-1"
    assert redis.set_calls[0][2] == PROFILE_CACHE_TTL_SECONDS


@pytest.mark.asyncio
async def test_invalidate_user_profile_cache_deletes_key(monkeypatch) -> None:
    redis = _Redis()
    redis.data["user_profile:user-1"] = "{}"

    async def fake_get_redis():
        return redis

    monkeypatch.setattr("app.services.profile_cache_service.get_redis", fake_get_redis)

    await invalidate_user_profile_cache("user-1")

    assert "user_profile:user-1" not in redis.data
