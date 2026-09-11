# Evidence Map

## Document control

**Status:** Proposed provisional baseline. This map records the Policy Forge documentation foundation only; it is not final competition evidence.

**Owner:** Project lead.

**Reviewer:** QA owner.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `Not started` | No artifact or proof exists yet. |
| `Proposed` | A provisional documented contract exists; not yet implemented or validated. |
| `Blocked by policy-owner confirmation` | Cannot proceed truthfully until a policy owner confirms values (e.g. numeric limits). |
| `Draft` | An early artifact exists but is not complete or validated. |

## Rubric-to-proof matrix

| Rubric area | Required proof | Planned artifact or location | Owner | Status |
| --- | --- | --- | --- | --- |
| Live URL | Public no-login route and fresh-device check | [08_demo_runbook.md](08_demo_runbook.md) (later) | Backend owner | Not started |
| One-click Verify | Timestamped expected versus actual PASS or FAIL table | [08_demo_runbook.md](08_demo_runbook.md); future public five in [04_case_corpus.csv](04_case_corpus.csv) | QA owner | Blocked by policy-owner confirmation (needs thresholds and 15+ corpus) |
| New judge input | Generic input path and held-out safety checks | [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md); [07_system_contract.md](07_system_contract.md) | Backend owner and QA owner | Proposed (shared vocabulary defined; not implemented) |
| Slides and video | Five required slides and a three-minute or shorter video | [11_demo_storyboard.md](11_demo_storyboard.md) (later) | Project lead | Not started |
| Real users and organization | Roles, consent, quotes, feedback change, and adverse effect | [05_user_research_plan.md](05_user_research_plan.md) (later) | Policy & scenario owner | Not started (no real users claimed in this baseline) |
| Human control and audit | Trace, approve, reject, undo, pause, and explanation proof | [07_system_contract.md](07_system_contract.md) | Backend owner | Proposed (audit/control contract defined; not implemented) |
| Challenge A verification | Three routine cases and two escalation cases | [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md); [04_case_corpus.csv](04_case_corpus.csv) | Policy & scenario owner and QA owner | Proposed (provisional seed of 8 synthetic cases; below the 15+ requirement) |

## Evidence review log

| Date | Requirement reviewed | Evidence gap | Decision | Owner |
| --- | --- | --- | --- | --- |
| Not yet confirmed (provisional baseline) | Policy coverage, new-input safety, future Verify, and future audit/control evidence | Numeric thresholds unset; seed corpus is 8 synthetic cases, not 15+; no real-user or implementation evidence | Record the provisional baseline as truthfully `Proposed` or `Blocked`; defer implementation until the handoff gate is met | Project lead |