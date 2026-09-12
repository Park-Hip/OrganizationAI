"""Shared pytest fixtures for the OrganizationalAI backend."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.settings import get_settings

TEST_DATABASE_URL = "postgresql+psycopg2://decisioncore:decisioncore@localhost:5432/decisioncore"


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    """Prevent cached settings from leaking across tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """Return a fresh application instance per test."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Return a TestClient bound to the fresh application instance."""
    with TestClient(app) as test_client:
        yield test_client
