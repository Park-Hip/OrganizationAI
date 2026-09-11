# Pre-Sprint Team Preparation Roadmap

**Goal:** arrive at kickoff with one selected real workflow, documented rules, real-user access, a complete test/evidence plan, clear ownership, and zero ambiguity—while keeping core competition code for the sprint.

> **Rule boundary:** The competition says core development must happen in the sprint and disallows projects substantially developed before kickoff. This roadmap prepares decisions, people, data design, tests, accounts, and task management. Create the competition code repository at kickoff; do not privately prebuild the core app or move practice code into it.

---

## 0. Leader setup — first 2 hours

### Create the team operating space

| Tool | Set up now | Why |
|---|---|---|
| Group chat (Discord/Zalo/Slack) | `#announcements`, `#daily-standup`, `#help-blockers`, `#research` | Fast decisions and visible blockers |
| Notion / Google Drive | Shared documentation folder using the structure below | One source of truth |
| GitHub | Confirm every member account, add team members to an organization, create a **GitHub Project board** | Ready for sprint without starting competition code |
| Calendar | Daily 15-min standup, evening demo/review, kickoff block | Makes availability explicit |
| FigJam / Excalidraw | One workflow-map board | Collaborate on process, not code |
| Accounts checklist | Vercel, Supabase, LLM provider, screen recorder | Remove access blockers; do not build the core product yet |

### Create the task board

Columns:

```text
Inbox → Ready → In progress → Blocked → Review/demo → Done
                       ↘ Parking lot / cut list
```

Every task must have:

```text
Title
Single owner
Deadline
Expected artifact/link
Definition of done / acceptance test
Dependency or blocker
Rubric label: Operational / Verify / New input / Users / Audit / Challenge A
```

**Example task**

> `POL-03 — Write reimbursement policy v0.1`
> Owner: Linh · Due: Tuesday 18:00
> Output: `02_policy.md`
> Done when: rule owner can verify required fields, eligible categories, amount limits, exceptions, and escalation owners.
> Dependency: user interview #1
> Rubric: Challenge A, new judge input, audit.

---

## 1. Team alignment meeting — 75 minutes, Day 1

Do this before researching tools or writing code.

| Time | Activity | Output |
|---:|---|---|
| 0–10 min | Read `docs/eng_rules.md`; highlight 100-point rubric and 8-minute judge path. | Shared success definition |
| 10–25 min | Everyone proposes one workflow they can access. | 2–4 candidate workflows |
| 25–40 min | Score candidates using the selection matrix. | One chosen candidate or a 24-hour research action |
| 40–50 min | Write the one-sentence product promise. | Scope statement |
| 50–60 min | Agree what not to build. | Cut list |
| 60–70 min | Assign prep-week outcomes. | Board with owners/deadlines |
| 70–75 min | Confirm next standup and decision-log owner. | Operating agreement |

### One-sentence scope template

> For **[requester/handler]**, when **[routine request]** arrives, the system reads the request, applies **[policy version]**, automatically completes **[clear normal cases]**, and escalates **[missing fact / outside policy / authority]** to **[named human role]** with a specific question; every action is auditable and reversible.

### Candidate selection matrix

Score 1–5. Do not choose a candidate that scores below 4 on Access, Rules, or Judge resilience.

| Criterion | Weight | Candidate A: reimbursement | Candidate B | Candidate C |
|---|---:|---:|---:|---:|
| Access to 3 real people/roles | 5 |  |  |  |
| Clear, compact rules | 5 |  |  |  |
| Easy synthetic/consented data | 4 |  |  |  |
| New judge inputs can be handled | 5 |  |  |  |
| Natural escalation boundary | 5 |  |  |  |
| Can be explained in 30 seconds | 3 |  |  |  |
| Technical feasibility in 72h | 4 |  |  |  |
| **Weighted total** |  |  |  |  |

**Default recommendation:** Challenge A + student-club reimbursement, unless your team has stronger access to a different real workflow.

---

## 2. Documents to prepare before kickoff

