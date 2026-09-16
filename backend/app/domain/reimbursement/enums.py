"""Frozen vocabulary for the reimbursement v1 synthetic-pilot contract.

This vocabulary is separate from the historical TMP-DEV-001 enums. It contains
no policy implementation, framework, persistence, clock, or I/O dependency.
"""

from __future__ import annotations

from enum import Enum


class FlowType(str, Enum):  # noqa: UP042
    """Supported reimbursement flows."""

    MEMBER_PAID = "MEMBER_PAID"
    ADVANCE_SETTLEMENT = "ADVANCE_SETTLEMENT"


class EvidenceType(str, Enum):  # noqa: UP042
    """Metadata-only evidence classifications."""

    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    PAYMENT_PROOF = "PAYMENT_PROOF"
    APPROVAL = "APPROVAL"
    ADVANCE_RECORD = "ADVANCE_RECORD"
    OTHER = "OTHER"


class PaymentMethod(str, Enum):  # noqa: UP042
    """Declared payment methods for an expense line."""

    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CARD = "CARD"
    E_WALLET = "E_WALLET"
    OTHER = "OTHER"


class LineAssessment(str, Enum):  # noqa: UP042
    """The evaluator's assessment of an expense line."""

    PENDING = "PENDING"
    ELIGIBLE = "ELIGIBLE"
    FACT_UNKNOWN = "FACT_UNKNOWN"
    OUT_OF_POLICY = "OUT_OF_POLICY"


class DuplicateCheckState(str, Enum):  # noqa: UP042
    """The deterministic duplicate-check result supplied to the evaluator."""

    CLEAR = "CLEAR"
    SUSPECTED = "SUSPECTED"
    CONFIRMED_PAID = "CONFIRMED_PAID"
    NOT_RUN = "NOT_RUN"


class AuthorityThresholdOperator(str, Enum):  # noqa: UP042
    """Comparison applied to the profile's routine-processing threshold."""

    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"


class ProcessingResult(str, Enum):  # noqa: UP042
    """The only agent processing results."""

    ROUTINE_PROCESSED = "ROUTINE_PROCESSED"
    ESCALATED = "ESCALATED"


class EscalationType(str, Enum):  # noqa: UP042
    """Safe human-handoff categories."""

    FACT_UNKNOWN = "FACT_UNKNOWN"
    OUT_OF_POLICY = "OUT_OF_POLICY"
    AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"


class ApprovalStatus(str, Enum):  # noqa: UP042
    """Agent outcomes are always pending a human approval."""

    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"


class ControlState(str, Enum):  # noqa: UP042
    """Operational state evaluated before policy rules."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class AuditActorType(str, Enum):  # noqa: UP042
    """Actor class recorded on an append-only audit event."""

    AGENT = "AGENT"
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


class AuditEventType(str, Enum):  # noqa: UP042
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
