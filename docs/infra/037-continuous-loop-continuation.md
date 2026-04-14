# 037-continuous-loop-continuation

## Title
Continuous Canonical Loop Continuation Semantics

## Summary
Transform successful iteration completion from a default terminal stop into a checkpoint, enabling disciplined autonomous continuation into the next canonical loop stage unless an explicit stop condition applies.

This feature addresses the core autonomy gap where `amazing-async-dev` currently stops after each successful iteration even when no escalation condition exists and meaningful next steps are known.

## Goal
Introduce explicit **Continuous Canonical Loop Continuation Semantics** so that:

1. Successful completion of one iteration becomes a **checkpoint, not a default stop**
2. The system continues into the next meaningful canonical loop stage by default
3. The system only stops when a real stop condition is reached
4. Continuity is governed by clear, inspectable rules rather than implicit agent caution
5. Downstream artifacts are produced in a way that naturally feeds the next iteration

## Why
`amazing-async-dev` demonstrates strong single-iteration autonomous execution capability, but its post-iteration continuation behavior is not aligned with the intended low-interruption canonical loop model.

**Observed behavior:**
- System can autonomously derive a first executable scope from a north-star document
- System can implement a coherent iteration
- System can test, summarize, commit, and push successfully
- System can identify the correct next action
- BUT after reaching a successful iteration milestone, it tends to stop and frame the next canonical loop stage as **"a new session"**, even when:
  - There is a meaningful next step
  - There is no serious blocker
  - No explicit human escalation condition has been triggered
  - The project governance expects continuous autonomous progression

**This creates problems:**

1. **Breaks low-interruption execution intent** - User must manually push system forward between iterations
2. **Weakens canonical loop continuity** - Dogfood, friction capture, next-scope derivation treated as optional
3. **Reduces value of north-star-driven governance** - System can interpret next step but doesn't execute it
4. **Creates false completion semantics** - Commit/push interpreted as endpoint instead of milestone
5. **Limits practical autonomous product development** - Long-running iteration requires manual restart

## Core Principle

> **Successful progress is a continuation trigger unless a defined stop condition overrides it.**

This principle should become part of the execution constitution of `amazing-async-dev`.

## Current Undesired Pattern

```
1. derive scope
2. plan
3. implement
4. test
5. summarize
6. commit + push
7. identify next step
8. stop with wording equivalent to "this would be a new session"
```

## Desired Pattern

```
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
```

## Scope

Implement explicit continuation semantics in `amazing-async-dev`:

### FR-1: Explicit Checkpoint vs Terminal Outcome Distinction
Distinguish between:
- **Checkpoint events**: iteration implementation completed, tests passed, audit report generated, commit completed, push completed, dogfood report generated
- **Terminal stop events**: explicit escalation required, no meaningful next step exists, external dependency blocks further progress, governance requires human decision, safety/integrity issue requires pause

A successful commit/push must not, by itself, imply terminal completion.

### FR-2: Default Continuation Policy
After each checkpoint, evaluate whether continuation is allowed and expected.

If:
- There is a meaningful next canonical step
- No explicit stop condition is active
- No escalation condition is triggered

Then the system should continue by default.

### FR-3: Canonical Next-Step Resolution
Resolve the next stage from current artifacts and governance context.

Possible next stages:
- dogfood current iteration on target repo or scenario
- collect friction and observations
- consolidate audit findings
- repair known issues
- derive next iteration scope
- generate next execution artifacts
- continue product evolution

This must not depend on ad hoc phrasing alone. It should be driven by inspectable program state and rules.

### FR-4: Explicit Stop Condition Framework
Define and apply explicit stop conditions.

**Minimum stop conditions:**
1. **Escalation Required** - Major product metaphor, scope, architecture, or dependency decision requires human approval
2. **No Meaningful Next Step** - Current artifacts do not support a coherent next action
3. **External Blocker** - Required resource, repo, credential, dependency, or environment is missing
4. **Integrity / Safety Pause** - Continuing risks compounding significant errors or invalid state
5. **Policy-Based Stop** - Governing document explicitly mandates stop after a given milestone

If none of the above apply, the system should not stop by default.

### FR-5: Program State Continuity Artifact
Maintain a machine-readable continuity artifact that survives checkpoint boundaries.

**Suggested artifact:**
- `continuation-ledger.md` plus machine-readable companion
- Or extend existing RunState with continuation fields

**Minimum fields:**
- current project
- current phase
- latest completed checkpoint
- continuation allowed (boolean)
- next intended stage
- active blockers
- escalation required (boolean)
- reason for stop if stopped
- last meaningful outputs
- candidate next actions

### FR-6: Session Handoff Contract
Every successful iteration summary should feed the next step in a structured way.

Checkpoint outputs should include:
- what was completed
- what remains open
- what should happen next
- whether continuation is allowed
- whether escalation is required
- what artifact(s) the next stage should consume

### FR-7: Dogfood and Friction Capture as First-Class Continuation Stages
When relevant to the project mode, dogfood and friction capture should be treated as default canonical stages, not optional extras.

For product-development programs, a typical sequence:
- implement → verify → checkpoint → dogfood → capture friction → derive improvements → continue

### FR-8: Human Escalation Discipline
The system must escalate only when genuine escalation conditions are present.

It must NOT escalate merely because:
- one iteration ended cleanly
- a commit was pushed
- the next step is in a new logical phase
- the work could be described as a "new session"

