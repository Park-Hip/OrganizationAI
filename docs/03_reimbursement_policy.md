# Reimbursement Processing Policy v1.2

## Document control

**Status:** Project-approved policy baseline. It may not be used for real cases until the activation conditions in [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md) are satisfied.

**Policy ID:** `POL-REIMB-CLB`

**Policy version:** `1.2.0`

**Canonical rule source:** [policy-forge-baseline/policy_rules.yaml](../policy-forge-baseline/policy_rules.yaml).

**Human-readable source:** [Policy Forge reimbursement policy](../policy-forge-baseline/Policy_Hoan_Ung_CLB.md).

**Purpose:** Define deterministic processing, escalation, calculation, and control rules for club reimbursement cases. The agent prepares packets and escalates uncertainty; it never approves, rejects, or transfers money.

## 1. Scope and policy precedence

This policy covers:

- `MEMBER_PAID`: repayment for a member's approved club expense paid with personal funds; and
- `ADVANCE_SETTLEMENT`: accounting for a club advance, including money to return or an additional amount proposed after approval.

The policy is subordinate to mandatory law and to the governing organization's applicable financial, accounting, procurement, tax, and data-protection rules. When requirements conflict, the more restrictive applicable rule controls and the case is escalated to an authorized human. Internal approval cannot legalize an illegal expense.

Only synthetic data may be committed to this repository. Real cases require the approved environment, access controls, and retention policy described in the workflow document.

## 2. Organization profile and configuration

Each decision uses an immutable, versioned `OrganizationProfile`. The policy rules must not be implemented with unversioned hard-coded configuration.

| Configuration | Policy Forge default | Operational rule |
| --- | --- | --- |
| `profile_id` | `DEFAULT-CLB-STUDENT` | The actual profile ID, owner, and effective version must be recorded before real use. |
| Profile/policy version, owner, effective date | `1.2.0`, `TO_BE_CONFIRMED`, `null` | Profile version, policy version, owner, and effective date are server-owned and snapshotted with every case. |
| Parent organization and accounting regime | `TO_BE_CONFIRMED` | Must be confirmed before real use. |
| Currency | `VND` | Do not convert currency without an approved exchange-rate rule. |
| Submission deadline | 10 business days | A later submission requires authority review. |
| Routine-processing threshold | 5,000,000 VND | Amounts strictly greater than the configured threshold require authority review. An amount at the threshold is not automatically approved. |
| Authority threshold operator | `greater_than` | The comparison applied to the routine-processing threshold. |
| Conditional non-cash evidence threshold | 5,000,000 VND | Applied only when the configured tax regime applies; it is not an approval threshold. |
| Aggregation keys | normalized vendor, transaction date, purpose code | Related lines are aggregated before threshold and tax checks. |
| Roles and retention | MEMBER/TREASURER/CLUB_CHAIR; OCR 30 days | Roles, OCR retention, and official-record retention are profile-owned, never hard-coded. |
| Separation of duties | `no_self_approval: true` | Requester and approver must be independent. |

The baseline profile permits `venue`, `transport`, `printing`, `supplies`, `communication`, `approved_food`, and `approved_service`; treats `gift`, `honorarium`, `equipment`, and `late_submission` as conditional; treats `alcohol`, `tobacco`, and `personal_expense` as prohibited by internal policy; and treats `illegal_goods` as legally prohibited (never overridable). Categories, thresholds, roles, owner, effective date, versions, and retention settings are configuration inputs requiring confirmation before real operation.

## 3. Roles and agent boundary

| Role | Policy responsibility |
| --- | --- |
| Requester (`MEMBER`) | Supplies truthful case facts and supporting evidence; cannot approve their own case. |
| Agent / preparer | Validates, normalizes, cross-checks, calculates, classifies, prepares packets and escalations, and records audit events. |
| Treasurer | Reviews within delegated authority and executes settlement only after recorded human approval. |
| Club Chair | Handles over-threshold, budget, and conflict-of-interest authority decisions. |
| Parent Advisor / governing organization | Confirms configuration and handles sensitive exceptions as configured. |
| System administrator | Administers access, security, backup, and authorized operational pauses. |

The agent is always configured with `agent_can_approve: false`, `agent_can_reject: false`, and `agent_can_transfer_money: false`. It must not invent facts, ignore a suspicion flag, or override mandatory law.

