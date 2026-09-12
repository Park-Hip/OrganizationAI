"""Application composition root for the temporary L0 foundation."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Build the application instance.

    L0 exposes a health operation only.
    Later layers register routers and application services here.
    """
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logging.getLogger().setLevel(settings.log_level)
    application = FastAPI(title=settings.app_name, version=settings.app_version)
    application.include_router(health_router)
    logger.info(
        "starting %s %s in environment %s",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    return application


app = create_app()
