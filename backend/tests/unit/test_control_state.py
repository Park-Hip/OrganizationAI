"""Unit tests for the pure Control Deck state kernel."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.domain.control import (
    ControlAction,
    ControlActor,
    ControlCommand,
    ControlProjection,
    ControlState,
    DemoDisposition,
    IllegalControlTransition,
    PlannedControlEvent,
    StoredAuditEvent,
    base_control_state,
    derive_control_state,
    plan_control_command,
    reduce_control_state,
)
from app.domain.enums import DecisionOutcome

pytestmark = pytest.mark.unit


def _event(
    sequence: int, action: str, payload: dict[str, object] | None = None
) -> StoredAuditEvent:
    return StoredAuditEvent(
        event_id=UUID(int=sequence),
        sequence_number=sequence,
        action=action,
        payload=payload if payload is not None else {},
    )


def _project(outcome: DecisionOutcome, *actions: str) -> ControlProjection:
    events = [_event(index, action) for index, action in enumerate(actions, start=1)]
    return reduce_control_state(outcome, events)


def _plan(
    outcome: DecisionOutcome,
    actions: tuple[str, ...],
    command: ControlCommand,
    *,
    disposition: DemoDisposition | None = None,
) -> PlannedControlEvent:
    return plan_control_command(
        _project(outcome, *actions),
        command,
        reason="synthetic reason",
        disposition=disposition,
    )


# ---------------------------------------------------------------------------
# Base states
# ---------------------------------------------------------------------------


def test_base_control_state_maps_every_decision_outcome() -> None:
    assert base_control_state(DecisionOutcome.AUTO_APPROVED) is ControlState.AUTO_APPROVED
    assert base_control_state(DecisionOutcome.MISSING_FACT) is ControlState.AWAITING_INPUT
    assert base_control_state(DecisionOutcome.OUT_OF_POLICY) is ControlState.AWAITING_REVIEW
    assert base_control_state(DecisionOutcome.AUTHORITY_EXCEEDED) is ControlState.AWAITING_REVIEW


def test_system_events_do_not_change_the_derived_state() -> None:
    events = [
        _event(1, "CASE_RECEIVED"),
        _event(2, "CASE_NORMALIZED"),
        _event(3, "DECISION_RECORDED"),
    ]
    assert (
        derive_control_state(DecisionOutcome.OUT_OF_POLICY, events) is ControlState.AWAITING_REVIEW
    )


# ---------------------------------------------------------------------------
# Pause
# ---------------------------------------------------------------------------


def test_pause_is_legal_from_awaiting_input() -> None:
    planned = _plan(DecisionOutcome.MISSING_FACT, (), ControlCommand.PAUSE)

    assert planned.action is ControlAction.CASE_PAUSED
    assert planned.actor is ControlActor.DEMO_REVIEWER
    assert planned.prior_state is ControlState.AWAITING_INPUT
    assert planned.target_event_id is None
    assert planned.payload["prior_state"] == "AWAITING_INPUT"


def test_pause_is_legal_from_awaiting_review() -> None:
    planned = _plan(DecisionOutcome.OUT_OF_POLICY, (), ControlCommand.PAUSE)

    assert planned.action is ControlAction.CASE_PAUSED
    assert planned.prior_state is ControlState.AWAITING_REVIEW


@pytest.mark.parametrize(
    ("outcome", "actions", "command", "state"),
    [
        (DecisionOutcome.AUTO_APPROVED, (), ControlCommand.PAUSE, "AUTO_APPROVED"),
        (DecisionOutcome.AUTO_APPROVED, (), ControlCommand.RECORD_DEMO_REVIEW, "AUTO_APPROVED"),
        (DecisionOutcome.MISSING_FACT, ("CASE_PAUSED",), ControlCommand.PAUSE, "PAUSED"),
    ],
)
def test_illegal_commands_raise_for_unsupported_states(
    outcome: DecisionOutcome, actions: tuple[str, ...], command: ControlCommand, state: str
) -> None:
    with pytest.raises(IllegalControlTransition) as exc_info:
        _plan(outcome, actions, command, disposition=DemoDisposition.DEMO_ALLOW)
    assert exc_info.value.state.value == state


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------


def test_resume_restores_the_pause_prior_state() -> None:
    planned = _plan(DecisionOutcome.OUT_OF_POLICY, ("CASE_PAUSED",), ControlCommand.RESUME)

    assert planned.action is ControlAction.CASE_RESUMED
    assert planned.prior_state is ControlState.AWAITING_REVIEW
    assert planned.payload["resumed_event_id"] == str(planned.target_event_id)
    assert planned.payload["prior_state"] == "AWAITING_REVIEW"


def test_resume_is_illegal_when_not_paused() -> None:
    with pytest.raises(IllegalControlTransition):
        _plan(DecisionOutcome.OUT_OF_POLICY, (), ControlCommand.RESUME)


# ---------------------------------------------------------------------------
# Record demo review
# ---------------------------------------------------------------------------


def test_record_demo_review_records_the_bounded_disposition() -> None:
    planned = _plan(
        DecisionOutcome.AUTHORITY_EXCEEDED,
        (),
        ControlCommand.RECORD_DEMO_REVIEW,
        disposition=DemoDisposition.DEMO_DECLINE,
    )

    assert planned.action is ControlAction.DEMO_REVIEW_RECORDED
    assert planned.prior_state is ControlState.AWAITING_REVIEW
    assert planned.payload["disposition"] == "DEMO_DECLINE"


def test_record_demo_review_requires_a_disposition() -> None:
    with pytest.raises(ValueError, match="disposition"):
        _plan(DecisionOutcome.OUT_OF_POLICY, (), ControlCommand.RECORD_DEMO_REVIEW)


def test_record_demo_review_is_illegal_for_missing_fact() -> None:
    with pytest.raises(IllegalControlTransition):
        _plan(
            DecisionOutcome.MISSING_FACT,
            (),
            ControlCommand.RECORD_DEMO_REVIEW,
            disposition=DemoDisposition.DEMO_ALLOW,
        )


# ---------------------------------------------------------------------------
# Undo / compensation
# ---------------------------------------------------------------------------


def test_undo_compensates_the_latest_pause() -> None:
    planned = _plan(DecisionOutcome.OUT_OF_POLICY, ("CASE_PAUSED",), ControlCommand.UNDO)

    assert planned.action is ControlAction.CONTROL_COMPENSATED
    assert planned.prior_state is ControlState.AWAITING_REVIEW
    assert planned.payload["target_event_id"] == str(planned.target_event_id)


def test_undo_compensates_the_latest_review() -> None:
    planned = _plan(
        DecisionOutcome.OUT_OF_POLICY,
        ("DEMO_REVIEW_RECORDED",),
        ControlCommand.UNDO,
    )

    assert planned.action is ControlAction.CONTROL_COMPENSATED
    assert planned.prior_state is ControlState.AWAITING_REVIEW


def test_undo_is_illegal_with_no_reversible_event() -> None:
    with pytest.raises(IllegalControlTransition):
        _plan(DecisionOutcome.OUT_OF_POLICY, (), ControlCommand.UNDO)


def test_undo_is_illegal_when_the_latest_event_is_already_resolved() -> None:
    with pytest.raises(IllegalControlTransition):
        _plan(DecisionOutcome.OUT_OF_POLICY, ("CASE_PAUSED", "CASE_RESUMED"), ControlCommand.UNDO)


# ---------------------------------------------------------------------------
# Full reducer sequences
# ---------------------------------------------------------------------------


def test_reducer_reconstructs_a_full_demo_sequence() -> None:
    projection = _project(
        DecisionOutcome.AUTHORITY_EXCEEDED,
        "CASE_PAUSED",
        "CASE_RESUMED",
        "DEMO_REVIEW_RECORDED",
        "CONTROL_COMPENSATED",
        "CASE_PAUSED",
    )

    assert projection.state is ControlState.PAUSED
    assert len(projection.active) == 1
    assert projection.active[0].action is ControlAction.CASE_PAUSED


def test_reducer_reconstructs_state_after_review_and_undo() -> None:
    projection = _project(
        DecisionOutcome.AUTHORITY_EXCEEDED,
        "CASE_PAUSED",
        "CASE_RESUMED",
        "DEMO_REVIEW_RECORDED",
        "CONTROL_COMPENSATED",
    )

    assert projection.state is ControlState.AWAITING_REVIEW
    assert projection.active == ()


def test_reducer_rejects_a_resume_without_a_pause() -> None:
    with pytest.raises(ValueError, match="no active pause"):
        _project(DecisionOutcome.OUT_OF_POLICY, "CASE_RESUMED")


def test_reducer_rejects_compensation_without_a_reversible_event() -> None:
    with pytest.raises(ValueError, match="no active control event"):
        _project(DecisionOutcome.OUT_OF_POLICY, "CONTROL_COMPENSATED")


def test_plan_requires_a_non_blank_reason() -> None:
    with pytest.raises(ValueError, match="reason"):
        plan_control_command(
            _project(DecisionOutcome.OUT_OF_POLICY),
            ControlCommand.PAUSE,
            reason="   ",
        )
