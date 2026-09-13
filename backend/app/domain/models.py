"""Frozen Layer 0 domain record shapes.

These models are transport- and persistence-agnostic record definitions.
They carry only structural validation and intentionally contain no evaluator,
normalizer, clock, network, filesystem, or database behavior.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.enums import (
    DataClass,
    DecisionOutcome,
    EvidenceStatus,
    ProfileSource,
    TemporaryCategory,
    TemporaryRuleId,
    WorkflowValidationStatus,
)


class Expense(BaseModel):
    """One optional expense line whose business fields can all be null.

    A null field is a missing business fact that a later evaluator can ask to
    repair. An invalid transport value is rejected before that evaluator runs.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: TemporaryCategory | None = None
    description: str | None = None
    amount_vnd: int | None = None
    expense_date: date | None = None
    evidence_status: EvidenceStatus | None = None

    @field_validator("amount_vnd", mode="before")
    @classmethod
    def _reject_boolean_or_non_integer_amount(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("amount_vnd must be an integer")
        return value

    @field_validator("amount_vnd")
    @classmethod
    def _reject_non_positive_amount(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("amount_vnd must be a positive integer")
        return value


class CaseSubmission(BaseModel):
    """Client transport shape with no profile, provenance, route, or activity reference."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str
    submitted_at: datetime
    requester_role: str | None = None
    purpose: str | None = None
    expense: Expense | None = None

    @field_validator("case_id")
    @classmethod
    def _require_non_blank_case_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("case_id must not be blank")
        return value


class NormalizedCase(CaseSubmission):
    """The explicit output of Layer 1 normalization.

    It intentionally retains the transport shape while Layer 1 canonicalizes
    only its approved decision-bearing text fields.
    """


class TemporaryProfile(BaseModel):
    """Immutable server-owned snapshot used by a future evaluator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str
    profile_source: ProfileSource
    data_class: DataClass
    workflow_validation_status: WorkflowValidationStatus
    allowed_categories: frozenset[TemporaryCategory]
    required_evidence_status: EvidenceStatus
    auto_approve_limit_vnd: int

    @field_validator("profile_id")
    @classmethod
    def _require_non_blank_profile_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("profile_id must not be blank")
        return value

    @field_validator("auto_approve_limit_vnd", mode="before")
    @classmethod
    def _reject_boolean_or_non_integer_limit(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("auto_approve_limit_vnd must be an integer")
        return value

    @field_validator("auto_approve_limit_vnd")
    @classmethod
    def _reject_non_positive_limit(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("auto_approve_limit_vnd must be a positive integer")
        return value


class DecisionDraft(BaseModel):
    """Pure decision result with no route, key, ID, timestamp, or persistence snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: DecisionOutcome
    applied_rule_id: TemporaryRuleId
    reason: str
    question: str | None = None
    profile_id: str

    @field_validator("reason")
    @classmethod
    def _require_non_blank_reason(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be blank")
        return value

    @field_validator("profile_id")
    @classmethod
    def _require_non_blank_profile_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("profile_id must not be blank")
        return value
