# Reimbursement Case Corpus and Verify Suite v1.1

## Document control

**Status:** Adopted corpus manifest - frozen for the reimbursement v1 synthetic pilot; all fixtures remain synthetic until the real-operation gate in [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md) is complete.

**Depends on:**

- [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md)
- [02_MVP_Spec.md](02_MVP_Spec.md)
- [03_reimbursement_policy.md](03_reimbursement_policy.md)
- [04_reimbursement_system_contract.md](04_reimbursement_system_contract.md)

**Canonical fixtures:**

- [Policy Forge test suite](../policy-forge-baseline/test_cases.json)
- [Policy Forge Verify suite](../policy-forge-baseline/verify_cases.json)

**Purpose:** Define the synthetic policy cases that every reimbursement implementation must evaluate consistently. The JSON fixtures are canonical; this document is their human-readable manifest and acceptance contract.

**Adopted decisions:** [ADR-006](ADRs/006_synthetic-pilot-and-public-private-surfaces.md) (public Verify boundary and vocabulary mapping), [ADR-007](ADRs/007_versioned-fixture-input-schema.md) (fixture expansion), and [ADR-011](ADRs/011_relocate-legacy-regression-fixture.md) (legacy fixture separation).

## 1. Corpus boundary

All corpus data is synthetic. It contains no real person, vendor, account, receipt, transaction, or payment information.

The corpus tests the Policy Forge v1.1 reimbursement policy. It is not a record of real club decisions, a source of real configuration, or authorization to process a payment.

Implementations must use the full synthetic suite for regression tests and the five-case Verify suite for a concise demonstration of deterministic processing and safe escalation.

Each concise scenario fixture expands deterministically into a full reimbursement envelope through a data-driven expander; the expander never branches on fixture ID, title, or free text. See [ADR-007](ADRs/007_versioned-fixture-input-schema.md).

## 2. Full policy suite

The canonical suite has 16 cases. Each case must return the expected processing result, escalation type where applicable, fixed `PENDING_HUMAN_APPROVAL` status, rule IDs, and calculation fields where specified.

| Case | Group | Scenario focus | Expected result | Expected escalation | Primary rule(s) |
| --- | --- | --- | --- | --- | --- |
| `TC-R01` | Routine | Complete member-paid printing reimbursement within budget. | `ROUTINE_PROCESSED` | `null` | `RULE-ROUTINE-001` |
| `TC-R02` | Routine | Advance settlement with surplus to return. | `ROUTINE_PROCESSED` | `null` | `RULE-CALC-001`, `RULE-ROUTINE-001` |
| `TC-R03` | Routine / Verify | Amount immediately below routine threshold. | `ROUTINE_PROCESSED` | `null` | `RULE-ROUTINE-001` |
| `TC-R04` | Routine / Verify | Amount exactly at routine threshold with required non-cash evidence. | `ROUTINE_PROCESSED` | `null` | `RULE-ROUTINE-001` |
| `TC-R05` | Routine | Advance settlement requiring additional payment after approval. | `ROUTINE_PROCESSED` | `null` | `RULE-CALC-001`, `RULE-ROUTINE-001` |
| `TC-R06` | Routine / Verify | Multiple eligible lines within budget. | `ROUTINE_PROCESSED` | `null` | `RULE-ROUTINE-001` |
| `TC-F01` | Fact unknown / Verify | Unreadable invoice and low OCR confidence. | `ESCALATED` | `FACT_UNKNOWN` | `RULE-FACT-001` |
| `TC-F02` | Fact unknown | Missing payment proof for a member-paid case. | `ESCALATED` | `FACT_UNKNOWN` | `RULE-DOC-001` |
| `TC-F03` | Fact unknown | Declared total conflicts with evidence total. | `ESCALATED` | `FACT_UNKNOWN` | `RULE-FACT-002` |
| `TC-O01` | Out of policy | Alcohol category without exception approval. | `ESCALATED` | `OUT_OF_POLICY` | `RULE-CAT-002` |
| `TC-O02` | Out of policy | Personal expense has no approved event link. | `ESCALATED` | `OUT_OF_POLICY` | `RULE-SCOPE-001` |
| `TC-O03` | Out of policy | Tobacco is a prohibited category. | `ESCALATED` | `OUT_OF_POLICY` | `RULE-CAT-001` |
| `TC-A01` | Authority / Verify | Amount immediately above routine threshold. | `ESCALATED` | `AUTHORITY_REQUIRED` | `RULE-AUTH-001` |
| `TC-A02` | Authority | Eligible amount exceeds remaining budget. | `ESCALATED` | `AUTHORITY_REQUIRED` | `RULE-BUDGET-001` |
| `TC-A03` | Authority | Requester is also proposed approver. | `ESCALATED` | `AUTHORITY_REQUIRED` | `RULE-CONFLICT-001` |
| `TC-X01` | Out of policy | Verified evidence was already paid with no credit/reversal. | `ESCALATED` | `OUT_OF_POLICY` | `RULE-DUP-002` |

