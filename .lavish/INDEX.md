# Lavish Research Index

Catalog for the local review inbox in `.lavish/`. This folder is **not the source of truth** — that is `docs/`. Lavish artifacts exist to help reach a decision; once a decision is made, its durable conclusion is promoted into `docs/` and the HTML is retired here.

## Status legend

| Status | Meaning |
| --- | --- |
| **Active** | Still a live working document; a decision is still open. |
| **Promoted → docs** | Conclusion moved into `docs/`; HTML retired to `retired/`. |
| **Retired** | Superseded, absorbed, or archived as evidence; moved to `retired/`. |

## Reading in the right order

Skip hunting by filename. `docs/README.md` is the entry point. The durable decisions now live there:

- `docs/07_system_overview.md` — what we are (and aren't) building.
- `docs/decisions/0001-backend-stack.md` — why the Python/FastAPI stack, and its hard boundaries.
- `docs/01..05` — the temporary development chain (current behavior source).

## Active

| File | Date | What it is | Supersedes / note |
| --- | --- | --- | --- |
| `judge-screen-plan.html` | 2026-09-11 | Spec for the judge's 8-minute demo path: the 5 screens and screen→rubric map. | Still open — the demo surface is not yet resolved in `docs/`. |
| `phan-vai-ranh-gioi-nhom.html` | 2026-09-10 | Team role boundaries and artifact-based handoffs (Vietnamese). | Operating agreement; still the team's current split. |

## Promoted → docs (retired here)

| File | Date | Promoted to |
| --- | --- | --- |
| `retired/techstack-layer-research.html` | 2026-09-10 | `docs/decisions/0001-backend-stack.md` (stack decision + rationale) |
| `retired/python-backend-blueprint.html` | 2026-09-11 | `docs/decisions/0001-backend-stack.md`; module map → `docs/07_system_overview.md` |
| `retired/what-you-are-building-manual-to-automated.html` | 2026-09-11 | `docs/07_system_overview.md` (product orientation) |

## Retired (superseded / absorbed / evidence)

| File | Date | Why retired |
| --- | --- | --- |
| `retired/temporary-backend-workflow-design.html` | 2026-09-11 | Its "temporary contract v0.1" decision is now `docs/01..05`. |
| `retired/reimbursement-workflow-drift-decision-report.html` | 2026-09-11 | Decision made (temporary contract); superseded by the docs temporary chain. |
| `retired/vietnam-reimbursement-reality-check.html` | 2026-09-11 | Local-practice evidence; conclusions absorbed into the drift report. Keep as evidence. |
| `retired/policy-forge-implementation-plan.html` | 2026-09-11 | Became `docs/03_temporary_demo_policy.md` + `docs/04_temporary_system_contract.md`. |
| `retired/backend-decide-before-code.html` | 2026-09-10 | All six decisions were made downstream; superseded by blueprint + ADR. |
| `retired/backend-architecture-strategy.html` | 2026-09-10 | Early backend blueprint; superseded by the Python blueprint. |
| `retired/industry-research-escalation-referee.html` | 2026-09-10 | Durable "rules route, humans resolve" pattern carried into the ADR; keep as evidence. |
| `retired/team-onboarding-overview.html` | 2026-09-10 | Absorbed into `docs/07_system_overview.md` and `docs/README.md`. |
| `retired/challenge-a-vietnam-workflow-strategy.html` | 2026-09-10 | Superseded by reality-check → drift report → temporary chain. |

## Maintenance rules

1. **Drain the inbox on every decision.** When a Lavish review ends, either (a) promote the conclusion to `docs/`, or (b) retire it. Do not leave a resolved artifact unlabeled in the active list.
2. **Supersede, don't silently delete.** Every retired file keeps a pointer here to what replaced it.
3. **Re-verify on `docs/` change.** When a `docs/` file changes, re-check the artifacts that claim to feed it and update their status.
4. **Commit only this index.** The HTML stays local (git-ignored); the catalog and `docs/` are the shareable truth.