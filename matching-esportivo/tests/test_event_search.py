from __future__ import annotations

import asyncio

from datetime import UTC, datetime, timedelta

from geoalchemy2.elements import WKTElement

from app.models.event import Event
from app.schemas.event import EventSearchFilters, UserLocation
from app.services.event_service import find_nearby_events

from tests.conftest import FakeAsyncSession, FakeResult


def test_find_nearby_events_builds_spatial_query_and_serializes_results() -> None:
    async def run() -> tuple[list, str]:
        now = datetime.now(UTC)
        event = Event(
            id="event-nearby-1",
            creator_id="creator-1",
            club_id=None,
            sport_type="futebol",
            sub_type=None,
            scheduled_time=now + timedelta(hours=2),
            status="open",
            max_participants=10,
            location=WKTElement("POINT(-46.633308 -23.55052)", srid=4326),
        )
        session = FakeAsyncSession(execute_results=[FakeResult(rows=[event])])

        results = await find_nearby_events(
            UserLocation(latitude=-23.55052, longitude=-46.633308),
            radius_km=5,
            filters=EventSearchFilters(sport_type="Futebol", limit=5),
            session=session,
        )

        compiled_query = str(session.queries[0].compile(compile_kwargs={"literal_binds": True}))
        return results, compiled_query

    results, compiled_query = asyncio.run(run())

    assert len(results) == 1
    assert results[0].id == "event-nearby-1"
    assert "ST_DWithin" in compiled_query
    assert "futebol" in compiled_query
    assert "open" in compiled_query