# Feature 078 — Acceptance × Recovery Console Integration

## Metadata

- **Feature ID**: `078-acceptance-recovery-console-integration`
- **Feature Name**: `Acceptance × Recovery Console Integration`
- **Feature Type**: `operator surface integration / platform productization / acceptance recovery UX`
- **Priority**: `High`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Target Branch**: `platform/foundation`
- **Related Features**:
  - `063-execution-observer-foundation`
  - `066-execution-recovery-console`
  - `066a-recovery-console-integration-into-async-dev`
  - `069-acceptance-artifact-model-foundation`
  - `070-observer-triggered-acceptance-readiness`
  - `071-isolated-acceptance-runner`
  - `072-acceptance-findings-to-recovery-integration`
  - `073-re-acceptance-loop-orchestration`
  - `074-acceptance-console-operator-visibility`
  - `075-policy-and-gating-integration-for-completion`
  - `077-acceptance-cli-and-mainflow-integration`

---

## 1. Problem Statement

The acceptance subsystem is now implemented, integrated into async-dev mainflow, exposed through CLI, and validated through dogfooding.

The Recovery Console is also established as the first focused operator-facing surface.

However, these two platform capabilities are still not fully unified in the operator experience.

At the moment, acceptance may exist as:

- readiness state,
- acceptance attempts and results,
- failed criteria,
- remediation guidance,
- retry / re-acceptance flows,
- completion blocking,

while the Recovery Console focuses on:

- recovery-required executions,
- observer findings,
- recovery categories,
- suggested next actions,
- operator recovery flow.

Without deeper integration, operators still face a gap:

> acceptance failures are part of recovery reality, but they are not yet fully surfaced and actionable inside the Recovery Console.

That creates several usability problems:

- rejected or blocked acceptance may not appear as first-class recovery items,
- operators may need to switch between CLI and console to understand acceptance state,
- failed criteria and remediation guidance may not be visible where recovery action happens,
- re-acceptance may remain operationally separate from recovery handling,
- the platform may still feel like adjacent subsystems rather than one coherent operator experience.

Feature 078 closes that gap by integrating acceptance into the Recovery Console as a first-class recovery and operator workflow dimension.

---

## 2. Goal

Make acceptance state, failure, remediation, and re-acceptance operable directly inside the Recovery Console.

After this feature, operators should be able to:

1. see acceptance-blocked or acceptance-failed items in the Recovery Console,
2. inspect latest acceptance result and failed criteria,
3. inspect remediation guidance and recovery significance,
4. understand whether re-acceptance is required,
5. trigger or prepare acceptance retry / re-acceptance actions from the console,
6. treat acceptance issues as part of the same recovery workflow rather than a disconnected subsystem.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the acceptance subsystem,
- replace acceptance CLI,
- replace isolated validator execution,
- replace Recovery Console itself,
- create a giant all-in-one platform shell,
- redesign completion policy.

This feature is specifically about **operator-surface integration between acceptance and recovery**.

---

## 4. Core Design Principle

### 4.1 Acceptance Failure Is Recovery-Relevant

A failed or blocked acceptance result should be treated as a first-class recovery concern inside operator workflows.

### 4.2 Operator Surfaces Must Minimize Context Switching

The operator should not need to jump between multiple tools to answer:

- why this item is blocked,
- what acceptance failed,
- what to fix,
- whether re-acceptance is needed,
- what action to take now.

### 4.3 Console Should Be Actionable

The console must not only display acceptance state. It must help the operator move the feature forward.

### 4.4 Reuse Canonical Truth

The Recovery Console must consume canonical acceptance artifacts and state rather than inventing parallel interpretations.

---

## 5. Target Outcomes

After this feature is complete, the Recovery Console should be able to show items such as:

- `NEEDS_ACCEPTANCE`
- `AWAITING_ACCEPTANCE`
- rejected acceptance requiring remediation
- repeated failed acceptance requiring operator intervention
- completion blocked by acceptance

For each relevant item, the operator should be able to:

- view latest acceptance status,
- inspect failed criteria,
- inspect remediation guidance,
- inspect acceptance attempt history summary,
- understand whether recovery vs re-acceptance is the next action,
- trigger or prepare acceptance retry/revalidation.

The operator experience should feel unified.

---

## 6. Required Functional Changes

### 6.1 Acceptance-Aware Recovery Item Model

Extend the Recovery Console’s item model so that it can represent acceptance-related recovery states explicitly.

Suggested additions include:

- `acceptance_status`
- `acceptance_blocking`
- `acceptance_attempt_count`
- `latest_acceptance_result_ref`
- `latest_failed_criteria_summary`
- `acceptance_remediation_summary`
- `reacceptance_required`
- `acceptance_next_action`

The model should not flatten acceptance into vague generic recovery text.

### 6.2 Acceptance-Driven Recovery Categories

Ensure the Recovery Console can classify and display acceptance-related recovery categories such as:

- acceptance_failed
- acceptance_blocked
- awaiting_acceptance
- reacceptance_required
- acceptance_escalation_needed

