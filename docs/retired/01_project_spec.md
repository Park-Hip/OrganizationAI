# Project Specification

## 1. Document control

**Status:** Draft v0.1.

**Canonical workflow:** Campus student-club event expense reimbursement.

**Challenge:** OrganizationAI 2026, Challenge A: The Escalation Referee.

**Purpose:** Define the product boundary, decision rules, evidence requirements, and documentation structure before implementation begins.

This file is the committed source of truth for project scope.

The leader setup roadmap is local-only operational material and must not be committed.

## 2. Product summary

The product is a public web application that processes expense reimbursement requests for one participating student club under a versioned pilot policy.

It automatically completes routine, complete, eligible requests within its delegated authority.

It safely escalates requests with missing facts, policy violations, or amounts above its authority to a named human reviewer with one answerable question.

Every system and reviewer action creates an append-only audit event.

The MVP does not move money or represent an institutional finance system.

## 3. Problem and intended outcome

Student-club reimbursement requests can require repeated checks of receipts, expense categories, event references, and approval limits.

Routine requests should not consume human decision time when the required facts are complete and the pilot policy clearly permits them.

The system moves those repeatable checks into a transparent, testable decision flow.

It preserves human control for uncertainty, exceptions, and higher-authority decisions.

Success means that a stranger can submit a request, understand the outcome, inspect the decision evidence, and verify five representative cases without an account.

## 4. Users and responsibilities

| Role | Current responsibility | Product responsibility |
| --- | --- | --- |
| Event lead or requester | Submits an expense reimbursement request and supporting facts. | Provides structured request data and receives the result or a specific follow-up question. |
| Club treasurer | Reviews routine reimbursement requests within the club's delegated limit. | Validates the pilot policy and resolves requests that need a treasurer decision. |
| Club president | Decides valid requests above the treasurer's delegated limit. | Resolves authority-exceeded requests when the policy requires presidential approval. |
| System referee | Does not exist in the current workflow. | Applies the versioned policy, routes the request, explains the result, and records audit events. |

The treasurer and president remain accountable human decision-makers.

The system must never claim to be university-wide finance policy unless a relevant institutional owner validates that claim in writing.

## 5. Scope

### In scope

- One participating student club and one reimbursement workflow.
- Synthetic reimbursement requests for public demonstrations and automated tests.
- A compact pilot policy with a version, rule identifiers, and named human authority limits.
- Structured request intake with optional free-text extraction into validated fields.
- Deterministic classification of routine requests and the three required escalation categories.
- Human review actions to approve, reject, pause automation, and undo a prior action through a compensating audit event.
- A public Verify flow that executes five cases through the production decision path and shows a timestamped PASS or FAIL result.
- A decision-detail view that displays the input facts, policy version, rule identifiers, reason, actor, time, and audit history.

### Out of scope

- Real payments, bank transfers, accounting-system integrations, tax decisions, or financial compliance claims.
- Real receipts, vendor details, bank information, or personal financial data in public fixtures.
- Authentication, role-based access control, notifications, mobile applications, and multi-club support.
- OCR accuracy claims, fraud detection, fine-tuning, large retrieval systems, or an LLM making a final decision.
- A generic chatbot that approves reimbursement based on unconstrained free text.

## 6. Decision policy boundary

The deterministic policy evaluator is the decision source of truth.

An optional AI component may extract a typed draft from free text or phrase an explanation.

Every extracted field must pass schema validation before policy evaluation.

The initial policy is a proposed pilot policy until the club treasurer and president validate it.

| Outcome | Condition | Required system behavior |
| --- | --- | --- |
| `AUTO_APPROVED` | Required facts are complete, the category is eligible, the receipt is readable, and the amount is within delegated authority. | Complete the routine decision and append an audit event. |
| `MISSING_FACT` | A required fact is missing, ambiguous, or contradictory. | Stop without approval or rejection and ask for the exact fact needed. |
| `OUT_OF_POLICY` | The category or request conflicts with, or is absent from, the pilot policy. | Stop, cite the relevant rule, and ask the authorized reviewer whether an exception is allowed. |
| `AUTHORITY_EXCEEDED` | The request may be valid but is above the automated or treasurer authority threshold. | Stop and ask the named higher authority for a specific approval or rejection. |

