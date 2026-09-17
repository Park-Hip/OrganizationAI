# 07 — Reimbursement Architecture

**Status:** Adopted target architecture for the reimbursement v1 synthetic pilot - not implemented by the current legacy `TMP-DEV-001` backend.

**Applies to:** [01_manual_reimbursement_workflow.md](01_manual_reimbursement_workflow.md), [02_MVP_Spec.md](02_MVP_Spec.md), [03_reimbursement_policy.md](03_reimbursement_policy.md), [04_reimbursement_system_contract.md](04_reimbursement_system_contract.md), and [05_reimbursement_case_corpus.md](05_reimbursement_case_corpus.md).

---

## System context

Sprint 1 OrganizationalAI is a synthetic, AI-led reimbursement case-preparation demo. One bounded AI agent guides intake, creates an editable structured draft, asks targeted clarification questions, and explains the result. A deterministic versioned policy engine, not the agent, produces classifications, calculations, rule IDs, and escalation types. A human remains responsible for approval and settlement.

```text
Requester / synthetic judge input
            │
            ▼
Single AI intake and packet-preparation agent
            │ schema-validated tool call
            ▼
  Application use case + deterministic policy processing
      │                    │
      ▼                    ▼
Immutable v1 case/audit store   Metadata-only evidence references
      │
      ▼
Review packet / structured escalation
            │
            ▼
Fixed synthetic human-control demo
(no real approval or settlement)
```

The system does not approve, reject, or transfer money. It does not replace governing-organization accounting, procurement, tax, or legal controls.

## Architectural principles

1. **Policy is versioned and deterministic.** The same normalized input, policy version, and organization-profile snapshot produce the same processing result.
2. **Human approval is separate from processing.** `ROUTINE_PROCESSED` means the packet is ready for a human; every agent result remains `PENDING_HUMAN_APPROVAL`.
3. **Agent authority is bounded.** The agent may draft, clarify, explain, and call schema-validated tools; it cannot classify, calculate, approve, reject, transfer money, select a policy/profile, invent or verify financial facts, or bypass controls.
4. **Sprint 1 actors are synthetic and server-owned.** The public demo has no login and uses fixed synthetic actor context for its limited human-control demonstration. Real authentication and authorization are activation-gate work, not Sprint 1 work.
5. **Audit history is append-only.** Corrections, pauses, overrides, human decisions, undo, and agent tool actions are new events. Historical decisions and inputs are not overwritten.
6. **Evidence is minimized and protected.** The application uses references, hashes, verification state, and masked financial data. Real evidence storage requires approved retention and access controls.
7. **Policy configuration is server-owned.** Clients and the agent cannot select thresholds, categories, roles, policy versions, or profiles for a case.
8. **Legacy is isolated.** Existing `TMP-DEV-001` code and traces remain synthetic historical material; the reimbursement architecture is a separate versioned path.

## Layer architecture

Requests flow downward through the application; responses and stored projections flow upward. A lower layer must not import from a higher layer.

| Layer | Responsibility | Does not own |
| --- | --- | --- |
| **Public API and synthetic actor context** | Synthetic-only request shape, fixed server-owned actor context, HTTP errors, provenance labels, and response serialization. Real OIDC is deferred. | Policy decisions, database rules, payment, or client-selected roles. |
| **Agent adapter** | One agent's prompt/versioning, structured draft, targeted clarification, schema-validated tool calls, explanation, and agent-action audit metadata. | Policy decisions, calculation, fact verification, payment, direct persistence, arbitrary network access, or agent delegation. |
| **Application** | Use cases that load a case/profile/policy snapshot, call pure processing, append events, and coordinate fixed synthetic human-control actions. | HTTP transport, policy rule definitions, payment execution. |
| **Policy processing** | Normalization, ordered policy evaluation, aggregation, calculation, explanations, and structured escalation drafts. | Database access, clock, network, LLM inference, authorization lookup. |
| **Domain contract** | Versioned reimbursement case, profile, evidence, outcome, escalation, control, and audit value objects. | Framework, database, API, or file storage. |
| **Persistence** | Immutable snapshots, append-only events, concurrency/idempotency safeguards, and authorized retrieval projections. | Business-rule evaluation or human-authority decisions. |
| **Evidence boundary** | Approved ingestion/storage integration, hash/reference creation, readability/verification metadata, and retention enforcement. | Inferring a financial fact or approving a document. |

