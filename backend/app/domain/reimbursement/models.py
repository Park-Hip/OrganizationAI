"""Immutable value objects for the reimbursement v1 processing contract.

These models define structural and cross-field invariants only. They are pure
and deliberately separate from the historical TMP-DEV-001 domain models.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.reimbursement.enums import (
    ApprovalStatus,
    AuditActorType,
    AuditEventType,
    AuthorityThresholdOperator,
    ControlState,
    DuplicateCheckState,
    EscalationType,
    EvidenceType,
    FlowType,
    LineAssessment,
    PaymentMethod,
    ProcessingResult,
)


class FrozenDomainModel(BaseModel):
    """Base model for transport- and persistence-agnostic immutable values."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class PersonRef(FrozenDomainModel):
    """Minimized person reference used for a requester or authorized actor."""

    person_id: str
    display_name: str
    role: str
    contact: str | None = None

    @field_validator("person_id", "display_name", "role")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("person reference fields must not be blank")
        return value


class RoleSet(FrozenDomainModel):
    """Profile-owned roles rather than application hard-coded authorities."""

    requester: str
    preparer: str
    approver_within_authority: str
    approver_over_threshold: str
    exception_approvers: tuple[str, ...]
    payment_executor: str

    @field_validator(
        "requester",
        "preparer",
        "approver_within_authority",
        "approver_over_threshold",
        "payment_executor",
    )
    @classmethod
    def require_non_blank_role(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("role must not be blank")
        return value


class OrganizationProfile(FrozenDomainModel):
    """Immutable, server-owned policy configuration snapshot."""

    profile_id: str
    profile_version: str
    policy_version: str
    owner: str
    effective_date: date | None
    parent_organization: str
    accounting_regime: str
    tax_regime_applies: bool
    currency: str = "VND"
    submission_deadline_business_days: int = Field(ge=0)
    routine_processing_max_vnd: int = Field(ge=0)
    authority_threshold_operator: AuthorityThresholdOperator
    non_cash_evidence_threshold_vnd: int = Field(ge=0)
    non_cash_rule_is_conditional: bool
    aggregation_keys: tuple[str, ...]
    allowed_categories: frozenset[str]
    conditional_categories: frozenset[str]
    prohibited_categories: frozenset[str]
    legally_prohibited_categories: frozenset[str]
    roles: RoleSet
    no_self_approval: bool = True
    agent_can_approve: bool = False
    agent_can_reject: bool = False
    agent_can_transfer_money: bool = False
    raw_ocr_retention_days: int = Field(ge=0)
    official_record_retention: str

    @field_validator(
        "profile_id",
        "profile_version",
        "policy_version",
        "owner",
        "parent_organization",
        "accounting_regime",
        "currency",
        "official_record_retention",
    )
    @classmethod
    def require_non_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("profile text fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_safety_and_categories(self) -> OrganizationProfile:
        if self.currency != "VND":
            raise ValueError("the reimbursement v1 contract supports VND only")
        if not self.aggregation_keys or any(not key.strip() for key in self.aggregation_keys):
            raise ValueError("at least one non-blank aggregation key is required")
        categories = (
            self.allowed_categories,
            self.conditional_categories,
            self.prohibited_categories,
            self.legally_prohibited_categories,
        )
        if any(not category.strip() for group in categories for category in group):
            raise ValueError("configured categories must not be blank")
        if self.allowed_categories & self.conditional_categories:
            raise ValueError("allowed and conditional categories must be disjoint")
        if self.prohibited_categories & self.legally_prohibited_categories:
            raise ValueError("policy and legal prohibitions must be disjoint")
        if not self.no_self_approval:
            raise ValueError("no_self_approval must remain true")
        if self.agent_can_approve or self.agent_can_reject or self.agent_can_transfer_money:
            raise ValueError("the agent cannot approve, reject, or transfer money")
        return self


class PolicySnapshot(FrozenDomainModel):
    """Versioned policy source retained with a case for reproducibility."""

    policy_id: str
    policy_version: str
    content_hash: str = Field(min_length=8)
    serialized_policy: str = Field(min_length=1)

    @field_validator("policy_id", "policy_version")
    @classmethod
    def require_non_blank_identifier(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("policy identifiers must not be blank")
        return value


class Evidence(FrozenDomainModel):
    """Metadata-only evidence reference, never a stored receipt body."""

    evidence_id: str
    type: EvidenceType
    file_hash: str = Field(min_length=8)
    readable: bool
    verified: bool
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)
    document_number: str | None = None
    document_date: date | None = None
    amount_vnd: int | None = Field(default=None, ge=0)
    notes: str | None = None
    approval_decision_ids: tuple[str, ...] = ()

    @field_validator("evidence_id")
    @classmethod
    def require_non_blank_evidence_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence_id must not be blank")
        return value


class ExpenseItem(FrozenDomainModel):
    """One complete expense line retained regardless of its assessment."""

    line_id: str
    vendor: str
    vendor_tax_id: str | None = None
    transaction_date: date
    purpose_code: str
    description: str
    category: str
    amount_vnd: int = Field(ge=0)
    tax_amount_vnd: int | None = Field(default=None, ge=0)
    payment_method: PaymentMethod
    evidence_ids: tuple[str, ...] = Field(min_length=1)
    suspicion_flags: tuple[str, ...]
    line_assessment: LineAssessment = LineAssessment.PENDING

    @field_validator("line_id", "vendor", "purpose_code", "description", "category")
    @classmethod
    def require_non_blank_line_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("expense-line text fields must not be blank")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def require_non_blank_evidence_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not evidence_id.strip() for evidence_id in value):
            raise ValueError("expense evidence IDs must not be blank")
        return value


class MaskedReimbursementAccount(FrozenDomainModel):
    """A masked account representation permitted in the processing packet."""

    account_name: str
    bank_name: str
    masked_account_number: str

    @field_validator("account_name", "bank_name", "masked_account_number")
    @classmethod
    def require_non_blank_account_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("masked-account fields must not be blank")
        return value


class ReimbursementCase(FrozenDomainModel):
    """Versioned reimbursement case supplied to the pure processing boundary."""

    case_id: str
    flow_type: FlowType
    requester: PersonRef
    submitted_at: datetime
    task_or_event: str
    event_end_date: date
    purpose: str
    budget_code: str
    approved_budget_vnd: int = Field(ge=0)
    remaining_budget_vnd: int = Field(ge=0)
    prior_approval_ids: tuple[str, ...] = ()
    prior_payment_reference: str | None = None
    advance_reference: str | None = None
    advance_amount_vnd: int | None = Field(default=None, ge=0)
    expense_items: tuple[ExpenseItem, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    declared_total_vnd: int = Field(ge=0)
    non_cash_evidence_verified: bool | None = None
    reimbursement_account: MaskedReimbursementAccount
    proposed_approver: PersonRef | None = None
    duplicate_check: DuplicateCheckState | None = None
    submitted_business_days_after_end: int | None = Field(default=None, ge=0)
    paused: bool

    @field_validator("case_id", "task_or_event", "purpose")
    @classmethod
    def require_non_blank_case_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("case text fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_flow_specific_fields(self) -> ReimbursementCase:
        has_advance_amount = self.advance_amount_vnd is not None
        if self.flow_type is FlowType.ADVANCE_SETTLEMENT:
            if (
                self.advance_reference is None
                or not self.advance_reference.strip()
                or not has_advance_amount
            ):
                raise ValueError(
                    "ADVANCE_SETTLEMENT requires advance_reference and advance_amount_vnd"
                )
        elif self.advance_reference is not None or has_advance_amount:
            raise ValueError("MEMBER_PAID must not contain advance-specific fields")
        return self


class PrerequisiteConsultation(FrozenDomainModel):
    """An auditable prerequisite, not a second escalation decision."""

    role: str
    requirement: str

    @field_validator("role", "requirement")
    @classmethod
    def require_non_blank_consultation_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("consultation fields must not be blank")
        return value


class Escalation(FrozenDomainModel):
    """One self-contained question routed to one authorized role."""

    type: EscalationType
    addressee_role: str
    related_evidence: tuple[str, ...] = Field(min_length=1)
    known_facts: tuple[str, ...] = Field(min_length=1)
    specific_question: str = Field(min_length=20)
    response_format: str = Field(min_length=5)
    resume_action: str = Field(min_length=10)
    prerequisite_consultations: tuple[PrerequisiteConsultation, ...] = ()

    @field_validator("addressee_role")
    @classmethod
    def require_non_blank_addressee(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("escalation addressee_role must not be blank")
        return value


class ProcessingOutcome(FrozenDomainModel):
    """Agent-produced result that remains pending human approval."""

    outcome_id: str
    processing_result: ProcessingResult
    escalation_type: EscalationType | None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_HUMAN_APPROVAL
    eligible_total_vnd: int | None = Field(default=None, ge=0)
    amount_to_return_vnd: int | None = Field(default=None, ge=0)
    additional_payment_vnd: int | None = Field(default=None, ge=0)
    reimbursement_amount_vnd: int | None = Field(default=None, ge=0)
    triggered_rule_ids: tuple[str, ...] = Field(min_length=1)
    evidence_used: tuple[str, ...] = ()
    explanation_vi: str = Field(min_length=20)
    created_at: datetime

    @field_validator("outcome_id")
    @classmethod
    def require_non_blank_outcome_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("outcome_id must not be blank")
        return value

    @model_validator(mode="after")
    def validate_result_shape(self) -> ProcessingOutcome:
        if self.approval_status is not ApprovalStatus.PENDING_HUMAN_APPROVAL:
            raise ValueError("agent outcomes must remain pending human approval")
        if self.processing_result is ProcessingResult.ROUTINE_PROCESSED:
            if self.escalation_type is not None:
                raise ValueError("ROUTINE_PROCESSED must not have an escalation type")
            if self.eligible_total_vnd is None:
                raise ValueError("ROUTINE_PROCESSED requires an eligible total")
        elif self.escalation_type is None:
            raise ValueError("ESCALATED requires exactly one escalation type")
        return self


class ProcessingPacket(FrozenDomainModel):
    """Pure evaluator output, separate from persistence and transport envelopes."""

    control_state: ControlState
    outcome: ProcessingOutcome | None = None
    escalation: Escalation | None = None

    @model_validator(mode="after")
    def validate_packet_shape(self) -> ProcessingPacket:
        if self.control_state is ControlState.PAUSED:
            if self.outcome is not None or self.escalation is not None:
                raise ValueError("a paused packet has neither outcome nor escalation")
            return self
        if self.outcome is None:
            raise ValueError("an active packet requires a processing outcome")
        if self.outcome.processing_result is ProcessingResult.ROUTINE_PROCESSED:
            if self.escalation is not None:
                raise ValueError("a routine packet has no escalation")
        elif self.escalation is None:
            raise ValueError("an escalated packet requires one escalation")
        elif self.escalation.type is not self.outcome.escalation_type:
            raise ValueError("packet escalation type must match the outcome")
        return self


class AuditEvent(FrozenDomainModel):
    """Append-only audit value ready for a persistence adapter to record."""

    event_id: str
    timestamp: datetime
    actor_id: str
    actor_type: AuditActorType
    policy_version: str
    event_type: AuditEventType
    input_hash: str = Field(min_length=8)
    triggered_rule_ids: tuple[str, ...]
    explanation: str
    actor_role: str | None = None
    outcome_id: str | None = None
    reason: str | None = None
    decision: str | None = None
    previous_outcome_id: str | None = None
    target_audit_event_id: str | None = None
    predecessor_event_id: str | None = None
    evidence_ids: tuple[str, ...] = ()

    @field_validator("event_id", "actor_id", "policy_version", "explanation")
    @classmethod
    def require_non_blank_audit_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("required audit text fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_control_requirements(self) -> AuditEvent:
        requires_role_and_reason = {
            AuditEventType.PAUSED,
            AuditEventType.RESUMED,
            AuditEventType.OVERRIDDEN,
            AuditEventType.UNDONE,
            AuditEventType.HUMAN_DECISION,
            AuditEventType.SETTLEMENT,
        }
        if self.event_type in requires_role_and_reason and (not self.actor_role or not self.reason):
            raise ValueError(f"{self.event_type.value} requires actor_role and reason")
        if self.event_type is AuditEventType.OVERRIDDEN and not self.previous_outcome_id:
            raise ValueError("OVERRIDDEN requires previous_outcome_id")
        if self.event_type is AuditEventType.UNDONE and not self.target_audit_event_id:
            raise ValueError("UNDONE requires target_audit_event_id")
        if self.event_type is AuditEventType.HUMAN_DECISION and (
            self.actor_type is not AuditActorType.HUMAN
            or not self.previous_outcome_id
            or not self.decision
        ):
            raise ValueError(
                "HUMAN_DECISION requires a human actor, previous outcome, and decision"
            )
        if self.event_type is AuditEventType.SETTLEMENT and (
            self.actor_type is not AuditActorType.HUMAN
            or not self.predecessor_event_id
            or not self.evidence_ids
        ):
            raise ValueError("SETTLEMENT requires a human actor, predecessor event, and evidence")
        return self
