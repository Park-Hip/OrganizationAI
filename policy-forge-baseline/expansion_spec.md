# Reimbursement Fixture Expansion Specification v1.2.0

**Status:** Adopted. Canonical for the reimbursement v1 synthetic pilot.

**Depends on:** [ADR-007](../docs/ADRs/007_versioned-fixture-input-schema.md), [reimbursement.schema.json](reimbursement.schema.json), and [reimbursement-fixture.schema.json](reimbursement-fixture.schema.json).

**Purpose:** Define the single deterministic mapping from a concise synthetic fixture input to a full reimbursement envelope. Every service (policy engine, harness, Verify path, and persistence integration) must share this mapping so a concise fixture and its full envelope are interchangeable.

This document does not implement policy evaluation. It only turns a concise input into the complete input side of the envelope: `policy_version`, `organization_profile`, `case`, `control_state`, and the initial `audit_events`.

## 1. Invariants

1. Expansion is deterministic. The same concise input always produces the same full envelope.
2. Expansion never depends on the fixture id, title, group, note, or any free-text prose. Two fixtures with identical structural input and different ids/titles expand to byte-identical envelopes.
3. The expander optionally applies only the data-driven field mappings below. It never hard-codes a category price, a real profile value, a real person, or an organization decision.
4. Structural inputs that fail [reimbursement-fixture.schema.json](reimbursement-fixture.schema.json) are rejected before expansion. The expander never silently reinterprets malformed input.
5. A valid structural input that describes missing, unreadable, conflicting, or unknown business facts expands into a structurally valid case whose flags represent those facts. The policy engine, not the expander, is responsible for turning them into an escalation.
6. Expansion produces server-owned fields. A concise fixture cannot supply the case id, outcome id, event id, input hash, audit timestamps, profile id, or policy snapshot id directly.

## 2. Generated, server-owned fields

| Field | Derivation |
| --- | --- |
| `policy_version` | The suite's declared `policy_version`. |
| `organization_profile` | The default `organization_profile` from `policy_rules.yaml`, with any allowed `profile_overrides` applied. Profile id and version are server-owned; overrides may only change the explicit allow-listed configuration keys. |
| `control_state` | `PAUSED` when `input.paused == true`; otherwise `ACTIVE`. |
| `evidence_amount_vnd` | Only from the concise evidence amount fields; the expander never invents an amount. |
| IDs and hashes | Derived from a deterministic digest of the canonicalized structural input only. The digest never includes the fixture id, title, group, note, or free-text prose. |
| Timestamps | Fixed synthetic constants when the concise input does not override them. |

## 3. Defaults

| Concise field | Default when absent |
| --- | --- |
| `requester_id` / `proposed_approver_id` | `P-001` / `P-002` (synthetic). |
| `task_or_event` / `purpose` | `EVT-SYN-001` / `Chi cho hoat dong cau lac bo (tong hop)`. |
| `event_end_date` / `submitted_at` | `2026-08-31` / `2026-09-10T09:00:00Z`. |
| `budget.approved_vnd` / `budget.remaining_vnd` | `10000000` / `10000000`. |
| `days_late` | `0`. |
| `conflict` / `paused` | `false` / `false`. |
| `evidence.readable` / `evidence.verified` | `true` / `true`. |
| `evidence.payment_proof` | `true`. |
| `evidence.non_cash_verified` | `true` when a line's `payment_method` is not `CASH`; otherwise `false`. |
| `evidence.prior_approval_present` | `false`. |
| `evidence.event_link` | `true`. |
| `evidence.ocr_confidence` | `null`. |

## 4. Field mappings

### 4.1 People, event, budget, deadline

- `requester` becomes `PersonRef{person_id: requester_id, display_name, role: profile.roles.requester}`. The display name is deterministic and synthetic: `Synthetic <person_id>`.
- `proposed_approver` becomes `PersonRef{person_id: proposed_approver_id, display_name, role: profile.roles.approver_within_authority}`.
- `task_or_event`, `purpose`, `event_end_date`, `submitted_at` map directly.
- `budget.approved_vnd` → `approved_budget_vnd`; `budget.remaining_vnd` → `remaining_budget_vnd`. A stable synthetic `budget_code` is generated.
- `days_late` → `submitted_business_days_after_end`.

