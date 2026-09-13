"""Policy layer for the OrganizationalAI backend.

Layer 0 freezes the sole temporary development profile, and Layer 1 adds
normalization. Layer 2 adds a pure evaluator.

The temporary profile and pure evaluator are intentionally independent from
HTTP, persistence, settings, and external services.
"""

from app.policy.evaluator import evaluate_case
from app.policy.profile import TMP_DEV_001_PROFILE

__all__ = ["TMP_DEV_001_PROFILE", "evaluate_case"]
