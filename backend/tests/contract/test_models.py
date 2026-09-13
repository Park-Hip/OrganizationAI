"""Contract tests for the frozen Layer 0 record shapes."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums import EvidenceStatus, TemporaryCategory
from app.domain.models import CaseSubmission, Expense, NormalizedCase, TemporaryProfile


def _valid_submission(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "case_id": "TMP-CASE-01",
        "submitted_at": "2026-01-15T09:00:00Z",
        "requester_role": "TEST_REQUESTER",
        "purpose": "Synthetic allowed expense",
        "expense": {
            "category": "TEST_ALLOWED",
            "description": "Synthetic materials line",
            "amount_vnd": 999,
            "expense_date": "2026-01-14",
            "evidence_status": "PRESENT",
        },
    }
    data.update(overrides)
    return data


def test_valid_case_with_null_business_facts_constructs() -> None:
    case = CaseSubmission(
        case_id="TMP-CASE-01",
        submitted_at=datetime(2026, 1, 15, 9, 0, 0),
        requester_role=None,
        purpose=None,
        expense=None,
    )

    assert case.case_id == "TMP-CASE-01"
    assert case.requester_role is None
    assert case.purpose is None
    assert case.expense is None


def test_fully_populated_case_constructs_and_parses_transport_typed_fields() -> None:
    case = CaseSubmission.model_validate(_valid_submission())

    assert case.expense is not None
    assert case.submitted_at == datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC)
    assert case.expense.category is TemporaryCategory.TEST_ALLOWED
    assert case.expense.amount_vnd == 999
    assert case.expense.expense_date == date(2026, 1, 14)
    assert case.expense.evidence_status is EvidenceStatus.PRESENT


def test_expense_accepts_all_null_business_fields() -> None:
    expense = Expense.model_validate({})

    assert expense.category is None
    assert expense.description is None
    assert expense.amount_vnd is None
    assert expense.expense_date is None
    assert expense.evidence_status is None


def test_case_submission_rejects_blank_case_id() -> None:
    with pytest.raises(ValidationError):
        CaseSubmission.model_validate(_valid_submission(case_id="   "))


def test_case_submission_rejects_missing_case_id() -> None:
    data = _valid_submission()
    data.pop("case_id")

    with pytest.raises(ValidationError):
        CaseSubmission.model_validate(data)


def test_case_submission_rejects_invalid_timestamp() -> None:
    with pytest.raises(ValidationError):
        CaseSubmission.model_validate(_valid_submission(submitted_at="not-a-timestamp"))


def test_expense_rejects_unknown_enum_token() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"category": "REAL_FLIGHT"})


def test_expense_rejects_boolean_amount() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"amount_vnd": True})


def test_expense_rejects_string_amount() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"amount_vnd": "999"})


def test_expense_rejects_non_integral_amount() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"amount_vnd": 1.5})


def test_expense_rejects_zero_amount() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"amount_vnd": 0})


def test_expense_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"amount_vnd": -1})


def test_case_submission_rejects_client_provided_profile_or_provenance_fields() -> None:
    for field in ("profile_id", "profile_source", "data_class", "workflow_validation_status"):
        data = _valid_submission(**{field: "TEMPORARY_DEVELOPMENT"})

        with pytest.raises(ValidationError):
            CaseSubmission.model_validate(data)


def test_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Expense.model_validate({"category": "TEST_ALLOWED", "receipt_file": "not-supported"})
    with pytest.raises(ValidationError):
        CaseSubmission.model_validate(_valid_submission(activity_ref="ACT-001"))


def test_normalized_case_has_the_same_fields_as_case_submission() -> None:
    assert set(NormalizedCase.model_fields) == set(CaseSubmission.model_fields)


def test_temporary_profile_is_frozen_and_forbids_extra_fields() -> None:
    profile = TemporaryProfile(
        profile_id="TMP-DEV-001",
        profile_source="TEMPORARY_DEVELOPMENT",
        data_class="SYNTHETIC",
        workflow_validation_status="UNVALIDATED",
        allowed_categories={"TEST_ALLOWED"},
        required_evidence_status="PRESENT",
        auto_approve_limit_vnd=1000,
    )

    assert profile.allowed_categories == frozenset({TemporaryCategory.TEST_ALLOWED})

    with pytest.raises(ValidationError):
        TemporaryProfile.model_validate(
            {
                "profile_id": "TMP-DEV-001",
                "profile_source": "TEMPORARY_DEVELOPMENT",
                "data_class": "SYNTHETIC",
                "workflow_validation_status": "UNVALIDATED",
                "allowed_categories": {"TEST_ALLOWED"},
                "required_evidence_status": "PRESENT",
                "auto_approve_limit_vnd": 1000,
                "blocked_categories": {"TEST_BLOCKED"},
            }
        )
