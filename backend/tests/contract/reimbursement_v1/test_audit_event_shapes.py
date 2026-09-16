"""Audit-event shapes enforce actor, reason, predecessor, and target fields."""

from __future__ import annotations

from typing import Any

import jsonschema
from _artifacts import REIMBURSEMENT_SCHEMA


def _audit_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        {"$ref": "#/$defs/AuditEvent", "$defs": REIMBURSEMENT_SCHEMA["$defs"]},
        format_checker=jsonschema.FormatChecker(),
    )


def _event(event_type: str) -> dict[str, Any]:
    return {
        "event_id": "EVT-1",
        "timestamp": "2026-09-10T09:00:00Z",
        "actor_id": "P-009",
        "actor_type": "HUMAN",
        "policy_version": "1.2.0",
        "event_type": event_type,
        "input_hash": "sha256-" + "a" * 64,
        "triggered_rule_ids": [],
        "explanation": "Synthetic audit event.",
    }


def _errors(value: dict[str, Any]) -> list[str]:
    return [error.message for error in _audit_validator().iter_errors(value)]


def test_human_decision_requires_role_reason_outcome_and_decision() -> None:
    event = _event("HUMAN_DECISION")
    event.update(
        {
            "actor_role": "CLUB_CHAIR",
            "reason": "Authorized review decision.",
            "previous_outcome_id": "OUT-1",
            "decision": "APPROVE",
        }
    )
    assert not _errors(event)

    for field in ("actor_role", "reason", "previous_outcome_id", "decision"):
        missing = dict(event)
        del missing[field]
        assert _errors(missing)


def test_settlement_requires_role_reason_predecessor_and_evidence() -> None:
    event = _event("SETTLEMENT")
    event.update(
        {
            "actor_role": "TREASURER",
            "reason": "Settled after recorded human approval.",
            "predecessor_event_id": "EVT-DEC-1",
            "evidence_ids": ["E-1"],
        }
    )
    assert not _errors(event)

    for field in ("actor_role", "reason", "predecessor_event_id", "evidence_ids"):
        missing = dict(event)
        del missing[field]
        assert _errors(missing)


def test_override_requires_previous_outcome_and_reason() -> None:
    event = _event("OVERRIDDEN")
    event.update(
        {
            "actor_role": "CLUB_CHAIR",
            "reason": "Configured override.",
            "previous_outcome_id": "OUT-1",
        }
    )
    assert not _errors(event)

    missing = dict(event)
    del missing["previous_outcome_id"]
    assert _errors(missing)


def test_undo_requires_target_audit_event_and_reason() -> None:
    event = _event("UNDONE")
    event.update(
        {
            "actor_role": "CLUB_CHAIR",
            "reason": "Compensating undo.",
            "target_audit_event_id": "EVT-2",
        }
    )
    assert not _errors(event)

    missing = dict(event)
    del missing["target_audit_event_id"]
    assert _errors(missing)


def test_pause_and_resume_require_actor_role_and_reason() -> None:
    for event_type in ("PAUSED", "RESUMED"):
        event = _event(event_type)
        event.update({"actor_role": "CLUB_CHAIR", "reason": "Synthetic control."})
        assert not _errors(event), event_type

        missing = dict(event)
        del missing["reason"]
        assert _errors(missing), event_type
