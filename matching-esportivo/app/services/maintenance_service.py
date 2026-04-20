"""Serviço de manutenção de integridade para XP, prestígio e rollback seguro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from pathlib import Path

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.positions import normalize_position_input
from app.models.player_stats import MatchPerformance, PlayerStats, UserPrestige, UserXP
from app.models.user import User

XP_PER_ATTRIBUTE_POINT = 60
BASE_ATTRIBUTE_VALUE = 50
MAX_ATTRIBUTE_VALUE = 99
MAX_COMMON_LEVEL = MAX_ATTRIBUTE_VALUE - BASE_ATTRIBUTE_VALUE
MAX_COMMON_XP_TOTAL = MAX_COMMON_LEVEL * XP_PER_ATTRIBUTE_POINT
INACTIVITY_DECAY_REASON = "Decaimento por Inatividade"

DEFAULT_BATCH_SIZE = 100

MAINTENANCE_ATTRIBUTES: tuple[str, ...] = (
    "balance",
    "vision",
    "ball_control",
    "dribble",
    "shoot_long",
    "shoot_mid",
    "shoot_short",
    "finishing",
    "velocity",
    "jump",
    "agility",
    "energy",
    "strength",
    "steal",
    "block",
    "perim_def",
    "post_def",
    "rebound",
    "reb_predict",
    "combativeness",
    "short_finish",
    "long_shot",
    "free_kick",
    "short_pass",
    "long_pass",
    "crossing",
    "dribbling",
    "ball_shielding",
    "sprint",
    "acceleration",
    "stamina",
    "tackle",
    "interception",
    "marking",
    "reflexes",
    "elasticity",
    "box_presence",
    "distribution",
    "spike_power",
    "spike_accuracy",
    "serve_power",
    "serve_tactical",
    "reception",
    "floor_defense",
    "coverage",
    "setting",
    "creativity",
    "game_vision",
    "lateral_agility",
    "reaction",
    "coordination",
)


@dataclass(frozen=True)
class XpIntegerConversion:
    """Resultado da conversão inteira de XP para pontos de atributo."""

    points_gained: int
    residual_xp: int


@dataclass(frozen=True)
class XpApplyResult:
    """Resultado da aplicação de XP com proteção de cap/prestígio."""

    applied_points: int
    residual_xp: int
    prestige_xp: int
    reached_cap: bool


@dataclass(frozen=True)
class XpConsistencyReport:
    """Resumo da varredura de consistência de UserXP."""

    scanned_rows: int
    capped_rows: int
    prestige_rows_created: int
    prestige_xp_moved: int


@dataclass(frozen=True)
class CleanupReport:
    """Resumo da limpeza de registros órfãos/inválidos."""

    scanned_rows: int
    deleted_rows: int


@dataclass(frozen=True)
class BackfillReport:
    """Resumo da migração de atributos faltantes para default 50."""

    scanned_profiles: int
    updated_profiles: int


def _get_maintenance_logger() -> logging.Logger:
    """Logger dedicado de manutenção com arquivo logs/maintenance.log."""
    logger = logging.getLogger("maintenance_audit")
    if logger.handlers:
        return logger

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(logs_dir / "maintenance.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def _profile_needs_backfill(stats: PlayerStats) -> bool:
    for attribute_name in MAINTENANCE_ATTRIBUTES:
        value = getattr(stats, attribute_name, None)
        if value is None:
            return True
    return False


def convert_xp_to_attribute_points(xp_amount: int) -> XpIntegerConversion:
    """Converte XP para pontos usando guarda de matemática inteira (// e %).

    Regra central: 60 XP = +1 ponto e resto fica como residual.
    """
    safe_xp = max(0, int(xp_amount))
    return XpIntegerConversion(
        points_gained=safe_xp // XP_PER_ATTRIBUTE_POINT,
        residual_xp=safe_xp % XP_PER_ATTRIBUTE_POINT,
    )


def apply_penalty_with_rollback_guard(
    current_value: int,
    penalty: int,
    *,
    reason: str,
) -> int:
    """Impede queda abaixo do base (50), exceto em decaimento por inatividade."""
    safe_current = int(current_value)
    safe_penalty = max(0, int(penalty))
    updated = safe_current - safe_penalty

    if reason != INACTIVITY_DECAY_REASON:
        return max(BASE_ATTRIBUTE_VALUE, updated)
    return max(0, updated)


async def _get_or_create_user_prestige(
    session: AsyncSession,
    user_id: str,
    attribute_name: str,
) -> tuple[UserPrestige, bool]:
    query = select(UserPrestige).where(
        UserPrestige.user_id == user_id,
        UserPrestige.attribute_name == attribute_name,
    )
    result = await session.execute(query)
    row = result.scalars().first()
    created = False

    if not row:
        row = UserPrestige(user_id=user_id, attribute_name=attribute_name, prestige_level=1)
        session.add(row)
        created = True
    elif row.prestige_level < 1:
        row.prestige_level = 1

    return row, created


async def credit_prestige_xp(
    session: AsyncSession,
    *,
    user_id: str,
    attribute_name: str,
    xp_amount: int,
) -> tuple[UserPrestige, bool]:
    """Credita Pontos de Estilo na trilha de prestígio usando guarda inteira."""
    amount = max(0, int(xp_amount))
    prestige_row, created = await _get_or_create_user_prestige(session, user_id, attribute_name)

    total_buffer = prestige_row.residual_xp + amount
    converted = convert_xp_to_attribute_points(total_buffer)

    prestige_row.prestige_level += converted.points_gained
    prestige_row.style_points += amount
    prestige_row.residual_xp = converted.residual_xp
    prestige_row.total_prestige_xp += amount
    prestige_row.updated_at = datetime.now(UTC)

    return prestige_row, created


async def sync_user_prestige_entries(
    session: AsyncSession,
    *,
    user_id: str,
    stats: PlayerStats,
    xp_rows: list[UserXP] | None = None,
) -> tuple[int, int]:
    """Garante UserPrestige para atributos no cap e credita excedente como Pontos de Estilo."""
    from app.services.xp_constants import ALL_PROGRESS_ATTRIBUTES

    xp_by_attribute = {row.attribute_name: row for row in (xp_rows or [])}
    prestige_rows_created = 0
    prestige_style_points_moved = 0

    for attribute_name in ALL_PROGRESS_ATTRIBUTES:
        current_value = int(getattr(stats, attribute_name, BASE_ATTRIBUTE_VALUE) or BASE_ATTRIBUTE_VALUE)
        if current_value < MAX_ATTRIBUTE_VALUE:
            continue

        xp_row = xp_by_attribute.get(attribute_name)
        overflow_xp = 0
        if xp_row is not None:
            overflow_common_xp = max(0, xp_row.total_xp - MAX_COMMON_XP_TOTAL)
            overflow_xp = max(0, xp_row.residual_xp) + overflow_common_xp

        _, created = await credit_prestige_xp(
            session,
            user_id=user_id,
            attribute_name=attribute_name,
            xp_amount=overflow_xp,
        )

        if created:
            prestige_rows_created += 1
        if overflow_xp > 0:
            prestige_style_points_moved += overflow_xp

    return prestige_rows_created, prestige_style_points_moved


def apply_common_xp_with_cap(
    *,
    current_attribute_value: int,
    current_residual_xp: int,
    incoming_xp: int,
) -> XpApplyResult:
    """Aplica XP comum com cap em 99 e overflow para prestígio.

    Mantém matemática inteira: // para pontos e % para residual.
    """
    current_attr = int(current_attribute_value)
    residual = max(0, int(current_residual_xp))
    incoming = max(0, int(incoming_xp))

    if current_attr >= MAX_ATTRIBUTE_VALUE:
        return XpApplyResult(
            applied_points=0,
            residual_xp=0,
            prestige_xp=residual + incoming,
            reached_cap=True,
        )

    available_points = max(0, MAX_ATTRIBUTE_VALUE - current_attr)
    buffer_xp = residual + incoming
    converted = convert_xp_to_attribute_points(buffer_xp)

    applied_points = min(converted.points_gained, available_points)
    overflow_points = max(0, converted.points_gained - applied_points)
    reached_cap = applied_points == available_points and available_points > 0

    prestige_xp = overflow_points * XP_PER_ATTRIBUTE_POINT
    next_residual = converted.residual_xp

    if reached_cap:
        prestige_xp += next_residual
        next_residual = 0

    return XpApplyResult(
        applied_points=applied_points,
        residual_xp=next_residual,
        prestige_xp=prestige_xp,
        reached_cap=reached_cap,
    )


async def check_xp_consistency(session: AsyncSession) -> XpConsistencyReport:
    """Varre UserXP e move overflow/residual para UserPrestige quando atributo capa em 99.

    Regras:
    - Atributo em 99 para de acumular XP comum.
    - XP residual (e overflow comum) vai para UserPrestige.
    - level/residual de UserXP ficam coerentes com cap comum.
    """
    xp_result = await session.execute(select(UserXP))
    xp_rows = xp_result.scalars().all()

    if not xp_rows:
        return XpConsistencyReport(
            scanned_rows=0,
            capped_rows=0,
            prestige_rows_created=0,
            prestige_xp_moved=0,
        )

    user_ids = list({row.user_id for row in xp_rows})
    stats_result = await session.execute(select(PlayerStats).where(PlayerStats.user_id.in_(user_ids)))
    stats_rows = stats_result.scalars().all()
    stats_by_user = {row.user_id: row for row in stats_rows}

    capped_rows = 0
    prestige_rows_created = 0
    prestige_xp_moved = 0

    for xp_row in xp_rows:
        stats = stats_by_user.get(xp_row.user_id)
        if not stats:
            continue

        current_value = int(getattr(stats, xp_row.attribute_name, BASE_ATTRIBUTE_VALUE) or BASE_ATTRIBUTE_VALUE)

        if current_value < MAX_ATTRIBUTE_VALUE:
            continue

        capped_rows += 1

        # Bloquear progressão comum acima do cap.
        overflow_common_xp = max(0, xp_row.total_xp - MAX_COMMON_XP_TOTAL)
        movable_xp = max(0, xp_row.residual_xp) + overflow_common_xp

        _, created = await credit_prestige_xp(
            session,
            user_id=xp_row.user_id,
            attribute_name=xp_row.attribute_name,
            xp_amount=movable_xp,
        )
        prestige_xp_moved += movable_xp
        if created:
            prestige_rows_created += 1

        xp_row.level = min(xp_row.level, MAX_COMMON_LEVEL)
        xp_row.residual_xp = 0
        xp_row.total_xp = min(xp_row.total_xp, MAX_COMMON_XP_TOTAL)
        xp_row.updated_at = datetime.now(UTC)

    if capped_rows > 0:
        await session.commit()

    return XpConsistencyReport(
        scanned_rows=len(xp_rows),
        capped_rows=capped_rows,
        prestige_rows_created=prestige_rows_created,
        prestige_xp_moved=prestige_xp_moved,
    )


async def cleanup_orphaned_matches(
    session: AsyncSession,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> CleanupReport:
    """Delete MatchPerformance órfãos (sem user válido) ou com sport_type nulo.

    Executa em lotes para reduzir impacto em horário de pico.
    """
    logger = _get_maintenance_logger()
    safe_batch = max(1, int(batch_size))

    scanned_rows = 0
    deleted_rows = 0

    while True:
        orphan_query = (
            select(MatchPerformance.id, MatchPerformance.user_id, MatchPerformance.sport_type)
            .select_from(MatchPerformance)
            .outerjoin(User, User.id == MatchPerformance.user_id)
            .where(
                or_(
                    User.id.is_(None),
                    MatchPerformance.sport_type.is_(None),
                    func.length(func.trim(MatchPerformance.sport_type)) == 0,
                )
            )
            .limit(safe_batch)
        )

        result = await session.execute(orphan_query)
        rows = result.all()
        if not rows:
            break

        scanned_rows += len(rows)
        ids_to_delete = [row[0] for row in rows]

        await session.execute(delete(MatchPerformance).where(MatchPerformance.id.in_(ids_to_delete)))
        await session.commit()

        for match_id, user_id, sport_type in rows:
            logger.info(
                "JANITOR_DELETE_MATCH | match_id=%s | user_id=%s | sport_type=%s",
                match_id,
                user_id,
                sport_type,
            )

        deleted_rows += len(ids_to_delete)

    return CleanupReport(scanned_rows=scanned_rows, deleted_rows=deleted_rows)


async def backfill_missing_sub_attributes(
    session: AsyncSession,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> BackfillReport:
    """Preenche sub-atributos faltantes com default 50 em lotes de 100."""
    logger = _get_maintenance_logger()
    safe_batch = max(1, int(batch_size))

    scanned_profiles = 0
    updated_profiles = 0

    # 1) Criar perfis PlayerStats inexistentes (usuários sem sub-atributos por ausência de perfil).
    while True:
        missing_profiles_query = (
            select(User.id)
            .outerjoin(PlayerStats, PlayerStats.user_id == User.id)
            .where(PlayerStats.id.is_(None))
            .limit(safe_batch)
        )
        missing_result = await session.execute(missing_profiles_query)
        missing_user_ids = [row[0] for row in missing_result.all()]

        if not missing_user_ids:
            break

        for user_id in missing_user_ids:
            session.add(PlayerStats(user_id=user_id, position=normalize_position_input("meia")))
            updated_profiles += 1
            logger.info(
                "MIGRATION_CREATE_PROFILE | user_id=%s | default_value=%s",
                user_id,
                BASE_ATTRIBUTE_VALUE,
            )

        await session.commit()

    last_id = ""

    while True:
        query = (
            select(PlayerStats)
            .where(PlayerStats.id > last_id)
            .order_by(PlayerStats.id)
            .limit(safe_batch)
        )
        result = await session.execute(query)
        batch = result.scalars().all()

        if not batch:
            break

        scanned_profiles += len(batch)
        batch_updated = 0

        for stats in batch:
            last_id = stats.id
            if not _profile_needs_backfill(stats):
                continue

            changed = False
            for attribute_name in MAINTENANCE_ATTRIBUTES:
                if getattr(stats, attribute_name, None) is None:
                    setattr(stats, attribute_name, BASE_ATTRIBUTE_VALUE)
                    changed = True

            if changed:
                stats.updated_at = datetime.now(UTC)
                updated_profiles += 1
                batch_updated += 1
                logger.info(
                    "MIGRATION_BACKFILL_PROFILE | user_id=%s | stats_id=%s | default_value=%s",
                    stats.user_id,
                    stats.id,
                    BASE_ATTRIBUTE_VALUE,
                )

        if batch_updated > 0:
            await session.commit()

    return BackfillReport(scanned_profiles=scanned_profiles, updated_profiles=updated_profiles)
