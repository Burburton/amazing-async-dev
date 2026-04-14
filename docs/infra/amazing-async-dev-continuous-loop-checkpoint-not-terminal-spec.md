# amazing-async-dev — Continuous Canonical Loop Continuation Semantics
## Repair / Enhancement Spec

- **Spec ID:** `amazing-async-dev-continuous-loop-checkpoint-not-terminal`
- **Type:** Repair / Enhancement
- **Priority:** High
- **Status Intent:** Ready for autonomous derivation and implementation
- **Related Context:** This spec is derived from real dogfooding behavior observed while running `amazing-visual-map` under a north-star-driven low-interruption autonomous execution model.

---

## 1. Problem Statement

`amazing-async-dev` currently demonstrates strong **single-iteration autonomous execution** capability, but its **post-iteration continuation behavior** is not yet aligned with the intended low-interruption canonical loop model.

Observed behavior:

- the system can autonomously derive a first executable scope from a north-star document
- the system can implement a coherent iteration
- the system can test, summarize, commit, and push successfully
- the system can identify the correct next action
- but after reaching a successful iteration milestone, it tends to stop and frame the next canonical loop stage as **"a new session"**, even when:
  - there is a meaningful next step
  - there is no serious blocker
  - no explicit human escalation condition has been triggered
  - the project governance expects continuous autonomous progression

This creates a semantic mismatch:

- **Desired model:** successful completion of an iteration is a **checkpoint**
- **Current model:** successful completion of an iteration is often treated as a **terminal stop**

That mismatch weakens the intended product value of `amazing-async-dev` as a long-horizon autonomous development system.

---

## 2. Why This Matters

This is not a minor UX issue. It is a core autonomy gap.

If the system stops after each successful iteration and requires manual restart even when no escalation condition exists, then the loop is still fundamentally **session-based**, not truly **program-continuous**.

This causes several problems:

1. **Breaks low-interruption execution intent**
   - the user still has to manually push the system forward between iterations

2. **Weakens canonical loop continuity**
   - dogfood, friction capture, next-scope derivation, and follow-on planning are treated as optional follow-up work instead of default loop stages

3. **Reduces value of north-star-driven governance**
   - the system can interpret the next step, but does not reliably execute it

4. **Creates false completion semantics**
   - commit/push is interpreted as an endpoint instead of a milestone

5. **Limits practical autonomous product development**
   - long-running product iteration requires the system to continue unless a meaningful stop condition is hit

---

## 3. Goal

Introduce explicit **Continuous Canonical Loop Continuation Semantics** so that:

- successful completion of one iteration becomes a **checkpoint, not a default stop**
- the system continues into the next meaningful canonical loop stage by default
- the system only stops when a real stop condition is reached
- continuity is governed by clear, inspectable rules rather than implicit agent caution
- downstream artifacts are produced in a way that naturally feeds the next iteration

---

## 4. Non-Goals

This spec does **not** aim to:

- make the system reckless or infinitely recursive
- remove all human escalation boundaries
- force continuation when there is no meaningful next step
- bypass governance, audit, or safety constraints
- replace product-specific north-star constraints with generic always-continue behavior

The goal is **disciplined continuity**, not uncontrolled looping.

---

## 5. Target Behavioral Change

### Current undesired pattern
1. derive scope
2. plan
3. implement
4. test
5. summarize
6. commit + push
7. identify next step
8. stop with wording equivalent to "this would be a new session"

### Desired pattern
1. derive scope
2. plan
3. implement
4. test
5. summarize checkpoint
6. commit + push if appropriate
7. inspect whether stop conditions are triggered
8. if not, continue by default into the next canonical stage, such as:
   - dogfood
   - friction capture
   - audit consolidation
   - next-scope derivation
   - next-iteration planning
   - repair loop
9. only stop if an explicit stop condition is satisfied

---

## 6. Core Design Principle

> **Successful progress is a continuation trigger unless a defined stop condition overrides it.**

This principle should become part of the execution constitution of `amazing-async-dev`.

---

## 7. Functional Requirements

## FR-1: Explicit Checkpoint vs Terminal Outcome Distinction
The system must distinguish between:
- **checkpoint events**
- **terminal stop events**

Examples of checkpoint events:
- iteration implementation completed
- tests passed
- audit report generated
- commit completed
- push completed
- dogfood report generated

Examples of terminal stop events:
- explicit escalation required
- no meaningful next step exists
- external dependency blocks further progress
- governance requires human decision before continuation
- safety or integrity issue requires pause

A successful commit/push must not, by itself, imply terminal completion.

---

## FR-2: Default Continuation Policy
After each checkpoint, the system must evaluate whether continuation is allowed and expected.

