# OrganizationalAI backend (temporary)

This directory is the temporary backend development foundation: a frozen domain vocabulary, one temporary profile constant, a pure Layer 1 normalizer, a pure Layer 2 evaluator, and a temporary decision-history persistence layer.
The persistence layer stores immutable synthetic case/decision snapshots plus an append-only `SYSTEM` audit-event chain, and exposes a minimal submit-and-trace API under `/api/temporary/decision-traces`.
Its operational `/health` readiness endpoint remains intentionally limited to process and database status.

Everything here serves the explicitly temporary `TMP-DEV-001` development profile.
No real reimbursement workflow, payment, or policy claim is implied.

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

## What this foundation proves

- A clean clone installs and configures from committed, locked dependencies.
- The typed settings object fails fast when `DATABASE_URL` is absent.
- The frozen domain vocabulary and sole profile construct and validate their structural rules.
- The Layer 1 normalizer converts whitespace-only decision-bearing text to canonical absence and exposes the canonical purpose and expense-field repair questions without any I/O.
- The Layer 2 evaluator returns a deterministic `DecisionDraft` from a normalized case and injected immutable profile without I/O, then applies missing-fact, category, evidence, authority, and automatic-approval precedence.
- The temporary decision-history layer writes one immutable trace (case snapshot, decision snapshot, three ordered `SYSTEM` events) in a single transaction and rejects update/delete through immutability triggers.
- The submit-and-trace API accepts only the frozen case shape, returns stored snapshots without reevaluating a past decision, and marks every business response as temporary, synthetic, and unvalidated.
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

The authoritative required-fact, normalization, field-priority, and repair-question contract is [docs/04_temporary_system_contract.md](../docs/04_temporary_system_contract.md).

## Layer 2 evaluation

Layer 2 adds `app/policy/evaluator.py` and its `evaluate_case` function.
It accepts only a normalized case and injected immutable profile, and returns a `DecisionDraft` without selecting a profile or accessing infrastructure.
The authoritative precedence, profile behavior, and question contract is [docs/04_temporary_system_contract.md](../docs/04_temporary_system_contract.md).

## Temporary decision-history

The temporary decision-history layer adds immutable, append-only persistence and a minimal submit-and-trace API. The existing normalizer and evaluator stay pure and unchanged.

- **Schema.** One Alembic revision creates `temporary_case_snapshots`, `temporary_decision_snapshots`, and `temporary_audit_events`, plus `BEFORE UPDATE OR DELETE` immutability triggers. Apply it with the command in step 4 above after starting the database.
- **Endpoints.** `POST /api/temporary/decision-traces` validates, normalizes, evaluates, and writes one complete trace in one transaction (201, with a `Location` header). `GET /api/temporary/decision-traces/{trace_id}` returns the stored snapshots and ordered events without reevaluating the decision (200). Errors are `422 INPUT_INVALID`, `409 CASE_ID_ALREADY_RECORDED`, and `404 TRACE_NOT_FOUND`; `/health` is unchanged.
- **Append-only and atomic.** Each trace writes a case snapshot, a decision snapshot, and three `SYSTEM` events (`CASE_RECEIVED` → `CASE_NORMALIZED` → `DECISION_RECORDED`) in one transaction. A failed write leaves no partial record, and the database triggers reject update and delete.
- **Reset (no API route).** For a local or demo reset, recreate the synthetic-only database and rerun `uv run alembic upgrade head`. Confirm first that the database contains no real data; the reset is intentionally destructive and is never exposed to an end user.

## Database integration tests

Service, migration, and immutability tests run against a separate, synthetic-only `test-db` service so they never touch a development or demo database.

```bash
docker compose up -d test-db
export TEST_DATABASE_URL='postgresql+psycopg2://decisioncore:<your-postgres-password>@localhost:5433/decisioncore_test'
uv run pytest tests/integration
```

`TEST_DATABASE_URL` is required. Use the same password you set for `POSTGRES_PASSWORD`. When it is unset or the server is unreachable, the database integration tests skip with a clear message so the short quality gate still runs.

## Not in current scope

- No pause, approve, reject, override, undo, reviewer queue, login, or role-based access control.
- No payment, authentication, upload, OCR, LLM, or LangChain/Langfuse features.
- No public deployment or production readiness claim.
