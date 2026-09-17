# OrganizationalAI backend (temporary)

This directory is the temporary backend development foundation: a frozen domain vocabulary, one temporary profile constant, a pure Layer 1 normalizer, a pure Layer 2 evaluator, and a temporary decision-history persistence layer.
The persistence layer stores immutable synthetic case/decision snapshots plus an append-only audit-event chain, and exposes a minimal submit-and-trace API under `/api/temporary/decision-traces`.
A narrow temporary Control Deck appends labelled synthetic control events (`DEMO_REVIEWER`) and derives a visible `control_state` through a pure reducer, without mutating the finished ledger.
Its operational `/health` readiness endpoint remains intentionally limited to process and database status.

Everything here serves the explicitly temporary `TMP-DEV-001` development profile.
No real reimbursement workflow, payment, or policy claim is implied.

> **Sprint 1 direction:** This runnable temporary backend is historical synthetic material, not the next product path. Sprint 1 implements a separate reimbursement-v1 path: deterministic policy evaluation and immutable audit history first, then a bounded single AI intake and packet-preparation agent. Do not add agent features, policy behavior, or new demo controls to `TMP-DEV-001`. See [ADR-012](../docs/ADRs/012_single-agent-sprint-1-pilot.md) and [the target architecture](../docs/07_architecture.md).

## Prerequisites

- Python 3.12 (pinned in `backend/.python-version`).
- uv, the package manager, from https://docs.astral.sh/uv/.
- Docker Desktop or an equivalent Docker and Compose environment.

## Setup from a clean clone

Run these commands from the `backend/` directory.

### 1. Configure local environment

Copy the example environment file, choose a local Docker password, and use the same URL-safe value in both `POSTGRES_PASSWORD` and `DATABASE_URL`.

```bash
cp .env.example .env
```

`.env` is git-ignored and must never contain real credentials.
Postgres refuses to initialize until `POSTGRES_PASSWORD` is set.

### 2. Install pinned dependencies

```bash
uv sync
```

This creates the virtual environment, installs runtime and development dependencies from the committed `uv.lock`, and installs the `app` package.

### 3. Start the local database

```bash
docker compose up -d db
```

Wait until the health check reports the container as healthy.

### 4. Apply the migration

Apply the single temporary decision-history revision, then confirm the reported head.

```bash
uv run alembic upgrade head
uv run alembic current
```

`alembic current` reports the applied revision and proves Alembic connects to Postgres with the configured URL.

### 5. Run the readiness service

With the database running, choose one local development option.

```bash
uv run uvicorn app.main:app --reload
```

Or build and run the Compose app service, which starts only when its `app` profile is selected.

```bash
docker compose --profile app up -d --build
```

Request `http://localhost:8000/health` to confirm the service reports its process and database status.

### 6. Run the full quality gate

```bash
./scripts/check.sh       # macOS or Linux
# or
.\scripts\check.ps1      # PowerShell on Windows
```

The gate runs, in order: format check, lint, type check, tests, and the environment smoke check.
It stops on the first failure and returns that exit code.

## Test groups and supported commands

Tests are grouped with pytest markers so a local run and CI can target one group at a time.
The markers are defined in `pyproject.toml`.

| Marker | Group | Command |
| --- | --- | --- |
| `unit` | Domain, API, application, and policy unit tests that need no database or service. | `uv run pytest -m unit` |
| `contract` | Layer 0 frozen-contract and layer-boundary tests. | `uv run pytest -m contract` |
| `legacy` | Historical synthetic `TMP-DEV-001` corpus and regression tests. | `uv run pytest -m legacy` |
| `v1_contract` | Reimbursement v1 source-contract validation tests. | `uv run pytest -m v1_contract` |
| `integration` | Postgres-backed service, migration, and immutability tests. | `uv run pytest -m integration` |

Run the whole non-database suite with one command:

```bash
uv run pytest -m "not integration"
```

This is the normal local loop and is the command the repository requires as its green baseline.
On Windows the same run is available directly from the created virtual environment:

```powershell
.venv\Scripts\python.exe -m pytest -m "not integration" -q
```

### Expected pass and skip behavior

The non-database baseline does not collect integration tests and is green when its selected tests pass.
`uv run pytest -m integration` skips with a message naming `TEST_DATABASE_URL` whenever the isolated test database is not configured.
They run, rather than skip, only after `test-db` is started and `TEST_DATABASE_URL` is exported.
A skip is reported clearly and is never presented as a pass.
The `v1_contract` command runs the reimbursement v1 source-contract and module-seam tests in `tests/contract/reimbursement_v1/`.
CI runs the same group by path, so missing v1 source-contract coverage fails explicitly.

### Failure triage

