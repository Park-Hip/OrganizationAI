"""API route and error-envelope tests for the temporary decision-trace endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NoReturn, cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.api.routes.temporary_history as routes_module
import app.application.temporary_history as service_module
from app.api.schemas.temporary_history import (
    DecisionReadModel,
    ProvenanceReadModel,
    TraceReadModel,
)
from app.domain.models import CaseSubmission

pytestmark = pytest.mark.unit

_ENDPOINT = "/api/temporary/decision-traces"
_TRACE_ID = UUID("00000000-0000-0000-0000-000000000001")
_EXPECTED_PROVENANCE = {
    "profile_id": "TMP-DEV-001",
    "profile_source": "TEMPORARY_DEVELOPMENT",
    "data_class": "SYNTHETIC",
    "workflow_validation_status": "UNVALIDATED",
}


def _valid_body(case_id: str = "TMP-API-01") -> dict[str, object]:
    return {
        "case_id": case_id,
        "submitted_at": "2030-01-01T09:00:00Z",
        "requester_role": "TEST_REQUESTER",
        "purpose": "Synthetic allowed expense",
        "expense": {
            "category": "TEST_ALLOWED",
            "description": "Synthetic materials line",
            "amount_vnd": 999,
            "expense_date": "2030-01-01",
            "evidence_status": "PRESENT",
        },
    }


def _canned_trace() -> TraceReadModel:
    now = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    return TraceReadModel(
        temporary_notice=service_module.TEMPORARY_NOTICE,
        trace_id=_TRACE_ID,
        recorded_at=now,
        provenance=ProvenanceReadModel(
            profile_id="TMP-DEV-001",
            profile_source="TEMPORARY_DEVELOPMENT",
            data_class="SYNTHETIC",
            workflow_validation_status="UNVALIDATED",
        ),
        submission={"case_id": "TMP-API-01"},
        facts_used={"purpose": "Synthetic allowed expense"},
        decision=DecisionReadModel(
            outcome="AUTO_APPROVED",
            applied_rule_id="TMP-AUT-01",
            reason="Approved under temporary development profile; no payment was made.",
            question=None,
            profile_id="TMP-DEV-001",
            profile_snapshot={"profile_id": "TMP-DEV-001"},
            decided_at=now,
        ),
        events=[],
        control_state="AUTO_APPROVED",
    )


def test_post_returns_201_with_location_and_temporary_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        routes_module,
        "submit_trace",
        lambda submission, session: _canned_trace(),
    )

    response = client.post(_ENDPOINT, json=_valid_body())

    assert response.status_code == 201
    assert response.headers["location"] == f"{_ENDPOINT}/{_TRACE_ID}"
    payload = response.json()
    assert payload["trace_id"] == str(_TRACE_ID)
    assert payload["temporary_notice"] == service_module.TEMPORARY_NOTICE
    assert payload["provenance"]["data_class"] == "SYNTHETIC"
    assert payload["provenance"]["workflow_validation_status"] == "UNVALIDATED"


def test_get_returns_the_stored_trace(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routes_module,
        "read_trace",
        lambda trace_id, session: _canned_trace(),
    )

    response = client.get(f"{_ENDPOINT}/{_TRACE_ID}")

    assert response.status_code == 200
    assert response.json()["trace_id"] == str(_TRACE_ID)


def test_get_unknown_trace_returns_404_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_not_found(trace_id: UUID, session: Session) -> NoReturn:
        raise service_module.TraceNotFoundError(trace_id)

    monkeypatch.setattr(routes_module, "read_trace", _raise_not_found)

    response = client.get(f"{_ENDPOINT}/{_TRACE_ID}")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "TRACE_NOT_FOUND"
    assert payload["temporary_notice"] == service_module.TEMPORARY_NOTICE
    assert payload["provenance"] == _EXPECTED_PROVENANCE


def test_post_duplicate_case_returns_409_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_duplicate(submission: CaseSubmission, session: Session) -> NoReturn:
        raise service_module.TraceAlreadyRecordedError(submission.case_id)

    monkeypatch.setattr(routes_module, "submit_trace", _raise_duplicate)

    response = client.post(_ENDPOINT, json=_valid_body("TMP-API-DUP"))

    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "CASE_ID_ALREADY_RECORDED"
    assert payload["temporary_notice"] == service_module.TEMPORARY_NOTICE
    assert payload["provenance"] == _EXPECTED_PROVENANCE


def _with_extra_field(field: str, value: object, *, in_expense: bool = False) -> dict[str, object]:
    body = _valid_body()
    if in_expense:
        expense = dict(cast("dict[str, object]", body["expense"]))
        expense[field] = value
        body["expense"] = expense
    else:
        body[field] = value
    return body


def _with_case_id(case_id: str) -> dict[str, object]:
    body = _valid_body()
    body["case_id"] = case_id
    return body


@pytest.mark.parametrize(
    "body",
    [
        _with_extra_field("profile_id", "TEMPORARY_DEVELOPMENT"),
        _with_extra_field("profile_source", "TEMPORARY_DEVELOPMENT"),
        _with_extra_field("data_class", "SYNTHETIC"),
        _with_extra_field("workflow_validation_status", "UNVALIDATED"),
        _with_extra_field("vendor", "Synthetic Vendor"),
        _with_extra_field("bank_account", "123456789"),
        _with_extra_field("receipt_file", "not-supported.png", in_expense=True),
        _with_case_id(" "),
    ],
)
def test_unapproved_fields_are_rejected_with_422(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.post(_ENDPOINT, json=body)

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "INPUT_INVALID"
    assert payload["error"]["message"] == "The submitted temporary case is invalid."
    assert payload["temporary_notice"] == service_module.TEMPORARY_NOTICE
    assert payload["provenance"] == _EXPECTED_PROVENANCE
