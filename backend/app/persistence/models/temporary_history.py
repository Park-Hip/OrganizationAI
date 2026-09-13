"""Immutable temporary decision-history tables for TMP-DEV-001.

These are persistence records only. They are not part of the frozen Layer 0
domain shapes, and they never describe a real reimbursement history.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.db import Base


class AuditActorType(str, Enum):  # noqa: UP042
    """Technical actor labels. SYSTEM is not a human or authority claim."""

    SYSTEM = "SYSTEM"


class AuditAction(str, Enum):  # noqa: UP042
    """The only actions recorded by a submitted temporary trace."""

    CASE_RECEIVED = "CASE_RECEIVED"
    CASE_NORMALIZED = "CASE_NORMALIZED"
    DECISION_RECORDED = "DECISION_RECORDED"


class TemporaryCaseSnapshot(Base):
    """One immutable synthetic case, its facts, and its provenance markers."""

    __tablename__ = "temporary_case_snapshots"
    __table_args__ = (UniqueConstraint("case_id", name="uq_temporary_case_snapshots_case_id"),)

    trace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(255), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submission_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    normalized_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_source: Mapped[str] = mapped_column(String(255), nullable=False)
    data_class: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_validation_status: Mapped[str] = mapped_column(String(255), nullable=False)

    decision: Mapped[TemporaryDecisionSnapshot] = relationship(
        back_populates="case", uselist=False, lazy="selectin"
    )
    events: Mapped[list[TemporaryAuditEvent]] = relationship(
        back_populates="case", lazy="selectin", order_by="TemporaryAuditEvent.sequence_number"
    )


class TemporaryDecisionSnapshot(Base):
    """One immutable stored decision and the profile snapshot that produced it."""

    __tablename__ = "temporary_decision_snapshots"
    __table_args__ = (
        UniqueConstraint("trace_id", name="uq_temporary_decision_snapshots_trace_id"),
    )

    decision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    trace_id: Mapped[UUID] = mapped_column(
        ForeignKey("temporary_case_snapshots.trace_id"), nullable=False
    )
    profile_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    applied_rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped[TemporaryCaseSnapshot] = relationship(back_populates="decision")


class TemporaryAuditEvent(Base):
    """One append-only, ordered system event in a temporary trace."""

    __tablename__ = "temporary_audit_events"
    __table_args__ = (
        UniqueConstraint(
            "trace_id", "sequence_number", name="uq_temporary_audit_events_trace_sequence"
        ),
        CheckConstraint("sequence_number > 0", name="ck_temporary_audit_events_sequence_positive"),
    )

    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    trace_id: Mapped[UUID] = mapped_column(
        ForeignKey("temporary_case_snapshots.trace_id"), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("temporary_audit_events.event_id"), nullable=True
    )
    actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped[TemporaryCaseSnapshot] = relationship(back_populates="events")
