"""The canonical envelope and fixture schemas are valid JSON Schemas."""

from __future__ import annotations

import jsonschema
from _artifacts import FIXTURE_SCHEMA, REIMBURSEMENT_SCHEMA


def test_reimbursement_schema_is_a_valid_draft_2020_12_schema() -> None:
    draft = jsonschema.Draft202012Validator.META_SCHEMA
    jsonschema.Draft202012Validator.check_schema(REIMBURSEMENT_SCHEMA)
    validator = jsonschema.Draft202012Validator(draft)
    assert validator.is_valid(REIMBURSEMENT_SCHEMA)


def test_fixture_schema_is_a_valid_draft_2020_12_schema() -> None:
    jsonschema.Draft202012Validator.check_schema(FIXTURE_SCHEMA)


def test_reimbursement_schema_declares_contract_version() -> None:
    assert REIMBURSEMENT_SCHEMA["title"] == (
        "OrganizationAI Reimbursement Processing Envelope (v1.2.0)"
    )
