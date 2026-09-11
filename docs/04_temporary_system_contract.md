# Temporary System Contract v0.1

## Document control

**Status:** Temporary development contract — non-canonical.

**Depends on:** [03_temporary_demo_policy.md](03_temporary_demo_policy.md).

**Purpose:** Define the exact temporary backend records, evaluator boundary, persistence behavior, and service operations needed to implement `TMP-DEV-001`.

**Not a claim:** This is not the future club workflow, pilot policy, public API, or production data contract.

---

## 1. Invariants

1. Every persisted record is synthetic and carries `profile_id = TMP-DEV-001`, `profile_source = TEMPORARY_DEVELOPMENT`, `data_class = SYNTHETIC`, and `workflow_validation_status = UNVALIDATED`.
2. The service stamps provenance; a client cannot select a different profile.
3. The only claim route is `SELF_PAID`.
4. Each case has exactly one expense object.
5. The evaluator is deterministic: the same normalized case and immutable profile snapshot produce the same decision.
6. A decision does not make, authorize, or report a payment.
7. Audit events are append-only. A stored snapshot is never updated in place.

## 2. Type definitions

### 2.1 Primitive enums

| Type | Permitted values |
| --- | --- |
| `ClaimRoute` | `SELF_PAID` |
| `EvidenceProofStatus` | `PRESENT`, `NOT_PROVIDED`, `UNREADABLE`, `AMBIGUOUS` |
| `TemporaryCategory` | `TEST_ALLOWED`, `TEST_BLOCKED` |
| `DecisionOutcome` | `AUTO_APPROVED`, `MISSING_FACT`, `OUT_OF_POLICY`, `AUTHORITY_EXCEEDED` |
| `ReviewerRoute` | `TREASURER` |
| `CaseState` | `SUBMITTED`, `EVALUATED` |
| `AuditAction` | `SUBMITTED`, `EVALUATED` |
| `AuditActor` | `TEST_CLIENT`, `SYSTEM` |

### 2.2 Case submission

The transport contract allows a business field to be absent/null so the evaluator can return a safe `MISSING_FACT` decision. A malformed transport value is handled separately in section 5.

| Field | Type | Required by transport | Required for a routine decision | Notes |
| --- | --- | --- | --- | --- |
| `case_id` | non-empty string | Yes | Yes | Synthetic unique ID supplied by the test client. |
| `submitted_at` | valid timestamp | Yes | Yes | Client assertion of submission time; server also records event time. |
| `requester_role` | non-empty string or null | Yes | Yes | Synthetic role label only. |
| `claim_route` | `SELF_PAID` or null | Yes | Yes | Any other valid enum is intentionally unsupported. |
| `activity_ref` | non-empty string or null | Yes | Yes | Synthetic activity reference. |
| `purpose` | non-empty string or null | Yes | Yes | Stated purpose. |
| `expense` | object or null | Yes | Yes | Exactly one object in v0.1. |
| `expense.category` | `TemporaryCategory` or null | Yes when expense exists | Yes | Profile applies category rule. |
| `expense.description` | non-empty string or null | Yes when expense exists | Yes | Stated expense description. |
| `expense.amount_vnd` | positive integer or null | Yes when expense exists | Yes | Synthetic integer only; no real spend. |
| `expense.expense_date` | valid date or null | Yes when expense exists | Yes | Expense fact. |
| `expense_proof_status` | `EvidenceProofStatus` or null | Yes | Yes | Declared status; no file analysis occurs. |

The client must not submit profile/provenance fields. The service adds them when the case is accepted.

### 2.3 Temporary profile snapshot

A case evaluation uses an immutable copy of this profile:

| Field | Value |
| --- | --- |
| `profile_id` | `TMP-DEV-001` |
| `profile_source` | `TEMPORARY_DEVELOPMENT` |
| `data_class` | `SYNTHETIC` |
| `workflow_validation_status` | `UNVALIDATED` |
| `allowed_categories` | `TEST_ALLOWED` |
| `blocked_categories` | `TEST_BLOCKED` |
| `required_evidence_status` | `PRESENT` |
| `dev_auto_limit_vnd` | `1000` |
| `authority_exceeded_route` | `TREASURER` |

### 2.4 Decision

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `decision_id` | server-generated unique ID | Yes | Identifies one evaluator result. |
| `case_id` | string | Yes | Links decision to immutable case snapshot. |
| `outcome` | `DecisionOutcome` | Yes | Result of deterministic evaluation. |
| `applied_rule_ids` | non-empty list of strings | Yes | `TMP-REQ-01`, `TMP-CAT-01`, `TMP-EVD-01`, `TMP-AUT-01`, or `TMP-AUT-02` as applicable. |
| `reason` | non-empty string | Yes | Short, user-readable explanation. |
| `question` | non-empty string or null | Conditional | Required for `MISSING_FACT`, `OUT_OF_POLICY`, and `AUTHORITY_EXCEEDED`; null for routine result. |
| `reviewer_route` | `TREASURER` or null | Conditional | Required for `OUT_OF_POLICY` and `AUTHORITY_EXCEEDED`; null otherwise. |
| `decision_state` | `EVALUATED` | Yes | Temporary terminal state. |
| `created_at` | server timestamp | Yes | Time of evaluation. |
| `profile_snapshot` | immutable profile object | Yes | Proves temporary behavior and provenance. |

For `AUTO_APPROVED`, the reason/output must include: **“Approved under temporary development profile; no payment was made.”**

