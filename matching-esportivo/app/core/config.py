"""Configurações da aplicação."""

from __future__ import annotations

import os


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _get_bool_env(name: str, default: bool) -> bool:
    value = _get_env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = _get_env(name)
    if value is None:
        return default
    return int(value)


def _get_float_env(name: str, default: float) -> float:
    value = _get_env(name)
    if value is None:
        return default
    return float(value)


class Settings:
    """Configurações centralizadas da aplicação."""

    def __init__(self) -> None:
        self.app_name = _get_env("APP_NAME", "Matching Esportivo")
        self.app_env = (_get_env("APP_ENV", "development") or "development").lower()
        self.debug = _get_bool_env("DEBUG", self.app_env != "production")
        self.log_level = _get_env("LOG_LEVEL", "INFO")
        self.api_port = _get_int_env("API_PORT", 8000)
        self.uvicorn_workers = _get_int_env("UVICORN_WORKERS", 1)
        self.allowed_origins = _get_env("ALLOWED_ORIGINS", "*")

        self.db_host = _get_env("DB_HOST", "localhost" if self.app_env != "production" else None)
        self.db_port = _get_int_env("DB_PORT", 5432)
        self.db_name = _get_env("DB_NAME", "matching_db" if self.app_env != "production" else None)
        self.db_user = _get_env("DB_USER", "postgres" if self.app_env != "production" else None)
        self.db_password = _get_env(
            "DB_PASSWORD",
            "postgres_dev_password" if self.app_env != "production" else None,
        )

        self.redis_host = _get_env("REDIS_HOST", "localhost" if self.app_env != "production" else None)
        self.redis_port = _get_int_env("REDIS_PORT", 6379)
        self.redis_db = _get_int_env("REDIS_DB", 0)
        self.redis_password = _get_env("REDIS_PASSWORD", "" if self.app_env != "production" else None)

        self.secret_key = _get_env(
            "SECRET_KEY",
            f"{self.app_name}:{self.app_env}:local-only-jwt-key",
        )
        self.algorithm = _get_env("ALGORITHM", "HS256")
        self.access_token_expire_minutes = _get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30)

        self.default_proximity_radius_km = _get_float_env("DEFAULT_PROXIMITY_RADIUS_KM", 15.0)
        self.max_events_per_search = _get_int_env("MAX_EVENTS_PER_SEARCH", 50)

        self._validate()

    @property
    def database_url(self) -> str:
        """Constrói a URL de conexão do PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_async(self) -> str:
        """Constrói a URL de conexão assíncrona do PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        """Constrói a URL do Redis."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Retorna lista de origins a partir de CSV no env."""
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def _validate(self) -> None:
        valid_envs = {"development", "staging", "production", "test"}
        if self.app_env not in valid_envs:
            raise ValueError(f"app_env inválido: {self.app_env}. Use one of {sorted(valid_envs)}")

        if self.app_env == "production":
            missing = []
            for key, value in {
                "DB_HOST": self.db_host,
                "DB_NAME": self.db_name,
                "DB_USER": self.db_user,
                "DB_PASSWORD": self.db_password,
                "REDIS_HOST": self.redis_host,
                "REDIS_PASSWORD": self.redis_password,
                "SECRET_KEY": self.secret_key,
                "ALLOWED_ORIGINS": self.allowed_origins,
            }.items():
                if not value:
                    missing.append(key)

            if self.debug:
                missing.append("DEBUG=false")

            if self.allowed_origins.strip() == "*":
                missing.append("ALLOWED_ORIGINS(non-wildcard)")

            if not self.secret_key or len(self.secret_key) < 32 or "local-only" in self.secret_key.lower():
                missing.append("SECRET_KEY(32+ chars)")

            if missing:
                raise ValueError("Configuração de produção inválida. Ajuste variáveis: " + ", ".join(sorted(set(missing))))


settings = Settings()
