# ADR-009: Metadata-only evidence boundary

**Status:** Accepted
**Date:** 2026-09-15
**Decided by:** project lead

## Context

The system contract defines an evidence record as id, type, file hash, readability, and verification state.
It does not prescribe file-storage technology or an OCR vendor.
Introducing a real receipt store or OCR vendor before real-operation configuration would risk committing real data or locking in an unapproved vendor.

## Decision

Keep evidence to metadata, hash, and reference only.
Do not select a receipt store or OCR vendor yet.
Expose the evidence boundary as an approved adapter to be implemented later behind the same metadata contract.

## Consequences

No real receipt, identity, vendor, bank, or token content is committed.
The policy layer depends only on hash/reference plus verification state, keeping evaluation reproducible.
File storage and OCR selection are deferred to the real-operation activation gate.