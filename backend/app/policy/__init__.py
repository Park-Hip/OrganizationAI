"""Policy packages for historical and reimbursement v1 processing.

Historical TMP-DEV-001 exports remain lazy so the reimbursement v1 policy path
can be imported without loading a legacy evaluator or temporary profile.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_LEGACY_EXPORTS = {
    "TMP_DEV_001_PROFILE": ("app.policy.profile", "TMP_DEV_001_PROFILE"),
    "evaluate_case": ("app.policy.evaluator", "evaluate_case"),
}


def __getattr__(name: str) -> Any:
    """Load a historical export only when legacy callers request it."""
    try:
        module_name, attribute_name = _LEGACY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error
    return getattr(import_module(module_name), attribute_name)


__all__ = list(_LEGACY_EXPORTS)
