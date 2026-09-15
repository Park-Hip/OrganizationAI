# Reimbursement System Contract v1.0

## Document control

**Status:** Draft system contract — approved structural direction; awaiting team review before implementation.

**Depends on:**

- [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md)
- [02_MVP_Spec.md](02_MVP_Spec.md)
- [03_reimbursement_policy.md](03_reimbursement_policy.md)

**Canonical machine-readable schema:** [policy-forge-baseline/reimbursement.schema.json](../policy-forge-baseline/reimbursement.schema.json).

**Purpose:** Freeze the versioned data shapes, invariants, deterministic processing boundary, escalation handoff, audit requirements, and migration boundary for reimbursement processing. The policy document owns rule conditions and priorities; this contract owns how systems represent and preserve those decisions.

## 1. Contract invariants

1. The agent never approves, rejects, or transfers money. Every agent-produced outcome has `approval_status: PENDING_HUMAN_APPROVAL`.
2. A processing result is reproducible from the normalized input snapshot, policy version, and immutable organization-profile snapshot.
3. The server owns generated identifiers, policy/profile snapshots, input hashes, audit times, and actor identity derived from authenticated context. A client cannot choose or alter them.
4. A structural validation failure is not a business decision. A structurally valid case with unresolved business facts is processed safely as `ESCALATED / FACT_UNKNOWN`.
5. A case and its policy/profile snapshot are immutable after recording. Correction, pause, human decision, override, and undo create new append-only events; they do not rewrite history.
6. `ROUTINE_PROCESSED` means a review packet has been prepared. It is never a human approval, payment instruction, or settlement confirmation.
7. A pause is an operational state that halts evaluation before every policy rule. It is not a processing outcome or escalation type.
8. The historical `TMP-DEV-001` API, records, and audit events remain labelled synthetic historical data. This contract introduces a separate versioned model and does not reinterpret or mutate those traces.

## 2. Contract envelope

A reimbursement record is represented as a versioned envelope:

```text
policy_version + organization_profile + reimbursement_case + control_state
    -> processing_outcome + optional escalation + append-only audit_events
```

The canonical JSON Schema defines the cross-field rules:

- an `ACTIVE` envelope requires a `processing_outcome`;
- a `PAUSED` envelope has neither a processing outcome nor escalation;
- an `ESCALATED` outcome requires an escalation; and
- a `ROUTINE_PROCESSED` outcome has no escalation.

## 3. Versioned input contracts

### 3.1 `OrganizationProfile`

The profile is server-owned and snapshotted with every case. It configures policy behavior rather than allowing application code to hard-code a club's values.

| Field group | Required contract |
| --- | --- |
| Identity and applicability | `profile_id`, parent organization, accounting regime, policy/profile version, currency, and applicable tax-regime flag. |
| Authority and timing | Routine-processing threshold, threshold operator, submission deadline, conditional non-cash-evidence threshold, and aggregation keys. |
| Policy categories | Allowed, conditional, and prohibited category sets. |
| Roles | Requester, preparer, within-authority approver, over-threshold approver, exception approvers, and payment executor. |
| Safety controls | `no_self_approval: true`; `agent_can_approve: false`; `agent_can_reject: false`; `agent_can_transfer_money: false`. |
| Retention | OCR-artifact retention and official-record retention instruction. |

The profile must be complete and approved before a real case is accepted. Policy Forge defaults are configuration values, not universal club rules.

### 3.2 `PersonRef` and authorization context

`PersonRef` carries `person_id`, display name, and role; contact information is optional and must be minimized. The server derives the authenticated actor identity and permissions from the authorization context, not from a client-selected role field.

The authorization boundary must enforce at minimum:

- a requester may access only their permitted cases;
- a reviewer acts only within their configured role and authority;
- a requester cannot approve their own case;
- a system administrator does not automatically receive financial-decision authority; and
- a payment executor acts only after a recorded human approval.

### 3.3 `Evidence`

