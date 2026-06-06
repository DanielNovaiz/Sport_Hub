"""Aplicação principal FastAPI"""

import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware 

from app.core.config import settings
from app.core.database import init_db, close_db, async_session
from app.core.redis import close_redis, get_redis
from app.core.logger import configure_logging
from app.repositories import StructuredTelemetryRepository
from app.middleware.match_performance_rate_limit import MatchPerformanceRateLimitMiddleware
from app.services.self_healing_service import recalculate_impossible_overalls
from app.api import auth_router, clubs_router, events_router, feed_router, notifications_router, users_router, ranked_router, ranking_router, chat_router, court_router

# Configurar logging
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager para lifecycle da aplicação"""
    # Startup
    logger.info("starting_application", extra={"app": settings.app_name, "env": settings.app_env})
    try:
        db_ready = await init_db()
        if not db_ready:
            logger.warning("database_starting_in_degraded_mode")
    except Exception as error:
        logger.exception("database_startup_failed", extra={"error": str(error)})
        logger.warning("database_starting_in_degraded_mode")

    try:
        redis_client = await get_redis()
        if redis_client is None:
            logger.warning("redis_unavailable_starting_degraded_mode")
        else:
            logger.info("redis_connected")
    except Exception as error:
        logger.warning("redis_init_failed", extra={"error": str(error)})
    logger.info("database_initialized")

    try:
        async with async_session() as session:
            healing = await recalculate_impossible_overalls(session)
            logger.info("startup_self_healing", extra=healing)
    except Exception as error:
        logger.exception("startup_self_healing_failed", extra={"error": str(error)})
    
    yield
    
    # Shutdown
    logger.info("shutting_down_application")
    try:
        await close_redis()
    except Exception as error:
        logger.warning("redis_shutdown_failed", extra={"error": str(error)})
    await close_db()
    logger.info("connections_closed")


# Criar app
app = FastAPI(
    title=settings.app_name,
    description="SaaS de matching de usuários para esportes e criação de eventos",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MatchPerformanceRateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Incluir routers
app.include_router(events_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(clubs_router)
app.include_router(feed_router)
app.include_router(notifications_router)
app.include_router(ranked_router)
app.include_router(ranking_router)
app.include_router(chat_router)
app.include_router(court_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.exception("unhandled_server_error", extra={"path": str(request.url.path)})
    stacktrace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    telemetry = StructuredTelemetryRepository()
    telemetry.emit(
        category="unhandled_exception",
        user_id="system",
        entries=[str(exc), stacktrace],
        extra={"path": str(request.url.path)},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "internal_server_error",
            "detail": "Ocorreu um erro inesperado. Nossa equipe já foi notificada.",
        },
    )


@app.get("/", tags=["health"])
async def root():
    """Health check e informações da API"""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "status": "healthy",
        "environment": settings.app_env,
    }


@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """
    Health check assíncrono com verificação do banco de dados.
    
    Valida:
    - Status da aplicação FastAPI
    - Conexão com PostgreSQL
    - Disponibilidade de PostGIS
    
    Returns:
        JSON com status de cada componente
        
    Status codes:
        200: Tudo OK
        503: Serviço indisponível (DB down)
    """
    try:
        # Verifica conexão com DB de forma assíncrona
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            db_status = "connected"
    except Exception as e:
        logger.error(f"❌ DB health check falhou: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "app": "operational",
                "database": "disconnected",
                "error": str(e),
            },
        )
    
    return {
        "status": "healthy",
        "app": "operational",
        "database": db_status,
        "version": "0.1.0",
    }


@app.get("/health/db", tags=["health"], status_code=status.HTTP_200_OK)
async def health_check_db() -> dict[str, str]:
    """
    Health check específico para banco de dados.
    
    Verifica:
    - Conexão PostgreSQL
    - Extensão PostGIS
    
    Returns:
        JSON com status do DB
        
    Status codes:
        200: DB pronto
        503: DB indisponível
    """
    try:
        async with async_session() as session:
            # Verifica PostgreSQL
            await session.execute(text("SELECT 1"))
            
            # Verifica PostGIS
            result = await session.execute(text("SELECT postgis_version()"))
            postgis_version = result.scalar()
            
        return {
            "status": "healthy",
            "database": "connected",
            "postgis": "available",
            "version": postgis_version or "unknown",
        }
    
    except Exception as e:
        logger.error(f"❌ DB specific health check falhou: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "postgis": "unavailable",
                "error": str(e),
            },
        )


@app.get("/health/redis", tags=["health"], status_code=status.HTTP_200_OK)
async def health_check_redis() -> dict[str, str]:
    """Health check específico para Redis."""
    try:
        redis_client = await get_redis()
        if redis_client is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unhealthy", "redis": "disconnected"},
            )
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as error:
        logger.error("redis_healthcheck_failed", extra={"error": str(error)})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "redis": "disconnected", "error": str(error)},
        )



if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
