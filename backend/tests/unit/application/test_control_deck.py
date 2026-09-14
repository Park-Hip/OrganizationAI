"""Unit tests for the temporary Control Deck service (no database)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.api.schemas.temporary_history import TraceReadModel
from app.application.control_deck import (
    ControlIdempotencyConflictError,
    IllegalControlActionError,
    command_fingerprint,
    submit_control,
)
from app.application.temporary_history import TraceNotFoundError
from app.domain.control import ControlCommand, DemoDisposition
from app.persistence.models.temporary_history import (
    TemporaryAuditEvent,
    TemporaryCaseSnapshot,
    TemporaryDecisionSnapshot,
)
from app.persistence.repositories.temporary_history import TemporaryHistoryRepository

_FIXED_NOW = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
_TRACE_ID = UUID(int=1)


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


class _RecordingControlRepository(TemporaryHistoryRepository):
    def __init__(self, case: TemporaryCaseSnapshot | None) -> None:
        self.case = case
        self.receipts: dict[str, TemporaryAuditEvent] = {}
        self.appended: list[TemporaryAuditEvent] = []

    def find_trace_for_update(
        self, session: Session, trace_id: UUID
    ) -> TemporaryCaseSnapshot | None:
        return self.case

    def find_control_receipt(
        self, session: Session, trace_id: UUID, idempotency_key: str
    ) -> TemporaryAuditEvent | None:
        return self.receipts.get(idempotency_key)

    def add_control_event(self, session: Session, event: TemporaryAuditEvent) -> None:
        self.appended.append(event)


def _system_event(sequence: int, action: str, previous: UUID | None) -> TemporaryAuditEvent:
    return TemporaryAuditEvent(
        event_id=UUID(int=10 + sequence),
        trace_id=_TRACE_ID,
        sequence_number=sequence,
        previous_event_id=previous,
        actor_type="SYSTEM",
        action=action,
        payload={"case_id": "TMP-CTRL-01"},
        recorded_at=_FIXED_NOW,
    )


def _stored_case(outcome: str = "OUT_OF_POLICY") -> TemporaryCaseSnapshot:
    case = TemporaryCaseSnapshot(
        trace_id=_TRACE_ID,
        case_id="TMP-CTRL-01",
        recorded_at=_FIXED_NOW,
        submission_snapshot={"case_id": "TMP-CTRL-01"},
        normalized_snapshot={"purpose": "Synthetic out-of-policy expense"},
        profile_id="TMP-DEV-001",
        profile_source="TEMPORARY_DEVELOPMENT",
        data_class="SYNTHETIC",
        workflow_validation_status="UNVALIDATED",
    )
    case.decision = TemporaryDecisionSnapshot(
        decision_id=UUID(int=2),
        trace_id=_TRACE_ID,
        profile_snapshot={"profile_id": "TMP-DEV-001"},
        profile_id="TMP-DEV-001",
        outcome=outcome,
        applied_rule_id="TMP-CAT-01",
        reason="Synthetic out-of-policy expense.",
        question="Do you authorize this temporary exception?",
        decided_at=_FIXED_NOW,
    )
    first = _system_event(1, "CASE_RECEIVED", None)
    second = _system_event(2, "CASE_NORMALIZED", first.event_id)
    third = _system_event(3, "DECISION_RECORDED", second.event_id)
    case.events = [first, second, third]
    return case


def _submit(
    case: TemporaryCaseSnapshot,
    command: ControlCommand,
    *,
    reason: str = "synthetic control reason",
    disposition: DemoDisposition | None = None,
    idempotency_key: str | None = None,
) -> tuple[TemporaryAuditEvent, TraceReadModel]:
    """Run submit_control and return (appended event, result)."""
    repository = _RecordingControlRepository(case)
    session = cast(Session, _FakeSession())
    result = submit_control(
        case.trace_id,
        command,
        session,
        reason=reason,
        disposition=disposition,
        idempotency_key=idempotency_key,
        repository=repository,
        clock=lambda: _FIXED_NOW,
        id_factory=lambda: UUID(int=99),
    )
    return repository.appended[0], result


def test_pause_appends_one_event_and_returns_paused_state() -> None:
    case = _stored_case("OUT_OF_POLICY")
    event, result = _submit(case, ControlCommand.PAUSE, reason="pause for review")

    assert event.actor_type == "DEMO_REVIEWER"
    assert event.action == "CASE_PAUSED"
    assert event.sequence_number == 4
    assert event.previous_event_id == case.events[2].event_id
    assert event.payload["reason"] == "pause for review"
    assert event.payload["prior_state"] == "AWAITING_REVIEW"
    assert result.control_state == "PAUSED"
    assert [e.action for e in result.events] == [
        "CASE_RECEIVED",
        "CASE_NORMALIZED",
        "DECISION_RECORDED",
        "CASE_PAUSED",
    ]


def test_idempotent_retry_returns_saved_result_without_appending() -> None:
    case = _stored_case("OUT_OF_POLICY")
    repository = _RecordingControlRepository(case)
    key = "control-key-1"
    receipt = TemporaryAuditEvent(
        event_id=UUID(int=99),
        trace_id=case.trace_id,
        sequence_number=4,
        previous_event_id=case.events[2].event_id,
        actor_type="DEMO_REVIEWER",
        action="CASE_PAUSED",
        payload={"reason": "pause for review", "prior_state": "AWAITING_REVIEW"},
        recorded_at=_FIXED_NOW,
        idempotency_key=key,
        command_fingerprint=command_fingerprint(
            case.trace_id, ControlCommand.PAUSE, "pause for review", None
        ),
    )
    repository.receipts[key] = receipt
    case.events.append(receipt)
    session = cast(Session, _FakeSession())

    result = submit_control(
        case.trace_id,
        ControlCommand.PAUSE,
        session,
        reason="pause for review",
        idempotency_key=key,
        repository=repository,
        clock=lambda: _FIXED_NOW,
        id_factory=lambda: UUID(int=99),
    )

    assert repository.appended == []
    assert result.control_state == "PAUSED"  # replay reflects the stored receipt chain


def test_idempotency_key_reuse_with_different_command_raises_conflict() -> None:
    case = _stored_case("OUT_OF_POLICY")
    repository = _RecordingControlRepository(case)
    key = "control-key-2"
    repository.receipts[key] = TemporaryAuditEvent(
        event_id=UUID(int=99),
        trace_id=case.trace_id,
        sequence_number=4,
        previous_event_id=case.events[2].event_id,
        actor_type="DEMO_REVIEWER",
        action="CASE_PAUSED",
        payload={"reason": "other reason", "prior_state": "AWAITING_REVIEW"},
        recorded_at=_FIXED_NOW,
        idempotency_key=key,
        command_fingerprint="a-different-fingerprint",
    )
    session = cast(Session, _FakeSession())

    with pytest.raises(ControlIdempotencyConflictError):
        submit_control(
            case.trace_id,
            ControlCommand.PAUSE,
            session,
            reason="pause for review",
            idempotency_key=key,
            repository=repository,
            clock=lambda: _FIXED_NOW,
            id_factory=lambda: UUID(int=99),
        )

    assert repository.appended == []


def test_illegal_transition_raises_a_typed_conflict() -> None:
    case = _stored_case("AUTO_APPROVED")
    repository = _RecordingControlRepository(case)
    session = cast(Session, _FakeSession())

    with pytest.raises(IllegalControlActionError) as exc_info:
        submit_control(
            case.trace_id,
            ControlCommand.PAUSE,
            session,
            reason="synthetic reason",
            repository=repository,
            clock=lambda: _FIXED_NOW,
            id_factory=lambda: UUID(int=99),
        )

    assert exc_info.value.state == "AUTO_APPROVED"
    assert repository.appended == []


def test_unknown_trace_raises_not_found() -> None:
    repository = _RecordingControlRepository(None)
    session = cast(Session, _FakeSession())

    with pytest.raises(TraceNotFoundError):
        submit_control(
            _TRACE_ID,
            ControlCommand.PAUSE,
            session,
            reason="synthetic reason",
            repository=repository,
            clock=lambda: _FIXED_NOW,
            id_factory=lambda: UUID(int=99),
        )


def test_command_fingerprint_is_deterministic_and_orders_independently() -> None:
    args = (_TRACE_ID, ControlCommand.RECORD_DEMO_REVIEW, "synthetic reason", None)
    assert command_fingerprint(*args) == command_fingerprint(*args)
    assert command_fingerprint(*args) != command_fingerprint(
        _TRACE_ID, ControlCommand.PAUSE, "synthetic reason", None
    )
