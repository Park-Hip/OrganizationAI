"""Contract tests for the Layer 0 import boundary."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]

_PROBE = """
import sys

import app.domain
import app.policy

for module_name in ("fastapi", "sqlalchemy", "app.core.settings", "app.persistence"):
    assert module_name not in sys.modules, f"{module_name} was imported by the contract"

from app.domain.enums import (
    DataClass,
    EvidenceStatus,
    ProfileSource,
    TemporaryCategory,
    WorkflowValidationStatus,
)
from app.policy.profile import TMP_DEV_001_PROFILE

assert TMP_DEV_001_PROFILE.profile_id == "TMP-DEV-001"
assert TMP_DEV_001_PROFILE.profile_source is ProfileSource.TEMPORARY_DEVELOPMENT
assert TMP_DEV_001_PROFILE.data_class is DataClass.SYNTHETIC
assert (
    TMP_DEV_001_PROFILE.workflow_validation_status
    is WorkflowValidationStatus.UNVALIDATED
)
assert TMP_DEV_001_PROFILE.allowed_categories == frozenset({TemporaryCategory.TEST_ALLOWED})
assert TMP_DEV_001_PROFILE.required_evidence_status is EvidenceStatus.PRESENT

from app.domain.models import CaseSubmission
from app.policy import normalization as l1

assert l1.MISSING_FIELD_PATHS == (
    "purpose",
    "expense.category",
    "expense.description",
    "expense.amount_vnd",
    "expense.expense_date",
    "expense.evidence_status",
)

blank_case = CaseSubmission(
    case_id="PROBE-01",
    submitted_at="2026-01-15T09:00:00Z",
    requester_role=None,
    purpose="   ",
    expense=None,
)
assert l1.normalize_case(blank_case).purpose is None
assert l1.first_missing_field(l1.normalize_case(blank_case)) == "purpose"

for module_name in ("fastapi", "sqlalchemy", "app.core.settings", "app.persistence"):
    assert module_name not in sys.modules, f"{module_name} was imported by Layer 1"
print("import-boundary-ok")
"""


def test_domain_contract_does_not_boot_fastapi_or_a_database() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "import-boundary-ok" in result.stdout
