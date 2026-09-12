"""Health probe for the temporary L0 foundation."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, text

from app.persistence.db import build_engine

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service readiness probe")
def health(engine: Engine = Depends(build_engine)) -> JSONResponse:
    """Report process and database readiness without exposing credentials."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "unreachable"},
        )
    return JSONResponse(content={"status": "ok", "database": "reachable"})
