# Challenge A Score-Maximization Rubric

**Challenge:** A — The Escalation Referee (`Bộ điều phối chuyển tiếp`)

**Purpose:** This is the team’s single scoring contract. Do not add a feature, claim, test, or slide statement unless it maps to this document.

**Canonical competition source:** `docs/Challenge_Brief_OrganizationAI_VN.docx.txt`

**Project decision status:** Challenge A is selected as the target challenge. The final workflow is **not selected yet**.

---

## 1. Winning principle

The product must prove **calibrated autonomy**:

1. It completes routine work without human decision-making.
2. It stops safely when evidence is incomplete, policy does not cover the case, or the automated agent lacks authority.
3. It asks one specific question that a human can answer directly.
4. A human can inspect, approve, undo, and stop the system.
5. A judge can verify all of this in eight minutes without an account or installation.

> A system that escalates everything fails autonomy. A system that decides every uncertain case confidently fails safety.

---

## 2. Score map — 100 points


| Score area                | Max     | What the judge must see                                                                                | Definition of done / evidence                                                                          |
| ------------------------- | -------: | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Live URL                  | 10      | Public app opens without login; landing page states the first action clearly.                          | Test in incognito on a different device; landing text says exactly what to try.                        |
| One-click Verify          | 12      | One action runs all generic test cases and shows timestamped PASS/FAIL output.                         | Live Verify invokes the same production decision path; no hardcoded green screen.                      |
| New judge input           | 8       | Two unseen judge inputs are handled appropriately or safely refused/escalated.                         | Generic validation + policy logic; held-out internal variants; never match fixture IDs/text.           |
| Slides + video            | 10      | Exactly five required slides and a ≤3-minute demo video; limits disclosed.                             | Slide outline and video script map every required item. Missing Slide 3 or 5 costs half this category. |
| Real users + organization | 20      | Three named people in real roles; direct quotes; a product change from feedback; one adverse effect.   | Consent, role, exact quote, feedback → issue → commit/change evidence, and honest negative finding.    |
| Human-in-the-loop + audit | 20      | Human decision points match slide/system; decision trace; approve/undo/stop; nontechnical explanation. | Select any action and reconstruct input, policy/rule, reason, actor, time, result, and reversal.       |
| Challenge A verification  | 20      | Correctly separates routine from escalation; escalation questions are actionable.                      | Five-case Challenge-A suite: three routine + two escalation; blind/held-out variants.                  |
| **Total**                 | **100** |                                                                                                        |                                                                                                        |


### Score priority

```text
40 points — operational proof: URL, Verify, unseen inputs, slides/video
20 points — real people and honest evidence
20 points — human control and auditability
20 points — Challenge A decision quality
```

Do not sacrifice operational reliability, testability, or auditability for model complexity or visual polish.

---

## 3. Non-negotiable compliance gates

The compliance check can stop the project before judges score it.

- [ ] Public live URL works.
- [ ] Verify harness produces output.
- [ ] Public repository has full truthful commit history; no force-push or squash history.
- [ ] At least four generic test cases, including at least one correct refusal/escalation.
- [ ] Required deliverables are present.
- [ ] Three real users are identified when required by the stage.
- [ ] At least one feedback-originated improvement is evidenced when required by the stage.
- [ ] Five slides, demo video, and build log exist.

### Rules and integrity

- Core development must occur during the official sprint.
- Pre-existing public scaffolds are allowed only when disclosed in the README and only a small part of the project.
- Never fabricate user identities, roles, quotes, test logs, data, feedback, or commit evidence.
- Use real data only with written permission; replace sensitive data with synthetic data.
- Clearly distinguish real, observed, synthetic, simulated, and proposed components—especially on Slide 4.

---

## 4. Challenge A — required system behavior

### 4.1 Select one narrow routine workflow

The workflow must have:

- A requester, a routine handler, and a human authority/reviewer.
- A compact, written, versioned policy.
- Clear routine cases that can complete automatically.
- Natural uncertainty and exception boundaries.
- A safe way to accept newly typed judge inputs.

### 4.2 Maintain at least 15 labeled cases

The corpus must include:

- Routine/standard cases.
- Ambiguous or incomplete cases.
- Out-of-policy cases.
- Authority-exceeded cases.
- Boundary variants that are not part of the public Verify fixtures.

Each row must identify input, expected result, rule/policy ID, escalation type if any, expected question, and data status (synthetic/consented).

### 4.3 Required escalation categories


