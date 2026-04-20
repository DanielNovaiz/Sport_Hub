from __future__ import annotations

import pytest
from geoalchemy2.elements import WKTElement

from app.models.club import Club, ClubMember, TeamSynergy
from app.schemas.club import ClubCreate
from app.schemas.event import UserLocation
from app.services.club_service import (
    SYNERGY_STATUS_DYNAMIC_DUO,
    SYNERGY_STATUS_NONE,
    build_members_key,
    create_club,
    list_user_synergy_badges,
    request_club_join,
    resolve_synergy_status,
    review_club_membership,
    search_nearby_clubs,
    upsert_team_synergy,
)

from tests.conftest import FakeAsyncSession, FakeResult


@pytest.mark.asyncio
async def test_create_club_sets_owner_as_admin(point: WKTElement) -> None:
    session = FakeAsyncSession()
    payload = ClubCreate(
        name="Clube Goleadores",
        description="Clube de bairro",
        owner_id="owner-1",
        sport_type="futebol",
        privacy_type="private",
        latitude=-23.55052,
        longitude=-46.633308,
    )

    result = await create_club(payload, session)

    assert result.name == "Clube Goleadores"
    assert result.privacy_type == "private"
    assert len(session.added) == 2
    assert isinstance(session.added[0], Club)
    assert isinstance(session.added[1], ClubMember)
    assert session.added[1].status == "admin"
    assert session.added[1].club_id == session.added[0].id


@pytest.mark.asyncio
async def test_request_club_join_public_becomes_member(club: Club) -> None:
    session = FakeAsyncSession(
        execute_results=[FakeResult(rows=[])],
        get_map={(Club, club.id): club},
    )

    membership = await request_club_join(club.id, "user-2", session)

    assert membership.status == "member"
    assert session.commits == 1
    assert session.added[0].status == "member"


@pytest.mark.asyncio
async def test_request_club_join_private_becomes_pending(private_club: Club) -> None:
    session = FakeAsyncSession(
        execute_results=[FakeResult(rows=[])],
        get_map={(Club, private_club.id): private_club},
    )

    membership = await request_club_join(private_club.id, "user-2", session)

    assert membership.status == "pending"
    assert session.added[0].status == "pending"


@pytest.mark.asyncio
async def test_review_club_membership_approve(private_club: Club) -> None:
    pending = ClubMember(id="member-1", user_id="user-2", club_id=private_club.id, status="pending")
    reviewer = ClubMember(id="member-2", user_id="owner-1", club_id=private_club.id, status="admin")
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[reviewer]),
            FakeResult(rows=[pending]),
        ],
        get_map={(Club, private_club.id): private_club},
    )

    reviewed = await review_club_membership(private_club.id, "user-2", "owner-1", True, session)

    assert reviewed is not None
    assert reviewed.status == "member"
    assert pending.status == "member"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_review_club_membership_reject(private_club: Club) -> None:
    pending = ClubMember(id="member-1", user_id="user-2", club_id=private_club.id, status="pending")
    reviewer = ClubMember(id="member-2", user_id="owner-1", club_id=private_club.id, status="admin")
    session = FakeAsyncSession(
        execute_results=[
            FakeResult(rows=[reviewer]),
            FakeResult(rows=[pending]),
        ],
        get_map={(Club, private_club.id): private_club},
    )

    reviewed = await review_club_membership(private_club.id, "user-2", "owner-1", False, session)

    assert reviewed is None
    assert session.deleted == [pending]
    assert session.commits == 1


@pytest.mark.asyncio
async def test_search_nearby_clubs_uses_geospatial_query(club: Club) -> None:
    session = FakeAsyncSession(execute_results=[FakeResult(rows=[club])])
    location = UserLocation(latitude=-23.55052, longitude=-46.633308)

    clubs = await search_nearby_clubs(location, session, sport_type="futebol", limit=10)

    assert clubs[0].id == club.id
    statement_text = str(session.queries[0])
    assert "ST_DWithin" in statement_text
    assert "ST_Distance" in statement_text


def test_build_members_key_is_canonical_and_deduplicated() -> None:
    key = build_members_key([" user-2 ", "user-1", "user-2"])
    assert key == "|user-1|user-2|"


def test_resolve_synergy_status_thresholds() -> None:
    assert resolve_synergy_status(2, 71.0) == SYNERGY_STATUS_DYNAMIC_DUO
    assert resolve_synergy_status(3, 71.0) == "perfect_synergy"
    assert resolve_synergy_status(2, 70.0) == SYNERGY_STATUS_NONE


@pytest.mark.asyncio
async def test_upsert_team_synergy_creates_and_updates_win_rate() -> None:
    session = FakeAsyncSession(execute_results=[FakeResult(rows=[])])

    synergy = await upsert_team_synergy(
        session=session,
        club_id="club-1",
        user_id="user-1",
        teammate_ids=["user-2"],
        won_match=True,
        sport_type="football",
    )

    assert synergy is not None
    assert isinstance(synergy, TeamSynergy)
    assert synergy.members_key == "|user-1|user-2|"
    assert synergy.matches_together == 1
    assert synergy.wins_together == 1
    assert synergy.win_rate == 100.0
    assert synergy.status == SYNERGY_STATUS_DYNAMIC_DUO


@pytest.mark.asyncio
async def test_list_user_synergy_badges_returns_distinct_high_statuses() -> None:
    session = FakeAsyncSession(execute_results=[FakeResult(rows=["dynamic_duo", "perfect_synergy", "dynamic_duo"])])

    badges = await list_user_synergy_badges(session=session, user_id="user-1", club_id="club-1")

    assert badges == ["dynamic_duo", "perfect_synergy"]
