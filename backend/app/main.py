"""Application composition root for the temporary L0 foundation."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.health import router as health_router
from app.api.routes.temporary_history import router as temporary_history_router
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Build the application instance.

    Exposes the operational health probe plus the temporary decision-trace
    submit/retrieve operations. No human-control or authority surface is included.
    """
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logging.getLogger().setLevel(settings.log_level)
    application = FastAPI(title=settings.app_name, version=settings.app_version)
    application.include_router(health_router)
    application.include_router(temporary_history_router)
    register_exception_handlers(application)
    logger.info(
        "starting %s %s in environment %s",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    return application


app = create_app()
