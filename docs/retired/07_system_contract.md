# System Contract

## Document control

**Status:** Proposed provisional baseline. No framework, database, or API implementation is asserted.

**Owner:** Backend owner.

**Reviewer:** UI/UX and QA owners.

**Classification:** This document defines the shared vocabulary for the Policy Forge provisional baseline only. It does not introduce Pydantic/JSON schemas, API paths, SQL, idempotency implementation, or RBAC.

## Shared enums

These names are the single source of truth for backend, UI, and QA. They match [01_project_spec.md](01_project_spec.md) and [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md) exactly.

| Enum | Values |
| --- | --- |
| Outcome | `AUTO_APPROVED`, `MISSING_FACT`, `OUT_OF_POLICY`, `AUTHORITY_EXCEEDED` |
| Receipt status | `READABLE`, `UNREADABLE`, `NOT_PROVIDED`, `AMBIGUOUS` |
| Allowed category | `VENUE`, `PRINTING`, `EVENT_MATERIALS` |
| Escalation type | `MISSING_FACT`, `OUT_OF_POLICY`, `AUTHORITY_EXCEEDED`, or `null` |
| Actor | `SYSTEM`, `REQUESTER`, `TREASURER`, `PRESIDENT` |

`Escalation type` is the three escalation values for an escalated decision and `null` for an `AUTO_APPROVED` decision.

`PRESIDENT` is reserved as a possible later actor and is not part of the current pilot decision path.

## Request contract

The request contains exactly the six required facts defined in `REQ-01`–`REQ-06`.

| Field | Type | Required | Validation rule | Example |
| --- | --- | --- | --- | --- |
| `requester_role` | String | Yes | Non-empty proposed scenario role label. | `event_lead` |
| `event_reference` | String | Yes | Non-empty, unambiguous single event reference. | `EVT-2026-001` |
| `expense_category` | String (enum) | Yes | Normalized to `VENUE`, `PRINTING`, or `EVENT_MATERIALS` for eligibility; any other value is `OUT_OF_POLICY`. | `VENUE` |
| `amount_vnd` | Number | Yes | Positive number greater than zero. | `3000000` |
| `receipt_status` | String (enum) | Yes | One of `READABLE`, `UNREADABLE`, `NOT_PROVIDED`, `AMBIGUOUS`. | `READABLE` |
| `description` | String | Yes | Non-empty expense description. | `Venue deposit for spring event` |

## Decision contract

| Field | Type | Description |
| --- | --- | --- |
| `request_id` | String | Identifier of the related reimbursement request. |
| `policy_id` | String | Applied policy identifier, e.g. `POL-REF-TEMP-0.1`. |
| `policy_version` | String | Applied policy version, e.g. `v0.1-provisional`. |
| `outcome` | Enum | One of the four outcome values. |
| `escalation_type` | Enum or null | Escalation value for escalated decisions; `null` for `AUTO_APPROVED`. |
| `matched_rule_ids` | String array | Rule IDs that produced the result, e.g. `REQ-*`, `ELG-*`, `RCT-*`, `AUT-*`, `ESC-*`. |
| `facts_used` | Object | The normalized input facts the evaluator actually used. |
| `explanation` | String | Plain-language reason for the result. |
| `named_owner` | String or null | Named decision owner for an escalation (e.g. `REQUESTER`, `TREASURER`); `null` for `AUTO_APPROVED`. |
| `question` | String or null | One answerable question for an escalation; `null` for `AUTO_APPROVED`. |

The UI must be able to render an escalation using only `outcome`, `escalation_type`, `explanation`, `named_owner`, and `question`.

## Provisional state model

| State | Meaning |
| --- | --- |
| `SUBMITTED` | Request received and not yet decided. |
| `AUTO_APPROVED` | Routine request completed automatically. |
| `AWAITING_INPUT` | A required fact is missing; waiting for the requester. |
| `AWAITING_REVIEW` | A policy or authority escalation is waiting for the Treasurer. |
| `PAUSED` | Automation paused by a human; requests await manual handling. |
| `RESOLVED` | A human resolution (approve/reject/override) was recorded. |
| `REOPENED` | A prior resolution or decision was undone via a compensating event. |

