"""Serviço de chat e comunicação em tempo real."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.chat import ChatMessage, ChatRoom
from app.schemas.chat import ChatMessageRead, ChatRoomRead


async def create_chat_room(session: AsyncSession, event_id: str) -> ChatRoomRead:
    """Input: event_id. Output: ChatRoomRead."""
    query = select(ChatRoom).where(ChatRoom.event_id == event_id)
    result = await session.execute(query)
    existing = result.scalars().first()
    if existing:
        return ChatRoomRead.model_validate(existing)

    room = ChatRoom(event_id=event_id)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return ChatRoomRead.model_validate(room)


async def list_messages(session: AsyncSession, chat_room_id: str, limit: int = 100) -> list[ChatMessageRead]:
    """Input: room_id. Output: messages ordered by creation time asc."""
    query = (
        select(ChatMessage)
        .where(ChatMessage.chat_room_id == chat_room_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await session.execute(query)
    messages = result.scalars().all()
    return [ChatMessageRead.model_validate(message) for message in messages]


async def send_message(
    session: AsyncSession,
    chat_room_id: str,
    user_id: str,
    content: str,
) -> ChatMessageRead:
    """Input: message data. Output: ChatMessageRead com persistência + Redis Pub/Sub."""
    message = ChatMessage(chat_room_id=chat_room_id, user_id=user_id, content=content)
    session.add(message)
    await session.commit()
    await session.refresh(message)

    redis = await get_redis()
    if redis:
        channel = f"chat:room:{chat_room_id}"
        payload = f"{user_id}:{content}"
        await redis.publish(channel, payload)

    return ChatMessageRead.model_validate(message)
