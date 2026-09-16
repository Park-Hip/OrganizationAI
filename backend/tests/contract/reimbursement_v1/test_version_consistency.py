"""One declared policy/profile/schema/corpus version across every artifact."""

from __future__ import annotations

from _artifacts import (
    FIXTURE_SCHEMA,
    POLICY_VERSION,
    PROFILE,
    REIMBURSEMENT_SCHEMA,
    TEST_CASES,
    VERIFY_CASES,
)

CONTRACT_VERSION = "1.2.0"


def test_policy_version_is_contract_version() -> None:
    assert POLICY_VERSION == CONTRACT_VERSION


def test_profile_versions_match_policy() -> None:
    assert PROFILE["profile_version"] == CONTRACT_VERSION
    assert PROFILE["policy_version"] == CONTRACT_VERSION


def test_corpus_versions_match() -> None:
    assert TEST_CASES["policy_version"] == CONTRACT_VERSION
    assert TEST_CASES["profile_version"] == CONTRACT_VERSION
    assert TEST_CASES["schema_version"] == CONTRACT_VERSION
    assert VERIFY_CASES["policy_version"] == CONTRACT_VERSION


def test_schema_titles_carry_contract_version() -> None:
    assert "v1.2.0" in REIMBURSEMENT_SCHEMA["title"]
    assert "v1.2.0" in FIXTURE_SCHEMA["title"]
