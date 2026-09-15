# ADR-001: Use FastAPI with Pydantic v2

**Status:** Accepted
**Date:** 2026-07
**Decided by:** team

## Context

The project needs a Python web framework for exposing a REST API and a validation library for request/response shapes. The framework must integrate cleanly with a typed domain model and support automatic OpenAPI generation for testability.

## Decision

Use FastAPI as the web framework and Pydantic v2 as the data-validation engine. All request and response shapes are defined as Pydantic models with frozen configuration (`ConfigDict(frozen=True, extra="forbid")`). FastAPI reads these models directly to validate requests, generate `/docs`, and serialize responses.

## Consequences

- **Pros:** Automatic OpenAPI/Swagger at `/docs`; zero runtime overhead for shape validation; strict model config catches unexpected fields early; fast development velocity.
- **Cons:** Tight coupling to FastAPI's dependency-injection style in the application layer; Pydantic v2 model configuration must be repeated on each model for consistency.
- **Mitigation:** Application-layer functions accept plain Pydantic models, so switching the framework later would only require rewriting the API layer, not the policy or domain layers.
