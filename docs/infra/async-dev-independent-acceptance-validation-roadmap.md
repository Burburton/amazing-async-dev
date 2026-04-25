# async-dev Roadmap — Independent Acceptance Validation Integration

## Metadata

- **Document Type**: `roadmap / platform planning / acceptance integration`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `platform-level`
- **Purpose**: `Plan the multi-feature evolution from executor-self-validation to independent acceptance validation integrated into async-dev`

---

## 1. Why This Needs a Roadmap, Not One Feature

Independent acceptance validation is not a single isolated capability.

To become truly useful inside async-dev, it must eventually support the full loop:

1. implementation completes,
2. acceptance is triggered automatically,
3. acceptance runs in an isolated context,
4. findings are written back in a structured way,
5. development flow consumes those findings,
6. the feature is fixed,
7. acceptance is re-triggered,
8. the loop repeats until acceptance passes or escalates.

That means this work touches multiple platform layers:

- execution kernel
- observer/supervision
- artifact/state model
- operator surfaces
- retry/recovery semantics
- policy layer
- docs and readiness model

So the right way to approach it is as a **roadmap**.

---

## 2. End-State Vision

The target end state is:

> Every completed feature or meaningful phase result can be independently validated inside async-dev through an isolated acceptance flow, with structured findings feeding back into recovery and rework until acceptance passes.

In that future state, async-dev should behave like this:

1. executor finishes implementation,
2. runtime recognizes acceptance prerequisites are satisfied,
3. system builds an **Acceptance Pack**,
4. an independent validator runs in a separate acceptance context,
5. validator produces an **Acceptance Result**,
6. if rejected, async-dev converts the result into actionable recovery/fix work,
7. executor works on the fixes,
8. acceptance re-runs,
9. feature is only considered truly complete once acceptance passes.

This is a platform-level capability, not a single command.

---

## 3. Design Principles

### 3.1 Separate Implementation from Acceptance

The same actor should not be the final authority on whether work is accepted.

### 3.2 Acceptance Must Be Structured

Acceptance should use formal inputs and outputs, not vague freeform review.

### 3.3 Acceptance Must Be Repeatable

The system must support multiple acceptance attempts over the same feature or phase result.

### 3.4 Acceptance Must Be Integrated into Recovery

A failed acceptance result should not be a dead-end. It should feed directly into retry, recovery, or follow-up implementation.

### 3.5 Build the Loop in Stages

Do not attempt the full autonomous acceptance loop in one step. Build the foundation first, then wiring, then iterative closure.

---

## 4. Proposed Roadmap Structure

This roadmap is split into six major stages.

### Stage A — Acceptance Foundations
Define the core acceptance objects and lifecycle.

### Stage B — Observer-Triggered Acceptance
Teach async-dev when and how to start acceptance.

### Stage C — Isolated Acceptance Execution
Run validation in a separate acceptance context.

### Stage D — Acceptance Feedback Integration
Convert failed acceptance into structured rework inputs.

### Stage E — Iterative Acceptance Loop
Support repeated validate → fix → revalidate cycles.

### Stage F — Operator and Platform Productization
Expose the acceptance loop clearly in operator surfaces and platform docs.

---

## 5. Proposed Feature Roadmap

## Feature 069 — Acceptance Artifact Model Foundation

### Purpose
Define the canonical artifact and schema foundation for independent acceptance.

### Scope
- define `AcceptancePack`
- define `AcceptanceResult`
- define acceptance status / terminal states
- define acceptance finding model
- define relationship to `ExecutionPack` and `ExecutionResult`

### Key Outputs
- structured acceptance input model
- structured acceptance output model
- canonical fields for acceptance pass/fail/conditional/manual-review

### Why First
Without artifact contracts, the rest of the system has nothing stable to trigger, run, or consume.

---

## Feature 070 — Observer-Triggered Acceptance Readiness

### Purpose
Allow async-dev to determine when a feature or phase result is ready for independent acceptance.

### Scope
- define acceptance-readiness conditions
- extend observer or adjacent orchestration to recognize acceptance trigger points
- prevent acceptance from starting too early
- record why acceptance was or was not triggered

### Key Outputs
- acceptance readiness policy
- acceptance trigger decision model
- structured “ready for acceptance” or “not ready yet” state

