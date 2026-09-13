"""Persistence models for the temporary backend.

Importing this package registers every mapped entity on ``Base.metadata`` so
Alembic can see the complete schema.
"""

from app.persistence.models.temporary_history import (
    AuditAction,
    AuditActorType,
    TemporaryAuditEvent,
    TemporaryCaseSnapshot,
    TemporaryDecisionSnapshot,
)

__all__ = [
    "AuditAction",
    "AuditActorType",
    "TemporaryAuditEvent",
    "TemporaryCaseSnapshot",
    "TemporaryDecisionSnapshot",
]
