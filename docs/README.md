# Documentation Index

## Current status

The participating club's real manual reimbursement workflow is **not yet validated**.

Until it is, the project uses an explicitly synthetic temporary development workflow to build backend mechanics. Temporary documents are not a club policy, financial procedure, user-research finding, or public-demo evidence.

## Read in this order

1. [00_challenge_a_rubric.md](00_challenge_a_rubric.md) — challenge/scoring reference.
2. [06_git_collaboration_playbook.md](06_git_collaboration_playbook.md) — required before any branch, commit, or pull request.
3. Temporary development chain below — the only current source for temporary backend behavior.

## Temporary development chain

| Order | Document | Purpose | Status |
| --- | --- | --- | --- |
| 1 | [01_temporary_manual_workflow.md](01_temporary_manual_workflow.md) | Synthetic end-to-end workflow for `TMP-DEV-001`; not a description of the club's manual process. | Temporary |
| 2 | [02_MVP_Spec.md](02_MVP_Spec.md) | Empty placeholder for the future MVP definition after workflow validation. | Placeholder |
| 3 | [03_temporary_demo_policy.md](03_temporary_demo_policy.md) | Explicit synthetic decision rules for `TMP-DEV-001`; not a pilot policy. | Temporary |
| 4 | [04_temporary_system_contract.md](04_temporary_system_contract.md) | Frozen temporary vocabulary, record shapes, profile, and deferred evaluation boundary; not a future public API. | Temporary |
| 5 | [05_temporary_case_corpus.csv](05_temporary_case_corpus.csv) | Six planned synthetic fixtures covering every temporary outcome and the inclusive authority boundary. | Temporary |

## Retired legacy documents

The former product specification, proposed policy, contract, corpus, research plan, evidence map, runbook, logs, storyboard, roles, and preparation roadmap are preserved in [retired/](retired/). They are historical material only and must not be treated as the current source of truth.

## Documentation rules

- Follow [06_git_collaboration_playbook.md](06_git_collaboration_playbook.md) for every branch, commit, and pull request.
- Use the temporary development chain only to implement/test synthetic backend behavior.
- Mark every temporary record, result, and business-operation UI/API response with its synthetic/unvalidated provenance. The operational `/health` readiness response is exempt and retains its minimal status/database contract.
- Do not copy `TEST_ALLOWED`, `TEST_BLOCKED`, or `1000` into a real club policy.
- Do not place real personal, financial, receipt, vendor, or bank data in committed artifacts.
- When a teammate validates the real workflow, replace the temporary chain in a controlled migration: manual workflow → MVP specification → pilot policy → system contract → case corpus.
