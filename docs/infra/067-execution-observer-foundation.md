# Feature 067 — Execution Observer Foundation

## Metadata

- **Feature ID**: `067-execution-observer-foundation`
- **Feature Name**: `Execution Observer Foundation`
- **Feature Type**: `execution supervision / observability / platform foundation`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Related Features**:
  - `060-system-owned-frontend-verification-orchestration`
  - `061-external-execution-closeout-orchestration`
  - `062-controlled-frontend-verification-execution-recipe`

---

## 1. Problem Statement

`async-dev` can increasingly execute multi-step software work, but it still lacks a dedicated supervision layer that continuously checks whether executions are actually progressing as expected.

In real runs, several failure modes repeatedly appear:

- a run starts but then makes no meaningful progress,
- frontend work starts a server but verification never finishes,
- closeout begins but never reaches a terminal state,
- required artifacts are missing,
- recovery-worthy situations exist but are not surfaced clearly,
- decision requests remain unanswered beyond useful time windows,
- the system technically has state artifacts, but no independent process is actively watching them.

This creates a structural weakness:

> async-dev can run work, but it does not yet reliably watch that work.

Without an observer layer, the platform depends too heavily on:

- the execution path behaving perfectly,
- operators manually checking state,
- humans discovering failures late,
- post-hoc artifact reading to infer whether the system got stuck.

That is not strong enough for a platform intended to support asynchronous, low-interruption, multi-step software execution.

Feature 067 introduces an **Execution Observer Foundation**: a lightweight, periodic, state-driven supervision component that inspects active executions, detects anomalies, and produces structured findings that later operator surfaces and recovery workflows can consume.

---

## 2. Goal

Create a foundational **Execution Observer** that periodically inspects active or relevant executions and answers questions such as:

- Is this execution still making progress?
- Has this execution exceeded a timeout or stall window?
- Are required artifacts missing?
- Is verification overdue or incomplete?
- Is closeout stalled?
- Is recovery likely needed?
- Is a decision request overdue?

The observer must emit structured findings rather than only logs, so that async-dev can use those findings for:

- operator awareness,
- recovery workflows,
- escalation logic,
- later platform surfaces such as Recovery Console.

---

## 3. Non-Goals

This feature does **not** aim to:

- replace the main execution engine,
- replace verification or closeout orchestration,
- become a second execution planner,
- directly perform every recovery action,
- become a giant monitoring system with infrastructure complexity far beyond current platform needs,
- solve all observability concerns in one release.

This feature is specifically about creating a **foundational execution supervision layer**.

---

## 4. Core Design Principle

### 4.1 Execution and Observation Must Be Distinct Roles

The execution kernel is responsible for running work.

The observer is responsible for periodically inspecting whether that work is healthy, complete, stalled, or missing expected outputs.

This separation is important because a system that only executes may fail silently.

### 4.2 State-Driven, Not Transcript-Driven

The observer should rely primarily on structured state and artifacts, such as:

- run metadata,
- execution results,
- verification state,
- closeout state,
- recovery state,
- decision request state,
- timestamps and last-updated markers.

It should not depend mainly on brittle transcript scraping or freeform logs to determine health.

### 4.3 Findings Before Full Automation

The first version should prioritize structured anomaly detection and actionable findings.

It does not need to automatically fix everything yet.

The first win is:

- detect reliably,
- classify clearly,
- recommend next action.

### 4.4 Narrow, Foundational, Reusable

This observer should be a platform foundation, not a UI-first product.

It should feed later operator products such as:

- Recovery Console,
- Decision Inbox,
- Verification Console,
- future platform shell surfaces.

---

## 5. Target Outcomes

After this feature is complete, async-dev should be able to:

1. periodically inspect active executions,
2. detect common stall / timeout / missing-artifact conditions,
3. classify recovery-significant anomalies,
4. produce structured observer findings,
5. associate those findings with executions and artifacts,
6. expose recommended next actions,
7. provide reusable inputs for operator-facing recovery tooling.

The platform should no longer depend solely on humans noticing that “nothing seems to be happening.”

---

## 6. Required Functional Changes

### 6.1 Introduce an Execution Observer Component

Add a dedicated observer component, for example:

- `runtime/execution_observer.py`

or equivalent canonical module.

This component is responsible for periodic execution supervision and finding generation.

Its responsibilities must include:

- selecting executions to inspect,
- evaluating state freshness and progress,
- checking for known anomaly conditions,
- generating structured findings,
- persisting or exposing those findings for downstream consumption.

### 6.2 Define the Inspection Scope

The observer must have a clear policy for which executions it inspects.

At minimum, this should include executions in states such as:

- active/running,
- verification pending,
- closeout in progress,
- recovery required,
- awaiting decision,
- recently incomplete or recently non-terminal.

