"""Unit and corpus tests for the reimbursement v1 policy evaluator.

Covers:
- All 29 canonical synthetic cases from policy-forge-baseline/test_cases.json.
- Determinism: every Verify case runs twice with identical output.
- Escalation completeness: every escalated result carries all seven required fields.
- Import boundary: the evaluator imports no framework, persistence, or legacy modules.
- PAUSED control-state behaviour (RULE-SYS-001).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

from app.domain.reimbursement import (
    ApprovalStatus,
    ControlState,
    DuplicateCheckState,
    EscalationType,
    Evidence,
    EvidenceType,
    ExpenseItem,
    FlowType,
    LineAssessment,
    MaskedReimbursementAccount,
    OrganizationProfile,
    PaymentMethod,
    PersonRef,
    PolicySnapshot,
    ProcessingPacket,
    ProcessingResult,
    ReimbursementCase,
)
from app.policy.reimbursement.evaluator import evaluate

# ---------------------------------------------------------------------------
# Test-data paths
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_POLICY_FORGE = _BACKEND_ROOT.parent / "policy-forge-baseline"
_TEST_CASES_PATH = _POLICY_FORGE / "test_cases.json"
_VERIFY_CASES_PATH = _POLICY_FORGE / "verify_cases.json"

# ---------------------------------------------------------------------------
# Load fixtures
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


_TEST_CASES = _load_json(_TEST_CASES_PATH)
_VERIFY_CASES = _load_json(_VERIFY_CASES_PATH)

# Default organisation profile from the Policy Forge YAML (same shape as the
# expanded fixture profile).
_DEFAULT_PROFILE = {
    "profile_id": "DEFAULT-CLB-STUDENT",
    "profile_version": "1.2.0",
    "policy_version": "1.2.0",
    "owner": "TO_BE_CONFIRMED",
    "effective_date": None,
    "parent_organization": "TO_BE_CONFIRMED",
    "accounting_regime": "TO_BE_CONFIRMED",
    "tax_regime_applies": False,
    "currency": "VND",
    "submission_deadline_business_days": 10,
    "routine_processing_max_vnd": 5_000_000,
    "authority_threshold_operator": "greater_than",
    "non_cash_evidence_threshold_vnd": 5_000_000,
    "non_cash_rule_is_conditional": True,
    "aggregation_keys": ("vendor_normalized", "transaction_date", "purpose_code"),
    "allowed_categories": frozenset(
        {"venue", "transport", "printing", "supplies", "communication", "approved_food", "approved_service"}
    ),
    "conditional_categories": frozenset({"gift", "honorarium", "equipment", "late_submission"}),
    "prohibited_categories": frozenset({"alcohol", "tobacco", "personal_expense"}),
    "legally_prohibited_categories": frozenset({"illegal_goods"}),
    "roles": {
        "requester": "MEMBER",
        "preparer": "TREASURER_OR_AGENT",
        "approver_within_authority": "TREASURER",
        "approver_over_threshold": "CLUB_CHAIR",
        "exception_approvers": ("CLUB_CHAIR", "PARENT_ADVISOR"),
        "payment_executor": "TREASURER_OR_AUTHORIZED_PAYMENT_SYSTEM",
    },
    "no_self_approval": True,
    "agent_can_approve": False,
    "agent_can_reject": False,
    "agent_can_transfer_money": False,
    "raw_ocr_retention_days": 30,
    "official_record_retention": "FOLLOW_PARENT_POLICY_AND_LAW",
}

_POLICY_VERSION = "1.2.0"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def default_profile() -> OrganizationProfile:
    return OrganizationProfile.model_validate(_DEFAULT_PROFILE)


@pytest.fixture(scope="session")
def policy_snapshot() -> PolicySnapshot:
    return PolicySnapshot(
        policy_id="POL-REIMB-CLB",
        policy_version=_POLICY_VERSION,
        content_hash="sha256-synthetic-policy-hash",
        serialized_policy="synthetic-policy-content",
    )


def _make_case(concise: dict) -> ReimbursementCase:
    """Build a ReimbursementCase from a concise fixture input dict."""
    flow_type = concise["flow_type"]
    expense = concise.get("expense", {})
    evidence_cfg = concise.get("evidence", {}) or {}

    # Build expense items
    if "items" in expense:
        expense_items = []
        for idx, item in enumerate(expense["items"], start=1):
            suspicion_flags = []
            for fact in evidence_cfg.get("missing_facts", []):
                if fact == "vendor_identity":
                    suspicion_flags.append("VENDOR_IDENTITY_UNVERIFIED")
            if evidence_cfg.get("event_link") is False:
                suspicion_flags.append("NO_EVENT_LINK")
            expense_items.append(
                ExpenseItem(
                    line_id=f"LN-{idx:03d}",
                    vendor=item.get("vendor", "V-SYN-001"),
                    transaction_date=date.fromisoformat(item.get("transaction_date", "2026-08-05")),
                    purpose_code=item.get("purpose_code", "PURP-SYN"),
                    description="Synthetic expense line",
                    category=item["category"],
                    amount_vnd=item["amount_vnd"],
                    payment_method=PaymentMethod(item.get("payment_method", "BANK_TRANSFER")),
                    evidence_ids=("E-1-001",),
                    suspicion_flags=tuple(suspicion_flags),
                    line_assessment=LineAssessment.PENDING,
                )
            )
        declared_total = sum(it.amount_vnd for it in expense_items)
    else:
        suspicion_flags = []
        for fact in evidence_cfg.get("missing_facts", []):
            if fact == "vendor_identity":
                suspicion_flags.append("VENDOR_IDENTITY_UNVERIFIED")
        if evidence_cfg.get("event_link") is False:
            suspicion_flags.append("NO_EVENT_LINK")
        expense_items = [
            ExpenseItem(
                line_id="LN-001",
                vendor=expense.get("vendor", "V-SYN-001"),
                transaction_date=date.fromisoformat(expense.get("transaction_date", "2026-08-05")),
                purpose_code=expense.get("purpose_code", "PURP-SYN"),
                description="Synthetic expense line",
                category=expense["category"],
                amount_vnd=expense["total_vnd"],
                payment_method=PaymentMethod(expense.get("payment_method", "BANK_TRANSFER")),
                evidence_ids=("E-1-001",),
                suspicion_flags=tuple(suspicion_flags),
                line_assessment=LineAssessment.PENDING,
            )
        ]
        declared_total = evidence_cfg.get("declared_total_vnd", expense["total_vnd"])

    # Build evidence records
    evidence_records = []
    readable = evidence_cfg.get("readable", True)
    ocr_confidence = evidence_cfg.get("ocr_confidence", None)
    invoice_total = evidence_cfg.get("evidence_total_vnd", declared_total)
    evidence_records.append(
        Evidence(
            evidence_id="E-1-001",
            type=EvidenceType.INVOICE,
            file_hash="sha256-synthetic-invoice",
            readable=bool(readable),
            verified=True,
            ocr_confidence=ocr_confidence,
            document_number="INV-SYN-001",
            document_date=date(2026, 8, 5),
            amount_vnd=int(invoice_total),
        )
    )

    payment_proof = evidence_cfg.get("payment_proof", True)
    if payment_proof:
        non_cash_verified = evidence_cfg.get("non_cash_verified")
        if non_cash_verified is None:
            pm = expense.get("payment_method", "BANK_TRANSFER")
            non_cash_verified = pm != "CASH"
        evidence_records.append(
            Evidence(
                evidence_id="E-2-001",
                type=EvidenceType.PAYMENT_PROOF,
                file_hash="sha256-synthetic-pay",
                readable=bool(readable),
                verified=True,
                amount_vnd=int(invoice_total),
            )
        )

    prior_approval = evidence_cfg.get("prior_approval_present", False)
    if prior_approval:
        evidence_records.append(
            Evidence(
                evidence_id="E-3-001",
                type=EvidenceType.APPROVAL,
                file_hash="sha256-synthetic-approval",
                readable=True,
                verified=True,
                approval_decision_ids=("APR-SYN-001",),
            )
        )

    if flow_type == FlowType.ADVANCE_SETTLEMENT:
        advance_ref = evidence_cfg.get("advance_reference", "ADV-SYN-001")
        advance_amt = int(concise.get("advance_amount_vnd", 0))
        evidence_records.append(
            Evidence(
                evidence_id="E-4-001",
                type=EvidenceType.ADVANCE_RECORD,
                file_hash="sha256-synthetic-advance",
                readable=bool(readable),
                verified=True,
                document_number=advance_ref,
                amount_vnd=advance_amt,
            )
        )

    duplicate_check_raw = concise.get("duplicate_check", "CLEAR")
    from app.domain.reimbursement import DuplicateCheckState
    duplicate_check = DuplicateCheckState(duplicate_check_raw) if duplicate_check_raw else None

    budget = concise.get("budget", {})
    days_late = concise.get("days_late", 0)
    conflict = concise.get("conflict", False)

    requester_id = concise.get("requester_id", "P-001")
    proposed_id = requester_id if conflict else "P-002"

    return ReimbursementCase(
        case_id=f"CASE-{concise.get('id', 'XXX')}",
        flow_type=flow_type,
        requester=PersonRef(
            person_id=requester_id,
            display_name=f"Synthetic {requester_id}",
            role="MEMBER",
        ),
        submitted_at=datetime(2026, 9, 10, 9, 0, 0, tzinfo=datetime.now().astimezone().tzinfo),
        task_or_event="EVT-SYN-001",
        event_end_date=date(2026, 8, 31),
        purpose="Chi cho hoat dong cau lac bo",
        budget_code="BUD-SYN-001",
        approved_budget_vnd=int(budget.get("approved_vnd", 10_000_000)),
        remaining_budget_vnd=int(budget.get("remaining_vnd", 10_000_000)),
        prior_approval_ids=("APR-SYN-001",) if prior_approval else (),
        prior_payment_reference=concise.get("prior_payment_reference"),
        advance_reference=concise.get("advance_reference", "ADV-SYN-001") if flow_type == FlowType.ADVANCE_SETTLEMENT else None,
        advance_amount_vnd=int(concise.get("advance_amount_vnd", 0)) if flow_type == FlowType.ADVANCE_SETTLEMENT else None,
        expense_items=tuple(expense_items),
        evidence=tuple(evidence_records),
        declared_total_vnd=int(declared_total),
        non_cash_evidence_verified=evidence_cfg.get("non_cash_verified") if "non_cash_verified" in evidence_cfg else None,
        reimbursement_account=MaskedReimbursementAccount(
            account_name="Synthetic Member",
            bank_name="Synthetic Bank",
            masked_account_number="*****0001",
        ),
            proposed_approver=PersonRef(
                person_id=proposed_id,
                display_name=f"Synthetic {proposed_id}",
                role="TREASURER",
            ),
        duplicate_check=duplicate_check,
        submitted_business_days_after_end=int(days_late),
        paused=bool(concise.get("paused", False)),
    )


def _runEvaluate(concise: dict, profile: OrganizationProfile, ps: PolicySnapshot) -> ProcessingPacket:
    case = _make_case(concise)
    # Apply profile overrides if present
    overrides = concise.get("profile_overrides")
    if overrides:
        profile = OrganizationProfile.model_validate({**profile.model_dump(), **overrides})
    ctrl = ControlState.PAUSED if concise.get("paused") else ControlState.ACTIVE
    return evaluate(case, profile, ps, ctrl)


# ---------------------------------------------------------------------------
# 29-canonical-case parameterised test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", _TEST_CASES["cases"])
def test_canonical_case_matches_expected(case: dict, default_profile: OrganizationProfile, policy_snapshot: PolicySnapshot) -> None:
    concise = case["input"]
    expected = case["expected"]
    packet = _runEvaluate(concise, default_profile, policy_snapshot)

    # PAUSED cases
    if expected.get("control_state") == "PAUSED":
        assert packet.control_state is ControlState.PAUSED
        assert packet.outcome is None
        assert packet.escalation is None
        assert expected.get("triggered_rule_ids") == ["RULE-SYS-001"]
        return

    assert packet.control_state is ControlState.ACTIVE
    assert packet.outcome is not None

    # Processing result
    assert packet.outcome.processing_result.value == expected["processing_result"]

    # Triggered rule IDs
    assert list(packet.outcome.triggered_rule_ids) == expected["triggered_rule_ids"]

    if expected["processing_result"] == "ROUTINE_PROCESSED":
        assert packet.outcome.eligible_total_vnd == expected["eligible_total_vnd"]
        if concise["flow_type"] == FlowType.MEMBER_PAID:
            assert packet.outcome.reimbursement_amount_vnd == expected["reimbursement_amount_vnd"]
            assert packet.outcome.amount_to_return_vnd is None
            assert packet.outcome.additional_payment_vnd is None
        else:
            assert packet.outcome.amount_to_return_vnd == expected["amount_to_return_vnd"]
            assert packet.outcome.additional_payment_vnd == expected["additional_payment_vnd"]
            assert packet.outcome.reimbursement_amount_vnd is None
        assert packet.outcome.escalation_type is None
        assert packet.escalation is None

    elif expected["processing_result"] == "ESCALATED":
        assert packet.outcome.escalation_type is not None
        assert packet.outcome.escalation_type.value == expected["escalation_type"]
        assert packet.escalation is not None
        if expected.get("addressee_role"):
            assert packet.escalation.addressee_role == expected["addressee_role"]
        # No calculation fields on escalated results
        assert packet.outcome.eligible_total_vnd is None
        assert packet.outcome.amount_to_return_vnd is None
        assert packet.outcome.additional_payment_vnd is None
        assert packet.outcome.reimbursement_amount_vnd is None


# ---------------------------------------------------------------------------
# Determinism — five Verify cases run twice
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("verify_case", _VERIFY_CASES["cases"])
def test_verify_case_is_deterministic(
    verify_case: dict,
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    concise = next(c["input"] for c in _TEST_CASES["cases"] if c["id"] == verify_case["case_id"])
    first = _runEvaluate(concise, default_profile, policy_snapshot)
    second = _runEvaluate(concise, default_profile, policy_snapshot)
    assert first.model_dump() == second.model_dump()


# ---------------------------------------------------------------------------
# Escalation completeness — every escalated result has all seven fields
# ---------------------------------------------------------------------------


def test_every_escalated_result_has_all_required_escalation_fields(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    for case in _TEST_CASES["cases"]:
        if case["expected"].get("processing_result") != "ESCALATED":
            continue
        packet = _runEvaluate(case["input"], default_profile, policy_snapshot)
        esc = packet.escalation
        assert esc is not None
        assert esc.type is not None
        assert esc.addressee_role.strip()
        assert len(esc.related_evidence) >= 1
        assert len(esc.known_facts) >= 1
        assert len(esc.specific_question) >= 20
        assert len(esc.response_format) >= 5
        assert len(esc.resume_action) >= 10


# ---------------------------------------------------------------------------
# RULE-SYS-001 pause behaviour
# ---------------------------------------------------------------------------


def test_sys_001_halts_before_other_rules(default_profile: OrganizationProfile, policy_snapshot: PolicySnapshot) -> None:
    """A paused case returns PAUSED with no outcome and no escalation."""
    packet = _runEvaluate(
        {"flow_type": "MEMBER_PAID", "expense": {"total_vnd": 100000, "category": "printing"}, "paused": True},
        default_profile,
        policy_snapshot,
    )
    assert packet.control_state is ControlState.PAUSED
    assert packet.outcome is None
    assert packet.escalation is None


def test_sys_001_with_active_control_state_raises(default_profile: OrganizationProfile, policy_snapshot: PolicySnapshot) -> None:
    """A paused case submitted with ACTIVE control state must raise."""
    case = _make_case({"flow_type": "MEMBER_PAID", "expense": {"total_vnd": 100000, "category": "printing"}, "paused": True})
    with pytest.raises(ValueError, match="paused case requires"):
        evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)


# ---------------------------------------------------------------------------
# Calculation arithmetic exactness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", _TEST_CASES["cases"])
def test_calculation_fields_are_arithmetically_exact(
    case: dict,
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    if case["expected"].get("processing_result") != "ROUTINE_PROCESSED":
        return
    packet = _runEvaluate(case["input"], default_profile, policy_snapshot)
    assert packet.outcome.eligible_total_vnd == case["expected"]["eligible_total_vnd"]
    if case["input"]["flow_type"] == FlowType.MEMBER_PAID:
        assert packet.outcome.reimbursement_amount_vnd == case["expected"]["reimbursement_amount_vnd"]
    else:
        advance = int(case["input"].get("advance_amount_vnd", 0))
        eligible = case["expected"]["eligible_total_vnd"]
        assert packet.outcome.amount_to_return_vnd == max(advance - eligible, 0)
        assert packet.outcome.additional_payment_vnd == max(eligible - advance, 0)


# ---------------------------------------------------------------------------
# No automatic approval / rejection / money transfer
# ---------------------------------------------------------------------------


def test_no_result_grants_approval_or_rejection(default_profile: OrganizationProfile, policy_snapshot: PolicySnapshot) -> None:
    """Every agent-produced outcome must remain PENDING_HUMAN_APPROVAL."""
    for case in _TEST_CASES["cases"]:
        if case["expected"].get("control_state") == "PAUSED":
            continue
        packet = _runEvaluate(case["input"], default_profile, policy_snapshot)
        if packet.outcome is None:
            continue
        assert packet.outcome.approval_status is ApprovalStatus.PENDING_HUMAN_APPROVAL


# ---------------------------------------------------------------------------
# Import boundary — no forbidden modules imported
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_evaluator_has_no_runtime_service_dependencies() -> None:
    probe = r"""
