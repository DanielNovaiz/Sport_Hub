"""Tests para chat service (validação de schemas)."""

import pytest
from datetime import datetime, UTC

from app.schemas.chat import ChatMessageCreate, ChatRoomRead


def test_chat_message_create_validation_max_length():
    """ChatMessageCreate deve validar tamanho máximo."""
    valid = ChatMessageCreate(
        chat_room_id="room-1",
        user_id="user-1",
        content="x" * 500,
    )
    assert len(valid.content) == 500


def test_chat_message_create_validation_required():
    """ChatMessageCreate deve exigir campos obrigatórios."""
    with pytest.raises(ValueError):
        ChatMessageCreate(chat_room_id="room-1", user_id="user-1", content="")


def test_chat_room_read_from_attributes():
    """ChatRoomRead deve suportar ORM deserialization."""
    data = {
        "id": "room-123",
        "event_id": "event-456",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    room = ChatRoomRead(**data)
    assert room.event_id == "event-456"
