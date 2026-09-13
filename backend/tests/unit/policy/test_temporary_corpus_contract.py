"""Contract tests for the L3 test-only temporary corpus reader.

Proves the canonical temporary document loads, carries the sole temporary
profile, and converts into the frozen Layer 0 CaseSubmission shape.
The L3 decision matrix separately evaluates those parsed submissions through
the real Layer 1 and Layer 2 composition.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import cast

import pytest

from app.domain.enums import DecisionOutcome, EvidenceStatus, TemporaryCategory, TemporaryRuleId
from app.domain.models import CaseSubmission
from app.policy.profile import TMP_DEV_001_PROFILE


def _row_for(rows: list[dict[str, str | None]], fixture_id: str) -> dict[str, str | None]:
    for row in rows:
        if row["fixture_id"] == fixture_id:
            return row
    raise AssertionError(f"fixture {fixture_id} not found in the temporary corpus")


def _submission_for(
    reader_tools: SimpleNamespace,
    rows: list[dict[str, str | None]],
    fixture_id: str,
) -> CaseSubmission:
    return cast(CaseSubmission, reader_tools.submission_from_row(_row_for(rows, fixture_id)))


def test_canonical_corpus_has_exactly_six_rows(
    corpus_rows: list[dict[str, str | None]],
) -> None:
    assert len(corpus_rows) == 6


def test_corpus_fixture_ids_are_the_documented_six(
    corpus_rows: list[dict[str, str | None]],
) -> None:
    assert {row["fixture_id"] for row in corpus_rows} == {f"TMP-00{index}" for index in range(1, 7)}


def test_every_row_carries_the_sole_temporary_profile_provenance(
    corpus_rows: list[dict[str, str | None]],
) -> None:
    for row in corpus_rows:
        assert row["profile_id"] == TMP_DEV_001_PROFILE.profile_id
        assert row["profile_source"] == TMP_DEV_001_PROFILE.profile_source.value
        assert row["data_class"] == TMP_DEV_001_PROFILE.data_class.value
        assert (
            row["workflow_validation_status"]
            == TMP_DEV_001_PROFILE.workflow_validation_status.value
        )


def test_expected_outcomes_are_valid_and_cover_all_four_results(
    corpus_rows: list[dict[str, str | None]],
) -> None:
    values = {row["expected_outcome"] for row in corpus_rows}
    assert values == {outcome.value for outcome in DecisionOutcome}


def test_expected_rule_ids_are_valid_and_cover_all_five_rules(
    corpus_rows: list[dict[str, str | None]],
) -> None:
    values = {row["expected_rule_id"] for row in corpus_rows}
    assert values == {rule.value for rule in TemporaryRuleId}


def test_frozen_header_is_accepted(corpus_reader_tools: SimpleNamespace) -> None:
    headers = list(corpus_reader_tools.required_headers)
    assert corpus_reader_tools.validate_header(headers) == headers


def test_header_validation_rejects_a_missing_required_column(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    headers = [name for name in corpus_reader_tools.required_headers if name != "expected_outcome"]
    with pytest.raises(ValueError, match="missing columns"):
        corpus_reader_tools.validate_header(headers)


def test_header_validation_rejects_an_unexpected_column(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    headers = [*corpus_reader_tools.required_headers, "unexpected_column"]
    with pytest.raises(ValueError, match="unexpected columns"):
        corpus_reader_tools.validate_header(headers)


def test_header_validation_rejects_duplicate_columns(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    headers = list(corpus_reader_tools.required_headers)
    headers[1] = headers[0]
    with pytest.raises(ValueError, match="duplicate columns"):
        corpus_reader_tools.validate_header(headers)


def test_header_validation_rejects_a_missing_header_row(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    with pytest.raises(ValueError, match="no header row"):
        corpus_reader_tools.validate_header(None)


def test_empty_to_none_only_maps_truly_empty_cells(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    assert corpus_reader_tools.empty_to_none(None) is None
    assert corpus_reader_tools.empty_to_none("") is None
    assert corpus_reader_tools.empty_to_none("   ") == "   "
    assert corpus_reader_tools.empty_to_none("Synthetic allowed expense") == (
        "Synthetic allowed expense"
    )


def test_row_validation_rejects_an_empty_corpus(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    with pytest.raises(ValueError, match="no data rows"):
        corpus_reader_tools.validate_rows([])


def test_row_validation_rejects_duplicate_fixture_ids(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    rows = [
        {"fixture_id": "TMP-001", "case_id": "TMP-001"},
        {"fixture_id": "TMP-001", "case_id": "TMP-002"},
    ]
    with pytest.raises(ValueError, match="duplicate fixture_id"):
        corpus_reader_tools.validate_rows(rows)


def test_row_validation_rejects_duplicate_case_ids(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    rows = [
        {"fixture_id": "TMP-001", "case_id": "SAME"},
        {"fixture_id": "TMP-002", "case_id": "SAME"},
    ]
    with pytest.raises(ValueError, match="duplicate case_id"):
        corpus_reader_tools.validate_rows(rows)


def test_row_validation_rejects_blank_fixture_id(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    with pytest.raises(ValueError, match="blank fixture_id"):
        corpus_reader_tools.validate_rows([{"fixture_id": "   ", "case_id": "TMP-001"}])


def test_row_validation_rejects_blank_case_id(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    with pytest.raises(ValueError, match="blank case_id"):
        corpus_reader_tools.validate_rows([{"fixture_id": "TMP-001", "case_id": "   "}])


def test_row_validation_rejects_missing_fixture_id(
    corpus_reader_tools: SimpleNamespace,
) -> None:
    with pytest.raises(ValueError, match="blank fixture_id"):
        corpus_reader_tools.validate_rows([{"case_id": "TMP-001"}])


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("profile_id", "OTHER"),
        ("profile_source", "OTHER"),
        ("data_class", "OTHER"),
        ("workflow_validation_status", "OTHER"),
    ],
)
def test_row_validation_rejects_mismatched_profile_provenance(
    corpus_reader_tools: SimpleNamespace,
    column: str,
    value: str,
) -> None:
    row = {
        "fixture_id": "TMP-001",
        "case_id": "TMP-001",
        "profile_id": TMP_DEV_001_PROFILE.profile_id,
        "profile_source": TMP_DEV_001_PROFILE.profile_source.value,
        "data_class": TMP_DEV_001_PROFILE.data_class.value,
        "workflow_validation_status": TMP_DEV_001_PROFILE.workflow_validation_status.value,
    }
    row[column] = value

    with pytest.raises(ValueError, match=f"invalid {column}"):
        corpus_reader_tools.validate_rows([row])


def test_every_row_converts_to_a_valid_case_submission(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    for row in corpus_rows:
        submission = corpus_reader_tools.submission_from_row(row)
        assert isinstance(submission, CaseSubmission)
        assert submission.expense is not None
        assert submission.submitted_at.tzinfo is not None


def test_empty_purpose_row_converts_to_a_none_business_fact(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    row = _row_for(corpus_rows, "TMP-002")
    assert row["purpose"] is None
    submission = corpus_reader_tools.submission_from_row(row)
    assert submission.purpose is None
    assert submission.requester_role == "TEST_REQUESTER"


def test_authority_boundary_amounts_parse_onto_the_documented_side(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    expected = {"TMP-001": 999, "TMP-005": 1001, "TMP-006": 1000}
    for fixture_id, amount in expected.items():
        submission = _submission_for(corpus_reader_tools, corpus_rows, fixture_id)
        assert submission.expense is not None
        assert submission.expense.amount_vnd == amount


def test_blocked_category_parses_to_the_valid_temporary_enum(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    submission = _submission_for(corpus_reader_tools, corpus_rows, "TMP-004")
    assert submission.expense is not None
    assert submission.expense.category is TemporaryCategory.TEST_BLOCKED


def test_not_provided_evidence_parses_to_the_temporary_enum(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    submission = _submission_for(corpus_reader_tools, corpus_rows, "TMP-003")
    assert submission.expense is not None
    assert submission.expense.evidence_status is EvidenceStatus.NOT_PROVIDED


def test_routine_row_parses_allowed_category_present_evidence_and_dates(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    submission = _submission_for(corpus_reader_tools, corpus_rows, "TMP-001")
    assert submission.expense is not None
    assert submission.expense.category is TemporaryCategory.TEST_ALLOWED
    assert submission.expense.evidence_status is EvidenceStatus.PRESENT
    assert submission.expense.expense_date == date(2026, 1, 14)
    assert submission.submitted_at == datetime(2026, 1, 15, 9, 0, tzinfo=UTC)


def test_corpus_reading_is_deterministic(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    assert corpus_reader_tools.read_corpus() == corpus_rows


def test_conversion_is_deterministic(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
) -> None:
    first = [corpus_reader_tools.submission_from_row(row) for row in corpus_rows]
    second = [corpus_reader_tools.submission_from_row(row) for row in corpus_rows]
    assert first == second
