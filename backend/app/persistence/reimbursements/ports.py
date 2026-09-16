"""Persistence ports for immutable reimbursement v1 records.

Adapters in Lane C may depend on database technology. These protocols may not.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.reimbursement import (
    AuditEvent,
    OrganizationProfile,
    PolicySnapshot,
    ProcessingPacket,
    ReimbursementCase,
)


class CaseRepository(Protocol):
    """Stores and retrieves immutable case and configuration snapshots."""

    def case_exists(self, case_id: str) -> bool:
        """Return whether an immutable snapshot exists for the supplied case ID."""

    def append_case_snapshot(
        self,
        *,
        case: ReimbursementCase,
        profile_snapshot: OrganizationProfile,
        policy_snapshot: PolicySnapshot,
        input_hash: str,
        idempotency_key: str,
    ) -> None:
        """Append the case and its reproducibility inputs in one unit of work."""

    def get_case_snapshot(self, case_id: str) -> ReimbursementCase | None:
        """Return the stored case snapshot without reevaluating it."""


class AuditEventRepository(Protocol):
    """Appends and reads ordered immutable audit events."""

    def append_events(self, case_id: str, events: Sequence[AuditEvent]) -> None:
        """Append events without changing earlier events."""

    def list_events(self, case_id: str) -> Sequence[AuditEvent]:
        """Return the ordered event history for a case."""


class ControlEventRepository(Protocol):
    """Records control events and idempotency receipts as append-only data."""

    def idempotency_key_exists(self, case_id: str, idempotency_key: str) -> bool:
        """Return whether a control command was already recorded for its key."""

    def append_control_event(
        self,
        case_id: str,
        event: AuditEvent,
        *,
        idempotency_key: str,
    ) -> None:
        """Append exactly one compensable control event and its receipt."""


class OutcomeRepository(Protocol):
    """Stores and retrieves the immutable output packet for a case."""

    def append_processing_packet(self, case_id: str, packet: ProcessingPacket) -> None:
        """Append the agent processing result without mutating an earlier result."""

    def get_processing_packet(self, case_id: str) -> ProcessingPacket | None:
        """Return the stored result packet without reevaluation."""
