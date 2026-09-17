# ADR-012: Single-agent Sprint 1 synthetic pilot

**Status:** Accepted
**Date:** 2026-09-16
**Decided by:** project lead

## Context

Sprint 1 must make AI-agent use a visible part of OrganizationalAI while preserving the reimbursement policy's deterministic financial boundary. The repository already has an adopted Policy Forge reimbursement contract and synthetic corpus, but the runnable backend is a separate, historical `TMP-DEV-001` implementation. Real-operation configuration, including the parent organization, accounting regime, approved identity provider, retention controls, and data-handling approval, remains incomplete.

A multi-agent system, LLM policy decisions, inferred financial facts, and production authentication would add cost and uncertainty without improving Sprint 1's evidence of calibrated autonomy.

## Decision

Sprint 1 is a synthetic, AI-led reimbursement case-preparation demo. One AI agent is the primary user experience: it guides Vietnamese intake, creates an editable structured draft, identifies unknown facts, asks focused follow-up questions, calls schema-validated tools, and explains a resulting review packet or escalation.

The deterministic, versioned reimbursement evaluator is the sole source of classifications, calculations, rule IDs, and escalation types. The agent may not approve, reject, transfer money, select a policy/profile, invent or verify a financial fact, bypass a pause or mandatory-law rule, access raw evidence, or write directly to persistence.

The public Sprint 1 surface is no-login and synthetic-only. It may run the five-case Verify suite and accept synthetic judge input. For the synthetic human-control demonstration, the server assigns fixed synthetic actors and records their actions in the append-only audit trail; the client does not select a role, policy, profile, identifier, timestamp, or audit event. This is not production authentication or authorization.

Do not implement real OIDC/login/RBAC, real case intake, receipt upload/OCR storage, RAG, fine-tuning, multi-agent orchestration, payment/accounting integration, or notifications in Sprint 1. ADR-006's public synthetic Verify surface and vocabulary mapping remain in force; this ADR narrows its private authenticated surface to a post-Sprint-1 activation concern.

## Consequences

The Sprint 1 critical path is: deterministic evaluator and corpus → immutable v1 audit path → public synthetic Verify/API → bounded single-agent adapter → judge-facing UI.

The legacy `TMP-DEV-001` endpoints, records, and Control Deck remain labelled synthetic history. They are not converted, dual-written, or extended for the new path.

The demo can truthfully show an AI agent while keeping outcomes reproducible, reviewable, and pending human approval. Before real operation, the deferred authentication, authorization, privacy, evidence, retention, incident, and settlement controls must be approved and implemented.