### 2.1 Required calculation checks

The suite verifies calculations in addition to classification:

| Case | Required assertion |
| --- | --- |
| `TC-R01` | Proposed eligible total is 850,000 VND. |
| `TC-R02` | Eligible total is 2,400,000 VND; amount to return is 600,000 VND; additional payment is 0 VND. |
| `TC-R05` | Eligible total is 1,500,000 VND; amount to return is 0 VND; additional payment is 300,000 VND. |
| `TC-R03` | 4,999,999 VND is within the configured routine-processing boundary. |
| `TC-R04` | 5,000,000 VND is within the configured routine-processing boundary; this remains pending human approval. |
| `TC-A01` | 5,000,001 VND requires authority review. |

The threshold values above are Policy Forge default-profile fixtures. Production configuration must use the approved `OrganizationProfile`; a fixture value is never a universal club rule.

## 3. Verify suite

The five-case Verify suite supplies a short, repeatable demonstration.

| Verify case | What it proves | Required result |
| --- | --- | --- |
| `TC-R03` | Lower routine threshold boundary. | `ROUTINE_PROCESSED`, no escalation, `PENDING_HUMAN_APPROVAL`. |
| `TC-R04` | Inclusive routine threshold boundary. | `ROUTINE_PROCESSED`, no escalation, `PENDING_HUMAN_APPROVAL`. |
| `TC-R06` | Routine multi-line case. | `ROUTINE_PROCESSED`, no escalation, `PENDING_HUMAN_APPROVAL`. |
| `TC-F01` | Unclear evidence never receives an assertive conclusion. | `ESCALATED / FACT_UNKNOWN` and a self-contained evidence question. |
| `TC-A01` | Above-threshold authority path. | `ESCALATED / AUTHORITY_REQUIRED` and a self-contained authority question. |

The Verify suite determinism key is:

```text
normalized_input_hash + policy_version + organization_profile.profile_id
```

## 4. Acceptance criteria

A policy implementation satisfies this corpus only when all of the following hold:

| Measure | Required result |
| --- | --- |
| Routine verification | 3 of 3 Verify routine cases return `ROUTINE_PROCESSED`. |
| Escalation verification | 2 of 2 Verify escalation cases return `ESCALATED` with the expected type. |
| Approval boundary | All cases return `PENDING_HUMAN_APPROVAL`; agent approvals or rejections: 0. |
| Suspected data safety | Assertive conclusions on suspected data: 0. |
| Question quality | Every Verify escalation includes case context, relevant evidence/facts, requested action, response format, and resume action. |
| Determinism | Repeat runs using the same determinism key return the same result. |
| Missed escalations | `required_escalation_but_routine_processed / total_required_escalations = 0`. |
| Unnecessary escalations | `routine_cases_escalated / total_routine_cases = 0`. |
| Regression coverage | All 16 canonical cases match expected result, escalation type, rule IDs, and specified calculation assertions. |

## 5. Harness requirements

The implementation test harness must:

1. Load the canonical fixtures without fixture-title or free-text matching.
2. Validate each case against the adopted reimbursement contract before evaluation.
3. Execute the same deterministic processing boundary used for submitted cases.
4. Compare result, escalation type, approval status, rule IDs, calculation fields, and required question facts with the fixture expectation.
5. Report expected versus actual results per case and fail on any mismatch.
6. Run the five Verify cases at least twice with the same versioned profile and policy snapshot to demonstrate repeatability.
7. Keep held-out safety and regression cases independent from evaluator implementation decisions.

## 6. Migration from the temporary corpus

The former `TMP-DEV-001` fixture corpus was removed from the working documentation and remains retrievable from Git history. Its temporary categories, 1,000-VND boundary, and outcomes must not be mixed with this corpus.

The new reimbursement implementation must add a separate Policy Forge v1.1 test path. It must run this corpus for the new versioned contract and policy path; legacy temporary behavior remains synthetic historical material until its endpoints are retired.

## 7. Corpus maintenance

- Change a fixture only through a reviewed policy/profile change; do not change expected output to accommodate a defect.
- Add a policy rule, category, threshold behavior, calculation, or control behavior only with a corresponding fixture and test.
- Version the policy, profile, schema, full suite, and Verify suite together when behavior changes.
- Keep synthetic provenance on all public/demo fixtures and never introduce real personal, financial, receipt, vendor, or bank data.
