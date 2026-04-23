# Feature 066 — Execution Recovery Console

## Metadata

- **Feature ID**: `066-execution-recovery-console`
- **Feature Name**: `Execution Recovery Console`
- **Feature Type**: `operator surface / recovery operations / platform productization`
- **Priority**: `High`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Related Features**:
  - `060-system-owned-frontend-verification-orchestration`
  - `061-external-execution-closeout-orchestration`
  - `062-controlled-frontend-verification-execution-recipe`
  - `064-decision-email-blocking-protocol`
  - `065-session-start-blocking-check`
  - `067-execution-observer-foundation`

---

## 1. Problem Statement

`async-dev` is increasingly capable of executing, verifying, and recovering software work, but the operator experience is still weak when runs enter incomplete, stalled, or recovery-required states.

Today, the system may already produce or soon produce signals such as:

- `recovery_required`
- stalled or timeout findings
- missing artifact findings
- verification failure classifications
- closeout failure or incomplete terminalization
- observer-generated anomaly findings

However, these signals are still difficult to operate on in a clean, productized way. In practice, the operator often has to:

- inspect scattered artifacts manually,
- infer what went wrong,
- determine what the next action should be,
- figure out whether to continue, retry, resume, or escalate,
- jump between logs, markdown files, and execution state documents.

This creates a platform gap:

> async-dev may know that recovery is needed, but the operator still lacks a focused interface for understanding and acting on that fact.

Feature 066 addresses that gap by introducing the first major operator-facing product:

> **Execution Recovery Console**

This console is not a generic dashboard. It is a focused operational surface for identifying, inspecting, and acting on executions that need recovery attention.

---

## 2. Goal

Create a focused **Execution Recovery Console** that allows the operator to:

1. see executions that require recovery attention,
2. understand why they require attention,
3. inspect the most relevant execution state and artifacts,
4. see a suggested next action,
5. trigger an appropriate recovery action such as continue, retry, resume, or escalate.

The console should convert recovery from a scattered artifact-reading exercise into a structured operator workflow.

---

## 3. Non-Goals

This feature does **not** aim to:

- replace the execution kernel,
- replace verification or closeout orchestration,
- replace the observer foundation,
- become a giant all-in-one platform control center,
- solve every operator workflow in one UI,
- fully implement decision inbox behavior,
- redesign execution artifacts from scratch.

This feature is specifically about **recovery-focused operator usability**.

---

## 4. Core Design Principle

### 4.1 Narrow Operator Surface First

The first operator surface should be narrow and highly useful.

The Recovery Console must focus on:

- executions with recovery significance,
- operational clarity,
- explicit actionability.

It should **not** attempt to become a broad platform shell in v1.

### 4.2 Observer + Recovery Pairing

Feature 066 includes an execution observer that monitors async-dev runs.

The relationship should be:

- **Observer** finds issues (stalled, timeout, missing artifacts, verification failure),
- **Recovery Console** helps the operator interpret and respond.

This pairing makes recovery actionable rather than passive.

### 4.3 Actionable Over Decorative

The console must not be a passive status page.

It must help answer these questions quickly:

- What is broken or incomplete?
- Why is it in recovery?
- What is the recommended next action?
- What artifacts matter most?
- What can I do right now?

---

## 5. Target Outcomes

After this feature is complete, the operator should be able to:

- open a recovery-focused UI or console,
- see all executions currently needing attention,
- understand the reason each execution is in that list,
- open a recovery detail view,
- inspect key execution metadata, recovery state, verification state, and recent observer findings,
- trigger a recovery action or prepare the correct next step.

The system should no longer require the operator to reconstruct recovery context manually from many files.

---

## 6. Required Functional Changes

### 6.1 Recovery List View

Introduce a recovery-centered list view that surfaces executions requiring attention.

At minimum, this list should include executions that satisfy one or more conditions such as:

- `recovery_required = true`
- recent observer finding with actionable anomaly
- closeout timeout or stall
- verification incomplete with recovery significance
- decision overdue with execution-blocking effect
- missing execution result or required artifact in a recoverable path

Each row/item should include enough summary context for quick triage.

### 6.2 Recovery Detail View

Introduce a detailed recovery view for an individual execution.

This view should make it easy to see:

- execution identity and context
- current status / terminal or non-terminal state
- recovery reason
- verification state
- closeout state
- key observer findings
- recent timestamps / progress markers
- linked artifacts
- recommended action

This view should be optimized for operator understanding rather than raw artifact dumping.

### 6.3 Suggested Recovery Action

The console must surface a structured suggested action when possible.

Examples:

- `continue`
- `resume`
- `retry`
- `inspect verification`
- `wait for decision`
- `escalate`
- `manual investigation required`

