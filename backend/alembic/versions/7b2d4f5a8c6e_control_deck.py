"""temporary control deck: idempotency and command fingerprint columns

Revision ID: 7b2d4f5a8c6e
Revises: 6a1c2e3f9b4d
Create Date: 2026-02-14 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "7b2d4f5a8c6e"
down_revision = "6a1c2e3f9b4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable idempotency/fingerprint columns and a partial unique index."""
    op.add_column(
        "temporary_audit_events", sa.Column("idempotency_key", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "temporary_audit_events",
        sa.Column("command_fingerprint", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "uq_temporary_audit_events_trace_idempotency",
        "temporary_audit_events",
        ["trace_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove the control idempotency index and columns only."""
    op.drop_index(
        "uq_temporary_audit_events_trace_idempotency", table_name="temporary_audit_events"
    )
    op.drop_column("temporary_audit_events", "command_fingerprint")
    op.drop_column("temporary_audit_events", "idempotency_key")
