"""Authentication seam for reimbursement v1.

The server derives this context through the later OIDC adapter. Client input
must never select its own actor identity, role, or scope.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import Field

from app.domain.reimbursement import FrozenDomainModel, PersonRef


class AuthenticatedActor(FrozenDomainModel):
    """Server-derived actor context used by authorization and application code."""

    person: PersonRef
    permitted_case_ids: frozenset[str] = Field(default_factory=frozenset)
    permitted_roles: frozenset[str] = Field(default_factory=frozenset)


class IdentityProvider(Protocol):
    """Adapter interface for validated OIDC credentials or synthetic test identities."""

    def authenticated_actor(self, credential: str) -> AuthenticatedActor:
        """Derive a server-owned actor context from a verified credential."""
