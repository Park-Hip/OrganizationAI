#!/usr/bin/env bash
# L0 quality gate: stops on the first failing check and returns its exit code.
# The database reachability smoke test is documented separately in backend/README.md.
set -euo pipefail

command -v uv >/dev/null 2>&1 || {
  echo "check.sh: uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
}

cd "$(dirname "$0")/.." || exit 1

echo "==> 1/5 format check"
uv run ruff format --check .

echo "==> 2/5 lint"
uv run ruff check .

echo "==> 3/5 type check"
uv run mypy app tests

echo "==> 4/5 tests"
uv run pytest

echo "==> 5/5 environment smoke"
uv run python scripts/smoke.py

echo "All checks passed."