# MVP Specification v1.0

## Document control

**Status:** Adopted MVP specification - frozen for the reimbursement v1 synthetic pilot; real-operation activation remains conditional on the checklist in [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md).

**Depends on:** [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md).

**Policy sources:** [Policy Forge reimbursement policy](../policy-forge-baseline/Policy_Hoan_Ung_CLB.md), [policy rules](../policy-forge-baseline/policy_rules.yaml), [reimbursement schema](../policy-forge-baseline/reimbursement.schema.json), and the associated synthetic cases.

**Purpose:** Define the smallest product slice that prepares an auditable reimbursement packet and routes uncertainty to an authorized human. Sprint 1 makes one bounded AI intake and packet-preparation agent the primary user experience; it does not approve, reject, or transfer money.

**Adopted decisions:** [ADR-006](ADRs/006_synthetic-pilot-and-public-private-surfaces.md) (synthetic Verify surface and vocabulary mapping), [ADR-007](ADRs/007_versioned-fixture-input-schema.md) (versioned fixture-input schema and deterministic expansion), [ADR-008](ADRs/008_oidc-identity-adapter.md) (future OIDC adapter boundary), [ADR-009](ADRs/009_metadata-only-evidence-boundary.md) (metadata-only evidence), [ADR-010](ADRs/010_alcohol-escalation-ownership.md) (alcohol handoff), and [ADR-012](ADRs/012_single-agent-sprint-1-pilot.md) (single-agent synthetic Sprint 1 boundary).

## 1. Product statement

OrganizationalAI is a synthetic, AI-led reimbursement case-preparation demo. One AI agent guides intake and prepares clear, editable review packets; the deterministic versioned policy engine controls classifications, calculations, rule IDs, and escalation types. A human remains responsible for approval and settlement, and every agent result remains `PENDING_HUMAN_APPROVAL`.

## 2. MVP goals

The MVP must:

1. Make one bounded AI agent the primary Sprint 1 experience for Vietnamese intake, structured drafting, missing-fact clarification, and explanation of a completed packet or escalation.
2. Support the two approved workflow types: `MEMBER_PAID` and `ADVANCE_SETTLEMENT`.
3. Capture a case packet with requester, activity/purpose, budget, expense lines, evidence references, and the flow-specific facts needed to calculate a proposed settlement.
4. Evaluate the configured policy in its documented priority order, including evidence integrity, duplicates, scope/category, required documents, deadline, budget, conflict, aggregation, authority, conditional tax evidence, and calculation checks.
5. Return one of two processing results: `ROUTINE_PROCESSED` or `ESCALATED`.
6. Keep `approval_status` as `PENDING_HUMAN_APPROVAL` for every case; neither the agent nor the policy engine may approve, reject, or transfer money.
7. Produce one structured escalation for every escalated case.
8. Store immutable case and policy/profile snapshots plus an append-only audit-event history, including agent tool actions and fixed synthetic human-control actions.
9. Demonstrate deterministic behavior against the approved synthetic test and Verify suites through the same evaluator path used by the agent.

## 3. MVP users and responsibilities

| User | MVP capability | Boundary |
| --- | --- | --- |
| Requester | Creates a reimbursement case and supplies requested facts/evidence. | Cannot approve their own case. |
| AI agent / preparer | Guides intake, creates an editable structured draft, identifies unknown facts, calls schema-validated tools, and explains a review packet or escalation. | Cannot classify a case, calculate a settlement, invent or verify facts, approve, reject, transfer money, choose a policy/profile, or bypass controls. |
| Deterministic policy engine | Applies the versioned policy, calculations, rule IDs, and structured escalation contract. | Has no LLM, database, payment, network, or human-authority dependency. |
| Synthetic reviewer (Sprint 1) | Demonstrates a fixed, server-owned synthetic human-control action with reason in the audit trail. | Is not production authentication, authorization, or a real financial authority. |
| Treasurer / payment executor | Records the settlement evidence after a recorded human approval. | Settlement is not an agent side effect. |
| System administrator | Administers access, backup, and an authorized operational pause. | Has no automatic financial-decision authority. |

## 4. In-scope capabilities

### 4.1 Case preparation and validation

- Let the single AI agent create and update an editable structured draft only through schema-validated tool calls; every value remains supplied, unknown, or unverified until the deterministic boundary can use it.
- Create and validate a versioned reimbursement case with one or more expense lines.
- Select the declared flow type and require advance-specific fields for `ADVANCE_SETTLEMENT`.
- Record evidence metadata and references, including readability, verification state, and duplicate-check result.
- Preserve a masked reimbursement-account representation in outputs and logs.
- Keep structural validation separate from a policy-level `FACT_UNKNOWN` escalation.

