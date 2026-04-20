from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from geoalchemy2.elements import WKTElement

from app.models.club import Club, ClubMember
from app.models.event import Event
from app.services.event_service import join_event

from tests.conftest import FakeAsyncSession, FakeResult


@pytest.mark.asyncio
async def test_join_event_private_club_blocks_non_member() -> None:
    scheduled_time = datetime.now(UTC) + timedelta(hours=2)
    private_club = Club(
        id="club-private",
        name="Arena Fechada",
        description="Clube privado",
        owner_id="owner-1",
        sport_type="futebol",
        privacy_type="private",
        location=WKTElement("POINT(-46.633308 -23.55052)", srid=4326),
    )
    event = Event(
        id="event-1",
        creator_id="owner-1",
        club_id=private_club.id,
        sport_type="futebol",
        scheduled_time=scheduled_time,
        status="open",
        max_participants=10,
        location=WKTElement("POINT(-46.633308 -23.55052)", srid=4326),
    )
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[event]),
            FakeResult(rows=[]),
        ],
        get_map={(Club, private_club.id): private_club},
    )

    with pytest.raises(ValueError, match="private_club_membership_required"):
        await join_event("user-2", event.id, session)


@pytest.mark.asyncio
async def test_join_event_private_club_allows_member() -> None:
    scheduled_time = datetime.now(UTC) + timedelta(hours=2)
    private_club = Club(
        id="club-private",
        name="Arena Fechada",
        description="Clube privado",
        owner_id="owner-1",
        sport_type="futebol",
        privacy_type="private",
        location=WKTElement("POINT(-46.633308 -23.55052)", srid=4326),
    )
    event = Event(
        id="event-1",
        creator_id="owner-1",
        club_id=private_club.id,
        sport_type="futebol",
        scheduled_time=scheduled_time,
        status="open",
        max_participants=10,
        location=WKTElement("POINT(-46.633308 -23.55052)", srid=4326),
    )
    membership = ClubMember(
        id="membership-1",
        user_id="user-2",
        club_id=private_club.id,
        status="member",
    )
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[event]),
            FakeResult(rows=[membership]),
            FakeResult(rows=[]),
            FakeResult(scalar_value=0),
        ],
        get_map={(Club, private_club.id): private_club},
    )

    participant = await join_event("user-2", event.id, session)

    assert participant.user_id == "user-2"
    assert participant.status == "confirmed"
    assert session.commits == 0 or session.commits == 1
