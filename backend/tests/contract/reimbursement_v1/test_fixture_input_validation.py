"""Every concise fixture input validates; malformed structure fails early."""

from __future__ import annotations

import jsonschema
from _artifacts import FIXTURE_SCHEMA, TEST_CASES, VERIFY_CASES


def _validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        FIXTURE_SCHEMA, format_checker=jsonschema.FormatChecker()
    )


def test_every_fixture_input_validates_against_the_fixture_schema() -> None:
    for case in TEST_CASES["cases"]:
        errors = list(_validator().iter_errors(case["input"]))
        assert not errors, (case["id"], [error.message for error in errors])


def test_fixture_ids_are_unique() -> None:
    ids = [case["id"] for case in TEST_CASES["cases"]]
    assert len(ids) == len(set(ids))


def test_verify_case_ids_exist_in_the_full_suite() -> None:
    full_ids = {case["id"] for case in TEST_CASES["cases"]}
    for verify_case in VERIFY_CASES["cases"]:
        assert verify_case["case_id"] in full_ids


def test_malformed_structural_input_is_rejected() -> None:
    malformed = {"expense": {"total_vnd": 1000, "category": "printing"}, "duplicate_check": "CLEAR"}
    errors = list(_validator().iter_errors(malformed))
    assert errors
    assert any("flow_type" in error.message for error in errors)