Exact labels may vary, but they should be operator-comprehensible.

### 6.3 Acceptance Result Surfacing in Detail View

For recovery items that are acceptance-related, the detail view should surface:

- latest acceptance status
- failed criteria summary
- missing evidence summary
- remediation guidance
- validator summary
- whether completion is blocked
- whether re-acceptance is mandatory

This should be concise but meaningful.

### 6.4 Acceptance Attempt History Summary

The Recovery Console should show acceptance attempt history in a lightweight operator form.

At minimum, it should help answer:

- how many attempts were made,
- what the latest outcome is,
- whether the item is repeatedly failing,
- whether escalation may be needed.

This does not require the full acceptance history UI to be duplicated, but the recovery operator should see enough context to act intelligently.

### 6.5 Acceptance Retry / Re-Run Actions from Console

The Recovery Console should support or prepare actions such as:

- retry acceptance
- rerun acceptance after remediation
- open latest acceptance result
- open acceptance history
- escalate acceptance issue

Depending on current safety and architecture, actions may be:

- direct console actions,
- action intents,
- exact command generation,
- or linked command execution hooks.

The key requirement is practical operator actionability.

### 6.6 Completion Blocking Visibility

If completion is blocked because acceptance has not passed, the Recovery Console must surface that clearly.

The operator should not confuse:

- execution failure,
- acceptance failure,
- acceptance pending,
- acceptance blocked by prerequisites,
- or completion blocked by policy.

These states must be distinguishable.

### 6.7 Observer + Acceptance + Recovery Alignment

If observer findings exist that are relevant to acceptance, the console should align them with acceptance state.

This should help the operator see:

- what the observer noticed,
- what acceptance concluded,
- what recovery action is now appropriate.

---

## 7. Detailed Requirements

### 7.1 Canonical Acceptance Sources

The Recovery Console integration must use canonical acceptance truth sources such as:

- acceptance readiness state
- latest `AcceptanceResult`
- acceptance attempt history
- completion gate/block status
- remediation or recovery mapping artifacts

The exact source list may vary, but it must be explicit.

### 7.2 Acceptance Summary Adapter

The feature should introduce or extend an adapter/view-model layer that summarizes acceptance for recovery use.

Suggested acceptance summary fields:

- `latest_status`
- `attempt_count`
- `latest_failed_criteria`
- `latest_remediation_summary`
- `is_blocking_completion`
- `needs_reacceptance`
- `recommended_action`

This adapter should feed list/detail rendering.

### 7.3 Recovery Console List Behavior

The recovery list should include acceptance-driven items when they are recovery-significant.

Typical inclusion examples:

- latest acceptance rejected and remediation needed
- acceptance required but awaiting trigger/completion
- repeated acceptance failure with operator action needed
- feature blocked from completion due to missing acceptance

The list should remain focused and avoid becoming noisy.

### 7.4 Recovery Console Detail Behavior

The recovery detail view should support acceptance-specific sections such as:

- Acceptance status
- Latest validator summary
- Failed criteria
- Remediation guidance
- Re-acceptance required?
- Acceptance history summary
- Completion gate status

The operator should not have to leave the console to understand the problem.

### 7.5 Action Semantics

The integration must define what acceptance-related actions actually do.

Examples:

- `retry acceptance` -> invoke or prepare canonical acceptance retry flow
- `open acceptance result` -> resolve linked result artifact/view
- `open acceptance history` -> surface linked attempt history
- `escalate` -> mark or create escalation flow for repeated failure
- `continue remediation` -> route operator back into recovery/implementation step

The semantics must be explicit and testable.

### 7.6 Noisy-Failure Controls

The integration should avoid turning every acceptance detail into a top-level recovery alert.

Acceptance data should be surfaced strongly when it is:

- blocking completion,
- requiring remediation,
- awaiting operator action,
- repeatedly failing,
- or otherwise recovery-significant.

This will keep the Recovery Console useful rather than cluttered.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch categories like the following.

### 8.1 Recovery Console Data Integration

Potential areas:

- recovery console item adapters/view-models
- acceptance summary integration layer
- artifact link resolution
- action trigger/command generation helpers

### 8.2 Recovery Console UI / Surface

Potential updates:

- recovery list rendering
- recovery detail rendering
- acceptance-specific UI sections
- action controls or command output surfaces

### 8.3 Existing Acceptance / Runtime Integration

Likely updates:

- acceptance artifact readers
- acceptance history accessors
- recovery classifiers / state adapters
- completion block summarization helpers
- operator docs

### 8.4 Documentation Updates

Likely updates:

- Recovery Console docs
- acceptance docs
- platform operator guide
- README/operator flow references where applicable

---

## 9. Acceptance Criteria

## AC-001 Acceptance-Related Recovery Items Are Visible
Acceptance-blocked or acceptance-failed items appear meaningfully in the Recovery Console.

## AC-002 Acceptance Status Is Visible in Detail View
Operators can see the latest acceptance status and blocking significance inside the Recovery Console detail view.