### Why Second
The platform needs a reliable trigger layer before it can run acceptance automatically.

---

## Feature 071 — Isolated Acceptance Runner

### Purpose
Run acceptance in a separate, isolated context from implementation.

### Scope
- define isolated acceptance execution path
- invoke independent validator
- ensure validator consumes `AcceptancePack`
- persist `AcceptanceResult`
- keep acceptance clearly separate from executor context

### Key Outputs
- acceptance runner
- independent validator invocation path
- isolated acceptance execution records

### Why Third
This is the first step where independent acceptance becomes real rather than conceptual.

---

## Feature 072 — Acceptance Findings to Recovery Integration

### Purpose
Convert failed or conditional acceptance into structured recovery/rework inputs.

### Scope
- map acceptance failures to recovery categories
- create fix-oriented follow-up items
- attach acceptance findings to recovery state
- surface suggested remediation actions

### Key Outputs
- acceptance-to-recovery mapping
- actionable remediation structure
- failed acceptance feeding into next implementation attempt

### Why Fourth
Without this step, acceptance can fail, but the system does not yet know how to continue productively.

---

## Feature 073 — Re-Acceptance Loop Orchestration

### Purpose
Support repeated acceptance cycles until the work is accepted or escalated.

### Scope
- track acceptance attempt history
- define re-trigger rules
- prevent endless blind loops
- support bounded retry/revalidation
- mark terminal acceptance success/failure/escalation

### Key Outputs
- iterative acceptance loop
- acceptance attempt lineage
- retry/revalidation orchestration rules

### Why Fifth
This is where the platform moves from “can validate once” to “can work through validation failure.”

---

## Feature 074 — Acceptance Console / Operator Visibility

### Purpose
Expose acceptance state and findings to operators cleanly.

### Scope
- list pending/failed/passed acceptance runs
- show latest acceptance result and attempt history
- show failed criteria and evidence gaps
- show next action or escalation path
- optionally integrate with Recovery Console

### Key Outputs
- operator-facing acceptance surface
- acceptance visibility and traceability
- clearer platform operability

### Why Sixth
Once the loop exists, it needs to be observable and operable.

---

## Feature 075 — Policy and Gating Integration for Completion

### Purpose
Make acceptance a first-class gate for feature completion.

### Scope
- define when acceptance is mandatory
- connect acceptance pass to “feature complete”
- prevent premature completion status
- support exceptions/manual override where justified

### Key Outputs
- acceptance gating rules
- completion semantics tied to acceptance state
- policy integration with platform readiness

### Why Seventh
This is where acceptance stops being optional and becomes part of platform truth.

---

## Feature 076 — Platform Documentation and Readiness Rollup for Acceptance

### Purpose
Update platform docs so independent acceptance is part of async-dev’s canonical model.

### Scope
- update README/platform docs
- explain implementation vs acceptance separation
- explain acceptance lifecycle
- define alpha/beta maturity for acceptance loop

### Key Outputs
- coherent platform narrative for acceptance
- user/operator guidance
- readiness framing

### Why Eighth
This completes the productization and prevents the acceptance subsystem from becoming invisible complexity.

---

## 6. Stage-by-Stage Plan

## Stage A — Foundations
### Includes
- Feature 069

### Goal
Define the objects and statuses.

### Exit Criteria
- `AcceptancePack` and `AcceptanceResult` are stable enough for downstream work.
- acceptance statuses are no longer vague.

---

## Stage B — Triggering
### Includes
- Feature 070

### Goal
Determine when acceptance should start.

### Exit Criteria
- async-dev can identify acceptance-ready outcomes.
- observer/runtime can emit acceptance-trigger state.

---

## Stage C — Independent Execution
### Includes
- Feature 071

### Goal
Run acceptance in isolation.

### Exit Criteria
- validator is separate from executor.
- acceptance artifacts are created reliably.

---

## Stage D — Feedback Loop Integration
### Includes
- Feature 072

### Goal
Feed failed acceptance back into implementation.

### Exit Criteria
- failed acceptance produces structured recovery/rework inputs.

---

## Stage E — Iterative Closure
### Includes
- Feature 073
- partially Feature 075

### Goal
Support repeated validate → fix → validate cycles.

### Exit Criteria
- multiple acceptance attempts are tracked.
- the system can retry intelligently.
- completion is not declared prematurely.

