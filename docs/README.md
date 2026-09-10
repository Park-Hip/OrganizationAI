# Documentation Index

## Purpose

This directory contains the committed project documentation for the OrganizationAI 2026 Challenge A submission.

Use this page as the single navigation and artifact-status source.

The project specification defines the product.

The rubric defines what must be proven.

The remaining documents provide the evidence, contracts, and operating instructions needed to implement and demonstrate the project.

## Reading order

0. Read the Git collaboration playbook to learn how we branch, commit, and open pull requests.
1. Read the challenge rubric to understand the score and compliance requirements.
2. Read the project specification to understand the selected workflow and product boundary.
3. Validate the workflow charter and pilot policy with real policy owners.
4. Use the case corpus and system contract to implement one consistent decision path.
5. Maintain the evidence map, research plan, risk log, build log, and runbook throughout the sprint.
6. Rehearse the final experience using the demo storyboard and runbook.

## Document map

| Document | Status | Purpose | Primary owner |
| --- | --- | --- | --- |
| [00_challenge_a_rubric.md](00_challenge_a_rubric.md) | Existing draft | Scoring contract, compliance gates, and proof requirements. | Project lead |
| [01_project_spec.md](01_project_spec.md) | Draft v0.1 | Canonical workflow, product scope, requirements, and decision boundary. | Project lead |
| [12_git_collaboration_playbook.md](12_git_collaboration_playbook.md) | Active | Member workflow plus enforced `main` protection and maintainer-only emergency bypass. | Every contributor |
| [02_workflow_charter.md](02_workflow_charter.md) | Skeleton | Validated real workflow, participant roles, scope, exclusions, and sign-off state. | Project lead |
| [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md) | Skeleton | Versioned reimbursement rules, authority limits, and escalation owners. | Treasurer and president |
| [04_case_corpus.csv](04_case_corpus.csv) | Skeleton | Labeled cases for policy tests, public Verify, and held-out robustness checks. | QA and policy owner |
| [05_user_research_plan.md](05_user_research_plan.md) | Skeleton | Consent, interview protocol, measures, and adverse-effect research. | Project lead |
| [06_evidence_map.md](06_evidence_map.md) | Skeleton | Rubric-to-proof matrix with evidence location, owner, and status. | Project lead |
| [07_system_contract.md](07_system_contract.md) | Skeleton | Shared request, decision, audit, state, and control contracts. | Decision engineer |
| [08_demo_runbook.md](08_demo_runbook.md) | Skeleton | Setup, deployment, Verify, recovery, and fresh-device checks. | Platform and QA |
| [09_build_log.md](09_build_log.md) | Skeleton | Build disclosures, AI-tool use, decisions, and feature cuts. | Project lead |
| [10_measurement_and_risk_log.md](10_measurement_and_risk_log.md) | Skeleton | Measurement plan, limitations, risks, mitigations, and decision record. | Project lead and QA |
| [11_demo_storyboard.md](11_demo_storyboard.md) | Skeleton | Eight-minute judge journey, required slides, and video script. | Project lead and UI/UX |

## Documentation rules

- Follow [12_git_collaboration_playbook.md](12_git_collaboration_playbook.md) for every branch, commit, and pull request.
- Keep one source of truth for each topic in the document map above.
- Link to the source document instead of copying policy rules, scope statements, or proof tables into another document.
- Mark every unvalidated statement as proposed, synthetic, observed, or pending validation.
- Do not place real personal, financial, receipt, or vendor data in committed artifacts without written permission.
- Update the evidence map when a requirement gains or loses proof.
- Record material product decisions and feature cuts in the build log or risk log.
- Keep local operating notes out of version control.

## Local-only material

`01_leader_setup_phase_roadmap.md` is intentionally ignored and remains a local operating document.

It must not be added to commits.

## Documentation-phase completion check

- The workflow charter identifies the policy owners and validation status.
- The pilot policy has rule IDs, required facts, authority boundaries, and escalation owners.
- The case corpus contains the public Verify cases and at least 15 labeled cases overall.
- The system contract supports the same semantics in the UI, evaluator, audit trail, and Verify flow.
- The evidence map assigns proof for every rubric criterion.
- The runbook and storyboard can support a fresh-device demonstration.
