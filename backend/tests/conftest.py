"""Shared pytest fixtures and the L3 test-only temporary corpus reader."""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterator
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.domain.enums import EvidenceStatus, TemporaryCategory
from app.domain.models import CaseSubmission, DecisionDraft, Expense
from app.policy.profile import TMP_DEV_001_PROFILE

TEST_DATABASE_URL = "postgresql+psycopg2://decisioncore:decisioncore@localhost:5432/decisioncore"


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    """Prevent cached settings from leaking across tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """Return a fresh application instance per test."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Return a TestClient bound to the fresh application instance."""
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Temporary corpus reader (L3 reader-first scope).
#
# Reads the canonical temporary corpus as test-only data and converts each row
# into the frozen Layer 0 CaseSubmission shape. Production code never imports
# this reader, and the reader never decides policy.
# ---------------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
CORPUS_PATH = REPOSITORY_ROOT / "docs" / "05_temporary_case_corpus.csv"

CORPUS_REQUIRED_HEADERS: tuple[str, ...] = (
    "fixture_id",
    "profile_id",
    "profile_source",
    "data_class",
    "workflow_validation_status",
    "case_id",
    "submitted_at",
    "requester_role",
    "purpose",
    "expense_category",
    "expense_description",
    "expense_amount_vnd",
    "expense_date",
    "expense_evidence_status",
    "expected_outcome",
    "expected_rule_id",
    "notes",
)


def _validate_corpus_header(fields: list[str] | None) -> list[str]:
    """Return the header only when it matches the frozen corpus schema."""
    if fields is None:
        raise ValueError("corpus CSV has no header row")
    if len(fields) != len(set(fields)):
        raise ValueError(f"corpus CSV header has duplicate columns: {fields}")
    missing = set(CORPUS_REQUIRED_HEADERS) - set(fields)
    unexpected = set(fields) - set(CORPUS_REQUIRED_HEADERS)
    problems = []
    if missing:
        problems.append(f"missing columns {sorted(missing)}")
    if unexpected:
        problems.append(f"unexpected columns {sorted(unexpected)}")
    if problems:
        raise ValueError("corpus CSV header drifted from the frozen schema: " + "; ".join(problems))
    return fields


def _empty_to_none(value: str | None) -> str | None:
    """Map a truly empty CSV cell to None while preserving whitespace-only text.

    Whitespace-only business text is deliberately retained so the L1 normalizer
    can canonicalize it. This reader must not silently invent absence.
    """
    if value is None or value == "":
        return None
    return value


def _validate_corpus_rows(
    rows: list[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    """Reject an empty corpus or any identity drift between temporary rows."""
    if not rows:
        raise ValueError("corpus CSV contains no data rows")
    for index, row in enumerate(rows, start=2):
        for column in ("fixture_id", "case_id"):
            value = row.get(column)
            if value is None or not value.strip():
                raise ValueError(f"corpus row {index} has a blank {column}")
    fixture_ids = [row["fixture_id"] for row in rows]
    case_ids = [row["case_id"] for row in rows]
    if len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("corpus CSV contains duplicate fixture_id values")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("corpus CSV contains duplicate case_id values")
    expected_provenance = {
        "profile_id": TMP_DEV_001_PROFILE.profile_id,
        "profile_source": TMP_DEV_001_PROFILE.profile_source.value,
        "data_class": TMP_DEV_001_PROFILE.data_class.value,
        "workflow_validation_status": TMP_DEV_001_PROFILE.workflow_validation_status.value,
    }
    for index, row in enumerate(rows, start=2):
        for column, expected_value in expected_provenance.items():
            if row.get(column) != expected_value:
                raise ValueError(
                    f"corpus row {index} has invalid {column}; expected {expected_value!r}"
                )
    return rows


def _read_temporary_corpus() -> list[dict[str, str | None]]:
    """Read and validate the canonical temporary corpus from the repository docs."""
    if not CORPUS_PATH.is_file():
        raise ValueError(f"temporary corpus not found at {CORPUS_PATH}")
    with CORPUS_PATH.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        fields = _validate_corpus_header(next(reader, None))
        rows: list[dict[str, str | None]] = []
        for index, raw_row in enumerate(reader, start=2):
            if len(raw_row) != len(fields):
                raise ValueError(
                    f"corpus row {index} has {len(raw_row)} fields; expected {len(fields)}"
                )
            rows.append(
                {name: _empty_to_none(value) for name, value in zip(fields, raw_row, strict=True)}
            )
    return _validate_corpus_rows(rows)


def _category_from(row: dict[str, str | None]) -> TemporaryCategory | None:
    value = _empty_to_none(row.get("expense_category"))
    return None if value is None else TemporaryCategory(value)


def _evidence_from(row: dict[str, str | None]) -> EvidenceStatus | None:
    value = _empty_to_none(row.get("expense_evidence_status"))
    return None if value is None else EvidenceStatus(value)


def _amount_from(row: dict[str, str | None]) -> int | None:
    value = _empty_to_none(row.get("expense_amount_vnd"))
    return None if value is None else int(value)


def _date_from(row: dict[str, str | None]) -> date | None:
    value = _empty_to_none(row.get("expense_date"))
    return None if value is None else date.fromisoformat(value)


def _case_submission_from_corpus_row(
    row: dict[str, str | None],
) -> CaseSubmission:
    """Convert one validated corpus row into the frozen Layer 0 submission shape."""
    submitted_at_raw = _empty_to_none(row.get("submitted_at"))
    if submitted_at_raw is None:
        raise ValueError("corpus row is missing the required submitted_at value")
    case_id_raw = row.get("case_id")
    if case_id_raw is None:
        raise ValueError("corpus row is missing the required case_id value")

    return CaseSubmission(
        case_id=case_id_raw,
        submitted_at=datetime.fromisoformat(submitted_at_raw.replace("Z", "+00:00")),
        requester_role=_empty_to_none(row.get("requester_role")),
        purpose=_empty_to_none(row.get("purpose")),
        expense=Expense(
            category=_category_from(row),
            description=_empty_to_none(row.get("expense_description")),
            amount_vnd=_amount_from(row),
            expense_date=_date_from(row),
            evidence_status=_evidence_from(row),
        ),
    )


@pytest.fixture(scope="session")
def corpus_rows() -> list[dict[str, str | None]]:
    """Return the validated canonical temporary corpus rows."""
    return _read_temporary_corpus()


@pytest.fixture(scope="session")
def corpus_reader_tools() -> SimpleNamespace:
    """Expose the reader's pure helpers for focused contract tests."""
    return SimpleNamespace(
        required_headers=CORPUS_REQUIRED_HEADERS,
        empty_to_none=_empty_to_none,
        validate_header=_validate_corpus_header,
        validate_rows=_validate_corpus_rows,
        read_corpus=_read_temporary_corpus,
        submission_from_row=_case_submission_from_corpus_row,
    )


@pytest.fixture(scope="session")
def evaluate_submission() -> Callable[[CaseSubmission], DecisionDraft]:
    """Return the real L1 normalization plus L2 evaluation composition."""
    from app.policy.evaluator import evaluate_case
    from app.policy.normalization import normalize_case

    def _evaluate(submission: CaseSubmission) -> DecisionDraft:
        return evaluate_case(normalize_case(submission), TMP_DEV_001_PROFILE)

    return _evaluate