| Category             | Meaning                                                                       | System obligation                                                                               |
| -------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `MISSING_FACT`       | Facts needed to decide are absent, ambiguous, or contradictory.               | Do not decide; ask for the exact missing fact.                                                  |
| `OUT_OF_POLICY`      | The request is not covered by the written rules or violates a rule.           | Do not silently approve; explain rule and ask the authorized human about exception/next action. |
| `AUTHORITY_EXCEEDED` | The case may be valid, but exceeds the automated agent’s delegated authority. | Route/signpost the correct human sign-off with decision-ready context.                          |


### 4.4 Never do this

- Do not output a definitive approval/rejection for a flagged uncertain input.
- Do not use generic escalation text such as “Please review.”
- Do not make every case escalate.
- Do not make every case automatic.
- Do not hardcode known fixture text or IDs.

---

## 5. Challenge A verification — 20 points

### Semi-final quick check (90 seconds)

The judge runs **Verify → Escalation**, then enters a new ambiguous case from the team policy.

Pass condition:

- Three standard cases are fully handled automatically.
- Two cases are correctly escalated.
- The new ambiguous input is handled safely and appropriately.

### Final challenge score


| Test                                 | Points | Full-score standard                                                   |
| ------------------------------------ | ------: | --------------------------------------------------------------------- |
| Detect cases requiring escalation    | 8      | Both of two escalation cases are correctly detected and classified.   |
| Do not interfere with standard cases | 6      | All three ordinary cases complete automatically; no false escalation. |
| Escalation-question quality          | 6      | Questions allow one-answer decision without source-file lookup.       |


### Question-quality standard

A strong question contains:

```text
Observed fact or rule → consequence → named decision owner → one decision-ready question
```

Example pattern:

> “The request has no [required fact]. Is [option A] or [option B] correct?”

> “This request conflicts with Policy v1.0 rule [ID]. Do you authorize this exception?”

> “The amount/action exceeds the agent’s delegated limit. [Role], do you approve [specific action]?”

---

## 6. Verify harness contract — 12 points plus Challenge A proof

### Generic submission requirement

The general rules require at least **four** sequential cases and a timestamped PASS/FAIL table.

### Challenge A requirement

Challenge A explicitly requires **five** cases: three automatic and two escalation.

### Team decision

Ship a **five-case Verify suite**:

- Cases 1–4 satisfy the generic four-case compliance rule.
- All five satisfy the Challenge A quick-check pattern.

The live Verify output must show:


| Field                                      | Required    |
| ------------------------------------------ | ----------- |
| Run timestamp                              | Yes         |
| Case ID                                    | Yes         |
| Input summary                              | Yes         |
| Expected behavior                          | Yes         |
| Actual behavior                            | Yes         |
| Escalation category/question when relevant | Yes         |
| PASS/FAIL                                  | Yes         |
| Link to audit trace                        | Recommended |


The harness must invoke the same policy version and decision path as a judge-submitted request.

---

## 7. New-input robustness — 8 points

The judge will submit unfamiliar inputs, including an abnormal/edge case.

### Design requirements

- Parse/validate facts generically, not by matching known examples.
- Display missing/invalid fields clearly.
- Tie decisions to versioned rules.
- Use a safe unresolved state whenever a required fact is unknown.
- Keep a private/internal held-out set of policy boundary variants for regression testing.
- Test typos, blank fields, conflicting values, unfamiliar category names, thresholds, and malicious/irrelevant text.

### Acceptance check before submission

A non-team tester writes two awkward requests from policy documentation alone. The system must either resolve them under policy or produce a correct, specific escalation—not a confident unsupported answer.

---

## 8. Human-in-the-loop and auditability — 20 points


| Requirement                              | Points | Product requirement                                                                    |
| ---------------------------------------- | ------: | -------------------------------------------------------------------------------------- |
| Slide 2 and live decision boundary agree | 6      | One documented input → processing → outcome flow, reflected exactly in UI.             |
| Any action is auditable                  | 6      | Show what happened, when, with which input, under which policy/rule, why, and by whom. |
| Interrupt/override works                 | 4      | Staff can pause automation and approve/reject/override; effect is visible and logged.  |
| Explanation is understandable            | 4      | A nontechnical human understands the decision without confidence-score jargon.         |


### Minimum audit event fields

```text
request_id
occurred_at
actor_type and actor_id/demo role
action
input snapshot or privacy-safe hash
policy_version
matched rule IDs
facts used
result and escalation type
human question/reason
previous event / reversal relation
```

`undo` must create a compensating event. It must not erase history.

---

## 9. Real-user proof — 20 points


