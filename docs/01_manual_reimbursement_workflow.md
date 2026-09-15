# Manual Reimbursement Workflow v1.1

## Document control

**Status:** Project-approved workflow baseline. Real-world activation remains conditional on the configuration and approval record below.

**Policy source:** [Policy Forge reimbursement policy](../policy-forge-baseline/Policy_Hoan_Ung_CLB.md) and [machine-readable rules](../policy-forge-baseline/policy_rules.yaml) (`POL-REIMB-CLB` v1.1.0).

**Purpose:** Describe the intended end-to-end club reimbursement workflow for people and systems. It separates automated processing from human approval and payment.

**Activation conditions:** Before a real case is accepted, record the named parent organization, applicable accounting/tax regime, approved `OrganizationProfile`, policy owner, effective date, and data-handling approval. Until then, use synthetic data only.

## 1. Workflow boundary

This workflow supports two reimbursement flows:

- `MEMBER_PAID`: a member requests repayment for an approved club expense paid with personal funds.
- `ADVANCE_SETTLEMENT`: a member accounts for a club advance, including money to return or an additional amount to pay after approval.

The agent may read, normalize, cross-check, calculate, classify, create a review packet, create a structured escalation, and write audit events. It must not approve, reject, transfer money, invent facts, or override mandatory law.

## 2. Roles and separation of duties

| Role | Responsibility in this workflow | Must not do |
| --- | --- | --- |
| Requester (`MEMBER`) | Submit the case and supporting evidence; answer requests for clarification. | Approve their own request. |
| Agent / preparer | Check data and evidence, run the policy, calculate, prepare the packet, and record audit events. | Approve, reject, or transfer money. |
| Treasurer | Check the prepared packet, act within delegated authority, and execute an approved settlement. | Approve their own request or disburse without human approval. |
| Club Chair | Decide over-threshold, budget, or conflict-of-interest escalations. | Override mandatory law. |
| Parent Advisor / governing organization | Confirm configuration, applicable regime, and sensitive exceptions. | Approve without a recorded reason and audit trail. |
| System administrator | Manage authorized access, security, backup, and an authorized pause. | Change a financial outcome without authority. |

## 3. Required case packet

A case contains the following before routine processing can finish:

1. Requester identity and contact channel.
2. Approved task/event, purpose, budget reference, approved amount, and remaining budget.
3. One or more expense lines: vendor, date, purpose code, category, amount, payment method, and evidence references.
4. Readable, verified evidence: invoice/receipt, payment proof, and required prior approval.
5. A masked reimbursement account; never expose a full account number in logs or public materials.
6. For `ADVANCE_SETTLEMENT`: advance reference and advance amount.
7. For `MEMBER_PAID`: proof that the requester made the payment and a declaration that it has not been reimbursed elsewhere.

## 4. End-to-end workflow

| Step | Actor | Action | System result / handoff |
| --- | --- | --- | --- |
| 1. Start case | Requester | Selects `MEMBER_PAID` or `ADVANCE_SETTLEMENT`; submits the packet and evidence. | System assigns a case ID and writes a `RECEIVED` audit event. |
| 2. Validate and preserve facts | Agent | Validates the case shape; records input/evidence references and policy/profile version. | Invalid structure is returned for correction; valid facts enter processing. |
| 3. Check evidence and consistency | Agent | Checks readability, verified fields, totals, payment proof, missing data, and duplicate signals. | Unclear, missing, conflicting, or suspected-duplicate facts become `ESCALATED / FACT_UNKNOWN`. |
| 4. Check scope and category | Agent | Verifies the event/purpose link and applies allowed, conditional, prohibited, and mandatory-law constraints. | Out-of-policy items become `ESCALATED / OUT_OF_POLICY`; conditional items without approval become `ESCALATED / AUTHORITY_REQUIRED`. |
| 5. Apply budget, conflict, and authority checks | Agent | Aggregates related lines by vendor/date/purpose; checks deadline, remaining budget, self-approval conflict, and authority threshold. | Over-budget, late, conflicted, or over-threshold cases become `ESCALATED / AUTHORITY_REQUIRED`. |
| 6. Apply conditional tax evidence check | Agent | When the configured tax regime applies, checks required non-cash evidence for the configured aggregated threshold. | Missing required evidence becomes `ESCALATED / FACT_UNKNOWN`. |
| 7. Calculate the proposed settlement | Agent | Calculates only verified eligible lines. For advances: return amount or additional payment; for member-paid: proposed reimbursement. | A transparent calculation with line/evidence references is added to the packet. |
| 8. Classify and explain | Agent | Produces either a routine-processing outcome or one structured escalation. | Every outcome has rule IDs, evidence used, a Vietnamese explanation, and `PENDING_HUMAN_APPROVAL`. |
| 9. Human decision | Treasurer, Club Chair, or authorized independent reviewer | Reviews the packet or answers the targeted escalation question. | A human decision, reason, role, time, and any permitted exception are appended to the audit history. |
| 10. Settle and close | Treasurer / authorized payment system | After a recorded human approval, returns advance surplus or executes the approved reimbursement/additional payment. | Settlement evidence is linked; the workflow never treats an agent result as a payment instruction. |

