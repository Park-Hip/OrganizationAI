# OrganizationalAI - Challenge A

This repository tracks the MLAI Hackathon 2026 submission for Challenge A, The Escalation Referee.

OrganizationalAI's Sprint 1 product is a **synthetic, AI-led reimbursement case-preparation demo**. One AI agent guides intake and prepares clear review packets; a deterministic, versioned policy engine controls classifications and escalates uncertainty to a human. Every agent result remains pending human approval.

The project uses only synthetic data in Sprint 1. It does not accept real reimbursement cases, approve or reject a case automatically, transfer money, or claim production readiness. Read [ADR-012](docs/ADRs/012_single-agent-sprint-1-pilot.md) for the agent boundary and deferred controls.

## Current implementation status

The runnable backend remains the explicitly temporary `TMP-DEV-001` implementation. It is historical synthetic development material, not the Sprint 1 reimbursement path, and must not be extended or relabelled as a club policy. The adopted reimbursement-v1 policy, contract, corpus, and architecture define the replacement path.

## Documentation

Start with [docs/README.md](docs/README.md) for the documentation map, ownership, and artifact status.

Read [docs/06_git_collaboration_playbook.md](docs/06_git_collaboration_playbook.md) before your first commit.

It defines our branch, commit, and pull-request rules.

## Backend development

The backend lives in [backend/](backend/). Its currently wired endpoints are temporary, synthetic, and unvalidated; they are retained only as historical material. The reimbursement-v1 deterministic evaluator is implemented. Separate immutable audit history, followed by a bounded single-agent adapter and public synthetic Verify surface, remains next.

Read [backend/README.md](backend/README.md) for clean-clone prerequisites, quality commands, and the legacy/v1 boundary. Its operational `/health` readiness endpoint is intentionally limited to process and database status.

## Sprint Integrity

The team will preserve a public, truthful commit history throughout the sprint.

Public fixtures will be synthetic unless written permission explicitly allows real data.

No real payments, bank transfers, or irreversible integrations are in scope for the prototype.