An evidence record contains `evidence_id`, type, file hash, readability, and verification state. It may also record OCR confidence, document number/date, amount, and notes.

Permitted evidence types are `INVOICE`, `RECEIPT`, `PAYMENT_PROOF`, `APPROVAL`, `ADVANCE_RECORD`, and `OTHER`. The contract defines evidence metadata and references; it does not prescribe file-storage technology, OCR vendor, or receipt-review UI.

### 3.4 `ExpenseItem`

Each expense item has a line ID, vendor, transaction date, purpose code, description, category, VND amount, payment method, evidence references, and suspicion flags. It may carry tax amount and a line assessment of `PENDING`, `ELIGIBLE`, `FACT_UNKNOWN`, or `OUT_OF_POLICY`.

Related lines use the profile's aggregation keys before authority and conditional tax checks. The complete set of lines is preserved even when one is ineligible or unresolved.

### 3.5 `ReimbursementCase`

| Field group | Contract |
| --- | --- |
| Identity and flow | Non-blank case ID; `flow_type` is `MEMBER_PAID` or `ADVANCE_SETTLEMENT`; requester and submitted time are required. |
| Purpose and budget | Task/event, purpose, budget code, approved budget, remaining budget, and prior-approval references as applicable. |
| Expense packet | One or more expense items, one or more evidence records, declared total, and a masked reimbursement account. |
| Review context | Proposed approver, duplicate-check state, submitted-business-days-after-end, and paused state where applicable. |
| Advance-only fields | `ADVANCE_SETTLEMENT` requires an advance reference and advance amount. |

No full bank account number, raw real receipt, personal identity data, vendor data, credential, or secret may be committed to this repository.

## 4. Deterministic processing boundary

The processing boundary accepts a validated reimbursement case, immutable profile snapshot, policy version/snapshot, and current control state. It produces a processing outcome, an escalation when required, calculation facts, and rule/evidence explanations.

```text
validated case + normalized facts + policy snapshot + profile snapshot + control state
    -> deterministic processing outcome + optional escalation
```

It has no payment, bank, clock, file-storage, network, or LLM dependency. It may normalize text and identifiers only according to documented rules; it must not infer a missing financial fact.

Processing performs the policy's ordered checks, including pause/data integrity, duplicate signals, scope/category, dossier, deadline, budget/conflict/aggregation/authority, conditional tax evidence, calculation, and routine classification. The policy's 21 rules and their priority values remain defined only in [03_reimbursement_policy.md](03_reimbursement_policy.md) and the canonical YAML.

## 5. Output and escalation contracts

### 5.1 `ProcessingOutcome`

A processing outcome contains:

| Field | Contract |
| --- | --- |
| Identity and result | Server-generated `outcome_id`; `processing_result` is `ROUTINE_PROCESSED` or `ESCALATED`; nullable `escalation_type`; fixed `approval_status: PENDING_HUMAN_APPROVAL`. |
| Explanation | One or more triggered rule IDs, evidence references used, Vietnamese user-facing explanation, and server-generated creation time. |
| Proposed calculations | `eligible_total_vnd`; for advances, `amount_to_return_vnd` and `additional_payment_vnd`; for member-paid cases, proposed reimbursement represented from eligible total. These are proposals, not authorization to settle. |

A routine result has a null escalation type and no escalation object. An escalated result has exactly one of `FACT_UNKNOWN`, `OUT_OF_POLICY`, or `AUTHORITY_REQUIRED` and must include an escalation object.

### 5.2 `Escalation`

Every escalation has all of the following required fields:

| Field | Meaning |
| --- | --- |
| `type` | `FACT_UNKNOWN`, `OUT_OF_POLICY`, or `AUTHORITY_REQUIRED`. |
| `addressee_role` | The role that can supply the fact or make the authorized decision. |
| `related_evidence` | Evidence IDs or references needed to answer safely. |
| `known_facts` | Case, amount, threshold, budget, and other verified context. |
| `specific_question` | One concrete, answerable question; not a generic request to “check.” |
| `response_format` | The required evidence, choice, or response shape. |
| `resume_action` | The rule or processing action to run after a valid response. |

