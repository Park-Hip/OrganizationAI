# L0 Contract Baseline - Durable Implementation Record

## Document control

**Status:** Durable L0 implementation baseline.
It is derived from the current temporary development chain, does not supersede its source documents, and is explicitly non-policy.

**Depends on:** [04_temporary_system_contract.md](04_temporary_system_contract.md), [03_temporary_demo_policy.md](03_temporary_demo_policy.md), [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv), and [01_temporary_manual_workflow.md](01_temporary_manual_workflow.md).

**Authority:** The documents listed above remain authoritative for temporary backend behavior.
This baseline restates no new business rules and maps their implementation boundaries so later layers share one interpretation.
It does not make the temporary workflow, categories, threshold, or reviewer route real.

## Purpose

This record freezes the vocabulary, validation split, provenance ownership, and layer ownership that L1 through L5 must share.
It exists so parallel implementation does not silently invent incompatible names or behavior.

## 1. Frozen vocabulary

Names listed here are implementation contracts, not policy changes.

| Area | Frozen name | Source |
| --- | --- | --- |
| Profile identifier | `TMP-DEV-001` | `04` section 2.3 |
| Provenance source | `TEMPORARY_DEVELOPMENT` | `04` section 1 |
| Provenance data class | `SYNTHETIC` | `04` section 1 |
| Provenance validation status | `UNVALIDATED` | `04` section 1 |
| Claim route | `SELF_PAID` | `04` section 2.1 |
| Evidence proof statuses | `PRESENT`, `NOT_PROVIDED`, `UNREADABLE`, `AMBIGUOUS` | `04` section 2.1 |
| Temporary categories | `TEST_ALLOWED`, `TEST_BLOCKED` | `04` section 2.1 |
| Decision outcomes | `AUTO_APPROVED`, `MISSING_FACT`, `OUT_OF_POLICY`, `AUTHORITY_EXCEEDED` | `04` section 2.1 |
| Reviewer route | `TREASURER` | `04` section 2.1 |
| Case states | `SUBMITTED`, `EVALUATED` | `04` section 2.1 |
| Audit actions | `SUBMITTED`, `EVALUATED` | `04` section 2.1 |
| Audit actors | `TEST_CLIENT`, `SYSTEM` | `04` section 2.1 |
| Adapter error label | `INPUT_INVALID` | `04` section 5 |

## 2. Transport validation versus business missing facts

These two paths are never collapsed.

| Path | Condition | Result | Persistence |
| --- | --- | --- | --- |
| Transport-invalid | Malformed body, missing `case_id` or `submitted_at`, invalid timestamp or enum token, unsupported route, non-integer or non-positive amount | `INPUT_INVALID` with exact invalid fields | None |
| Transport-valid but incomplete | A business-required field is null or blank | Persisted `MISSING_FACT` decision | Submitted case, decision, and two audit events |

Source: `04` sections 2.2 and 5.

## 3. Provenance ownership

The server stamps provenance.
A client can never select a different profile.
Every persisted record and profile snapshot carries `profile_id`, `profile_source`, `data_class`, and `workflow_validation_status`.

Source: `04` section 1.

## 4. Evaluator boundary

The pure evaluator takes a normalized temporary case and an immutable profile snapshot and returns a deterministic decision.
It has no HTTP, database, clock, LLM, file, payment, or network dependency.

Source: `04` section 3.1.

## 5. Rule precedence

The evaluator applies the first matching rule in this fixed order.

| Priority | Rule ID | Result |
| --- | --- | --- |
| 1 | `TMP-REQ-01` | `MISSING_FACT` |
| 2 | `TMP-CAT-01` | `OUT_OF_POLICY`, route `TREASURER` |
| 3 | `TMP-EVD-01` | `MISSING_FACT` |
| 4 | `TMP-AUT-02` | `AUTHORITY_EXCEEDED`, route `TREASURER` |
| 5 | `TMP-AUT-01` | `AUTO_APPROVED` |

Source: `03` section 5 and `04` section 3.2.

The `1000` authority boundary is inclusive.

Source: `03` section 2 and `04` section 7.

## 6. Fixture traceability map

These six fixtures cover every temporary outcome and the inclusive boundary.
Fixture identifiers are evidence labels, never decision inputs.

| Fixture ID | Expected outcome | Rule ID | Question key or route |
| --- | --- | --- | --- |
| `TMP-001` | `AUTO_APPROVED` | `TMP-AUT-01` | None |
| `TMP-002` | `MISSING_FACT` | `TMP-REQ-01` | `ACTIVITY_REF` |
| `TMP-003` | `MISSING_FACT` | `TMP-EVD-01` | `EXPENSE_PROOF` |
| `TMP-004` | `OUT_OF_POLICY` | `TMP-CAT-01` | `EXCEPTION_DECISION` and route `TREASURER` |
| `TMP-005` | `AUTHORITY_EXCEEDED` | `TMP-AUT-02` | `AUTHORITY_DECISION` and route `TREASURER` |
| `TMP-006` | `AUTO_APPROVED` | `TMP-AUT-01` | Exact boundary `1000` is inclusive |

Source: `05` and `04` section 7.

## 7. Layer ownership

| Layer | Owns | Must not claim |
| --- | --- | --- |
| L0 | Package, tooling, settings, database plumbing, health, this traceability record | Policy, entities, endpoints, fixture execution |
| L1 | Domain types, pure evaluator, question builders | Persistence or HTTP |
| L2 | Mappings, first migration, repositories, event-chain integrity | Policy logic or transport schemas |
| L3 | Request, response, and error schemas | Business decision logic |
| L4 | CSV loading and Verify reporting | An independent decision path |
| L5 | Application commands and the one-transaction submission path | Policy changes |

## 8. Explicit deferrals

These are not implemented in the L0 foundation and are not silently introduced by any layer.

- No LangChain, Langfuse, or natural-language extraction.
- No real people, finance data, receipts, uploads, OCR, payment, or authority claim.
- No approve, reject, pause, undo, re-evaluate, authentication, or role-management operation.
- No expansion of the temporary policy into a real workflow.

## 9. Replacement gate

When a validated manual workflow exists, the source documents are replaced in a controlled migration.
This record must then be updated to point at the new non-temporary profile, rules, fixtures, and contracts.
Temporary records stay labelled synthetic historical data.

Sources: `01` section 8, `03` section 7, and `04` section 8.