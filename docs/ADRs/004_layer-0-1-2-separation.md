# ADR-004: Three-layer domain evaluation architecture

**Status:** Accepted
**Date:** 2026-07
**Decided by:** team

## Context

The evaluator needs to transform raw client input into a clean decision, but the transformation logic (normalization), the decision logic (evaluation), and the data shapes (domain models) are each independently testable and may evolve at different rates. Mixing them together makes isolated testing impossible and changes in one layer ripple into others.

## Decision

Split the core logic into three layers with strict import direction:

- **Layer 0** (`app/domain/`): frozen enums and Pydantic record shapes. No imports from any other app module.
- **Layer 1** (`app/policy/normalization.py`): pure function that converts `CaseSubmission` to `NormalizedCase`. Imports only from Layer 0.
- **Layer 2** (`app/policy/evaluator.py`): pure function `evaluate_case()` that accepts a `NormalizedCase` and an injected `TemporaryProfile`. Imports only from Layer 0 and Layer 1.

The application layer (`app/application/`) coordinates between persistence and policy. The API layer (`app/api/`) handles HTTP only.

## Consequences

- **Pros:** Each layer can be unit-tested in isolation without starting FastAPI or a database; replacing the evaluator (e.g. with an LLM-based one) only requires a Layer 2 swap; the contract is machine-verifiable through the frozen model tests in `tests/contract/`.
- **Cons:** Slightly more files than a single-module design; new contributors need to understand the layer boundary before contributing to policy.
- **Key invariant:** nothing in a lower layer may import from a higher layer. Build tools or static analysis can enforce this if needed.
