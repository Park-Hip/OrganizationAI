"""Database engine and declarative metadata boundaries for L0."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import get_settings


class Base(DeclarativeBase):
    """Declarative base for future mapped entities.

    Empty in L0 on purpose: no Case, Decision, or Audit tables exist yet.
    """


@lru_cache
def build_engine() -> Engine:
    """Build the SQLAlchemy engine from typed application settings."""
    settings = get_settings()
    return create_engine(settings.database_url.get_secret_value(), pool_pre_ping=True)
