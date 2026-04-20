"""Endpoints de ranking e competição."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.ranked import BoxScoreCreate, BoxScoreResponse, RankedUsersResponse, UserRankRead, UserRankResponse
from app.services.ranked_service import (
    get_user_rank_read,
    list_ranked_users,
    submit_box_score,
    update_rank_after_match,
)

router = APIRouter(prefix="/api/ranked", tags=["Ranked"])


@router.get("/", response_model=RankedUsersResponse, status_code=status.HTTP_200_OK)
async def list_rankings(
    sport_type: str | None = Query(default=None, description="Filtro por esporte, ex: basquete"),
    limit: int = Query(default=100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> RankedUsersResponse:
    """Listar ranking competitivo ordenado por MMR."""
    rankings = await list_ranked_users(session, sport_type=sport_type, limit=limit)
    return RankedUsersResponse(
        message="Rankings retrieved successfully",
        data=rankings,
        meta={"count": len(rankings), "sport_type": sport_type or "geral"},
    )


@router.get("/{user_id}", response_model=UserRankResponse, status_code=status.HTTP_200_OK)
async def get_user_rank(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> UserRankResponse:
    """Obter perfil de ranking do usuário."""
    rank = await get_user_rank_read(session, user_id)
    return UserRankResponse(
        message="Ranking retrieved successfully",
        data=rank,
    )


@router.post("/match/{winner_id}/{loser_id}", response_model=UserRankResponse, status_code=status.HTTP_200_OK)
async def register_match(
    winner_id: str,
    loser_id: str,
    session: AsyncSession = Depends(get_session),
) -> UserRankResponse:
    """Registrar resultado de partida e atualizar MMR."""
    if winner_id == loser_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Winner and loser must be different users",
        )

    winner_rank, loser_rank = await update_rank_after_match(session, winner_id, loser_id)
    return UserRankResponse(
        message=f"Match registered. {winner_id} gained {winner_rank.mmr - 100} MMR",
        data=winner_rank,
    )


@router.post("/box-score", response_model=BoxScoreResponse, status_code=status.HTTP_200_OK)
async def register_box_score(
    payload: BoxScoreCreate,
    session: AsyncSession = Depends(get_session),
) -> BoxScoreResponse:
    """Registrar box score da partida e aplicar progressão de XP/conquistas."""
    try:
        result = await submit_box_score(session, payload)
    except ValueError as error:
        message = str(error)
        if message == "event_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return BoxScoreResponse(
        message="box_score_registered",
        data=result,
        meta={
            "user_id": result.user_id,
            "sport_type": result.sport_type,
            "achievements_count": len(result.triggered_achievements),
            "processing_ms": result.processing_ms,
            "slow_processing": result.slow_processing,
            "synergy_status": result.synergy_status,
            "synergy_visual_bonus": result.synergy_visual_bonus,
            "xp_multiplier": result.xp_multiplier,
            "season_code": result.season_code,
            "season_level": result.season_level,
            "season_xp_total": result.season_xp_total,
            "season_frame": result.season_frame,
        },
    )
