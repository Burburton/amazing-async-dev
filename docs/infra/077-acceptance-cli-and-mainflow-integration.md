# Feature 077 — Acceptance CLI and Mainflow Integration

## Metadata

- **Feature ID**: `077-acceptance-cli-and-mainflow-integration`
- **Feature Name**: `Acceptance CLI and Mainflow Integration`
- **Feature Type**: `platform integration / operator interface / execution flow wiring`
- **Priority**: `High`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Target Branch**: `platform/foundation`
- **Related Features**:
  - `069-acceptance-artifact-model-foundation`
  - `070-observer-triggered-acceptance-readiness`
  - `071-isolated-acceptance-runner`
  - `072-acceptance-findings-to-recovery-integration`
  - `073-re-acceptance-loop-orchestration`
  - `074-acceptance-console-operator-visibility`
  - `075-policy-and-gating-integration-for-completion`
  - `076-platform-documentation-and-readiness-rollup-for-acceptance`

---

## 1. Problem Statement

The acceptance system defined across Features 069–076 now has artifact models, readiness logic, isolated execution, recovery integration, re-acceptance loop behavior, visibility concepts, completion gating, and end-to-end integration coverage.

However, a system that only exists as internal runtime logic and integration tests is not yet a fully usable platform capability.

The current gap is:

> acceptance may work internally, but it is not yet fully exposed as a first-class async-dev workflow.

Without CLI and mainflow integration, the acceptance system remains harder to use than it should be:

- operators may not have a clear entrypoint,
- acceptance lifecycle actions may not be directly accessible,
- run-day / resume-next-day may not yet expose acceptance naturally,
- re-acceptance may still require indirect or internal invocation,
- the acceptance loop may feel like a subsystem rather than a canonical platform capability.

This feature closes that gap by:

1. exposing acceptance through canonical CLI commands,
2. integrating acceptance trigger points into main async-dev flows,
3. making acceptance actions operable and repeatable,
4. aligning docs and operator expectations with actual platform usage.

---

## 2. Goal

Make acceptance a real, operator-usable, platform-native capability inside async-dev.

After this feature, async-dev should support a practical acceptance workflow such as:

1. execution completes,
2. acceptance readiness is evaluated,
3. acceptance can be triggered automatically and/or manually,
4. operators can inspect acceptance status/history/results,
5. failed acceptance can be retried through a clear command path,
6. acceptance becomes part of the main execution story rather than a hidden subsystem.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the acceptance artifact model,
- redesign isolated validator execution,
- replace the observer foundation,
- create a full acceptance UI platform from scratch,
- replace Recovery Console or Decision Inbox,
- rewrite all execution flows.

This feature is specifically about **CLI exposure and mainflow integration** for the already-established acceptance subsystem.

---

## 4. Core Design Principle

### 4.1 Acceptance Must Be Usable, Not Merely Implemented

A platform capability is not complete until operators and workflows can actually invoke and use it reliably.

### 4.2 Mainflow First

Acceptance should connect into async-dev’s main execution paths rather than living only behind internal helpers.

### 4.3 Manual + Automatic Paths

The system should support both:

- automatic acceptance triggering when policy/readiness allow,
- explicit operator CLI commands for inspection, rerun, and debugging.

### 4.4 Keep the Interface Narrow and Canonical

Introduce a small, clear acceptance command surface rather than many overlapping commands.

---

## 5. Target Outcomes

After this feature is complete, async-dev should support a canonical acceptance operator flow such as:

- `run-day` finishes and records `ExecutionResult`,
- acceptance readiness is evaluated,
- if policy requires, acceptance is triggered automatically,
- operator can inspect status/history/results through CLI,
- if acceptance fails, recovery path is created,
- operator or system can invoke re-acceptance after remediation,
- acceptance outcome participates in completion truth.

This should make acceptance feel like part of async-dev’s platform, not a detached experiment.

---

## 6. Required Functional Changes

### 6.1 Acceptance CLI Command Group

Introduce a canonical CLI group for acceptance operations.

Suggested commands include:

- `acceptance-run`
- `acceptance-status`
- `acceptance-history`
- `acceptance-result`
- `acceptance-retry`

Exact naming may vary, but the command surface should be coherent and small.

### 6.2 Manual Acceptance Trigger Command

Provide a command to manually trigger acceptance for a feature/run/execution where appropriate.

This command should:

- resolve the relevant acceptance context,
- validate readiness or explain why not ready,
- build or load `AcceptancePack`,
- invoke the isolated acceptance runner,
- persist `AcceptanceResult`.

### 6.3 Acceptance Status Inspection Command

Provide a command to inspect the current acceptance state of a target.

This should surface:

