"""Unit tests for the pure temporary policy evaluator."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from app.domain.enums import (
    DataClass,
    DecisionOutcome,
    EvidenceStatus,
    ProfileSource,
    TemporaryCategory,
    TemporaryRuleId,
    WorkflowValidationStatus,
)
from app.domain.models import NormalizedCase, TemporaryProfile
from app.policy.evaluator import evaluate_case
from app.policy.profile import TMP_DEV_001_PROFILE

_BACKEND_ROOT = Path(__file__).resolve().parents[3]

_BASE_EXPENSE: dict[str, object] = {
    "category": TemporaryCategory.TEST_ALLOWED,
    "description": "Synthetic materials line",
    "amount_vnd": 999,
    "expense_date": "2026-01-14",
    "evidence_status": EvidenceStatus.PRESENT,
}


def _case(**overrides: object) -> NormalizedCase:
    data: dict[str, object] = {
        "case_id": "UNFIXTURED-CASE",
        "submitted_at": datetime.fromisoformat("2026-01-15T09:00:00+00:00"),
        "requester_role": "TEST_REQUESTER",
        "purpose": "Synthetic allowed expense",
        "expense": dict(_BASE_EXPENSE),
    }
    data.update(overrides)
    return NormalizedCase.model_validate(data)


def _expense(**overrides: object) -> dict[str, object]:
    expense = dict(_BASE_EXPENSE)
    expense.update(overrides)
    return expense


def _profile(**overrides: object) -> TemporaryProfile:
    data: dict[str, object] = {
        "profile_id": "ALT-TMP-PROFILE",
        "profile_source": ProfileSource.TEMPORARY_DEVELOPMENT,
        "data_class": DataClass.SYNTHETIC,
        "workflow_validation_status": WorkflowValidationStatus.UNVALIDATED,
        "allowed_categories": frozenset({TemporaryCategory.TEST_ALLOWED}),
        "required_evidence_status": EvidenceStatus.PRESENT,
        "auto_approve_limit_vnd": 1000,
    }
    data.update(overrides)
    return TemporaryProfile.model_validate(data)


def test_complete_case_returns_auto_approved_with_exact_reason_and_profile_id() -> None:
    draft = evaluate_case(_case(), TMP_DEV_001_PROFILE)

    assert draft.outcome is DecisionOutcome.AUTO_APPROVED
    assert draft.applied_rule_id is TemporaryRuleId.TMP_AUT_01
    assert draft.reason == "Approved under temporary development profile; no payment was made."
    assert draft.question is None
    assert draft.profile_id == TMP_DEV_001_PROFILE.profile_id


@pytest.mark.parametrize(
    ("overrides", "expected_question"),
    [
        (
            {"purpose": None, "requester_role": None, "expense": None},
            "What is the synthetic purpose of this expense?",
        ),
        ({"purpose": "   \t"}, "What is the synthetic purpose of this expense?"),
        ({"requester_role": "\n"}, "What is the synthetic requester role for this request?"),
        ({"expense": None}, "What synthetic expense should this request cover?"),
        (
            {"expense": _expense(category=None)},
            "Which temporary expense category applies to this synthetic expense?",
        ),
        ({"expense": _expense(description="  ")}, "What is the synthetic expense description?"),
        (
            {"expense": _expense(amount_vnd=None)},
            "What is the positive integer synthetic expense amount in VND?",
        ),
        ({"expense": _expense(expense_date=None)}, "What is the synthetic expense date?"),
        (
            {"expense": _expense(evidence_status=None)},
            "Is the declared synthetic expense evidence status PRESENT or NOT_PROVIDED?",
        ),
    ],
)
def test_first_missing_business_fact_wins(
    overrides: dict[str, object], expected_question: str
) -> None:
    draft = evaluate_case(_case(**overrides), TMP_DEV_001_PROFILE)

    assert draft.outcome is DecisionOutcome.MISSING_FACT
    assert draft.applied_rule_id is TemporaryRuleId.TMP_REQ_01
    assert draft.question == expected_question


def test_missing_fact_question_is_one_direct_nonblank_question() -> None:
    draft = evaluate_case(_case(purpose=None), TMP_DEV_001_PROFILE)

    assert draft.question == "What is the synthetic purpose of this expense?"
    assert draft.question is not None
    assert draft.question.endswith("?")
    assert draft.reason.strip()


def test_missing_fact_precedes_out_of_policy_category() -> None:
    draft = evaluate_case(
        _case(
            purpose=None,
            expense=_expense(category=TemporaryCategory.TEST_BLOCKED),
        ),
        TMP_DEV_001_PROFILE,
    )

    assert draft.outcome is DecisionOutcome.MISSING_FACT
    assert draft.applied_rule_id is TemporaryRuleId.TMP_REQ_01


def test_out_of_policy_category_precedes_authority_limit() -> None:
    draft = evaluate_case(
        _case(expense=_expense(category=TemporaryCategory.TEST_BLOCKED, amount_vnd=1001)),
        TMP_DEV_001_PROFILE,
    )

    assert draft.outcome is DecisionOutcome.OUT_OF_POLICY
    assert draft.applied_rule_id is TemporaryRuleId.TMP_CAT_01
    assert "TEST_BLOCKED" in draft.reason
    assert "temporary development profile" in draft.reason
    assert draft.question == "Do you authorize this temporary exception?"


def test_missing_evidence_precedes_authority_limit() -> None:
    draft = evaluate_case(
        _case(expense=_expense(evidence_status=EvidenceStatus.NOT_PROVIDED, amount_vnd=1001)),
        TMP_DEV_001_PROFILE,
    )

    assert draft.outcome is DecisionOutcome.MISSING_FACT
    assert draft.applied_rule_id is TemporaryRuleId.TMP_EVD_01
    assert draft.question == "Can you provide the expense proof or reference?"
    assert "inspect" not in draft.reason.lower()


@pytest.mark.parametrize(
    ("amount", "expected_outcome", "expected_rule"),
    [
        (999, DecisionOutcome.AUTO_APPROVED, TemporaryRuleId.TMP_AUT_01),
        (1000, DecisionOutcome.AUTO_APPROVED, TemporaryRuleId.TMP_AUT_01),
        (1001, DecisionOutcome.AUTHORITY_EXCEEDED, TemporaryRuleId.TMP_AUT_02),
    ],
)
def test_authority_limit_is_inclusive(
    amount: int,
    expected_outcome: DecisionOutcome,
    expected_rule: TemporaryRuleId,
) -> None:
    draft = evaluate_case(_case(expense=_expense(amount_vnd=amount)), TMP_DEV_001_PROFILE)

    assert draft.outcome is expected_outcome
    assert draft.applied_rule_id is expected_rule
    assert draft.profile_id == TMP_DEV_001_PROFILE.profile_id
    assert draft.reason.strip()
    if expected_outcome is DecisionOutcome.AUTO_APPROVED:
        assert draft.question is None
    else:
        assert draft.question == "Do you approve this named synthetic request for 1001 VND?"


def test_alternate_profile_controls_allow_list_and_limit() -> None:
    profile = _profile(
        allowed_categories=frozenset({TemporaryCategory.TEST_BLOCKED}),
        auto_approve_limit_vnd=2000,
    )

    draft = evaluate_case(
        _case(expense=_expense(category=TemporaryCategory.TEST_BLOCKED, amount_vnd=1500)),
        profile,
    )

    assert draft.outcome is DecisionOutcome.AUTO_APPROVED
    assert draft.applied_rule_id is TemporaryRuleId.TMP_AUT_01
    assert draft.profile_id == profile.profile_id


def test_alternate_profile_controls_required_evidence_status() -> None:
    profile = _profile(required_evidence_status=EvidenceStatus.NOT_PROVIDED)

    draft = evaluate_case(
        _case(expense=_expense(evidence_status=EvidenceStatus.NOT_PROVIDED)),
        profile,
    )

    assert draft.outcome is DecisionOutcome.AUTO_APPROVED
    assert draft.applied_rule_id is TemporaryRuleId.TMP_AUT_01
    assert draft.profile_id == profile.profile_id


def test_structural_fields_do_not_change_the_decision() -> None:
    first = evaluate_case(
        _case(case_id="NO-FIXTURE-ID-A", submitted_at=datetime(2030, 1, 1)),
        TMP_DEV_001_PROFILE,
    )
    second = evaluate_case(
        _case(case_id="NO-FIXTURE-ID-B", submitted_at=datetime(2040, 1, 1)),
        TMP_DEV_001_PROFILE,
    )

    assert first == second


def test_evaluator_does_not_mutate_its_frozen_inputs() -> None:
    case = _case()
    profile = TMP_DEV_001_PROFILE
    case_before = case.model_dump()
    profile_before = profile.model_dump()

    evaluate_case(case, profile)

    assert case.model_dump() == case_before
    assert profile.model_dump() == profile_before


def test_policy_import_boundary_excludes_runtime_services() -> None:
    probe = """
import sys

from app.policy.evaluator import evaluate_case

assert callable(evaluate_case)
for module_name in ("fastapi", "sqlalchemy", "app.core.settings", "app.persistence"):
    assert module_name not in sys.modules, f"{module_name} was imported by the evaluator"
print("evaluator-import-boundary-ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "evaluator-import-boundary-ok" in result.stdout
