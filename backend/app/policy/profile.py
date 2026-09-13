"""The single immutable temporary development profile for Layer 0.

There is exactly one profile. No factory, setting, request parameter, or
fixture can select or alter it.
"""

from __future__ import annotations

from app.domain.enums import (
    DataClass,
    EvidenceStatus,
    ProfileSource,
    TemporaryCategory,
    WorkflowValidationStatus,
)
from app.domain.models import TemporaryProfile

TMP_DEV_001_PROFILE = TemporaryProfile(
    profile_id="TMP-DEV-001",
    profile_source=ProfileSource.TEMPORARY_DEVELOPMENT,
    data_class=DataClass.SYNTHETIC,
    workflow_validation_status=WorkflowValidationStatus.UNVALIDATED,
    allowed_categories=frozenset({TemporaryCategory.TEST_ALLOWED}),
    required_evidence_status=EvidenceStatus.PRESENT,
    auto_approve_limit_vnd=1000,
)
