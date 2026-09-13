"""Database engine, session factory, and declarative metadata boundaries."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import get_settings


class Base(DeclarativeBase):
    """Declarative base for mapped entities.

    Mapped temporary-history entities are registered by importing
    ``app.persistence.models``.
    """


@lru_cache
def build_engine() -> Engine:
    """Build the SQLAlchemy engine from typed application settings."""
    settings = get_settings()
    return create_engine(settings.database_url.get_secret_value(), pool_pre_ping=True)


@lru_cache
def build_session_factory() -> sessionmaker[Session]:
    """Build a session factory bound to the cached application engine."""
    return sessionmaker(bind=build_engine(), expire_on_commit=False, autoflush=False)


def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session for FastAPI dependency injection."""
    factory = build_session_factory()
    with factory() as session:
        yield session
