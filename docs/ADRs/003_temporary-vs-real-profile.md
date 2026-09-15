# ADR-003: Separate temporary profile from future real policy

**Status:** Accepted
**Date:** 2026-07
**Decided by:** team

## Context

The club's real reimbursement workflow has not been validated. Building against a fake workflow risks confusing temporary code with real product behavior, especially around policy rules, category names, and monetary limits.

## Decision

Define an explicit temporary profile (`TMP-DEV-001`) with provenance markers (`TEMPORARY_DEVELOPMENT`, `SYNTHETIC`, `UNVALIDATED`) that are included in every persisted record and every business-response envelope. The real policy uses a different profile ID, source, and version. The migration boundary in `docs/04_reimbursement_system_contract.md` defines how temporary records remain historical during replacement.

## Consequences

- **Pros:** Any stored temporary trace is self-documenting — a judge or auditor can tell at a glance that it is synthetic; accidental deployment of temporary policy as real policy is prevented by the marker contract; the migration path is explicit rather than implicit.
- **Cons:** Every API response carries extra provenance fields that will be removed for the real product, requiring a future cleanup pass.
- **Rule:** Never copy `TEST_ALLOWED`, `TEST_BLOCKED`, or the value `1000` into a real club policy.
