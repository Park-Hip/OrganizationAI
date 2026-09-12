# OrganizationalAI - Challenge A

This repository tracks the MLAI Hackathon 2026 submission for Challenge A, The Escalation Referee.

The current backend-development scenario is a synthetic campus student-club expense reimbursement referee. The participating club’s real manual workflow and pilot policy are pending validation.

The temporary evaluator is specified only for synthetic routine cases under the explicitly temporary `TMP-DEV-001` profile and for safely escalating incomplete, out-of-policy, or authority-exceeding synthetic cases.

## Pre-Sprint Status

This repository contains the temporary backend-development documentation, legacy planning material, and GitHub workflow templates.

The temporary profile must be replaced before any real-workflow or policy claim is made.

## Documentation

Start with [docs/README.md](docs/README.md) for the documentation map, ownership, and artifact status.

Read [docs/06_git_collaboration_playbook.md](docs/06_git_collaboration_playbook.md) before your first commit.

It defines our branch, commit, and pull-request rules.

## Backend development (temporary)

The backend foundation lives in [backend/](backend/) and is temporary, synthetic, and unvalidated.
Read [backend/README.md](backend/README.md) for clean-clone prerequisites, setup, and quality commands.
The durable L0 contract baseline in [docs/07_l0_contract_baseline.md](docs/07_l0_contract_baseline.md) maps the current temporary documents to implementation boundaries without superseding them.
The backend does not yet evaluate policy, persist cases, expose a public product API, or make any real workflow claim.
Its operational `/health` readiness endpoint is intentionally limited to process and database status.

## Sprint Integrity

The team will preserve a public, truthful commit history throughout the sprint.

Public fixtures will be synthetic unless written permission explicitly allows real data.

No real payments, bank transfers, or irreversible integrations are in scope for the prototype.
