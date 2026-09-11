# Temporary Demo Policy `TMP-DEV-001`

## Document control

**Status:** Temporary development policy — non-canonical.

**Purpose:** Supply explicit, synthetic business rules so the evaluator, demo fixtures, and audit behavior can be built before a participating club validates its real workflow and policy.

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

Every decision made under this policy must visibly state that it uses a temporary development profile. It must never be described as a real club approval policy.

## 2. Scope

This policy evaluates one synthetic, self-paid, post-spend request with one expense line.

It does not define payment, bank transfer, accounting, tax, receipt authentication, uploads, advance reconciliation, direct-vendor payment, or real authority delegation.

## 3. Synthetic policy rules

| Rule ID | Condition | Policy result |
| --- | --- | --- |
| `TMP-REQ-01` | A required business fact is absent. | `MISSING_FACT`; ask for the first missing fact. |
| `TMP-CAT-01` | Category is `TEST_BLOCKED` or has no entry in this temporary policy. | `OUT_OF_POLICY`; route the exception question to temporary `TREASURER`. |
| `TMP-EVD-01` | An otherwise eligible case has expense-proof status other than `PRESENT`. | `MISSING_FACT`; ask for expense proof/reference. |
| `TMP-AUT-01` | An eligible, evidenced case has amount at or below `DEV_AUTO_LIMIT_VND`. | `AUTO_APPROVED`. |
| `TMP-AUT-02` | An eligible, evidenced case has amount above `DEV_AUTO_LIMIT_VND`. | `AUTHORITY_EXCEEDED`; route to temporary `TREASURER`. |

## 4. Synthetic parameters

All values below are arbitrary test constants chosen to make temporary behavior unmistakably non-businesslike.

| Parameter | Value |
| --- | --- |
| Supported claim route | `SELF_PAID` |
| Allowed category | `TEST_ALLOWED` |
| Blocked category | `TEST_BLOCKED` |
| Required expense-proof status | `PRESENT` |
| `DEV_AUTO_LIMIT_VND` | `1000` |
| Temporary reviewer route | `TREASURER` |

The numeric value `1000`, category labels, and reviewer route are not candidate club rules. They must not be copied into a real policy.

## 5. Evaluation order

The evaluator applies the first applicable rule:

1. Required business fact missing → `MISSING_FACT` (`TMP-REQ-01`).
2. Category blocked/unknown → `OUT_OF_POLICY` (`TMP-CAT-01`).
3. Required proof not `PRESENT` → `MISSING_FACT` (`TMP-EVD-01`).
4. Amount above `1000` → `AUTHORITY_EXCEEDED` (`TMP-AUT-02`).
5. Otherwise → `AUTO_APPROVED` (`TMP-AUT-01`).

For a routine result, the displayed message must state:

> Approved under temporary development profile; no payment was made.

## 6. Fixture coverage

[05_temporary_case_corpus.csv](05_temporary_case_corpus.csv) supplies one or more synthetic cases for every rule and for the inclusive `1000` authority boundary.

## 7. Replacement gate

Retire this policy rather than editing it into a real policy when the team has:

- a validated manual-workflow summary;
- a named policy owner;
- owner-approved categories, evidence requirements, authority behavior, and reviewer route;
- a new non-temporary policy ID/version/source; and
- revised system contract, fixtures, UI wording, and public demo claims.

Temporary cases, decisions, and audit events remain labelled synthetic/historical after replacement.
