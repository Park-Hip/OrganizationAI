"""Frozen Layer 0 domain enums.

Every enum subclasses ``str`` and ``Enum`` so serialized values are stable and
unambiguous. The value each member exposes is its single source of truth for
any later transport, normalization, or persistence layer.
"""

from __future__ import annotations

# The frozen contract intentionally subclasses ``str`` and ``Enum`` directly
# rather than ``enum.StrEnum`` to make the serialization guarantee explicit.
# ruff: noqa: UP042
from enum import Enum


class TemporaryCategory(str, Enum):
    """Temporary category labels that do not claim any real category."""

    TEST_ALLOWED = "TEST_ALLOWED"
    TEST_BLOCKED = "TEST_BLOCKED"


class EvidenceStatus(str, Enum):
    """A requester declaration about evidence existence, not a receipt check."""

    PRESENT = "PRESENT"
    NOT_PROVIDED = "NOT_PROVIDED"


class DecisionOutcome(str, Enum):
    """The four temporary decision results."""

    AUTO_APPROVED = "AUTO_APPROVED"
    MISSING_FACT = "MISSING_FACT"
    OUT_OF_POLICY = "OUT_OF_POLICY"
    AUTHORITY_EXCEEDED = "AUTHORITY_EXCEEDED"


class TemporaryRuleId(str, Enum):
    """Typed evidence for the single first-applicable rule the evaluator applies."""

    TMP_REQ_01 = "TMP-REQ-01"
    TMP_CAT_01 = "TMP-CAT-01"
    TMP_EVD_01 = "TMP-EVD-01"
    TMP_AUT_01 = "TMP-AUT-01"
    TMP_AUT_02 = "TMP-AUT-02"


class ProfileSource(str, Enum):
    """Temporary provenance marker for the sole development profile."""

    TEMPORARY_DEVELOPMENT = "TEMPORARY_DEVELOPMENT"


class DataClass(str, Enum):
    """Temporary data-class provenance marker."""

    SYNTHETIC = "SYNTHETIC"


class WorkflowValidationStatus(str, Enum):
    """Temporary workflow-validation provenance marker."""

    UNVALIDATED = "UNVALIDATED"
