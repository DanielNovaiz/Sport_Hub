"""Endpoints para usuários."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_session
from app.schemas.user import (
    PlayerStatsResponse,
    PlayerStatsUpdate,
    UserCreate,
    UserDeleteData,
    UserDeleteResponse,
    UserListResponse,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import (
    get_user_profile_card,
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user_stats,
    update_user,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Input: UserCreate. Output: envelope com UserRead."""
    try:
        user = await create_user(session, payload)
    except ValueError as error:
        if str(error) == "email_or_username_already_exists":
            raise HTTPException(status_code=409, detail="email_or_username_already_exists")
        raise
    return UserResponse(message="user_created", data=user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Input: user_id. Output: envelope com UserRead."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserResponse(message="user_found", data=user)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile_endpoint(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> UserProfileResponse:
    """Input: user_id. Output: card com perfil, overall, atributos e arquétipo."""
    profile = await get_user_profile_card(session, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserProfileResponse(message="user_profile_found", data=profile)


@router.get("/", response_model=UserListResponse)
async def list_users_endpoint(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> UserListResponse:
    """Input: paginação. Output: envelope com lista de usuários."""
    users = await list_users(session, skip=skip, limit=limit)
    meta = {"skip": skip, "limit": limit, "count": len(users)}
    return UserListResponse(message="users_listed", data=users, meta=meta)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Input: user_id e payload parcial. Output: envelope com UserRead atualizado."""
    try:
        user = await update_user(session, user_id, payload)
    except ValueError as error:
        if str(error) == "email_or_username_already_exists":
            raise HTTPException(status_code=409, detail="email_or_username_already_exists")
        raise
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserResponse(message="user_updated", data=user)


@router.patch("/me/stats", response_model=PlayerStatsResponse)
async def update_user_stats_endpoint(
    payload: PlayerStatsUpdate,
    session: AsyncSession = Depends(get_session),
) -> PlayerStatsResponse:
    """Input: atributos do jogador. Output: stats atualizados com overall e arquétipo."""
    try:
        stats = await update_user_stats(session, payload)
    except ValueError as error:
        if str(error) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        raise
    return PlayerStatsResponse(message="user_stats_updated", data=stats)


@router.delete("/{user_id}", response_model=UserDeleteResponse)
async def delete_user_endpoint(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> UserDeleteResponse:
    """Input: user_id. Output: envelope de remoção."""
    deleted = await delete_user(session, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="user_not_found")
    return UserDeleteResponse(message="user_deleted", data=UserDeleteData(id=user_id))