If:
- there is a meaningful next canonical step
- no explicit stop condition is active
- no escalation condition is triggered

then the system should continue by default.

---

## FR-3: Canonical Next-Step Resolution
The system must resolve the next stage from current artifacts and governance context.

Possible next stages include:
- dogfood current iteration on target repo or scenario
- collect friction and observations
- consolidate audit findings
- repair known issues
- derive next iteration scope
- generate next execution artifacts
- continue product evolution

This must not depend on ad hoc phrasing alone. It should be driven by inspectable program state and rules.

---

## FR-4: Explicit Stop Condition Framework
The system must define and apply explicit stop conditions.

Minimum stop conditions:
1. **Escalation Required**
   - a major product metaphor, scope, architecture, or dependency decision requires human approval

2. **No Meaningful Next Step**
   - current artifacts do not support a coherent next action

3. **External Blocker**
   - a required resource, repo, credential, dependency, or environment is missing

4. **Integrity / Safety Pause**
   - continuing risks compounding significant errors or invalid state

5. **Policy-Based Stop**
   - a governing document explicitly mandates stop after a given milestone

If none of the above apply, the system should not stop by default.

---

## FR-5: Program State Continuity Artifact
The system should maintain a machine-readable continuity artifact that survives checkpoint boundaries.

Suggested examples:
- `program-state.json`
- `loop-state.yaml`
- `continuation-ledger.md` plus machine-readable companion

Minimum fields should include:
- current project
- current phase
- latest completed checkpoint
- continuation allowed
- next intended stage
- active blockers
- escalation required
- reason for stop if stopped
- last meaningful outputs
- candidate next actions

This artifact must be suitable for both autonomous continuation and later audit.

---

## FR-6: Session Handoff Contract
Every successful iteration summary should feed the next step in a structured way.

The system must avoid producing summaries that are only human-readable and not operationally useful for continuation.

Checkpoint outputs should include:
- what was completed
- what remains open
- what should happen next
- whether continuation is allowed
- whether escalation is required
- what artifact(s) the next stage should consume

---

## FR-7: Dogfood and Friction Capture as First-Class Continuation Stages
When relevant to the project mode, dogfood and friction capture should be treated as default canonical stages, not optional extras.

For product-development programs, a typical sequence may be:
- implement
- verify
- checkpoint
- dogfood
- capture friction
- derive improvements
- continue

---

## FR-8: Human Escalation Discipline
The system must escalate only when genuine escalation conditions are present.

It must not escalate merely because:
- one iteration ended cleanly
- a commit was pushed
- the next step is in a new logical phase
- the work could be described as a "new session"

Phase boundary alone is not a sufficient stop reason.

---

## 8. Quality Requirements

## QR-1: Continuation Correctness
The system should continue when it should continue, and stop only when a real stop condition applies.

## QR-2: Auditability
A reviewer should be able to inspect why the system continued or stopped.

## QR-3: Low-Interruption Alignment
Behavior should align with north-star-driven low-interruption workflows.

## QR-4: Governance Respect
Continuation must remain bounded by product-specific constitutions and escalation rules.

## QR-5: Recoverability
If a process does stop, the next session should be able to resume from explicit continuity artifacts rather than relying on vague summary text.

---

## 9. Proposed Design Directions

The exact implementation may vary, but the following design directions are strongly recommended.

### Direction A: Introduce Continuation Semantics in the Execution Layer
Create explicit semantics for:
- checkpoint
- continue
- stop
- escalate
- blocked
- awaiting-input

These states should be operational, not merely descriptive.

### Direction B: Add a Continuation Evaluator
Implement a decision component that runs after each checkpoint and decides:

- continue automatically
- stop with explicit reason
- escalate with explicit reason

This evaluator should inspect:
- governing documents
- current program state
- known blockers
- artifact completeness
- next-step availability

### Direction C: Add Continuation Ledger / State File
Persist continuity state in a structured artifact that can be used across sessions and audits.

### Direction D: Redesign Summary Templates
Session summaries should explicitly state:
- checkpoint reached
- continuation decision
- next action
- stop reason if stopped
- escalation status

Avoid summaries that imply completion merely because one bounded unit ended.

### Direction E: Treat "new session" as an implementation detail, not a governance stop
If the tool runtime needs a new process invocation, that should not automatically become a product-level stop.
The system should preserve the distinction between:
- **runtime process boundary**
- **program-level stop**

---

## 10. Acceptance Criteria

## AC-1
When an iteration completes successfully and a meaningful next stage exists, the system continues by default without requiring human restart.

## AC-2
Commit/push completion is recorded as a checkpoint, not automatically treated as terminal completion.