The exact inclusion policy may vary, but it must be explicit and testable.

### 6.3 Define a Structured Observer Finding Model

The observer must emit a structured finding model.

Suggested fields include:

- `finding_id`
- `run_id`
- `execution_id`
- `finding_type`
- `severity`
- `summary`
- `reason`
- `recommended_action`
- `detected_at`
- `related_artifacts`
- `related_state_snapshot`
- `recovery_significant`

This finding model should be easy for later operator surfaces to consume.

### 6.4 Periodic Scan Capability

The observer must support periodic scanning of active executions.

This does not necessarily require a long-running daemon in v1, but it must support a repeatable scheduled or callable scan workflow.

Possible forms include:

- CLI command,
- loop-integrated periodic step,
- cron-friendly entrypoint,
- future automation hook.

The key requirement is that the observer can be invoked regularly and produce meaningful findings.

### 6.5 Detect Common Anomaly Types

The first version should support a focused set of anomaly detections.

At minimum, recommended anomaly types include:

- `run_timeout`
- `verification_stall`
- `closeout_stall`
- `missing_execution_result`
- `recovery_overdue`
- `decision_overdue`

These should be implemented as explicit checks rather than vague heuristics.

### 6.6 Surface Recommended Next Action

Each meaningful finding should include a recommended next action when possible.

Examples:

- `resume`
- `retry`
- `continue closeout`
- `inspect verification`
- `request decision`
- `escalate`
- `manual investigation`

The first version does not need a complex planner, but it must do more than report “something is wrong.”

### 6.7 Persist or Expose Findings Reliably

Observer findings must not disappear into transient logs only.

They must be:

- persisted to artifacts,
- or exposed through a reliable machine-readable interface,
- or both.

This is required so later tools can consume them.

### 6.8 Integrate With Existing Recovery Direction

The observer must align with the broader platform direction:

- execution kernel remains the source of runtime state,
- observer reads and evaluates that state,
- later operator products consume observer findings,
- recovery actions may eventually be layered on top.

The observer should not take over kernel responsibilities.

---

## 7. Detailed Requirements

## 7.1 Canonical Observer Entry Point

The feature should define a single clear entry point, such as:

- `observe_executions(...)`
- `run_observer_scan(...)`
- `asyncdev observe-runs`

The exact naming may vary, but the entry point should be canonical and easy to schedule or invoke.

## 7.2 Inputs

The observer should consume structured runtime inputs, including as available:

- active run records,
- execution result artifacts,
- verification state,
- closeout state,
- recovery state,
- decision request state,
- timestamps / last-updated indicators.

The implementation may introduce adapters or indexes if raw artifact traversal is too fragmented.

## 7.3 Output Model

The observer output should include:

- zero or more structured findings,
- scan metadata,
- optionally a summary such as total findings by type/severity,
- a reliable way to associate findings with runs/executions.

This output must be predictable and machine-readable.

## 7.4 Severity Model

The feature should define a simple severity model, for example:

- `info`
- `warning`
- `critical`

The exact names may vary, but the model should help later operator tools prioritize findings.

## 7.5 Recovery Significance

Not every observation needs to become a recovery issue.

The observer should explicitly flag whether a finding is recovery-significant.

This is important so later UIs do not become noisy.

## 7.6 Time-Based Policies

The observer must use explicit time-based policies for anomaly detection, such as:

- maximum run duration before suspected timeout,
- maximum verification inactivity window,
- maximum closeout inactivity window,
- maximum overdue decision window.

These thresholds should be configurable or at least clearly centralized.

## 7.7 Artifact Linking

Each finding should include references to the most relevant artifacts where possible.

This may include:

- execution result,
- verification artifact,
- closeout artifact,
- decision request artifact,
- run summary artifact.

This will significantly improve downstream operability.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch categories like the following.

### 8.1 New Runtime / Observer Files

Potential new files:

- `runtime/execution_observer.py`
- `runtime/observer_finding.py`
- `runtime/observer_policy.py`

Potential CLI or entrypoint files:

- `cli/commands/observe_runs.py`

### 8.2 Existing Runtime Integration

Likely updates:

- execution artifact readers/indexers
- run state helpers
- recovery state helpers
- verification / closeout state summarization helpers
- decision request state accessors
- logging / artifact persistence helpers

### 8.3 Documentation Updates

Must update documentation to reflect:

- what the Execution Observer is,
- what anomaly types it checks,
- how findings are persisted or surfaced,
- how later operator surfaces are expected to consume those findings.

---

## 9. Acceptance Criteria

## AC-001 Observer Component Exists
A dedicated execution observer component exists in code.

## AC-002 Periodic or Repeatable Scan Exists
The observer can be invoked in a repeatable way to inspect current executions.

## AC-003 Structured Findings Exist
The observer emits structured findings rather than only human-readable logs.

