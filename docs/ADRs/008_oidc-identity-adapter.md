# ADR-008: OIDC identity adapter with synthetic test identities

**Status:** Accepted
**Date:** 2026-09-15
**Decided by:** project lead

## Context

The reimbursement v1 path requires a server-derived authenticated actor and authorization controls.
Production direction is an approved OIDC provider, but committing real credentials, user data, or token secret management now would be inappropriate.
ADR-005 continues to keep the legacy temporary endpoints unauthenticated; this ADR scopes only the new reimbursement path.

## Decision

Implement authentication behind an approved OIDC provider adapter under `app/security/`, so the application depends on a stable authenticated-actor boundary rather than a specific provider.
Use synthetic test identities only during development.
Do not commit real credentials, storage services, or personal data to the repository.

## Consequences

The security owner can build a stable boundary without real credentials, storage, or personal data.
The server derives actor identity and roles; a client cannot select them.
Legacy `TMP-DEV-001` endpoints remain unauthenticated synthetic history under ADR-005.
Real operation requires selecting and approving the OIDC provider during the activation gate.