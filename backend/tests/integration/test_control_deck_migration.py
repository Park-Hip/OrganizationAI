"""Migration contract tests for the temporary Control Deck schema extension."""

from __future__ import annotations

from typing import Any

from _db_utils import run_alembic
from sqlalchemy import Engine, inspect

pytest_plugins = ["_db_utils"]

_HISTORY_REVISION = "6a1c2e3f9b4d"


def _columns(engine: Engine) -> dict[str, Any]:
    inspector = inspect(engine)
    return {column["name"]: column for column in inspector.get_columns("temporary_audit_events")}


def test_control_columns_are_nullable(migrated_test_engine: Engine) -> None:
    columns = _columns(migrated_test_engine)

    assert "idempotency_key" in columns
    assert "command_fingerprint" in columns
    assert columns["idempotency_key"]["nullable"] is True
    assert columns["command_fingerprint"]["nullable"] is True


def test_partial_unique_index_covers_trace_and_key(migrated_test_engine: Engine) -> None:
    indexes = {
        index["name"]: index
        for index in inspect(migrated_test_engine).get_indexes("temporary_audit_events")
    }

    assert "uq_temporary_audit_events_trace_idempotency" in indexes
    index = indexes["uq_temporary_audit_events_trace_idempotency"]
    assert index["unique"] is True
    column_names = [name for name in (index["column_names"] or []) if name is not None]
    assert sorted(column_names) == ["idempotency_key", "trace_id"]


def test_downgrade_reverts_to_history_head_and_reupgrades(migrated_test_engine: Engine) -> None:
    run_alembic("downgrade", _HISTORY_REVISION)
    columns = _columns(migrated_test_engine)
    assert "idempotency_key" not in columns
    assert "command_fingerprint" not in columns

    run_alembic("upgrade", "head")
    columns = _columns(migrated_test_engine)
    assert "idempotency_key" in columns
    assert "command_fingerprint" in columns
