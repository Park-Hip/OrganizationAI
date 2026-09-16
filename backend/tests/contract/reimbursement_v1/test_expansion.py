"""Deterministic expansion and full-envelope schema validation."""

from __future__ import annotations

import json

import jsonschema
from _artifacts import POLICY_VERSION, PROFILE, REIMBURSEMENT_SCHEMA, TEST_CASES
from _expand import expand, materialize_envelope


def _envelope_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        REIMBURSEMENT_SCHEMA, format_checker=jsonschema.FormatChecker()
    )


def test_every_fixture_expands_to_a_valid_full_envelope() -> None:
    for case in TEST_CASES["cases"]:
        envelope = materialize_envelope(case["input"], PROFILE, POLICY_VERSION, case["expected"])
        errors = list(_envelope_validator().iter_errors(envelope))
        assert not errors, (case["id"], [error.message for error in errors])


def test_expansion_is_deterministic() -> None:
    first = TEST_CASES["cases"][0]["input"]
    assert json.dumps(expand(first, PROFILE, POLICY_VERSION), sort_keys=True) == json.dumps(
        expand(first, PROFILE, POLICY_VERSION), sort_keys=True
    )


def test_expander_receives_no_fixture_metadata() -> None:
    metadata_keys = {"id", "group", "title", "note", "verify"}
    for case in TEST_CASES["cases"]:
        assert metadata_keys.isdisjoint(case["input"])


def test_expansion_is_independent_of_free_text_prose() -> None:
    from copy import deepcopy

    base = TEST_CASES["cases"][0]["input"]
    changed = dict(base, purpose="Một mục đích hoàn toàn khác", task_or_event="EVT-KHAC")

    envelope_a = expand(base, PROFILE, POLICY_VERSION)
    envelope_b = expand(changed, PROFILE, POLICY_VERSION)

    assert envelope_a["case"]["case_id"] == envelope_b["case"]["case_id"]
    assert envelope_a["case"]["evidence"] == envelope_b["case"]["evidence"]
    assert envelope_a["case"]["expense_items"] == envelope_b["case"]["expense_items"]

    # Only the two prose fields propagate; the whole rest of the envelope is identical.
    structural_a = deepcopy(envelope_a)
    structural_b = deepcopy(envelope_b)
    del structural_a["case"]["purpose"]
    del structural_a["case"]["task_or_event"]
    del structural_b["case"]["purpose"]
    del structural_b["case"]["task_or_event"]
    assert structural_a == structural_b
    assert envelope_b["case"]["purpose"] == "Một mục đích hoàn toàn khác"
