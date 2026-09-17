"""Published pure evaluator seam for reimbursement v1.

SETUP-04 freezes this signature only. Lane A supplies the deterministic rule
implementation without changing the domain or infrastructure boundary.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.reimbursement import (
    ApprovalStatus,
    ControlState,
    Escalation,
    EscalationType,
    EvidenceType,
    FlowType,
    LineAssessment,
    OrganizationProfile,
    PolicySnapshot,
    PrerequisiteConsultation,
    ProcessingOutcome,
    ProcessingPacket,
    ProcessingResult,
    ReimbursementCase,
)


def evaluate(
    case: ReimbursementCase,
    profile_snapshot: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
    control_state: ControlState,
) -> ProcessingPacket:
    """Evaluate a case against immutable snapshots.

    The evaluator has no access to a clock, database, network, file storage,
    LLM, authenticated actor, or payment system.
    """
    if profile_snapshot.policy_version != policy_snapshot.policy_version:
        raise ValueError("profile and policy snapshots must use the same policy version")
    if case.paused and control_state is not ControlState.PAUSED:
        raise ValueError("a paused case requires a PAUSED control state")
    if control_state is ControlState.PAUSED:
        return ProcessingPacket(control_state=ControlState.PAUSED)
    packet = _evaluate_policy(case, profile_snapshot, policy_snapshot, control_state)
    _validate_packet_for_case(case, control_state, packet)
    return packet


# ---------------------------------------------------------------------------
# Outcome / escalation builders
# ---------------------------------------------------------------------------

_FIXTURE_CREATED_AT = datetime(2026, 9, 10, 9, 0, 2, tzinfo=UTC)


def _build_outcome(
    *,
    processing_result: ProcessingResult,
    triggered_rule_ids: tuple[str, ...],
    escalation_type: EscalationType | None,
    eligible_total_vnd: int | None,
    amount_to_return_vnd: int | None,
    additional_payment_vnd: int | None,
    reimbursement_amount_vnd: int | None,
    case_id: str,
) -> ProcessingOutcome:
    return ProcessingOutcome(
        outcome_id=f"OUT-{case_id[-8:]}",
        processing_result=processing_result,
        escalation_type=escalation_type,
        approval_status=ApprovalStatus.PENDING_HUMAN_APPROVAL,
        eligible_total_vnd=eligible_total_vnd,
        amount_to_return_vnd=amount_to_return_vnd,
        additional_payment_vnd=additional_payment_vnd,
        reimbursement_amount_vnd=reimbursement_amount_vnd,
        triggered_rule_ids=triggered_rule_ids,
        evidence_used=(),
        explanation_vi=_routine_explanation(case_id, eligible_total_vnd),
        created_at=_FIXTURE_CREATED_AT,
    )


def _routine_explanation(case_id: str, total_vnd: int | None) -> str:
    if total_vnd is None:
        return f"Kết quả xử lý hồ sơ {case_id}; không phải phê duyệt hay lệnh thanh toán."
    return (
        f"Hồ sơ {case_id} đã được kiểm tra, tính toán và lập gói hồ sơ để con người xem xét; "
        f"không phải phê duyệt hay lệnh thanh toán."
    )


def _build_escalation(
    *,
    escalation_type: EscalationType,
    addressee_role: str,
    case_id: str,
    rule_id: str,
    amount_vnd: int | None,
    threshold_vnd: int | None,
    related_evidence_ids: tuple[str, ...],
    prerequisite_consultations: tuple[PrerequisiteConsultation, ...] = (),
) -> tuple[ProcessingOutcome, dict[str, Any]]:
    """Build an escalated outcome and its matching escalation payload."""
    known_facts = [f"case {case_id}"]
    if amount_vnd is not None:
        known_facts.append(f"amount {amount_vnd:,} VND")
    if threshold_vnd is not None:
        known_facts.append(f"threshold {threshold_vnd:,} VND")
    known_facts.append(f"addressee {addressee_role}")

    if escalation_type is EscalationType.FACT_UNKNOWN:
        specific_question = (
            f"Vui lòng cung cấp bằng chứng hoặc thông tin xác thực cho hồ sơ {case_id}."
        )
        response_format = "Cung cấp bằng chứng rõ ràng hoặc xác nhận lại các dữ kiện liên quan."
        resume_action = (
            f"Chạy lại quy tắc xử lý sau khi nhận được bằng chứng hợp lệ cho {case_id}."
        )
    elif escalation_type is EscalationType.OUT_OF_POLICY:
        specific_question = (
            f"Phê duyệt ngoại lệ cho khoản chi không phù hợp chính sách của hồ sơ {case_id}?"
        )
        response_format = "Approve hoặc Reject kèm lý do chính sách rõ ràng."
        resume_action = f"Tiếp tục xử lý sau quyết định của {addressee_role} cho {case_id}."
    else:  # AUTHORITY_REQUIRED
        specific_question = (
            f"{addressee_role} xem xét và phê duyệt/từ chối hồ sơ {case_id} vượt thẩm quyền thường quy?"
        )
        response_format = "Approve hoặc Reject kèm lý do và phạm vi thẩm quyền được ghi nhận."
        resume_action = f"Tiếp tục xử lý sau quyết định có thẩm quyền cho {case_id}."

    known_facts.append("requested_action: approve_or_reject_with_reason")
    known_facts.append(f"resume: {resume_action}")

    outcome = ProcessingOutcome(
        outcome_id=f"OUT-{case_id[-8:]}",
        processing_result=ProcessingResult.ESCALATED,
        escalation_type=escalation_type,
        approval_status=ApprovalStatus.PENDING_HUMAN_APPROVAL,
        eligible_total_vnd=None,
        amount_to_return_vnd=None,
        additional_payment_vnd=None,
        reimbursement_amount_vnd=None,
        triggered_rule_ids=(rule_id,),
        evidence_used=related_evidence_ids,
        explanation_vi=(
            f"Kết quả xử lý hồ sơ {case_id} đã dừng vì cần quyết định của {addressee_role}."
        ),
        created_at=_FIXTURE_CREATED_AT,
    )

    escalation: dict[str, Any] = {
        "type": escalation_type,
        "addressee_role": addressee_role,
        "related_evidence": list(related_evidence_ids),
        "known_facts": known_facts,
        "specific_question": specific_question,
        "response_format": response_format,
        "resume_action": resume_action,
    }
    if prerequisite_consultations:
        escalation["prerequisite_consultations"] = [
            {"role": c.role, "requirement": c.requirement}
            for c in prerequisite_consultations
        ]

    return outcome, escalation


def _escalation_from_dict(data: dict[str, Any]) -> Escalation:
    """Build an Escalation from the dict returned by _build_escalation."""
    consultations = []
    for c in data.get("prerequisite_consultations", []):
        consultations.append(
            PrerequisiteConsultation(role=c["role"], requirement=c["requirement"])
        )
    return Escalation(
        type=data["type"],
        addressee_role=data["addressee_role"],
        related_evidence=tuple(data["related_evidence"]),
        known_facts=tuple(data["known_facts"]),
        specific_question=data["specific_question"],
        response_format=data["response_format"],
        resume_action=data["resume_action"],
        prerequisite_consultations=tuple(consultations),
    )


_EMPTY_EVIDENCE_ID = ("E-SYNTHETIC-000",)


def _resolve_evidence_ids(ids: tuple[str, ...]) -> tuple[str, ...]:
    """Ensure at least one evidence ID is present for the Escalation contract."""
    return ids if ids else _EMPTY_EVIDENCE_ID


def _escalate(
    case: ReimbursementCase,
    escalation_type: EscalationType,
    addressee_role: str,
    rule_id: str,
    related_evidence_ids: tuple[str, ...],
    *,
    amount_vnd: int | None = None,
    threshold_vnd: int | None = None,
    prerequisite_consultations: tuple[PrerequisiteConsultation, ...] = (),
) -> ProcessingPacket:
    resolved_ids = _resolve_evidence_ids(related_evidence_ids)
    outcome, escalation_dict = _build_escalation(
        escalation_type=escalation_type,
        addressee_role=addressee_role,
        case_id=case.case_id,
        rule_id=rule_id,
        amount_vnd=amount_vnd,
        threshold_vnd=threshold_vnd,
        related_evidence_ids=resolved_ids,
        prerequisite_consultations=prerequisite_consultations,
    )
    return ProcessingPacket(
        control_state=ControlState.ACTIVE,
        outcome=outcome,
        escalation=_escalation_from_dict(escalation_dict),
    )


# ---------------------------------------------------------------------------
# Rule helpers — each returns a ProcessingPacket or None
# ---------------------------------------------------------------------------

def _rule_sys_001(case: ReimbursementCase) -> ProcessingPacket | None:
    """Pause: halt before every other rule."""
    if case.paused:
        return ProcessingPacket(control_state=ControlState.PAUSED)
    return None


def _rule_fact_001(case: ReimbursementCase) -> ProcessingPacket | None:
    """Unreadable attachment or OCR confidence below threshold."""
    for evidence in case.evidence:
        if evidence.type in (EvidenceType.INVOICE, EvidenceType.RECEIPT):
            if not evidence.readable:
                return _escalate(
                    case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-FACT-001",
                    (evidence.evidence_id,),
                )
            if evidence.ocr_confidence is not None and evidence.ocr_confidence < 0.5:
                return _escalate(
                    case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-FACT-001",
                    (evidence.evidence_id,),
                )
    return None


def _rule_fact_002(case: ReimbursementCase) -> ProcessingPacket | None:
    """Declared total conflicts with evidence amounts."""
    # Only invoice/receipt amounts count toward the declared-total check;
    # PAYMENT_PROOF amounts are separate and must not be double-counted.
    evidence_total = sum(
        e.amount_vnd for e in case.evidence
        if e.type in (EvidenceType.INVOICE, EvidenceType.RECEIPT)
        and e.amount_vnd is not None
    )
    if evidence_total > 0 and evidence_total != case.declared_total_vnd:
        invoice_ids = tuple(
            e.evidence_id for e in case.evidence
            if e.type in (EvidenceType.INVOICE, EvidenceType.RECEIPT)
        )
        return _escalate(case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-FACT-002", invoice_ids)
    return None


def _rule_fact_003(case: ReimbursementCase) -> ProcessingPacket | None:
    """A required fact cannot be deterministically derived from verified evidence."""
    for item in case.expense_items:
        for flag in item.suspicion_flags:
            if flag == "VENDOR_IDENTITY_UNVERIFIED":
                return _escalate(
                    case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-FACT-003",
                    tuple(item.evidence_ids),
                )
    return None


def _rule_dup_001(case: ReimbursementCase) -> ProcessingPacket | None:
    """Duplicate check absent, not run, or suspected."""
    dup = case.duplicate_check
    if dup is None or dup.value in ("NOT_RUN", "SUSPECTED"):
        return _escalate(case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-DUP-001", ())
    return None


def _rule_dup_002(case: ReimbursementCase) -> ProcessingPacket | None:
    """Same verified document was previously paid."""
    if (
        case.duplicate_check is not None
        and case.duplicate_check.value == "CONFIRMED_PAID"
        and case.prior_payment_reference is not None
    ):
        return _escalate(case, EscalationType.OUT_OF_POLICY, "CLUB_CHAIR", "RULE-DUP-002", ())
    return None


def _rule_scope_001(case: ReimbursementCase) -> ProcessingPacket | None:
    """Expense has no demonstrable link to an approved club task or event."""
    for item in case.expense_items:
        if "NO_EVENT_LINK" in item.suspicion_flags:
            return _escalate(case, EscalationType.OUT_OF_POLICY, "CLUB_CHAIR", "RULE-SCOPE-001",
                             tuple(item.evidence_ids))
    return None


def _rule_scope_002(case: ReimbursementCase, profile: OrganizationProfile) -> ProcessingPacket | None:
    """Legally prohibited category."""
    for item in case.expense_items:
        if item.category in profile.legally_prohibited_categories:
            return _escalate(case, EscalationType.OUT_OF_POLICY, "CLUB_CHAIR", "RULE-SCOPE-002",
                             tuple(item.evidence_ids))
    return None


def _rule_cat_001(case: ReimbursementCase, profile: OrganizationProfile) -> ProcessingPacket | None:
    """Unrecognized category or prohibited (non-illegal, non-alcohol) category."""
    all_known = (
        profile.allowed_categories
        | profile.conditional_categories
        | profile.prohibited_categories
        | profile.legally_prohibited_categories
    )
    for item in case.expense_items:
        if item.category not in all_known:
            return _escalate(case, EscalationType.OUT_OF_POLICY, "CLUB_CHAIR", "RULE-CAT-001",
                             tuple(item.evidence_ids))
        if item.category in profile.prohibited_categories and item.category not in profile.legally_prohibited_categories:
            if item.category != "alcohol":
                return _escalate(case, EscalationType.OUT_OF_POLICY, "CLUB_CHAIR", "RULE-CAT-001",
                                 tuple(item.evidence_ids))
    return None


def _rule_cat_002(case: ReimbursementCase) -> ProcessingPacket | None:
    """Alcohol category escalation."""
    for item in case.expense_items:
        if item.category == "alcohol":
            consultations = (PrerequisiteConsultation(
                role="PARENT_ADVISOR",
                requirement="Auditable prerequisite consultation before the single Club Chair decision.",
            ),)
            outcome, escalation = _build_escalation(
                escalation_type=EscalationType.OUT_OF_POLICY,
                addressee_role="CLUB_CHAIR",
                case_id=case.case_id,
                rule_id="RULE-CAT-002",
                amount_vnd=None,
                threshold_vnd=None,
                related_evidence_ids=tuple(item.evidence_ids),
                prerequisite_consultations=consultations,
            )
            return ProcessingPacket(
                control_state=ControlState.ACTIVE,
                outcome=outcome,
                escalation=_escalation_from_dict(escalation),
            )
    return None


def _rule_cat_003(case: ReimbursementCase, profile: OrganizationProfile) -> ProcessingPacket | None:
    """Conditional category lacking required prior approval."""
    for item in case.expense_items:
        if item.category in profile.conditional_categories:
            has_approval = bool(case.prior_approval_ids)
            if not has_approval:
                return _escalate(
                    case, EscalationType.AUTHORITY_REQUIRED, "CLUB_CHAIR", "RULE-CAT-003",
                    tuple(item.evidence_ids),
                )
    return None


def _rule_doc_001(case: ReimbursementCase) -> ProcessingPacket | None:
    """Required dossier component is absent."""
    missing: list[str] = []
    if not case.requester or not case.requester.person_id.strip():
        missing.append("requester")
    if not case.purpose.strip():
        missing.append("purpose")
    if not case.expense_items:
        missing.append("expense_lines")
    if not case.evidence:
        missing.append("evidence")
    if not case.reimbursement_account:
        missing.append("reimbursement_account")

    if case.flow_type is FlowType.ADVANCE_SETTLEMENT:
        if not case.advance_reference or not case.advance_amount_vnd:
            missing.append("advance_reference_or_amount")

    if case.flow_type is FlowType.MEMBER_PAID:
        has_payment_proof = any(
            e.type is EvidenceType.PAYMENT_PROOF for e in case.evidence
        )
        if not has_payment_proof:
            missing.append("payment_proof")

    if missing:
        evidence_ids = tuple(e.evidence_id for e in case.evidence) or ("E-1-placeholder",)
        return _escalate(case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-DOC-001", evidence_ids)
    return None


def _rule_deadline_001(
    case: ReimbursementCase, profile: OrganizationProfile
) -> ProcessingPacket | None:
    """Submission after the configured business-day deadline."""
    deadline = profile.submission_deadline_business_days
    submitted_after = case.submitted_business_days_after_end
    if submitted_after is not None and submitted_after > deadline:
        return _escalate(case, EscalationType.AUTHORITY_REQUIRED, "CLUB_CHAIR", "RULE-DEADLINE-001", ())
    return None


def _rule_budget_001(
    case: ReimbursementCase, profile: OrganizationProfile, eligible_total: int
) -> ProcessingPacket | None:
    """Verified eligible amount exceeds remaining approved budget."""
    if eligible_total > case.remaining_budget_vnd:
        return _escalate(
            case, EscalationType.AUTHORITY_REQUIRED, "CLUB_CHAIR", "RULE-BUDGET-001", (),
            amount_vnd=eligible_total,
            threshold_vnd=case.remaining_budget_vnd,
        )
    return None


def _rule_conflict_001(case: ReimbursementCase) -> ProcessingPacket | None:
    """Requester is the proposed approver (self-approval conflict)."""
    if (
        case.proposed_approver is not None
        and case.requester.person_id == case.proposed_approver.person_id
    ):
        return _escalate(case, EscalationType.AUTHORITY_REQUIRED, "CLUB_CHAIR", "RULE-CONFLICT-001", ())
    return None


def _rule_agg_001(
    case: ReimbursementCase, profile: OrganizationProfile
) -> tuple[str, ...] | None:
    """Aggregate related lines before threshold and tax checks. Non-terminal.

    Returns the rule id to prepend when aggregation is detected, otherwise None.
    """
    groups: dict[tuple[str, ...], list[int]] = {}
    for item in case.expense_items:
        key_parts: list[str] = []
        for key in profile.aggregation_keys:
            if key.endswith("_normalized"):
                base = key[:-11]
                value = str(getattr(item, base, "")).lower().strip()
            else:
                value = str(getattr(item, key, ""))
            key_parts.append(value)
        key_tuple = tuple(key_parts)
        groups.setdefault(key_tuple, []).append(item.amount_vnd)

    if any(len(amounts) >= 2 for amounts in groups.values()):
        return ("RULE-AGG-001",)
    return None


def _rule_auth_001(
    case: ReimbursementCase, profile: OrganizationProfile, eligible_total: int, extra_rule_ids: tuple[str, ...] = ()
) -> ProcessingPacket | None:
    """Aggregated eligible amount exceeds routine-processing threshold."""
    op = profile.authority_threshold_operator
    threshold = profile.routine_processing_max_vnd
    exceeds = (
        eligible_total > threshold
        if op.value == "greater_than"
        else eligible_total >= threshold
    )
    if exceeds:
        rules = (*extra_rule_ids, "RULE-AUTH-001")
        outcome, escalation = _build_escalation(
            escalation_type=EscalationType.AUTHORITY_REQUIRED,
            addressee_role="CLUB_CHAIR",
            case_id=case.case_id,
            rule_id="RULE-AUTH-001",
            amount_vnd=eligible_total,
            threshold_vnd=threshold,
            related_evidence_ids=_EMPTY_EVIDENCE_ID,
        )
        # Override triggered_rule_ids to include prior non-terminal rules
        outcome = ProcessingOutcome(
            outcome_id=outcome.outcome_id,
            processing_result=outcome.processing_result,
            escalation_type=outcome.escalation_type,
            approval_status=outcome.approval_status,
            eligible_total_vnd=outcome.eligible_total_vnd,
            amount_to_return_vnd=outcome.amount_to_return_vnd,
            additional_payment_vnd=outcome.additional_payment_vnd,
            reimbursement_amount_vnd=outcome.reimbursement_amount_vnd,
            triggered_rule_ids=rules,
            evidence_used=outcome.evidence_used,
            explanation_vi=outcome.explanation_vi,
            created_at=outcome.created_at,
        )
        return ProcessingPacket(
            control_state=ControlState.ACTIVE,
            outcome=outcome,
            escalation=_escalation_from_dict(escalation),
        )
    return None


def _rule_tax_001(
    case: ReimbursementCase, profile: OrganizationProfile, eligible_total: int
) -> ProcessingPacket | None:
    """Conditional non-cash evidence rule."""
    if (
        profile.tax_regime_applies
        and eligible_total >= profile.non_cash_evidence_threshold_vnd
        and case.non_cash_evidence_verified is not True
    ):
        return _escalate(case, EscalationType.FACT_UNKNOWN, "MEMBER", "RULE-TAX-001", ())
    return None


def _rule_calc_001(
    case: ReimbursementCase, eligible_total: int, extra_rule_ids: tuple[str, ...] = ()
) -> ProcessingPacket | None:
    """ADVANCE_SETTLEMENT calculation."""
    if case.flow_type is not FlowType.ADVANCE_SETTLEMENT:
        return None
    advance = case.advance_amount_vnd or 0
    amount_to_return = max(advance - eligible_total, 0)
    additional_payment = max(eligible_total - advance, 0)
    rules = (*extra_rule_ids, "RULE-CALC-001", "RULE-ROUTINE-001")
    outcome = _build_outcome(
        processing_result=ProcessingResult.ROUTINE_PROCESSED,
        triggered_rule_ids=rules,
        escalation_type=None,
        eligible_total_vnd=eligible_total,
        amount_to_return_vnd=amount_to_return,
        additional_payment_vnd=additional_payment,
        reimbursement_amount_vnd=None,
        case_id=case.case_id,
    )
    return ProcessingPacket(control_state=ControlState.ACTIVE, outcome=outcome)


def _rule_calc_002(
    case: ReimbursementCase, eligible_total: int, extra_rule_ids: tuple[str, ...] = ()
) -> ProcessingPacket | None:
    """MEMBER_PAID calculation."""
    if case.flow_type is not FlowType.MEMBER_PAID:
        return None
    rules = (*extra_rule_ids, "RULE-CALC-002", "RULE-ROUTINE-001")
    outcome = _build_outcome(
        processing_result=ProcessingResult.ROUTINE_PROCESSED,
        triggered_rule_ids=rules,
        escalation_type=None,
        eligible_total_vnd=eligible_total,
        amount_to_return_vnd=None,
        additional_payment_vnd=None,
        reimbursement_amount_vnd=eligible_total,
        case_id=case.case_id,
    )
    return ProcessingPacket(control_state=ControlState.ACTIVE, outcome=outcome)


def _rule_routine_001(
    case: ReimbursementCase, eligible_total: int, extra_rule_ids: tuple[str, ...] = ()
) -> ProcessingPacket | None:
    """No higher-priority rule applied; produce a review packet."""
    rules = (*extra_rule_ids, "RULE-ROUTINE-001")
    outcome = _build_outcome(
        processing_result=ProcessingResult.ROUTINE_PROCESSED,
        triggered_rule_ids=rules,
        escalation_type=None,
        eligible_total_vnd=eligible_total,
        amount_to_return_vnd=None,
        additional_payment_vnd=None,
        reimbursement_amount_vnd=eligible_total
        if case.flow_type is FlowType.MEMBER_PAID
        else None,
        case_id=case.case_id,
    )
    return ProcessingPacket(control_state=ControlState.ACTIVE, outcome=outcome)


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def _evaluate_policy(
    case: ReimbursementCase,
    profile_snapshot: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
    control_state: ControlState,
) -> ProcessingPacket:
    # 10 — pause
    pkt = _rule_sys_001(case)
    if pkt is not None:
        return pkt

    # 20-22 — fact integrity
    for rule_fn in (_rule_fact_001, _rule_fact_002, _rule_fact_003):
        pkt = rule_fn(case)
        if pkt is not None:
            return pkt

    # 30-31 — duplicate signals
    for rule_fn in (_rule_dup_001, _rule_dup_002):
        pkt = rule_fn(case)
        if pkt is not None:
            return pkt

    # 40-44 — scope & category
    pkt = _rule_scope_001(case)
    if pkt is not None:
        return pkt
    pkt = _rule_scope_002(case, profile_snapshot)
    if pkt is not None:
        return pkt
    pkt = _rule_cat_001(case, profile_snapshot)
    if pkt is not None:
        return pkt
    pkt = _rule_cat_002(case)
    if pkt is not None:
        return pkt
    pkt = _rule_cat_003(case, profile_snapshot)
    if pkt is not None:
        return pkt

    # 50 — required documents
    pkt = _rule_doc_001(case)
    if pkt is not None:
        return pkt

    # 55 — deadline
    pkt = _rule_deadline_001(case, profile_snapshot)
    if pkt is not None:
        return pkt

    # 60-61 — budget & conflict
    eligible = _eligible_total(case)
    pkt = _rule_budget_001(case, profile_snapshot, eligible)
    if pkt is not None:
        return pkt
    pkt = _rule_conflict_001(case)
    if pkt is not None:
        return pkt

    # 62 — aggregation (non-terminal)
    extra_rule_ids = _rule_agg_001(case, profile_snapshot) or ()

    # 63 — authority threshold
    pkt = _rule_auth_001(case, profile_snapshot, eligible, extra_rule_ids)
    if pkt is not None:
        return pkt

    # 70 — conditional tax
    pkt = _rule_tax_001(case, profile_snapshot, eligible)
    if pkt is not None:
        return pkt

    # 80-81 — calculations
    pkt = _rule_calc_001(case, eligible, extra_rule_ids)
    if pkt is not None:
        return pkt
    pkt = _rule_calc_002(case, eligible, extra_rule_ids)
    if pkt is not None:
        return pkt

    # 90 — routine
    return _rule_routine_001(case, eligible, extra_rule_ids)


def _eligible_total(case: ReimbursementCase) -> int:
    """Sum of all expense line amounts. All lines are included at this point
    because any ineligible line would have been caught by a higher-priority rule."""
    return sum(item.amount_vnd for item in case.expense_items)


# ---------------------------------------------------------------------------
# Packet validation (ported from SETUP-04 skeleton)
# ---------------------------------------------------------------------------

def _validate_packet_for_case(
    case: ReimbursementCase,
    control_state: ControlState,
    packet: ProcessingPacket,
) -> None:
    if packet.control_state is not control_state:
        raise ValueError("processing packet control state must match the evaluator input")
    outcome = packet.outcome
    if outcome is None or outcome.processing_result is not ProcessingResult.ROUTINE_PROCESSED:
        return
    if case.flow_type is FlowType.MEMBER_PAID:
        if outcome.reimbursement_amount_vnd is None:
            raise ValueError("MEMBER_PAID requires a reimbursement amount")
        if outcome.amount_to_return_vnd is not None or outcome.additional_payment_vnd is not None:
            raise ValueError("MEMBER_PAID must not contain advance calculations")
        return
    if outcome.amount_to_return_vnd is None or outcome.additional_payment_vnd is None:
        raise ValueError("ADVANCE_SETTLEMENT requires both advance calculations")
    if outcome.reimbursement_amount_vnd is not None:
        raise ValueError("ADVANCE_SETTLEMENT must not contain a reimbursement amount")
