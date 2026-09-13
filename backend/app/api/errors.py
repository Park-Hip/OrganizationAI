"""Temporary-context error handling for the business API.

Every business error is returned inside the same temporary, synthetic,
unvalidated envelope so no response can be mistaken for an operational
financial or authority record.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas.temporary_history import ErrorBody, ErrorResponse, ProvenanceReadModel
from app.application.temporary_history import (
    TEMPORARY_NOTICE,
    TraceAlreadyRecordedError,
    TraceNotFoundError,
)
from app.policy.profile import TMP_DEV_001_PROFILE

_INPUT_INVALID_CODE = "INPUT_INVALID"
_CASE_ID_ALREADY_RECORDED_CODE = "CASE_ID_ALREADY_RECORDED"
_TRACE_NOT_FOUND_CODE = "TRACE_NOT_FOUND"


def _response(
    status_code: int,
    code: str,
    message: str,
    details: list[object] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details),
        temporary_notice=TEMPORARY_NOTICE,
        provenance=ProvenanceReadModel(
            profile_id=TMP_DEV_001_PROFILE.profile_id,
            profile_source=TMP_DEV_001_PROFILE.profile_source.value,
            data_class=TMP_DEV_001_PROFILE.data_class.value,
            workflow_validation_status=TMP_DEV_001_PROFILE.workflow_validation_status.value,
        ),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def register_exception_handlers(application: FastAPI) -> None:
    """Install handlers that keep every business error in the temporary envelope."""

    @application.exception_handler(TraceAlreadyRecordedError)
    async def _already_recorded(_request: Request, exc: TraceAlreadyRecordedError) -> JSONResponse:
        return _response(
            409,
            _CASE_ID_ALREADY_RECORDED_CODE,
            f"A temporary trace already exists for synthetic case_id {exc.case_id!r}.",
        )

    @application.exception_handler(TraceNotFoundError)
    async def _not_found(_request: Request, exc: TraceNotFoundError) -> JSONResponse:
        return _response(
            404,
            _TRACE_NOT_FOUND_CODE,
            f"No temporary trace exists for trace_id {exc.trace_id!r}.",
        )

    @application.exception_handler(RequestValidationError)
    async def _validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return _response(
            422,
            _INPUT_INVALID_CODE,
            "The submitted temporary case is invalid.",
            details=jsonable_encoder(exc.errors()),
        )
