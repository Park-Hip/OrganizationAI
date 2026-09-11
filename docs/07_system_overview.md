# 07 — What we are building (orientation)

> **Orientation only.** This is a plain-language explainer of the product shape and boundaries. It is **not** the MVP specification, and it does **not** validate the club's real workflow. All rules, categories, thresholds, and amounts below are proposed/synthetic until a club owner confirms them. The definitive behavior source remains the temporary development chain in `docs/README.md`; `02_MVP_Spec.md` stays a placeholder until workflow validation.

## One-sentence definition

**Input** — a submitted reimbursement case packet → **Brain** — an explicit club policy and checklist → **Output** — one of four reasoned outcomes: approve under the pilot policy, a specific item to repair, or an exception routed to the Treasurer.

This is the disciplined *first reviewer* of a reimbursement file: it makes the Treasurer's routine checklist visible, repeatable, and auditable. The Treasurer still owns policy, resolves exceptions, and performs (or authorizes) any real settlement.

## What it is — and is not

It **is**: a deterministic referee over *declared, policy-defined facts* (a structured index of the dossier — header, line items, evidence status/reference).

It is **not**: a payment, banking, accounting, tax/VAT, or invoice-authentication system. It does not move money, keep original receipts, or claim to verify a real tax invoice. "Approved" means *approved for settlement*, never *paid*.

## Two different inputs

1. **Per-request case packet** — what the requester submits for one claim: header (role, route, event, purpose), expense line(s), evidence checklist (receipt status, approval reference).
2. **Reusable policy** — what the Treasurer configures once: eligibility rules, evidence requirements, authority rules (which complete cases auto-complete vs. route to Treasurer), and outcome wording. This is a versioned rulebook, not case input.

## The three routes — selected slice

| Route | Real-world meaning | MVP role |
| --- | --- | --- |
| **A. Self-paid → reimbursement** | Member spends own money, keeps documents, requests money back | **Primary pilot route** — check the packet against policy |
| B. Advance → settlement | Club gives money first; later reconcile spend vs. advance | Contextual "advance reference" field only; no financial lifecycle |
| C. Club pays vendor directly | Finance pays/settles with the supplier | Outside the first MVP |

## Automated vs. stays human

**Automated (the referee):** accept the structured packet index → apply one versioned pilot policy → test facts/evidence → return a targeted repair question (not "please send more") → auto-complete only defined routine decisions → route exceptions and preserve rule/input/outcome history.

**Stays human:** bank transfer, cash handling, accounting entries, tax/VAT eligibility, legal invoice verification, budget ownership, and final discretionary approval.

## The four outcomes

1. `AUTO_APPROVED` — "Approved under pilot policy; settlement remains human."
2. `MISSING_FACT` — a precise repair question, e.g. "Provide the receipt/invoice reference for expense line 1."
3. `OUT_OF_POLICY` — "This category needs an exception."
4. `AUTHORITY_EXCEEDED` — "Treasurer review required under rule …" (facts complete; only the authority rule blocks automation).

## Before we can truthfully build it

The product shape above is real-world-informed, but the *club-specific* policy is not invented here. The path to a validated build is:

1. Ask one Treasurer about one past request (route, pre-approval, who checks, evidence, exceptions).
2. Convert only stable answers into pilot rules.
3. Create synthetic cases with expected outcome + reason.
4. Build the referee and show the boundary honestly in the demo.

Until then, development proceeds on the explicitly synthetic temporary chain (`docs/01..05`) with every record marked as synthetic/unvalidated.