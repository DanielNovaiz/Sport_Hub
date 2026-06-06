"""Configuração do banco de dados com SQLModel e PostGIS"""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app import models as _models  # noqa: F401
from app.core.config import settings

logger = logging.getLogger(__name__)

# Engine assíncrono
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def _is_transient_database_startup_error(error: Exception) -> bool:
    message = str(error).lower()
    transient_markers = (
        "could not translate host name",
        "name or service not known",
        "temporary failure in name resolution",
        "no address associated with hostname",
        "connection refused",
        "could not connect to server",
        "server closed the connection",
    )
    return isinstance(error, (OSError, TimeoutError, ConnectionError, socket.gaierror)) or any(
        marker in message for marker in transient_markers
    )


async def init_db(max_attempts: int = 8, initial_delay_seconds: float = 1.0) -> bool:
    """Inicializa o banco de dados criando as tabelas.

    Retorna False quando a falha parece ser só de disponibilidade do Postgres
    após todas as tentativas, para permitir startup em modo degradado.
    """
    delay_seconds = initial_delay_seconds

    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.begin() as conn:
                # Habilita extensão PostGIS
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                logger.info("Extensão PostGIS habilitada")

                # Cria as tabelas
                await conn.run_sync(SQLModel.metadata.create_all)
                logger.info("Tabelas criadas com sucesso")

                # Cria índices geoespaciais
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_event_location 
                        ON event USING GIST(location)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_user_location
                        ON "user" USING GIST(location)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_user_location_geography
                        ON "user" USING GIST((location::geography))
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_event_participant_event_id
                        ON event_participant(event_id)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_event_participant_user_id
                        ON event_participant(user_id)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_player_stats_overall_score
                        ON player_stats(overall DESC)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_match_performance_user_created_at
                        ON match_performance(user_id, created_at DESC)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_match_performance_event_user
                        ON match_performance(event_id, user_id)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_user_xp_user_attribute_level
                        ON user_xp(user_id, attribute_name, level DESC)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_user_achievement_user_created_at
                        ON user_achievement(user_id, created_at DESC)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_team_synergy_members_key
                        ON team_synergy(members_key)
                    """)
                )
                await conn.execute(
                    text("""
                        CREATE INDEX IF NOT EXISTS idx_season_rank_xp_total
                        ON season_rank(xp_total DESC)
                    """)
                )
                logger.info("Índices geoespaciais e relacionais criados")
                return True
        except SQLAlchemyError as error:
            if not _is_transient_database_startup_error(error):
                raise
            logger.warning(
                "Banco ainda indisponível na inicialização (tentativa %s/%s): %s",
                attempt,
                max_attempts,
                error,
            )
        except Exception as error:
            if not _is_transient_database_startup_error(error):
                raise
            logger.warning(
                "Banco ainda indisponível na inicialização (tentativa %s/%s): %s",
                attempt,
                max_attempts,
                error,
            )

        if attempt < max_attempts:
            await asyncio.sleep(delay_seconds)
            delay_seconds = min(delay_seconds * 2, 5.0)

    logger.warning("Banco não respondeu após todas as tentativas; iniciando em modo degradado")
    return False


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obter a sessão do banco de dados"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Fecha todas as conexões do engine"""
    await engine.dispose()