### 4.2 Expense items

Single-line form (`expense.total_vnd` + `expense.category`):

- One `ExpenseItem` with `amount_vnd = expense.total_vnd`, `category = expense.category`, and `line_assessment = PENDING`.
- Vendor, transaction date, and purpose code come from `expense.vendor`, `expense.transaction_date`, and `expense.purpose_code` or stable synthetic defaults.
- `declared_total_vnd = expense.total_vnd` unless `evidence.declared_total_vnd` is present, in which case that value is declared.

Multi-line form (`expense.items`):

- One `ExpenseItem` per item, copying vendor, transaction date, purpose code, category, amount, and payment method.
- `declared_total_vnd = sum(item.amount_vnd)` unless overridden by `evidence.declared_total_vnd`.

`line_assessment` always starts as `PENDING`. Aggregation over related lines happens in the policy engine using `organization_profile.aggregation_keys`.

### 4.3 Evidence

One `Evidence` record per evidence concept, all synthetic:

- `INVOICE`/`RECEIPT` derived from the expense; its `readable` and `ocr_confidence` come from `evidence.readable` and `evidence.ocr_confidence`, and `verified` from `evidence.verified`.
- `PAYMENT_PROOF` present only when `evidence.payment_proof` is true; its `verified` matches and, for non-cash flows, mirrors `evidence.non_cash_verified`.
- `APPROVAL` present only when `evidence.prior_approval_present` is true; its `approval_decision_ids` carries the deterministic generated approval reference(s) so approval-to-evidence provenance is preserved.
- `ADVANCE_RECORD` present only for `ADVANCE_SETTLEMENT`, referencing `advance_reference`.

When `evidence.evidence_total_vnd` is present, the generated invoice/receipt `amount_vnd` sums to that value so an inconsistency with `declared_total_vnd` is representable and the policy engine can escalate as `FACT_UNKNOWN`.

### 4.4 Duplicate, scope, conditional, and control signals

- `duplicate_check` maps directly to `case.duplicate_check`.
- `prior_payment_reference` is carried so a confirmed duplicate is reproducible.
- `evidence.event_link == false` omits the event-link reference so the policy engine can see "no demonstrable connection".
- `evidence.missing_facts` lists required facts that are deliberately absent in the synthetic case (they are not synthesized by the expander).
- `conflict == true` sets `proposed_approver.person_id == requester.person_id`.
- `paused == true` sets both the case paused flag and the envelope control state.

### 4.5 Non-cash verification

`evidence.non_cash_verified == false` sets the case's `non_cash_evidence_verified` to false. This is the signal the conditional tax rule consumes; it is not an approval.

## 5. Initial audit events

Expansion emits the minimum ordered event sequence under a `PAUSED` or `ACTIVE` control state:

```text
RECEIVED → VALIDATED
```

When `PAUSED`, a `PAUSED` event is appended and no outcome or escalation is produced. When `ACTIVE`, the remaining events (`RULE_TRIGGERED`, `CLASSIFIED`, and any control/decision/settlement event) are produced by the policy engine and the authorized human actors, never by this expander.

## 6. Determinism key

The determinism key is:

```text
sha256(canonical structural input) + policy_version + organization_profile.profile_id
```

Prose, titles, notes, and the fixture id are excluded from the digest.

## 7. Compliance test

The contract-validation suite must prove:

1. Every concise fixture validates against [reimbursement-fixture.schema.json](reimbursement-fixture.schema.json).
2. Every expansion validates against [reimbursement.schema.json](reimbursement.schema.json), including its cross-field conditions.
3. Expansion is deterministic across repeated runs.
4. Expansion is independent of fixture id, title, group, note, and prose.
5. Malformed structural inputs fail before evaluation.