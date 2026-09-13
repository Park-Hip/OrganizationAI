# Temporary System Contract v0.2

## Document control

**Status:** Temporary development contract - non-canonical.

**Depends on:** [03_temporary_demo_policy.md](03_temporary_demo_policy.md).

**Purpose:** Define the frozen Layer 0 vocabulary, record shapes, temporary profile, and deterministic evaluation boundary for `TMP-DEV-001`.

**Not a claim:** This is not the future club workflow, pilot policy, public API, or production data contract.

---

## 1. Invariants

1. The only supported claim route is `SELF_PAID`; the client payload has no route field.
2. Each case has exactly one optional expense object.
3. Every `Expense` business field can be null so a later evaluator can return a safe `MISSING_FACT` decision.
4. A client cannot submit profile or provenance fields.
5. The evaluator is deterministic: the same normalized case and immutable profile snapshot produce the same decision.
6. A decision never makes, authorizes, or reports a payment.
7. Persistence and append-only audit records are defined by the persistence layer, not by Layer 0.

## 2. Frozen enums

All enums subclass `str` and `Enum` for stable serialization.

| Enum | Permitted values | Purpose |
| --- | --- | --- |
| `TemporaryCategory` | `TEST_ALLOWED`, `TEST_BLOCKED` | Temporary category labels, none of which is a real category. |
| `EvidenceStatus` | `PRESENT`, `NOT_PROVIDED` | A requester declaration about evidence, not a receipt check. |
| `DecisionOutcome` | `AUTO_APPROVED`, `MISSING_FACT`, `OUT_OF_POLICY`, `AUTHORITY_EXCEEDED` | The four temporary decision results. |
| `TemporaryRuleId` | `TMP-REQ-01`, `TMP-CAT-01`, `TMP-EVD-01`, `TMP-AUT-01`, `TMP-AUT-02` | Typed evidence for the single rule a future evaluator applies. |
| `ProfileSource` | `TEMPORARY_DEVELOPMENT` | Temporary provenance marker. |
| `DataClass` | `SYNTHETIC` | Temporary provenance marker. |
| `WorkflowValidationStatus` | `UNVALIDATED` | Temporary provenance marker. |

There are no `ClaimRoute`, `ReviewerRoute`, `CaseState`, `AuditAction`, `AuditActor`, or `QuestionKey` enums in Layer 0.

## 3. Frozen record shapes

All shapes are frozen Pydantic v2 models with `extra="forbid"`.
No global string stripping is enabled, because whitespace-only business text must remain available for later missing-fact normalization.

### 3.1 `Expense`

One optional expense line.

| Field | Type | Meaning |
| --- | --- | --- |
| `category` | `TemporaryCategory` or null | Expense category. |
| `description` | string or null | Stated expense description. |
| `amount_vnd` | positive integer or null | Synthetic integer amount only. |
| `expense_date` | valid date or null | Expense fact. |
| `evidence_status` | `EvidenceStatus` or null | Declared evidence state; null is a missing business fact. |

A null field is a missing business fact for the evaluator, not a transport error.

### 3.2 `CaseSubmission`

The client transport shape.

| Field | Type | Meaning |
| --- | --- | --- |
| `case_id` | non-blank string | Synthetic unique ID supplied by the test client. |
| `submitted_at` | valid timestamp | Client assertion of submission time. |
| `requester_role` | string or null | Synthetic role label only. |
| `purpose` | string or null | Stated purpose. |
| `expense` | `Expense` or null | Exactly one optional expense object. |

The shape has no profile, provenance, claim route, activity reference, or reviewer route.

### 3.3 `NormalizedCase`

Same fields as `CaseSubmission`.
Layer 0 creates the type only; normalization rules are deferred.

### 3.4 `TemporaryProfile`

An immutable server-owned snapshot.

| Field | Type | Meaning |
| --- | --- | --- |
| `profile_id` | non-blank string | Profile identifier. |
| `profile_source` | `ProfileSource` | Provenance marker. |
| `data_class` | `DataClass` | Provenance marker. |
| `workflow_validation_status` | `WorkflowValidationStatus` | Provenance marker. |
| `allowed_categories` | `frozenset[TemporaryCategory]` | The only categories in policy. |
| `required_evidence_status` | `EvidenceStatus` | The evidence state the policy requires. |
| `auto_approve_limit_vnd` | positive integer | Inclusive automatic approval limit. |

