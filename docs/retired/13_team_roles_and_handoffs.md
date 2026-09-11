# Team Roles and Handoffs

## Document control

**Status:** Proposed for team confirmation.

**Applies to:** The four-person OrganizationAI 2026 Challenge A team.

**Purpose:** Define accountable ownership, independent verification, and handoffs for the campus student-club reimbursement referee.

## Recommended team structure

Use four independent workstreams.

This structure protects the decision engine, judge experience, real-user evidence, and operational reliability at the same time.

It is the recommended option because the competition score requires much more than a working application.

| Person | Role | Primary outcome | Primary scoring protection |
| --- | --- | --- | --- |
| 1 | Team lead and backend engineer | Deterministic decision path and end-to-end integration | Challenge A decisions and human control/auditability |
| 2 | Policy, scenarios, and user-evidence owner | Validated pilot policy, corpus, and real-user proof | Real users, policy validity, and impact evidence |
| 3 | UI/UX and human-controls engineer | Clear judge-facing application and usable controls | New-input experience, explanation quality, and audit usability |
| 4 | Platform, QA, and demo engineer | Public production proof and independent verification | Live URL, Verify, regression testing, and runbook |

Each workstream has one accountable owner.

Helpers may contribute work, but the owner accepts the result and remains accountable for its definition of done.

## Product boundary shared by all roles

The product is a public web application for reimbursement requests from one participating student club under a versioned pilot policy.

It automatically completes only routine requests that are complete, eligible, and within delegated authority.

It must safely stop and ask a specific question when facts are missing, the request is outside policy, or authority is exceeded.

It does not move money, impersonate institutional finance approval, make tax decisions, or use real financial data in public fixtures.

| Result | Required system behavior |
| --- | --- |
| `AUTO_APPROVED` | Complete the routine request and append an audit event. |
| `MISSING_FACT` | Do not decide and ask for the exact missing, ambiguous, or conflicting fact. |
| `OUT_OF_POLICY` | Cite the relevant rule and ask the authorized person whether an exception is allowed. |
| `AUTHORITY_EXCEEDED` | Route a decision-ready approval or rejection question to the named higher authority. |

## Role 1 - Team lead and backend engineer

### Accountable ownership

- Own the deterministic policy evaluator, result schema, API, state transitions, and append-only audit event model.
- Own pause, approve, reject, and undo semantics, including compensating audit events for undo.
- Publish the request, decision, audit, and control contracts before UI and Verify integration begins.
- Run the daily integration decision and maintain the cut list.
- Make final scope decisions when work does not map to the rubric or threatens the public demo gate.

### Required deliverables

- Implemented evaluator that resolves all approved policy cases without fixture-text matching.
- API and state-transition contract in `docs/07_system_contract.md`.
- Auditable decision history that records input, policy version, rule IDs, actor, time, outcome, reason, and reversal relation.
- A thin end-to-end path that UI and QA can use from Sprint Day 1.

### Boundary

This role does not self-certify the public Verify run or independently own the real-user research evidence.

Those checks belong to other owners to preserve independent verification.

## Role 2 - Policy, scenarios, and user-evidence owner

### Accountable ownership

- Facilitate policy validation with the participating club's treasurer and president.
- Maintain the versioned pilot policy, rule IDs, required facts, authority matrix, and escalation wording.
- Create and maintain at least 15 labeled cases, including the public five-case Verify suite and private held-out boundary cases.
- Recruit and document three real participants in actual workflow roles, including consent, quotes, feedback, and one adverse effect.
- Maintain the evidence map inputs for policy validity, real users, impact, limitations, and slides.

### Required deliverables

- Validated `docs/02_workflow_charter.md` and `docs/03_pilot_policy_v0.1.md`.
- A completed case corpus with expected outcomes, rule IDs, escalation types, and specific expected questions.
- Participant evidence that shows consent, real role, verbatim feedback, one feedback-originated improvement, and one adverse or unexpected effect.
- Evidence-ready input for Slides 1, 3, and 5.

### Boundary

This role does not change the evaluator solely to make an expected result pass.

Changes to policy behavior require a reviewed policy update, corresponding cases, and backend implementation by the backend owner.

## Role 3 - UI/UX and human-controls engineer

### Accountable ownership

- Build the five judge-facing screens: landing page, request form, decision result, audit/control detail, and Verify report.
- Translate each decision into plain language that names the observed fact or rule, consequence, decision owner, and one answerable question.
- Build visible pause, approve, reject, and undo controls using the backend contract.
- Keep the live UI consistent with the input-process-output boundary presented in Slide 2.
- Capture UI evidence and make the public journey responsive and accessible.