### 4.2 Deterministic policy processing

- Load a server-owned, immutable `OrganizationProfile` and a versioned policy snapshot for each case.
- Apply the policy in priority order; pause has precedence over all evaluation.
- Aggregate related lines before budget, authority, and conditional tax checks.
- Calculate the proposed eligible total and the applicable advance return, additional payment, or reimbursement amount from verified eligible lines only.
- Explain the triggered rule IDs and evidence used in the resulting packet.

### 4.3 Agent boundary

- Give the agent only tools to create/update a draft, validate a draft, evaluate a case, retrieve an allowed policy explanation, and retrieve an audit timeline.
- Record the agent/prompt/tool version, tool inputs and outputs, and resulting case reference in the append-only audit history, subject to data minimization.
- If the model or a tool fails, preserve the draft and return a structured correction or escalation path; do not guess or silently complete a financial fact.

### 4.4 Escalation and human handoff

Every escalated result must contain:

- `type`: `FACT_UNKNOWN`, `OUT_OF_POLICY`, or `AUTHORITY_REQUIRED`;
- the intended `addressee_role`;
- related evidence and known facts;
- one specific question and a response format; and
- the `resume_action` that can continue processing after a valid response.

A routine packet has no escalation, but still requires human approval.

### 4.5 Audit and control

- Store an append-only event history for receipt, validation, rule triggering, classification, pause, resume, permitted override, undo, human decision, and settlement evidence.
- Store the normalized-input hash, policy version, profile snapshot, actor identity/role where applicable, and time for reproducibility.
- Implement pause as an operational control, not an outcome prediction.
- Implement undo as a compensating event; never delete or mutate a prior event.
- Permit overrides only for configured internal-policy rules and require an authorized actor, reason, timestamp, and prior outcome reference. Mandatory-law rules are never overridable.

## 5. Explicit non-goals

The MVP does not:

- approve, reject, or transfer money automatically;
- treat `ROUTINE_PROCESSED` as a payment instruction or final approval;
- use an LLM to infer or verify missing financial facts, make policy decisions, calculate a settlement, or select a policy/profile;
- commit real receipts, bank details, identities, vendor data, credentials, or tokens to this repository;
- expose a real or shared reimbursement endpoint without the required authentication, authorization, and data-protection controls; the sole Sprint 1 public exception is the clearly labelled synthetic agent/Verify demo defined by ADR-012;
- replace the governing organization's accounting, procurement, tax, or legal obligations; or
- silently reinterpret the historical `TMP-DEV-001` traces as real-policy records.

## 6. Data and security boundary

The first implementation may use synthetic data only until the real-operation checklist in the workflow is complete. Before a real case is accepted, the team must configure and approve the parent organization, accounting/tax regime, categories, thresholds, authority roles, evidence requirements, retention policy, access model, and incident process.

The MVP must minimize personal data, show only masked account information where needed, and preserve evidence/audit history according to the approved profile. Sprint 1 uses fixed, server-owned synthetic actors for its limited human-control demonstration; production authentication and authorization remain deferred until the real-operation gate.

## 7. Acceptance criteria

| Area | Acceptance criterion |
| --- | --- |
| Determinism | The same normalized input, policy version, and profile snapshot always produce the same result. |
| Routine processing | The three routine cases in `verify_cases.json` return `ROUTINE_PROCESSED`, no escalation, and `PENDING_HUMAN_APPROVAL`. |
| Escalation | The two escalation cases in `verify_cases.json` return `ESCALATED` with the expected escalation type and a self-contained question. |
| Safety | No suspected-data case receives an assertive conclusion; the agent never approves, rejects, or transfers money. |
| Auditability | A reviewer can reconstruct the input, profile/policy version, triggered rules, evidence references, result, actor, timestamps, and compensation history. |
| Sprint 1 human control | The server records only fixed synthetic actors for the demo; the client cannot select a role, policy, profile, identifier, timestamp, or audit event. A requester cannot approve their own case. Production authorization remains deferred. |
| Regression coverage | The full Policy Forge synthetic suite passes, including authority boundaries, duplicate handling, conflict, multi-line aggregation, and both workflow types. |

## 8. Delivery boundary and next document

This specification defines product scope, not the transport or database contract. The versioned contract is defined in [04_reimbursement_system_contract.md](04_reimbursement_system_contract.md), and the adopted test/Verify manifest is defined in [05_reimbursement_case_corpus.md](05_reimbursement_case_corpus.md).

The current temporary backend remains the source of behavior for its existing endpoints until the policy, contract, corpus, and corresponding implementation are adopted together.
