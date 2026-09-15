# ADR-011: Relocate the legacy TMP-DEV-001 regression fixture

**Status:** Accepted
**Date:** 2026-09-15
**Decided by:** project lead

## Context

The legacy regression suite is red (`3 failed, 16 errors`) because temporary tests still look for the removed `docs/05_temporary_case_corpus.csv`.
The historical temporary material must remain runnable as synthetic coverage without being confused with the current numbered reimbursement corpus.

## Decision

Preserve temporary behavior as synthetic historical coverage, and move its corpus dependency to a clearly named test fixture under `backend/tests/fixtures/legacy_tmp_dev_001/`.
Do not restore `docs/05_temporary_case_corpus.csv`.
Do not relabel the temporary material as a reimbursement corpus.

## Consequences

The existing suite returns to health without mixing historical temporary material with the current numbered corpus.
When moved, the fixture carries explicit `TMP-DEV-001`, `SYNTHETIC`, `TEMPORARY_DEVELOPMENT`, and `UNVALIDATED` provenance.