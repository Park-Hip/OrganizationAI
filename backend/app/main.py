"""Application composition root for the temporary L0 foundation."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router

PROJECT_NAME = "Decision Core API"
PROJECT_VERSION = "0.1.0"


def create_app() -> FastAPI:
    """Build the application instance.

    L0 exposes a health operation only.
    Later layers register routers and application services here.
    """
    application = FastAPI(title=PROJECT_NAME, version=PROJECT_VERSION)
    application.include_router(health_router)
    return application


app = create_app()