The first version may generate these suggestions from existing state plus observer findings rather than from a complex planner.

### 6.4 Recovery Action Triggers

The console should support operator-triggered actions or at minimum action preparation.

Depending on current repo/UI capabilities, this may mean:

- direct action buttons,
- command generation,
- action intent creation,
- or copyable operator commands.

Actions of interest include:

- continue
- retry
- resume
- escalate
- open linked artifacts
- navigate to relevant run/result

The exact degree of action execution may vary in v1, but the console must go beyond passive display.

### 6.5 Observer Finding Integration

The console must integrate cleanly with the execution observer outputs.

If observer findings exist, the console should display:

- finding type
- severity or importance
- summarized reason
- suggested next step
- relevant timestamps

The console should treat observer outputs as first-class recovery inputs.

### 6.6 Artifact Linking

The console should surface the most useful linked artifacts, such as:

- execution pack
- execution result
- verification output
- closeout-related artifacts
- observer finding records
- relevant logs or summaries

The operator should not need to guess which file is the important one.

### 6.7 Recovery State Normalization

The console may require light normalization of recovery-related fields so that the UI can render a consistent model.

This may include normalizing or computing:

- recovery reason
- recovery category
- recommended action
- blocked status
- last meaningful progress timestamp
- whether operator intervention is mandatory

This feature may add a view-model layer or summary adapter if needed.

---

## 7. Detailed Requirements

## 7.1 Canonical Recovery Item Model

The feature should define a canonical recovery item model for the console.

Suggested fields:

- `run_id`
- `product_id`
- `execution_id`
- `title` or short label
- `status`
- `recovery_required`
- `recovery_reason`
- `recovery_category`
- `suggested_action`
- `verification_status`
- `closeout_status`
- `observer_findings_summary`
- `last_updated_at`
- `linked_artifacts`

This model may be derived from multiple underlying artifacts.

## 7.2 Recovery Categories

The system should define a small set of recovery categories for operator comprehension.

Suggested categories:

- verification
- closeout
- missing_artifact
- stalled_execution
- timeout
- decision_blocked
- manual_investigation

The exact list may vary, but the v1 console should avoid showing only raw low-level fields without higher-level grouping.

## 7.3 UI / Surface Form

The feature may be implemented as:

- a simple web UI,
- a lightweight local operator app,
- or another focused operator surface consistent with current async-dev direction.

A web UI is likely the most natural choice if the repo is already moving toward operator-facing product surfaces.

The design should prioritize:

- clarity,
- compact triage,
- easy detail inspection,
- actionability,
- low cognitive load.

## 7.4 Filtering and Sorting

The recovery list should support at least basic filtering and ordering.

Useful controls may include:

- severity / importance
- newest / oldest
- product
- recovery category
- status
- actionability

This need not be overbuilt, but some triage controls are important.

## 7.5 Action Execution Semantics

If direct execution is supported in v1, the action path must be explicit and safe.

If direct execution is not yet supported, the console must at minimum provide:

- clear action recommendation,
- the exact command or flow to run,
- and the artifact/context needed to perform it.

The system should not give vague suggestions with no practical next step.

## 7.6 Compatibility With Platform Architecture

Feature 066 should align with the platform architecture direction:

- async-dev remains the execution kernel,
- this console is an operator surface,
- observer findings and execution artifacts remain core truth inputs,
- this product is intentionally narrower than a full platform shell.

---

## 8. Expected File Changes

The exact file list may vary depending on repo structure and chosen UI stack, but implementation is expected to touch categories like the following.

### 8.1 New Operator Surface / UI Files

Potential new files/directories:

- operator surface UI routes/components for recovery list and detail
- recovery data adapter/view-model files
- action trigger or action command helper files

Example areas if using a web UI:

- `apps/recovery-console/...`
- `ui/recovery-console/...`
- `src/routes/recovery/...`
- `src/components/recovery/...`

### 8.2 Existing Runtime / Data Integration

Likely updates:

- execution artifact reading/indexing code
- observer finding integration code
- recovery state summarization helpers
- linked artifact resolution helpers
- any current lightweight UI shell if one exists

### 8.3 Documentation Updates

Must update documentation to reflect:

- the role of the Recovery Console
- how it relates to observer outputs
- what operator actions it supports
- how it fits into the broader platform architecture

---

## 9. Acceptance Criteria

## AC-001 Recovery List Exists
The operator can view a list of executions requiring recovery attention.

## AC-002 Recovery Detail Exists
The operator can open a detailed view showing recovery reason, verification/closeout context, observer findings, and linked artifacts.

## AC-003 Suggested Action Is Surfaced
Each recovery item surfaces a meaningful suggested next action.

## AC-004 Observer Integration Works
Execution observer findings are visible and useful within the Recovery Console.