A `legacy` failure usually means the historical fixture under `tests/fixtures/legacy_tmp_dev_001/` no longer matches the frozen reader schema.
Check that the fixture still carries the `TMP-DEV-001`, `SYNTHETIC`, `TEMPORARY_DEVELOPMENT`, and `UNVALIDATED` provenance and has not been mixed with the `policy-forge-baseline` corpus.
When `TEST_DATABASE_URL` names an unreachable database, integration tests skip with a `temporary-history test database unavailable` message.
An integration error after the database is reachable can mean its schema is stale.
Recreate the synthetic-only database and rerun `uv run alembic upgrade head` against it.
Formatting, lint, and type failures are the first CI checks; reproduce them locally with `uv run ruff format --check .`, `uv run ruff check .`, and `uv run mypy app tests`.

### Continuous integration

The `.github/workflows/ci.yml` workflow runs six separately reported jobs on every pull request:
`quality` (format, lint, type), `test-legacy` (legacy regressions), `test-unit` (unit tests), `test-contract` (frozen contract tests), `v1-contract` (v1 source-contract validation), and `integration` (Postgres-backed tests against a synthetic-only database service).
These job names become the required status checks once the workflow is shown green on the setup branch.

## What this foundation proves

- A clean clone installs and configures from committed, locked dependencies.
- The typed settings object fails fast when `DATABASE_URL` is absent.
- The frozen domain vocabulary and sole profile construct and validate their structural rules.
- The Layer 1 normalizer converts whitespace-only decision-bearing text to canonical absence and exposes the canonical purpose and expense-field repair questions without any I/O.
- The Layer 2 evaluator returns a deterministic `DecisionDraft` from a normalized case and injected immutable profile without I/O, then applies missing-fact, category, evidence, authority, and automatic-approval precedence.
- The temporary decision-history layer writes one immutable trace (case snapshot, decision snapshot, three ordered `SYSTEM` events) in a single transaction and rejects update/delete through immutability triggers.
- The submit-and-trace API accepts only the frozen case shape, returns stored snapshots without reevaluating a past decision, and marks every business response as temporary, synthetic, and unvalidated.
- The temporary Control Deck appends exactly one labelled synthetic control event per command (`pause`, `resume`, `record_demo_review`, `undo`), derives `control_state` from the stored decision plus control events, and rejects illegal transitions and reused idempotency keys without changing the original snapshots.
- FastAPI metadata and startup logging resolve from typed runtime settings.
- Postgres starts through a reproducible Compose definition with a health check.
- Alembic applies the temporary decision-history revision reproducibly, with a clean downgrade.
- The health endpoint distinguishes a reachable database from an unreachable one without leaking credentials.

## Temporary provenance

Every later layer must keep these markers on persisted records and business-operation responses:

| Field | Value |
| --- | --- |
| `profile_id` | `TMP-DEV-001` |
| `profile_source` | `TEMPORARY_DEVELOPMENT` |
| `data_class` | `SYNTHETIC` |
| `workflow_validation_status` | `UNVALIDATED` |

Do not treat `TEST_ALLOWED`, `TEST_BLOCKED`, or `1000` as real club practice.
Every persisted temporary trace is marked through its immutable case snapshot and the immutable profile snapshot stored with its decision, and every business response under `/api/temporary/decision-traces` adds an explicit temporary, synthetic, unvalidated notice on top of the server-owned markers.
The operational `/health` readiness response is intentionally exempt and retains its minimal status/database contract.

## Layer 0 frozen contract

The backend freezes the smallest contract needed before normalization and pure policy evaluation:

- `app/domain` defines the frozen enums and record shapes (`Expense`, `CaseSubmission`, `NormalizedCase`, `TemporaryProfile`, and `DecisionDraft`).
- `app/policy/profile.py` exports exactly one immutable temporary profile, `TMP_DEV_001_PROFILE`, with provenance, `{TEST_ALLOWED}`, required evidence `PRESENT`, and an inclusive `1000` limit.
- `tests/contract/` proves the enum values, structural validation, deep immutability, decision-draft combinations, and the import boundary without starting FastAPI or a database.

The Layer 0 contract itself has no evaluator, API schema, or persistence model.
The evaluator belongs to Layer 2.

## Layer 1 normalization

Layer 1 adds one pure policy module, `app/policy/normalization.py`, with no HTTP, database, clock, file, LLM, settings, or profile dependency.

- `normalize_case` copies a validated `CaseSubmission` into a `NormalizedCase`, converting only whitespace-only decision-bearing text to absent while preserving every nonblank value exactly.
- `first_missing_field` identifies the first absent required business fact.
- `question_for_field_path` returns the approved synthetic-safe repair question for that field path.

The former temporary-contract document was retired from the working documentation; the frozen legacy behavior remains evidenced by the legacy code and regression fixtures and is not the Sprint 1 policy source.

## Layer 2 evaluation