The initial policy template will cover required fields, eligible and ineligible categories, receipt requirements, authority thresholds, exceptions, and escalation owners.

Do not present example thresholds as real club policy before policy-owner validation.

## 7. Functional requirements

| ID | Requirement | Acceptance condition |
| --- | --- | --- |
| FR-01 | Accept a structured reimbursement request with requester, event reference, category, amount, receipt status, and description. | Missing or invalid required fields are shown clearly before an unsupported decision is made. |
| FR-02 | Evaluate each request against one recorded policy version. | The result and audit trace show the policy version and applied rule identifiers. |
| FR-03 | Automatically handle routine requests only. | At least three complete standard cases complete without a human decision. |
| FR-04 | Escalate uncertainty, policy violations, and authority limits distinctly. | Each of the three escalation categories has an actionable, one-answer question. |
| FR-05 | Support human approve, reject, pause, and undo controls. | Each action visibly changes state and appends an audit event without deleting history. |
| FR-06 | Make every decision inspectable. | A user can reconstruct the input, rules, reason, actor, time, outcome, and reversal relation. |
| FR-07 | Provide a no-login Verify flow. | One click runs five sequential cases through the same production path and shows timestamped expected versus actual PASS or FAIL results. |

## 8. Quality and safety requirements

- The public application must work without login or local installation.
- New judge input must be evaluated generically rather than matched to known fixture text or identifiers.
- Uncertain facts must never produce a confident final approval or rejection.
- Audit history is append-only, and undo creates a compensating event rather than deleting a prior event.
- Synthetic, real, observed, and proposed data or claims must be visibly distinguished.
- The deployed flow must be checked in an incognito browser or fresh-device environment before submission.
- The live product, Verify output, slides, video, and documentation must describe the same decision boundary.

## 9. Initial information model

| Record | Essential fields | Purpose |
| --- | --- | --- |
| Policy | ID, version, effective time, rules, authority limits | Makes decisions reproducible and traceable to a declared rule set. |
| Reimbursement request | ID, requester role, event reference, category, amount, receipt status, description, submitted time | Captures the facts needed to decide a request. |
| Decision | Request ID, policy version, outcome, escalation type, rule IDs, explanation, question | Separates the evaluator result from the raw request. |
| Audit event | ID, request ID, time, actor type, action, reason, input snapshot, previous event ID | Preserves a chronological, explainable history including reversals. |
| Verify run and result | Run ID, time, case ID, expected result, actual result, pass status | Proves that the public test flow uses the real decision path. |

## 10. Documentation-phase exit criteria

The documentation map, ownership, and artifact status are maintained in [README.md](README.md).

- The treasurer and president roles are identified, and policy-validation interviews are scheduled.
- The workflow charter and pilot policy have clear validation status rather than invented facts.
- The case corpus structure can represent all three routine cases and all three escalation categories.
- Every rubric area has a named evidence owner and planned proof.
- The system contract lets the UI, evaluator, and Verify flow use the same decision semantics.
- The scope cuts, risks, data-disclosure boundary, and local-only file rule are documented.

## 11. Open decisions

| Decision | Owner | Needed before |
| --- | --- | --- |
| Participating club and named policy owners | Project lead | User research and policy validation. |
| Actual eligible categories, receipt standard, and approval limits | Treasurer and president | Pilot policy approval and evaluator implementation. |
| Whether a policy exception is rejected or routed for review | Treasurer and president | Escalation wording and reviewer experience. |
| Consent method and what participant evidence can be published | Project lead and participants | Recording quotes, screenshots, or user-study findings. |
| Final deployment, database, and optional AI provider | Technical owner | Sprint implementation and runbook completion. |
