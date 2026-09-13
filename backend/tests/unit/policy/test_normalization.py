"""Unit tests for Layer 1 normalization and repair-question preparation."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums import EvidenceStatus, TemporaryCategory
from app.domain.models import CaseSubmission, NormalizedCase
from app.policy.normalization import (
    MISSING_FIELD_PATHS,
    QUESTION_BY_FIELD_PATH,
    first_missing_field,
    normalize_case,
    question_for_field_path,
)

_EXPENSE = {
    "category": "TEST_ALLOWED",
    "description": "Synthetic materials line",
    "amount_vnd": 999,
    "expense_date": "2026-01-14",
    "evidence_status": "PRESENT",
}


def _submission(**overrides: object) -> CaseSubmission:
    data: dict[str, object] = {
        "case_id": "TMP-CASE-01",
        "submitted_at": "2026-01-15T09:00:00Z",
        "requester_role": "TEST_REQUESTER",
        "purpose": "Synthetic allowed expense",
        "expense": dict(_EXPENSE),
    }
    data.update(overrides)
    return CaseSubmission.model_validate(data)


def test_whitespace_only_purpose_normalizes_to_absent() -> None:
    case = normalize_case(_submission(purpose="   \t\n"))

    assert case.purpose is None


def test_whitespace_only_expense_description_normalizes_to_absent() -> None:
    case = normalize_case(_submission(expense={**_EXPENSE, "description": "   "}))

    assert case.expense is not None
    assert case.expense.description is None


def test_requester_role_is_left_unchanged_when_whitespace_only() -> None:
    case = normalize_case(_submission(requester_role="   "))

    assert case.requester_role == "   "


def test_nonblank_text_is_preserved_exactly() -> None:
    case = normalize_case(
        _submission(
            purpose="  A  ",
            expense={**_EXPENSE, "description": "  B  "},
        )
    )

    assert case.purpose == "  A  "
    assert case.expense is not None
    assert case.expense.description == "  B  "


def test_normalize_case_returns_a_normalized_case_instance() -> None:
    case = normalize_case(_submission())

    assert isinstance(case, NormalizedCase)


def test_normalize_case_returns_new_instances_and_preserves_input() -> None:
    submission = _submission()
    normalized = normalize_case(submission)

    assert normalized is not submission
    assert submission.purpose == "Synthetic allowed expense"
    assert submission.expense is not None
    assert normalized.expense is not submission.expense
    assert submission.expense.description == "Synthetic materials line"


def test_normalization_is_idempotent() -> None:
    normalized_once = normalize_case(
        _submission(purpose="   ", expense={**_EXPENSE, "description": "  "})
    )

    normalized_twice = normalize_case(normalized_once)

    assert normalized_twice == normalized_once


@pytest.mark.parametrize(
    "invalid_overrides",
    [
        {"case_id": "   "},
        {"expense": {"category": "REAL_FLIGHT"}},
        {"expense": {"amount_vnd": 0}},
        {"expense": {"amount_vnd": True}},
    ],
)
def test_structural_errors_are_rejected_before_normalization(
    invalid_overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        _submission(**invalid_overrides)


def test_first_missing_field_is_purpose_when_purpose_absent() -> None:
    case = normalize_case(_submission(purpose=None))

    assert first_missing_field(case) == "purpose"


@pytest.mark.parametrize(
    ("expense_overrides", "expected_path"),
    [
        ({"category": None}, "expense.category"),
        ({"description": None}, "expense.description"),
        ({"amount_vnd": None}, "expense.amount_vnd"),
        ({"expense_date": None}, "expense.expense_date"),
        ({"evidence_status": None}, "expense.evidence_status"),
    ],
)
def test_first_missing_field_within_expense(
    expense_overrides: dict[str, object], expected_path: str
) -> None:
    case = normalize_case(_submission(expense={**_EXPENSE, **expense_overrides}))

    assert first_missing_field(case) == expected_path


def test_first_missing_field_is_category_when_expense_absent() -> None:
    case = normalize_case(_submission(expense=None))

    assert first_missing_field(case) == "expense.category"


def test_first_missing_field_is_none_for_complete_case() -> None:
    case = normalize_case(_submission())

    assert first_missing_field(case) is None


def test_field_paths_and_question_map_are_identical_and_ordered() -> None:
    assert tuple(QUESTION_BY_FIELD_PATH) == MISSING_FIELD_PATHS
    assert MISSING_FIELD_PATHS == (
        "purpose",
        "expense.category",
        "expense.description",
        "expense.amount_vnd",
        "expense.expense_date",
        "expense.evidence_status",
    )


def test_question_map_matches_the_approved_exact_text() -> None:
    assert QUESTION_BY_FIELD_PATH == {
        "purpose": "What is the synthetic purpose of this expense?",
        "expense.category": "Which temporary expense category applies to this synthetic expense?",
        "expense.description": "What is the synthetic expense description?",
        "expense.amount_vnd": "What is the positive integer synthetic expense amount in VND?",
        "expense.expense_date": "What is the synthetic expense date?",
        "expense.evidence_status": (
            "Is the declared synthetic expense evidence status PRESENT or NOT_PROVIDED?"
        ),
    }


def test_question_for_field_path_returns_approved_text() -> None:
    assert question_for_field_path("purpose") == "What is the synthetic purpose of this expense?"


def test_question_for_field_path_rejects_unknown_path() -> None:
    with pytest.raises(ValueError):
        question_for_field_path("unknown.field")


def test_not_provided_evidence_is_not_a_structurally_missing_fact() -> None:
    case = normalize_case(_submission(expense={**_EXPENSE, "evidence_status": "NOT_PROVIDED"}))

    assert case.expense is not None
    assert case.expense.evidence_status is EvidenceStatus.NOT_PROVIDED
    assert first_missing_field(case) is None


def test_provenance_and_domain_values_pass_through_normalization() -> None:
    case = normalize_case(_submission())

    assert case.expense is not None
    assert case.submitted_at == datetime.fromisoformat("2026-01-15T09:00:00+00:00")
    assert case.expense.category is TemporaryCategory.TEST_ALLOWED
    assert case.expense.expense_date == date(2026, 1, 14)
