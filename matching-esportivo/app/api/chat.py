"""Endpoints de chat e comunicação."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.chat import ChatRoom
from app.schemas.chat import ChatMessageCreate, ChatMessageListResponse, ChatMessageResponse, ChatRoomRead, ChatRoomResponse
from app.services.chat_service import create_chat_room, list_messages, send_message

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/rooms/{event_id}", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    event_id: str,
    session: AsyncSession = Depends(get_session),
) -> ChatRoomResponse:
    """Criar sala de chat para um evento."""
    room = await create_chat_room(session, event_id)
    return ChatRoomResponse(
        message="Chat room created successfully",
        data=room,
    )


@router.get("/rooms/{room_id}/messages", response_model=ChatMessageListResponse, status_code=status.HTTP_200_OK)
async def list_room_messages(
    room_id: str,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> ChatMessageListResponse:
    """Get room messages for simple polling."""
    messages = await list_messages(session, room_id, limit=limit)
    return ChatMessageListResponse(
        message="Messages retrieved successfully",
        data=messages,
        meta={"room_id": room_id, "count": len(messages)},
    )


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse, status_code=status.HTTP_200_OK)
async def get_room(
    room_id: str,
    session: AsyncSession = Depends(get_session),
) -> ChatRoomResponse:
    """Obter detalhes da sala de chat."""
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )
    return ChatRoomResponse(
        message="Chat room retrieved successfully",
        data=ChatRoomRead.model_validate(room),
    )


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_msg(
    room_id: str,
    payload: ChatMessageCreate,
    session: AsyncSession = Depends(get_session),
) -> ChatMessageResponse:
    """Enviar mensagem na sala de chat (persistida + Redis Pub/Sub)."""
    room = await session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )

    msg = await send_message(session, room_id, payload.user_id, payload.content)
    return ChatMessageResponse(
        message="Message sent successfully",
        data=msg,
    )
