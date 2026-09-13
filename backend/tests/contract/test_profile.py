"""Contract tests for the sole frozen temporary profile."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    DataClass,
    EvidenceStatus,
    ProfileSource,
    TemporaryCategory,
    WorkflowValidationStatus,
)
from app.policy.profile import TMP_DEV_001_PROFILE


def test_profile_matches_the_frozen_temporary_policy_exactly() -> None:
    assert TMP_DEV_001_PROFILE.profile_id == "TMP-DEV-001"
    assert TMP_DEV_001_PROFILE.profile_source is ProfileSource.TEMPORARY_DEVELOPMENT
    assert TMP_DEV_001_PROFILE.data_class is DataClass.SYNTHETIC
    assert TMP_DEV_001_PROFILE.workflow_validation_status is WorkflowValidationStatus.UNVALIDATED
    assert TMP_DEV_001_PROFILE.allowed_categories == frozenset({TemporaryCategory.TEST_ALLOWED})
    assert TMP_DEV_001_PROFILE.required_evidence_status is EvidenceStatus.PRESENT
    assert TMP_DEV_001_PROFILE.auto_approve_limit_vnd == 1000


def test_profile_assignment_to_a_field_fails() -> None:
    with pytest.raises(ValidationError):
        TMP_DEV_001_PROFILE.profile_id = "CHANGED"  # type: ignore[misc]


def test_profile_allowed_categories_cannot_be_mutated() -> None:
    assert isinstance(TMP_DEV_001_PROFILE.allowed_categories, frozenset)
    assert not hasattr(TMP_DEV_001_PROFILE.allowed_categories, "add")


def test_profile_exports_one_constant_without_factory_or_selector() -> None:
    import app.policy as policy_module

    assert policy_module.TMP_DEV_001_PROFILE is TMP_DEV_001_PROFILE
    assert not hasattr(policy_module, "profile_factory")
    assert not hasattr(policy_module, "get_profile")