Put these in the shared documentation workspace, not the competition source repository.

| File | Owner | What it must answer |
|---|---|---|
| `01_problem_brief.md` | Lead | Who has the problem? What is the current manual workflow and harm? |
| `02_workflow_candidates.md` | Lead + all | Why did we choose this workflow over alternatives? |
| `03_policy_v0.1.md` | Lead + rule owner | Required facts, rules, thresholds, authority, exceptions, policy version |
| `04_user_research.md` | Lead | Named roles, consent, interview notes, exact quotes; no fabrication |
| `05_case_matrix.csv` | QA/data | 15+ synthetic cases, expected decision, rule IDs, escalation question |
| `06_solution_blueprint.md` | Decision + UX engineers | Screens, architecture, event/audit fields, API/data contracts |
| `07_evidence_matrix.md` | Lead | Each rubric item → proof → owner → status |
| `08_measurement_plan.md` | Lead + QA | Pre/post measures, protocol, limitations, expected negative effects |
| `09_risk_cut_log.md` | Lead | Risks, deliberate cuts, mitigation, decisions |
| `10_sprint_backlog.md` | All | Build tasks ordered by dependency and score leverage |
| `11_runbook_draft.md` | Experience/QA | Planned clean-machine setup/deploy/check instructions |
| `12_demo_script.md` | Lead + UX | Exact 8-minute judge path and 3-minute video path |

### Most important document: evidence matrix

| Score area | Proof required | Owner | Status |
|---|---|---|---|
| Live URL — 10 | Public, no-login URL; landing instruction; incognito test | UX/deployment | Not started |
| Verify — 12 | One click, timestamped expected/actual/PASS table | QA | Not started |
| New input — 8 | Generic input path + edge-case behavior | Decision engineer | Not started |
| Real users — 20 | Roles, consent, quotes, feedback change, adverse effect | Lead | Recruiting |
| Human/audit — 20 | Decision flow, audit evidence, approve/undo/stop, explanation | UX + decision | Not started |
| Challenge A — 20 | 3 auto + 2 escalation fixture proof | QA + decision | Drafting |

---

## 3. Seven-day preparation roadmap

| Day | Leader focus | Team tasks | End-of-day gate |
|---|---|---|---|
| **Day 1 — Align** | Run the 75-minute meeting; create workspace/board; schedule user conversations. | Everyone proposes workflows; research access and policies. | Candidate shortlist, board, meeting cadence, user contacts. |
| **Day 2 — Choose** | Run selection matrix; make the scope decision; record cut list. | Decision engineer maps rules; UX maps current workflow; QA identifies data needs. | One workflow, one-sentence promise, named rule owner. |
| **Day 3 — Learn reality** | Interview at least requester + approver; obtain consent/data rules. | QA starts synthetic case matrix; UX documents current pain/exception path. | Policy v0.1, workflow map, 15-case outline. |
| **Day 4 — Design proof** | Lead evidence-matrix review. | Decision: escalation table; UX: audit/review/undo sketches; QA: Verify expected table. | Every score row has an intended proof and owner. |
| **Day 5 — Plan build** | Turn artifacts into small sprint tasks and sequence dependencies. | Team agrees field schema, data contracts, deployment/services checklist. | Sprint backlog with acceptance criteria; no implementation ambiguity. |
| **Day 6 — Attack risks** | Run a tabletop judge test: give the team two unseen cases. | QA adds boundary/adversarial cases; everyone lists failures and cuts. | Risk/cut log; revised policy/questions; fallback plan. |
| **Day 7 — Launch rehearsal** | Confirm availability, accounts, role handoffs, kickoff plan. | Dry-run documentation and 8-minute judge story; check all links/accounts. | Kickoff launch kit is complete. |

---

## 4. What each teammate owns

### Four-person team