## 5. Decision outcomes

| Processing result | Escalation type | Meaning | Required next action |
| --- | --- | --- | --- |
| `ROUTINE_PROCESSED` | `null` | The agent completed routine checks and prepared a packet. This is not approval. | Human review remains required; `approval_status` is `PENDING_HUMAN_APPROVAL`. |
| `ESCALATED` | `FACT_UNKNOWN` | A material fact is missing, unreadable, conflicting, or suspicious. | Ask the person who can supply evidence one concrete question. |
| `ESCALATED` | `OUT_OF_POLICY` | The expense is prohibited, unrelated, illegal, or already paid. | Route the policy/exception question to an authorized reviewer; mandatory law cannot be overridden. |
| `ESCALATED` | `AUTHORITY_REQUIRED` | The case exceeds delegated authority/budget, is late, is conditional, or has a conflict. | Route to the required independent authority with clear options and a reason field. |

Every escalation must contain: its type, addressee role, related evidence, known facts, one specific question, response format, and resume action.

## 6. Policy order and safety controls

The evaluator applies the policy in this order:

1. Authorized pause and data-integrity checks.
2. Duplicate and fraud signals.
3. Scope, purpose, and category checks.
4. Required-document checks.
5. Deadline, budget, conflict, aggregation, and authority checks.
6. Invoice, payment, and tax-condition checks.
7. Calculation and routine classification.

A pause stops processing before all other rules. The workflow retains an append-only audit trail for receipt, validation, triggered rules, classification, pause/resume, permitted override, and undo. Undo is a compensating event; it never deletes history. An override needs the authorized actor, role, reason, time, and prior outcome, and cannot override mandatory law.

## 7. Operational controls

- Access is role-scoped: requesters see only their cases; reviewers see only cases within their authority; administrators do not automatically receive financial-decision authority.
- Commit only synthetic data. Real evidence, identities, bank details, and tokens must never enter this repository.
- Store or display masked account numbers in logs and review materials.
- Retain official records according to the confirmed governing organization and applicable law; retain temporary OCR artifacts only according to the approved profile.
- Use the policy/profile version and normalized-input hash to make results reproducible.

## 8. Relationship to the current temporary implementation

The existing `TMP-DEV-001` workflow remains historical synthetic development behavior. It is not this workflow and must not be relabelled as such. Its append-only trace, profile snapshot, deterministic evaluator, and compensation pattern are useful implementation foundations, but its one-line scope, test categories, 1,000-VND limit, `AUTO_APPROVED` outcome, and `DEMO_REVIEWER` control actor must be retired in the real-policy migration.

## 9. Real-operation checklist

Before a real case is accepted:

- [ ] Record the approving policy owner, organization, approval date, and effective date.
- [ ] Confirm the accounting and tax regime and populate the organization profile.
- [ ] Confirm categories, thresholds, authority roles, evidence standards, and retention rules.
- [ ] Review the policy, workflow, system contract, corpus, and user-facing wording together.
- [ ] Preserve all existing `TMP-DEV-001` records as labelled synthetic historical traces.
