"""Constructed (non-fixture) behavior proofs for the temporary decision core.

These tests never read the canonical corpus. They build fresh cases with new
IDs and different prose so a decision must follow facts and the immutable
profile, not any fixture identity or copied fixture text.
"""

from __future__ import annotations

from collections.abc import Callable

from app.domain.enums import DecisionOutcome, TemporaryRuleId
from app.domain.models import CaseSubmission, DecisionDraft

_NO_PAYMENT_REASON = "Approved under temporary development profile; no payment was made."

_Evaluator = Callable[[CaseSubmission], DecisionDraft]


def _submission(
    *,
    case_id: str = "PROP-CASE",
    purpose: str | None = "Property-check purpose",
    requester_role: str | None = "TEST_REQUESTER",
    category: str = "TEST_ALLOWED",
    description: str = "Property-check line",
    amount_vnd: int = 999,
    evidence_status: str = "PRESENT",
) -> CaseSubmission:
    return CaseSubmission.model_validate(
        {
            "case_id": case_id,
            "submitted_at": "2026-02-01T10:00:00Z",
            "requester_role": requester_role,
            "purpose": purpose,
            "expense": {
                "category": category,
                "description": description,
                "amount_vnd": amount_vnd,
                "expense_date": "2026-01-31",
                "evidence_status": evidence_status,
            },
        }
    )


def test_different_identity_and_prose_share_the_automatic_decision(
    evaluate_submission: _Evaluator,
) -> None:
    first = _submission(case_id="PROP-A", purpose="First stated purpose", description="First line")
    second = _submission(
        case_id="PROP-B",
        purpose="Completely different stated purpose",
        description="Second line",
    )

    first_draft = evaluate_submission(first)
    second_draft = evaluate_submission(second)

    assert first_draft == second_draft
    assert first_draft.outcome is DecisionOutcome.AUTO_APPROVED
    assert first_draft.applied_rule_id is TemporaryRuleId.TMP_AUT_01
    assert first_draft.reason == _NO_PAYMENT_REASON
    assert first_draft.question is None


def test_inclusive_authority_boundary_split(evaluate_submission: _Evaluator) -> None:
    at_limit = evaluate_submission(_submission(amount_vnd=1000))
    above_limit = evaluate_submission(_submission(amount_vnd=1001))

    assert at_limit.outcome is DecisionOutcome.AUTO_APPROVED
    assert at_limit.applied_rule_id is TemporaryRuleId.TMP_AUT_01
    assert above_limit.outcome is DecisionOutcome.AUTHORITY_EXCEEDED
    assert above_limit.applied_rule_id is TemporaryRuleId.TMP_AUT_02


def test_first_missing_fact_precedes_every_later_check(
    evaluate_submission: _Evaluator,
) -> None:
    draft = evaluate_submission(
        _submission(
            purpose="   ",
            category="TEST_BLOCKED",
            evidence_status="NOT_PROVIDED",
            amount_vnd=1001,
        )
    )

    assert draft.outcome is DecisionOutcome.MISSING_FACT
    assert draft.applied_rule_id is TemporaryRuleId.TMP_REQ_01
    assert draft.question is not None and draft.question.strip() != ""


def test_category_precedes_evidence_and_authority(
    evaluate_submission: _Evaluator,
) -> None:
    draft = evaluate_submission(
        _submission(
            category="TEST_BLOCKED",
            evidence_status="NOT_PROVIDED",
            amount_vnd=1001,
        )
    )

    assert draft.outcome is DecisionOutcome.OUT_OF_POLICY
    assert draft.applied_rule_id is TemporaryRuleId.TMP_CAT_01


def test_evidence_precedes_the_authority_limit(
    evaluate_submission: _Evaluator,
) -> None:
    draft = evaluate_submission(_submission(evidence_status="NOT_PROVIDED", amount_vnd=1001))

    assert draft.outcome is DecisionOutcome.MISSING_FACT
    assert draft.applied_rule_id is TemporaryRuleId.TMP_EVD_01


def test_evaluation_is_deterministic_and_does_not_mutate_input(
    evaluate_submission: _Evaluator,
) -> None:
    submission = _submission(case_id="PROP-D")
    frozen_snapshot = submission.model_dump()

    first = evaluate_submission(submission)
    second = evaluate_submission(submission)

    assert first == second
    assert submission.model_dump() == frozen_snapshot
