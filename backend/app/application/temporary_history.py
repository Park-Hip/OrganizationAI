"""Application service that composes the pure decision path with persistence.

The write path records one immutable temporary trace in a single transaction.
The read path reconstructs a stored trace from snapshots without calling the
normalizer or evaluator, so a historical decision never changes under future
code.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas.temporary_history import (
    AuditEventReadModel,
    DecisionReadModel,
    ProvenanceReadModel,
    TraceReadModel,
)
from app.domain.models import CaseSubmission
from app.persistence.models.temporary_history import (
    AuditAction,
    AuditActorType,
    TemporaryAuditEvent,
    TemporaryCaseSnapshot,
    TemporaryDecisionSnapshot,
)
from app.persistence.repositories.temporary_history import TemporaryHistoryRepository
from app.policy.evaluator import evaluate_case
from app.policy.normalization import normalize_case
from app.policy.profile import TMP_DEV_001_PROFILE

TEMPORARY_NOTICE = "Temporary synthetic development record; workflow is unvalidated."

_Clock = Callable[[], datetime]
_IdFactory = Callable[[], UUID]

_FIRST_EVENT_SEQUENCE = 1
_NORMALIZED_EVENT_SEQUENCE = 2
_DECISION_EVENT_SEQUENCE = 3


class TraceAlreadyRecordedError(Exception):
    """A synthetic trace already exists for the submitted client case ID."""

    def __init__(self, case_id: str) -> None:
        super().__init__(f"a temporary trace already exists for case_id {case_id!r}")
        self.case_id = case_id


class TraceNotFoundError(Exception):
    """No stored trace exists for the requested server trace ID."""

    def __init__(self, trace_id: UUID) -> None:
        super().__init__(f"no temporary trace exists for trace_id {trace_id!r}")
        self.trace_id = trace_id


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> UUID:
    return uuid4()


def _submission_snapshot(submission: CaseSubmission) -> dict[str, object]:
    return submission.model_dump(mode="json")


def _build_events(
    trace_id: UUID,
    case_id: str,
    outcome: str,
    applied_rule_id: str,
    clock: _Clock,
    id_factory: _IdFactory,
) -> list[TemporaryAuditEvent]:
    received_event = TemporaryAuditEvent(
        event_id=id_factory(),
        trace_id=trace_id,
        sequence_number=_FIRST_EVENT_SEQUENCE,
        previous_event_id=None,
        actor_type=AuditActorType.SYSTEM.value,
        action=AuditAction.CASE_RECEIVED.value,
        payload={"case_id": case_id},
        recorded_at=clock(),
    )
    normalized_event = TemporaryAuditEvent(
        event_id=id_factory(),
        trace_id=trace_id,
        sequence_number=_NORMALIZED_EVENT_SEQUENCE,
        previous_event_id=received_event.event_id,
        actor_type=AuditActorType.SYSTEM.value,
        action=AuditAction.CASE_NORMALIZED.value,
        payload={"case_id": case_id},
        recorded_at=clock(),
    )
    decided_event = TemporaryAuditEvent(
        event_id=id_factory(),
        trace_id=trace_id,
        sequence_number=_DECISION_EVENT_SEQUENCE,
        previous_event_id=normalized_event.event_id,
        actor_type=AuditActorType.SYSTEM.value,
        action=AuditAction.DECISION_RECORDED.value,
        payload={"outcome": outcome, "applied_rule_id": applied_rule_id},
        recorded_at=clock(),
    )
    return [received_event, normalized_event, decided_event]


def _is_duplicate_case_id(error: IntegrityError) -> bool:
    """Return whether a PostgreSQL integrity error is the duplicate-case constraint."""
    diag = getattr(getattr(error, "orig", None), "diag", None)
    constraint_name = getattr(diag, "constraint_name", "")
    if constraint_name:
        return constraint_name == "uq_temporary_case_snapshots_case_id"
    return "uq_temporary_case_snapshots_case_id" in str(error)


def _to_trace_model(case: TemporaryCaseSnapshot) -> TraceReadModel:
    decision = case.decision
    assert decision is not None, "a stored temporary trace never lacks a decision snapshot"
    provenance = ProvenanceReadModel(
        profile_id=case.profile_id,
        profile_source=case.profile_source,
        data_class=case.data_class,
        workflow_validation_status=case.workflow_validation_status,
    )
    events = [
        AuditEventReadModel(
            event_id=event.event_id,
            sequence_number=event.sequence_number,
            previous_event_id=event.previous_event_id,
            actor_type=event.actor_type,
            action=event.action,
            payload=event.payload,
            recorded_at=event.recorded_at,
        )
        for event in sorted(case.events, key=lambda item: item.sequence_number)
    ]
    return TraceReadModel(
        temporary_notice=TEMPORARY_NOTICE,
        trace_id=case.trace_id,
        recorded_at=case.recorded_at,
        provenance=provenance,
        submission=case.submission_snapshot,
        facts_used=case.normalized_snapshot,
        decision=DecisionReadModel(
            outcome=decision.outcome,
            applied_rule_id=decision.applied_rule_id,
            reason=decision.reason,
            question=decision.question,
            profile_id=decision.profile_id,
            profile_snapshot=decision.profile_snapshot,
            decided_at=decision.decided_at,
        ),
        events=events,
    )


_DEFAULT_REPOSITORY = TemporaryHistoryRepository()


def submit_trace(
    submission: CaseSubmission,
    session: Session,
    *,
    repository: TemporaryHistoryRepository = _DEFAULT_REPOSITORY,
    clock: _Clock = _utc_now,
    id_factory: _IdFactory = _new_uuid,
) -> TraceReadModel:
    """Normalize, evaluate, persist, and return one complete temporary trace.

    The caller is responsible for structural validation. The existing pure
    normalizer and evaluator are invoked exactly once; the completed history is
    written in one transaction so a failure leaves no partial record.
    """
    profile = TMP_DEV_001_PROFILE
    now = clock()
    trace_id = id_factory()

    normalized = normalize_case(submission)
    draft = evaluate_case(normalized, profile)

    case_row = TemporaryCaseSnapshot(
        trace_id=trace_id,
        case_id=submission.case_id,
        recorded_at=now,
        submission_snapshot=_submission_snapshot(submission),
        normalized_snapshot=normalized.model_dump(mode="json"),
        profile_id=profile.profile_id,
        profile_source=profile.profile_source.value,
        data_class=profile.data_class.value,
        workflow_validation_status=profile.workflow_validation_status.value,
    )
    decision_row = TemporaryDecisionSnapshot(
        decision_id=id_factory(),
        trace_id=trace_id,
        profile_snapshot=profile.model_dump(mode="json"),
        profile_id=draft.profile_id,
        outcome=draft.outcome.value,
        applied_rule_id=draft.applied_rule_id.value,
        reason=draft.reason,
        question=draft.question,
        decided_at=now,
    )
    events = _build_events(
        trace_id=trace_id,
        case_id=submission.case_id,
        outcome=draft.outcome.value,
        applied_rule_id=draft.applied_rule_id.value,
        clock=clock,
        id_factory=id_factory,
    )

    try:
        with session.begin():
            if repository.case_id_exists(session, submission.case_id):
                raise TraceAlreadyRecordedError(submission.case_id)
            repository.add_trace(session, case_row, decision_row, events)
            session.flush()
    except IntegrityError as error:
        if _is_duplicate_case_id(error):
            raise TraceAlreadyRecordedError(submission.case_id) from error
        raise

    stored = repository.find_trace(session, trace_id)
    if stored is None:
        raise TraceNotFoundError(trace_id)
    return _to_trace_model(stored)


def read_trace(
    trace_id: UUID,
    session: Session,
    *,
    repository: TemporaryHistoryRepository = _DEFAULT_REPOSITORY,
) -> TraceReadModel:
    """Return a stored trace from its snapshots without reevaluating the decision."""
    stored = repository.find_trace(session, trace_id)
    if stored is None:
        raise TraceNotFoundError(trace_id)
    return _to_trace_model(stored)
