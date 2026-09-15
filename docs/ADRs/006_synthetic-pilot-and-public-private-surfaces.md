# ADR-006: Synthetic-pilot delivery and separate public/private surfaces

**Status:** Accepted
**Date:** 2026-09-15
**Decided by:** project lead

## Context

The project documents deliberately separate a buildable pilot from authorization to process real financial information.
`parent_organization` and `accounting_regime` remain `TO_BE_CONFIRMED`, so no production roles, thresholds, retention rules, or approval authorities may be invented.
At the same time, Challenge A wants an unauthenticated public demo, while the reimbursement contract requires authentication before any shared or real-data endpoint.
The competition rubric also uses `MISSING_FACT` and `AUTHORITY_EXCEEDED`, while the adopted Policy Forge model uses `FACT_UNKNOWN` and `AUTHORITY_REQUIRED`.

## Decision

Remain synthetic-pilot-only: `parent_organization` and `accounting_regime` stay `TO_BE_CONFIRMED`, and real intake stays disabled until the real-operation gate is complete.
Ship two intentionally separate surfaces: a public, unauthenticated Verify surface that consumes only synthetic fixtures, and a private authenticated reimbursement surface whose real intake remains disabled.
Adopt a tested public/rubric vocabulary mapping at the public Verify boundary: `MISSING_FACT` maps to `FACT_UNKNOWN`, and `AUTHORITY_EXCEEDED` maps to `AUTHORITY_REQUIRED`.
Do not rename the Policy Forge internal enums repository-wide.

## Consequences

No developer invents production roles, thresholds, retention, or organization approval.
Demo terminology drift is eliminated by an explicit tested mapping rather than a broad rename.
The public surface stays visibly synthetic, and the authenticated surface stays visibly gated until activation.