## 4. Output contract

| Field | Permitted value | Meaning |
| --- | --- | --- |
| `processing_result` | `ROUTINE_PROCESSED` | The agent completed checks, calculations, and a review packet. This is not an approval or payment instruction. |
| `processing_result` | `ESCALATED` | Routine processing stopped and the system created one structured escalation. |
| `escalation_type` | `FACT_UNKNOWN`, `OUT_OF_POLICY`, or `AUTHORITY_REQUIRED` | Required for every escalation; otherwise `null`. |
| `approval_status` | `PENDING_HUMAN_APPROVAL` | Fixed for every agent result. |
| `control_state` | `ACTIVE` or `PAUSED` | Operational state, separate from the processing result. |

Every escalation includes its type, `addressee_role`, related evidence, known facts, a specific question, response format, and a `resume_action`.

## 5. Evaluation order and rules

Rules are evaluated in ascending priority. A terminal result stops routine evaluation; aggregation and calculation rules are non-terminal transformations.

| Priority | Rule ID | Condition | Result |
| --- | --- | --- | --- |
| 10 | `RULE-SYS-001` | The case or authorized control state is paused. | Set `control_state: PAUSED` and halt processing without a processing result. |
| 20 | `RULE-FACT-001` | Required attachment is unreadable or OCR confidence is below the configured minimum. | `ESCALATED / FACT_UNKNOWN`. |
| 21 | `RULE-FACT-002` | Declared totals, line amounts, evidence amounts, payment proof, or advance amount conflict. | `ESCALATED / FACT_UNKNOWN`. |
| 22 | `RULE-FACT-003` | A required fact cannot be deterministically derived from verified evidence. | `ESCALATED / FACT_UNKNOWN`. |
| 30 | `RULE-DUP-001` | The duplicate check is absent or `NOT_RUN`, or a duplicate match is suspected, incomplete, or disputed. | `ESCALATED / FACT_UNKNOWN`. |
| 31 | `RULE-DUP-002` | The same verified document was previously paid and no credit/reversal applies. | `ESCALATED / OUT_OF_POLICY`; an authorized human determines corrective action. |
| 40 | `RULE-SCOPE-001` | An expense has no demonstrated link to an approved club task or event. | `ESCALATED / OUT_OF_POLICY`. |
| 41 | `RULE-SCOPE-002` | The category is in `legally_prohibited_categories` or the expense is otherwise flagged illegal by applicable law. | `ESCALATED / OUT_OF_POLICY`; no internal exception is permitted. |
| 42 | `RULE-CAT-001` | A category is unrecognized, or a prohibited category that is neither illegal nor alcohol applies. | `ESCALATED / OUT_OF_POLICY`. |
| 43 | `RULE-CAT-002` | The category is alcohol. | `ESCALATED / OUT_OF_POLICY` to a single `CLUB_CHAIR` addressee; `PARENT_ADVISOR` consultation is an auditable prerequisite, not a second agent decision. |
| 44 | `RULE-CAT-003` | A conditional category lacks the required prior approval. | `ESCALATED / AUTHORITY_REQUIRED`. |
| 50 | `RULE-DOC-001` | A required dossier component is absent. | `ESCALATED / FACT_UNKNOWN`. |
| 55 | `RULE-DEADLINE-001` | Submission is after the configured business-day deadline. | `ESCALATED / AUTHORITY_REQUIRED`. |
| 60 | `RULE-BUDGET-001` | Verified eligible amount exceeds remaining approved budget. | `ESCALATED / AUTHORITY_REQUIRED`. |
| 61 | `RULE-CONFLICT-001` | Requester is the approver or an approver has a declared conflict. | `ESCALATED / AUTHORITY_REQUIRED` to an independent authorized reviewer. |
| 62 | `RULE-AGG-001` | Multiple related lines share the configured aggregation keys. | Aggregate before threshold and tax checks; continue processing. |
| 63 | `RULE-AUTH-001` | Aggregated verified eligible amount is strictly greater than the routine-processing threshold. | `ESCALATED / AUTHORITY_REQUIRED` to the configured over-threshold authority. |
| 70 | `RULE-TAX-001` | Tax regime applies, related aggregated purchase reaches the non-cash threshold, and verified non-cash evidence is absent. | `ESCALATED / FACT_UNKNOWN`. |
| 80 | `RULE-CALC-001` | `ADVANCE_SETTLEMENT` lines are verified. | Calculate eligible total, amount to return, and additional payment; continue processing. |
| 81 | `RULE-CALC-002` | `MEMBER_PAID` lines are verified. | Calculate eligible total and proposed reimbursement; continue processing. |
| 90 | `RULE-ROUTINE-001` | No higher-priority terminal rule applies; facts are verified; budget/authority are satisfied; no unresolved flag remains. | `ROUTINE_PROCESSED`, no escalation, and `PENDING_HUMAN_APPROVAL`. |