Layer 2 adds `app/policy/evaluator.py` and its `evaluate_case` function.
It accepts only a normalized case and injected immutable profile, and returns a `DecisionDraft` without selecting a profile or accessing infrastructure.
The former temporary-contract document was retired from the working documentation; this legacy evaluator is not the Sprint 1 policy source.

## Temporary decision-history

The temporary decision-history layer adds immutable, append-only persistence and a minimal submit-and-trace API. The existing normalizer and evaluator stay pure and unchanged.

- **Schema.** One Alembic revision creates `temporary_case_snapshots`, `temporary_decision_snapshots`, and `temporary_audit_events`, plus `BEFORE UPDATE OR DELETE` immutability triggers. Apply it with the command in step 4 above after starting the database.
- **Endpoints.** `POST /api/temporary/decision-traces` validates, normalizes, evaluates, and writes one complete trace in one transaction (201, with a `Location` header). `GET /api/temporary/decision-traces/{trace_id}` returns the stored snapshots and ordered events without reevaluating the decision (200). Errors are `422 INPUT_INVALID`, `409 CASE_ID_ALREADY_RECORDED`, and `404 TRACE_NOT_FOUND`; `/health` is unchanged.
- **Append-only and atomic.** Each trace writes a case snapshot, a decision snapshot, and three `SYSTEM` events (`CASE_RECEIVED` → `CASE_NORMALIZED` → `DECISION_RECORDED`) in one transaction. A failed write leaves no partial record, and the database triggers reject update and delete.
- **Reset (no API route).** For a local or demo reset, recreate the synthetic-only database and rerun `uv run alembic upgrade head`. Confirm first that the database contains no real data; the reset is intentionally destructive and is never exposed to an end user.

## Temporary Control Deck

The temporary Control Deck adds a narrow, synthetically labelled control layer on top of the finished decision-history ledger. The evaluator, normalizer, profile, and original snapshots are unchanged.

- **Vocabulary.** The server records the fixed synthetic actor `DEMO_REVIEWER` and the append-only actions `CASE_PAUSED`, `CASE_RESUMED`, `DEMO_REVIEW_RECORDED`, and `CONTROL_COMPENSATED`. The bounded review disposition is `DEMO_ALLOW` or `DEMO_DECLINE`.
- **Derived state.** `control_state` is one of `AUTO_APPROVED`, `AWAITING_INPUT`, `AWAITING_REVIEW`, `PAUSED`, or `DEMO_REVIEWED`, projected by the pure reducer in `app/domain/control.py`. It is never stored as a mutable column.
- **Command service.** `app/application/control_deck.py` locks the trace row with `SELECT ... FOR UPDATE`, replays the reducer, validates the transition, calculates `max(sequence_number) + 1`, appends one event plus its idempotency receipt, and returns the derived trace view in a single transaction.
- **Endpoint.** `POST /api/temporary/decision-traces/{trace_id}/controls` accepts `{command, reason, disposition?, idempotency_key?}` and returns the trace view with `control_state`. `GET /api/temporary/decision-traces/{trace_id}` also returns `control_state`.
- **Errors.** Malformed commands return `422 INPUT_INVALID`, unknown traces `404 TRACE_NOT_FOUND`, and illegal transitions or reused keys `409 ILLEGAL_CONTROL_ACTION` or `409 CONTROL_IDEMPOTENCY_CONFLICT`.
- **Undo.** `undo` compensates only the latest still-reversible control event by appending a `CONTROL_COMPENSATED` event that records `target_event_id` and the target's `prior_state`; it never edits or deletes the target.

The former temporary-contract document was retired from the working documentation; this Control Deck remains legacy synthetic behavior only.

## Database integration tests

Service, migration, and immutability tests run against a separate, synthetic-only `test-db` service so they never touch a development or demo database.

```bash
docker compose up -d test-db
export TEST_DATABASE_URL='postgresql+psycopg2://decisioncore:<your-postgres-password>@localhost:5433/decisioncore_test'
uv run pytest -m integration
```

`TEST_DATABASE_URL` is required to run the decision-history and Control Deck service, migration, immutability, idempotency, and concurrency tests against the synthetic-only `test-db` service.
Use the same password you set for `POSTGRES_PASSWORD`.
When `TEST_DATABASE_URL` is unset or the server is unreachable, the database integration tests skip with a clear message so the short quality gate still runs.

## Legacy implementation exclusions

These exclusions describe `TMP-DEV-001` only. They do not prevent the separate Sprint 1 reimbursement-v1 path from adding the bounded AI agent defined in ADR-012.

- No real human approval, rejection, override, reviewer queue, login, or role-based access control. The temporary Control Deck is a synthetic demo mechanic using the fixed `DEMO_REVIEWER` label and never a real authority.
- No payment, authentication, upload, OCR, LLM, or LangChain/Langfuse features in the legacy path.
- No public deployment or production readiness claim.
