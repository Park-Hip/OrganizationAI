"""Deterministic expansion and full-envelope schema validation."""

from __future__ import annotations

import json
from copy import deepcopy

import jsonschema
import pytest
from _artifacts import POLICY_VERSION, PROFILE, REIMBURSEMENT_SCHEMA, TEST_CASES
from _expand import expand, materialize_envelope


def _envelope_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        REIMBURSEMENT_SCHEMA, format_checker=jsonschema.FormatChecker()
    )


def _component_validator(definition: str) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        {"$ref": f"#/$defs/{definition}", "$defs": REIMBURSEMENT_SCHEMA["$defs"]},
        format_checker=jsonschema.FormatChecker(),
    )


def _policy_version_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        REIMBURSEMENT_SCHEMA["properties"]["policy_version"],
        format_checker=jsonschema.FormatChecker(),
    )


def _control_state_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        REIMBURSEMENT_SCHEMA["properties"]["control_state"],
        format_checker=jsonschema.FormatChecker(),
    )


def test_every_fixture_expands_to_a_valid_input_snapshot() -> None:
    profile_validator = _component_validator("OrganizationProfile")
    case_validator = _component_validator("ReimbursementCase")
    audit_validator = _component_validator("AuditEvent")
    policy_version_validator = _policy_version_validator()
    control_state_validator = _control_state_validator()

    for fixture in TEST_CASES["cases"]:
        snapshot = expand(fixture["input"], PROFILE, POLICY_VERSION)
        errors = [
            *profile_validator.iter_errors(snapshot["organization_profile"]),
            *case_validator.iter_errors(snapshot["case"]),
            *policy_version_validator.iter_errors(snapshot["policy_version"]),
            *control_state_validator.iter_errors(snapshot["control_state"]),
            *(
                error
                for event in snapshot["audit_events"]
                for error in audit_validator.iter_errors(event)
            ),
        ]
        assert not errors, (fixture["id"], [error.message for error in errors])


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


def test_expansion_binds_generated_identifiers_to_the_full_snapshot() -> None:
    concise = TEST_CASES["cases"][0]["input"]
    current = expand(concise, PROFILE, POLICY_VERSION)
    different_profile = deepcopy(PROFILE)
    different_profile["policy_version"] = "1.3.0"
    different_profile["profile_version"] = "1.3.0"
    different_policy = expand(concise, different_profile, "1.3.0")

    assert current["case"]["case_id"] != different_policy["case"]["case_id"]
    assert (
        current["audit_events"][0]["input_hash"]
        != different_policy["audit_events"][0]["input_hash"]
    )


def test_expansion_rejects_policy_profile_version_mismatch() -> None:
    concise = TEST_CASES["cases"][0]["input"]

    with pytest.raises(ValueError, match="policy_version"):
        expand(concise, PROFILE, "1.3.0")


def test_expansion_normalizes_defaulted_input_before_hashing() -> None:
    concise = next(
        case["input"] for case in TEST_CASES["cases"] if "days_late" not in case["input"]
    )
    explicit_defaults = dict(concise, days_late=0)

    implicit = expand(concise, PROFILE, POLICY_VERSION)
    explicit = expand(explicit_defaults, PROFILE, POLICY_VERSION)

    assert implicit["case"]["case_id"] == explicit["case"]["case_id"]
    assert implicit["audit_events"][0]["input_hash"] == explicit["audit_events"][0]["input_hash"]


def test_expansion_rejects_hybrid_expense_input() -> None:
    hybrid = {
        "flow_type": "MEMBER_PAID",
        "expense": {
            "total_vnd": 850000,
            "category": "printing",
            "items": [
                {
                    "vendor": "V-SYN-001",
                    "transaction_date": "2026-08-01",
                    "purpose_code": "print",
                    "category": "printing",
                    "amount_vnd": 6000000,
                }
            ],
        },
        "duplicate_check": "CLEAR",
    }

    with pytest.raises(jsonschema.ValidationError):
        expand(hybrid, PROFILE, POLICY_VERSION)


def test_expansion_is_independent_of_free_text_prose() -> None:
    base = TEST_CASES["cases"][0]["input"]
    changed = dict(base, purpose="Một mục đích hoàn toàn khác")

    envelope_a = expand(base, PROFILE, POLICY_VERSION)
    envelope_b = expand(changed, PROFILE, POLICY_VERSION)

    assert envelope_a["case"]["case_id"] == envelope_b["case"]["case_id"]
    assert envelope_a["case"]["evidence"] == envelope_b["case"]["evidence"]
    assert envelope_a["case"]["expense_items"] == envelope_b["case"]["expense_items"]

    # Only the two prose fields propagate; the whole rest of the envelope is identical.
    structural_a = deepcopy(envelope_a)
    structural_b = deepcopy(envelope_b)
    del structural_a["case"]["purpose"]
    del structural_b["case"]["purpose"]
    assert structural_a == structural_b
    assert envelope_b["case"]["purpose"] == changed["purpose"]


def test_expansion_maps_absent_duplicate_check_to_not_run() -> None:
    concise = dict(TEST_CASES["cases"][0]["input"])
    del concise["duplicate_check"]

    envelope = expand(concise, PROFILE, POLICY_VERSION)

    assert envelope["case"]["duplicate_check"] == "NOT_RUN"


