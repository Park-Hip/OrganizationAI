# AGENTS.md

## Project

OrganizationalAI 2026 submission for Challenge A: The Escalation Referee.

The product and service name is `OrganizationalAI`.

Read `docs/README.md` first. Treat the documents it links as the source of truth.

## Documentation discipline

- Use `.local/` for personal, exploratory, or temporary plans. Do not treat its contents as shared project requirements, and do not commit them.
- GitHub Issues and the GitHub Project hold shared task scope, ownership, acceptance criteria, and status.
- Files named `docs/NN_*.md` are durable base documentation. Add, renumber, replace, or substantially restructure a numbered document only after explicit team consideration; do not use numbered documents for drafts or short-lived plans.

## Pull-request clarity

Pull-request descriptions must be understandable to an external reader with no prior knowledge of the project. Avoid internal vocabulary (e.g., L0, L1, profile, provenance) unless you define it on first use in plain language. Do not rely on the reader having access to private `.local/` files or prior chat history.

- Use every section of `.github/pull_request_template.md`; do not replace its headings with tool-generated headings.
- Start with a plain-language Summary and Context: state the problem, why the change is needed now, and the outcome it enables.
- Define or link project-specific terms on first use, including Layer 0, profile, provenance, and temporary-policy identifiers.
- List the key changed file paths or path groups and explain why each changed.
- Link the governing GitHub **Issue** (not another PR) and use `Closes #<issue-number>` so the issue is auto-closed when the PR merges.

## Git

When using Git, follow `docs/06_git_collaboration_playbook.md`.
