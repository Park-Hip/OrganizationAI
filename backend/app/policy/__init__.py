"""Policy layer for the OrganizationalAI backend.

Layer 0 freezes the sole temporary development profile. No evaluator lives
here yet.
"""

from app.policy.profile import TMP_DEV_001_PROFILE

__all__ = ["TMP_DEV_001_PROFILE"]
