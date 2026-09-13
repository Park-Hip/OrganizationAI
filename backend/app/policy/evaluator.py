"""Pure deterministic evaluation for the temporary development profile.

The evaluator accepts already validated, normalized domain values and returns a
``DecisionDraft``. It owns no transport, persistence, timing, network, file,
or payment behavior.
"""

from __future__ import annotations

from app.domain.enums import DecisionOutcome, TemporaryRuleId
from app.domain.models import DecisionDraft, NormalizedCase, TemporaryProfile
from app.policy.normalization import QUESTION_BY_FIELD_PATH

_AUTO_APPROVED_REASON = "Approved under temporary development profile; no payment was made."

_EVALUATOR_ONLY_MISSING_FACT_QUESTIONS: dict[str, str] = {
    "requester_role": "What is the synthetic requester role for this request?",
    "expense": "What synthetic expense should this request cover?",
}


def _is_missing(value: object) -> bool:
    """Return whether a validated business value is absent or whitespace-only."""
    return value is None or (isinstance(value, str) and not value.strip())


def _first_missing_fact(case: NormalizedCase) -> str | None:
    """Return the first missing business fact in the approved request order."""
    request_facts: tuple[tuple[str, object], ...] = (
        ("purpose", case.purpose),
        ("requester_role", case.requester_role),
    )
    for field_path, value in request_facts:
        if _is_missing(value):
            return field_path

    expense = case.expense
    if expense is None:
        return "expense"

    expense_facts: tuple[tuple[str, object], ...] = (
        ("expense.category", expense.category),
        ("expense.description", expense.description),
        ("expense.amount_vnd", expense.amount_vnd),
        ("expense.expense_date", expense.expense_date),
        ("expense.evidence_status", expense.evidence_status),
    )
    for field_path, value in expense_facts:
        if _is_missing(value):
            return field_path
    return None


def _missing_fact_draft(profile: TemporaryProfile, field_path: str) -> DecisionDraft:
    """Build the first-rule result for one missing business fact."""
    return DecisionDraft(
        outcome=DecisionOutcome.MISSING_FACT,
        applied_rule_id=TemporaryRuleId.TMP_REQ_01,
        reason=(
            f"Required synthetic business fact '{field_path}' is missing under "
            f"temporary development profile {profile.profile_id}."
        ),
        question=(
            QUESTION_BY_FIELD_PATH[field_path]
            if field_path in QUESTION_BY_FIELD_PATH
            else _EVALUATOR_ONLY_MISSING_FACT_QUESTIONS[field_path]
        ),
        profile_id=profile.profile_id,
    )


def evaluate_case(case: NormalizedCase, profile: TemporaryProfile) -> DecisionDraft:
    """Evaluate a normalized case using the supplied immutable profile.

    Rules are evaluated in documented first-applicable order: missing business
    fact, category eligibility, evidence declaration, authority limit, and
    automatic approval. The function has no side effects and never selects a
    profile or performs a payment action.
    """
    missing_fact = _first_missing_fact(case)
    if missing_fact is not None:
        return _missing_fact_draft(profile, missing_fact)

    # The first rule guarantees that every value below is present.
    expense = case.expense
    assert expense is not None
    assert expense.category is not None
    assert expense.description is not None
    assert expense.amount_vnd is not None
    assert expense.expense_date is not None
    assert expense.evidence_status is not None
    if expense.category not in profile.allowed_categories:
        return DecisionDraft(
            outcome=DecisionOutcome.OUT_OF_POLICY,
            applied_rule_id=TemporaryRuleId.TMP_CAT_01,
            reason=(
                f"Expense category '{expense.category.value}' is outside temporary "
                f"development profile {profile.profile_id}."
            ),
            question="Do you authorize this temporary exception?",
            profile_id=profile.profile_id,
        )

    if expense.evidence_status != profile.required_evidence_status:
        return DecisionDraft(
            outcome=DecisionOutcome.MISSING_FACT,
            applied_rule_id=TemporaryRuleId.TMP_EVD_01,
            reason=(
                f"The declared expense evidence status is '{expense.evidence_status.value}', "
                f"but temporary development profile {profile.profile_id} requires "
                f"'{profile.required_evidence_status.value}'."
            ),
            question="Can you provide the expense proof or reference?",
            profile_id=profile.profile_id,
        )

    if expense.amount_vnd > profile.auto_approve_limit_vnd:
        return DecisionDraft(
            outcome=DecisionOutcome.AUTHORITY_EXCEEDED,
            applied_rule_id=TemporaryRuleId.TMP_AUT_02,
            reason=(
                f"Amount {expense.amount_vnd} VND exceeds temporary development profile "
                f"{profile.profile_id} delegated limit of {profile.auto_approve_limit_vnd} VND."
            ),
            question=(f"Do you approve this named synthetic request for {expense.amount_vnd} VND?"),
            profile_id=profile.profile_id,
        )

    return DecisionDraft(
        outcome=DecisionOutcome.AUTO_APPROVED,
        applied_rule_id=TemporaryRuleId.TMP_AUT_01,
        reason=_AUTO_APPROVED_REASON,
        question=None,
        profile_id=profile.profile_id,
    )