## Processing flow

A submitted reimbursement case follows this path:

1. The public synthetic surface assigns a fixed server-owned synthetic actor, validates the transport shape, and labels the interaction as synthetic.
2. The agent guides intake and may create or update only a schema-validated structured draft. Unknown or unverified facts remain explicit.
3. The application loads the active policy and immutable `OrganizationProfile` snapshot; neither the client nor agent can supply either.
4. The policy layer normalizes documented fields, checks whether the case is operationally paused, and evaluates the ordered rules: data integrity, duplicate signals, scope/category, required dossier, deadline, budget/conflict/aggregation/authority, conditional tax evidence, calculation, and routine classification.
5. The application writes one transaction containing immutable case/profile/policy/outcome snapshots and ordered audit events, including agent tool actions where applicable.
6. The agent explains the returned review packet. A routine packet has no escalation; an escalated packet has one self-contained structured escalation.
7. A fixed synthetic human-control action may append its own event for the demo; it never changes the original agent processing result and never represents a real financial authority.

```text
synthetic input + fixed server-owned actor
        │
        ▼
agent drafts/clarifies through validated tools
        │
        ▼
load policy/profile snapshot
        │
        ▼
normalize → evaluate → aggregate/calculate
        │
        ├── routine ──► review packet + PENDING_HUMAN_APPROVAL
        │
        └── escalation ► structured human handoff
        │
        ▼
immutable snapshots + append-only audit events
```

## Escalation and human-control flow

The system creates an escalation rather than guessing or making a final financial decision.

| Trigger | Processing result | Required handoff |
| --- | --- | --- |
| Missing, unreadable, inconsistent, suspected, or disputed fact | `ESCALATED / FACT_UNKNOWN` | Ask the role able to supply evidence a specific question with a response format and resume action. |
| Prohibited, illegal, unrelated, or previously-paid expense | `ESCALATED / OUT_OF_POLICY` | Route the exception/corrective-action question to an authorized reviewer. Mandatory law is never overridable. |
| Over threshold/budget, late, conditional, or conflicted case | `ESCALATED / AUTHORITY_REQUIRED` | Route the decision to the configured independent authority. |
| Authorized operational pause | `control_state: PAUSED` | Halt processing; do not create an outcome or erase prior state. |

Human approval, exception resolution, settlement, and settlement evidence are separate authorized actions. The agent never converts an escalation response into a payment side effect without the required human record.

## Persistence model

The target persistence design is conceptual; concrete table and endpoint names belong to implementation. It must preserve the following records and relationships.

| Record | Immutable content |
| --- | --- |
| **Case snapshot** | Submitted case, normalized facts, case hash, server record time, actor context allowed by data-minimization rules. |
| **Profile/policy snapshot** | Organization profile, policy ID/version/snapshot, source applicability, and configuration needed to reproduce the result. |
| **Outcome snapshot** | Processing result, escalation type, fixed approval status, calculations, rule IDs, evidence references, explanation, and decision time. |
| **Escalation snapshot** | Type, addressee role, known facts, evidence references, specific question, response format, and resume action. |
| **Audit event** | Event ID, ordered predecessor relation, actor/role, time, input hash, rules, reason, target/prior outcome references, and explanation. |
| **Evidence reference** | Evidence ID, type, hash, readability/verification metadata, and retention/access metadata; never a real receipt in this repository. |

The store must reject mutation or deletion of snapshots/events on normal paths. It must make duplicate submission and control/idempotency behavior safe under concurrency.

## v1 implementation seams and shared-file locks

### Seam agreement

The following boundaries are frozen for the reimbursement v1 path and are recorded in ADR-006 through ADR-012:

- The server owns synthetic actor identity, timestamps, identifiers, hashes, profile snapshots, and policy snapshots. A client or agent cannot supply or choose any of these server-owned fields.
- The single Sprint 1 agent may only draft, clarify, explain, and use schema-validated tools; the deterministic evaluator remains the sole source of policy outcomes, calculations, rule IDs, and escalation types.
- `ROUTINE_PROCESSED` means a review packet was prepared; it is never a human approval, payment instruction, or settlement confirmation.
- There is no legacy conversion and no dual write. `TMP-DEV-001` records remain labelled synthetic history, and the v1 path is a separate versioned contract.
- The v1.2.0 contract artifacts are [policy_rules.yaml](../policy-forge-baseline/policy_rules.yaml), [reimbursement.schema.json](../policy-forge-baseline/reimbursement.schema.json), [reimbursement-fixture.schema.json](../policy-forge-baseline/reimbursement-fixture.schema.json), [expansion_spec.md](../policy-forge-baseline/expansion_spec.md), and the two synthetic suites [test_cases.json](../policy-forge-baseline/test_cases.json) and [verify_cases.json](../policy-forge-baseline/verify_cases.json).

### Shared-file locks

Until SETUP-04 merges, the named setup owner changes these shared paths only through the serial setup PRs:

| Locked path | Changed by |
| --- | --- |
| `backend/app/main.py` | Integration/seam owner (SETUP-04 or a later coordinated integration PR) |
| `backend/tests/conftest.py` | Test/infrastructure owner (SETUP-03) |
| `backend/pyproject.toml` | Test/infrastructure owner (SETUP-03), narrowly scoped |
| `.github/workflows/` | Test/infrastructure owner (SETUP-03) |
| `backend/alembic/versions/` | Persistence owner, exactly one scheduled revision at a time |

### Setup and lane ownership

Each setup PR and each post-setup lane has one accountable owner and one owned directory boundary, recorded as GitHub issues in the SETUP-01 issue set (external to the repository):

| Item | Branch | Owner | Owned paths |
| --- | --- | --- | --- |
| SETUP-02 | `docs/reimbursement-v1-contract-and-corpus` | Policy/contract owner | `policy-forge-baseline/`, `backend/tests/contract/reimbursement_v1/` |
| SETUP-03 | `test/legacy-regression-and-v1-contract-gates` | Test/infrastructure owner | `backend/tests/fixtures/legacy_tmp_dev_001/`, `.github/workflows/`, `backend/pyproject.toml` |
| SETUP-04 | `feat/reimbursement-v1-contract-seams` | Integration/seam owner | v1 packages under `backend/app/domain/reimbursement/`, `backend/app/policy/reimbursement/`, `backend/app/application/reimbursements/`, `backend/app/persistence/reimbursements/`, `backend/app/security/` |
| Lane A | `feat/reimbursement-policy-engine` | Policy owner | `backend/app/policy/reimbursement/`, `backend/tests/unit/reimbursement_v1/policy/` |
| Lane B | `feat/reimbursement-identity-authorization` | Security owner | `backend/app/security/` |
| Lane C | `feat/reimbursement-v1-persistence` | Persistence owner | `backend/app/persistence/reimbursements/` |

## Legacy migration boundary

The current backend persists synthetic temporary traces and exposes temporary endpoints. It is not the target architecture.

Migration requirements:

1. Introduce the reimbursement model, policy/profile snapshots, and audit vocabulary as a new versioned path.
2. Preserve legacy temporary records without updating, deleting, relabelling, or returning them as real-policy results.
3. Keep the legacy endpoints clearly synthetic until they are explicitly retired.
4. Add the Policy Forge full suite and Verify suite to the new processing path before exposing it to any real workflow.
5. Add authentication, authorization, evidence protections, and review/settlement controls before accepting real data.

## Sprint 1 implementation order

1. Implement the deterministic reimbursement evaluator and pass the 29-case corpus plus five-case Verify suite.
2. Add separate immutable v1 case/outcome/audit persistence; do not convert or dual-write legacy records.
3. Expose a labelled public synthetic Verify/API path that uses the same evaluator and fixed server-owned synthetic actors.
4. Add the bounded single-agent adapter with schema-validated tools and agent-action audit metadata.
5. Build the judge-facing agent, Verify, and audit UI from the real API path.

## Out of scope for Sprint 1

- Automated payment, bank transfer, or accounting posting.
- Agent approval or rejection of a reimbursement case.
- LLM-based policy decisions, settlement calculation, inferred financial facts, or fact verification.
- Multi-agent orchestration, RAG, and fine-tuning.
- Real OIDC/login/RBAC, real case intake, real personal/financial data, or a production reviewer queue.
- Receipt upload/OCR storage, third-party evidence processing, email/SMS, or notification integrations.
- Reinterpreting `TMP-DEV-001` as a real workflow or policy.