import sys
from app.policy.reimbursement.evaluator import evaluate
for module_name in (
    "fastapi",
    "sqlalchemy",
    "app.core.settings",
    "app.persistence",
    "app.policy.evaluator",
    "app.domain.models",
    "app.domain.enums",
):
    assert module_name not in sys.modules, module_name
print("evaluator-import-boundary-ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "evaluator-import-boundary-ok" in result.stdout


# ---------------------------------------------------------------------------
# Evaluator does not mutate its frozen inputs
# ---------------------------------------------------------------------------


def test_evaluator_does_not_mutate_inputs(default_profile: OrganizationProfile, policy_snapshot: PolicySnapshot) -> None:
    concise = _TEST_CASES["cases"][0]["input"]
    case = _make_case(concise)
    case_before = case.model_dump()
    profile_before = default_profile.model_dump()

    evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert case.model_dump() == case_before
    assert default_profile.model_dump() == profile_before


def test_fact_002_rejects_payment_proof_amount_conflict(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
        }
    )
    case = case.model_copy(
        update={
            "evidence": tuple(
                evidence.model_copy(update={"amount_vnd": 900_000})
                if evidence.type is EvidenceType.PAYMENT_PROOF
                else evidence
                for evidence in case.evidence
            )
        }
    )

    packet = evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert packet.outcome is not None
    assert packet.outcome.triggered_rule_ids == ("RULE-FACT-002",)


