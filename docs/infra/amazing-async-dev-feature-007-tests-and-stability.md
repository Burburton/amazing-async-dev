# Feature 007 — Tests & Stability

## 1. Feature Summary

### Feature ID
`007-tests-and-stability`

### Title
Tests & Stability

### Goal
Establish a minimal but reliable automated safety net for the current `amazing-async-dev` core workflow, so future changes do not silently break the validated async development loop.

### Why this matters
At this stage, the repository already has a meaningful working core:

- core object system
- day loop CLI
- single feature demo
- failure / blocker / decision handling
- init / new-product / new-feature

The project is no longer at the “can this concept work at all?” stage.  
It is now at the “can this be changed safely over time?” stage.

Without a stability layer:
- regressions will be discovered too late
- CLI behavior may drift unexpectedly
- file outputs may become inconsistent
- `RunState` semantics may break silently
- future features will become slower and riskier to develop

This feature exists to protect the validated core before more capabilities are added.

---

## 2. Objective

Build a focused test and stability layer for the current repository so that the core async development path remains safe to evolve.

This feature should provide confidence in four areas:

1. CLI command behavior
2. core state transitions
3. artifact generation and file layout
4. failure-path clarity and error messaging

The intent is not to reach exhaustive test coverage.  
The intent is to protect the most important behaviors.

---

## 3. Scope

### In scope
- establish a test structure for the repository
- add tests for core CLI commands
- add tests for `RunState` transition behavior
- add tests for artifact generation
- add tests for external-tool-mode result collection assumptions
- validate basic error handling and failure messaging
- improve stability where tests reveal fragile logic
- ensure the validated happy path remains protected

### Out of scope
- live API mode
- archive / completion archive flow
- dashboard or UI
- multi-provider integration
- performance benchmarking
- full end-to-end tool execution against real OpenCode processes
- exhaustive test coverage for every future extension point

---

## 4. Success Criteria

This feature is successful when:

1. the repository has a clear automated test structure
2. the main CLI workflow is protected by basic automated tests
3. core `RunState` transitions are covered
4. key output artifacts are validated by tests
5. failure conditions produce stable and understandable outcomes
6. future refactors can be done with reasonable confidence

---

## 5. Core Design Principles

### 5.1 Protect the validated path first
Focus first on the workflows that have already been proven useful.

### 5.2 Test behavior, not implementation details
Tests should validate externally meaningful behavior, not internal code layout.

### 5.3 Keep the first layer small but high value
Do not build an oversized test system.  
Protect the core and expand later.

### 5.4 Prefer deterministic tests
Where possible, avoid relying on real external tool execution.

### 5.5 Stability includes error clarity
A failing command with a clear, correct message is often better than a silent bad state.

---

## 6. Main Areas to Cover

## 6.1 CLI command tests

### Commands to prioritize
- `asyncdev init`
- `asyncdev new-product`
- `asyncdev new-feature`
- `asyncdev plan-day`
- `asyncdev review-night`
- `asyncdev resume-next-day`

### Test expectations
Each command should be validated for:
- expected files/directories created
- expected output artifacts generated
- expected exit behavior
- expected behavior under missing or invalid inputs

### Notes
`run-day` can be covered in a controlled way without requiring real external tool execution.

---

## 6.2 RunState transition tests

### Transitions to prioritize
- initial state creation
- planning → executing
- blocked → resumed
- failed → blocked
- decision-needed persistence
- completion-ready state handling

### Test expectations
- state transitions must be explicit
- illegal transitions should not silently pass
- required fields should remain consistent after transitions

### Notes
This area is one of the most important long-term protection layers.

---

## 6.3 Artifact generation tests

### Artifacts to prioritize
- `ExecutionPack.yaml`
- `ExecutionPack.md`
- `ExecutionResult`
- `DailyReviewPack`
- generated `product-brief`
- generated `feature-spec`
- generated initial `runstate`

### Test expectations
- files exist at expected paths
- file content contains required sections/fields
- YAML and Markdown variants stay aligned where expected
- generated artifacts remain parseable and usable