def test_initial_audit_events_follow_submission_time() -> None:
    concise = deepcopy(TEST_CASES["cases"][0]["input"])
    concise["submitted_at"] = "2026-10-01T09:00:00Z"

    envelope = expand(concise, PROFILE, POLICY_VERSION)

    assert [event["timestamp"] for event in envelope["audit_events"]] == [
        "2026-10-01T09:00:00Z",
        "2026-10-01T09:00:01Z",
    ]


def test_non_cash_payment_proof_uses_non_cash_verification() -> None:
    concise = next(
        case["input"]
        for case in TEST_CASES["cases"]
        if case["input"]["expense"].get("payment_method") == "BANK_TRANSFER"
    )
    concise = deepcopy(concise)
    concise["evidence"] = {"non_cash_verified": False}

    envelope = expand(concise, PROFILE, POLICY_VERSION)
    payment_proof = next(
        evidence for evidence in envelope["case"]["evidence"] if evidence["type"] == "PAYMENT_PROOF"
    )

    assert envelope["case"]["non_cash_evidence_verified"] is False
    assert payment_proof["verified"] is False


def test_non_cash_verification_defaults_false_without_payment_proof() -> None:
    concise = next(
        case["input"]
        for case in TEST_CASES["cases"]
        if case["input"]["expense"].get("payment_method") == "BANK_TRANSFER"
    )
    concise = deepcopy(concise)
    concise["evidence"] = {"payment_proof": False}

    envelope = expand(concise, PROFILE, POLICY_VERSION)

    assert envelope["case"]["non_cash_evidence_verified"] is False
    assert not any(evidence["type"] == "PAYMENT_PROOF" for evidence in envelope["case"]["evidence"])


def test_materialized_outcome_follows_initial_audit_events() -> None:
    case = next(
        case
        for case in TEST_CASES["cases"]
        if case["expected"].get("control_state", "ACTIVE") == "ACTIVE"
    )
    concise = deepcopy(case["input"])
    concise["submitted_at"] = "2026-10-01T09:00:00Z"

    envelope = materialize_envelope(concise, PROFILE, POLICY_VERSION, case["expected"])

    assert envelope["processing_outcome"]["created_at"] == "2026-10-01T09:00:02Z"


def test_schema_rejects_advance_fields_for_member_paid_case() -> None:
    member_paid = next(
        case["input"] for case in TEST_CASES["cases"] if case["input"]["flow_type"] == "MEMBER_PAID"
    )
    case_validator = _component_validator("ReimbursementCase")
    base = expand(member_paid, PROFILE, POLICY_VERSION)["case"]

    only_reference = deepcopy(base)
    only_reference["advance_reference"] = "ADV-SYN-001"
    assert list(case_validator.iter_errors(only_reference))

    only_amount = deepcopy(base)
    only_amount["advance_amount_vnd"] = 1000000
    assert list(case_validator.iter_errors(only_amount))


def test_schema_rejects_mismatched_escalation_types() -> None:
    case = next(
        case
        for case in TEST_CASES["cases"]
        if case["expected"].get("escalation_type") == "FACT_UNKNOWN"
    )
    envelope = materialize_envelope(case["input"], PROFILE, POLICY_VERSION, case["expected"])
    envelope["escalation"]["type"] = "OUT_OF_POLICY"

    assert list(_envelope_validator().iter_errors(envelope))


def test_schema_enforces_routine_calculation_fields_by_flow() -> None:
    member_paid = next(
        case
        for case in TEST_CASES["cases"]
        if case["input"]["flow_type"] == "MEMBER_PAID"
        and case["expected"].get("processing_result") == "ROUTINE_PROCESSED"
    )
    member_envelope = materialize_envelope(
        member_paid["input"], PROFILE, POLICY_VERSION, member_paid["expected"]
    )
    del member_envelope["processing_outcome"]["reimbursement_amount_vnd"]

    advance = next(
        case
        for case in TEST_CASES["cases"]
        if case["input"]["flow_type"] == "ADVANCE_SETTLEMENT"
        and case["expected"].get("processing_result") == "ROUTINE_PROCESSED"
    )
    advance_envelope = materialize_envelope(
        advance["input"], PROFILE, POLICY_VERSION, advance["expected"]
    )
    advance_envelope["processing_outcome"]["reimbursement_amount_vnd"] = 1

    assert list(_envelope_validator().iter_errors(member_envelope))
    assert list(_envelope_validator().iter_errors(advance_envelope))


def test_schema_rejects_active_processing_for_a_paused_case() -> None:
    routine = next(
        case
        for case in TEST_CASES["cases"]
        if case["expected"].get("processing_result") == "ROUTINE_PROCESSED"
    )
    envelope = materialize_envelope(routine["input"], PROFILE, POLICY_VERSION, routine["expected"])
    envelope["case"]["paused"] = True

    assert list(_envelope_validator().iter_errors(envelope))


def test_expansion_preserves_confirmed_duplicate_reference() -> None:
    concise = next(
        case["input"]
        for case in TEST_CASES["cases"]
        if case["input"]["duplicate_check"] == "CONFIRMED_PAID"
    )

    envelope = expand(concise, PROFILE, POLICY_VERSION)

    assert envelope["case"]["prior_payment_reference"] == concise["prior_payment_reference"]