## AC-005 Artifacts Are Discoverable
The console clearly surfaces relevant linked artifacts needed for operator diagnosis.

## AC-006 Recovery Actions Are Supported
The operator can trigger or at least concretely prepare a recovery action such as continue/retry/resume/escalate.

## AC-007 Recovery Categories Are Understandable
The UI uses normalized recovery categories rather than exposing only raw internal fields.

## AC-008 Narrow Scope Maintained
The feature remains a focused recovery console rather than turning into a giant all-purpose dashboard.

## AC-009 Tests Added
Automated tests cover the recovery item model, rendering-critical transformations, and core action-state behavior.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Recovery Item List Population
- runs with `recovery_required` or actionable observer findings appear in the list,
- irrelevant completed runs do not appear.

### 10.2 Recovery Detail Rendering
- recovery detail correctly aggregates execution state, verification state, closeout state, and observer findings.

### 10.3 Suggested Action Mapping
- common recovery states map to clear suggested actions.

### 10.4 Observer Finding Integration
- observer findings are shown with useful summaries and linked context.

### 10.5 Artifact Linking
- the recovery detail view can surface the right related artifacts.

### 10.6 Action Preparation or Trigger
- the console provides valid action output or trigger behavior for continue/retry/resume/escalate flows.

### 10.7 Empty / Healthy State
- when there are no recovery-relevant executions, the UI behaves clearly and does not mislead the operator.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. define recovery item view-model,
2. integrate execution artifacts + observer findings into the model,
3. build recovery list view,
4. build recovery detail view,
5. add suggested action logic,
6. add operator action triggers or prepared commands,
7. add tests,
8. update docs.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- turning the product into a generic dashboard,
- exposing only raw JSON/markdown without useful summarization,
- depending entirely on manual artifact reading,
- providing vague “recommended actions” with no executable next step,
- duplicating execution-kernel logic instead of consuming it,
- hiding observer findings when they are the most important clue.

## 11.3 Backward Compatibility

This feature should layer on top of the current execution kernel and observer outputs without forcing a redesign of all runtime artifacts.

Where normalization is needed, prefer adapter/view-model logic over destructive rewrites of underlying state, unless a small canonicalization improvement is clearly beneficial.

---

## 12. Risks and Mitigations

### Risk 1: UI scope expands too quickly
**Mitigation:** keep v1 strictly centered on recovery-focused triage and actionability.

### Risk 2: Recovery data is too fragmented
**Mitigation:** define a strong recovery item view-model that adapts multiple sources into one operator-facing shape.

### Risk 3: Observer outputs are noisy
**Mitigation:** summarize findings and surface only the most actionable signals by default.

### Risk 4: Actions are not yet safely executable from the UI
**Mitigation:** allow v1 to provide concrete action preparation/commands if fully automated triggering is not ready.

### Risk 5: The console becomes another viewer with little operator value
**Mitigation:** prioritize suggested actions, recovery reasons, and action triggers over purely informational rendering.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- recovery list view
- recovery detail view
- normalized recovery item model
- observer finding integration
- linked artifact surfacing
- suggested action logic
- recovery action trigger or preparation path
- automated tests
- documentation updates

---

## 14. Definition of Done

This feature is considered done only when:

1. operators can quickly identify executions needing recovery attention,
2. they can understand why recovery is needed without reading scattered artifacts manually,
3. they can see a concrete next action,
4. they can trigger or prepare that action from the console,
5. the console materially improves async-dev operability without becoming an over-scoped platform shell.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as the first major operator-facing product surface,
- keep the feature tightly scoped to recovery workflows,
- consume observer outputs rather than ignoring them,
- optimize for actionability and triage, not decoration,
- preserve alignment with the platform architecture direction.

Recommended planning questions:

- what is the canonical recovery item model?
- what exact executions qualify for the list?
- what is the minimum useful detail view?
- what recovery actions are safe to expose in v1?
- how should observer findings be summarized by default?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- how the Recovery Console identifies recovery-relevant executions,
- how it uses observer outputs,
- how it presents recovery reasons and suggested actions,
- how an operator can act from the console,
- why this is materially different from a passive viewer.

It should not claim completion merely because a list page exists.

---

## 17. Summary

Feature 066 introduces the first focused operator-facing product for async-dev platformization:

> **Execution Recovery Console**

It turns recovery from a scattered artifact-reading exercise into a structured operator workflow.

In platform terms:

- the **execution kernel** keeps running and persisting truth,
- the **observer** detects anomalies and recovery significance,
- the **Recovery Console** becomes the operator surface for understanding and acting on those situations.

This is the recommended first operator product because it is narrow, highly practical, and directly reinforces the platform direction.
