"""Frozen vocabulary for the reimbursement v1 synthetic-pilot contract.

This vocabulary is separate from the historical TMP-DEV-001 enums. It contains
no policy implementation, framework, persistence, clock, or I/O dependency.
"""

from __future__ import annotations

from enum import StrEnum


class FlowType(StrEnum):
    """Supported reimbursement flows."""

    MEMBER_PAID = "MEMBER_PAID"
    ADVANCE_SETTLEMENT = "ADVANCE_SETTLEMENT"


class EvidenceType(StrEnum):
    """Metadata-only evidence classifications."""

    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    PAYMENT_PROOF = "PAYMENT_PROOF"
    APPROVAL = "APPROVAL"
    ADVANCE_RECORD = "ADVANCE_RECORD"
    OTHER = "OTHER"


class PaymentMethod(StrEnum):
    """Declared payment methods for an expense line."""

    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"
    E_WALLET = "E_WALLET"
    OTHER = "OTHER"


class LineAssessment(StrEnum):
    """The evaluator's assessment of an expense line."""

    PENDING = "PENDING"
    ELIGIBLE = "ELIGIBLE"
    FACT_UNKNOWN = "FACT_UNKNOWN"
    OUT_OF_POLICY = "OUT_OF_POLICY"


class DuplicateCheckState(StrEnum):
    """The deterministic duplicate-check result supplied to the evaluator."""

    CLEAR = "CLEAR"
    SUSPECTED = "SUSPECTED"
    CONFIRMED_PAID = "CONFIRMED_PAID"
    NOT_RUN = "NOT_RUN"


class AuthorityThresholdOperator(StrEnum):
    """Comparison applied to the profile's routine-processing threshold."""

    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"


class ProcessingResult(StrEnum):
    """The only agent processing results."""

    ROUTINE_PROCESSED = "ROUTINE_PROCESSED"
    ESCALATED = "ESCALATED"


class EscalationType(StrEnum):
    """Safe human-handoff categories."""

    FACT_UNKNOWN = "FACT_UNKNOWN"
    OUT_OF_POLICY = "OUT_OF_POLICY"
    AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"


class ApprovalStatus(StrEnum):
    """Agent outcomes are always pending a human approval."""

    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"


class ControlState(StrEnum):
    """Operational state evaluated before policy rules."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class AuditActorType(StrEnum):
    """Actor class recorded on an append-only audit event."""

    AGENT = "AGENT"
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


class AuditEventType(StrEnum):
    """The minimum reimbursement v1 audit-event vocabulary."""

    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    RULE_TRIGGERED = "RULE_TRIGGERED"
    CLASSIFIED = "CLASSIFIED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    OVERRIDDEN = "OVERRIDDEN"
    UNDONE = "UNDONE"
    HUMAN_DECISION = "HUMAN_DECISION"
    SETTLEMENT = "SETTLEMENT"
