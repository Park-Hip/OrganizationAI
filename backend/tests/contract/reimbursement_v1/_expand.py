"""Deterministic concise-fixture -> full-envelope expansion.

This is a test-support expander only, never imported by the application and
never a policy evaluator. It builds the complete input side of the envelope
(policy_version + organization_profile + case + control_state + audit_events)
from a concise fixture. It does not produce the processing outcome.

The expander is data-driven and never branches on fixture id, title, group,
note, or free-text prose (see ADR-007, docs/ADRs/007, and
policy-forge-baseline/expansion_spec.md).
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

PROSE_FIELDS = {"purpose", "task_or_event"}
FACT_FLAG_MAP = {"vendor_identity": "VENDOR_IDENTITY_UNVERIFIED"}

_DEFAULT_EVENT_END_DATE = "2026-08-31"
_DEFAULT_SUBMITTED_AT = "2026-09-10T09:00:00Z"
_DEFAULT_TRANSACTION_DATE = "2026-08-05"
_DEFAULT_APPROVED_BUDGET = 10000000
_DEFAULT_REMAINING_BUDGET = 10000000


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def structural_input(concise: dict[str, Any]) -> dict[str, Any]:
    """Return the concise input with free-text prose fields removed."""
    return {key: value for key, value in concise.items() if key not in PROSE_FIELDS}


def structural_digest(concise: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(structural_input(concise)).encode("utf-8")).hexdigest()


def _gen_id(prefix: str, concise: dict[str, Any]) -> str:
    return f"{prefix}-{structural_digest(concise)[:12]}"


def _person(person_id: str, role: str) -> dict[str, str]:
    return {"person_id": person_id, "display_name": f"Synthetic {person_id}", "role": role}


def _payment_is_non_cash(expense: dict[str, Any]) -> bool:
    if "items" in expense:
        return all(
            item.get("payment_method", "BANK_TRANSFER") != "CASH" for item in expense["items"]
        )
    return expense.get("payment_method", "BANK_TRANSFER") != "CASH"


def _build_lines(
    concise: dict[str, Any], invoice_evidence_id: str, suspicion_flags: list[str]
) -> list[dict[str, Any]]:
    expense = concise["expense"]
    lines: list[dict[str, Any]] = []
    if "items" in expense:
        for index, item in enumerate(expense["items"], start=1):
            lines.append(
                {
                    "line_id": f"LN-{structural_digest(concise)[:8]}-{index}",
                    "vendor": item["vendor"],
                    "transaction_date": item["transaction_date"],
                    "purpose_code": item["purpose_code"],
                    "description": "Synthetic expense line",
                    "category": item["category"],
                    "amount_vnd": item["amount_vnd"],
                    "payment_method": item.get("payment_method", "BANK_TRANSFER"),
                    "evidence_ids": [invoice_evidence_id],
                    "suspicion_flags": list(suspicion_flags),
                    "line_assessment": "PENDING",
                }
            )
    else:
        lines.append(
            {
                "line_id": f"LN-{structural_digest(concise)[:8]}-1",
                "vendor": expense.get("vendor", "V-SYN-001"),
                "transaction_date": expense.get("transaction_date", _DEFAULT_TRANSACTION_DATE),
                "purpose_code": expense.get("purpose_code", "PURP-SYN"),
                "description": "Synthetic expense line",
                "category": expense["category"],
                "amount_vnd": expense["total_vnd"],
                "payment_method": expense.get("payment_method", "BANK_TRANSFER"),
                "evidence_ids": [invoice_evidence_id],
                "suspicion_flags": list(suspicion_flags),
                "line_assessment": "PENDING",
            }
        )
    return lines


def _declared_total(concise: dict[str, Any]) -> int:
    evidence = concise.get("evidence") or {}
    if "declared_total_vnd" in evidence:
        return int(evidence["declared_total_vnd"])
    expense = concise["expense"]
    if "items" in expense:
        return sum(int(item["amount_vnd"]) for item in expense["items"])
    return int(expense["total_vnd"])


def _evidence_total(concise: dict[str, Any], declared_total: int) -> int:
    evidence = concise.get("evidence") or {}
    if "evidence_total_vnd" in evidence:
        return int(evidence["evidence_total_vnd"])
    return declared_total


def _build_evidence(
    concise: dict[str, Any], declared_total: int, advance_amount: int | None
) -> list[dict[str, Any]]:
    evidence = concise.get("evidence") or {}
    digest = structural_digest(concise)
    readable = bool(evidence.get("readable", True))
    verified = bool(evidence.get("verified", True))
    ocr_confidence = evidence.get("ocr_confidence", None)
    payment_proof = bool(evidence.get("payment_proof", True))
    prior_approval = bool(evidence.get("prior_approval_present", False))
    evidence_total = _evidence_total(concise, declared_total)

    records: list[dict[str, Any]] = []
    invoice: dict[str, Any] = {
        "evidence_id": f"E-1-{digest[:8]}",
        "type": "INVOICE",
        "file_hash": f"sha256-{digest}",
        "readable": readable,
        "verified": verified,
        "document_number": f"INV-{digest[:8]}",
        "document_date": _DEFAULT_TRANSACTION_DATE,
        "amount_vnd": evidence_total,
    }
    if ocr_confidence is not None:
        invoice["ocr_confidence"] = ocr_confidence
    records.append(invoice)

    if payment_proof:
        records.append(
            {
                "evidence_id": f"E-2-{digest[:8]}",
                "type": "PAYMENT_PROOF",
                "file_hash": f"sha256-{digest}",
                "readable": readable,
                "verified": verified,
                "amount_vnd": evidence_total,
            }
        )

    if prior_approval:
        approval_id = f"APR-{digest[:8]}"
        records.append(
            {
                "evidence_id": f"E-3-{digest[:8]}",
                "type": "APPROVAL",
                "file_hash": f"sha256-{digest}",
                "readable": True,
                "verified": True,
                "approval_decision_ids": [approval_id],
            }
        )

    if concise["flow_type"] == "ADVANCE_SETTLEMENT":
        records.append(
            {
                "evidence_id": f"E-4-{digest[:8]}",
                "type": "ADVANCE_RECORD",
                "file_hash": f"sha256-{digest}",
                "readable": readable,
                "verified": verified,
                "document_number": evidence.get("advance_reference", f"ADV-{digest[:8]}"),
                "amount_vnd": advance_amount,
            }
        )

    return records


def _suspicion_flags(concise: dict[str, Any]) -> list[str]:
    evidence = concise.get("evidence") or {}
    flags: list[str] = []
    for fact in evidence.get("missing_facts", []):
        if fact in FACT_FLAG_MAP:
            flags.append(FACT_FLAG_MAP[fact])
    if evidence.get("event_link") is False:
        flags.append("NO_EVENT_LINK")
    return flags


def _audit_events(
    concise: dict[str, Any], policy_version: str, paused: bool
) -> list[dict[str, Any]]:
    digest = structural_digest(concise)
    input_hash = f"sha256-{digest}"
    events: list[dict[str, Any]] = [
        {
            "event_id": f"EVT-{digest[:12]}-RECV",
            "timestamp": _DEFAULT_SUBMITTED_AT,
            "actor_id": "AGENT",
            "actor_type": "AGENT",
            "policy_version": policy_version,
            "event_type": "RECEIVED",
            "input_hash": input_hash,
            "triggered_rule_ids": [],
            "explanation": "Received synthetic reimbursement case.",
        },
        {
            "event_id": f"EVT-{digest[:12]}-VAL",
            "timestamp": "2026-09-10T09:00:01Z",
            "actor_id": "AGENT",
            "actor_type": "AGENT",
            "policy_version": policy_version,
            "event_type": "VALIDATED",
            "input_hash": input_hash,
            "triggered_rule_ids": [],
            "explanation": "Validated synthetic reimbursement case shape.",
        },
    ]
    if paused:
        events.append(
            {
                "event_id": f"EVT-{digest[:12]}-PAUSE",
                "timestamp": "2026-09-10T09:00:02Z",
                "actor_id": "SYSTEM",
                "actor_type": "SYSTEM",
                "actor_role": "CLUB_CHAIR",
                "policy_version": policy_version,
                "event_type": "PAUSED",
                "input_hash": input_hash,
                "triggered_rule_ids": [],
                "explanation": "Authorized synthetic operational pause.",
                "reason": "Synthetic authorized pause.",
            }
        )
    return events


def expand(concise: dict[str, Any], profile: dict[str, Any], policy_version: str) -> dict[str, Any]:
    """Expand a concise fixture input into a full input envelope."""
    concise = deepcopy(concise)
    flow_type = concise["flow_type"]
    paused = bool(concise.get("paused", False))
    conflict = bool(concise.get("conflict", False))
    days_late = int(concise.get("days_late", 0))
    requester_id = concise.get("requester_id", "P-001")
    proposed_id = concise.get("proposed_approver_id", "P-002")
    if conflict:
        proposed_id = requester_id

    profile = deepcopy(profile)
    for key, value in (concise.get("profile_overrides") or {}).items():
        if key in profile:
            profile[key] = value

    expense = concise["expense"]
    evidence = concise.get("evidence") or {}
    budget = concise.get("budget") or {}
    declared_total = _declared_total(concise)
    advance_amount = (
        int(concise["advance_amount_vnd"]) if flow_type == "ADVANCE_SETTLEMENT" else None
    )

    digest = structural_digest(concise)
    invoice_id = f"E-1-{digest[:8]}"
    flags = _suspicion_flags(concise)
    lines = _build_lines(concise, invoice_id, flags)
    evidence_records = _build_evidence(concise, declared_total, advance_amount)

    prior_approval_ids = []
    if evidence.get("prior_approval_present"):
        prior_approval_ids = [f"APR-{digest[:8]}"]

    if "non_cash_verified" in evidence:
        non_cash_verified = bool(evidence["non_cash_verified"])
    else:
        non_cash_verified = _payment_is_non_cash(expense)

    case: dict[str, Any] = {
        "case_id": _gen_id("CASE", concise),
        "flow_type": flow_type,
        "requester": _person(requester_id, profile["roles"]["requester"]),
        "submitted_at": concise.get("submitted_at", _DEFAULT_SUBMITTED_AT),
        "task_or_event": concise.get("task_or_event", "EVT-SYN-001"),
        "event_end_date": concise.get("event_end_date", _DEFAULT_EVENT_END_DATE),
        "purpose": concise.get("purpose", "Chi cho hoat dong cau lac bo (tong hop)"),
        "budget_code": f"BUD-{digest[:8]}",
        "approved_budget_vnd": int(budget.get("approved_vnd", _DEFAULT_APPROVED_BUDGET)),
        "remaining_budget_vnd": int(budget.get("remaining_vnd", _DEFAULT_REMAINING_BUDGET)),
        "prior_approval_ids": prior_approval_ids,
        "expense_items": lines,
        "evidence": evidence_records,
        "declared_total_vnd": declared_total,
        "non_cash_evidence_verified": non_cash_verified,
        "reimbursement_account": {
            "account_name": "Synthetic",
            "bank_name": "Synthetic Bank",
            "masked_account_number": "*****0001",
        },
        "proposed_approver": _person(proposed_id, profile["roles"]["approver_within_authority"]),
        "duplicate_check": concise["duplicate_check"],
        "submitted_business_days_after_end": days_late,
        "paused": paused,
    }

    if flow_type == "ADVANCE_SETTLEMENT":
        case["advance_reference"] = evidence.get("advance_reference", f"ADV-{digest[:8]}")
        case["advance_amount_vnd"] = advance_amount

    envelope: dict[str, Any] = {
        "policy_version": policy_version,
        "organization_profile": profile,
        "case": case,
        "control_state": "PAUSED" if paused else "ACTIVE",
        "audit_events": _audit_events(concise, policy_version, paused),
    }
    return envelope


def materialize_envelope(
    concise: dict[str, Any],
    profile: dict[str, Any],
    policy_version: str,
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Expand the input and attach the declared expected outcome/escalation.

    This produces a full envelope whose ProcessingOutcome and Escalation are
    populated from the corpus expectation so the whole envelope can be
    validated: the declared output must be schema-consistent with the
    deterministically expanded input.
    """
    envelope = expand(concise, profile, policy_version)
    if expected.get("control_state") == "PAUSED":
        return envelope

    outcome: dict[str, Any] = {
        "outcome_id": _gen_id("OUT", concise),
        "processing_result": expected["processing_result"],
        "escalation_type": expected.get("escalation_type"),
        "approval_status": expected["approval_status"],
        "triggered_rule_ids": list(expected["triggered_rule_ids"]),
        "evidence_used": [f"E-1-{structural_digest(concise)[:8]}"],
        "explanation_vi": "Kết quả xử lý tổng hợp; không phải phê duyệt hay lệnh thanh toán.",
        "created_at": "2026-09-10T09:05:00Z",
    }
    for field in (
        "eligible_total_vnd",
        "amount_to_return_vnd",
        "additional_payment_vnd",
        "reimbursement_amount_vnd",
    ):
        if expected.get(field) is not None:
            outcome[field] = expected[field]

    envelope["processing_outcome"] = outcome
    if expected.get("processing_result") == "ESCALATED":
        escalation: dict[str, Any] = {
            "type": expected["escalation_type"],
            "addressee_role": expected["addressee_role"],
            "related_evidence": [f"E-1-{structural_digest(concise)[:8]}"],
            "known_facts": [
                f"case {_gen_id('CASE', concise)}",
                f"amount {expected.get('eligible_total_vnd', 'n/a')}",
            ],
            "specific_question": "Cần câu trả lời có căn cứ kèm bằng chứng đính kèm.",
            "response_format": "Cung cấp bằng chứng hoặc chọn APPROVE/REJECT kèm lý do.",
            "resume_action": "Chạy lại quy tắc tương ứng sau khi nhận trả lời hợp lệ.",
        }
        if expected.get("prerequisite_consultations"):
            escalation["prerequisite_consultations"] = list(expected["prerequisite_consultations"])
        envelope["escalation"] = escalation

    return envelope
