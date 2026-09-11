# Measurement and Risk Log

## Document control

**Status:** Proposed provisional baseline. Records risks, mitigations, and the handoff gate for the Policy Forge documentation foundation.

**Owner:** Project lead and QA.

## Measurement plan

User-impact measurement, deployment evidence, final slides, video, and competition-readiness claims are **out of scope** for this provisional baseline.

| Outcome | Method | Baseline | Prototype measure | Limitation | Owner |
| --- | --- | --- | --- | --- | --- |
| (Not started) | User-impact measurement is deferred. | No baseline exists yet. | No prototype measure exists yet. | Out of scope until real users and a deployed prototype exist. | Project lead |

## Risk register

| Risk | Likelihood | Impact | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Starter categories and thresholds may not match actual club practice. | High | Medium | Policy-owner review before confirming categories or values; label starter categories as proposed and synthetic everywhere. | Policy & scenario owner | Open |
| Missing numeric limits block final authority evaluation and Verify. | High | High | Keep `AUTO_APPROVAL_LIMIT_VND` and `TREASURER_APPROVAL_LIMIT_VND` unset and visibly blocked; implement only generic contracts until confirmed. | Backend owner and policy owner | Open |
| Seed corpus lacks full boundary coverage (8 cases, not 15+). | High | Medium | Expand to 15+ labeled cases and boundary variants before final Verify selection. | QA owner | Open |
| Treasurer is a scenario role, not authorization. | High | High | Label the Treasurer role as synthetic and proposed everywhere; make no authorization claims. | Policy & scenario owner | Open |
| Unversioned policy changes would break audit reproducibility. | Medium | High | Every confirmed policy change creates a new version; decisions reference policy version and rule IDs. | Project lead | Open |

## Decision log

| Date | Decision | Rationale | Consequence | Owner | Evidence link |
| --- | --- | --- | --- | --- | --- |
| Provisional (not yet confirmed) | Adopt a small, temporary, replaceable, documentation-first policy foundation (Policy Forge). | No validated real policy or numeric limits exist yet; a minimal parameterized, synthetic baseline gives backend, UI, and QA stable vocabulary and a safe decision boundary without false claims. | Backend may implement generic contracts only after PF-01–PF-03 review; numeric authority and public Verify stay blocked until thresholds are confirmed and the corpus reaches 15+. The baseline remains replaceable by a policy-owner-confirmed version. | Project lead | [03_pilot_policy_v0.1.md](03_pilot_policy_v0.1.md); [07_system_contract.md](07_system_contract.md) |

## Handoff gate

- **Allowed after PF-01–PF-03 review:** backend may implement generic request, decision, state, and audit contracts using the vocabulary in [07_system_contract.md](07_system_contract.md).
- **Not allowed yet:** a numerical authority evaluator, a public Verify suite, or any authority-threshold logic, until `AUTO_APPROVAL_LIMIT_VND` and `TREASURER_APPROVAL_LIMIT_VND` are confirmed and the corpus is expanded to 15+ cases.