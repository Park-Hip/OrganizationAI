# Leader Setup-Phase Roadmap

## Purpose

This document lists the work that the team leader can complete alone before the official sprint starts.

The goal is to prepare people, decisions, documents, access, and acceptance criteria so the team can implement quickly during the sprint.

Do not build the core policy engine, the production UI, or other substantive product code before the official sprint.

Any pre-existing scaffold must be small, disclosed in the final README, and allowed by the competition rules.

## Outcome Before Sprint Day 1

By Sprint Day 1, the team must have a locked workflow direction, a policy owner meeting scheduled, a documented task board, a repository plan, and a shared evidence plan.

The selected workflow is a referee for campus student-club event expense reimbursement.

The prototype uses a signed pilot policy for one participating club.

The prototype does not move money, impersonate institutional finance approval, validate tax compliance, or use private financial data in public fixtures.

## Do This Today

- [ ] Create a shared team workspace in Notion, GitHub Projects, Trello, or Linear.
- [ ] Create the project repository if permitted by the competition rules.
- [ ] Add this repository's current rubric and challenge brief as the team's scoring source of truth.
- [ ] Invite every teammate and confirm one primary owner and one reviewer for each workstream.
- [ ] Send interview invitations to one event lead, one treasurer, and one club president.
- [ ] Book a 60-minute team kickoff and a 30-minute policy-validation meeting.
- [ ] Create the document folders and empty document files listed below.
- [ ] Add the Sprint Day 3 public-demo gate to the task board.

## Set the Scope Direction

Use this exact working statement until the policy owner revises it.

> We build a web-based referee that automatically completes routine reimbursement requests for one student club when the request is complete, eligible, within the approved event budget, and within delegated authority.

> The system safely escalates incomplete facts, out-of-policy requests, and valid requests above the agent's delegated authority.

> Every decision is auditable, reversible through a compensating event, and controllable by a human reviewer.

### In Scope

- One real student club and one defined event-reimbursement workflow.
- Synthetic reimbursement fixtures for public demonstration and testing.
- A compact, versioned pilot policy validated by the treasurer and president.
- Automatic handling of routine cases only.
- The three required escalation categories: `MISSING_FACT`, `OUT_OF_POLICY`, and `AUTHORITY_EXCEEDED`.
- A public Verify flow with five sequential cases.
- An append-only audit trail with pause, approve, reject, and undo actions.

### Explicitly Out of Scope

- Real payments, bank transfers, accounting integrations, and tax decisions.
- Login, RBAC, mobile applications, notifications, and multi-club support.
- OCR accuracy claims, document fraud detection, fine-tuning, and large RAG systems.
- Any use of real receipts, vendor information, or personal data without explicit written permission.
- A generic chatbot that makes reimbursement decisions from free text alone.

## Create the Task Board

Create these general statuses in the shared task board.

1. Backlog.
2. Ready.
3. In progress.
4. In review.
5. Testing.
6. Evidence.
7. Blocked.
8. Done.

Add these labels.

- `rubric-40-operational`
- `rubric-20-users`
- `rubric-20-control`
- `rubric-20-decision`
- `must-have`
- `risk`
- `needs-policy-owner`
- `needs-user-evidence`

Create every ticket with a rubric mapping, named owner, reviewer, acceptance check, and evidence location.

### First Tickets to Add

| Ticket | Owner | Reviewer | Definition of done |
|---|---|---|---|
| Validate pilot policy v0.1 | Policy and scenarios | Leader | Treasurer and president confirm the rules and authority limits in writing. |
| Recruit three real participants | Leader | Policy and scenarios | Roles, consent method, and interview times are recorded. |
| Create 15-case corpus | Policy and scenarios | Leader | Every case has an expected result, rule ID, escalation type, and expected question. |
| Define decision and audit contract | Leader | Platform, QA, and evidence | Input, result, audit event, approval, pause, and undo fields are agreed. |
| Draft five-screen UI map | UI/UX | Leader | Screens cover landing, submit, Verify, decision detail, and audit control. |
| Create deploy and Verify plan | Platform, QA, and evidence | Leader | Public URL, environment variables, production endpoint, and fresh-device check are defined. |
| Plan user study and baseline measure | Policy and scenarios | UI/UX | Interview questions and a measurement method are ready before user testing. |

## Prepare the GitHub Repository

Complete repository administration and documentation only during setup.

- [ ] Choose a clear repository name such as `club-expense-referee`.
- [ ] Add the correct team members and ensure each person can create branches and pull requests.
- [ ] Enable Issues and Projects.
- [ ] Add a minimal issue template with fields for rubric mapping, acceptance criteria, and evidence.
- [ ] Add a pull-request template with fields for policy impact, tests, screenshots, and audit impact.
- [ ] Protect the default branch if this does not conflict with the event's commit-history requirement.
- [ ] Write down the deployment account owner and recovery contact.
- [ ] Record all AI tools used from the first day for the required build log.
- [ ] Agree never to force-push or squash away the sprint's public history.

