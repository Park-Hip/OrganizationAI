"""Pure Control Deck state kernel for the temporary synthetic traces.

This module defines the temporary control vocabulary - commands, actions,
actors, dispositions, and derived states - plus a deterministic projection from
the original decision and the append-only control events into one visible
control state. It also plans exactly one control event for a legal transition.

It is intentionally pure: no FastAPI, SQLAlchemy, settings, clock, network,
filesystem, or evaluator dependency. The frozen Layer 0 vocabulary in
``app.domain.enums`` is not extended; this vocabulary is separate and temporary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.domain.enums import DecisionOutcome


class ControlState(str, Enum):  # noqa: UP042
    """Derived, visible control states for one stored temporary trace."""

    AUTO_APPROVED = "AUTO_APPROVED"
    AWAITING_INPUT = "AWAITING_INPUT"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    PAUSED = "PAUSED"
    DEMO_REVIEWED = "DEMO_REVIEWED"


class ControlCommand(str, Enum):  # noqa: UP042
    """Client-facing control commands, all demonstrably synthetic."""

    PAUSE = "pause"
    RESUME = "resume"
    RECORD_DEMO_REVIEW = "record_demo_review"
    UNDO = "undo"


class ControlAction(str, Enum):  # noqa: UP042
    """Append-only control event actions recorded for one trace."""

    CASE_PAUSED = "CASE_PAUSED"
    CASE_RESUMED = "CASE_RESUMED"
    DEMO_REVIEW_RECORDED = "DEMO_REVIEW_RECORDED"
    CONTROL_COMPENSATED = "CONTROL_COMPENSATED"


class ControlActor(str, Enum):  # noqa: UP042
    """The only actor allowed to append control events, a fixed synthetic label."""

    DEMO_REVIEWER = "DEMO_REVIEWER"


class DemoDisposition(str, Enum):  # noqa: UP042
    """Bounded synthetic review disposition; not a real approval decision."""

    DEMO_ALLOW = "DEMO_ALLOW"
    DEMO_DECLINE = "DEMO_DECLINE"


@dataclass(frozen=True)
class StoredAuditEvent:
    """Plain value view of one stored audit event for pure projection.

    ``action`` is the raw persisted action string. Non-control actions are
    ignored by the reducer, so callers may pass the complete event chain
    including the initial ``SYSTEM`` events.
    """

    event_id: UUID
    sequence_number: int
    action: str
    payload: Mapping[str, object]


@dataclass(frozen=True)
class ActiveControlEvent:
    """One currently reversible control event and the state it replaced."""

    event_id: UUID
    action: ControlAction
    prior_state: ControlState


@dataclass(frozen=True)
class ControlProjection:
    """The deterministic derived control state for one trace."""

    state: ControlState
    active: tuple[ActiveControlEvent, ...]

    @property
    def latest_reversible(self) -> ActiveControlEvent | None:
        """Return the latest still-active pause or review event, if any."""
        return self.active[-1] if self.active else None


@dataclass(frozen=True)
class PlannedControlEvent:
    """One validated control event ready to append, produced by the guard."""

    action: ControlAction
    actor: ControlActor
    prior_state: ControlState
    target_event_id: UUID | None
    payload: dict[str, object]


class IllegalControlTransition(ValueError):
    """A command is not legal for the trace's current derived control state."""

    def __init__(self, state: ControlState, command: ControlCommand, detail: str) -> None:
        super().__init__(f"command {command.value!r} is illegal in state {state.value!r}: {detail}")
        self.state = state
        self.command = command
        self.detail = detail


def base_control_state(outcome: DecisionOutcome) -> ControlState:
    """Map one original decision outcome to its initial derived control state."""
    if outcome is DecisionOutcome.AUTO_APPROVED:
        return ControlState.AUTO_APPROVED
    if outcome is DecisionOutcome.MISSING_FACT:
        return ControlState.AWAITING_INPUT
    if outcome in (DecisionOutcome.OUT_OF_POLICY, DecisionOutcome.AUTHORITY_EXCEEDED):
        return ControlState.AWAITING_REVIEW
    raise ValueError(f"unknown decision outcome {outcome.value!r}")


def _as_control_action(action: str) -> ControlAction | None:
    try:
        return ControlAction(action)
    except ValueError:
        return None


