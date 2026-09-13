"""Service-level database integration tests for temporary decision history."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from itertools import count
from typing import NoReturn
from uuid import UUID

import pytest
from sqlalchemy import Engine, delete, func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql import Executable

import app.application.temporary_history as service_module
from app.application.temporary_history import (
    TEMPORARY_NOTICE,
    TraceAlreadyRecordedError,
    read_trace,
    submit_trace,
)
from app.domain.enums import EvidenceStatus, TemporaryCategory
from app.domain.models import CaseSubmission, Expense
from app.persistence.models.temporary_history import (
    TemporaryAuditEvent,
    TemporaryCaseSnapshot,
    TemporaryDecisionSnapshot,
)
from app.persistence.repositories.temporary_history import TemporaryHistoryRepository

pytest_plugins = ["_db_utils"]

_FIXED_NOW = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)


def _fixed_clock() -> datetime:
    return _FIXED_NOW


def _sequential_id_factory() -> Callable[[], UUID]:
    counter = count(1)

    def factory() -> UUID:
        return UUID(int=next(counter))

    return factory


def _routine_submission(case_id: str = "TMP-DB-01") -> CaseSubmission:
    return CaseSubmission(
        case_id=case_id,
        submitted_at=datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC),
        requester_role="TEST_REQUESTER",
        purpose="Synthetic allowed expense",
        expense=Expense(
            category=TemporaryCategory.TEST_ALLOWED,
            description="Synthetic materials line",
            amount_vnd=999,
            expense_date=date(2030, 1, 1),
            evidence_status=EvidenceStatus.PRESENT,
        ),
    )


def _incomplete_submission(case_id: str = "TMP-DB-MISS") -> CaseSubmission:
    return CaseSubmission(
        case_id=case_id,
        submitted_at=datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC),
        requester_role=None,
        purpose=None,
        expense=None,
    )


class _FailAfterDecisionWrite(TemporaryHistoryRepository):
    """Persist a partial trace and then fail to prove transactional rollback."""

    def __init__(self) -> None:
        self.captured_case: TemporaryCaseSnapshot | None = None

    def add_trace(
        self,
        session: Session,
        case: TemporaryCaseSnapshot,
        decision: TemporaryDecisionSnapshot,
        events: list[TemporaryAuditEvent],
    ) -> None:
        self.captured_case = case
        session.add(case)
        session.add(decision)
        session.flush()
        raise RuntimeError("forced write failure")


def _assert_immutable(engine: Engine, statement: Executable) -> None:
    with pytest.raises(Exception, match="immutable"):
        with engine.begin() as connection:
            connection.execute(statement)


def test_submit_and_retrieve_reconstructs_a_full_trace(session: Session) -> None:
    result = submit_trace(
        _routine_submission(), session, clock=_fixed_clock, id_factory=_sequential_id_factory()
    )

    assert result.temporary_notice == TEMPORARY_NOTICE
    assert result.provenance.profile_id == "TMP-DEV-001"
    assert result.provenance.profile_source == "TEMPORARY_DEVELOPMENT"
    assert result.provenance.data_class == "SYNTHETIC"
    assert result.provenance.workflow_validation_status == "UNVALIDATED"
    assert result.submission["case_id"] == "TMP-DB-01"
    assert result.facts_used["purpose"] == "Synthetic allowed expense"
    assert result.decision.outcome == "AUTO_APPROVED"
    assert result.decision.applied_rule_id == "TMP-AUT-01"
    assert (
        result.decision.reason
        == "Approved under temporary development profile; no payment was made."
    )
    assert result.decision.question is None

    actions = [event.action for event in result.events]
    sequences = [event.sequence_number for event in result.events]
    assert actions == ["CASE_RECEIVED", "CASE_NORMALIZED", "DECISION_RECORDED"]
    assert sequences == [1, 2, 3]
    assert result.events[0].previous_event_id is None
    assert result.events[1].previous_event_id == result.events[0].event_id
    assert result.events[2].previous_event_id == result.events[1].event_id

    retrieved = read_trace(result.trace_id, session)
    assert retrieved.model_dump(mode="json") == result.model_dump(mode="json")


def test_event_ordering_holds_when_server_timestamps_are_equal(session: Session) -> None:
    result = submit_trace(_routine_submission("TMP-ORDER"), session, clock=_fixed_clock)

    recorded_times = {event.recorded_at for event in result.events}
    assert len(recorded_times) == 1  # a fixed clock makes every event share a timestamp
    assert [event.sequence_number for event in result.events] == [1, 2, 3]


def test_service_uses_the_real_normalization_and_evaluation_path(session: Session) -> None:
    result = submit_trace(_incomplete_submission(), session, clock=_fixed_clock)

    assert result.decision.outcome == "MISSING_FACT"
    assert result.decision.applied_rule_id == "TMP-REQ-01"
    assert result.decision.question is not None


def test_failed_write_leaves_no_partial_records(session: Session) -> None:
    repository = _FailAfterDecisionWrite()

    with pytest.raises(RuntimeError, match="forced write failure"):
        submit_trace(
            _routine_submission("TMP-ATOMIC"),
            session,
            repository=repository,
            clock=_fixed_clock,
        )

    session.rollback()
    assert session.scalar(select(func.count()).select_from(TemporaryCaseSnapshot)) == 0
    assert session.scalar(select(func.count()).select_from(TemporaryDecisionSnapshot)) == 0
    assert session.scalar(select(func.count()).select_from(TemporaryAuditEvent)) == 0


def test_stored_history_rejects_update_and_delete(
    migrated_test_engine: Engine, session: Session
) -> None:
    result = submit_trace(_routine_submission("TMP-IMMUTABLE"), session, clock=_fixed_clock)
    trace_id = result.trace_id

    _assert_immutable(
        migrated_test_engine,
        update(TemporaryCaseSnapshot)
        .where(TemporaryCaseSnapshot.trace_id == trace_id)
        .values(case_id="CHANGED"),
    )
    _assert_immutable(
        migrated_test_engine,
        delete(TemporaryDecisionSnapshot).where(TemporaryDecisionSnapshot.trace_id == trace_id),
    )
    _assert_immutable(
        migrated_test_engine,
        update(TemporaryAuditEvent)
        .where(TemporaryAuditEvent.trace_id == trace_id)
        .values(sequence_number=99),
    )


def test_duplicate_case_id_preserves_the_first_trace(session: Session) -> None:
    first = submit_trace(_routine_submission("TMP-DUP"), session, clock=_fixed_clock)

    with pytest.raises(TraceAlreadyRecordedError):
        submit_trace(_routine_submission("TMP-DUP"), session, clock=_fixed_clock)

    assert session.scalar(select(func.count()).select_from(TemporaryCaseSnapshot)) == 1
    assert read_trace(first.trace_id, session).submission["case_id"] == "TMP-DUP"


def test_retrieval_never_reevaluates_the_decision(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = submit_trace(_routine_submission("TMP-READ"), session, clock=_fixed_clock)

    def _boom(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("read path must not call the evaluator or normalizer")

    monkeypatch.setattr(service_module, "normalize_case", _boom)
    monkeypatch.setattr(service_module, "evaluate_case", _boom)

    retrieved = read_trace(result.trace_id, session)
    assert retrieved.decision.outcome == "AUTO_APPROVED"
    assert retrieved.decision.applied_rule_id == "TMP-AUT-01"