- acceptance readiness,
- latest attempt status,
- pass/fail/conditional/manual-review state,
- linked result artifact,
- whether re-acceptance is needed,
- whether completion is currently blocked.

### 6.4 Acceptance History Inspection Command

Provide a command to inspect prior acceptance attempts.

This should help operators answer:

- how many attempts have occurred,
- when they happened,
- what the outcome was,
- whether the current result is latest/final,
- whether recurring failure patterns exist.

### 6.5 Acceptance Retry / Re-Run Command

Provide a command to re-run acceptance after remediation or when revalidation is needed.

This command should:

- resolve the latest relevant acceptance target,
- respect retry policy where applicable,
- create a new acceptance attempt,
- persist updated result state.

### 6.6 Mainflow Integration with run-day

Integrate acceptance into `run-day` where appropriate.

Possible expected behavior:

- after `ExecutionResult` is completed,
- acceptance readiness is evaluated,
- if policy says acceptance is required and readiness is satisfied,
- `run-day` can trigger acceptance automatically or queue it explicitly.

The exact UX may vary, but the integration must be real and predictable.

### 6.7 Mainflow Integration with resume-next-day

Integrate acceptance-aware continuation into `resume-next-day` or equivalent continuation paths.

This may include:

- continuing incomplete acceptance states,
- surfacing blocked-by-acceptance situations,
- enabling recovery → re-acceptance transitions.

### 6.8 Completion Gating Integration

Ensure CLI/mainflow behavior aligns with acceptance-related completion policy.

If a feature/run is blocked on acceptance, the mainflow should expose that clearly.

This feature does not need to redefine the policy model, but it must respect and expose it consistently.

### 6.9 Documentation and Operator Guidance Update

Update docs so operators understand:

- what acceptance commands exist,
- when acceptance runs automatically,
- when manual acceptance is appropriate,
- how retry/revalidation works,
- how acceptance affects completion.

---

## 7. Detailed Requirements

## 7.1 Canonical Acceptance CLI Surface

The feature should define one canonical acceptance CLI surface.

Example:

- `asyncdev acceptance run ...`
- `asyncdev acceptance status ...`
- `asyncdev acceptance history ...`
- `asyncdev acceptance retry ...`
- `asyncdev acceptance result ...`

The exact syntax may vary, but it should be intuitive and consistent.

## 7.2 Target Resolution

Acceptance commands must clearly define what they target.

Possible target forms:

- by feature ID
- by product ID + feature
- by run ID
- by execution ID
- by acceptance attempt ID where relevant

The implementation must document target resolution semantics.

## 7.3 Acceptance Readiness Exposure

When acceptance cannot yet run, the CLI should surface why.

Examples:

- missing `ExecutionResult`
- policy does not require acceptance
- readiness prerequisites not met
- existing acceptance already terminal and no retry requested

This is critical for operator usability.

## 7.4 Result and Attempt Surfacing

Acceptance commands should make it easy to find:

- latest acceptance result
- latest status
- attempt history
- failed criteria
- remediation guidance
- linked artifacts

The CLI should not force operators to manually search files.

## 7.5 Retry Policy Awareness

The retry command should respect acceptance loop rules, such as:

- bounded retries if policy exists
- whether remediation evidence is expected
- whether retry is blocked pending other state

The UX should be clear when a retry is refused or redirected.

## 7.6 Error Handling

Commands must fail clearly and explain common issues such as:

- target not found
- acceptance not ready
- no prior attempts
- result artifact missing
- retry not allowed
- inconsistent acceptance state

### Requirement
Do not hide these failures behind vague messages.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch categories like the following.

### 8.1 New CLI Command Files

Potential new files:

- `cli/commands/acceptance_run.py`
- `cli/commands/acceptance_status.py`
- `cli/commands/acceptance_history.py`
- `cli/commands/acceptance_result.py`
- `cli/commands/acceptance_retry.py`

If grouped differently, equivalent command modules are acceptable.

### 8.2 Existing Mainflow Integration

Likely updates:

- `cli/commands/run_day.py`
- `cli/commands/resume_next_day.py`
- acceptance orchestration helpers
- target resolution helpers
- completion gate/status helpers

### 8.3 Documentation Updates

Likely updates:

- `README.md`
- acceptance roadmap / readiness docs
- CLI reference
- operator usage docs
- platform status/flow docs

---

## 9. Acceptance Criteria

## AC-001 Acceptance CLI Surface Exists
A clear acceptance-related CLI surface exists.

## AC-002 Manual Run Works
Operators can manually trigger acceptance from the CLI.

## AC-003 Status Inspection Works
Operators can inspect acceptance status in a practical, readable way.

## AC-004 History Inspection Works
Operators can inspect prior acceptance attempts.

