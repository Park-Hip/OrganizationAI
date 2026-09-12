"""Integration tests for the health endpoint."""

from __future__ import annotations

from typing import Any, Literal, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.persistence.db import build_engine


class _FakeConnection:
    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Literal[False]:
        return False

    def execute(self, statement: Any) -> None:
        return None


class _FakeEngine:
    def connect(self) -> _FakeConnection:
        return _FakeConnection()


def test_health_is_reachable_when_database_responds(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    app.dependency_overrides[build_engine] = lambda: _FakeEngine()
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_health_is_degraded_when_database_is_unreachable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.settings import get_settings

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://nobody:nothing@127.0.0.1:65432/missing",
    )
    get_settings.cache_clear()
    build_engine.cache_clear()

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}
