"""Contract tests for the frozen DecisionDraft shape."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import DecisionOutcome, TemporaryRuleId
from app.domain.models import DecisionDraft

pytestmark = pytest.mark.contract


def _draft(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "outcome": "AUTO_APPROVED",
        "applied_rule_id": "TMP-AUT-01",
        "reason": "Approved under temporary development profile; no payment was made.",
        "question": None,
        "profile_id": "TMP-DEV-001",
    }
    data.update(overrides)
    return data


def test_routine_draft_constructs_without_a_question() -> None:
    draft = DecisionDraft.model_validate(_draft(question=None))

    assert draft.outcome is DecisionOutcome.AUTO_APPROVED
    assert draft.applied_rule_id is TemporaryRuleId.TMP_AUT_01
    assert draft.question is None
    assert draft.profile_id == "TMP-DEV-001"


def test_question_bearing_draft_constructs() -> None:
    draft = DecisionDraft.model_validate(
        _draft(
            outcome="MISSING_FACT",
            applied_rule_id="TMP-REQ-01",
            reason="A required business fact is missing.",
            question="What is the stated purpose?",
        )
    )

    assert draft.outcome is DecisionOutcome.MISSING_FACT
    assert draft.applied_rule_id is TemporaryRuleId.TMP_REQ_01
    assert draft.question == "What is the stated purpose?"


def test_draft_rejects_unknown_outcome_token() -> None:
    with pytest.raises(ValidationError):
        DecisionDraft.model_validate(_draft(outcome="REJECTED"))


def test_draft_rejects_unknown_rule_id_token() -> None:
    with pytest.raises(ValidationError):
        DecisionDraft.model_validate(_draft(applied_rule_id="TMP-AUT-03"))


def test_draft_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        DecisionDraft.model_validate(_draft(reason="   "))


def test_draft_rejects_blank_profile_id() -> None:
    with pytest.raises(ValidationError):
        DecisionDraft.model_validate(_draft(profile_id="  "))


def test_draft_rejects_unknown_fields_such_as_route_or_key() -> None:
    with pytest.raises(ValidationError):
        DecisionDraft.model_validate(
            _draft(reviewer_route="TREASURER"),
        )
    with pytest.raises(ValidationError):
        DecisionDraft.model_validate(
            _draft(question_key="EXPENSE_PROOF"),
        )
