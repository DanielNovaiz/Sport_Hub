"""Endpoints de ranking regional por overall."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.ranked import RankedUsersResponse
from app.services.ranked_service import DEFAULT_REGIONAL_CITY, list_regional_ranked_users

router = APIRouter(prefix="/api/ranking", tags=["Ranking"])


@router.get("/regional", response_model=RankedUsersResponse, status_code=status.HTTP_200_OK)
async def list_regional_ranking(
    city: str = Query(default=DEFAULT_REGIONAL_CITY, description="Cidade base do ranking regional."),
    sport: str | None = Query(default=None, description="Filtro por esporte."),
    position: str | None = Query(default=None, description="Filtro por posição."),
    session: AsyncSession = Depends(get_session),
) -> RankedUsersResponse:
    """Top 50 jogadores regionais baseados em overall."""
    rows = await list_regional_ranked_users(
        session,
        city=city,
        sport=sport,
        position=position,
        limit=50,
    )

    return RankedUsersResponse(
        message="regional_ranking_retrieved",
        data=rows,
        meta={
            "count": len(rows),
            "city": city,
            "sport": sport,
            "position": position,
            "order_by": "overall_score",
            "limit": 50,
        },
    )
