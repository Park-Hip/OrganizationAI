"""Read models for the temporary decision-trace API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProvenanceReadModel(BaseModel):
    """Server-owned temporary-data markers echoed on every trace response."""

    profile_id: str
    profile_source: str
    data_class: str
    workflow_validation_status: str


class AuditEventReadModel(BaseModel):
    """One ordered system event from a stored temporary trace."""

    event_id: UUID
    sequence_number: int
    previous_event_id: UUID | None
    actor_type: str
    action: str
    payload: dict[str, object]
    recorded_at: datetime


class DecisionReadModel(BaseModel):
    """The stored decision snapshot, returned without reevaluation."""

    outcome: str
    applied_rule_id: str
    reason: str
    question: str | None
    profile_id: str
    profile_snapshot: dict[str, object]
    decided_at: datetime


class TraceReadModel(BaseModel):
    """The complete reconstructed temporary decision trace."""

    temporary_notice: str
    trace_id: UUID
    recorded_at: datetime
    provenance: ProvenanceReadModel
    submission: dict[str, object]
    facts_used: dict[str, object]
    decision: DecisionReadModel
    events: list[AuditEventReadModel]


class ErrorBody(BaseModel):
    """A single business error with an optional structured detail list."""

    code: str
    message: str
    details: list[object] | None = None


class ErrorResponse(BaseModel):
    """The temporary-context error envelope returned by the business API."""

    error: ErrorBody
    temporary_notice: str
