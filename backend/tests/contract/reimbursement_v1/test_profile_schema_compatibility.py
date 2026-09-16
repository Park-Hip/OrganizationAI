"""The YAML organization_profile is schema-compatible and complete."""

from __future__ import annotations

import jsonschema
import pytest
from _artifacts import PROFILE, REIMBURSEMENT_SCHEMA

pytestmark = pytest.mark.v1_contract


def _organization_profile_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        {"$ref": "#/$defs/OrganizationProfile", "$defs": REIMBURSEMENT_SCHEMA["$defs"]},
        format_checker=jsonschema.FormatChecker(),
    )


def test_default_profile_validates_against_organization_profile_schema() -> None:
    errors = list(_organization_profile_validator().iter_errors(PROFILE))
    assert not errors, [error.message for error in errors]


def test_default_profile_remains_synthetic_and_unactivated() -> None:
    assert PROFILE["parent_organization"] == "TO_BE_CONFIRMED"
    assert PROFILE["accounting_regime"] == "TO_BE_CONFIRMED"
    assert PROFILE["owner"] == "TO_BE_CONFIRMED"
    assert PROFILE["effective_date"] is None


def test_default_profile_separates_policy_and_legal_prohibitions() -> None:
    assert "alcohol" in PROFILE["prohibited_categories"]
    assert "illegal_goods" not in PROFILE["prohibited_categories"]
    assert "illegal_goods" in PROFILE["legally_prohibited_categories"]


def test_default_profile_has_required_roles_and_authority_configuration() -> None:
    roles = PROFILE["roles"]
    assert roles["requester"] == "MEMBER"
    assert roles["approver_over_threshold"] == "CLUB_CHAIR"
    assert PROFILE["authority_threshold_operator"] == "greater_than"
    assert PROFILE["routine_processing_max_vnd"] == 5000000
