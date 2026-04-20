"""Configuração do banco de dados com SQLModel e PostGIS"""

import logging
from typing import AsyncGenerator

from sqlalchemy import text
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


async def init_db() -> None:
    """Inicializa o banco de dados criando as tabelas"""
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