def test_fact_003_requires_verified_evidence(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
        }
    )
    case = case.model_copy(
        update={
            "evidence": tuple(
                evidence.model_copy(update={"verified": False})
                for evidence in case.evidence
            )
        }
    )

    packet = evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert packet.outcome is not None
    assert packet.outcome.triggered_rule_ids == ("RULE-FACT-003",)


def test_tax_001_uses_related_purchase_totals(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    packet = _runEvaluate(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"items": [
                {
                    "vendor": "A",
                    "transaction_date": "2026-08-05",
                    "purpose_code": "ONE",
                    "category": "printing",
                    "amount_vnd": 3_000_000,
                },
                {
                    "vendor": "B",
                    "transaction_date": "2026-08-05",
                    "purpose_code": "TWO",
                    "category": "printing",
                    "amount_vnd": 3_000_000,
                },
            ]},
            "evidence": {"non_cash_verified": False},
            "profile_overrides": {"routine_processing_max_vnd": 10_000_000},
        },
        default_profile,
        policy_snapshot,
    )

    assert packet.outcome is not None
    assert packet.outcome.processing_result is ProcessingResult.ROUTINE_PROCESSED


def test_auth_001_uses_profile_owned_over_threshold_role(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    profile = default_profile.model_copy(
        update={
            "roles": default_profile.roles.model_copy(
                update={"approver_over_threshold": "FINANCE_COMMITTEE"}
            )
        }
    )
    packet = _runEvaluate(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 5_000_001, "category": "printing"},
        },
        profile,
        policy_snapshot,
    )

    assert packet.escalation is not None
    assert packet.escalation.addressee_role == "FINANCE_COMMITTEE"


