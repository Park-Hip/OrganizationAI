# Temporary System Contract v0.2

## Document control

**Status:** Temporary development contract - non-canonical.

**Depends on:** [03_temporary_demo_policy.md](03_temporary_demo_policy.md).

**Purpose:** Define the frozen Layer 0 vocabulary, record shapes, and temporary profile, plus the Layer 1 normalization and Layer 2 deterministic evaluation contracts for `TMP-DEV-001`.

**Not a claim:** This is not the future club workflow, pilot policy, public API, or production data contract.

---

## 1. Invariants

1. The temporary policy's synthetic self-paid scope adds no field to `CaseSubmission`.
2. Each case has exactly one optional expense object.
3. Every `Expense` business field can be null so the evaluator can return a safe `MISSING_FACT` decision.
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
| `TemporaryRuleId` | `TMP-REQ-01`, `TMP-CAT-01`, `TMP-EVD-01`, `TMP-AUT-01`, `TMP-AUT-02` | Typed evidence for the single first-applicable rule the evaluator applies. |
| `ProfileSource` | `TEMPORARY_DEVELOPMENT` | Temporary provenance marker. |
| `DataClass` | `SYNTHETIC` | Temporary provenance marker. |
| `WorkflowValidationStatus` | `UNVALIDATED` | Temporary provenance marker. |

This table is the complete Layer 0 enum vocabulary.

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

The shape has no profile, provenance, activity reference, or human-handling assignment.

### 3.3 `NormalizedCase`

Same fields as `CaseSubmission`.
Layer 1 constructs it from a validated `CaseSubmission`.
The normalization rules are defined in section 6.3.

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

The allow-list and automatic-approval limit are the profile's only policy controls.

### 3.5 `DecisionDraft`

A pure decision result.

| Field | Type | Meaning |
| --- | --- | --- |
| `outcome` | `DecisionOutcome` | Result of deterministic evaluation. |
| `applied_rule_id` | `TemporaryRuleId` | The single first-applicable rule. |
| `reason` | non-blank string | Short, user-readable explanation. |
| `question` | string or null | Nullable question text only; no separate identifier. |
| `profile_id` | non-blank string | Links the result to the profile that produced it. |

The shape has no human-handling assignment, separate question identifier, decision ID, timestamp, audit state, or persistence snapshot.

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

A null `evidence_status` is a missing business fact that the evaluator can ask to repair.

## 6. Evaluation contract

### 6.1 Pure evaluator boundary

```text
normalized temporary case + immutable temporary profile snapshot
    -> deterministic DecisionDraft
```

`app.policy.evaluator.evaluate_case` accepts a `NormalizedCase` and an injected immutable `TemporaryProfile` and returns a `DecisionDraft`.
It has no HTTP, database, LLM, clock, file, payment, or external-service dependency.
Layer 0 freezes the input and output types and profile constant, Layer 1 supplies normalization and shared repair questions, and Layer 2 evaluates policy.

### 6.2 Rule precedence

| Priority | Check | Result |
| --- | --- | --- |
| 1 | `purpose`, `requester_role`, the `expense` object, or an expense business field is null, blank, or otherwise absent. | `MISSING_FACT` using `TMP-REQ-01`. Ask for the first missing fact. |
| 2 | Category is not in the allow-list. | `OUT_OF_POLICY` using `TMP-CAT-01`. Flag for later human handling. |
| 3 | `expense.evidence_status` does not equal the profile's required evidence status. | `MISSING_FACT` using `TMP-EVD-01`. Ask for expense proof/reference. |
| 4 | Allowed, evidenced amount is greater than the profile's automatic-approval limit. | `AUTHORITY_EXCEEDED` using `TMP-AUT-02`. Flag for later human handling. |
| 5 | No previous condition applies. | `AUTO_APPROVED` using `TMP-AUT-01`. |

`TMP-DEV-001` requires `PRESENT` evidence and uses the inclusive `1000` automatic-approval limit defined in section 4.
The first-missing-fact field order and repair wording are defined in section 6.3.

### 6.3 Normalization and repair questions

The Layer 1 normalizer is a pure function from `CaseSubmission` to `NormalizedCase`.
It copies every field and applies one change: a `purpose` or `expense.description` value with no non-whitespace content becomes null.
A nonblank string is preserved exactly, including surrounding whitespace.
`case_id` and `requester_role` are never altered.
The evaluator independently treats a null or whitespace-only `requester_role` as missing.

The required-fact scope is `purpose`, `requester_role`, the `expense` object, and every `Expense` business field.

The first-missing-fact order is fixed:

1. `purpose`
2. `requester_role`
3. `expense`
4. `expense.category`
5. `expense.description`
6. `expense.amount_vnd`
7. `expense.expense_date`
8. `expense.evidence_status`

The six purpose and expense-field questions are owned by the Layer 1 canonical mapping.
Layer 2 owns the requester-role and expense-object questions.

Each field has one exact repair question:

- `purpose`: the question `What is the synthetic purpose of this expense?`
- `requester_role`: the question `What is the synthetic requester role for this request?`
- `expense`: the question `What synthetic expense should this request cover?`
- `expense.category`: the question `Which temporary expense category applies to this synthetic expense?`
- `expense.description`: the question `What is the synthetic expense description?`
- `expense.amount_vnd`: the question `What is the positive integer synthetic expense amount in VND?`
- `expense.expense_date`: the question `What is the synthetic expense date?`
- `expense.evidence_status`: the question `Is the declared synthetic expense evidence status PRESENT or NOT_PROVIDED?`

A declared `NOT_PROVIDED` evidence status is not a structurally missing fact.
Its rule-specific repair wording belongs to the evaluator with `TMP-EVD-01`.

## 7. Structural validation versus missing business facts

| Condition | Layer 0 behavior |
| --- | --- |
| Blank `case_id`, invalid timestamp, unknown enum token, boolean or non-integer amount, or zero or negative amount | Rejected by the record shape validator before the evaluator runs. |
| A business field that is null or blank in an otherwise transport-valid case | Allowed by the record shape; the evaluator returns `MISSING_FACT`. |

`INPUT_INVALID` is a future adapter error label, not a `DecisionOutcome` and not part of the real-policy outcome vocabulary.

## 8. Explicitly deferred

- Case, decision, and audit persistence.
- API endpoints and response serialization.
- Human queues, approval actions, and real authority claims.
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