## AC-005 Retry/Re-Run Works
Operators can re-run acceptance through a clear CLI path.

## AC-006 run-day Integration Exists
`run-day` integrates with acceptance readiness/triggering in a meaningful way.

## AC-007 resume-next-day Integration Exists
Continuation flows surface or continue acceptance-related states appropriately.

## AC-008 Completion Blocking Is Visible
When acceptance blocks completion, the mainflow/CLI reflects that clearly.

## AC-009 Documentation Updated
Operators can understand how to use the acceptance subsystem through docs and CLI help.

## AC-010 Tests Added
Automated tests cover CLI behavior, target resolution, mainflow integration, and retry semantics.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Manual Acceptance Run
- target resolves correctly,
- readiness is checked,
- acceptance runs,
- result is persisted.

### 10.2 Acceptance Status Command
- status command shows latest acceptance state and blocking conditions correctly.

### 10.3 Acceptance History Command
- history command shows multiple attempts in correct order.

### 10.4 Acceptance Retry Command
- retry creates a new attempt when allowed,
- refuses or explains when retry is not allowed.

### 10.5 run-day Trigger Path
- after `ExecutionResult`, `run-day` evaluates readiness and triggers or exposes acceptance appropriately.

### 10.6 resume-next-day Continuation Path
- continuation flow recognizes and handles acceptance-related incomplete/blocked states.

### 10.7 Target Resolution Errors
- CLI clearly handles unknown target, missing artifacts, or inconsistent state.

### 10.8 Documentation/Help Integrity
- CLI help and operator docs match implemented behavior.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. define canonical CLI command surface,
2. implement target resolution helpers,
3. implement `acceptance-run`,
4. implement `acceptance-status` and `acceptance-result`,
5. implement `acceptance-history`,
6. implement `acceptance-retry`,
7. wire `run-day`,
8. wire `resume-next-day`,
9. update docs,
10. add tests.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- introducing too many overlapping acceptance commands,
- exposing commands without clear target semantics,
- making acceptance only manually callable with no mainflow integration,
- hiding blocking conditions,
- making retry behavior opaque,
- leaving operators to infer state from artifact paths manually.

## 11.3 Backward Compatibility

This feature should extend current mainflows without destabilizing them.

Where acceptance is not required by policy, the system should remain understandable and not overburden simple flows.

---

## 12. Risks and Mitigations

### Risk 1: CLI surface becomes confusing
**Mitigation:** keep the acceptance command family small and canonical.

### Risk 2: Mainflow integration introduces unexpected blocking
**Mitigation:** respect configurable policy and make blocking reasons explicit.

### Risk 3: Retry semantics become unclear
**Mitigation:** centralize retry policy awareness and provide strong error/help text.

### Risk 4: Operators still cannot find acceptance artifacts easily
**Mitigation:** make status/result/history commands artifact-aware and human-readable.

### Risk 5: Acceptance stays too hidden in docs
**Mitigation:** update README, CLI reference, and operator docs together.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- canonical acceptance CLI command group
- manual acceptance run command
- acceptance status inspection command
- acceptance history inspection command
- acceptance retry/re-run command
- run-day integration
- resume-next-day integration
- documentation updates
- automated tests

---

## 14. Definition of Done

This feature is considered done only when:

1. acceptance is callable and inspectable through async-dev CLI,
2. acceptance participates in main execution flows rather than only internal helpers,
3. operators can re-run and inspect acceptance without manual artifact spelunking,
4. acceptance-related blocking is visible and understandable,
5. the acceptance subsystem has become a practical platform capability.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as the transition from internal acceptance subsystem to real platform capability,
- prioritize usability and canonical flows,
- expose a small but complete CLI surface,
- wire acceptance into run-day and resume-next-day meaningfully,
- keep docs aligned with the implemented behavior.

Recommended planning questions:

- what is the smallest canonical acceptance CLI surface?
- how should targets resolve?
- when should run-day trigger acceptance automatically?
- what should resume-next-day do when acceptance is pending or blocked?
- how should acceptance blocking be communicated to operators?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- what acceptance commands now exist,
- how an operator manually runs and inspects acceptance,
- how run-day and resume-next-day now integrate with acceptance,
- how retry/revalidation works,
- how acceptance blocking is surfaced.

It should not claim completion merely because the runtime can call acceptance internally.

---

## 17. Summary

Feature 077 makes acceptance a first-class, operator-usable async-dev capability.

It does this by:

- exposing acceptance through canonical CLI commands,
- integrating acceptance into main execution flows,
- making retry/revalidation practical,
- aligning operator understanding with platform behavior.

In short:

> **077 turns acceptance from an internal subsystem into a real platform workflow.**
