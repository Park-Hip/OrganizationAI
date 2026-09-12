"""Health probe for the temporary L0 foundation."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.persistence.db import build_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Service readiness probe",
    responses={
        http_status.HTTP_200_OK: {"description": "Database reachable"},
        http_status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unreachable"},
    },
)
def health() -> JSONResponse:
    """Report process and database readiness without exposing credentials."""
    try:
        engine = build_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.warning("health probe failed: database unreachable")
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "unreachable"},
        )
    return JSONResponse(content={"status": "ok", "database": "reachable"})