## AC-003 Failed Criteria and Remediation Are Surfaced
The Recovery Console shows failed criteria summary and remediation guidance when acceptance fails.

## AC-004 Re-Acceptance Need Is Clear
Operators can tell whether re-acceptance is required and why.

## AC-005 Acceptance Attempt Summary Is Visible
Operators can see a useful summary of acceptance attempt history.

## AC-006 Acceptance Actions Are Available
The console can trigger or prepare practical actions such as retry acceptance or open result/history.

## AC-007 Completion Blocking Is Clear
Completion gating due to acceptance is clearly surfaced.

## AC-008 Observer and Acceptance Signals Are Coherent
Acceptance and observer/recovery signals do not appear contradictory or disconnected in the console.

## AC-009 Tests Added
Automated tests cover acceptance summary adaptation, list/detail rendering inputs, and acceptance-action wiring.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Acceptance Failure Appears in Recovery List
- rejected acceptance with remediation requirement appears as a recovery-significant item.

### 10.2 Acceptance Detail Rendering
- detail view shows latest acceptance status, failed criteria, remediation, and completion block state.

### 10.3 Awaiting Acceptance Rendering
- items waiting on acceptance are represented clearly and not misclassified as generic failure.

### 10.4 Re-Acceptance Action Wiring
- retry/re-acceptance action maps to the correct acceptance flow or prepared command.

### 10.5 Repeated Failure Summary
- multiple acceptance attempts show useful history summary and support escalation context.

### 10.6 Completion Gate Visibility
- acceptance-based completion blocking is surfaced clearly in console state.

### 10.7 Missing Acceptance Artifact Handling
- console fails clearly if expected acceptance artifacts are missing or inconsistent.

---

## 11. Implementation Guidance

### 11.1 Preferred Implementation Order

Recommended sequence:

1. define acceptance summary adapter for recovery use,
2. integrate acceptance-driven recovery categories,
3. extend recovery list inclusion logic,
4. extend recovery detail view with acceptance sections,
5. wire acceptance-related actions,
6. add tests,
7. update docs.

### 11.2 Avoid These Failure Patterns

The implementation must avoid:

- duplicating the full acceptance UI inside the Recovery Console,
- exposing raw acceptance artifacts without operator summarization,
- adding acceptance noise to every recovery item,
- hiding completion blocking reasons,
- leaving acceptance actions disconnected from real flows,
- making operators switch back to CLI for basic understanding.

### 11.3 Backward Compatibility

The integration should extend the Recovery Console cleanly without requiring a redesign of the acceptance subsystem.

Where possible, it should reuse existing acceptance CLI/runtime flows and canonical artifacts.

---

## 12. Risks and Mitigations

### Risk 1: Recovery Console becomes too dense
**Mitigation:** show acceptance details only when they are recovery-significant, and summarize by default.

### Risk 2: Acceptance data and recovery state disagree
**Mitigation:** use canonical adapters and align completion blocking/recovery classification logic.

### Risk 3: Re-acceptance actions are not safe to trigger directly
**Mitigation:** support prepared commands/intents where direct execution is not yet appropriate.

### Risk 4: Attempt history becomes hard to read
**Mitigation:** show concise history summary in console and link to deeper history when needed.

### Risk 5: Operator still needs too much context switching
**Mitigation:** prioritize failed criteria, remediation, latest status, and actionability in one place.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- acceptance-aware recovery item model or adapter
- acceptance-driven recovery categories
- recovery list inclusion for acceptance-significant items
- recovery detail acceptance sections
- acceptance retry/re-run action integration
- completion block visibility
- documentation updates
- automated tests

---

## 14. Definition of Done

This feature is considered done only when:

1. acceptance issues are first-class recovery concerns in the console,
2. operators can understand failed or blocked acceptance without leaving the Recovery Console,
3. re-acceptance and related actions are practically available,
4. acceptance-based completion blocking is visible and understandable,
5. the operator experience feels more unified and platform-native.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as operator-surface integration rather than acceptance subsystem redesign,
- keep the Recovery Console focused and actionable,
- surface acceptance data only where it matters for recovery,
- reuse canonical acceptance artifacts and flows,
- optimize for reduced operator context switching.

Recommended planning questions:

- what acceptance states are truly recovery-significant?
- what is the minimum useful acceptance summary for recovery use?
- which acceptance actions are safe to expose from the console?
- how should repeated failed acceptance be summarized?
- how should completion blocking be shown most clearly?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- how acceptance-related items now appear in the Recovery Console,
- what acceptance details are visible,
- what actions are available,
- how completion blocking is surfaced,
- how this reduces operator context switching.

It should not claim completion merely because acceptance artifacts are linked somewhere.

---

## 17. Summary

Feature 078 unifies two major platform capabilities:

- the acceptance subsystem
- the Recovery Console operator surface

It ensures that failed, blocked, or pending acceptance becomes part of the same operator recovery workflow rather than a disconnected side process.

In short:

> **078 makes acceptance recovery-visible, action-ready, and operator-native inside async-dev.**
