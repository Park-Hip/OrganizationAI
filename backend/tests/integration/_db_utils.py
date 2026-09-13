"""Shared fixtures and helpers for database integration tests.

This module is loaded via ``pytest_plugins`` from each integration test module
so it is not collected as a test file itself and does not duplicate the
top-level ``tests/conftest.py`` module name for static checking.

The fixtures require a reachable, synthetic-only PostgreSQL test database. They
skip with a clear message when it is unavailable so the short local quality
loop keeps working without Docker.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[2]

_TRUNCATE_TABLES_SQL = (
    "TRUNCATE temporary_audit_events, "
    "temporary_decision_snapshots, "
    "temporary_case_snapshots RESTART IDENTITY CASCADE"
)


def test_database_url() -> str:
    """Return the isolated synthetic-only test database URL from the environment."""
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL must name the synthetic-only test database")
    return database_url


def run_alembic(*args: str) -> None:
    """Run Alembic against the isolated test database as a subprocess."""
    env = {**os.environ, "DATABASE_URL": test_database_url()}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")


@pytest.fixture(scope="session")
def test_engine() -> Engine:
    """Return an engine for the isolated test database, or skip when unreachable."""
    engine = create_engine(test_database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on the local environment
        engine.dispose()
        pytest.skip(f"temporary-history test database unavailable: {exc}")
    return engine


@pytest.fixture(scope="session")
def migrated_test_engine(test_engine: Engine) -> Engine:
    """Reset the test schema and apply the migration to head exactly once."""
    with test_engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    run_alembic("upgrade", "head")
    return test_engine


@pytest.fixture(scope="session")
def test_session_factory(migrated_test_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=migrated_test_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
def session(
    migrated_test_engine: Engine, test_session_factory: sessionmaker[Session]
) -> Iterator[Session]:
    """Yield a session against a freshly truncated synthetic schema."""
    with migrated_test_engine.begin() as connection:
        connection.execute(text(_TRUNCATE_TABLES_SQL))
    with test_session_factory() as opened:
        yield opened
        opened.rollback()
