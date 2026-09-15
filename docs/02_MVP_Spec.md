# MVP Specification v1.0

## Document control

**Status:** Adopted MVP specification - frozen for the reimbursement v1 synthetic pilot; real-operation activation remains conditional on the checklist in [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md).

**Depends on:** [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md).

**Policy sources:** [Policy Forge reimbursement policy](../policy-forge-baseline/Policy_Hoan_Ung_CLB.md), [policy rules](../policy-forge-baseline/policy_rules.yaml), [reimbursement schema](../policy-forge-baseline/reimbursement.schema.json), and the associated synthetic cases.

**Purpose:** Define the smallest product slice that prepares an auditable reimbursement packet and routes uncertainty to an authorized human. It does not approve, reject, or transfer money.

**Adopted decisions:** [ADR-006](ADRs/006_synthetic-pilot-and-public-private-surfaces.md) (synthetic pilot and public/private boundary), [ADR-008](ADRs/008_oidc-identity-adapter.md) (OIDC adapter with synthetic test identities), [ADR-009](ADRs/009_metadata-only-evidence-boundary.md) (metadata-only evidence), and [ADR-010](ADRs/010_alcohol-escalation-ownership.md) (alcohol handoff).

## 1. Product statement

For a club requester and its authorized reviewers, OrganizationalAI accepts a reimbursement case, applies the versioned organization profile and policy deterministically, explains the result, creates a complete review packet or structured escalation, and retains an append-only audit trail. A human remains responsible for approval and settlement.

## 2. MVP goals

The MVP must:

1. Support the two approved workflow types: `MEMBER_PAID` and `ADVANCE_SETTLEMENT`.
2. Capture a case packet with requester, activity/purpose, budget, expense lines, evidence references, and the flow-specific facts needed to calculate a proposed settlement.
3. Evaluate the configured policy in its documented priority order, including evidence integrity, duplicates, scope/category, required documents, deadline, budget, conflict, aggregation, authority, conditional tax evidence, and calculation checks.
4. Return one of two processing results: `ROUTINE_PROCESSED` or `ESCALATED`.
5. Keep `approval_status` as `PENDING_HUMAN_APPROVAL` for every case; the agent may not approve, reject, or transfer money.
6. Produce one structured escalation for every escalated case.
7. Store immutable case and policy/profile snapshots plus an append-only audit-event history.
8. Demonstrate deterministic behavior against the approved synthetic test and Verify suites.

## 3. MVP users and responsibilities

| User | MVP capability | Boundary |
| --- | --- | --- |
| Requester | Creates a reimbursement case and supplies requested facts/evidence. | Cannot approve their own case. |
| Agent / preparer | Validates, normalizes, evaluates, calculates, prepares a review packet, and records audit events. | Cannot invent facts, approve, reject, or transfer money. |
| Authorized reviewer | Receives a structured escalation or routine packet and records a human decision with reason. | Must act only within the configured role/authority. |
| Treasurer / payment executor | Records the settlement evidence after a recorded human approval. | Settlement is not an agent side effect. |
| System administrator | Administers access, backup, and an authorized operational pause. | Has no automatic financial-decision authority. |

## 4. In-scope capabilities

### 4.1 Case preparation and validation

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

### 4.3 Escalation and human handoff

Every escalated result must contain:

- `type`: `FACT_UNKNOWN`, `OUT_OF_POLICY`, or `AUTHORITY_REQUIRED`;
- the intended `addressee_role`;
- related evidence and known facts;
- one specific question and a response format; and
- the `resume_action` that can continue processing after a valid response.

A routine packet has no escalation, but still requires human approval.

### 4.4 Audit and control

- Store an append-only event history for receipt, validation, rule triggering, classification, pause, resume, permitted override, undo, human decision, and settlement evidence.
- Store the normalized-input hash, policy version, profile snapshot, actor identity/role where applicable, and time for reproducibility.
- Implement pause as an operational control, not an outcome prediction.
- Implement undo as a compensating event; never delete or mutate a prior event.
- Permit overrides only for configured internal-policy rules and require an authorized actor, reason, timestamp, and prior outcome reference. Mandatory-law rules are never overridable.

## 5. Explicit non-goals

The MVP does not:

- approve, reject, or transfer money automatically;
- treat `ROUTINE_PROCESSED` as a payment instruction or final approval;
- use an LLM to infer missing financial facts or make policy decisions;
- commit real receipts, bank details, identities, vendor data, credentials, or tokens to this repository;
- expose a shared/public endpoint without the required authentication, authorization, and data-protection controls;
- replace the governing organization's accounting, procurement, tax, or legal obligations; or
- silently reinterpret the historical `TMP-DEV-001` traces as real-policy records.

## 6. Data and security boundary

The first implementation may use synthetic data only until the real-operation checklist in the workflow is complete. Before a real case is accepted, the team must configure and approve the parent organization, accounting/tax regime, categories, thresholds, authority roles, evidence requirements, retention policy, access model, and incident process.

The MVP must minimize personal data, show only masked account information where needed, restrict cases to authorized users, and preserve evidence/audit history according to the approved profile.

## 7. Acceptance criteria

| Area | Acceptance criterion |
| --- | --- |
| Determinism | The same normalized input, policy version, and profile snapshot always produce the same result. |
| Routine processing | The three routine cases in `verify_cases.json` return `ROUTINE_PROCESSED`, no escalation, and `PENDING_HUMAN_APPROVAL`. |
| Escalation | The two escalation cases in `verify_cases.json` return `ESCALATED` with the expected escalation type and a self-contained question. |
| Safety | No suspected-data case receives an assertive conclusion; the agent never approves, rejects, or transfers money. |
| Auditability | A reviewer can reconstruct the input, profile/policy version, triggered rules, evidence references, result, actor, timestamps, and compensation history. |
| Authorization | A requester cannot approve their own case; a reviewer can act only within the configured role and authority. |
| Regression coverage | The full Policy Forge synthetic suite passes, including authority boundaries, duplicate handling, conflict, multi-line aggregation, and both workflow types. |

## 8. Delivery boundary and next document

This specification defines product scope, not the transport or database contract. The versioned contract is defined in [04_reimbursement_system_contract.md](04_reimbursement_system_contract.md), and the adopted test/Verify manifest is defined in [05_reimbursement_case_corpus.md](05_reimbursement_case_corpus.md).

The current temporary backend remains the source of behavior for its existing endpoints until the policy, contract, corpus, and corresponding implementation are adopted together.