def test_duplicate_escalation_references_case_evidence(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
            "duplicate_check": "NOT_RUN",
        }
    )

    packet = evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert packet.escalation is not None
    assert packet.escalation.related_evidence == tuple(
        evidence.evidence_id for evidence in case.evidence
    )


def test_fact_001_rejects_unreadable_payment_proof(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
        }
    )
    case = case.model_copy(
        update={
            "evidence": tuple(
                evidence.model_copy(update={"readable": False})
                if evidence.type is EvidenceType.PAYMENT_PROOF
                else evidence
                for evidence in case.evidence
            )
        }
    )

    packet = evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert packet.outcome is not None
    assert packet.outcome.triggered_rule_ids == ("RULE-FACT-001",)


def test_fact_003_rejects_financial_evidence_without_amount(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
        }
    )
    case = case.model_copy(
        update={
            "evidence": tuple(
                evidence.model_copy(update={"amount_vnd": None})
                if evidence.type
                in (EvidenceType.INVOICE, EvidenceType.PAYMENT_PROOF)
                else evidence
                for evidence in case.evidence
            )
        }
    )

    packet = evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert packet.outcome is not None
    assert packet.outcome.triggered_rule_ids == ("RULE-FACT-003",)


def test_outcome_id_uses_the_complete_case_id(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
        }
    )
    first_packet = evaluate(
        case.model_copy(update={"case_id": "CASE-A-12345678"}),
        default_profile,
        policy_snapshot,
        ControlState.ACTIVE,
    )
    second_packet = evaluate(
        case.model_copy(update={"case_id": "CASE-B-12345678"}),
        default_profile,
        policy_snapshot,
        ControlState.ACTIVE,
    )

    assert first_packet.outcome is not None
    assert second_packet.outcome is not None
    assert first_packet.outcome.outcome_id == "OUT-CASE-A-12345678"
    assert second_packet.outcome.outcome_id == "OUT-CASE-B-12345678"


def test_fact_003_rejects_missing_line_evidence_reference(
    default_profile: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
) -> None:
    case = _make_case(
        {
            "flow_type": "MEMBER_PAID",
            "expense": {"total_vnd": 1_000_000, "category": "printing"},
        }
    )
    item = case.expense_items[0].model_copy(update={"evidence_ids": ("E-LINE",)})
    case = case.model_copy(update={"expense_items": (item,)})

    packet = evaluate(case, default_profile, policy_snapshot, ControlState.ACTIVE)

    assert packet.outcome is not None
    assert packet.outcome.triggered_rule_ids == ("RULE-FACT-003",)