## 6. Audit and operational-control contracts

### 6.1 `AuditEvent`

Audit history is append-only. Every event includes an event ID, timestamp, actor ID/type, policy version, event type, input hash, triggered-rule IDs, and explanation. It may include actor role, reason, prior outcome reference, and target audit-event reference.

The minimum event vocabulary is:

```text
RECEIVED → VALIDATED → RULE_TRIGGERED → CLASSIFIED
PAUSED / RESUMED / OVERRIDDEN / UNDONE
```

Human-decision and settlement-evidence events extend this history only after the corresponding authorized human action. They do not change the original processing outcome.

### 6.2 Pause, override, and undo

| Control | Contract |
| --- | --- |
| Pause | Authorized role, scope, reason, time, and actor are required. Processing state becomes `PAUSED` before policy evaluation. |
| Resume | An authorized event returns control state to `ACTIVE` without deleting prior alerts, questions, or missing approvals. |
| Override | Permitted only for configured internal-policy rules; requires actor ID, actor role, reason, timestamp, and previous outcome ID. Mandatory-law rules are never overridable. |
| Undo | Requires actor ID, reason, timestamp, and target audit-event ID; appends a compensating event and never deletes or edits the target. |

## 7. Persistence, retrieval, and API boundary

The implementation stores immutable snapshots for the submitted case, normalized facts, organization profile, policy version/snapshot, processing outcome, and evidence references. It stores ordered append-only audit events linked to the case and previous event where applicable.

Retrieval renders stored snapshots and replays permitted control events; it does not silently re-evaluate a historical case using a newer policy/profile version. The API and database design may choose concrete endpoint names and table names in implementation, but must preserve the contract invariants, response relationships, and authorization boundary above.

## 8. Structural errors versus safe business escalation

| Condition | Required behavior |
| --- | --- |
| Invalid JSON/schema shape, invalid identifier/date/type, malformed money value, or forbidden additional property | Reject before processing with a structural validation error; record no processing outcome. |
| Missing, unreadable, inconsistent, disputed, or suspicious business fact in an otherwise valid case | Return `ESCALATED / FACT_UNKNOWN` with a structured question and preserve the evidence/fact context. |
| Valid case outside policy or requiring authority | Return the corresponding structured escalation; never automatically reject or pay. |

## 9. Migration from `TMP-DEV-001`

The new reimbursement contract is introduced as a new versioned path. It does not update, delete, or convert the existing temporary case snapshots, decision snapshots, audit events, profile, Control Deck events, or API responses.

Historical temporary records remain labelled `TEMPORARY_DEVELOPMENT`, `SYNTHETIC`, `UNVALIDATED`, and `TMP-DEV-001`. They must never appear as evidence of a real reimbursement decision, payment, policy approval, or authorized human action.

The Policy Forge corpus and Verify-suite manifest is defined in [05_reimbursement_case_corpus.md](05_reimbursement_case_corpus.md). Before implementation begins, the team must review and adopt the workflow, MVP, policy, contract, and corpus together; then update tests, API wording, persistence migrations, authorization design, and UI together.

## 10. Contract acceptance criteria

- The adopted model validates against the canonical reimbursement schema and its cross-field conditions.
- Every policy rule can be represented with the profile, case, evidence, outcome, escalation, and audit contracts.
- The same normalized case, policy version, and profile snapshot reproduce the same processing result.
- Every escalation is self-contained and addresses an authorized role.
- No agent result grants approval, rejection, payment, or an override of mandatory law.
- A reviewer can reconstruct the case, evidence references, profile/policy version, rule triggers, calculation, result, actor, time, and compensation history.
- Existing `TMP-DEV-001` traces remain retrievable as synthetic history without mutation or semantic relabelling.