Phase boundary alone is not a sufficient stop reason.

## Non-Goals

Do NOT:
- Make the system reckless or infinitely recursive
- Remove all human escalation boundaries
- Force continuation when there is no meaningful next step
- Bypass governance, audit, or safety constraints
- Replace product-specific north-star constraints with generic always-continue behavior

The goal is **disciplined continuity**, not uncontrolled looping.

## Quality Requirements

### QR-1: Continuation Correctness
Continue when it should continue, and stop only when a real stop condition applies.

### QR-2: Auditability
A reviewer should be able to inspect why the system continued or stopped.

### QR-3: Low-Interruption Alignment
Behavior should align with north-star-driven low-interruption workflows.

### QR-4: Governance Respect
Continuation must remain bounded by product-specific constitutions and escalation rules.

### QR-5: Recoverability
If a process does stop, the next session should be able to resume from explicit continuity artifacts rather than relying on vague summary text.

## Implementation Tracks

### Track 1: Continuation Semantics Model
- Define execution states (checkpoint, continue, stop, escalate, blocked, awaiting-input)
- Define checkpoint vs terminal event model
- Define stop condition taxonomy

### Track 2: Continuation Evaluator
- Evaluate current state after checkpoint
- Decide continue / stop / escalate
- Emit structured reason

### Track 3: Continuity Artifact
- Design schema (possibly extend RunState)
- Persist and update state
- Make resumable across sessions

### Track 4: Summary / Reporting Upgrade
- Separate checkpoint summary from terminal summary
- Add continuation decision output
- Add stop-reason output

### Track 5: Dogfood Progression Integration
- Add policy-aware entry into dogfood / friction / next-scope stages

### Track 6: Tests
- Continuation when next step exists
- Stopping when no next step exists
- Escalation when required
- Commit/push not treated as terminal by default
- Restart/resume using continuity artifact

## Test Requirements

At minimum, add tests for:

1. **Successful iteration with meaningful next step** → expected: continue
2. **Successful iteration with no meaningful next step** → expected: stop with valid reason
3. **Successful iteration with escalation trigger** → expected: escalate
4. **Successful iteration with external blocker** → expected: stop as blocked
5. **Commit/push checkpoint** → expected: not terminal unless stop condition applies
6. **Dogfood-enabled product workflow** → expected: enter dogfood stage automatically after checkpoint
7. **Resume from prior continuity artifact** → expected: next stage derived without vague human restatement

## Acceptance Criteria

### AC-1
When an iteration completes successfully and a meaningful next stage exists, the system continues by default without requiring human restart.

### AC-2
Commit/push completion is recorded as a checkpoint, not automatically treated as terminal completion.

### AC-3
If the system stops, it records an explicit stop reason that matches a valid stop condition.

### AC-4
If the system escalates, it records an explicit escalation reason tied to a governance rule.

### AC-5
A continuity artifact exists and is updated at each checkpoint.

### AC-6
Dogfood and next-scope derivation can be entered automatically after implementation when no stop condition blocks continuation.

### AC-7
A reviewer can inspect the outputs of a run and determine:
- why it continued
- why it stopped
- what next step was selected
- whether the decision respected policy

### AC-8
The system no longer emits behavior equivalent to:
> "successful implementation complete, next step known, no blocker, but stopping because this would be a new session"

## Risks and Mitigations

### Risk 1: Over-continuation
System may continue too aggressively.
**Mitigation:** Explicit stop conditions, auditability, policy checks.

### Risk 2: Infinite or low-value looping
System may continue without meaningful progress.
**Mitigation:** Require meaningful next-step resolution, require explicit reason for continuation, allow policy stop when no coherent advancement exists.

### Risk 3: Governance drift
System may continue in ways that violate project identity.
**Mitigation:** Continuation evaluator must inspect governing documents, escalation for major metaphor/scope shifts.

### Risk 4: Ambiguous summaries remain operationally weak
**Mitigation:** Structured continuation artifact, upgraded summary templates.

## Recommended Application

Use `amazing-visual-map` as the validating dogfood scenario for this enhancement.

The observed pattern there is the exact motivating case:
- Successful V1 completion
- Explicit next step known
- No serious escalation condition
- Inappropriate stop due to session-style completion semantics

That makes it a strong real-world acceptance case.

## Definition of Done

This enhancement is done when:

- `amazing-async-dev` can treat successful iteration completion as a checkpoint rather than a default stop
- Continuation behavior is policy-driven and inspectable
- Stop conditions are explicit and enforced
- Summaries and state artifacts support real continuation
- Dogfood and next-step derivation can happen without manual restart when policy allows
- This behavior is validated with tests and demonstrated in at least one real autonomous product workflow

## Final Guiding Statement

> `amazing-async-dev` should not merely complete iterations well. It should continue responsibly across iterations until a real reason to stop appears.

## Source Spec

Derived from: `docs/infra/amazing-async-dev-continuous-loop-checkpoint-not-terminal-spec.md`

## Implementation Guidance

- Start with Track 1 (Continuation Semantics Model) to establish foundational concepts
- Proceed incrementally - each track should be testable before moving to the next
- Use existing RunState as the continuity artifact foundation (extend rather than create new)
- Keep continuation evaluator simple and inspectable
- Update documentation to explain checkpoint semantics clearly