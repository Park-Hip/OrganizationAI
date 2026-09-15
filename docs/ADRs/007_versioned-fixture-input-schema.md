# ADR-007: Versioned fixture-input schema with deterministic expansion

**Status:** Accepted
**Date:** 2026-09-15
**Decided by:** project lead

## Context

The canonical Policy Forge fixtures (`test_cases.json`, `verify_cases.json`) are concise scenario inputs, not full reimbursement envelopes.
Independent review showed that the raw fixtures cannot be validated against the canonical envelope schema and have no specified mapping into a full case.
Every service (policy engine, harness, Verify path, and persistence integration) needs the same full case contract.

## Decision

Keep concise synthetic scenario fixtures, and introduce a versioned fixture-input schema plus a deterministic fixture expander that produces a full reimbursement envelope.
The expander is data-driven; it must not branch on fixture ID, title, or free-text prose.

## Consequences

The policy/harness owner has an explicit input contract while all services share the full case contract.
Malformed structural inputs fail before evaluation rather than being silently reinterpreted.
Fixture expansion stays deterministic and independent of fixture identity or prose, which keeps the harness unbiased.
