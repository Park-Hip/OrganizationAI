"""Proof that the temporary corpus reaches the production evaluator path."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

import pytest

from app.domain.enums import DecisionOutcome, EvidenceStatus, TemporaryCategory, TemporaryRuleId
from app.domain.models import Expense, NormalizedCase
from app.policy.evaluator import evaluate_case
from app.policy.profile import TMP_DEV_001_PROFILE

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_CORPUS_PATH = _REPOSITORY_ROOT / "docs" / "05_temporary_case_corpus.csv"

_REQUIRED_HEADERS: tuple[str, ...] = (
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


def _validate_header(fields: list[str] | None) -> list[str]:
    """Validate and return the frozen corpus header."""
    if fields is None:
        raise ValueError("corpus CSV has no header row")
    if len(fields) != len(set(fields)):
        raise ValueError("corpus CSV header has duplicate columns")
    missing = set(_REQUIRED_HEADERS) - set(fields)
    unexpected = set(fields) - set(_REQUIRED_HEADERS)
    if missing or unexpected:
        raise ValueError(
            f"corpus CSV header drifted: missing={sorted(missing)} unexpected={sorted(unexpected)}"
        )
    return fields


def _empty_to_none(value: str) -> str | None:
    """Map empty cells to None without hiding whitespace-only text."""
    return None if value == "" else value


def _read_rows_from(path: Path) -> list[dict[str, str | None]]:
    """Read and validate corpus rows for this test module only."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        fields = _validate_header(next(reader, None))
        rows: list[dict[str, str | None]] = []
        for row_number, raw_row in enumerate(reader, start=2):
            if len(raw_row) != len(fields):
                raise ValueError(
                    f"corpus row {row_number} has {len(raw_row)} fields; expected {len(fields)}"
                )
            rows.append(
                {name: _empty_to_none(value) for name, value in zip(fields, raw_row, strict=True)}
            )

    if not rows:
        raise ValueError("corpus CSV contains no data rows")
    _validate_identity(rows)
    return rows


def _validate_identity(rows: list[dict[str, str | None]]) -> None:
    """Reject missing or duplicate fixture and case identities."""
    fixture_ids = [_required(row, "fixture_id") for row in rows]
    case_ids = [_required(row, "case_id") for row in rows]
    if len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("corpus CSV contains duplicate fixture_id values")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("corpus CSV contains duplicate case_id values")


def _required(row: dict[str, str | None], column: str) -> str:
    """Return a nonblank corpus cell needed to construct or verify a case."""
    value = row.get(column)
    if value is None or not value.strip():
        raise ValueError(f"corpus row has a blank {column}")
    return value


def _optional(row: dict[str, str | None], column: str) -> str | None:
    """Return a nullable corpus cell while preserving whitespace-only values."""
    return row.get(column)


def _case_from_row(row: dict[str, str | None]) -> NormalizedCase:
    """Map one validated row onto the frozen normalized case shape."""
    category_raw = _required(row, "expense_category")
    evidence_raw = _required(row, "expense_evidence_status")
    amount_raw = _required(row, "expense_amount_vnd")
    date_raw = _required(row, "expense_date")
    return NormalizedCase(
        case_id=_required(row, "case_id"),
        submitted_at=datetime.fromisoformat(_required(row, "submitted_at").replace("Z", "+00:00")),
        requester_role=_optional(row, "requester_role"),
        purpose=_optional(row, "purpose"),
        expense=Expense(
            category=TemporaryCategory(category_raw),
            description=_optional(row, "expense_description"),
            amount_vnd=int(amount_raw),
            expense_date=date.fromisoformat(date_raw),
            evidence_status=EvidenceStatus(evidence_raw),
        ),
    )


def _expected_outcome(row: dict[str, str | None]) -> DecisionOutcome:
    return DecisionOutcome(_required(row, "expected_outcome"))


def _expected_rule(row: dict[str, str | None]) -> TemporaryRuleId:
    return TemporaryRuleId(_required(row, "expected_rule_id"))


def test_temporary_fixture_matrix_matches_outcome_and_rule() -> None:
    rows = _read_rows_from(_CORPUS_PATH)

    assert {row["fixture_id"] for row in rows} == {f"TMP-00{index}" for index in range(1, 7)}
    for row in rows:
        case = _case_from_row(row)
        draft = evaluate_case(case, TMP_DEV_001_PROFILE)

        assert _required(row, "profile_id") == TMP_DEV_001_PROFILE.profile_id
        assert _required(row, "profile_source") == TMP_DEV_001_PROFILE.profile_source.value
        assert _required(row, "data_class") == TMP_DEV_001_PROFILE.data_class.value
        assert (
            _required(row, "workflow_validation_status")
            == TMP_DEV_001_PROFILE.workflow_validation_status.value
        )
        assert draft.outcome is _expected_outcome(row)
        assert draft.applied_rule_id is _expected_rule(row)
        assert draft.profile_id == TMP_DEV_001_PROFILE.profile_id
        assert draft.reason.strip()
        if draft.outcome is DecisionOutcome.AUTO_APPROVED:
            assert draft.question is None
        else:
            assert draft.question is not None
            assert draft.question.endswith("?")


def test_matrix_uses_no_fixture_metadata_as_a_policy_input() -> None:
    rows = _read_rows_from(_CORPUS_PATH)
    first = _case_from_row(rows[0])
    renamed = first.model_copy(update={"case_id": "DIFFERENT-CASE-ID"})

    assert evaluate_case(first, TMP_DEV_001_PROFILE) == evaluate_case(renamed, TMP_DEV_001_PROFILE)


def test_header_validation_rejects_missing_unexpected_and_duplicate_columns() -> None:
    headers = list(_REQUIRED_HEADERS)
    with pytest.raises(ValueError, match="no header row"):
        _validate_header(None)
    with pytest.raises(ValueError, match="duplicate columns"):
        _validate_header([headers[0], headers[0], *headers[2:]])
    with pytest.raises(ValueError, match="drifted"):
        _validate_header([*headers[:-1], "unexpected"])


def test_row_validation_rejects_bad_width_and_duplicate_identity(tmp_path: Path) -> None:
    bad_width = tmp_path / "bad-width.csv"
    bad_width.write_text(",".join(_REQUIRED_HEADERS) + "\nonly-one-value\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fields"):
        _read_rows_from(bad_width)

    duplicate_identity = tmp_path / "duplicate.csv"
    first_duplicate_row = [""] * len(_REQUIRED_HEADERS)
    first_duplicate_row[0] = "TMP-001"
    first_duplicate_row[5] = "CASE-001"
    second_duplicate_row = [""] * len(_REQUIRED_HEADERS)
    second_duplicate_row[0] = "TMP-001"
    second_duplicate_row[5] = "CASE-002"
    duplicate_identity.write_text(
        ",".join(_REQUIRED_HEADERS)
        + "\n"
        + ",".join(first_duplicate_row)
        + "\n"
        + ",".join(second_duplicate_row)
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate fixture_id"):
        _read_rows_from(duplicate_identity)


def test_empty_cells_become_none_but_whitespace_is_preserved() -> None:
    assert _empty_to_none("") is None
    assert _empty_to_none("   ") == "   "
    assert _empty_to_none("value") == "value"


def test_corpus_path_is_the_documented_repository_fixture() -> None:
    assert _CORPUS_PATH == _REPOSITORY_ROOT / "docs" / "05_temporary_case_corpus.csv"
    assert _CORPUS_PATH.is_file()
