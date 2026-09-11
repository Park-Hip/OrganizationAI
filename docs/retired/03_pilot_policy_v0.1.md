# Pilot Policy v0.1 (Provisional)

## Document control

**Status:** Proposed provisional baseline. Not approved club-finance policy.

**Policy owner:** Treasurer and president (pending policy-owner confirmation).

**Reviewer:** Backend owner.

**Validation status:** Proposed until approved in writing by the named policy owners.

**Classification:** This is a temporary, replaceable, synthetic policy foundation for the campus student-club reimbursement prototype. Rule IDs and outcomes describe proposed behavior, not validated organizational policy.

## Policy metadata

| Field | Value |
| --- | --- |
| Policy ID | `POL-REF-TEMP-0.1` |
| Version | `v0.1-provisional` |
| Effective date | Not effective. Provisional until policy-owner review. |
| Applies to | Synthetic campus student-club expense reimbursement scenarios for one participating club. |
| Approved by | Not approved. Pending policy-owner confirmation. |

## Required facts

A required fact is missing when it is absent, empty, zero where a positive value is required, ambiguous, or contradictory. A missing required fact always stops the request as `MISSING_FACT`.

| Field | Required condition | Missing / invalid behavior | Rule ID |
| --- | --- | --- | --- |
| Requester role | Non-empty proposed scenario role label (e.g. `event_lead`). | Absent or empty → `MISSING_FACT`; ask for the requester role. | `REQ-01` |
| Event reference | Non-empty, unambiguous single event reference. | Absent, empty, or ambiguous → `MISSING_FACT`; ask for one specific reference. | `REQ-02` |
| Expense category | Non-empty and normalized to an allowed category value. | Absent or empty → `MISSING_FACT`; present but not allowed → `OUT_OF_POLICY` via `ELG-04`. | `REQ-03` |
| Amount | Positive number greater than zero. | Absent, zero, negative, or non-numeric → `MISSING_FACT`. | `REQ-04` |
| Receipt status | Exactly one value from the receipt enum (`READABLE`, `UNREADABLE`, `NOT_PROVIDED`, `AMBIGUOUS`). | Absent or invalid → `MISSING_FACT`. | `REQ-05` |
| Description | Non-empty description of the expense. | Absent or empty → `MISSING_FACT`. | `REQ-06` |

## Receipt evidence

| Receipt status | Meaning (proposed) | Outcome | Rule ID |
| --- | --- | --- | --- |
| `READABLE` | Readable proof supports the expense. | Proceed to the next evaluation step. | `RCT-01` |
| `UNREADABLE` | Proof exists but cannot be read. | `MISSING_FACT` — request readable proof or confirmation. | `RCT-02` |
| `NOT_PROVIDED` | No proof was submitted. | `MISSING_FACT` — request readable proof or confirmation. | `RCT-03` |
| `AMBIGUOUS` | Proof is unclear or conflicting. | `MISSING_FACT` — request readable proof or confirmation. | `RCT-04` |

## Eligibility rules

Starter categories are proposed placeholder candidates and are not claimed as real club categories.

| Rule ID | Condition | Outcome if satisfied | Outcome if not satisfied |
| --- | --- | --- | --- |
| `ELG-01` | Category is exactly `VENUE`. | Eligible category; continue. | Not applicable to this category. |
| `ELG-02` | Category is exactly `PRINTING`. | Eligible category; continue. | Not applicable to this category. |
| `ELG-03` | Category is exactly `EVENT_MATERIALS`. | Eligible category; continue. | Not applicable to this category. |
| `ELG-04` | Category is not one of `VENUE`, `PRINTING`, `EVENT_MATERIALS` (unknown or excluded). | Not covered by the proposed policy. | `OUT_OF_POLICY` with a Treasurer exception question. |

## Authority matrix

Authority comparisons use parameter names only. **No numeric values are defined.** Both parameters remain unresolved until a policy owner confirms them.

