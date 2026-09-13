"""temporary synthetic decision history

Revision ID: 6a1c2e3f9b4d
Revises:
Create Date: 2026-02-14 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "6a1c2e3f9b4d"
down_revision = None
branch_labels = None
depends_on = None

_IMMUTABLE_FUNCTION = "temporary_history_immutable"
_TRIGGERS = (
    "trg_temporary_case_snapshots_immutable",
    "trg_temporary_decision_snapshots_immutable",
    "trg_temporary_audit_events_immutable",
)


def _table_for(trigger: str) -> str:
    return trigger.removeprefix("trg_").removesuffix("_immutable")


def upgrade() -> None:
    """Create the three immutable snapshot/event tables and their triggers."""
    op.create_table(
        "temporary_case_snapshots",
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.Text, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submission_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("normalized_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("profile_id", sa.String(length=255), nullable=False),
        sa.Column("profile_source", sa.String(length=255), nullable=False),
        sa.Column("data_class", sa.String(length=255), nullable=False),
        sa.Column("workflow_validation_status", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("case_id", name="uq_temporary_case_snapshots_case_id"),
    )

    op.create_table(
        "temporary_decision_snapshots",
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "trace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("temporary_case_snapshots.trace_id"),
            nullable=False,
        ),
        sa.Column("profile_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("profile_id", sa.String(length=255), nullable=False),
        sa.Column("outcome", sa.String(length=64), nullable=False),
        sa.Column("applied_rule_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("question", sa.Text, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("trace_id", name="uq_temporary_decision_snapshots_trace_id"),
    )

    op.create_table(
        "temporary_audit_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "trace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("temporary_case_snapshots.trace_id"),
            nullable=False,
        ),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column(
            "previous_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("temporary_audit_events.event_id"),
            nullable=True,
        ),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "trace_id", "sequence_number", name="uq_temporary_audit_events_trace_sequence"
        ),
        sa.CheckConstraint(
            "sequence_number > 0", name="ck_temporary_audit_events_sequence_positive"
        ),
    )
    op.create_index("ix_temporary_audit_events_trace_id", "temporary_audit_events", ["trace_id"])

    op.execute(
        f"""
        CREATE FUNCTION {_IMMUTABLE_FUNCTION}() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'temporary history is immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for trigger in _TRIGGERS:
        op.execute(
            f"""
            CREATE TRIGGER {trigger}
            BEFORE UPDATE OR DELETE ON {_table_for(trigger)}
            FOR EACH ROW EXECUTE FUNCTION {_IMMUTABLE_FUNCTION}();
            """
        )


def downgrade() -> None:
    """Drop the event, decision, and case tables, then the immutability function."""
    op.drop_table("temporary_audit_events")
    op.drop_table("temporary_decision_snapshots")
    op.drop_table("temporary_case_snapshots")
    op.execute(f"DROP FUNCTION IF EXISTS {_IMMUTABLE_FUNCTION}()")
