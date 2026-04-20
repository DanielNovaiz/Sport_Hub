from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.core.redis import pub_notification
from app.schemas.event import PersonalizedFeedItem
from app.services.event_service import get_personalized_feed
from app.services.notification_service import list_notifications


class _Result:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class _Session:
    def __init__(self, user=None, notifications=None, feed_rows=None):
        self.user = user
        self.notifications = notifications or []
        self.feed_rows = feed_rows or []
        self.calls = []

    async def get(self, model, identity):
        self.calls.append(("get", model.__name__, identity))
        return self.user

    async def execute(self, query):
        sql = str(query)
        self.calls.append(("execute", sql))
        if "FROM notification" in sql:
            return _Result(self.notifications)
        if "ST_X" in sql and "ST_Y" in sql:
            return _Result([( -46.633308, -23.55052 )])
        if "FROM user_interest" in sql:
            return _Result(["futebol"])
        if "ST_DWithin" in sql:
            return _Result(self.feed_rows)
        return _Result([])


class _Redis:
    def __init__(self):
        self.published = []

    async def publish(self, channel, payload):
        self.published.append((channel, payload))


@pytest.mark.asyncio
async def test_pub_notification_publishes_payload(monkeypatch):
    fake_redis = _Redis()

    async def fake_get_redis():
        return fake_redis

    monkeypatch.setattr("app.core.redis.get_redis", fake_get_redis)

    ok = await pub_notification("user-1", "Novo evento")

    assert ok is True
    assert fake_redis.published[0][0] == "notifications:user-1"
    assert "Novo evento" in fake_redis.published[0][1]


@pytest.mark.asyncio
async def test_list_notifications_returns_serialized_rows():
    now = datetime.now(UTC)
    session = _Session(
        notifications=[
            SimpleNamespace(
                id="n1",
                user_id="u1",
                content="novo participante",
                type="event_update",
                is_read=False,
                created_at=now,
            )
        ]
    )

    items = await list_notifications("u1", session)

    assert len(items) == 1
    assert items[0].content == "novo participante"
    assert items[0].user_id == "u1"


@pytest.mark.asyncio
async def test_get_personalized_feed_prioritizes_club_events():
    now = datetime.now(UTC).replace(year=2030)
    event = SimpleNamespace(
        id="e1",
        creator_id="c1",
        club_id="club-1",
        sport_type="futebol",
        scheduled_time=now,
        status="open",
        max_participants=10,
    )
    user = SimpleNamespace(location=SimpleNamespace())
    session = _Session(user=user, feed_rows=[(event, 1.25, 1)])

    async def fake_execute(query):
        sql = str(query)
        session.calls.append(("execute", sql))
        if "ST_X" in sql:
            return _Result([( -46.633308, -23.55052 )])
        if "FROM user_interest" in sql:
            return _Result(["futebol"])
        if "ST_DWithin" in sql:
            return _Result([(event, 1.25, 1)])
        return _Result([])

    session.execute = fake_execute

    response = await get_personalized_feed("u1", session)

    assert response.meta["count"] == 1
    assert isinstance(response.data[0], PersonalizedFeedItem)
    assert response.data[0].club_priority is True
    assert response.data[0].distance_km == 1.25