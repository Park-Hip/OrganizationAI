"""Unit tests for the temporary decision-history application service (no database)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal, cast
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.application.temporary_history import (
    TEMPORARY_NOTICE,
    TraceAlreadyRecordedError,
    TraceNotFoundError,
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

pytestmark = pytest.mark.unit

_FIXED_NOW = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)


class _FakeTransaction:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    def __enter__(self) -> _FakeTransaction:
        self._session.transaction_active = True
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> Literal[False]:
        self._session.transaction_active = False
        return False


class _FakeSession:
    def __init__(self) -> None:
        self.transaction_active = False

    def begin(self) -> _FakeTransaction:
        return _FakeTransaction(self)

    def flush(self) -> None:
        return None


class _RecordingRepository(TemporaryHistoryRepository):
    def __init__(self) -> None:
        self.case: TemporaryCaseSnapshot | None = None
        self.decision: TemporaryDecisionSnapshot | None = None
        self.events: list[TemporaryAuditEvent] = []
        self.existing_case_ids: set[str] = set()
        self.returned_trace: TemporaryCaseSnapshot | None = None
        self.find_transaction_states: list[bool] = []

    def case_id_exists(self, session: Session, case_id: str) -> bool:
        return case_id in self.existing_case_ids

    def add_trace(
        self,
        session: Session,
        case: TemporaryCaseSnapshot,
        decision: TemporaryDecisionSnapshot,
        events: list[TemporaryAuditEvent],
    ) -> None:
        self.case = case
        self.decision = decision
        self.events = list(events)
        self.returned_trace = case
        case.decision = decision
        case.events = events

    def find_trace(self, session: Session, trace_id: UUID) -> TemporaryCaseSnapshot | None:
        fake_session = cast(_FakeSession, session)
        self.find_transaction_states.append(fake_session.transaction_active)
        return self.returned_trace


def _routine_submission(case_id: str = "TMP-UNIT-01") -> CaseSubmission:
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


def _incomplete_submission(case_id: str = "TMP-UNIT-MISS") -> CaseSubmission:
    return CaseSubmission(
        case_id=case_id,
        submitted_at=datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC),
        requester_role=None,
        purpose=None,
        expense=None,
    )


def _snapshot_graph(case_id: str = "TMP-UNIT-01") -> TemporaryCaseSnapshot:
    trace_id = UUID(int=1)
    case = TemporaryCaseSnapshot(
        trace_id=trace_id,
        case_id=case_id,
        recorded_at=_FIXED_NOW,
        submission_snapshot={"case_id": case_id},
        normalized_snapshot={"purpose": "Synthetic allowed expense"},
        profile_id="TMP-DEV-001",
        profile_source="TEMPORARY_DEVELOPMENT",
        data_class="SYNTHETIC",
        workflow_validation_status="UNVALIDATED",
    )
    case.decision = TemporaryDecisionSnapshot(
        decision_id=UUID(int=2),
        trace_id=trace_id,
        profile_snapshot={"profile_id": "TMP-DEV-001"},
        profile_id="TMP-DEV-001",
        outcome="AUTO_APPROVED",
        applied_rule_id="TMP-AUT-01",
        reason="Approved under temporary development profile; no payment was made.",
        question=None,
        decided_at=_FIXED_NOW,
    )
    return case


def _event(sequence: int, action: str, previous: UUID | None) -> TemporaryAuditEvent:
    return TemporaryAuditEvent(
        event_id=UUID(int=sequence),
        trace_id=UUID(int=1),
        sequence_number=sequence,
        previous_event_id=previous,
        actor_type="SYSTEM",
        action=action,
        payload={"case_id": "TMP-UNIT-01"},
        recorded_at=_FIXED_NOW,
    )


def test_submit_trace_composes_policy_once_and_records_ordered_events() -> None:
    repository = _RecordingRepository()
    session = _FakeSession()
    fake_session = cast(Session, session)

    result = submit_trace(_routine_submission(), fake_session, repository=repository)

    assert result.temporary_notice == TEMPORARY_NOTICE
    assert repository.decision is not None
    assert repository.case is not None
    assert repository.decision.outcome == "AUTO_APPROVED"
    assert repository.decision.applied_rule_id == "TMP-AUT-01"
    assert repository.events == list(repository.case.events)
    assert [event.action for event in repository.events] == [
        "CASE_RECEIVED",
        "CASE_NORMALIZED",
        "DECISION_RECORDED",
    ]
    assert [event.sequence_number for event in repository.events] == [1, 2, 3]
    assert repository.events[0].previous_event_id is None
    assert repository.events[1].previous_event_id == repository.events[0].event_id
    assert repository.events[2].previous_event_id == repository.events[1].event_id
    assert repository.find_transaction_states == [True]
    assert not session.transaction_active


def test_submit_trace_preserves_the_real_decision_for_missing_facts() -> None:
    repository = _RecordingRepository()
    fake_session = cast(Session, _FakeSession())

    result = submit_trace(_incomplete_submission(), fake_session, repository=repository)

    assert repository.decision is not None
    assert result.decision.outcome == "MISSING_FACT"
    assert repository.decision.applied_rule_id == "TMP-REQ-01"
    assert result.decision.question is not None


def test_submit_trace_rejects_a_duplicate_case_id_before_writing() -> None:
    repository = _RecordingRepository()
    repository.existing_case_ids = {"TMP-UNIT-DUP"}
    fake_session = cast(Session, _FakeSession())

    with pytest.raises(TraceAlreadyRecordedError):
        submit_trace(_routine_submission("TMP-UNIT-DUP"), fake_session, repository=repository)

    assert repository.case is None
    assert repository.decision is None
    assert repository.events == []


def test_read_trace_returns_events_sorted_by_sequence() -> None:
    repository = _RecordingRepository()
    fake_session = cast(Session, _FakeSession())
    case = _snapshot_graph()
    first = UUID(int=10)
    second = UUID(int=20)
    case.events = [
        _event(3, "DECISION_RECORDED", second),
        _event(1, "CASE_RECEIVED", None),
        _event(2, "CASE_NORMALIZED", first),
    ]
    repository.returned_trace = case

    result = read_trace(case.trace_id, fake_session, repository=repository)

    assert [event.sequence_number for event in result.events] == [1, 2, 3]
    assert [event.action for event in result.events] == [
        "CASE_RECEIVED",
        "CASE_NORMALIZED",
        "DECISION_RECORDED",
    ]
    assert result.decision.outcome == "AUTO_APPROVED"
    assert result.facts_used == {"purpose": "Synthetic allowed expense"}


def test_read_trace_raises_when_no_trace_exists() -> None:
    repository = _RecordingRepository()
    fake_session = cast(Session, _FakeSession())

    with pytest.raises(TraceNotFoundError):
        read_trace(UUID(int=404), fake_session, repository=repository)
