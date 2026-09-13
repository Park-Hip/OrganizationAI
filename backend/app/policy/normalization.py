"""Layer 1 normalization and repair-question preparation for TMP-DEV-001.

This module turns a validated ``CaseSubmission`` into a canonical
``NormalizedCase`` and provides the deterministic first-missing-field and
repair-question helpers a future evaluator will consume.

It is pure: no HTTP, database, clock, file, LLM, settings, or profile
dependency. It never makes a policy decision.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.domain.models import CaseSubmission, Expense, NormalizedCase

# The single source of truth for the approved first-missing-fact order and its
# exact repair wording. Dictionary order also defines MISSING_FIELD_PATHS.
QUESTION_BY_FIELD_PATH: Mapping[str, str] = MappingProxyType(
    {
        "purpose": "What is the synthetic purpose of this expense?",
        "expense.category": "Which temporary expense category applies to this synthetic expense?",
        "expense.description": "What is the synthetic expense description?",
        "expense.amount_vnd": "What is the positive integer synthetic expense amount in VND?",
        "expense.expense_date": "What is the synthetic expense date?",
        "expense.evidence_status": (
            "Is the declared synthetic expense evidence status PRESENT or NOT_PROVIDED?"
        ),
    }
)

MISSING_FIELD_PATHS: tuple[str, ...] = tuple(QUESTION_BY_FIELD_PATH)


def _blank_to_none(value: str | None) -> str | None:
    """Treat whitespace-only text as absent and preserve nonblank text exactly."""
    if value is not None and not value.strip():
        return None
    return value


def normalize_case(submission: CaseSubmission) -> NormalizedCase:
    """Return a new case with only decision-bearing whitespace-only text made absent.

    ``purpose`` and ``expense.description`` lose values that contain no
    non-whitespace content. Nonblank text, including surrounding whitespace,
    is preserved exactly. ``case_id`` and ``requester_role`` are never altered.
    """
    expense: Expense | None = None
    if submission.expense is not None:
        expense = Expense(
            category=submission.expense.category,
            description=_blank_to_none(submission.expense.description),
            amount_vnd=submission.expense.amount_vnd,
            expense_date=submission.expense.expense_date,
            evidence_status=submission.expense.evidence_status,
        )
    return NormalizedCase(
        case_id=submission.case_id,
        submitted_at=submission.submitted_at,
        requester_role=submission.requester_role,
        purpose=_blank_to_none(submission.purpose),
        expense=expense,
    )


def _field_value(case: NormalizedCase, path: str) -> object | None:
    """Resolve one approved field path without dynamic attribute access."""
    if path == "purpose":
        return case.purpose
    if path == "expense.category":
        return case.expense.category if case.expense is not None else None
    if path == "expense.description":
        return case.expense.description if case.expense is not None else None
    if path == "expense.amount_vnd":
        return case.expense.amount_vnd if case.expense is not None else None
    if path == "expense.expense_date":
        return case.expense.expense_date if case.expense is not None else None
    if path == "expense.evidence_status":
        return case.expense.evidence_status if case.expense is not None else None
    raise ValueError(f"Unknown field path: {path}")


def first_missing_field(case: NormalizedCase) -> str | None:
    """Return the first absent field path in the approved order, or None."""
    for path in MISSING_FIELD_PATHS:
        if _field_value(case, path) is None:
            return path
    return None


def question_for_field_path(field_path: str) -> str:
    """Return one exact repair question for an approved field path."""
    try:
        return QUESTION_BY_FIELD_PATH[field_path]
    except KeyError as error:
        raise ValueError(f"No question defined for field path: {field_path}") from error