def reduce_control_state(
    outcome: DecisionOutcome,
    events: Sequence[StoredAuditEvent],
) -> ControlProjection:
    """Replay the stored control events and return the derived projection.

    The reducer is a pure fold: the initial state comes from the original
    decision outcome, then each control action updates the state and the stack
    of currently reversible pause/review events. ``SYSTEM`` events are ignored.
    """
    state = base_control_state(outcome)
    active: list[ActiveControlEvent] = []
    for event in sorted(events, key=lambda item: item.sequence_number):
        action = _as_control_action(event.action)
        if action is None:
            continue
        if action is ControlAction.CASE_PAUSED:
            active.append(ActiveControlEvent(event.event_id, action, state))
            state = ControlState.PAUSED
        elif action is ControlAction.DEMO_REVIEW_RECORDED:
            active.append(ActiveControlEvent(event.event_id, action, state))
            state = ControlState.DEMO_REVIEWED
        elif action is ControlAction.CASE_RESUMED:
            if not active or active[-1].action is not ControlAction.CASE_PAUSED:
                raise ValueError("stored trace has CASE_RESUMED with no active pause to restore")
            state = active[-1].prior_state
            active.pop()
        elif action is ControlAction.CONTROL_COMPENSATED:
            if not active:
                raise ValueError(
                    "stored trace has CONTROL_COMPENSATED with no active control event"
                )
            state = active[-1].prior_state
            active.pop()
    return ControlProjection(state=state, active=tuple(active))


def derive_control_state(
    outcome: DecisionOutcome,
    events: Sequence[StoredAuditEvent],
) -> ControlState:
    """Return only the derived state for a stored trace."""
    return reduce_control_state(outcome, events).state


def _require_reason(reason: str) -> None:
    if not reason.strip():
        raise ValueError("control command reason must not be blank")


def _require_state(
    state: ControlState,
    allowed: set[ControlState],
    command: ControlCommand,
) -> None:
    if state not in allowed:
        expected = " or ".join(sorted(member.value for member in allowed))
        raise IllegalControlTransition(state, command, f"expected state {expected}")


def plan_control_command(
    projection: ControlProjection,
    command: ControlCommand,
    *,
    reason: str,
    disposition: DemoDisposition | None = None,
) -> PlannedControlEvent:
    """Return one event draft for a legal command, or raise for an illegal one.

    The guard validates only the transition legality and computes the derived
    payload fields (``prior_state`` and any target linkage). Structural input
    validation such as a non-blank reason or a required disposition belongs to
    the transport layer; the guard still defensively rejects a blank reason.
    """
    _require_reason(reason)
    state = projection.state
    latest = projection.latest_reversible

    if command is ControlCommand.PAUSE:
        _require_state(
            state,
            {ControlState.AWAITING_INPUT, ControlState.AWAITING_REVIEW},
            command,
        )
        return PlannedControlEvent(
            action=ControlAction.CASE_PAUSED,
            actor=ControlActor.DEMO_REVIEWER,
            prior_state=state,
            target_event_id=None,
            payload={"reason": reason, "prior_state": state.value},
        )

    if command is ControlCommand.RESUME:
        _require_state(state, {ControlState.PAUSED}, command)
        if latest is None or latest.action is not ControlAction.CASE_PAUSED:
            raise IllegalControlTransition(state, command, "no active pause to resume")
        return PlannedControlEvent(
            action=ControlAction.CASE_RESUMED,
            actor=ControlActor.DEMO_REVIEWER,
            prior_state=latest.prior_state,
            target_event_id=latest.event_id,
            payload={
                "reason": reason,
                "prior_state": latest.prior_state.value,
                "resumed_event_id": str(latest.event_id),
            },
        )

    if command is ControlCommand.RECORD_DEMO_REVIEW:
        _require_state(state, {ControlState.AWAITING_REVIEW}, command)
        if disposition is None:
            raise ValueError("record_demo_review requires a demo disposition")
        return PlannedControlEvent(
            action=ControlAction.DEMO_REVIEW_RECORDED,
            actor=ControlActor.DEMO_REVIEWER,
            prior_state=state,
            target_event_id=None,
            payload={
                "reason": reason,
                "disposition": disposition.value,
                "prior_state": state.value,
            },
        )

    if command is ControlCommand.UNDO:
        if latest is None:
            raise IllegalControlTransition(state, command, "no reversible control event")
        _require_state(state, {ControlState.PAUSED, ControlState.DEMO_REVIEWED}, command)
        return PlannedControlEvent(
            action=ControlAction.CONTROL_COMPENSATED,
            actor=ControlActor.DEMO_REVIEWER,
            prior_state=latest.prior_state,
            target_event_id=latest.event_id,
            payload={
                "reason": reason,
                "target_event_id": str(latest.event_id),
                "prior_state": latest.prior_state.value,
            },
        )

    raise IllegalControlTransition(state, command, "unknown command")
