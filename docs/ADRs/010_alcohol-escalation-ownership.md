# ADR-010: Alcohol escalation ownership and handoff

**Status:** Accepted
**Date:** 2026-09-15
**Decided by:** project lead

## Context

The policy escalates alcohol category cases, and `TC-O01` expects a specific handoff.
Independent review found that the alcohol-specific rule can be shadowed by the generic prohibited-category rule, and the two-approver wording is not representable as a single structured escalation.

## Decision

For the synthetic prototype, `CLUB_CHAIR` is the one escalation addressee for alcohol cases, and the required `PARENT_ADVISOR` consultation is an auditable prerequisite rather than a second agent decision.
If an approved parent organization later requires sequential or joint approval, that becomes a new profile/contract version before real activation.

## Consequences

The current single-escalation contract can represent alcohol cases, and `TC-O01` becomes testable.
Making the alcohol path mutually exclusive with the generic prohibited-category path remains a SETUP-02 contract repair, but the escalation ownership is frozen here.
