"""L3 decision matrix: each canonical temporary corpus row through the real
normalizer and evaluator must land on its documented decision.

Expected values are read from the document row itself. This module maintains no
second fixture table, and it exercises the same L1 + L2 path a future Verify
service will drive.
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import pytest

from app.domain.models import CaseSubmission, DecisionDraft
from app.policy import TMP_DEV_001_PROFILE

pytestmark = pytest.mark.legacy

_NO_PAYMENT_REASON = "Approved under temporary development profile; no payment was made."

_Evaluator = Callable[[CaseSubmission], DecisionDraft]


def _evaluate_row(
    reader_tools: SimpleNamespace,
    evaluate_submission: _Evaluator,
    row: dict[str, str | None],
) -> DecisionDraft:
    submission = cast(CaseSubmission, reader_tools.submission_from_row(row))
    return evaluate_submission(submission)


def test_every_corpus_row_lands_on_its_documented_decision(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
    evaluate_submission: _Evaluator,
) -> None:
    for row in corpus_rows:
        fixture_id = row["fixture_id"]
        draft = _evaluate_row(corpus_reader_tools, evaluate_submission, row)
        assert draft.outcome.value == row["expected_outcome"], (
            f"{fixture_id}: expected outcome {row['expected_outcome']!r}, "
            f"got {draft.outcome.value!r}"
        )
        assert draft.applied_rule_id.value == row["expected_rule_id"], (
            f"{fixture_id}: expected rule {row['expected_rule_id']!r}, "
            f"got {draft.applied_rule_id.value!r}"
        )
        assert draft.profile_id == TMP_DEV_001_PROFILE.profile_id, (
            f"{fixture_id}: decision must link to the sole temporary profile"
        )


def test_automatic_decisions_carry_the_exact_non_payment_disclosure(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
    evaluate_submission: _Evaluator,
) -> None:
    automatic_rows = [row for row in corpus_rows if row["expected_outcome"] == "AUTO_APPROVED"]
    assert len(automatic_rows) == 2

    for row in automatic_rows:
        draft = _evaluate_row(corpus_reader_tools, evaluate_submission, row)
        assert draft.outcome.value == "AUTO_APPROVED"
        assert draft.reason == _NO_PAYMENT_REASON
        assert draft.question is None


def test_non_automatic_decisions_carry_a_nonblank_question(
    corpus_rows: list[dict[str, str | None]],
    corpus_reader_tools: SimpleNamespace,
    evaluate_submission: _Evaluator,
) -> None:
    non_automatic_rows = [row for row in corpus_rows if row["expected_outcome"] != "AUTO_APPROVED"]
    assert len(non_automatic_rows) == 4

    for row in non_automatic_rows:
        draft = _evaluate_row(corpus_reader_tools, evaluate_submission, row)
        assert draft.question is not None, f"{row['fixture_id']}: expected a question"
        assert draft.question.strip() != "", f"{row['fixture_id']}: question must not be blank"
        assert draft.reason.strip() != "", f"{row['fixture_id']}: reason must not be blank"
