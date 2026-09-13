"""Temporary decision-trace API routes.

The submit endpoint persists one immutable trace; the get endpoint returns the
stored snapshots without reevaluating the decision. There is no update, delete,
or list operation.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.schemas.temporary_history import TraceReadModel
from app.application.temporary_history import read_trace, submit_trace
from app.domain.models import CaseSubmission
from app.persistence.db import get_session

router = APIRouter(prefix="/api/temporary/decision-traces", tags=["temporary-decision-history"])


@router.post(
    "",
    response_model=TraceReadModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Duplicate synthetic case ID"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Invalid temporary case"},
    },
)
def create_trace(
    submission: CaseSubmission,
    response: Response,
    session: Session = Depends(get_session),
) -> TraceReadModel:
    """Validate, decide, and record one synthetic temporary case."""
    trace = submit_trace(submission=submission, session=session)
    response.headers["Location"] = f"/api/temporary/decision-traces/{trace.trace_id}"
    return trace


@router.get(
    "/{trace_id}",
    response_model=TraceReadModel,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Unknown trace ID"}},
)
def retrieve_trace(
    trace_id: UUID,
    session: Session = Depends(get_session),
) -> TraceReadModel:
    """Return the stored history for a server trace ID without reevaluation."""
    return read_trace(trace_id=trace_id, session=session)
