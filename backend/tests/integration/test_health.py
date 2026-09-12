"""Integration tests for the health endpoint."""

from __future__ import annotations

from typing import Any, Literal

import pytest
from fastapi.testclient import TestClient

from app.api import health as health_module


class _FakeConnection:
    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Literal[False]:
        return False

    def execute(self, statement: Any) -> None:
        return None


class _ReachableEngine:
    def connect(self) -> _FakeConnection:
        return _FakeConnection()


class _UnreachableEngine:
    def connect(self) -> _FakeConnection:
        raise RuntimeError("database unavailable")


def _patch_engine(monkeypatch: pytest.MonkeyPatch, engine: Any) -> None:
    monkeypatch.setattr(health_module, "build_engine", lambda: engine)


def test_health_is_ok_when_database_responds(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_engine(monkeypatch, _ReachableEngine())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_health_is_degraded_when_database_is_unreachable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_engine(monkeypatch, _UnreachableEngine())

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}
