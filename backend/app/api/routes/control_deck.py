"""Temporary Control Deck command endpoint.

The endpoint appends exactly one synthetic control event to a stored trace and
returns the derived trace view. Control state is a deterministic projection of
the stored decision plus control events; it never calls the evaluator or
normalizer and never mutates an existing snapshot.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.control_deck import ControlCommandRequest
from app.api.schemas.temporary_history import ErrorResponse, TraceReadModel
from app.application.control_deck import submit_control
from app.persistence.db import get_session

router = APIRouter(prefix="/api/temporary/decision-traces", tags=["temporary-control-deck"])


@router.post(
    "/{trace_id}/controls",
    response_model=TraceReadModel,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Unknown trace ID",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Illegal control transition or idempotency conflict",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Invalid temporary control command",
        },
    },
)
def create_control(
    trace_id: UUID,
    command: ControlCommandRequest,
    session: Session = Depends(get_session),
) -> TraceReadModel:
    """Append one synthetic control event and return the derived trace view."""
    return submit_control(
        trace_id=trace_id,
        command=command.command,
        session=session,
        reason=command.reason,
        disposition=command.disposition,
        idempotency_key=command.idempotency_key,
    )
