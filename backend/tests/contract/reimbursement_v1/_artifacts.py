"""Loader for the Policy Forge contract artifacts.

Pure stdlib + PyYAML. This module is test-support only; it never imports the
legacy application and never implements policy evaluation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[3]
REPOSITORY_ROOT = BACKEND_ROOT.parent
POLICY_FORGE = REPOSITORY_ROOT / "policy-forge-baseline"

SCHEMA_PATH = POLICY_FORGE / "reimbursement.schema.json"
FIXTURE_SCHEMA_PATH = POLICY_FORGE / "reimbursement-fixture.schema.json"
POLICY_PATH = POLICY_FORGE / "policy_rules.yaml"
TEST_CASES_PATH = POLICY_FORGE / "test_cases.json"
VERIFY_CASES_PATH = POLICY_FORGE / "verify_cases.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


REIMBURSEMENT_SCHEMA: dict[str, Any] = load_json(SCHEMA_PATH)
FIXTURE_SCHEMA: dict[str, Any] = load_json(FIXTURE_SCHEMA_PATH)
POLICY: dict[str, Any] = load_yaml(POLICY_PATH)
TEST_CASES: dict[str, Any] = load_json(TEST_CASES_PATH)
VERIFY_CASES: dict[str, Any] = load_json(VERIFY_CASES_PATH)

PROFILE: dict[str, Any] = POLICY["organization_profile"]
POLICY_VERSION: str = POLICY["policy"]["version"]
RULES: dict[str, dict[str, Any]] = {rule["id"]: rule for rule in POLICY["rules"]}
