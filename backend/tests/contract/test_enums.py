"""Contract tests for the frozen Layer 0 enums."""

from __future__ import annotations

from enum import Enum

import pytest

from app.domain import enums

pytestmark = pytest.mark.contract


def _values(enum_type: type[Enum]) -> set[str]:
    return {member.value for member in enum_type}


def test_temporary_category_values_are_exact() -> None:
    assert _values(enums.TemporaryCategory) == {"TEST_ALLOWED", "TEST_BLOCKED"}


def test_evidence_status_values_are_exact() -> None:
    assert _values(enums.EvidenceStatus) == {"PRESENT", "NOT_PROVIDED"}


def test_decision_outcome_values_are_exact() -> None:
    assert _values(enums.DecisionOutcome) == {
        "AUTO_APPROVED",
        "MISSING_FACT",
        "OUT_OF_POLICY",
        "AUTHORITY_EXCEEDED",
    }


def test_temporary_rule_id_values_are_exact() -> None:
    assert _values(enums.TemporaryRuleId) == {
        "TMP-REQ-01",
        "TMP-CAT-01",
        "TMP-EVD-01",
        "TMP-AUT-01",
        "TMP-AUT-02",
    }


def test_provenance_enums_each_have_a_single_value() -> None:
    assert _values(enums.ProfileSource) == {"TEMPORARY_DEVELOPMENT"}
    assert _values(enums.DataClass) == {"SYNTHETIC"}
    assert _values(enums.WorkflowValidationStatus) == {"UNVALIDATED"}


def test_every_frozen_enum_is_a_string_enum() -> None:
    for enum_type in (
        enums.TemporaryCategory,
        enums.EvidenceStatus,
        enums.DecisionOutcome,
        enums.TemporaryRuleId,
        enums.ProfileSource,
        enums.DataClass,
        enums.WorkflowValidationStatus,
    ):
        assert issubclass(enum_type, str)
        assert issubclass(enum_type, Enum)


def test_removed_enum_groups_are_absent_from_the_domain_vocabulary() -> None:
    for name in (
        "ClaimRoute",
        "ReviewerRoute",
        "CaseState",
        "AuditAction",
        "AuditActor",
        "QuestionKey",
    ):
        assert not hasattr(enums, name), f"{name} must not exist in the Layer 0 vocabulary"
