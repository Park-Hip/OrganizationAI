"""Insert-only and read-only repository for temporary decision history."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.persistence.models.temporary_history import (
    TemporaryAuditEvent,
    TemporaryCaseSnapshot,
    TemporaryDecisionSnapshot,
)


class TemporaryHistoryRepository:
    """Persist complete traces and read stored traces without mutation."""

    def add_trace(
        self,
        session: Session,
        case: TemporaryCaseSnapshot,
        decision: TemporaryDecisionSnapshot,
        events: list[TemporaryAuditEvent],
    ) -> None:
        """Register one complete trace in the unit of work managed by ``session``."""
        session.add(case)
        session.add(decision)
        session.add_all(events)

    def case_id_exists(self, session: Session, case_id: str) -> bool:
        """Return whether a synthetic client case ID already has a stored trace."""
        statement = select(TemporaryCaseSnapshot.trace_id).where(
            TemporaryCaseSnapshot.case_id == case_id
        )
        return session.scalar(statement.limit(1)) is not None

    def find_trace(self, session: Session, trace_id: UUID) -> TemporaryCaseSnapshot | None:
        """Return a stored trace with its decision and events eagerly loaded."""
        statement = (
            select(TemporaryCaseSnapshot)
            .where(TemporaryCaseSnapshot.trace_id == trace_id)
            .options(
                selectinload(TemporaryCaseSnapshot.decision),
                selectinload(TemporaryCaseSnapshot.events),
            )
        )
        return session.scalars(statement).first()
