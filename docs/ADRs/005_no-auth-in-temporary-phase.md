# ADR-005: No authentication in temporary phase

**Status:** Accepted
**Date:** 2026-07
**Decided by:** team

## Context

The temporary development profile is synthetic and unvalidated. Adding authentication (OAuth, JWT, RBAC) introduces complexity — secret management, token validation, user sessions — that does not serve the current goal of proving the evaluation pipeline and audit trail.

## Decision

Do not implement authentication, authorization, or user management in the temporary phase. All API endpoints are open. The `DEMO_REVIEWER` label used in the Control Deck is a fixed synthetic string, not a real user role. Any future authentication requirement will be introduced as a new architectural decision when a validated real workflow exists.

## Consequences

- **Pros:** Faster development; no secret-management burden during the hackathon sprint; the demo judge can interact with the API without credentials, matching the challenge requirement of "without an account."
- **Cons:** The temporary API must never be deployed to a shared or public environment without a protective barrier; real data must not be submitted.
- **Rule:** Never commit secrets, API keys, or real personal data to the repository. `.env` is git-ignored by design.
