from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.clubs import router as clubs_router
from app.core.database import get_session
from app.schemas.club import ClubJoinResponse, ClubRead


def test_club_api_routes_smoke(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(clubs_router)

    async def fake_session():
        yield object()

    app.dependency_overrides[get_session] = fake_session

    club = ClubRead(
        id="club-1",
        name="Clube Goleadores",
        description="Clube de bairro",
        owner_id="owner-1",
        sport_type="futebol",
        privacy_type="public",
        created_at="2026-04-13T00:00:00Z",
    )

    membership = ClubJoinResponse.model_validate(
        {
            "message": "club_join_requested",
            "data": {
                "id": "member-1",
                "user_id": "user-2",
                "club_id": "club-1",
                "status": "member",
                "created_at": "2026-04-13T00:00:00Z",
            },
        }
    )

    async def fake_create_club(payload, session):
        return club

    async def fake_search_nearby_clubs(location, session, sport_type=None, limit=50):
        return [club]

    async def fake_request_club_join(club_id, user_id, session):
        return membership.data

    async def fake_list_user_synergy_badges(*, session, user_id, club_id=None):
        return ["dynamic_duo"]

    monkeypatch.setattr("app.api.clubs.create_club", fake_create_club)
    monkeypatch.setattr("app.api.clubs.search_nearby_clubs", fake_search_nearby_clubs)
    monkeypatch.setattr("app.api.clubs.request_club_join", fake_request_club_join)
    monkeypatch.setattr("app.api.clubs.list_user_synergy_badges", fake_list_user_synergy_badges)

    with TestClient(app) as client:
        response = client.post(
            "/api/clubs/",
            json={
                "name": "Clube Goleadores",
                "description": "Clube de bairro",
                "owner_id": "owner-1",
                "sport_type": "futebol",
                "privacy_type": "public",
                "latitude": -23.55,
                "longitude": -46.63,
            },
        )
        assert response.status_code == 201
        assert response.json()["message"] == "club_created"

        nearby = client.get("/api/clubs/nearby?latitude=-23.55&longitude=-46.63")
        assert nearby.status_code == 200
        assert nearby.json()["meta"]["radius_km"] == 10

        join = client.post(
            "/api/clubs/club-1/join",
            json={"user_id": "user-2"},
        )
        assert join.status_code == 200
        assert join.json()["message"] == "club_join_requested"

        synergy = client.get("/api/clubs/club-1/members/user-2/synergy")
        assert synergy.status_code == 200
        assert synergy.json()["data"]["visual_bonus"] is True
