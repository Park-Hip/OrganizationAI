"""Shared pytest fixtures for the Decision Core backend."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "postgresql+psycopg2://decisioncore:decisioncore@localhost:5432/decisioncore"


@pytest.fixture
def app() -> FastAPI:
    """Return a fresh application instance per test."""
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Return a TestClient bound to the fresh application instance."""
    with TestClient(app) as test_client:
        yield test_client