| Decision | Automated authority | Treasurer authority | President authority | Rule ID |
| --- | --- | --- | --- | --- |
| Routine eligible request | Amount ≤ `AUTO_APPROVAL_LIMIT_VND`. | Not required when within automated authority. | Not required when within automated authority. | `AUT-01` |
| Request above the automated delegation | No final decision. | Amount ≤ `TREASURER_APPROVAL_LIMIT_VND`. | Not applicable while a Treasurer delegation exists. | `AUT-02` |
| Request above the Treasurer delegation | No final decision. | No final decision. | Deferred; later policy version only. | `AUT-03` |
| Policy exception (unknown or excluded category) | No final decision. | Proposed exception owner. | Deferred; later policy version only. | `ELG-04` |

`AUT-01`, `AUT-02`, and `AUT-03` are **blocked** until `AUTO_APPROVAL_LIMIT_VND` and `TREASURER_APPROVAL_LIMIT_VND` are confirmed. The evaluator must not fabricate numeric coverage in the meantime.

## Outcomes

| Outcome | Condition | Required system behavior |
| --- | --- | --- |
| `AUTO_APPROVED` | Required facts complete, category eligible, receipt readable, and amount within automated delegation. | Complete the routine decision and append an audit event. |
| `MISSING_FACT` | A required fact is missing, ambiguous, or contradictory; or receipt is unreadable, not provided, or ambiguous. | Stop without approval or rejection and ask for the exact fact or readable proof. |
| `OUT_OF_POLICY` | Category is unknown or excluded (`ELG-04`). | Stop, cite the rule, and ask the Treasurer whether an exception is allowed. |
| `AUTHORITY_EXCEEDED` | The request may be valid but exceeds the automated delegation. | Stop and ask the Treasurer for a specific approval or rejection. Blocked until parameters are confirmed. |

## Evaluation precedence

The evaluator applies rules strictly in this order and stops at the first triggered escalation:

1. **Required facts** (`REQ-01`–`REQ-06`) → missing, ambiguous, or contradictory → `MISSING_FACT`.
2. **Coverage** (`ELG-01`–`ELG-04`) → unknown or excluded category → `OUT_OF_POLICY`.
3. **Receipt evidence** (`RCT-01`–`RCT-04`) → `UNREADABLE`, `NOT_PROVIDED`, or `AMBIGUOUS` → `MISSING_FACT`.
4. **Authority** (`AUT-01`–`AUT-03`) → above the automated delegation → `AUTHORITY_EXCEEDED`.
5. **Automatic completion** → only when every prior step passes → `AUTO_APPROVED`.

## Escalation rules

Every escalation follows the same shape: observed fact or rule → consequence → named decision owner → one answerable question.

| Escalation type | Trigger | Named decision owner | Required question template | Rule ID |
| --- | --- | --- | --- | --- |
| `MISSING_FACT` | Any required fact is missing, ambiguous, or contradictory; or receipt is `UNREADABLE`, `NOT_PROVIDED`, or `AMBIGUOUS`. | Treasurer (proposed escalation owner); the direct question asks the Requester for the missing fact. | The request cannot be decided because [required fact] is [missing / ambiguous / unreadable] (rule [ID]). Provide the correct, readable [required fact], or confirm that the Treasurer should decide without it? | `ESC-01` |
| `OUT_OF_POLICY` | Category is not `VENUE`, `PRINTING`, or `EVENT_MATERIALS` (`ELG-04`). | Treasurer (proposed exception owner). | The category [value] is not `VENUE`, `PRINTING`, or `EVENT_MATERIALS` (rule `ELG-04`), so the request is outside policy. Treasurer, do you authorize this exception? | `ESC-02` |
| `AUTHORITY_EXCEEDED` | Amount is above the automated delegation (`AUT-02`, blocked until parameters are confirmed). | Treasurer (higher authority; President deferred). | The amount exceeds the automated delegation (rule `AUT-02`; `AUTO_APPROVAL_LIMIT_VND` unconfirmed). Treasurer, do you approve this specific reimbursement amount? | `ESC-03` |

## Approval record

No reviewer has approved this provisional policy. Names and approvals are intentionally not invented.

| Reviewer | Decision | Date | Evidence link | Notes |
| --- | --- | --- | --- | --- |
| Treasurer | Pending | Not yet confirmed | Not yet produced | Proposed scenario role; not authorization. |
| President | Deferred | Not yet confirmed | Not yet produced | Possible later role only. |