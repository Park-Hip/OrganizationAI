# Temporary Development Workflow v0.1

## Document control

**Status:** Temporary development workflow — non-canonical.

**Purpose:** Give the team one synthetic end-to-end scenario for building the backend before a teammate validates the participating club’s actual manual workflow.

**Not a claim:** This is not a description of how a real student club, Treasurer, university, or finance office currently works. It does not claim a paper form, an online form, receipt requirement, threshold, category, reviewer, or settlement procedure is real.

**Replacement trigger:** Replace this document with an observed/validated manual workflow when the teammate provides it. Do not silently relabel this temporary workflow as observed evidence.

**Related temporary documents:**

- [03_temporary_demo_policy.md](03_temporary_demo_policy.md) — synthetic decision rules.
- [04_temporary_system_contract.md](04_temporary_system_contract.md) — data, evaluation, persistence, and service behavior.
- [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv) — synthetic test cases.

---

## 1. One-sentence workflow

> A synthetic test requester submits one synthetic self-paid expense case; the system validates its declared facts against `TMP-DEV-001`, records an audit trail, and returns either a routine temporary-policy result, a repair question, or a temporary Treasurer route.

## 2. Scope boundary

| Included in temporary workflow | Explicitly excluded |
| --- | --- |
| One synthetic self-paid claim | Real person, club, event, vendor, receipt, or payment data |
| One expense line | Multi-line claims and aggregation |
| Declared proof status | File upload, OCR, invoice verification, or receipt storage |
| Deterministic evaluation | LLM decision-making or inferred facts |
| Temporary Treasurer route | Real approval authority or human action endpoint |
| Case, decision, and append-only audit persistence | Payment, bank transfer, accounting, tax, or advance reconciliation |

## 3. Temporary roles

| Role | Temporary action | Not a claim about reality |
| --- | --- | --- |
| `TEST_REQUESTER` | Sends a synthetic case object through the temporary service. | Not a real club member or defined requester role. |
| `SYSTEM` | Validates, evaluates `TMP-DEV-001`, creates a decision, and appends audit events. | Does not authorize payment or exercise human discretion. |
| `TREASURER` | Receives an output route for blocked/above-limit synthetic cases. | Not confirmation of a real Treasurer’s authority or workflow. |

## 4. Temporary input

The test requester submits the one-line case shape defined in the system contract:

| Group | Declared fields | Why they exist in the temporary workflow |
| --- | --- | --- |
| Request identity | Synthetic case ID, submission time, requester role | Trace fixtures and audit order. |
| Claim context | `SELF_PAID`, synthetic activity reference, purpose | Exercise required-fact validation. |
| One expense | Test category, description, integer amount, date | Exercise eligibility and authority rules. |
| Proof declaration | `PRESENT`, `NOT_PROVIDED`, `UNREADABLE`, or `AMBIGUOUS` | Exercise repair behavior without any file. |
| Provenance | Stamped by service: `TMP-DEV-001`, `TEMPORARY_DEVELOPMENT`, `SYNTHETIC`, `UNVALIDATED` | Prevent temporary records being mistaken for real data. |

## 5. Temporary workflow steps

| Step | Actor | Action | Output / handoff |
| --- | --- | --- | --- |
| 1. Prepare fixture | `TEST_REQUESTER` | Selects or creates a synthetic one-line self-paid case. | Transport-valid case object. |
| 2. Submit | `TEST_REQUESTER` → service | Sends the case to the temporary submit-and-evaluate operation. | Persisted synthetic case in `SUBMITTED` state; `SUBMITTED` audit event. |
| 3. Validate transport | `SYSTEM` | Rejects malformed data such as invalid enum token, invalid date, invalid timestamp, or non-positive/non-integer amount. | `INPUT_INVALID`; no business decision/audit record. |
| 4. Evaluate policy | `SYSTEM` | Applies `TMP-DEV-001` in documented precedence order. | One of four policy outcomes. |
| 5. Record result | `SYSTEM` | Persists immutable decision/profile/input snapshots and an `EVALUATED` audit event. | Case becomes terminal `EVALUATED`. |
| 6. Return explanation | `SYSTEM` → `TEST_REQUESTER` | Returns outcome, applied rule, reason, question if applicable, and reviewer route if applicable. | Inspectable case detail; no payment action. |

## 6. Temporary decision paths

| Condition | Result | System response |
| --- | --- | --- |
| A business fact is absent/null/blank in an otherwise transport-valid case. | `MISSING_FACT` | Ask for the first missing fact. |
| Category is `TEST_BLOCKED` or unlisted in the profile. | `OUT_OF_POLICY` | Cite `TMP-CAT-01`; route a temporary exception question to `TREASURER`. |
| Eligible case has proof status other than `PRESENT`. | `MISSING_FACT` | Ask for expense proof/reference. |
| Complete allowed/evidenced case has amount above the temporary `1000` constant. | `AUTHORITY_EXCEEDED` | Cite `TMP-AUT-02`; route to temporary `TREASURER`. |
| None of the preceding conditions applies. | `AUTO_APPROVED` | State: “Approved under temporary development profile; no payment was made.” |

## 7. Completion criteria for this temporary workflow

The workflow is ready for backend implementation when the team can show that every fixture in [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv):

- produces its expected outcome through the same evaluator path;
- returns the expected rule/question/route where applicable;
- persists `SUBMITTED` then `EVALUATED` audit events in order; and
- retains the temporary/synthetic/unvalidated provenance markers.

## 8. Handoff to the real workflow

When an actual manual workflow becomes available, the team must determine separately:

1. What a real requester submits and through which channel.
2. Whether the workflow begins before spending, after spending, or after an advance.
3. Which evidence is actually required and who judges it.
4. Which checks are routine versus discretionary.
5. Who owns approval/exception/payment decisions.

Those findings create a new validated workflow and policy version. They do not make `TEST_ALLOWED`, `TEST_BLOCKED`, `1000`, or temporary `TREASURER` routing real.
