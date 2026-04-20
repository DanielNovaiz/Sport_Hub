"""Pytest configuration for project imports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import sys
from pathlib import Path

import pytest
from geoalchemy2.elements import WKTElement

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.club import Club  # noqa: E402
from app.models.event import Event, EventParticipant  # noqa: E402


@dataclass
class FakeResult:
    rows: list[Any] | None = None
    scalar_value: Any | None = None

    def scalars(self) -> "FakeResult":
        return self

    def first(self) -> Any | None:
        return (self.rows or [None])[0]

    def all(self) -> list[Any]:
        return self.rows or []

    def scalar_one(self) -> Any:
        if self.scalar_value is not None:
            return self.scalar_value
        if self.rows:
            return self.rows[0]
        raise AssertionError("scalar_one called without scalar_value or rows")

    def scalar_one_or_none(self) -> Any | None:
        if self.scalar_value is not None:
            return self.scalar_value
        if self.rows:
            return self.rows[0]
        return None


class FakeBegin:
    async def __aenter__(self) -> "FakeBegin":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakeAsyncSession:
    def __init__(self, *, execute_results: list[FakeResult] | None = None, get_map: dict[tuple[type[Any], str], Any] | None = None):
        self.execute_results = execute_results or []
        self.get_map = get_map or {}
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.commits = 0
        self.refreshes: list[Any] = []
        self.flushes = 0
        self.queries: list[Any] = []

    async def execute(self, statement: Any) -> FakeResult:
        self.queries.append(statement)
        if not self.execute_results:
            raise AssertionError("No fake execute result configured")
        return self.execute_results.pop(0)

    async def get(self, model: type[Any], ident: str) -> Any | None:
        return self.get_map.get((model, ident))

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushes += 1

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, obj: Any) -> None:
        self.refreshes.append(obj)

    async def delete(self, obj: Any) -> None:
        self.deleted.append(obj)

    async def rollback(self) -> None:
        return None

    def begin(self) -> FakeBegin:
        return FakeBegin()


@pytest.fixture
def point() -> WKTElement:
    return WKTElement("POINT(-46.633308 -23.55052)", srid=4326)


@pytest.fixture
def club(point: WKTElement) -> Club:
    return Club(
        id="club-1",
        name="Bola Livre",
        description="Clube de futebol",
        owner_id="user-owner",
        sport_type="futebol",
        privacy_type="public",
        location=point,
    )


@pytest.fixture
def private_club(point: WKTElement) -> Club:
    return Club(
        id="club-private",
        name="Arena Fechada",
        description="Clube privado",
        owner_id="user-owner",
        sport_type="futebol",
        privacy_type="private",
        location=point,
    )


@pytest.fixture
def event(point: WKTElement) -> Event:
    scheduled_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=2)
    return Event(
        id="event-1",
        creator_id="user-owner",
        club_id="club-private",
        sport_type="futebol",
        scheduled_time=scheduled_time,
        status="open",
        max_participants=10,
        location=point,
    )


@pytest.fixture
def participant() -> EventParticipant:
    return EventParticipant(
        id="participant-1",
        user_id="user-1",
        event_id="event-1",
        status="confirmed",
    )
