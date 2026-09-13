"""Migration contract tests for the temporary decision-history schema."""

from __future__ import annotations

from _db_utils import run_alembic
from sqlalchemy import Engine, inspect, text

pytest_plugins = ["_db_utils"]

_TABLES = (
    "temporary_case_snapshots",
    "temporary_decision_snapshots",
    "temporary_audit_events",
)
_TRIGGERS = {
    "trg_temporary_case_snapshots_immutable",
    "trg_temporary_decision_snapshots_immutable",
    "trg_temporary_audit_events_immutable",
}


def test_upgrade_creates_the_temporary_history_tables(migrated_test_engine: Engine) -> None:
    inspector = inspect(migrated_test_engine)
    assert set(_TABLES) <= set(inspector.get_table_names())


def test_case_snapshot_columns_and_unique_constraint(migrated_test_engine: Engine) -> None:
    inspector = inspect(migrated_test_engine)
    columns = {column["name"] for column in inspector.get_columns("temporary_case_snapshots")}
    assert {
        "trace_id",
        "case_id",
        "recorded_at",
        "submission_snapshot",
        "normalized_snapshot",
        "profile_id",
        "profile_source",
        "data_class",
        "workflow_validation_status",
    } <= columns

    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("temporary_case_snapshots")
    }
    assert "uq_temporary_case_snapshots_case_id" in unique_names


def test_decision_snapshot_is_unique_per_trace(migrated_test_engine: Engine) -> None:
    inspector = inspect(migrated_test_engine)
    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("temporary_decision_snapshots")
    }
    assert "uq_temporary_decision_snapshots_trace_id" in unique_names


def test_audit_event_sequence_constraints(migrated_test_engine: Engine) -> None:
    inspector = inspect(migrated_test_engine)
    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("temporary_audit_events")
    }
    check_names = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("temporary_audit_events")
    }
    assert "uq_temporary_audit_events_trace_sequence" in unique_names
    assert "ck_temporary_audit_events_sequence_positive" in check_names


def test_immutability_triggers_and_function_exist(migrated_test_engine: Engine) -> None:
    with migrated_test_engine.connect() as connection:
        trigger_names = set(
            connection.execute(
                text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
            ).scalars()
        )
        function_names = set(
            connection.execute(
                text("SELECT proname FROM pg_proc WHERE proname = 'temporary_history_immutable'")
            ).scalars()
        )
    assert _TRIGGERS <= trigger_names
    assert "temporary_history_immutable" in function_names


def test_downgrade_and_reupgrade_on_a_clean_database(migrated_test_engine: Engine) -> None:
    run_alembic("downgrade", "base")
    inspector = inspect(migrated_test_engine)
    assert "temporary_case_snapshots" not in set(inspector.get_table_names())

    run_alembic("upgrade", "head")
    inspector = inspect(migrated_test_engine)
    assert set(_TABLES) <= set(inspector.get_table_names())