| Role | Pre-sprint responsibility | Sprint responsibility |
|---|---|---|
| **Lead / product (you)** | Users, policy decisions, ethics/consent, scope, evidence, backlog | Integration, score protection, user evidence, slides, final go/no-go decisions |
| **Decision engineer** | Field schema, policy decision table, typed outcomes/escalations | Validation, policy engine, decision explanations, new-input handling |
| **Experience/deployment engineer** | Workflow map, screen sketches, audit/undo/stop interaction, account readiness | UI, audit timeline, public deployment, landing instructions, demo capture |
| **QA/data engineer** | Case corpus, Verify spec, edge cases, evaluation protocol | Regression tests, Verify harness, fresh-device test, runbook, rehearsal |

### Three-person team

- **Lead/product:** users, policy, evidence, integration, slides.
- **Decision engineer:** policy logic, validation, cases.
- **Experience/QA engineer:** UI, deployment, Verify, audit interactions, runbook.

### Rule for assigning work

Assign **independent outcomes**, not overlapping endpoints. One person owns the policy decision path, another owns judge experience/deployment, another owns quality/evidence. Each person presents an artifact daily.

---

## 5. Task-management rules

1. **One accountable owner per task.** Helpers are listed, but ownership is never shared.
2. **No task enters “In progress” without definition of done.**
3. **No silent blocker lasts more than 30 minutes.** Post it in `#help-blockers`.
4. **Daily review uses demos/documents, not percentage updates.**
5. **Every new idea goes to Parking lot first.** Promote it only if it improves a rubric row or prevents a serious failure.
6. **Leader maintains the cut list.** Cut features before cutting reliability, Verify, auditability, or documentation.
7. **Decision log resolves repeat debates.** Every scope decision includes date, owner, rationale, and consequence.
8. **During Sprint 1, integrate a thin end-to-end flow early.** Do not let separate features mature in isolation.

### Definition-of-done examples

| Task | Done means |
|---|---|
| Policy evaluator | All 15 labeled cases produce expected outcome; uncertainty never returns a definitive result. |
| Verify | Button runs the same production decision path for the five fixtures and prints timestamp, expected, actual, question, PASS/FAIL. |
| Audit | A random action can be reconstructed: input, rule/policy version, decision, actor, timestamp, reason, and undo relation. |
| Landing page | Incognito visitor understands exactly what to try first and needs no account. |

---

## 6. GitHub setup without violating the preparation boundary

### Before kickoff

- Verify everyone has a GitHub account and two-factor recovery method.
- Create an organization/team and a GitHub Project board.
- Agree on branch naming: `feat/...`, `fix/...`, `docs/...`.
- Agree that the main branch is protected and reviewed before merge.
- Choose issue templates and a pull-request checklist.
- Identify any publicly available starter scaffold and record its URL/license for README disclosure.
- Do **not** put a substantial private implementation, copied practice app, test suite, or project commit history in the competition repo.

### At kickoff

1. Create the public competition repository.
2. Add README disclosure for any allowed public scaffold.
3. Make the initial truthful commit.
4. Create issues from `10_sprint_backlog.md`.
5. Commit in small, understandable increments; never force-push or squash the required history.

---

## 7. Your first message to the team

> We are going to prepare one real, testable workflow before kickoff. This week we will not compete on the most complicated AI. We will recruit real users, write clear rules, design unseen test cases, define human controls, and remove account/access blockers. At kickoff, we build a fresh, small, working system that judges can understand and test in eight minutes. Every task has one owner, a concrete output, and a deadline.

---

## 8. First 24-hour checklist for you

- [ ] Create group chat, shared workspace, task board, calendar invites.
- [ ] Share `docs/eng_rules.md`, `docs/mvp_blueprint.md`, and this roadmap.
- [ ] Schedule the 75-minute alignment meeting.
- [ ] Ask each teammate for one accessible workflow candidate before the meeting.
- [ ] Contact at least two potential rule owners/users.
- [ ] Create selection matrix and evidence matrix.
- [ ] Ask organizers to clarify the Sprint 1/Sprint 2 timing conflict regarding real-user evidence and feedback changes.
- [ ] End Day 1 with a written decision and tomorrow’s concrete outputs.
