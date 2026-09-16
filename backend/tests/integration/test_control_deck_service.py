"""Database integration tests for the temporary Control Deck service."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.control_deck import (
    ControlIdempotencyConflictError,
    IllegalControlActionError,
    submit_control,
)
from app.application.temporary_history import read_trace, submit_trace
from app.domain.control import ControlCommand, DemoDisposition
from app.domain.enums import EvidenceStatus, TemporaryCategory
from app.domain.models import CaseSubmission, Expense
from app.persistence.models.temporary_history import TemporaryAuditEvent
from app.persistence.repositories.temporary_history import TemporaryHistoryRepository

pytestmark = pytest.mark.integration

pytest_plugins = ["_db_utils"]


def _authority_submission(case_id: str = "TMP-CTRL-AUTH") -> CaseSubmission:
    return CaseSubmission(
        case_id=case_id,
        submitted_at=datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC),
        requester_role="TEST_REQUESTER",
        purpose="Synthetic authority escalation",
        expense=Expense(
            category=TemporaryCategory.TEST_ALLOWED,
            description="Synthetic materials line",
            amount_vnd=2000,
            expense_date=date(2030, 1, 1),
            evidence_status=EvidenceStatus.PRESENT,
        ),
    )


def _out_of_policy_submission(case_id: str = "TMP-CTRL-OOP") -> CaseSubmission:
    return CaseSubmission(
        case_id=case_id,
        submitted_at=datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC),
        requester_role="TEST_REQUESTER",
        purpose="Synthetic out-of-policy expense",
        expense=Expense(
            category=TemporaryCategory.TEST_BLOCKED,
            description="Synthetic blocked line",
            amount_vnd=500,
            expense_date=date(2030, 1, 1),
            evidence_status=EvidenceStatus.PRESENT,
        ),
    )


def _missing_fact_submission(case_id: str = "TMP-CTRL-MISS") -> CaseSubmission:
    return CaseSubmission(
        case_id=case_id,
        submitted_at=datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC),
        requester_role=None,
        purpose=None,
        expense=None,
    )


def _event_count(session: Session, trace_id: UUID, action: str | None = None) -> int:
    statement = (
        select(func.count())
        .select_from(TemporaryAuditEvent)
        .where(TemporaryAuditEvent.trace_id == trace_id)
    )
    if action is not None:
        statement = statement.where(TemporaryAuditEvent.action == action)
    return session.scalar(statement) or 0


def test_pause_and_resume_an_authority_escalation(session: Session) -> None:
    trace = submit_trace(_authority_submission(), session)
    assert trace.control_state == "AWAITING_REVIEW"

    paused = submit_control(trace.trace_id, ControlCommand.PAUSE, session, reason="hold for review")

    assert paused.control_state == "PAUSED"
    pause_event = next(event for event in paused.events if event.action == "CASE_PAUSED")
    assert pause_event.actor_type == "DEMO_REVIEWER"
    assert pause_event.payload["reason"] == "hold for review"
    assert pause_event.payload["prior_state"] == "AWAITING_REVIEW"

    resumed = submit_control(
        trace.trace_id, ControlCommand.RESUME, session, reason="review complete"
    )

    assert resumed.control_state == "AWAITING_REVIEW"
    assert [event.action for event in resumed.events] == [
        "CASE_RECEIVED",
        "CASE_NORMALIZED",
        "DECISION_RECORDED",
        "CASE_PAUSED",
        "CASE_RESUMED",
    ]
    # The original decision snapshot never changes.
    assert resumed.decision.outcome == "AUTHORITY_EXCEEDED"
    assert resumed.decision == trace.decision
    assert resumed.facts_used == trace.facts_used


def test_record_demo_review_then_undo_restores_the_prior_state(session: Session) -> None:
    trace = submit_trace(_out_of_policy_submission(), session)

    reviewed = submit_control(
        trace.trace_id,
        ControlCommand.RECORD_DEMO_REVIEW,
        session,
        reason="synthetic decline",
        disposition=DemoDisposition.DEMO_DECLINE,
    )

    assert reviewed.control_state == "DEMO_REVIEWED"
    review_event = next(
        event for event in reviewed.events if event.action == "DEMO_REVIEW_RECORDED"
    )
    assert review_event.payload["disposition"] == "DEMO_DECLINE"

    undone = submit_control(
        trace.trace_id, ControlCommand.UNDO, session, reason="compensate review"
    )

    assert undone.control_state == "AWAITING_REVIEW"
    compensation = next(event for event in undone.events if event.action == "CONTROL_COMPENSATED")
    assert compensation.payload["target_event_id"] == str(review_event.event_id)
    assert compensation.payload["prior_state"] == "AWAITING_REVIEW"


def test_pause_and_resume_a_missing_fact_escalation(session: Session) -> None:
    trace = submit_trace(_missing_fact_submission(), session)
    assert trace.control_state == "AWAITING_INPUT"

    paused = submit_control(trace.trace_id, ControlCommand.PAUSE, session, reason="parked")
    assert paused.control_state == "PAUSED"

    resumed = submit_control(trace.trace_id, ControlCommand.RESUME, session, reason="resume")
    assert resumed.control_state == "AWAITING_INPUT"


def test_read_trace_reports_the_derived_control_state(session: Session) -> None:
    trace = submit_trace(_out_of_policy_submission(), session)
    submit_control(trace.trace_id, ControlCommand.PAUSE, session, reason="pause for read")

    retrieved = read_trace(trace.trace_id, session)

    assert retrieved.control_state == "PAUSED"


def test_demo_review_is_rejected_for_a_missing_fact(session: Session) -> None:
    trace = submit_trace(_missing_fact_submission(), session)

    with pytest.raises(IllegalControlActionError):
        submit_control(
            trace.trace_id,
            ControlCommand.RECORD_DEMO_REVIEW,
            session,
            reason="synthetic review",
            disposition=DemoDisposition.DEMO_ALLOW,
        )

    assert _event_count(session, trace.trace_id) == 3


def test_idempotent_retry_creates_one_effect(session: Session) -> None:
    trace = submit_trace(_out_of_policy_submission(), session)
    key = "pause-key-1"

    first = submit_control(
        trace.trace_id, ControlCommand.PAUSE, session, reason="pause once", idempotency_key=key
    )
    replayed = submit_control(
        trace.trace_id, ControlCommand.PAUSE, session, reason="pause once", idempotency_key=key
    )

    assert first.control_state == "PAUSED"
    assert replayed.control_state == "PAUSED"
    assert _event_count(session, trace.trace_id, "CASE_PAUSED") == 1


def test_same_key_with_a_different_command_is_a_conflict(session: Session) -> None:
    trace = submit_trace(_out_of_policy_submission(), session)
    key = "pause-key-2"

    submit_control(
        trace.trace_id, ControlCommand.PAUSE, session, reason="first reason", idempotency_key=key
    )

    with pytest.raises(ControlIdempotencyConflictError):
        submit_control(
            trace.trace_id,
            ControlCommand.PAUSE,
            session,
            reason="a different reason",
            idempotency_key=key,
        )

    assert _event_count(session, trace.trace_id, "CASE_PAUSED") == 1


def test_sequence_numbers_stay_contiguous_across_a_demo_chain(session: Session) -> None:
    trace = submit_trace(_authority_submission(), session)

    submit_control(trace.trace_id, ControlCommand.PAUSE, session, reason="pause")
    submit_control(trace.trace_id, ControlCommand.RESUME, session, reason="resume")
    submit_control(
        trace.trace_id,
        ControlCommand.RECORD_DEMO_REVIEW,
        session,
        reason="review",
        disposition=DemoDisposition.DEMO_ALLOW,
    )
    final = submit_control(trace.trace_id, ControlCommand.UNDO, session, reason="undo")

    assert [event.sequence_number for event in final.events] == [1, 2, 3, 4, 5, 6, 7]
    assert final.control_state == "AWAITING_REVIEW"


class _FailAfterControlWrite(TemporaryHistoryRepository):
    def add_control_event(self, session: Session, event: TemporaryAuditEvent) -> None:
        session.add(event)
        session.flush()
        raise RuntimeError("forced control write failure")


def test_injected_failure_after_event_add_rolls_back(session: Session) -> None:
    trace = submit_trace(_out_of_policy_submission(), session)

    with pytest.raises(RuntimeError, match="forced control write failure"):
        submit_control(
            trace.trace_id,
            ControlCommand.PAUSE,
            session,
            reason="should roll back",
            repository=_FailAfterControlWrite(),
        )

    session.rollback()
    assert _event_count(session, trace.trace_id) == 3
    assert _event_count(session, trace.trace_id, "CASE_PAUSED") == 0


def test_concurrent_commands_allow_exactly_one_winner(
    session: Session, test_session_factory: sessionmaker[Session]
) -> None:
    trace = submit_trace(_out_of_policy_submission(), session)
    barrier = Barrier(2)

    def _submit(command: ControlCommand, reason: str, disposition: DemoDisposition | None) -> None:
        with test_session_factory() as own_session:
            barrier.wait()
            submit_control(
                trace.trace_id,
                command,
                own_session,
                reason=reason,
                disposition=disposition,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_submit, ControlCommand.PAUSE, "pause reason", None),
            pool.submit(
                _submit,
                ControlCommand.RECORD_DEMO_REVIEW,
                "review reason",
                DemoDisposition.DEMO_ALLOW,
            ),
        ]
        outcomes: list[str] = []
        for future in futures:
            try:
                future.result()
                outcomes.append("ok")
            except IllegalControlActionError:
                outcomes.append("conflict")

    assert sorted(outcomes) == ["conflict", "ok"]
    assert _event_count(session, trace.trace_id) == 4
