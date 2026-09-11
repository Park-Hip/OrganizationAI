# Git Collaboration Playbook

Follow this guide for every contribution to the project.

## 1. Start one task on one branch

Start from an assigned, rubric-mapped issue with clear acceptance criteria.

Do not begin work that overlaps another member's active task without agreeing who owns each file or outcome.

Before creating a branch, confirm that your working tree does not contain changes you do not own.

```powershell
git status
git switch main
git pull --ff-only origin main
git switch -c feat/short-task-name
```

Replace sample branch names and angle-bracket placeholders with the values for your task.

Use one of these branch prefixes.

| Prefix | Use for | Example |
| --- | --- | --- |
| `feat/` | New product capability | `feat/policy-evaluator` |
| `fix/` | Bug fix | `fix/audit-event-order` |
| `docs/` | Documentation only | `docs/user-research-plan` |
| `test/` | Tests or test fixtures | `test/verify-boundaries` |
| `chore/` | Tooling, configuration, or CI | `chore/ci-checks` |

Use lowercase words separated by hyphens.

## 2. Make a focused change

Keep each branch and pull request focused on one outcome.

Use the written policy, system contract, and acceptance criteria as the source of truth.

Do not add secrets, API keys, personal data, real receipts, or real vendor information.

Run the relevant tests or checks before requesting review.

If your change affects policy behavior, audit events, approval, rejection, pause, undo, or Verify cases, update the related documentation and tests in the same pull request.

## 3. Commit safely

Review the exact files before each commit.

```powershell
git status
git add <file-or-directory>
git diff --cached
git commit -m "<type>(<scope>): <short imperative description>"
git push -u origin feat/short-task-name
```

Do not use `git add .` unless you have checked every changed file and confirmed that all belong in the commit.

Use a conventional commit type such as `feat`, `fix`, `docs`, `test`, `refactor`, or `chore`.

Examples:

```text
feat(policy): classify missing receipt amounts
fix(audit): preserve prior event on undo
docs(runbook): add fresh-device verification
test(verify): add authority-limit boundary case
```

Make small commits that describe one logical change.

Do not amend, rebase, reset, squash, or force-push published competition history.

## 4. Open a pull request

Open a pull request from your branch to `main` after pushing your work.

Link the task issue with `Closes #<issue-number>`.

Use a draft pull request when you need early feedback on the approach.

Complete every section in the [pull request template](../.github/pull_request_template.md).

The pull request must state:

- What changed and why.
- Which rubric area it supports.
- Whether policy or audit behavior changed.
- How the change was verified.
- Where the supporting evidence is stored.

Request a teammate review before merging.

## 5. Review and merge

Reviewers check that the change meets its acceptance criteria, matches the written policy, preserves auditability, and has appropriate verification evidence.

The author addresses review feedback and reruns affected checks.

Merge only when the pull request is approved and all required checks pass.

Use a regular merge commit.

Do not squash merge or rebase merge because the sprint requires a truthful, auditable commit history.

Do not merge your own pull request without another teammate's review.

Delete the branch after its pull request is merged.

## 6. Main-branch enforcement and emergency bypass

GitHub must enforce these rules for `main` through an active branch ruleset.

- Require a pull request before merging.
- Require one approving review.
- Dismiss an approval when new commits are pushed.
- Require approval of the most recent push.
- Require all review conversations to be resolved.
- Add required status checks to this ruleset as soon as the first CI workflow exists.
- Block force pushes and branch deletion.

The repository maintainer is the only account allowed to bypass this ruleset.

The bypass is only for an actual production, security, or competition-blocking emergency when the normal review path cannot be used in time.

Before using the bypass, notify the team when practical and use the normal pull-request flow if time allows.

After using the bypass, create an issue or pull request that records the reason, affected files, verification, and rollback plan.

Request a teammate's retrospective review of the bypassed change by the next working day.

Contributors must never ask for or use bypass access.

## 7. Keep your branch current

Before merging, incorporate the latest `main` branch into your feature branch.

```powershell
git switch feat/short-task-name
git fetch origin
git merge origin/main
git push
```

If Git reports a conflict, read both changes and keep the version that satisfies the current policy and acceptance criteria.

Remove all conflict markers before staging the resolved files.

```powershell
git status
git add <resolved-file>
git commit
git push
```

Ask the original author or reviewer when the correct resolution is unclear.

## 8. Non-negotiable safeguards

- Never commit directly to `main` unless the maintainer invokes the documented emergency bypass.
- Never force-push, squash, or rewrite published history.
- Never merge failing checks or known broken behavior.
- Never commit secrets, personal data, real receipts, or real vendor information.
- Never delete or overwrite a teammate's work to resolve a conflict.
- Never make an unsupported policy decision to unblock a feature.
- Stop and ask for help before using a destructive Git command or resolving an unclear conflict.

## 9. Recover from a local mistake

Use `git status` first.

To remove a file from the next commit while keeping its local edits, run:

```powershell
git restore --staged <file>
```

To discard an uncommitted edit only when you are certain it is unwanted, run:

```powershell
git restore <file>
```

If the change was already pushed or someone else may depend on it, do not rewrite history.

Ask the team for the safest next step.