## AC-3
If the system stops, it records an explicit stop reason that matches a valid stop condition.

## AC-4
If the system escalates, it records an explicit escalation reason tied to a governance rule.

## AC-5
A continuity artifact exists and is updated at each checkpoint.

## AC-6
Dogfood and next-scope derivation can be entered automatically after implementation when no stop condition blocks continuation.

## AC-7
A reviewer can inspect the outputs of a run and determine:
- why it continued
- why it stopped
- what next step was selected
- whether the decision respected policy

## AC-8
The system no longer emits behavior equivalent to:
- "successful implementation complete, next step known, no blocker, but stopping because this would be a new session"

---

## 11. Example Desired Behavior

### Example undesired behavior
- V1 foundation implemented
- tests pass
- commit and push succeed
- summary states that dogfood and V2 derivation should happen next
- no blockers exist
- system stops anyway because the next work is framed as "a new session"

### Example desired behavior
- V1 foundation implemented
- tests pass
- commit and push succeed
- checkpoint summary recorded
- continuation evaluator runs
- no stop condition found
- system proceeds into dogfood stage
- friction is captured
- next iteration scope is derived
- the program continues unless a real blocker or escalation condition emerges

---

## 12. Suggested Implementation Breakdown

This section is intentionally non-binding but should help decomposition.

### Feature Track 1: Continuation Semantics Model
- define execution states
- define checkpoint vs terminal event model
- define stop condition taxonomy

### Feature Track 2: Continuation Evaluator
- evaluate current state after checkpoint
- decide continue / stop / escalate
- emit structured reason

### Feature Track 3: Continuity Artifact
- design schema
- persist and update state
- make resumable across sessions

### Feature Track 4: Summary / Reporting Upgrade
- separate checkpoint summary from terminal summary
- add continuation decision output
- add stop-reason output

### Feature Track 5: Dogfood Progression Integration
- add policy-aware entry into dogfood / friction / next-scope stages

### Feature Track 6: Tests
- continuation when next step exists
- stopping when no next step exists
- escalation when required
- commit/push not treated as terminal by default
- restart/resume using continuity artifact

---

## 13. Testing Expectations

At minimum, add tests for the following scenarios:

1. **Successful iteration with meaningful next step**
   - expected result: continue

2. **Successful iteration with no meaningful next step**
   - expected result: stop with valid reason

3. **Successful iteration with escalation trigger**
   - expected result: escalate

4. **Successful iteration with external blocker**
   - expected result: stop as blocked

5. **Commit/push checkpoint**
   - expected result: not terminal unless a stop condition applies

6. **Dogfood-enabled product workflow**
   - expected result: enter dogfood stage automatically after checkpoint

7. **Resume from prior continuity artifact**
   - expected result: next stage derived without vague human restatement

---

## 14. Risks and Failure Modes

### Risk 1: Over-continuation
The system may continue too aggressively.
Mitigation:
- explicit stop conditions
- auditability
- policy checks

### Risk 2: Infinite or low-value looping
The system may continue without meaningful progress.
Mitigation:
- require meaningful next-step resolution
- require explicit reason for continuation
- allow policy stop when no coherent advancement exists

### Risk 3: Governance drift
The system may continue in ways that violate project identity.
Mitigation:
- continuation evaluator must inspect governing documents
- escalation for major metaphor/scope shifts

### Risk 4: Ambiguous summaries remain operationally weak
Mitigation:
- structured continuation artifact
- upgraded summary templates

---

## 15. Definition of Done

This enhancement is done when:

- `amazing-async-dev` can treat successful iteration completion as a checkpoint rather than a default stop
- continuation behavior is policy-driven and inspectable
- stop conditions are explicit and enforced
- summaries and state artifacts support real continuation
- dogfood and next-step derivation can happen without manual restart when policy allows
- this behavior is validated with tests and demonstrated in at least one real autonomous product workflow

---

## 16. Recommended Immediate Application

Use `amazing-visual-map` as the validating dogfood scenario for this enhancement.

The observed pattern there is the exact motivating case:
- successful V1 completion
- explicit next step known
- no serious escalation condition
- inappropriate stop due to session-style completion semantics

That makes it a strong real-world acceptance case.

---

## 17. Requested Next Action

Use this spec to:
1. derive an implementation plan
2. implement continuation semantics enhancements in `amazing-async-dev`
3. validate the behavior against the `amazing-visual-map` workflow
4. confirm that post-iteration progression now behaves as checkpoint-based continuation rather than terminal stop by default

---

## 18. Final Guiding Statement

> `amazing-async-dev` should not merely complete iterations well. It should continue responsibly across iterations until a real reason to stop appears.
