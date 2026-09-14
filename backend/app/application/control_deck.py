"""Transactional command service for the temporary Control Deck.

The service locks one stored trace, replays the pure reducer, validates the
command, appends exactly one synthetic control event, and returns the derived
trace view. It never calls the normalizer or evaluator and never mutates an
existing snapshot or event.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas.temporary_history import TraceReadModel
from app.application.temporary_history import TraceNotFoundError, _to_trace_model
from app.domain.control import (
    ControlCommand,
    DemoDisposition,
    IllegalControlTransition,
    StoredAuditEvent,
    plan_control_command,
    reduce_control_state,
)
from app.domain.enums import DecisionOutcome
from app.persistence.models.temporary_history import TemporaryAuditEvent, TemporaryCaseSnapshot
from app.persistence.repositories.temporary_history import TemporaryHistoryRepository

_Clock = Callable[[], datetime]
_IdFactory = Callable[[], UUID]


class IllegalControlActionError(Exception):
    """A command is not legal for the trace's current derived control state."""

    def __init__(self, trace_id: UUID, state: str, command: str, detail: str) -> None:
        super().__init__(
            f"control command {command!r} is illegal for trace {trace_id} "
            f"in state {state!r}: {detail}"
        )
        self.trace_id = trace_id
        self.state = state
        self.command = command
        self.detail = detail


class ControlIdempotencyConflictError(Exception):
    """An idempotency key was reused for a different command on a trace."""

    def __init__(self, trace_id: UUID, idempotency_key: str) -> None:
        super().__init__(
            f"idempotency key {idempotency_key!r} was already used for a different "
            f"command on trace {trace_id}"
        )
        self.trace_id = trace_id
        self.idempotency_key = idempotency_key


def _to_idempotency_result(
    stored: TemporaryCaseSnapshot, receipt: TemporaryAuditEvent
) -> TraceReadModel:
    return _to_trace_model(
        stored,
        source_events=[
            event for event in stored.events if event.sequence_number <= receipt.sequence_number
        ],
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> UUID:
    return uuid4()


def command_fingerprint(
    trace_id: UUID,
    command: ControlCommand,
    reason: str,
    disposition: DemoDisposition | None,
) -> str:
    """Return a canonical fingerprint for one command intent."""
    canonical = json.dumps(
        {
            "trace_id": str(trace_id),
            "command": command.value,
            "reason": reason,
            "disposition": disposition.value if disposition is not None else None,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_idempotency_conflict(error: IntegrityError) -> bool:
    diag = getattr(getattr(error, "orig", None), "diag", None)
    constraint_name = getattr(diag, "constraint_name", "")
    if constraint_name:
        return constraint_name == "uq_temporary_audit_events_trace_idempotency"
    return "uq_temporary_audit_events_trace_idempotency" in str(error)


def _resolve_idempotency_conflict(
    session: Session,
    trace_id: UUID,
    idempotency_key: str,
    fingerprint: str,
    repository: TemporaryHistoryRepository,
) -> TraceReadModel:
    """Replay or reject an idempotency conflict after a concurrent insert lost."""
    with session.begin():
        receipt = repository.find_control_receipt(session, trace_id, idempotency_key)
        if receipt is not None and receipt.command_fingerprint == fingerprint:
            stored = repository.find_trace(session, trace_id)
            if stored is None:
                raise TraceNotFoundError(trace_id)
            return _to_idempotency_result(stored, receipt)
        if receipt is not None:
            raise ControlIdempotencyConflictError(trace_id, idempotency_key)
        # The conflicting row vanished unexpectedly; the caller can retry.
        raise ControlIdempotencyConflictError(trace_id, idempotency_key)


_DEFAULT_REPOSITORY = TemporaryHistoryRepository()


def submit_control(
    trace_id: UUID,
    command: ControlCommand,
    session: Session,
    *,
    reason: str,
    disposition: DemoDisposition | None = None,
    idempotency_key: str | None = None,
    repository: TemporaryHistoryRepository = _DEFAULT_REPOSITORY,
    clock: _Clock = _utc_now,
    id_factory: _IdFactory = _new_uuid,
) -> TraceReadModel:
    """Apply one synthetic control command to a stored trace and return its view.

    Structural validation belongs to the transport layer. The caller passes a
    non-blank ``reason`` and, for ``record_demo_review``, a ``disposition``.
    The whole command runs inside one transaction: lock the trace, replay the
    reducer, plan a legal event, append it, and return the derived view.
    """
    fingerprint = command_fingerprint(trace_id, command, reason, disposition)
    now = clock()

    try:
        with session.begin():
            stored = repository.find_trace_for_update(session, trace_id)
            if stored is None:
                raise TraceNotFoundError(trace_id)
            decision = stored.decision
            assert decision is not None, "a stored temporary trace never lacks a decision snapshot"

            if idempotency_key is not None:
                receipt = repository.find_control_receipt(session, trace_id, idempotency_key)
                if receipt is not None:
                    if receipt.command_fingerprint == fingerprint:
                        return _to_idempotency_result(stored, receipt)
                    raise ControlIdempotencyConflictError(trace_id, idempotency_key)

            projection = reduce_control_state(
                DecisionOutcome(decision.outcome),
                [
                    StoredAuditEvent(
                        event_id=event.event_id,
                        sequence_number=event.sequence_number,
                        action=event.action,
                        payload=event.payload,
                    )
                    for event in stored.events
                ],
            )

            try:
                planned = plan_control_command(
                    projection,
                    command,
                    reason=reason,
                    disposition=disposition,
                )
            except IllegalControlTransition as exc:
                raise IllegalControlActionError(
                    trace_id, projection.state.value, command.value, exc.detail
                ) from exc

            ordered_events = sorted(stored.events, key=lambda item: item.sequence_number)
            next_sequence = max((event.sequence_number for event in ordered_events), default=0) + 1
            previous_event_id = ordered_events[-1].event_id if ordered_events else None

            control_event = TemporaryAuditEvent(
                event_id=id_factory(),
                trace_id=trace_id,
                sequence_number=next_sequence,
                previous_event_id=previous_event_id,
                actor_type=planned.actor.value,
                action=planned.action.value,
                payload=planned.payload,
                recorded_at=now,
                idempotency_key=idempotency_key,
                command_fingerprint=fingerprint if idempotency_key is not None else None,
            )
            control_event.case = stored
            repository.add_control_event(session, control_event)
            session.flush()
            return _to_trace_model(stored)
    except IntegrityError as error:
        if idempotency_key is not None and _is_idempotency_conflict(error):
            return _resolve_idempotency_conflict(
                session, trace_id, idempotency_key, fingerprint, repository
            )
        raise