| Requirement                         | Points | Evidence to collect                                                                    |
| ----------------------------------- | ------: | -------------------------------------------------------------------------------------- |
| Three named people with real roles  | 6      | Name, actual role, organization/workflow relationship, consent.                        |
| Verbatim feedback                   | 4      | Direct quote from each participant; date/context.                                      |
| One feedback-originated improvement | 6      | Feedback → issue/decision → commit or before/after screen/test.                        |
| One adverse/unexpected effect       | 4      | Specific observation and mitigation/next step. “No negative effects” scores zero here. |


### Required research discipline

- Record observations separately from assumptions.
- Do not call a teammate or fictional persona a real operational user unless they truly perform the workflow.
- Do not use personal data in test fixtures without consent.
- With only three participants, report observations rather than universal causal claims.

---

## 10. Measurement and presentation — 10 slide/video points plus user proof

### Five mandatory slides


| Slide                       | Required evidence                                                      |
| ---------------------------: | ---------------------------------------------------------------------- |
| 1. Current problem          | Real workflow gap, current burden, user/context.                       |
| 2. Input → Process → Output | Exact human decision boundary; must match live system.                 |
| 3. Real impact              | Before/after measures and method; no unsupported saving claim.         |
| 4. Architecture/deployment  | Live components vs synthetic/simulated components and data disclosure. |
| 5. Limits and risks         | Failure cases, human/organizational risks, mitigations, next steps.    |


### Video

- Maximum three minutes.
- Screen recording is sufficient.
- Show the running system, including an incomplete/limited area where relevant.

### Demo-day truth rule

The live product, slides, data disclosure, Verify output, and audit log must tell the same story.

---

## 11. Delivery assets


| Asset             | Required content                                                             |
| ----------------- | ---------------------------------------------------------------------------- |
| Public repository | Full history throughout sprint; README; runbook; data/simulation disclosure. |
| Live URL          | No login/install; clear landing instruction; seeded demo safely usable.      |
| Verify            | One click, timestamped output, production decision path.                     |
| Runbook           | Clean clone → environment setup → commands → deploy/run → test.              |
| Five slides       | Exact prescribed structure only.                                             |
| Demo video        | ≤3 minutes.                                                                  |
| Build log         | AI tools used, value, time/cost overhead, largest cut feature and why.       |


---

## 12. Workflow-selection gate for Challenge A

Do not choose a workflow unless the team can answer **yes** to every question:

- [ ] Can three real people in actual roles be recruited?
- [ ] Can a policy owner validate a short written policy?
- [ ] Do at least three common cases complete automatically with no human decision?
- [ ] Do all three escalation categories occur naturally or can they be justified as a transparent pilot delegation boundary?
- [ ] Can the system ask an actionable one-answer question for each escalation?
- [ ] Can a judge plausibly generate new cases from the published policy?
- [ ] Can data be synthetic/de-identified and clearly disclosed?
- [ ] Can the entire result be tested in 90 seconds and explained in eight minutes?

A workflow that needs an LLM but has no credible policy is worse than a smaller hybrid system with a clear, safe human boundary.

---

## 13. Feature priority and cut rule

### Build first

1. Versioned written policy and decision engine.
2. Routine automatic route plus all three escalation routes.
3. Same-path Verify suite and judge-input form.
4. Audit timeline, approve/reject/undo/pause.
5. Public deployment and runbook.

### Build only if the above is green

- Natural-language extraction under strict schema validation.
- Better visual design.
- User-study dashboard.
- LLM explanation refinement.

### Explicit cuts for Sprint 1

- Multi-agent orchestration.
- Fine-tuning and large RAG/document library.
- Real payments, email/SMS, or irreversible integrations.
- Real student-card scanner integration.
- Login/RBAC, mobile application, and multi-workflow support.
- Claims not supported by measurement.

---

## 14. Pre-submission kill checklist

The team may submit only after every item is true:

- [ ] A stranger can open the live URL in incognito and complete the primary flow.
- [ ] Verify runs five cases and produces a real timestamped table.
- [ ] Three routine cases auto-complete; two escalation cases stop safely.
- [ ] Each escalation has a direct, policy-grounded question.
- [ ] Two held-out manual inputs behave safely.
- [ ] An action can be audited in under 30 seconds.
- [ ] Pause, override, and undo visibly work and are logged.
- [ ] Slide 2 matches live behavior.
- [ ] Slide 3 includes a method, not an unsupported benefit claim.
- [ ] Slide 4 discloses real versus synthetic/simulated components.
- [ ] Slide 5 reports concrete limits and at least one possible adverse effect.
- [ ] Repository history is public, readable, and unaltered.
- [ ] Runbook, five slides, ≤3-minute video, and one-page build log are present.
