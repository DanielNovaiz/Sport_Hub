"""Serviço de clubes: criação, descoberta geográfica e membership."""

from __future__ import annotations

from datetime import UTC, datetime

from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from sqlalchemy import cast, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club, ClubMember, TeamSynergy
from app.schemas.club import (
    ClubCreate,
    ClubMemberRead,
    ClubRead,
)
from app.schemas.event import UserLocation

SYNERGY_STATUS_NONE = "none"
SYNERGY_STATUS_DYNAMIC_DUO = "dynamic_duo"
SYNERGY_STATUS_PERFECT = "perfect_synergy"
HIGH_SYNERGY_STATUSES = {SYNERGY_STATUS_DYNAMIC_DUO, SYNERGY_STATUS_PERFECT}


async def create_club(payload: ClubCreate, session: AsyncSession) -> ClubRead:
    """Input: ClubCreate. Output: clube criado e owner como admin."""
    location_point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
    club = Club(
        name=payload.name,
        description=payload.description,
        owner_id=payload.owner_id,
        sport_type=payload.sport_type.lower(),
        privacy_type=payload.privacy_type,
        location=location_point,
    )
    owner_membership = ClubMember(user_id=payload.owner_id, status="admin")
    club_member_linked = False
    try:
        async with session.begin():
            session.add(club)
            await session.flush()
            owner_membership.club_id = club.id
            session.add(owner_membership)
            club_member_linked = True
    except IntegrityError as error:
        await session.rollback()
        raise ValueError("club_create_failed") from error

    if not club_member_linked:
        raise ValueError("club_create_failed")
    await session.refresh(club)
    data = ClubRead.model_validate(club).model_dump()
    data["active_members"] = 1
    return ClubRead(**data)


async def search_nearby_clubs(
    user_location: UserLocation,
    session: AsyncSession,
    sport_type: str | None = None,
    limit: int = 50,
) -> list[ClubRead]:
    """Input: localização. Output: clubes em 10km via ST_DWithin."""
    active_members_subquery = (
        select(
            ClubMember.club_id.label("club_id"),
            func.count(ClubMember.id).label("active_members"),
        )
        .where(ClubMember.status.in_(["admin", "member"]))
        .group_by(ClubMember.club_id)
        .subquery()
    )

    reference_point = func.ST_SetSRID(
        func.ST_MakePoint(user_location.longitude, user_location.latitude),
        4326,
    )
    query = (
        select(Club, func.coalesce(active_members_subquery.c.active_members, 0).label("active_members"))
        .outerjoin(active_members_subquery, active_members_subquery.c.club_id == Club.id)
        .where(
            func.ST_DWithin(
                cast(Club.location, Geography),
                cast(reference_point, Geography),
                10000.0,
            )
        )
        .order_by(
            func.ST_Distance(
                cast(Club.location, Geography),
                cast(reference_point, Geography),
            )
        )
        .limit(limit)
    )
    if sport_type:
        query = query.where(Club.sport_type == sport_type.lower())
    result = await session.execute(query)
    rows = result.all()
    data: list[ClubRead] = []
    for row in rows:
        if hasattr(row, "_mapping"):
            club = row[0]
            active_members = row._mapping.get("active_members", row[1] if len(row) > 1 else 0)
        elif isinstance(row, (tuple, list)):
            club = row[0]
            active_members = row[1] if len(row) > 1 else 0
        else:
            club = row
            active_members = 0

        payload = ClubRead.model_validate(club).model_dump()
        payload["active_members"] = int(active_members)
        data.append(ClubRead(**payload))
    return data


async def request_club_join(
    club_id: str,
    user_id: str,
    session: AsyncSession,
) -> ClubMemberRead:
    """Input: user/club. Output: membership member/pending conforme privacidade."""
    club = await session.get(Club, club_id)
    if not club:
        raise ValueError("club_not_found")

    existing_query = select(ClubMember).where(
        ClubMember.club_id == club_id,
        ClubMember.user_id == user_id,
    )
    existing_result = await session.execute(existing_query)
    existing = existing_result.scalars().first()
    if existing:
        raise ValueError("membership_already_exists")

    membership_status = "member" if club.privacy_type == "public" else "pending"
    membership = ClubMember(club_id=club_id, user_id=user_id, status=membership_status)
    session.add(membership)
    await session.commit()
    await session.refresh(membership)
    return ClubMemberRead.model_validate(membership)