### 2.5 Append-only audit event

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `event_id` | server-generated unique ID | Yes | Audit identifier. |
| `case_id` | string | Yes | Related synthetic case. |
| `action` | `SUBMITTED` or `EVALUATED` | Yes | Event type. |
| `actor` | `TEST_CLIENT` or `SYSTEM` | Yes | `TEST_CLIENT` submits; `SYSTEM` evaluates. |
| `created_at` | server timestamp | Yes | Authoritative event order. |
| `prior_event_id` | string or null | Yes | Null for first event; points to prior event afterward. |
| `case_snapshot` | immutable case object | Yes | Full normalized submission as used at that event. |
| `profile_snapshot` | immutable profile object | Yes | Required on every event. |
| `decision_snapshot` | decision object or null | Conditional | Present only on `EVALUATED`. |

## 3. Evaluation contract

### 3.1 Pure evaluator boundary

```text
normalized temporary case + immutable TMP-DEV-001 profile snapshot
    → deterministic Decision
```

The pure evaluator has no HTTP, database, LLM, clock, file, payment, or external-service dependency. The adapter creates IDs/timestamps and persists returned records.

### 3.2 Rule precedence

| Priority | Check | Result |
| --- | --- | --- |
| 1 | Routine-decision fact is null, blank, or otherwise absent. | `MISSING_FACT` using `TMP-REQ-01`. Ask for the first missing fact in documented field order. |
| 2 | Category is `TEST_BLOCKED` or not in the temporary profile. | `OUT_OF_POLICY` using `TMP-CAT-01`; route to `TREASURER`. |
| 3 | `expense_proof_status` is not `PRESENT`. | `MISSING_FACT` using `TMP-EVD-01`. Ask for expense proof/reference. |
| 4 | Allowed, evidenced amount is greater than `1000`. | `AUTHORITY_EXCEEDED` using `TMP-AUT-02`; route to `TREASURER`. |
| 5 | No previous condition applies. | `AUTO_APPROVED` using `TMP-AUT-01`. |

Documented missing-fact field order: `requester_role`, `claim_route`, `activity_ref`, `purpose`, `expense`, `expense.category`, `expense.description`, `expense.amount_vnd`, `expense.expense_date`, `expense_proof_status`.

## 4. State and persistence behavior

```text
valid transport submission
  → persist Case[state=SUBMITTED]
  → append Audit[SUBMITTED, actor=TEST_CLIENT]
  → evaluate synchronously
  → persist Decision[state=EVALUATED]
  → append Audit[EVALUATED, actor=SYSTEM]
  → return case + decision + ordered audit history
```

- A temporary case is evaluated once in v0.1; `EVALUATED` is terminal.
- There are no temporary human approve/reject, pause, undo, payment, or re-evaluate operations.
- Case, decision, and audit records must be queryable by `case_id` after persistence.
- If persistence of the decision/audit cannot complete, the service must not report a successful evaluation response.

## 5. Adapter validation versus business missing facts

| Condition | Service result | Persists a case/decision? |
| --- | --- | --- |
| Malformed body, missing `case_id`/`submitted_at`, invalid timestamp, invalid enum token, non-integer amount, zero/negative amount, or an unsupported route token | Transport validation error `INPUT_INVALID`; list exact invalid field(s). | No. This is not a business decision. |
| Valid transport shape but a business-required field is null/blank | Evaluator returns `MISSING_FACT`. | Yes: submitted case, decision, and two audit events. |
| Valid complete shape | Evaluator returns one of the four temporary outcomes. | Yes: submitted case, decision, and two audit events. |

`INPUT_INVALID` is an adapter error label, not a `DecisionOutcome` and not part of the future real-policy outcome vocabulary.

## 6. Minimum service operations

The technology/framework may choose endpoint names, but it must provide these operations:

| Operation | Input | Output | Constraints |
| --- | --- | --- | --- |
| Submit and evaluate temporary case | `CaseSubmission` | `CaseDetail` or `INPUT_INVALID` | Server stamps temporary provenance and evaluates synchronously. |
| Read temporary case detail | `case_id` | Case snapshot, decision, ordered audit history, profile provenance | Must visibly identify temporary/synthetic/unvalidated status. |
| Run fixture suite | None or fixture selector | Per-fixture expected/actual outcome and pass/fail | Must use the same evaluator path as case submission. |

## 7. Required fixture expectations

Use the fixture IDs and rules from [03_temporary_demo_policy.md](03_temporary_demo_policy.md) and [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv):

| Fixture | Expected outcome | Key assertion |
| --- | --- | --- |
| `TMP-001` | `AUTO_APPROVED` | Result contains temporary/no-payment disclosure and `TMP-AUT-01`. |
| `TMP-002` | `MISSING_FACT` | Question identifies `activity_ref`. |
| `TMP-003` | `MISSING_FACT` | Question identifies expense proof/reference. |
| `TMP-004` | `OUT_OF_POLICY` | Route is `TREASURER`; rule is `TMP-CAT-01`. |
| `TMP-005` | `AUTHORITY_EXCEEDED` | Route is `TREASURER`; rule is `TMP-AUT-02`. |
| `TMP-006` | `AUTO_APPROVED` | Exact authority boundary (`1000`) is inclusive. |

Every persisted fixture case must have exactly two ordered audit events: `SUBMITTED`, then `EVALUATED`.

## 8. Replacement gate

This contract must be replaced, not patched silently, when a validated workflow exists. A replacement must:

- use a new profile ID/source/version;
- map observed packet artifacts to input fields deliberately;
- obtain a named owner’s approval for policy/authority behavior;
- preserve temporary records as synthetic historical data;
- revise evaluator tests, API wording, policy document, and public fixtures together.
