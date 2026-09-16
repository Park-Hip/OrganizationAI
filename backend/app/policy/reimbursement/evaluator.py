"""Published pure evaluator seam for reimbursement v1.

SETUP-04 freezes this signature only. Lane A supplies the deterministic rule
implementation without changing the domain or infrastructure boundary.
"""

from __future__ import annotations

from app.domain.reimbursement import (
    ControlState,
    FlowType,
    OrganizationProfile,
    PolicySnapshot,
    ProcessingPacket,
    ProcessingResult,
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
    LLM, authenticated actor, or payment system.
    """
    if profile_snapshot.policy_version != policy_snapshot.policy_version:
        raise ValueError("profile and policy snapshots must use the same policy version")
    if case.paused and control_state is not ControlState.PAUSED:
        raise ValueError("a paused case requires a PAUSED control state")
    packet = _evaluate_policy(case, profile_snapshot, policy_snapshot, control_state)
    _validate_packet_for_case(case, control_state, packet)
    return packet


def _evaluate_policy(
    case: ReimbursementCase,
    profile_snapshot: OrganizationProfile,
    policy_snapshot: PolicySnapshot,
    control_state: ControlState,
) -> ProcessingPacket:
    del case, profile_snapshot, policy_snapshot, control_state
    raise NotImplementedError("reimbursement v1 policy evaluation is implemented by Lane A")


def _validate_packet_for_case(
    case: ReimbursementCase,
    control_state: ControlState,
    packet: ProcessingPacket,
) -> None:
    if packet.control_state is not control_state:
        raise ValueError("processing packet control state must match the evaluator input")
    outcome = packet.outcome
    if outcome is None or outcome.processing_result is not ProcessingResult.ROUTINE_PROCESSED:
        return
    if case.flow_type is FlowType.MEMBER_PAID:
        if outcome.reimbursement_amount_vnd is None:
            raise ValueError("MEMBER_PAID requires a reimbursement amount")
        if outcome.amount_to_return_vnd is not None or outcome.additional_payment_vnd is not None:
            raise ValueError("MEMBER_PAID must not contain advance calculations")
        return
    if outcome.amount_to_return_vnd is None or outcome.additional_payment_vnd is None:
        raise ValueError("ADVANCE_SETTLEMENT requires both advance calculations")
    if outcome.reimbursement_amount_vnd is not None:
        raise ValueError("ADVANCE_SETTLEMENT must not contain a reimbursement amount")
