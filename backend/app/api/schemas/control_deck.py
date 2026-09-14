"""Request schema for the temporary Control Deck command endpoint."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.control import ControlCommand, DemoDisposition


class ControlCommandRequest(BaseModel):
    """One synthetic control command with a mandatory non-blank reason.

    ``disposition`` is required exactly for ``record_demo_review`` and rejected
    for every other command, so the transport layer cannot smuggle a review
    resolution into a pause, resume, or compensation request.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: ControlCommand
    reason: str
    disposition: DemoDisposition | None = None
    idempotency_key: str | None = Field(default=None, max_length=255)

    @field_validator("reason")
    @classmethod
    def _require_non_blank_reason(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be blank")
        if "\x00" in value:
            raise ValueError("reason must not contain NUL characters")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def _require_non_blank_key(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("idempotency_key must not be blank")
        if value is not None and "\x00" in value:
            raise ValueError("idempotency_key must not contain NUL characters")
        return value

    @model_validator(mode="after")
    def _disposition_matches_command(self) -> ControlCommandRequest:
        if self.command is ControlCommand.RECORD_DEMO_REVIEW:
            if self.disposition is None:
                raise ValueError("record_demo_review requires a disposition")
        elif self.disposition is not None:
            raise ValueError("disposition is only valid with record_demo_review")
        return self