---

## Stage F — Productization
### Includes
- Feature 074
- Feature 076
- remainder of Feature 075

### Goal
Make acceptance visible, operable, and platform-native.

### Exit Criteria
- operator can inspect acceptance state easily.
- docs reflect the new model.
- completion semantics are platform-consistent.

---

## 7. Suggested Priority Order

### Priority 1
Feature 069 — Acceptance Artifact Model Foundation

### Priority 2
Feature 070 — Observer-Triggered Acceptance Readiness

### Priority 3
Feature 071 — Isolated Acceptance Runner

### Priority 4
Feature 072 — Acceptance Findings to Recovery Integration

### Priority 5
Feature 073 — Re-Acceptance Loop Orchestration

### Priority 6
Feature 075 — Policy and Gating Integration for Completion

### Priority 7
Feature 074 — Acceptance Console / Operator Visibility

### Priority 8
Feature 076 — Platform Documentation and Readiness Rollup for Acceptance

### Why This Order
This sequence builds:
- data contracts first,
- trigger logic second,
- isolated execution third,
- remediation fourth,
- iterative closure fifth,
- hard gating and visibility after the loop is real.

---

## 8. Key Platform Models to Introduce

This roadmap will likely require the following canonical models.

### 8.1 AcceptancePack
Contains:
- feature/spec context
- acceptance criteria
- implementation summary
- execution results
- verification evidence
- observer findings
- changed files / artifacts

### 8.2 AcceptanceResult
Contains:
- accepted / rejected / conditional / manual-review
- failed criteria
- missing evidence
- validator summary
- risk notes
- remediation guidance

### 8.3 AcceptanceAttempt
Contains:
- attempt number
- linked acceptance pack/result
- timestamp
- trigger reason
- validator identity
- terminal status

### 8.4 AcceptanceReadinessState
Contains:
- ready / not-ready
- prerequisites satisfied
- reasons blocked
- triggerable now or later

### 8.5 AcceptanceRemediationState
Contains:
- linked failed findings
- suggested fix path
- must-fix vs optional
- whether re-acceptance is required

---

## 9. Major Risks

### Risk 1 — Acceptance and verification get confused
**Mitigation:** keep verification about execution correctness and acceptance about requirement fulfillment.

### Risk 2 — Observer becomes too heavy
**Mitigation:** let observer trigger acceptance, but keep deep validation in a separate acceptance runner/validator.

### Risk 3 — Endless fix/retry loops
**Mitigation:** add bounded attempt policy and escalation rules.

### Risk 4 — Acceptance results are too vague to drive remediation
**Mitigation:** force structured criteria failure output from the beginning.

### Risk 5 — Too much is built before operator visibility exists
**Mitigation:** add an operator-facing acceptance surface once the core loop is stable enough.

---

## 10. Recommended Branching / Execution Strategy

A practical way to execute this roadmap:

### Branch Theme
Use a focused branch series or one long-running thematic branch, for example:
- `platform/acceptance-foundation`
- `platform/independent-acceptance`

### Recommended Delivery Style
- one feature per acceptance milestone
- each milestone should be independently reviewable
- keep docs updated incrementally
- avoid jumping directly to operator UI before core loop exists

---

## 11. Roadmap Success Criteria

This roadmap is successful when async-dev can do the following end-to-end:

1. finish implementation,
2. recognize acceptance readiness,
3. run independent acceptance in isolation,
4. write structured acceptance results,
5. turn failed acceptance into recovery/fix work,
6. re-run acceptance after fixes,
7. only declare real completion once acceptance passes or is explicitly overridden.

That is the moment when implementation and acceptance are truly separated inside the platform.

---

## 12. Recommended Immediate Next Step

Start with:

> **Feature 069 — Acceptance Artifact Model Foundation**

Because if `AcceptancePack` and `AcceptanceResult` are not defined well, every later piece becomes fuzzy.

Only after that should async-dev start triggering or running acceptance automatically.

---

## 13. Summary

Independent acceptance validation is not one feature. It is a staged platform capability.

The right path is:

- define acceptance objects,
- define trigger readiness,
- run isolated acceptance,
- feed results into recovery,
- support re-acceptance loops,
- surface acceptance clearly,
- tie completion to acceptance truth.

In short:

> **Build the acceptance loop progressively, not all at once.**
