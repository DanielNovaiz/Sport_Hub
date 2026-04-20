"""Repositórios de persistência da aplicação."""

from app.repositories.telemetry_repository import StructuredTelemetryRepository
from app.repositories.xp_repository import SqlAlchemyXpRepository

__all__ = ["StructuredTelemetryRepository", "SqlAlchemyXpRepository"]
