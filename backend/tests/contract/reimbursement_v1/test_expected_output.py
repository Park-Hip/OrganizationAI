"""Exact expected-output assertions and full rule-coverage matrix."""

from __future__ import annotations

from typing import Any

from _artifacts import POLICY_VERSION, PROFILE, RULES, TEST_CASES, VERIFY_CASES
from _expand import _declared_total, materialize_envelope


def _terminal_rule_ids(case: dict[str, Any]) -> list[str]:
    expected_processing = case["expected"].get("processing_result")
    if expected_processing is None:
        return []
    return [
        rule_id
        for rule_id in case["expected"].get("triggered_rule_ids", [])
        if (RULES[rule_id].get("result") or {}).get("processing_result") == expected_processing
    ]


def test_every_expected_rule_id_is_a_real_testable_rule() -> None:
    for case in TEST_CASES["cases"]:
        for rule_id in case["expected"].get("triggered_rule_ids", []):
            assert rule_id in RULES, (case["id"], rule_id)
            assert RULES[rule_id].get("testable") is True, (case["id"], rule_id)


def test_terminal_rule_declares_the_expected_escalation() -> None:
    for case in TEST_CASES["cases"]:
        if case["expected"].get("processing_result") is None:
            continue
        terminal_ids = _terminal_rule_ids(case)
        assert terminal_ids, case["id"]
        for rule_id in terminal_ids:
            rule_result = RULES[rule_id].get("result") or {}
            assert rule_result.get("escalation_type") == case["expected"].get("escalation_type"), (
                case["id"],
                rule_id,
            )
            if case["expected"].get("addressee_role"):
                assert rule_result.get("addressee_role") == case["expected"]["addressee_role"], (
                    case["id"],
                    rule_id,
                )


def test_calculation_fields_are_arithmetically_exact() -> None:
    for case in TEST_CASES["cases"]:
        if case["expected"].get("processing_result") != "ROUTINE_PROCESSED":
            continue
        eligible = _declared_total(case["input"])
        expected = case["expected"]
        assert expected["eligible_total_vnd"] == eligible, case["id"]
        if case["input"]["flow_type"] == "MEMBER_PAID":
            assert expected["reimbursement_amount_vnd"] == eligible, case["id"]
        else:
            advance = int(case["input"]["advance_amount_vnd"])
            assert expected["amount_to_return_vnd"] == max(advance - eligible, 0), case["id"]
            assert expected["additional_payment_vnd"] == max(eligible - advance, 0), case["id"]


def test_escalation_type_is_bound_to_escalation_type_field() -> None:
    for case in TEST_CASES["cases"]:
        if case["expected"].get("processing_result") != "ESCALATED":
            continue
        envelope = materialize_envelope(case["input"], PROFILE, POLICY_VERSION, case["expected"])
        assert (
            envelope["processing_outcome"]["escalation_type"] == envelope["escalation"]["type"]
        ), case["id"]


def test_all_testable_rules_have_a_positive_fixture() -> None:
    covered = {
        rule_id
        for case in TEST_CASES["cases"]
        for rule_id in case["expected"].get("triggered_rule_ids", [])
    }
    testable = {rule_id for rule_id, rule in RULES.items() if rule.get("testable") is True}
    assert testable == covered


def test_every_rule_has_a_positive_and_boundary_or_negative_assertion() -> None:
    cases = [(case["input"], case["expected"]) for case in TEST_CASES["cases"]]

    assert any(
        input_data["expense"].get("total_vnd") == 4999999
        and expected.get("processing_result") == "ROUTINE_PROCESSED"
        for input_data, expected in cases
    )
    assert any(
        input_data["expense"].get("total_vnd") == 5000000
        and expected.get("processing_result") == "ROUTINE_PROCESSED"
        for input_data, expected in cases
    )
    assert any(
        input_data["expense"].get("total_vnd") == 5000001
        and expected.get("escalation_type") == "AUTHORITY_REQUIRED"
        for input_data, expected in cases
    )
    assert any(
        input_data.get("days_late") == 10
        and expected.get("processing_result") == "ROUTINE_PROCESSED"
        for input_data, expected in cases
    )
    assert any(
        input_data.get("days_late") == 11
        and expected.get("escalation_type") == "AUTHORITY_REQUIRED"
        for input_data, expected in cases
    )
    assert any(
        input_data["expense"].get("category") == "gift"
        and input_data.get("evidence", {}).get("prior_approval_present") is True
        and expected.get("processing_result") == "ROUTINE_PROCESSED"
        for input_data, expected in cases
    )
    assert any(
        input_data["expense"].get("category") == "gift"
        and input_data.get("evidence", {}).get("prior_approval_present") is False
        and expected.get("escalation_type") == "AUTHORITY_REQUIRED"
        for input_data, expected in cases
    )
    assert any(
        sum(item["amount_vnd"] for item in input_data["expense"].get("items", [])) == 4000000
        and expected.get("processing_result") == "ROUTINE_PROCESSED"
        for input_data, expected in cases
    )
    assert any(
        sum(item["amount_vnd"] for item in input_data["expense"].get("items", [])) == 6000000
        and expected.get("escalation_type") == "AUTHORITY_REQUIRED"
        for input_data, expected in cases
    )


def test_verify_suite_matches_full_suite_expectations() -> None:
    full = {case["id"]: case for case in TEST_CASES["cases"]}
    for verify_case in VERIFY_CASES["cases"]:
        case = full[verify_case["case_id"]]
        assert case["expected"]["processing_result"] == verify_case["expected_processing_result"]
        assert case["expected"]["escalation_type"] == verify_case["expected_escalation_type"]
        assert case["expected"]["approval_status"] == verify_case["expected_approval_status"]
        if verify_case.get("expected_addressee_role"):
            assert case["expected"]["addressee_role"] == verify_case["expected_addressee_role"]
