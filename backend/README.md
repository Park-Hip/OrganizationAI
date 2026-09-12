# OrganizationalAI backend (temporary)

This directory is the temporary backend development foundation for the L0 contract-and-tooling task.
It contains no policy evaluation, no domain tables, and no public API yet.

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

### 5. Run the full quality gate

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
- FastAPI metadata and startup logging resolve from typed runtime settings.
- Postgres starts through a reproducible Compose definition with a health check.
- Alembic is wired to typed settings without a speculative schema.
- The health endpoint distinguishes a reachable database from an unreachable one without leaking credentials.

## Temporary provenance

Every later layer must keep these markers on persisted records and responses:

| Field | Value |
| --- | --- |
| `profile_id` | `TMP-DEV-001` |
| `profile_source` | `TEMPORARY_DEVELOPMENT` |
| `data_class` | `SYNTHETIC` |
| `workflow_validation_status` | `UNVALIDATED` |

Do not treat `TEST_ALLOWED`, `TEST_BLOCKED`, `1000`, or `TREASURER` as real club practice.

## Not in L0 scope

- No policy evaluator.
- No Case, Decision, or Audit tables.
- No submit, detail, or fixture endpoints.
- No human control, authentication, payment, upload, OCR, LLM, or LangChain/Langfuse features.
- No public deployment or production readiness claim.
