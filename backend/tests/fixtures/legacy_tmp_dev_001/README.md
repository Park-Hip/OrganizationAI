# Legacy TMP-DEV-001 synthetic regression fixture

This directory holds the historical synthetic test corpus for the legacy `TMP-DEV-001` temporary implementation.
It is preserved as synthetic historical coverage so the existing regression suite stays runnable.
It is not a reimbursement corpus and must not be treated as one.

Every row in `temporary_case_corpus.csv` carries these markers:

| Marker | Value |
| --- | --- |
| `profile_id` | `TMP-DEV-001` |
| `profile_source` | `TEMPORARY_DEVELOPMENT` |
| `data_class` | `SYNTHETIC` |
| `workflow_validation_status` | `UNVALIDATED` |

The values `TEST_ALLOWED`, `TEST_BLOCKED`, and `1000` are arbitrary development constants, not club policy.
The current Policy Forge reimbursement corpus lives separately in `policy-forge-baseline/` and must never be mixed with this fixture.
