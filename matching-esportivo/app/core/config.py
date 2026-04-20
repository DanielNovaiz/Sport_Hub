"""Configurações da aplicação"""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações centralizadas da aplicação"""

    # ==================== APP ====================
    app_name: str = "Matching Esportivo"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_port: int = 8000
    uvicorn_workers: int = 1
    allowed_origins: str = "*"

    # ==================== DATABASE ====================
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "matching_db"
    db_user: str = "postgres"
    db_password: str = "postgres_dev_password"

    @property
    def database_url(self) -> str:
        """Constrói a URL de conexão do PostgreSQL"""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_async(self) -> str:
        """Constrói a URL de conexão assíncrona do PostgreSQL"""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ==================== REDIS ====================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        """Constrói a URL do Redis"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ==================== SECURITY ====================
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ==================== MATCHING ====================
    default_proximity_radius_km: float = 15.0
    max_events_per_search: int = 50

    @property
    def allowed_origins_list(self) -> list[str]:
        """Retorna lista de origins a partir de CSV no env."""
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        normalized = value.lower()
        valid = {"development", "staging", "production", "test"}
        if normalized not in valid:
            raise ValueError(f"app_env inválido: {value}. Use one of {sorted(valid)}")
        return normalized

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env == "production":
            missing = []

            if not self.db_host:
                missing.append("DB_HOST")
            if not self.db_name:
                missing.append("DB_NAME")
            if not self.db_user:
                missing.append("DB_USER")
            if not self.db_password or self.db_password == "postgres_dev_password":
                missing.append("DB_PASSWORD")
            if not self.secret_key or "change" in self.secret_key.lower() or len(self.secret_key) < 32:
                missing.append("SECRET_KEY")
            if not self.redis_password:
                missing.append("REDIS_PASSWORD")
            if self.debug:
                missing.append("DEBUG(false)")
            if self.allowed_origins.strip() in {"", "*"}:
                missing.append("ALLOWED_ORIGINS(non-wildcard)")

            if missing:
                raise ValueError(
                    "Configuração de produção inválida. Ajuste variáveis: " + ", ".join(missing)
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


# Instância global de settings
settings = Settings()