async def review_club_membership(
    club_id: str,
    target_user_id: str,
    reviewer_id: str,
    approve: bool,
    session: AsyncSession,
) -> ClubMemberRead | None:
    """Input: reviewer/target. Output: aprovação ou rejeição de membership pendente."""
    club = await session.get(Club, club_id)
    if not club:
        raise ValueError("club_not_found")

    reviewer_membership_query = select(ClubMember).where(
        ClubMember.club_id == club_id,
        ClubMember.user_id == reviewer_id,
        ClubMember.status.in_(["admin", "member"]),
    )
    reviewer_result = await session.execute(reviewer_membership_query)
    reviewer_membership = reviewer_result.scalars().first()
    if not reviewer_membership and reviewer_id != club.owner_id:
        raise ValueError("reviewer_not_authorized")

    target_query = select(ClubMember).where(
        ClubMember.club_id == club_id,
        ClubMember.user_id == target_user_id,
    )
    target_result = await session.execute(target_query)
    target_membership = target_result.scalars().first()
    if not target_membership:
        raise ValueError("membership_not_found")
    if target_membership.status != "pending":
        raise ValueError("membership_not_pending")

    if approve:
        target_membership.status = "member"
        await session.commit()
        await session.refresh(target_membership)
        return ClubMemberRead.model_validate(target_membership)

    await session.delete(target_membership)
    await session.commit()
    return None


def build_members_key(user_ids: list[str]) -> str:
    """Input: lista de ids. Output: key canônica pipe-delimited para grupo."""
    normalized = sorted({user_id.strip() for user_id in user_ids if user_id and user_id.strip()})
    if not normalized:
        return ""
    return f"|{'|'.join(normalized)}|"


def resolve_synergy_status(group_size: int, win_rate: float) -> str:
    """Input: tamanho do grupo + win_rate. Output: status de sinergia."""
    if win_rate <= 70.0:
        return SYNERGY_STATUS_NONE
    if group_size == 2:
        return SYNERGY_STATUS_DYNAMIC_DUO
    if group_size == 3:
        return SYNERGY_STATUS_PERFECT
    return SYNERGY_STATUS_NONE


def has_high_synergy(status: str | None) -> bool:
    return (status or "").strip().lower() in HIGH_SYNERGY_STATUSES


async def upsert_team_synergy(
    *,
    session: AsyncSession,
    club_id: str,
    user_id: str,
    teammate_ids: list[str],
    won_match: bool,
    sport_type: str | None = None,
) -> TeamSynergy | None:
    """Atualiza/insere sinergia para duo/trio com base no resultado da partida."""
    members = sorted({user_id, *[teammate_id for teammate_id in teammate_ids if teammate_id and teammate_id != user_id]})
    group_size = len(members)
    if group_size not in {2, 3}:
        return None

    members_key = build_members_key(members)
    query = select(TeamSynergy).where(
        TeamSynergy.club_id == club_id,
        TeamSynergy.members_key == members_key,
    )
    result = await session.execute(query)
    synergy = result.scalars().first()
    now = datetime.now(UTC)

    if not synergy:
        synergy = TeamSynergy(
            club_id=club_id,
            members_key=members_key,
            group_size=group_size,
            sport_type=sport_type,
            created_at=now,
            updated_at=now,
        )
        session.add(synergy)

    synergy.matches_together += 1
    if won_match:
        synergy.wins_together += 1
    synergy.win_rate = (synergy.wins_together / synergy.matches_together) * 100.0 if synergy.matches_together else 0.0
    synergy.status = resolve_synergy_status(group_size, synergy.win_rate)
    synergy.sport_type = sport_type or synergy.sport_type
    synergy.updated_at = now

    await session.flush()
    return synergy


async def list_user_synergy_badges(
    *,
    session: AsyncSession,
    user_id: str,
    club_id: str | None = None,
) -> list[str]:
    """Lista badges ativos de sinergia para exibição visual em card."""
    query = select(TeamSynergy.status).where(
        TeamSynergy.members_key.like(f"%|{user_id}|%"),
        TeamSynergy.status.in_(tuple(HIGH_SYNERGY_STATUSES)),
    )
    if club_id:
        query = query.where(TeamSynergy.club_id == club_id)

    result = await session.execute(query)
    statuses = sorted({str(status).strip().lower() for status in result.scalars().all()})
    return statuses