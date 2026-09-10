# System Contract

## Document control

**Status:** Skeleton.

**Owner:** Decision engineer.

## Request contract

| Field | Type | Required | Validation rule | Example |
| --- | --- | --- | --- | --- |
| [To be completed] | [To be completed] | [To be completed] | [To be completed] | [To be completed] |

## Decision contract

| Field | Type | Description |
| --- | --- | --- |
| Outcome | Enum | `AUTO_APPROVED`, `MISSING_FACT`, `OUT_OF_POLICY`, or `AUTHORITY_EXCEEDED`. |
| Policy version | String | Version used by the evaluator. |
| Rule IDs | String array | Rules supporting the result. |
| Explanation | String | Plain-language reason for the result. |
| Escalation question | String or null | One answerable question when a human decision is required. |

## State transitions

| From state | Action | To state | Actor | Audit event |
| --- | --- | --- | --- | --- |
| [To be completed] | [To be completed] | [To be completed] | [To be completed] | [To be completed] |

## Audit-event contract

| Field | Description |
| --- | --- |
| Event ID | Immutable event identifier. |
| Request ID | Identifier of the related reimbursement request. |
| Occurred at | Timestamp of the event. |
| Actor type | System, requester, treasurer, or president. |
| Action | Submitted, decided, approved, rejected, paused, or undone action. |
| Input snapshot | Decision-relevant facts captured at the time of action. |
| Policy and rules | Applied policy version and rule identifiers. |
| Reason | Explanation for the action or result. |
| Previous event ID | Related prior event for an undo or compensating action. |

## Control contract

| Control | Permitted actor | Precondition | Visible result |
| --- | --- | --- | --- |
| Approve | [To be completed] | [To be completed] | [To be completed] |
| Reject | [To be completed] | [To be completed] | [To be completed] |
| Pause automation | [To be completed] | [To be completed] | [To be completed] |
| Undo | [To be completed] | [To be completed] | [To be completed] |
