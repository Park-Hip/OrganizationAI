"""Typed application settings for the temporary L0 foundation."""

from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, immutable application configuration.

    ``database_url`` is intentionally required with no default.
    Failing fast with a clear validation error is safer than starting a
    service that half-works without a database.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "OrganizationalAI"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: SecretStr

    @field_validator("database_url")
    @classmethod
    def _database_url_uses_postgres(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("database_url must be a PostgreSQL connection URL")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings value, resolved once."""
    return Settings()
