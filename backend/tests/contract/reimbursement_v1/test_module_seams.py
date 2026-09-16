"""Reimbursement v1 module seams stay pure and isolated from TMP-DEV-001."""

from __future__ import annotations

import inspect
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.domain.reimbursement import (
    ApprovalStatus,
    AuthorityThresholdOperator,
    ControlState,
    EscalationType,
    FlowType,
    OrganizationProfile,
    PersonRef,
    PolicySnapshot,
    ProcessingOutcome,
    ProcessingPacket,
    ProcessingResult,
    ReimbursementCase,
    RoleSet,
)
from app.policy.reimbursement.evaluator import evaluate

pytestmark = pytest.mark.v1_contract

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def _profile() -> OrganizationProfile:
    return OrganizationProfile(
        profile_id="DEFAULT-CLB-STUDENT",
        profile_version="1.2.0",
        policy_version="1.2.0",
        owner="TO_BE_CONFIRMED",
        effective_date=None,
        parent_organization="TO_BE_CONFIRMED",
        accounting_regime="TO_BE_CONFIRMED",
        tax_regime_applies=False,
        submission_deadline_business_days=10,
        routine_processing_max_vnd=5_000_000,
        authority_threshold_operator=AuthorityThresholdOperator.GREATER_THAN,
        non_cash_evidence_threshold_vnd=5_000_000,
        non_cash_rule_is_conditional=True,
        aggregation_keys=("vendor_normalized", "transaction_date", "purpose_code"),
        allowed_categories=frozenset({"printing"}),
        conditional_categories=frozenset({"equipment"}),
        prohibited_categories=frozenset({"alcohol"}),
        legally_prohibited_categories=frozenset({"illegal_goods"}),
        roles=RoleSet(
            requester="MEMBER",
            preparer="TREASURER_OR_AGENT",
            approver_within_authority="TREASURER",
            approver_over_threshold="CLUB_CHAIR",
            exception_approvers=("CLUB_CHAIR", "PARENT_ADVISOR"),
            payment_executor="TREASURER_OR_AUTHORIZED_PAYMENT_SYSTEM",
        ),
        raw_ocr_retention_days=30,
        official_record_retention="FOLLOW_PARENT_POLICY_AND_LAW",
    )


def _outcome() -> ProcessingOutcome:
    return ProcessingOutcome(
        outcome_id="OUT-001",
        processing_result=ProcessingResult.ROUTINE_PROCESSED,
        escalation_type=None,
        approval_status=ApprovalStatus.PENDING_HUMAN_APPROVAL,
        eligible_total_vnd=850_000,
        reimbursement_amount_vnd=850_000,
        triggered_rule_ids=("RULE-CALC-002", "RULE-ROUTINE-001"),
        explanation_vi="Hồ sơ tổng hợp đã sẵn sàng để con người xem xét.",
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )


def test_evaluator_signature_is_frozen_and_not_implemented_in_setup() -> None:
    signature = inspect.signature(evaluate)

    assert tuple(signature.parameters) == (
        "case",
        "profile_snapshot",
        "policy_snapshot",
        "control_state",
    )
    assert str(signature.return_annotation) == "ProcessingPacket"

    with pytest.raises(NotImplementedError, match="Lane A"):
        evaluate(
            ReimbursementCase(
                case_id="CASE-001",
                flow_type=FlowType.MEMBER_PAID,
                requester=PersonRef(
                    person_id="P-001", display_name="Synthetic Member", role="MEMBER"
                ),
                submitted_at=datetime(2026, 9, 16, tzinfo=UTC),
                task_or_event="Synthetic event",
                event_end_date=date(2026, 9, 15),
                purpose="Synthetic printing",
                budget_code="BUDGET-001",
                approved_budget_vnd=1_000_000,
                remaining_budget_vnd=1_000_000,
                expense_items=(
                    {
                        "line_id": "LINE-001",
                        "vendor": "Synthetic Vendor",
                        "transaction_date": "2026-09-15",
                        "purpose_code": "PRINT",
                        "description": "Synthetic printing",
                        "category": "printing",
                        "amount_vnd": 850_000,
                        "payment_method": "CARD",
                        "evidence_ids": ["EVD-001"],
                        "suspicion_flags": [],
                    },
                ),
                evidence=(
                    {
                        "evidence_id": "EVD-001",
                        "type": "INVOICE",
                        "file_hash": "sha256-synthetic",
                        "readable": True,
                        "verified": True,
                    },
                ),
                declared_total_vnd=850_000,
                reimbursement_account={
                    "account_name": "Synthetic Member",
                    "bank_name": "Synthetic Bank",
                    "masked_account_number": "***0001",
                },
                paused=False,
            ),
            _profile(),
            PolicySnapshot(
                policy_id="POL-REIMB-CLB",
                policy_version="1.2.0",
                content_hash="sha256-synthetic-policy",
                serialized_policy="synthetic policy snapshot",
            ),
            ControlState.ACTIVE,
        )


def test_packet_enforces_paused_and_routine_output_invariants() -> None:
    packet = ProcessingPacket(
        control_state=ControlState.ACTIVE,
        outcome=_outcome(),
    )
    assert packet.escalation is None

    with pytest.raises(ValueError, match="paused packet"):
        ProcessingPacket(
            control_state=ControlState.PAUSED,
            outcome=_outcome(),
        )

    with pytest.raises(ValueError, match="requires one escalation"):
        ProcessingPacket(
            control_state=ControlState.ACTIVE,
            outcome=ProcessingOutcome(
                outcome_id="OUT-002",
                processing_result=ProcessingResult.ESCALATED,
                escalation_type=EscalationType.FACT_UNKNOWN,
                triggered_rule_ids=("RULE-FACT-001",),
                explanation_vi="Cần thêm chứng từ rõ ràng để tiếp tục xử lý hồ sơ.",
                created_at=datetime(2026, 9, 16, tzinfo=UTC),
            ),
        )


def test_v1_packages_import_without_legacy_or_infrastructure_modules() -> None:
    probe = """
import inspect
import sys

from app.application.reimbursements import ReimbursementProcessingUseCase
from app.domain.reimbursement import ProcessingPacket
from app.persistence.reimbursements import (
    AuditEventRepository,
    CaseRepository,
    ControlEventRepository,
    OutcomeRepository,
)
from app.policy.reimbursement import PolicyEvaluator, evaluate
from app.security import AuthenticatedActor, IdentityProvider

assert inspect.isclass(PolicyEvaluator)
assert inspect.isclass(ReimbursementProcessingUseCase)
assert inspect.isclass(CaseRepository)
assert inspect.isclass(AuditEventRepository)
assert inspect.isclass(ControlEventRepository)
assert inspect.isclass(OutcomeRepository)
assert inspect.isclass(AuthenticatedActor)
assert inspect.isclass(IdentityProvider)
assert tuple(inspect.signature(evaluate).parameters) == (
    "case", "profile_snapshot", "policy_snapshot", "control_state"
)
assert str(inspect.signature(evaluate).return_annotation) == "ProcessingPacket"
assert ProcessingPacket.__name__ == "ProcessingPacket"

for module_name in (
    "fastapi",
    "sqlalchemy",
    "app.core.settings",
    "app.persistence.db",
    "app.domain.models",
    "app.domain.enums",
    "app.policy.evaluator",
    "app.policy.profile",
):
    assert module_name not in sys.modules, module_name
print("reimbursement-v1-seams-ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "reimbursement-v1-seams-ok" in result.stdout
