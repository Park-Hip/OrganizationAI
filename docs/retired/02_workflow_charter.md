# Workflow Charter

## Document control

**Status:** Proposed provisional baseline. Not validated by a real policy owner.

**Owner:** Policy & scenario owner.

**Reviewer:** Project lead.

**Validation status:** Pending policy-owner confirmation. No reviewer name or approval is asserted, invented, or implied.

**Classification:** Every workflow, policy, role, and scenario statement in this document is **proposed** and **synthetic** until a real policy owner confirms it in writing.

## Problem statement

This prototype models a campus student-club event expense reimbursement workflow.

When each request must be checked by hand, requests can require repeated review of receipts, expense categories, event references, and approval limits. Even complete, routine requests consume human decision time.

This pilot proposes to complete only routine, complete, eligible requests within a declared delegation, and to escalate anything uncertain, out-of-policy, or above authority to a named human with one answerable question.

All statements above describe the proposed synthetic prototype. They are not validated organizational or institutional finance policy.

## Workflow and participants

| Role | Scenario activity (proposed, synthetic) | Pilot-system interaction (proposed) | Validation source |
| --- | --- | --- | --- |
| Requester | Submits an expense reimbursement request with supporting facts. | Provides structured request data and receives a result or one specific follow-up question. | Scenario role; pending policy-owner confirmation |
| System referee | Does not exist in the modeled workflow. | Applies the proposed versioned policy, routes the request, explains the outcome, and records audit events. | Scenario role (synthetic) |
| Treasurer | Reviews routine requests within a proposed delegated limit and owns proposed policy exceptions. | Resolves requests that need a Treasurer decision; proposed exception and escalation owner. | Scenario role; proposed delegation, not authorization |
| President | Retained only as a possible later role. | Not a current pilot role. | Deferred to a later policy version |

## Product promise

> Synthetic reimbursement requests are auto-completed only when they are routine under a proposed, versioned policy; every exception receives a specific Treasurer question and an append-only audit trail.

## Scope boundary

### In scope

- Proposed, synthetic scenario roles: requester, system referee, Treasurer.
- A proposed versioned policy and rule vocabulary for the Policy Forge provisional baseline.
- Proposed starter expense categories: `VENUE`, `PRINTING`, `EVENT_MATERIALS`.
- Receipt handling that maps unreadable, missing, or ambiguous receipts to `MISSING_FACT`.
- Proposed Treasurer exception ownership.
- Parameterized authority that intentionally has **no numeric limits** yet.

### Out of scope

- Numeric authority or approval limits.
- Real validated club policy, real data, or real receipts.
- President decision path (possible later role only).
- State-machine code, backend, UI, database, or deployment.
- User research and institutional compliance claims.

## Assumptions

| Assumption | Status |
| --- | --- |
| Starter categories `VENUE`, `PRINTING`, and `EVENT_MATERIALS` are placeholder candidates, not real club categories. | Proposed, synthetic |
| An unreadable, missing, or ambiguous receipt is a missing fact (`MISSING_FACT`) and is never auto-completed. | Proposed |
| The Treasurer is the proposed exception and escalation owner. | Proposed delegation |
| No numeric approval limit exists until a policy owner confirms `AUTO_APPROVAL_LIMIT_VND` and `TREASURER_APPROVAL_LIMIT_VND`. | Blocked by policy-owner confirmation |
| The President role is reserved for a possible later version and is not a current pilot role. | Deferred |

## Validation record

| Claim or decision | Evidence source | Status | Date | Owner |
| --- | --- | --- | --- | --- |
| Temporary policy foundation and workflow boundary are proposed and synthetic. | [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md) (`v0.1-provisional`) | Proposed | Not yet confirmed | Policy & scenario owner |
| Treasurer exception ownership is a team-authored proposed delegation. | [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md) | Proposed | Not yet confirmed | Policy & scenario owner |
| `AUTO_APPROVAL_LIMIT_VND` and `TREASURER_APPROVAL_LIMIT_VND` remain unset and unresolved. | [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md) | Blocked by policy-owner confirmation | Not yet confirmed | Policy & scenario owner |

## Sign-off

No reviewer has validated this document. Names and approvals are intentionally not invented.

| Reviewer role | Name or identifier | Decision | Date | Evidence link |
| --- | --- | --- | --- | --- |
| Treasurer | Pending policy-owner confirmation | Pending | Not yet confirmed | Not yet produced |
| President | Deferred (not a current pilot role) | Deferred | Not yet confirmed | Not yet produced |