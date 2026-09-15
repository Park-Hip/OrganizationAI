# ADR-002: Immutable append-only audit ledger

**Status:** Accepted
**Date:** 2026-07
**Decided by:** team

## Context

The Escalation Referee challenge requires judges to verify that every decision is inspectable, reproducible, and tamper-evident. A mutable log or a simple SQL table with UPDATE/DELETE would allow a past decision to change silently, breaking auditability.

## Decision

Store all audit events in an append-only table enforced by database-level `BEFORE UPDATE OR DELETE` triggers. Each trace writes its case snapshot, decision snapshot, and initial three events in a single transaction. Control commands append one additional event. No row is ever modified after insertion.

## Consequences

- **Pros:** Tamper-evidence at the database layer, not just in code; replay of the event chain is deterministic; rollback is impossible without a full database reset.
- **Cons:** Resetting data requires a destructive migration, not an API call (intentionally); the schema is slightly more complex due to the trigger and composite unique constraint on `(trace_id, idempotency_key)`.
- **Future consideration:** If long-term archival or GDPR right-to-erasure becomes a requirement, a separate archival path will be needed rather than trying to delete from the live table.
