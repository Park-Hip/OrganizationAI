"""Unit tests for typed application settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.settings import Settings


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent a developer's local .env or environment from leaking into tests."""
    for name in ("DATABASE_URL", "APP_NAME", "APP_VERSION", "ENVIRONMENT", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)


def test_defaults_apply_when_only_database_url_is_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://example:example@localhost:5432/research",
    )

    settings = Settings(_env_file=None)

    assert settings.app_name == "Decision Core"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.log_level == "INFO"


def test_database_url_is_required() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "database_url" in str(exc_info.value)


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://example:example@localhost:5432/research",
    )
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"


def test_database_url_rejects_non_postgres_scheme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_url_is_masked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://example:secret@localhost:5432/research",
    )

    settings = Settings(_env_file=None)

    assert "secret" not in str(settings.database_url)
    assert settings.database_url.get_secret_value() == (
        "postgresql+psycopg2://example:secret@localhost:5432/research"
    )
