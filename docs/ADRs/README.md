# Architectural Decision Records

ADR files record *why* a structural choice was made. They live alongside the numbered documentation chain but are not part of it — they track engineering decisions, not product contracts.

## How to write an ADR

Each file follows this short template:

```markdown
# ADR-N: title

**Status:** Proposed | Accepted | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Decided by:** <author/team>

## Context
What problem or situation prompted this decision?

## Decision
What did we decide to do?

## Consequences
What follows from this decision? What are the trade-offs?
```

Keep each ADR to one page. Reference it from the code that implements it or from a numbered doc when the decision affects the product contract.

---

## Index

| ADR | Title | Status | Date |
| --- | --- | --- | --- |
| [001](001_use-fastapi-and-pydantic.md) | Use FastAPI with Pydantic v2 | Accepted | 2026-07 |
| [002](002_append-only-audit-events.md) | Immutable append-only audit ledger | Accepted | 2026-07 |
| [003](003_temporary-vs-real-profile.md) | Separate temporary profile from future real policy | Accepted | 2026-07 |
| [004](004_layer-0-1-2-separation.md) | Three-layer domain evaluation architecture | Accepted | 2026-07 |
| [005](005_no-auth-in-temporary-phase.md) | No authentication in temporary development | Accepted | 2026-07 |

---

## Linking ADRs

When a numbered document (e.g. `04_reimbursement_system_contract.md`) records the *what*, reference the ADR that records the *why*:

```markdown
See [ADR-002](002_append-only-audit-events.md) for the reasoning behind immutable audit events.
```

When code makes a non-obvious structural choice, add a one-line comment linking to the ADR:

```python
# See ADR-003: profile provenance markers separate temporary from real policy.
```
