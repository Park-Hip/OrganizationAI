# L0 quality gate: stops on the first failing check and returns its exit code.
# The database reachability smoke test is documented separately in backend/README.md.
$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "check.ps1: uv is required. Install it from https://docs.astral.sh/uv/"
    exit 1
}

Set-Location (Split-Path -Parent $PSScriptRoot)

function Step {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Command
    )
    Write-Host "==> $Name"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAILED: $Name (exit code $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
}

Step "1/5 format check" { uv run ruff format --check . }
Step "2/5 lint" { uv run ruff check . }
Step "3/5 type check" { uv run mypy app tests }
Step "4/5 tests" { uv run pytest }
Step "5/5 environment smoke" { uv run python scripts/smoke.py }

Write-Host "All checks passed."