There is no `blocked_categories`, `authority_exceeded_route`, or reviewer route field.

### 3.5 `DecisionDraft`

A pure decision result.

| Field | Type | Meaning |
| --- | --- | --- |
| `outcome` | `DecisionOutcome` | Result of deterministic evaluation. |
| `applied_rule_id` | `TemporaryRuleId` | The single first-applicable rule. |
| `reason` | non-blank string | Short, user-readable explanation. |
| `question` | string or null | Nullable question text only; no question key. |
| `profile_id` | non-blank string | Links the result to the profile that produced it. |

The shape has no route, question key, decision ID, timestamp, audit state, or persistence snapshot.

## 4. Temporary profile constant

`backend/app/policy/profile.py` exports exactly one immutable constant, `TMP_DEV_001_PROFILE`.

| Field | Value |
| --- | --- |
| `profile_id` | `TMP-DEV-001` |
| `profile_source` | `TEMPORARY_DEVELOPMENT` |
| `data_class` | `SYNTHETIC` |
| `workflow_validation_status` | `UNVALIDATED` |
| `allowed_categories` | `{TEST_ALLOWED}` |
| `required_evidence_status` | `PRESENT` |
| `auto_approve_limit_vnd` | `1000` |

No client request, environment variable, fixture, or query parameter can select or alter this profile.

## 5. Evidence declaration

`evidence_status` lives on the `Expense` object.

There is no file field, upload endpoint, object storage, receipt parser, OCR component, checksum, image inspection, or evidence review state.

`PRESENT` means the requester declares that evidence exists.
It does not mean OrganizationalAI received, read, authenticated, or verified proof.

`NOT_PROVIDED` means the requester declares that evidence is absent.

A null `evidence_status` is a missing business fact that a later evaluator can ask to repair.

## 6. Evaluation contract

### 6.1 Pure evaluator boundary

```text
normalized temporary case + immutable TMP-DEV-001 profile snapshot
    -> deterministic DecisionDraft
```

The future evaluator has no HTTP, database, LLM, clock, file, payment, or external-service dependency.
Layer 0 freezes only the input and output types and the profile constant.

### 6.2 Rule precedence

| Priority | Check | Result |
| --- | --- | --- |
| 1 | Routine-decision fact is null, blank, or otherwise absent. | `MISSING_FACT` using `TMP-REQ-01`. Ask for the first missing fact. |
| 2 | Category is not in the allow-list. | `OUT_OF_POLICY` using `TMP-CAT-01`. Flag for later human handling. |
| 3 | `expense.evidence_status` is not `PRESENT`. | `MISSING_FACT` using `TMP-EVD-01`. Ask for expense proof/reference. |
| 4 | Allowed, evidenced amount is greater than `1000`. | `AUTHORITY_EXCEEDED` using `TMP-AUT-02`. Flag for later human handling. |
| 5 | No previous condition applies. | `AUTO_APPROVED` using `TMP-AUT-01`. |

The documented missing-fact field order is deferred to the normalization layer.

## 7. Structural validation versus missing business facts

| Condition | Layer 0 behavior |
| --- | --- |
| Blank `case_id`, invalid timestamp, unknown enum token, boolean or non-integer amount, or zero or negative amount | Rejected by the record shape validator before a future evaluator runs. |
| A business field that is null or blank in an otherwise transport-valid case | Allowed by the record shape; the future evaluator returns `MISSING_FACT`. |

`INPUT_INVALID` is a future adapter error label, not a `DecisionOutcome` and not part of the real-policy outcome vocabulary.

## 8. Explicitly deferred

- Whitespace normalization and missing-field order.
- Question wording and question keys.
- Policy evaluation and rule precedence implementation.
- Fixture loading and evaluator matrix tests.
- Case, decision, and audit persistence.
- API endpoints and response serialization.
- Reviewer queues, approval actions, and real authority claims.
- Evidence upload, storage, OCR, receipt inspection, or verification.
- Real workflow migration.

## 9. Replacement gate

This contract must be replaced, not patched silently, when a validated workflow exists.
A replacement must:

- use a new profile ID/source/version;
- map observed packet artifacts to input fields deliberately;
- obtain a named owner's approval for policy/authority behavior;
- preserve temporary records as synthetic historical data;
- revise evaluator tests, API wording, policy document, and public fixtures together.