## Prepare the Document Pack

Create these documents as short, living files.

| File | Leader prepares now | Team completes during sprint |
|---|---|---|
| `docs/02_workflow_charter.md` | Scope, roles, exclusions, success statement | Final decision and policy-owner sign-off reference |
| `docs/03_pilot_policy_v0.1.md` | Policy template and open decisions | Approved thresholds, categories, rule IDs, and authority matrix |
| `docs/04_case_corpus.csv` | Column headings and case categories | Fifteen labeled cases and private held-out variants |
| `docs/05_user_research_plan.md` | Participant roles, consent, questions, and schedule | Quotes, observations, adverse effect, and feedback-originated change |
| `docs/06_evidence_map.md` | Rubric-to-proof table | Links to tests, screenshots, commits, slides, and video timestamps |
| `docs/07_system_contract.md` | Field and state templates | Final API, rule, audit, and control contract |
| `docs/08_demo_runbook.md` | Judge journey outline | Final deployment, Verify, recovery, and fresh-device instructions |
| `docs/09_build_log.md` | Sections for AI tools, time, cost, and cuts | Actual usage and the largest feature cut |

## Draft the Policy Meeting Agenda

Use this 30-minute agenda with the treasurer and president.

1. Confirm the actual reimbursement workflow and who performs each role.
2. List which expense categories are normally eligible.
3. List which facts and evidence are always required.
4. Decide the treasurer's delegated limit and the president's approval limit.
5. Define what happens when a receipt is missing, illegible, or conflicts with the request.
6. Define categories that are outside the pilot policy.
7. Validate three routine examples and three escalation examples.
8. Ask permission to quote the participants and document their role.

Do not invent thresholds or describe pilot rules as university-wide policy.

## Prepare the User-Evidence Runway

The user-proof category is worth 20 points and cannot be recovered at the end of the week.

Record the following before the sprint begins.

- [ ] Participant full name, actual role, and workflow relationship.
- [ ] Consent status and whether name, role, quote, or image may be used.
- [ ] A baseline question about the current manual process.
- [ ] A question about where mistakes, waiting, or uncertainty occur.
- [ ] A question designed to uncover an adverse effect or new burden.
- [ ] A follow-up appointment after the working prototype is available.

Use observations, not unsupported claims.

The final report should say what three people experienced, not what all student organizations experience.

## Prepare the Team Handoffs

### Leader and Backend

You own the deterministic rule evaluation, result schema, state transitions, audit event structure, and integration decisions.

Give the UI/UX teammate stable input and result fields before Sprint Day 1 ends.

Give the Platform, QA, and evidence teammate the production route contract before the Verify harness is built.

### UI/UX

Give this teammate the five judge-facing screens, expected decision states, plain-language explanations, and a strict rule that the live UI must match Slide 2.

Ask for an early clickable flow before visual polish.

### Platform, QA, and Evidence

Give this teammate the task of deployment, production-path Verify, fresh-device checks, regression cases, screenshots, and evidence links.

Prompt A/B testing begins only after the deployed five-case Verify suite passes.

### Policy, Scenarios, and Users

Give this teammate responsibility for policy wording, the corpus, held-out cases, participant sessions, consent records, quotes, and feedback interpretation.

Prompt A/B testing is limited to optional fact extraction and escalation wording, never the core decision.

## Define the Sprint Day 3 Gate

No optional feature may begin until all items below are true on the public URL.

- [ ] The landing page gives a stranger one clear first action.
- [ ] Three routine cases complete automatically under the versioned policy.
- [ ] Two Verify cases escalate safely with decision-ready questions.
- [ ] The Verify table has a real timestamp and PASS or FAIL output.
- [ ] A newly typed incomplete request reaches `MISSING_FACT` without a confident decision.
- [ ] Any decision can be opened as an audit trace.
- [ ] Pause, approve or reject, and undo visibly change the state and append audit events.

## Daily Leader Routine During the Sprint

Run a 20-minute stand-up each morning.

Ask each teammate what rubric item they advanced, what they will finish today, and what is blocked.

Run a 15-minute integration check each evening on the deployed URL.

Reject work that is not mapped to the rubric, not testable, or not auditable.

Record every product decision in an issue or pull request so it becomes submission evidence.

## Final Setup Checklist

- [ ] Workflow scope is locked.
- [ ] Three real roles are identified and contacted.
- [ ] Policy meeting is booked.
- [ ] Task board contains owner, reviewer, rubric mapping, and acceptance check for every ticket.
- [ ] Repository access, project board, and documentation structure are ready.
- [ ] The team knows that deployment, testing, and evidence are continuous work, not an end-of-week task.
- [ ] The Day 3 gate is visible on the board and blocks prompt work and visual polish.
- [ ] Everyone agrees that the deterministic policy engine is the decision-maker.
