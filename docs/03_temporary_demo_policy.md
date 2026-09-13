# Temporary Demo Policy `TMP-DEV-001` v0.2

## Document control

**Status:** Temporary development policy - non-canonical.

**Purpose:** Supply explicit, synthetic business rules so the evaluator, demo fixtures, and later persistence behavior can be built before a participating club validates its real workflow and policy.

**Not a claim:** This is not a club policy, financial procedure, institutional rule, user-research finding, or public-demo evidence.

**Applies to:** Synthetic cases represented by [04_temporary_system_contract.md](04_temporary_system_contract.md) and the fixtures in [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv).

---

## 1. Temporary provenance

| Field | Value |
| --- | --- |
| Policy ID | `TMP-DEV-001` |
| Policy source | `TEMPORARY_DEVELOPMENT` |
| Data class | `SYNTHETIC` |
| Workflow validation status | `UNVALIDATED` |
| Purpose | Backend and test-fixture development only |

Every decision made under this policy must visibly state that it uses a temporary development profile.
It must never be described as a real club approval policy.

## 2. Scope

The evaluator under this policy evaluates one synthetic, self-paid, post-spend request with one expense line.

This scope creates no client transport field.

This policy does not define payment, bank transfer, accounting, tax, receipt authentication, uploads, advance reconciliation, direct-vendor payment, or real authority delegation.

## 3. Synthetic policy rules

| Rule ID | Condition | Policy result |
| --- | --- | --- |
| `TMP-REQ-01` | A required business fact - purpose, requester role, expense object, or expense field - is absent. | `MISSING_FACT`; ask for the first missing fact. |
| `TMP-CAT-01` | Category is not in the temporary allow-list. | `OUT_OF_POLICY`; flag the case for later human handling. |
| `TMP-EVD-01` | An otherwise eligible case has `expense.evidence_status` other than `PRESENT`. | `MISSING_FACT`; ask for expense proof/reference. |
| `TMP-AUT-01` | An eligible, evidenced case has amount at or below `auto_approve_limit_vnd`. | `AUTO_APPROVED`. |
| `TMP-AUT-02` | An eligible, evidenced case has amount above `auto_approve_limit_vnd`. | `AUTHORITY_EXCEEDED`; flag the case for later human handling. |

## 4. Synthetic parameters

All values below are arbitrary test constants chosen to make temporary behavior unmistakably non-businesslike.

| Parameter | Value |
| --- | --- |
| Allowed categories | `{TEST_ALLOWED}` |
| Required evidence status | `PRESENT` |
| `auto_approve_limit_vnd` | `1000` |

`TEST_BLOCKED` is not a separately stored negative list.
It is simply a category label outside the allow-list, so a `TEST_BLOCKED` category is out of policy.

The numeric value `1000` and the category labels are not candidate club rules.
They must not be copied into a real policy.

## 5. Evaluation order

The evaluator applies the first applicable rule:

1. Required business fact missing - `MISSING_FACT` (`TMP-REQ-01`).
2. Category not in the allow-list - `OUT_OF_POLICY` (`TMP-CAT-01`).
3. Required evidence status not `PRESENT` - `MISSING_FACT` (`TMP-EVD-01`).
4. Amount above `1000` - `AUTHORITY_EXCEEDED` (`TMP-AUT-02`).
5. Otherwise - `AUTO_APPROVED` (`TMP-AUT-01`).

For a routine result, the displayed message must state:

> Approved under temporary development profile; no payment was made.

When the temporary decision-history layer persists a decision, the stored record keeps the same temporary, synthetic, unvalidated provenance markers and the same no-payment wording. A persisted trace is historical synthetic evidence; it never authorizes, initiates, or reports a payment, and it never turns `TEST_ALLOWED`, `TEST_BLOCKED`, or `1000` into a real club rule.

## 6. Fixture coverage

[05_temporary_case_corpus.csv](05_temporary_case_corpus.csv) supplies one or more synthetic cases for every rule and for the inclusive `1000` authority boundary.

## 7. Replacement gate

Retire this policy rather than editing it into a real policy when the team has:

- a validated manual-workflow summary;
- a named policy owner;
- owner-approved categories, evidence requirements, and authority behavior;
- a new non-temporary policy ID/version/source; and
- revised system contract, fixtures, UI wording, and public demo claims.

Temporary cases, decisions, and audit events remain labelled synthetic and historical after replacement.
