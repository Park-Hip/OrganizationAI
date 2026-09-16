"""Application seam for coordinating reimbursement v1 processing.

Concrete use cases arrive in the integration phase after policy, security, and
persistence adapters are available. This contract deliberately owns no HTTP,
database, policy-rule, or authentication implementation.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.reimbursement import (
    ControlState,
    OrganizationProfile,
    PolicySnapshot,
    ProcessingPacket,
    ReimbursementCase,
)


class ReimbursementProcessingUseCase(Protocol):
    """Coordinates snapshot loading, pure evaluation, and event recording."""

    def process(
        self,
        case: ReimbursementCase,
        profile_snapshot: OrganizationProfile,
        policy_snapshot: PolicySnapshot,
        control_state: ControlState,
    ) -> ProcessingPacket:
        """Return the recorded processing packet for a structurally valid case."""
