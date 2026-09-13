# Temporary Development Workflow v0.2

## Document control

**Status:** Temporary development workflow - non-canonical.

**Purpose:** Give the team one synthetic end-to-end scenario for building the backend before a teammate validates the participating club's actual manual workflow.

**Not a claim:** This is not a description of how a real student club, Treasurer, university, or finance office currently works.
It does not claim a paper form, an online form, receipt requirement, threshold, category, reviewer, or settlement procedure is real.

**Replacement trigger:** Replace this document with an observed/validated manual workflow when the teammate provides it.
Do not silently relabel this temporary workflow as observed evidence.

**Related temporary documents:**

- [03_temporary_demo_policy.md](03_temporary_demo_policy.md) - synthetic decision rules.
- [04_temporary_system_contract.md](04_temporary_system_contract.md) - frozen vocabulary, records, and evaluation boundary.
- [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv) - synthetic test cases.

---

## 1. One-sentence workflow

> A synthetic test requester will submit one synthetic self-paid expense case when the deferred service exists; Layer 0 freezes the facts and result shape that its future evaluator will use.

## 2. Scope boundary

| Included in temporary workflow | Explicitly excluded |
| --- | --- |
| One synthetic self-paid claim | Real person, club, event, vendor, receipt, or payment data |
| One expense line | Multi-line claims and aggregation |
| Declared evidence status of `PRESENT` or `NOT_PROVIDED` | File upload, OCR, invoice verification, or receipt storage |
| Deterministic evaluation | LLM decision-making or inferred facts |
| Case, decision, and append-only audit persistence as a later layer | Payment, bank transfer, accounting, tax, or advance reconciliation |

The temporary policy's self-paid scope is stated in [03_temporary_demo_policy.md](03_temporary_demo_policy.md).
It creates no field on the client transport shape.

## 3. Temporary roles

| Role | Temporary action | Not a claim about reality |
| --- | --- | --- |
| `TEST_REQUESTER` | Will send a synthetic case object through a future temporary service. | Not a real club member or defined requester role. |
| `SYSTEM` | Will validate and evaluate `TMP-DEV-001` when the deferred evaluator layer is built. | Does not authorize payment or exercise human discretion. |

Layer 0 models no human-handling role.
`OUT_OF_POLICY` and `AUTHORITY_EXCEEDED` only identify cases that need later human handling; no authority is claimed.

## 4. Temporary input

The test requester will submit the one-line case shape defined in the system contract when a transport layer is built:

| Group | Declared fields | Why they exist in the temporary workflow |
| --- | --- | --- |
| Request identity | Synthetic case ID, submission time, requester role | Identify an individual fixture submission. |
| Stated context | Purpose | Exercise required-fact validation. |
| One expense | Test category, description, integer amount, date, declared evidence status | Exercise eligibility and authority rules. |
| Provenance | Stamped by the server-owned profile `TMP-DEV-001` | Prevent temporary records being mistaken for real data. |

A client cannot select or alter provenance, and the transport shape rejects any profile or provenance field.

## 5. Deferred temporary workflow steps

| Step | Actor | Action | Output / handoff |
| --- | --- | --- | --- |
| 1. Prepare fixture | `TEST_REQUESTER` | Will select or create a synthetic one-line self-paid case. | Transport-valid case object. |
| 2. Submit | `TEST_REQUESTER` to service | Will send the case to a future submit-and-evaluate operation. | Accepted synthetic case. |
| 3. Validate transport | `SYSTEM` | A future adapter will reject malformed data such as an invalid enum token, invalid timestamp, blank case ID, or boolean/non-integer/non-positive amount. | `INPUT_INVALID`; no business decision is produced. |
| 4. Evaluate policy | `SYSTEM` | A future evaluator will apply `TMP-DEV-001` in documented precedence order. | One of four policy outcomes. |
| 5. Return explanation | `SYSTEM` to `TEST_REQUESTER` | A future service will return outcome, applied rule, reason, and a question when the outcome is `MISSING_FACT`. | Inspectable result; no payment action. |

Persistence of the case, decision, and append-only audit history is defined by a later persistence layer, not by this Layer 0 contract.

## 6. Deferred temporary decision paths

| Condition | Result | System response |
| --- | --- | --- |
| A business fact is absent, null, or blank in an otherwise transport-valid case. | `MISSING_FACT` | The future evaluator will ask for the first missing fact. |
| Category is not in the profile allow-list, for example `TEST_BLOCKED`. | `OUT_OF_POLICY` | The future evaluator will cite `TMP-CAT-01` and flag the case for later human handling. |
| Eligible case has a declared evidence status other than `PRESENT`. | `MISSING_FACT` | The future evaluator will ask for expense proof/reference. |
| Complete allowed and evidenced case has amount above the temporary `1000` constant. | `AUTHORITY_EXCEEDED` | The future evaluator will cite `TMP-AUT-02` and flag the case for later human handling. |
| None of the preceding conditions applies. | `AUTO_APPROVED` | The future evaluator will state: "Approved under temporary development profile; no payment was made." |

## 7. Completion criteria for this temporary workflow

The workflow is ready for the evaluator layer when the team can show that every fixture in [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv):

- produces its expected outcome through the same evaluator path;
- returns the expected rule ID and a nullable question where applicable;
- retains the temporary, synthetic, unvalidated provenance markers; and
- leaves persistence and audit ordering to the persistence layer.

## 8. Handoff to the real workflow

When an actual manual workflow becomes available, the team must determine separately:

1. What a real requester submits and through which channel.
2. Whether the workflow begins before spending, after spending, or after an advance.
3. Which evidence is actually required and who judges it.
4. Which checks are routine versus discretionary.
5. Who owns approval, exception, and payment decisions.

Those findings create a new validated workflow and policy version.
They do not make `TEST_ALLOWED`, `TEST_BLOCKED`, or `1000` real.