---

## 6.4 External Tool Mode stability checks

### What to verify
- `ExecutionPack.md` is created at the expected location
- result collection expects the correct result file path
- missing result file yields a clear error or wait state
- malformed result file yields a clear validation failure
- external-mode workflow assumptions are stable

### Notes
Do not attempt full real OpenCode process testing in this feature.  
Test the repository-side expectations instead.

---

## 6.5 Error handling and failure messaging

### Situations to test
- missing project
- missing feature
- invalid product ID
- missing `RunState`
- invalid `RunState`
- blocked feature resumed incorrectly
- result file missing
- result file malformed
- required schema fields absent

### Test expectations
- failure should be explicit
- message should be actionable
- system should not silently corrupt state

---

## 7. Deliverables

This feature must add:

### 7.1 Test structure
A clear repository test layout, for example:

```text
tests/
├─ test_cli_init.py
├─ test_cli_new_product.py
├─ test_cli_new_feature.py
├─ test_plan_day.py
├─ test_review_night.py
├─ test_resume_next_day.py
├─ test_runstate_transitions.py
├─ test_execution_pack.py
├─ test_execution_result_collection.py
└─ test_error_conditions.py
```

The exact file split can vary, but the responsibilities should be clear.

### 7.2 Core automated tests
A meaningful set of passing automated tests covering the in-scope areas.

### 7.3 Stability improvements
Small targeted code changes needed to make the system more robust where tests expose fragility.

### 7.4 Test running instructions
A documented command or short section in README/docs that explains how to run the tests.

---

## 8. Acceptance Criteria

- [ ] repository has a stable test directory structure
- [ ] `init` is covered by automated tests
- [ ] `new-product` is covered by automated tests
- [ ] `new-feature` is covered by automated tests
- [ ] `plan-day` is covered by automated tests
- [ ] `review-night` is covered by automated tests
- [ ] `resume-next-day` is covered by automated tests
- [ ] key `RunState` transitions are tested
- [ ] `ExecutionPack` generation is tested
- [ ] `ExecutionResult` collection assumptions are tested
- [ ] failure cases produce understandable outcomes
- [ ] test instructions are documented

---

## 9. Risks

### Risk 1 — Over-testing too early
Too much test infrastructure may slow iteration.

**Mitigation:** focus only on high-value behaviors first.

### Risk 2 — Testing internals instead of outcomes
Tests that are tightly coupled to implementation will be brittle.

**Mitigation:** validate observable behavior and artifacts.

### Risk 3 — Ignoring failure paths
Only testing the happy path would provide false confidence.

**Mitigation:** include blocked, failed, and missing-file cases in the first test layer.

### Risk 4 — Depending on external tools in automated tests
Tests may become flaky if they require real tool execution.

**Mitigation:** test repository-side expectations, not real external process behavior.

---

## 10. Recommended Implementation Order

1. establish test framework and basic test runner command
2. add tests for `init`, `new-product`, and `new-feature`
3. add tests for `plan-day`, `review-night`, and `resume-next-day`
4. add `RunState` transition tests
5. add artifact generation tests
6. add failure-path and error-message tests
7. patch fragile areas exposed by tests
8. document how to run the suite

---

## 11. Suggested Test Philosophy

The first test layer should answer these questions:

- can a new workspace be created reliably?
- can a new product be created reliably?
- can a new feature be initialized correctly?
- can the repository generate a valid execution pack?
- can review and resume flows operate on expected artifacts?
- does the system clearly communicate blocked/failed conditions?
- can the validated async workflow survive ordinary refactors?

If those answers are not protected by tests, the repository is not yet stable enough for fast iteration.

---

## 12. Definition of Done

Feature 007 is done when:

- the current validated core workflow is protected by a meaningful automated test suite
- key state transitions are covered
- artifact generation is verified
- important failures are explicit and understandable
- future feature work can proceed with significantly lower regression risk

If the repository still relies mostly on manual re-checking after every change, this feature is not done.