Every outcome has exactly one next state:

| Outcome | Next state |
| --- | --- |
| `AUTO_APPROVED` | `AUTO_APPROVED` |
| `MISSING_FACT` | `AWAITING_INPUT` |
| `OUT_OF_POLICY` | `AWAITING_REVIEW` |
| `AUTHORITY_EXCEEDED` | `AWAITING_REVIEW` |

### Intended transitions

| From state | Action | To state | Actor | Audit event |
| --- | --- | --- | --- | --- |
| (new request) | Submit | `SUBMITTED` | `REQUESTER` | `SUBMITTED` |
| `SUBMITTED` | Evaluate → routine result | `AUTO_APPROVED` | `SYSTEM` | `DECIDED` |
| `SUBMITTED` | Evaluate → missing fact | `AWAITING_INPUT` | `SYSTEM` | `ESCALATED` |
| `SUBMITTED` | Evaluate → out of policy | `AWAITING_REVIEW` | `SYSTEM` | `ESCALATED` |
| `SUBMITTED` | Evaluate → authority exceeded | `AWAITING_REVIEW` | `SYSTEM` | `ESCALATED` |
| `AWAITING_INPUT` | Supply the missing fact | `SUBMITTED` (re-evaluate) | `REQUESTER` | `FACT_SUPPLIED` |
| `AWAITING_REVIEW` | Approve or reject | `RESOLVED` | `TREASURER` | `APPROVED` / `REJECTED` |
| `SUBMITTED` / `AWAITING_*` | Pause automation | `PAUSED` | `TREASURER` | `PAUSED` |
| `PAUSED` | Resume processing | `SUBMITTED` | `TREASURER` | `RESUMED` |
| `AUTO_APPROVED` / `RESOLVED` | Undo a prior action | `REOPENED` | Actor who performed the action | `UNDONE` (compensating event) |

## Audit-event contract

| Field | Description |
| --- | --- |
| `event_id` | Immutable event identifier. |
| `request_id` | Identifier of the related reimbursement request. |
| `occurred_at` | Timestamp of the event. |
| `actor_type` | `SYSTEM`, `REQUESTER`, `TREASURER`, or `PRESIDENT`. |
| `actor_id` | Synthetic demo role label for the actor. |
| `action` | Submitted, decided, escalated, approved, rejected, paused, resumed, or undone. |
| `input_snapshot` | Decision-relevant input facts or a privacy-safe hash captured at the time of action. |
| `policy_version` | Applied policy version. |
| `matched_rule_ids` | Rule IDs supporting the action. |
| `facts_used` | Normalized facts the evaluator used. |
| `result` | Outcome and escalation type when applicable. |
| `question_or_reason` | Human question for an escalation, or the plain-language reason. |
| `previous_event_id` | Prior event ID for an undo or compensating action (reversal relation). |

Actor roles are synthetic demo labels only. Authentication, role-based access control, and real authorization are outside the MVP scope.

## Control contract

| Control | Permitted actor | Precondition | Visible result |
| --- | --- | --- | --- |
| Approve | `TREASURER` | State is `AWAITING_REVIEW`. | State → `RESOLVED`; `APPROVED` audit event appended. |
| Reject | `TREASURER` | State is `AWAITING_REVIEW`. | State → `RESOLVED`; `REJECTED` audit event appended. |
| Pause automation | `TREASURER` | State is `SUBMITTED`, `AWAITING_INPUT`, or `AWAITING_REVIEW`. | State → `PAUSED`; `PAUSED` audit event appended. |
| Undo | Actor who performed the prior action | A prior decision or control event exists. | State → `REOPENED`; compensating `UNDONE` audit event appended; history is never deleted. |