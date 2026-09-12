"""Shared pytest fixtures for the Decision Core backend."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Return a fresh application instance per test."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Return a TestClient bound to the fresh application instance."""
    with TestClient(app) as test_client:
        yield test_client
