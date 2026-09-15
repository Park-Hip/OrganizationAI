# Documentation Index

## Current status

The project has adopted [the reimbursement workflow baseline](01_manual_reimbursement_workflow.md) derived from Policy Forge v1.1. It defines the workflow to be implemented next; it is not evidence that a real case may be processed yet.

The current backend still contains legacy synthetic `TMP-DEV-001` behavior while the workflow, MVP, policy, system contract, and corpus transition into implementation. The former temporary source documents have been removed from the working documentation; Git history retains them. Temporary records and endpoints remain synthetic historical material and are not a club policy, financial procedure, user-research finding, or public-demo evidence.

## Read in this order

1. [00_challenge_a_rubric.md](00_challenge_a_rubric.md) — challenge/scoring reference.
2. [06_git_collaboration_playbook.md](06_git_collaboration_playbook.md) — required before any branch, commit, or pull request.
3. [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md) — the project-approved workflow baseline and its real-operation gate.
4. Implementation-transition chain below — the source for current behavior and the ordered replacement work.

## Implementation transition chain

| Order | Document | Purpose | Status |
| --- | --- | --- | --- |
| 1 | [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md) | Project-approved reimbursement workflow baseline derived from Policy Forge v1.1. Real-operation activation remains conditional on its checklist. | Current workflow baseline |
| 2 | [02_MVP_Spec.md](02_MVP_Spec.md) | MVP scope for a deterministic reimbursement packet, structured escalation, human approval boundary, and audit history. | Adopted (synthetic pilot) |
| 3 | [03_reimbursement_policy.md](03_reimbursement_policy.md) | Project-approved Policy Forge v1.1 baseline: versioned profile, deterministic rules, structured escalation, human-approval boundary, and audit controls. | Current policy baseline |
| 4 | [04_reimbursement_system_contract.md](04_reimbursement_system_contract.md) | Contract for the versioned reimbursement case, organization profile, deterministic processing, escalation, audit, authorization, and `TMP-DEV-001` migration boundary. | Adopted (synthetic pilot) |
| 5 | [05_reimbursement_case_corpus.md](05_reimbursement_case_corpus.md) | Manifest for the 16 Policy Forge synthetic cases and five-case Verify suite. | Adopted (synthetic pilot) |

## Legacy temporary implementation

The current backend still contains legacy synthetic `TMP-DEV-001` behavior. Its temporary workflow, policy, system contract, and corpus were removed from the working documentation during this transition and remain retrievable from Git history. That legacy behavior is not the current reimbursement-policy baseline and must not be extended as though it were one.

Stored `TMP-DEV-001` records and endpoints remain synthetic historical material. They never claim a real human authority, authentication, or a payment side effect.

## Retired legacy documents

The former product specification, proposed policy, contract, corpus, research plan, evidence map, runbook, logs, storyboard, roles, and preparation roadmap are preserved in [retired/](retired/). They are historical material only and must not be treated as the current source of truth.

## Architecture

- [07_architecture.md](07_architecture.md) — system context, layer boundaries, data-flow diagrams, and the append-only persistence schema.

## Architectural Decision Records

- [ADRs/README.md](ADRs/README.md) — index of all ADRs with templates for adding new ones.

## Documentation rules

- Follow [06_git_collaboration_playbook.md](06_git_collaboration_playbook.md) for every branch, commit, and pull request.
- Do not extend legacy `TMP-DEV-001` behavior as though it were the reimbursement-policy baseline; preserve it only as synthetic historical material until its endpoints are retired.
- Mark every temporary record, result, and business-operation UI/API response with its synthetic/unvalidated provenance. The operational `/health` readiness response is exempt and retains its minimal status/database contract.
- Do not copy `TEST_ALLOWED`, `TEST_BLOCKED`, or `1000` into a real club policy.
- Do not place real personal, financial, receipt, vendor, or bank data in committed artifacts.
- Complete the controlled migration in this order: manual workflow → MVP specification → pilot policy → system contract → case corpus. Revise implementation, tests, API wording, and UI together only after those documents are aligned.
