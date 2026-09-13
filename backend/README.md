# OrganizationalAI backend (temporary)

This directory is the temporary backend development foundation for the L0 contract-and-tooling task and the Layer 1 normalization work.
It contains a frozen domain vocabulary, one temporary profile constant, a pure Layer 1 normalizer, and no policy evaluation, domain tables, or public product API yet.
Its operational `/health` readiness endpoint is intentionally limited to process and database status.

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

### 4. Confirm the migration state

The database is empty in L0.
Running the check below proves Alembic connects to Postgres with the configured URL and finds no application revision.

```bash
uv run alembic current
```

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
- The Layer 1 normalizer converts whitespace-only decision-bearing text to canonical absence and exposes a deterministic first-missing-fact order and repair-question map without any I/O.
- FastAPI metadata and startup logging resolve from typed runtime settings.
- Postgres starts through a reproducible Compose definition with a health check.
- Alembic is wired to typed settings without a speculative schema.
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
The operational `/health` readiness response is intentionally exempt and retains its minimal status/database contract.

## Layer 0 frozen contract

The backend freezes the smallest contract needed before normalization and pure policy evaluation:

- `app/domain` defines the frozen enums and record shapes (`Expense`, `CaseSubmission`, `NormalizedCase`, `TemporaryProfile`, and `DecisionDraft`).
- `app/policy/profile.py` exports exactly one immutable temporary profile, `TMP_DEV_001_PROFILE`, with provenance, `{TEST_ALLOWED}`, required evidence `PRESENT`, and an inclusive `1000` limit.
- `tests/contract/` proves the enum values, structural validation, deep immutability, decision-draft combinations, and the import boundary without starting FastAPI or a database.

The contract intentionally has no evaluator, API schema, or persistence model yet.

## Layer 1 normalization

Layer 1 adds one pure policy module, `app/policy/normalization.py`, with no HTTP, database, clock, file, LLM, settings, or profile dependency.

- `normalize_case` copies a validated `CaseSubmission` into a `NormalizedCase`, converting only whitespace-only decision-bearing text to absent while preserving every nonblank value exactly.
- `first_missing_field` identifies the first absent required business fact.
- `question_for_field_path` returns the approved synthetic-safe repair question for that field path.

The authoritative required-fact, normalization, field-priority, and repair-question contract is [docs/04_temporary_system_contract.md](../docs/04_temporary_system_contract.md).

## Not in L0 or L1 scope

- No policy evaluator.
- No rule-specific question wording such as the `TMP-EVD-01` evidence-referral prompt.
- No Case, Decision, or Audit tables.
- No submit, detail, or fixture endpoints.
- No human control, authentication, payment, upload, OCR, LLM, or LangChain/Langfuse features.
- No public deployment or production readiness claim.
