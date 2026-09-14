"""API route and error-envelope tests for the temporary Control Deck endpoint."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NoReturn
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import app.api.routes.control_deck as routes_module
import app.application.control_deck as service_module
from app.api.schemas.temporary_history import (
    DecisionReadModel,
    ProvenanceReadModel,
    TraceReadModel,
)
from app.application.temporary_history import TEMPORARY_NOTICE, TraceNotFoundError
from app.domain.control import ControlCommand, DemoDisposition

_TRACE_ID = UUID("00000000-0000-0000-0000-000000000001")
_ENDPOINT = f"/api/temporary/decision-traces/{_TRACE_ID}/controls"
_EXPECTED_PROVENANCE = {
    "profile_id": "TMP-DEV-001",
    "profile_source": "TEMPORARY_DEVELOPMENT",
    "data_class": "SYNTHETIC",
    "workflow_validation_status": "UNVALIDATED",
}


def _canned_trace(control_state: str = "PAUSED") -> TraceReadModel:
    now = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    return TraceReadModel(
        temporary_notice=TEMPORARY_NOTICE,
        trace_id=_TRACE_ID,
        recorded_at=now,
        provenance=ProvenanceReadModel(**_EXPECTED_PROVENANCE),
        submission={"case_id": "TMP-CTRL-01"},
        facts_used={"purpose": "Synthetic out-of-policy expense"},
        decision=DecisionReadModel(
            outcome="OUT_OF_POLICY",
            applied_rule_id="TMP-CAT-01",
            reason="Synthetic out-of-policy expense.",
            question="Do you authorize this temporary exception?",
            profile_id="TMP-DEV-001",
            profile_snapshot={"profile_id": "TMP-DEV-001"},
            decided_at=now,
        ),
        events=[],
        control_state=control_state,
    )


def _body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {"command": "pause", "reason": "synthetic control reason"}
    body.update(overrides)
    return body


def test_post_control_returns_200_with_temporary_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(routes_module, "submit_control", lambda **kwargs: _canned_trace())

    response = client.post(_ENDPOINT, json=_body())

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_id"] == str(_TRACE_ID)
    assert payload["control_state"] == "PAUSED"
    assert payload["temporary_notice"] == TEMPORARY_NOTICE
    assert payload["provenance"] == _EXPECTED_PROVENANCE


def test_post_control_unknown_trace_returns_404_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_not_found(**kwargs: object) -> NoReturn:
        raise TraceNotFoundError(_TRACE_ID)

    monkeypatch.setattr(routes_module, "submit_control", _raise_not_found)

    response = client.post(_ENDPOINT, json=_body())

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "TRACE_NOT_FOUND"
    assert payload["temporary_notice"] == TEMPORARY_NOTICE
    assert payload["provenance"] == _EXPECTED_PROVENANCE


def test_post_control_illegal_action_returns_409_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_illegal(**kwargs: object) -> NoReturn:
        raise service_module.IllegalControlActionError(
            _TRACE_ID, "PAUSED", "pause", "already paused"
        )

    monkeypatch.setattr(routes_module, "submit_control", _raise_illegal)

    response = client.post(_ENDPOINT, json=_body())

    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "ILLEGAL_CONTROL_ACTION"
    assert payload["temporary_notice"] == TEMPORARY_NOTICE
    assert payload["provenance"] == _EXPECTED_PROVENANCE


def test_post_control_idempotency_conflict_returns_409_envelope(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise_conflict(**kwargs: object) -> NoReturn:
        raise service_module.ControlIdempotencyConflictError(_TRACE_ID, "key-1")

    monkeypatch.setattr(routes_module, "submit_control", _raise_conflict)

    response = client.post(_ENDPOINT, json=_body(idempotency_key="key-1"))

    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "CONTROL_IDEMPOTENCY_CONFLICT"
    assert payload["provenance"] == _EXPECTED_PROVENANCE


@pytest.mark.parametrize(
    "body",
    [
        _body(command="dispatch"),  # unknown command token
        _body(reason="   "),  # blank reason
        _body(reason="synthetic\u0000reason"),
        _body(idempotency_key="x" * 256),
        _body(idempotency_key="key\u0000one"),
        _body(reason="synthetic reason", actor="DEMO_REVIEWER"),  # unapproved actor field
        _body(reason="synthetic reason", profile_id="TMP-DEV-001"),
        _body(reason="synthetic reason", disposition="DEMO_ALLOW"),  # disposition without review
        _body(
            command="record_demo_review", reason="synthetic reason"
        ),  # review without disposition
        _body(reason="synthetic reason", real_role="Treasurer"),
    ],
)
def test_malformed_commands_are_rejected_with_422(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.post(_ENDPOINT, json=body)

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "INPUT_INVALID"
    assert payload["provenance"] == _EXPECTED_PROVENANCE


def test_record_demo_review_passes_through_the_disposition(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def _capture(**kwargs: object) -> TraceReadModel:
        captured.update(kwargs)
        return _canned_trace("DEMO_REVIEWED")

    monkeypatch.setattr(routes_module, "submit_control", _capture)

    response = client.post(
        _ENDPOINT,
        json={
            "command": "record_demo_review",
            "reason": "synthetic review",
            "disposition": "DEMO_DECLINE",
            "idempotency_key": "review-key-1",
        },
    )

    assert response.status_code == 200
    assert captured["trace_id"] == _TRACE_ID
    assert captured["command"] is ControlCommand.RECORD_DEMO_REVIEW
    assert captured["disposition"] is DemoDisposition.DEMO_DECLINE
    assert captured["idempotency_key"] == "review-key-1"
    assert response.json()["control_state"] == "DEMO_REVIEWED"
