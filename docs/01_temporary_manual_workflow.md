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

> A synthetic test requester submits one synthetic self-paid expense case through the temporary decision-history API; Layers 0 through 2 define its facts, normalization, and deterministic decision result, and the temporary persistence layer stores the complete synthetic history.

## 2. Scope boundary

| Included in temporary workflow | Explicitly excluded |
| --- | --- |
| One synthetic self-paid claim | Real person, club, event, vendor, receipt, or payment data |
| One expense line | Multi-line claims and aggregation |
| Declared evidence status of `PRESENT` or `NOT_PROVIDED` | File upload, OCR, invoice verification, or receipt storage |
| Deterministic evaluation | LLM decision-making or inferred facts |
| Immutable case, decision, and append-only audit persistence with stored-only retrieval | Payment, bank transfer, accounting, tax, or advance reconciliation |

The temporary policy's self-paid scope is stated in [03_temporary_demo_policy.md](03_temporary_demo_policy.md).
It creates no field on the client transport shape.

## 3. Temporary roles

| Role | Temporary action | Not a claim about reality |
| --- | --- | --- |
| `TEST_REQUESTER` | Sends a synthetic case object to the temporary decision-history API. | Not a real club member or defined requester role. |
| `SYSTEM` | Validates transport, applies the Layer 2 `TMP-DEV-001` evaluator, and writes an immutable trace plus ordered `SYSTEM` audit events. | Does not authorize payment or exercise human discretion. |
| `DEMO_REVIEWER` | The server records this fixed synthetic label on every temporary Control Deck event (pause, resume, demo review, or compensation). | Not a real reviewer, Treasurer, officer, or authority. The label proves the software mechanic without claiming a real authorization. |

Layer 0 models no human-handling role.
`OUT_OF_POLICY` and `AUTHORITY_EXCEEDED` only identify cases that need later human handling; no authority is claimed.
`DEMO_REVIEWER` exists only in the temporary Control Deck on top of that stored history and is never a Layer 0 actor.

## 4. Temporary input

The test requester submits the one-line case shape defined in the system contract through the temporary decision-history API:

| Group | Declared fields | Why they exist in the temporary workflow |
| --- | --- | --- |
| Request identity | Synthetic case ID, submission time, requester role | Identify an individual fixture submission. |
| Stated context | Purpose | Exercise required-fact validation. |
| One expense | Test category, description, integer amount, date, declared evidence status | Exercise eligibility and authority rules. |
| Provenance | Stamped by the server-owned profile `TMP-DEV-001` | Prevent temporary records being mistaken for real data. |

A client cannot select or alter provenance, and the transport shape rejects any profile or provenance field.

## 5. Temporary workflow steps

| Step | Actor | Action | Output / handoff |
| --- | --- | --- | --- |
| 1. Prepare fixture | `TEST_REQUESTER` | Selects or creates a synthetic one-line self-paid case. | Transport-valid case object. |
| 2. Submit | `TEST_REQUESTER` to service | Sends the case to `POST /api/temporary/decision-traces`. | Accepted synthetic case. |
| 3. Validate transport | `SYSTEM` | The API adapter rejects malformed data such as an invalid enum token, invalid timestamp, blank case ID, or boolean/non-integer/non-positive amount. | `INPUT_INVALID`; no business decision is produced. |
| 4. Evaluate policy | `SYSTEM` | The Layer 2 evaluator applies `TMP-DEV-001` in documented precedence order. | One of four policy outcomes. |
| 5. Record and return | `SYSTEM` to `TEST_REQUESTER` | One transaction writes the immutable case snapshot, decision snapshot, and three ordered `SYSTEM` audit events, then returns outcome, rule, reason, and a question when the outcome is `MISSING_FACT`. | Stored, retrievable trace; no payment action. |
| 6. Apply synthetic control | `DEMO_REVIEWER` via service | Appends exactly one labelled control event (`pause`, `resume`, `record_demo_review`, or `undo`) to the stored trace and returns the derived `control_state`. | An immutable append-only control event plus the projected state; the original decision snapshot never changes. |

The service writes the complete synthetic history in one transaction and stores it as immutable snapshots and append-only audit events. `GET /api/temporary/decision-traces/{trace_id}` returns the stored history, including the derived `control_state`, without reevaluating the decision. No real human-control authority exists; the temporary Control Deck only appends labelled synthetic control events.

## 6. Temporary decision paths

The Layer 2 evaluator returns one of the four temporary outcomes in the first-applicable order defined by the [temporary policy](03_temporary_demo_policy.md) and [system contract](04_temporary_system_contract.md).
The surrounding service and persistence workflow are implemented by the temporary decision-history and Control Deck layers; real human-control authority remains deferred.
The temporary Control Deck is a synthetic demo mechanic defined in [04_temporary_system_contract.md](04_temporary_system_contract.md) and does not claim a real reviewer decision.

## 7. Completion criteria for this temporary workflow

The temporary decision-history implementation is complete when the team can show that every fixture in [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv):

- produces its expected outcome through the same evaluator path;
- returns the expected rule ID and a nullable question where applicable;
- retains the temporary, synthetic, unvalidated provenance markers; and
- stores an immutable snapshot and an ordered, append-only audit event chain through the temporary persistence layer.

## 8. Handoff to the real workflow

When an actual manual workflow becomes available, the team must determine separately:

1. What a real requester submits and through which channel.
2. Whether the workflow begins before spending, after spending, or after an advance.
3. Which evidence is actually required and who judges it.
4. Which checks are routine versus discretionary.
5. Who owns approval, exception, and payment decisions.

Those findings create a new validated workflow and policy version.
They do not make `TEST_ALLOWED`, `TEST_BLOCKED`, or `1000` real.