## 6. Calculation rules

Only verified eligible lines contribute to the proposed settlement.

| Flow | Formula |
| --- | --- |
| Both flows | `eligible_total = sum(eligible line amounts)` |
| `ADVANCE_SETTLEMENT` | `balance = advance_amount - eligible_total` |
| `ADVANCE_SETTLEMENT` | `amount_to_return = max(balance, 0)` |
| `ADVANCE_SETTLEMENT` | `additional_payment = max(-balance, 0)` |
| `MEMBER_PAID` | `reimbursement_amount = eligible_total` |

A calculation mismatch is not silently repaired. It remains a `FACT_UNKNOWN` escalation until verified evidence resolves it.

## 7. Audit, pause, override, and undo

The audit history is append-only.
It records at least `RECEIVED`, `VALIDATED`, `RULE_TRIGGERED`, `CLASSIFIED`, `PAUSED`, `RESUMED`, `OVERRIDDEN`, `UNDONE`, `HUMAN_DECISION`, and `SETTLEMENT` events, each with the policy version, input hash, actor, role, time, triggered rules, ordered predecessor where applicable, and explanation needed to reproduce the result.
Pause and resume require an authorized role and reason.
Override requires a reason and previous outcome reference.
Undo requires a reason and target audit-event reference.
Human decisions require a reason, previous outcome, and decision.
Settlement requires a reason, the predecessor decision event, and settlement evidence.

- An authorized pause takes precedence over every evaluation rule and does not delete outstanding questions or missing approvals.
- Resume restarts processing without erasing prior history.
- An override is limited to permitted internal-policy rules and requires an authorized actor ID and role, reason, timestamp, and previous outcome reference.
- Mandatory-law rules are never overridable.
- Undo appends a compensating event referring to the target audit event; it never changes or deletes history.

## 8. Verification and migration

The canonical synthetic test set is [test_cases.json](../policy-forge-baseline/test_cases.json); the quick Verify suite is [verify_cases.json](../policy-forge-baseline/verify_cases.json); the concise fixture-input shape is [reimbursement-fixture.schema.json](../policy-forge-baseline/reimbursement-fixture.schema.json); and the deterministic expansion mapping is [expansion_spec.md](../policy-forge-baseline/expansion_spec.md). The 29-case suite covers both flows, routine and authority boundaries, unreadable and missing evidence, inconsistent totals, missing facts, absent/`NOT_RUN` and confirmed duplicate checks, illegal categories, unrecognized categories, conditional categories with and without approval, deadline boundaries, budget and conflict, split-purchase aggregation on both sides of the threshold, and the conditional non-cash evidence rule on both sides.

The historical `TMP-DEV-001` policy remains archived synthetic behavior. Its test categories, 1,000-VND limit, `AUTO_APPROVED` outcome, and `DEMO_REVIEWER` actor are not part of this policy and must not be copied into the real-policy implementation.

## 9. Real-operation checklist

Before accepting a real case, the team must:

- [ ] Record the policy owner, parent organization, approval date, effective date, and profile version.
- [ ] Confirm the accounting and tax regime, applicable source hierarchy, categories, thresholds, roles, evidence rules, retention rules, and exception authority.
- [ ] Implement role-based authorization, evidence/data protection, incident handling, and settlement controls in the approved environment.
- [ ] Run the policy suite, Verify suite, authorization tests, pause/undo tests, and reproducibility checks against the adopted system contract.
- [ ] Preserve `TMP-DEV-001` traces as labelled synthetic historical records.
