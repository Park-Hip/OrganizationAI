"""Reimbursement v1 module seams stay pure and isolated from TMP-DEV-001."""

from __future__ import annotations

import inspect
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import app.policy.reimbursement.evaluator as evaluator_module
from app.domain.reimbursement import (
    ApprovalStatus,
    AuditActorType,
    AuditEvent,
    AuditEventType,
    AuthorityThresholdOperator,
    ControlState,
    EscalationType,
    Evidence,
    ExpenseItem,
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


def _member_paid_case(*, paused: bool = False) -> ReimbursementCase:
    return ReimbursementCase(
        case_id="CASE-001",
        flow_type=FlowType.MEMBER_PAID,
        requester=PersonRef(person_id="P-001", display_name="Synthetic Member", role="MEMBER"),
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
        paused=paused,
    )


def _policy_snapshot() -> PolicySnapshot:
    return PolicySnapshot(
        policy_id="POL-REIMB-CLB",
        policy_version="1.2.0",
        content_hash="sha256-synthetic-policy",
        serialized_policy="synthetic policy snapshot",
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
            _member_paid_case(),
            _profile(),
            _policy_snapshot(),
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

    with pytest.raises(ValueError, match="must not contain proposed calculations"):
        ProcessingOutcome(
            outcome_id="OUT-003",
            processing_result=ProcessingResult.ESCALATED,
            escalation_type=EscalationType.FACT_UNKNOWN,
            eligible_total_vnd=0,
            triggered_rule_ids=("RULE-FACT-001",),
            explanation_vi="Additional evidence is required before processing can continue.",
            created_at=datetime(2026, 9, 16, tzinfo=UTC),
        )


def test_profile_and_policy_snapshots_reject_schema_incompatible_versions() -> None:
    profile_payload = _profile().model_dump()

    with pytest.raises(ValueError, match="semantic versioning"):
        OrganizationProfile.model_validate(profile_payload | {"profile_version": "draft"})

    with pytest.raises(ValueError, match="aggregation keys must be unique"):
        OrganizationProfile.model_validate(
            profile_payload | {"aggregation_keys": ("vendor", "vendor")}
        )

    with pytest.raises(ValueError, match="semantic versioning"):
        PolicySnapshot(
            policy_id="POL-REIMB-CLB",
            policy_version="draft",
            content_hash="sha256-synthetic-policy",
            serialized_policy="synthetic policy snapshot",
        )


def test_v1_structural_scalars_reject_coercible_values() -> None:
    profile_payload = _profile().model_dump()
    profile_payload.update(
        {
            "tax_regime_applies": "false",
            "submission_deadline_business_days": True,
            "routine_processing_max_vnd": "5000000",
            "non_cash_evidence_threshold_vnd": True,
            "non_cash_rule_is_conditional": "true",
            "no_self_approval": "true",
            "agent_can_approve": "false",
            "agent_can_reject": "false",
            "agent_can_transfer_money": "false",
            "raw_ocr_retention_days": "30",
        }
    )
    with pytest.raises(ValueError):
        OrganizationProfile.model_validate(profile_payload)

    with pytest.raises(ValueError):
        ExpenseItem(
            line_id="LINE-001",
            vendor="Synthetic Vendor",
            transaction_date=date(2026, 9, 15),
            purpose_code="PRINT",
            description="Synthetic printing",
            category="printing",
            amount_vnd=True,
            tax_amount_vnd="0",
            payment_method="CARD",
            evidence_ids=("EVD-001",),
            suspicion_flags=(),
        )

    with pytest.raises(ValueError):
        Evidence(
            evidence_id="EVD-001",
            type="INVOICE",
            file_hash="sha256-synthetic",
            readable="true",
            verified="true",
            amount_vnd=True,
        )

    evidence_payload = {
        "evidence_id": "EVD-001",
        "type": "INVOICE",
        "file_hash": "sha256-synthetic",
        "readable": True,
        "verified": True,
    }
    for ocr_confidence in (True, "0.9"):
        with pytest.raises(ValueError):
            Evidence.model_validate(evidence_payload | {"ocr_confidence": ocr_confidence})

    case_payload = ReimbursementCase(
        case_id="CASE-001",
        flow_type=FlowType.MEMBER_PAID,
        requester=PersonRef(person_id="P-001", display_name="Synthetic Member", role="MEMBER"),
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
    ).model_dump()
    case_payload.update(
        {
            "approved_budget_vnd": True,
            "remaining_budget_vnd": "1000000",
            "flow_type": "ADVANCE_SETTLEMENT",
            "advance_reference": "ADV-001",
            "advance_amount_vnd": True,
            "declared_total_vnd": True,
            "non_cash_evidence_verified": "false",
            "submitted_business_days_after_end": "1",
            "paused": "false",
        }
    )
    with pytest.raises(ValueError):
        ReimbursementCase.model_validate(case_payload)

    outcome_payload = _outcome().model_dump()
    outcome_payload.update(
        {
            "eligible_total_vnd": True,
            "amount_to_return_vnd": "0",
            "additional_payment_vnd": True,
            "reimbursement_amount_vnd": "850000",
        }
    )
    with pytest.raises(ValueError):
        ProcessingOutcome.model_validate(outcome_payload)


def test_v1_timestamps_require_timezones() -> None:
    with pytest.raises(ValueError):
        ReimbursementCase.model_validate(
            _member_paid_case().model_dump() | {"submitted_at": datetime(2026, 9, 16)}
        )

    with pytest.raises(ValueError):
        ProcessingOutcome.model_validate(
            _outcome().model_dump() | {"created_at": datetime(2026, 9, 16)}
        )

    with pytest.raises(ValueError):
        AuditEvent(
            event_id="AUD-001",
            timestamp=datetime(2026, 9, 16),
            actor_id="AGENT-001",
            actor_type=AuditActorType.AGENT,
            policy_version="1.2.0",
            event_type=AuditEventType.RECEIVED,
            input_hash="sha256-synthetic",
            triggered_rule_ids=(),
            explanation="Synthetic receipt of a reimbursement case.",
        )


def test_evaluator_enforces_case_control_and_flow_output_invariants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid_member_outcome = ProcessingOutcome(
        outcome_id="OUT-004",
        processing_result=ProcessingResult.ROUTINE_PROCESSED,
        escalation_type=None,
        eligible_total_vnd=850_000,
        amount_to_return_vnd=0,
        additional_payment_vnd=0,
        reimbursement_amount_vnd=850_000,
        triggered_rule_ids=("RULE-CALC-002",),
        explanation_vi="A valid result with incompatible calculations.",
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )
    monkeypatch.setattr(
        evaluator_module,
        "_evaluate_policy",
        lambda *_: ProcessingPacket(
            control_state=ControlState.ACTIVE,
            outcome=invalid_member_outcome,
        ),
    )

    with pytest.raises(ValueError, match="MEMBER_PAID must not contain advance calculations"):
        evaluate(_member_paid_case(), _profile(), _policy_snapshot(), ControlState.ACTIVE)

    mismatched_profile = _profile().model_copy(update={"policy_version": "1.3.0"})
    with pytest.raises(ValueError, match="same policy version"):
        evaluate(_member_paid_case(), mismatched_profile, _policy_snapshot(), ControlState.ACTIVE)

    with pytest.raises(ValueError, match="paused case requires"):
        evaluate(
            _member_paid_case(paused=True), _profile(), _policy_snapshot(), ControlState.ACTIVE
        )

    def policy_core_must_not_run(*_: object) -> ProcessingPacket:
        raise AssertionError("a paused case must not reach policy evaluation")

    monkeypatch.setattr(evaluator_module, "_evaluate_policy", policy_core_must_not_run)
    paused_packet = evaluate(
        _member_paid_case(paused=True),
        _profile(),
        _policy_snapshot(),
        ControlState.PAUSED,
    )
    assert paused_packet.control_state is ControlState.PAUSED
    assert paused_packet.outcome is None
    assert paused_packet.escalation is None

    monkeypatch.setattr(
        evaluator_module,
        "_evaluate_policy",
        lambda *_: ProcessingPacket(control_state=ControlState.PAUSED),
    )
    with pytest.raises(ValueError, match="control state must match"):
        evaluate(_member_paid_case(), _profile(), _policy_snapshot(), ControlState.ACTIVE)

    advance_case = ReimbursementCase.model_validate(
        _member_paid_case().model_dump()
        | {
            "flow_type": FlowType.ADVANCE_SETTLEMENT,
            "advance_reference": "ADV-001",
            "advance_amount_vnd": 850_000,
        }
    )
    monkeypatch.setattr(
        evaluator_module,
        "_evaluate_policy",
        lambda *_: ProcessingPacket(control_state=ControlState.ACTIVE, outcome=_outcome()),
    )
    with pytest.raises(ValueError, match="ADVANCE_SETTLEMENT requires both advance calculations"):
        evaluate(advance_case, _profile(), _policy_snapshot(), ControlState.ACTIVE)


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
from app.policy.reimbursement import evaluate
from app.security import AuthenticatedActor, IdentityProvider

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
