"""Published pure evaluator seam for reimbursement v1.

SETUP-04 freezes this signature only. Lane A supplies the deterministic rule
implementation without changing the domain or infrastructure boundary.
"""

from __future__ import annotations

from app.domain.reimbursement import (
    ControlState,
    OrganizationProfile,
    PolicySnapshot,
    ProcessingPacket,
    ReimbursementCase,
)


def evaluate(
    case: ReimbursementCase,
    profile_snapshot: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
    control_state: ControlState,
) -> ProcessingPacket:
    """Evaluate a case against immutable snapshots.

    The evaluator has no access to a clock, database, network, file storage,
    LLM, authenticated actor, or payment system. It remains unimplemented at
    this seam so Lane A can add policy behavior without changing its contract.
    """
    del case, profile_snapshot, policy_snapshot, control_state
    raise NotImplementedError("reimbursement v1 policy evaluation is implemented by Lane A")
