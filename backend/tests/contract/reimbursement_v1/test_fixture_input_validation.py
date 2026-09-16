"""Every concise fixture input validates; malformed structure fails early."""

from __future__ import annotations

from copy import deepcopy

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


def test_expense_cannot_combine_single_line_and_itemized_forms() -> None:
    ambiguous = {
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
    assert list(_validator().iter_errors(ambiguous))


def test_itemized_expense_cannot_carry_single_line_scalars() -> None:
    base = {
        "flow_type": "MEMBER_PAID",
        "expense": {
            "items": [
                {
                    "vendor": "V-SYN-001",
                    "transaction_date": "2026-08-01",
                    "purpose_code": "print",
                    "category": "printing",
                    "amount_vnd": 6000000,
                }
            ]
        },
        "duplicate_check": "CLEAR",
    }
    scalars = {
        "vendor": "V-SYN-001",
        "transaction_date": "2026-08-01",
        "purpose_code": "print",
        "payment_method": "CASH",
    }
    for key, value in scalars.items():
        hybrid = deepcopy(base)
        hybrid["expense"][key] = value
        errors = list(_validator().iter_errors(hybrid))
        assert errors, key


def test_unknown_missing_fact_is_rejected() -> None:
    unknown_fact = {
        "flow_type": "MEMBER_PAID",
        "expense": {"total_vnd": 850000, "category": "printing"},
        "evidence": {"missing_facts": ["invoice_number"]},
        "duplicate_check": "CLEAR",
    }
    assert list(_validator().iter_errors(unknown_fact))


def test_cash_expenses_cannot_claim_non_cash_verification() -> None:
    single_line_cash = {
        "flow_type": "MEMBER_PAID",
        "expense": {
            "total_vnd": 5000000,
            "category": "printing",
            "payment_method": "CASH",
        },
        "evidence": {"non_cash_verified": True},
        "duplicate_check": "CLEAR",
    }
    mixed_payment_items = {
        "flow_type": "MEMBER_PAID",
        "expense": {
            "items": [
                {
                    "vendor": "V-SYN-001",
                    "transaction_date": "2026-08-01",
                    "purpose_code": "print",
                    "category": "printing",
                    "amount_vnd": 2500000,
                    "payment_method": "BANK_TRANSFER",
                },
                {
                    "vendor": "V-SYN-002",
                    "transaction_date": "2026-08-01",
                    "purpose_code": "print",
                    "category": "printing",
                    "amount_vnd": 2500000,
                    "payment_method": "CASH",
                },
            ]
        },
        "evidence": {"non_cash_verified": True},
        "duplicate_check": "CLEAR",
    }

    assert list(_validator().iter_errors(single_line_cash))
    assert list(_validator().iter_errors(mixed_payment_items))


def test_member_paid_fixture_cannot_include_advance_evidence() -> None:
    member_paid_with_advance = {
        "flow_type": "MEMBER_PAID",
        "expense": {"total_vnd": 850000, "category": "printing"},
        "evidence": {"advance_reference": "ADV-SYN-001"},
        "duplicate_check": "CLEAR",
    }
    assert list(_validator().iter_errors(member_paid_with_advance))


def test_non_cash_verification_requires_payment_proof() -> None:
    contradictory_evidence = {
        "flow_type": "MEMBER_PAID",
        "expense": {
            "total_vnd": 850000,
            "category": "printing",
            "payment_method": "BANK_TRANSFER",
        },
        "evidence": {"payment_proof": False, "non_cash_verified": True},
        "duplicate_check": "CLEAR",
    }
    assert list(_validator().iter_errors(contradictory_evidence))


def test_budget_cannot_be_an_empty_object() -> None:
    empty_budget = {
        "flow_type": "MEMBER_PAID",
        "expense": {"total_vnd": 850000, "category": "printing"},
        "budget": {},
        "duplicate_check": "CLEAR",
    }
    assert list(_validator().iter_errors(empty_budget))