## AC-004 Core Anomaly Types Detected
The observer detects at least the initial focused anomaly set:
- run timeout
- verification stall
- closeout stall
- missing execution result
- recovery overdue
- decision overdue

## AC-005 Recommended Action Included
Findings include a suggested next action when applicable.

## AC-006 Findings Are Persisted or Reliably Exposed
Observer findings can be consumed by later operator tooling.

## AC-007 Artifact Linking Works
Findings include useful links or references to related artifacts.

## AC-008 Recovery Significance Is Expressed
The observer can indicate whether a finding is recovery-significant.

## AC-009 Tests Added
Automated tests cover key anomaly detections and finding generation behavior.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Healthy Active Run
- active run within expected windows,
- no false-positive critical finding emitted.

### 10.2 Run Timeout
- active run exceeds configured duration or inactivity threshold,
- observer emits `run_timeout` finding.

### 10.3 Verification Stall
- verification required but not progressing or overdue,
- observer emits `verification_stall` finding.

### 10.4 Closeout Stall
- closeout has started but not reached a terminal state within expected time,
- observer emits `closeout_stall` finding.

### 10.5 Missing Execution Result
- execution should have produced a result artifact but has not,
- observer emits `missing_execution_result` finding.

### 10.6 Recovery Overdue
- execution is in `recovery_required` for too long without follow-up,
- observer emits `recovery_overdue` finding.

### 10.7 Decision Overdue
- a blocking decision request remains unanswered beyond policy threshold,
- observer emits `decision_overdue` finding.

### 10.8 Finding Persistence / Exposure
- generated findings are written or exposed in the expected structured form.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. define observer finding model,
2. define anomaly policy thresholds and check interfaces,
3. implement scan selection logic,
4. implement core anomaly checks,
5. implement finding persistence/exposure,
6. add CLI or callable entrypoint,
7. add tests,
8. update docs.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- relying mainly on log scraping instead of structured state,
- creating findings that cannot be consumed later,
- overbuilding a full monitoring system too early,
- mixing observer responsibilities with execution responsibilities,
- generating noisy findings without severity or recovery significance,
- requiring a UI before the foundation is useful.

## 11.3 Backward Compatibility

The observer should layer on top of the current runtime state and artifacts without forcing a redesign of all existing execution flows.

Where normalization is required, prefer adapters and policy helpers over broad rewrites unless a small canonicalization improvement is clearly beneficial.

---

## 12. Risks and Mitigations

### Risk 1: Fragmented state sources make inspection difficult
**Mitigation:** introduce adapter/index helpers or a normalized scan input layer.

### Risk 2: Too many false positives
**Mitigation:** start with a narrow anomaly set and conservative thresholds.

### Risk 3: Findings are generated but not used
**Mitigation:** persist findings in a machine-readable form and align them with future Recovery Console integration.

### Risk 4: Observer grows into a second execution engine
**Mitigation:** keep it read-evaluate-report in v1; avoid execution ownership.

### Risk 5: Time-based rules become hardcoded and brittle
**Mitigation:** centralize thresholds in policy/config helpers.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- execution observer component
- repeatable scan entrypoint
- structured finding model
- initial anomaly detection set
- recommended action generation
- finding persistence or reliable exposure
- artifact linking
- automated tests
- documentation updates

---

## 14. Definition of Done

This feature is considered done only when:

1. async-dev has a real supervision foundation separate from execution,
2. common stall/timeout/missing-artifact situations are detected structurally,
3. findings are actionable rather than purely descriptive,
4. findings can be consumed by later operator surfaces,
5. the observer materially improves platform awareness without becoming over-scoped.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as a platform supervision foundation,
- optimize for structured findings and low-noise anomaly detection,
- keep the observer separate from kernel execution ownership,
- prioritize downstream usability for recovery/operator tooling.

Recommended planning questions:

- what are the canonical scan inputs?
- how are thresholds defined and configured?
- what is the exact finding schema?
- which findings are recovery-significant in v1?
- how will later operator tooling consume the observer outputs?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- what executions are scanned,
- what anomaly types are supported,
- what the finding model looks like,
- how findings are persisted or exposed,
- how recommended actions are derived,
- how this foundation enables later Recovery Console or similar operator tools.

It should not claim completion merely because a polling loop exists.

---

## 17. Summary

Feature 067 introduces the missing supervision foundation for async-dev:

> **Execution Observer Foundation**

It ensures the platform not only executes work, but also periodically inspects whether that work is still healthy, complete, stalled, or missing critical outputs.

In platform terms:

- the **execution kernel** runs work,
- the **observer** watches work,
- future operator surfaces such as Recovery Console can act on observer findings.

This is a foundational step toward making async-dev a more operable, recoverable, and trustworthy execution platform.
