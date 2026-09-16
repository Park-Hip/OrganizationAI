"""Domain packages for both historical and reimbursement v1 contracts.

The historical TMP-DEV-001 exports stay available lazily for compatibility.
The lazy boundary prevents an import of ``app.domain.reimbursement`` from
loading legacy models into the v1 processing path.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_LEGACY_EXPORTS = {
    "CaseSubmission": ("app.domain.models", "CaseSubmission"),
    "DataClass": ("app.domain.enums", "DataClass"),
    "DecisionDraft": ("app.domain.models", "DecisionDraft"),
    "DecisionOutcome": ("app.domain.enums", "DecisionOutcome"),
    "EvidenceStatus": ("app.domain.enums", "EvidenceStatus"),
    "Expense": ("app.domain.models", "Expense"),
    "NormalizedCase": ("app.domain.models", "NormalizedCase"),
    "ProfileSource": ("app.domain.enums", "ProfileSource"),
    "TemporaryCategory": ("app.domain.enums", "TemporaryCategory"),
    "TemporaryProfile": ("app.domain.models", "TemporaryProfile"),
    "TemporaryRuleId": ("app.domain.enums", "TemporaryRuleId"),
    "WorkflowValidationStatus": ("app.domain.enums", "WorkflowValidationStatus"),
}


def __getattr__(name: str) -> Any:
    """Load a historical export only when legacy callers request it."""
    try:
        module_name, attribute_name = _LEGACY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error
    return getattr(import_module(module_name), attribute_name)


__all__ = list(_LEGACY_EXPORTS)