### Required deliverables

- A public landing page that tells a visitor exactly what to try without login.
- A structured request path that clearly handles missing or invalid fields.
- A decision detail and audit timeline that a nontechnical user can understand.
- A human-control experience that visibly updates the state and shows the resulting audit event.

### Boundary

This role does not define policy thresholds or implement separate decision rules in the client.

The UI renders the shared backend decision contract and never duplicates policy logic.

## Role 4 - Platform, QA, and demo engineer

### Accountable ownership

- Own CI, deployment configuration, environment readiness, health checks, and safe recovery procedures.
- Build the one-click Verify harness that runs five cases through the same production decision path as new user input.
- Maintain regression, boundary, adversarial, and fresh-device checks.
- Maintain the deployment and demo runbook, rehearsal log, and operational evidence.
- Independently report failures and block release when the public flow is broken or unverified.

### Required deliverables

- A public no-login URL and documented deployment process.
- A timestamped Verify report showing expected versus actual PASS or FAIL for five sequential cases.
- Regression tests for policy boundaries and safety cases.
- A completed `docs/08_demo_runbook.md` with recovery and fresh-device verification.

### Boundary

This role does not change expected outcomes to make a Verify run pass.

Any discrepancy becomes a defect or an explicitly reviewed policy decision.

## Handoff contract

| Time | Owner | Receiver | Required handoff | Acceptance condition |
| --- | --- | --- | --- | --- |
| Before Sprint Day 1 | Policy, scenarios, and user evidence | Backend and QA | Required facts, proposed rule IDs, case template, and policy-validation schedule | Backend can define typed contracts without inventing policy values. |
| Sprint Day 1 | Backend | UI/UX and QA | Request, decision, audit, and control contracts with state transitions | UI can render every outcome and QA can write independent assertions. |
| Sprint Day 2 | UI/UX | Backend and policy owner | Five-screen flow and escalation copy | Every escalation has a fact or rule, consequence, named owner, and one decision-ready question. |
| Sprint Days 2-3 | Platform and QA | Entire team | Staging or public URL, Verify report, regression defects, and fresh-device checklist | Verify uses the production decision path and has no hardcoded success screen. |
| Sprint Day 4 onward | Policy, scenarios, and user evidence | UI/UX and team lead | Consented feedback, adverse effect, and feedback-originated improvement candidate | A traceable path exists from feedback to issue, change, and evidence. |

## Support rules

Support begins only after the helper's primary daily milestone is complete.

The primary owner remains accountable for accepting the work.

| When available | Helpful support | Not allowed |
| --- | --- | --- |
| Team lead and backend engineer | Pair-review audit behavior and recovery tests with QA. | Taking ownership of additional UI screens or self-certifying Verify. |
| Policy, scenarios, and user-evidence owner | Convert held-out cases into regression specifications and review escalation copy with UI/UX. | Changing the evaluator to force a desired test outcome. |
| UI/UX and human-controls engineer | Improve accessibility, responsive behavior, and demo capture with QA. | Duplicating policy logic in the client. |
| Platform, QA, and demo engineer | Pair-test UI, rehearse the demo, and verify the evidence map. | Quietly changing production behavior or expected results. |

## Shared milestones

| Milestone | Exit condition |
| --- | --- |
| Before the official sprint | Workflow direction, policy-owner meeting, participant plan, contracts, task board, and accounts are ready. No substantive core product code is built before the official sprint. |
| Sprint Day 1 | A thin path runs from structured input through the deterministic evaluator to a rendered result. |
| Sprint Day 3 public-demo gate | The public URL works without login, Verify runs five cases with a real timestamp, three routine cases auto-complete, two escalation cases stop safely, a new incomplete input is safe, and audit controls visibly work. |
| Sprint Day 4 onward | The team collects user feedback, implements one evidenced improvement, hardens the demo, and prepares the required slides, video, runbook, and build log. |

## Operating rules

1. Every task has one owner, one reviewer, a rubric mapping, a definition of done, and an evidence location.
2. The team reports daily by showing an artifact, test result, or deployed behavior instead of a percentage estimate.
3. A blocker that lasts more than 30 minutes is posted for help with its expected decision or missing input.
4. Optional AI extraction, visual polish, and analytics are cut before reliability, Verify, auditability, documentation, or evidence.
5. All policy-affecting changes update the policy, cases, tests, and relevant explanation in the same pull request.
6. The team follows `docs/12_git_collaboration_playbook.md` for branches, reviews, and merge history.

## Decision record

The team should confirm this recommended structure before the sprint starts.

Any change to a role boundary must identify the new owner, reviewer, affected handoffs, and affected rubric evidence.
