# ADR 0001 — Python backend stack for the Escalation Referee

- **Status:** Accepted (extracted from the Lavish review artifacts; confirm in review)
- **Date:** 2026-09-11
- **Supersedes:** `.lavish/backend-architecture-strategy.html`, `.lavish/backend-decide-before-code.html` (earlier `Node`/`Hono`/`SQLite` proposals)
- **Sources:** `.lavish/techstack-layer-research.html`, `.lavish/python-backend-blueprint.html`, `.lavish/industry-research-escalation-referee.html`, official framework/provider docs cited in those artifacts

## Context

Challenge A requires a system that completes routine work and escalates ambiguity or authority issues with reasons. The industry scan established a durable pattern: **rules route cases, humans resolve exceptions, and the system records an inspectable history.** The stack must satisfy, with a 72-hour MVP bias:

- an LLM lane (required in Sprint 1), without making the LLM the decision authority;
- deterministic, versioned policy decisions (four outcomes);
- named human controls (approve / reject / pause / undo);
- an append-only business audit trail that Verifies can replay;
- separate LLM observability that never substitutes for the audit log.

## Decision

Adopt a **Python modular monolith** ("Policy Forge" / "Model A"):

| Layer | Choice |
| --- | --- |
| API + schema | FastAPI + Pydantic (single typed model family for HTTP, LLM, policy, tests) |
| LLM lane | LangChain with provider-native structured output (`ExtractionDraft`); direct OpenAI SDK accepted as fallback |
| Policy | Pure, typed deterministic evaluator + versioned policy data (`evaluate(request, policy) → Decision`) |
| Workflow state | Database-backed finite-state machine (explicit transition table + one transaction per action + audit event) |
| Business store | Managed Postgres (Neon or Supabase) via SQLAlchemy + Alembic; append-only audit events |
| LLM observability | Langfuse (traces, prompts, cost, datasets, scores) |
| Tests / Verify | pytest + HTTPX + static case corpus; public Verify calls the same evaluator |
| Deploy | Render or Railway + Docker / native FastAPI |

## Alternatives considered

| Option | Verdict |
| --- | --- |
| TypeScript: Hono + Zod (+ Vercel AI SDK, Neon/D1, Vitest) | Strong for a TS-first team; rejected because LangChain/Langfuse are first-class in Python and the team selected Python. |
| Python, minimal abstraction (direct OpenAI SDK, no LangChain) | Fewest moving parts; fallback if LangChain adds confusion, not the default. |
| OPA / Rego policy engine | Clean policy/decision separation; deferred until multiple policy authors or enforcement points. |
| LangGraph or Temporal orchestration | Durable multi-step/human-in-the-loop semantics; overbuilt for the MVP — deferred. |

## Consequences

Positive:

- One language across API, schema, LLM integration, tests, and evaluation.
- LangChain + Langfuse are first-class rather than bolted on.
- FastAPI auto-generates the OpenAPI contract the UI and Verify share.
- Policy tests run with no database, web server, model key, or Langfuse account.

Risks / commitments:

- LangChain must stay narrow — one named extraction chain; no free-running agents, autonomous tools, or multi-agent graphs.
- Direct provider SDK is the escape hatch if LangChain abstraction costs time.

## Non-negotiable boundaries

1. **The LLM is never the policy engine.** For free text it drafts typed fields; the deterministic evaluator decides `AUTO_APPROVED`, `MISSING_FACT`, `OUT_OF_POLICY`, or `AUTHORITY_EXCEEDED`. Refusal / timeout / invalid output becomes a safe `MISSING_FACT`, never a guessed approval.
2. **Langfuse is never the business audit log.** LLM traces live in Langfuse; the append-only business history lives in Postgres. They may share a correlation ID, not a role.
3. **Business history is append-only.** Every action commits its audit event in the same transaction; undo records the event it compensates and reopens the correct state.
4. **Synthetic fixtures only.** No real receipts, bank details, or personal financial data in traces or fixtures.