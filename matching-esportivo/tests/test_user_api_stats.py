from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.users import router as users_router
from app.core import get_session


def test_user_profile_and_stats_routes_smoke(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(users_router)

    async def fake_session():
        yield object()

    app.dependency_overrides[get_session] = fake_session

    async def fake_get_user_profile_card(session, user_id):
        return {
            "user": {
                "id": user_id,
                "email": "user@example.com",
                "username": "user",
                "full_name": "User Name",
                "phone": None,
                "avatar_url": None,
                "bio": None,
                "is_active": True,
                "is_verified": False,
                "created_at": "2026-04-13T00:00:00Z",
                "updated_at": "2026-04-13T00:00:00Z",
                "last_login": None,
                "interests": [],
            },
            "stats": {
                "id": "stats-1",
                "user_id": user_id,
                "position": "atacante",
                "overall": 88,
                "playstyle_archetype": "Sharpshooter",
                "pace": 90,
                "shooting": 92,
                "passing": 70,
                "defense": 55,
                "physical": 72,
                "technique": 78,
                "created_at": "2026-04-13T00:00:00Z",
                "updated_at": "2026-04-13T00:00:00Z",
            },
        }

    async def fake_update_user_stats(session, payload):
        return {
            "id": "stats-1",
            "user_id": payload.user_id,
            "position": payload.position or "meia",
            "overall": 84,
            "playstyle_archetype": "Speedster",
            "pace": payload.pace or 88,
            "shooting": payload.shooting or 78,
            "passing": payload.passing or 76,
            "defense": payload.defense or 70,
            "physical": payload.physical or 74,
            "technique": payload.technique or 75,
            "created_at": "2026-04-13T00:00:00Z",
            "updated_at": "2026-04-13T00:00:00Z",
        }

    monkeypatch.setattr("app.api.users.get_user_profile_card", fake_get_user_profile_card)
    monkeypatch.setattr("app.api.users.update_user_stats", fake_update_user_stats)

    with TestClient(app) as client:
        profile = client.get("/api/users/user-1/profile")
        assert profile.status_code == 200
        assert profile.json()["data"]["stats"]["overall"] == 88

        updated = client.patch(
            "/api/users/me/stats",
            json={"user_id": "user-1", "position": "atacante", "shooting": 90, "pace": 89},
        )
        assert updated.status_code == 200
        assert updated.json()["message"] == "user_stats_updated"
