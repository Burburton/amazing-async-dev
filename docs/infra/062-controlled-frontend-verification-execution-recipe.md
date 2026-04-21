# Feature 062 — Controlled Frontend Verification Execution Recipe

## Metadata

- **Feature ID**: `062-controlled-frontend-verification-execution-recipe`
- **Feature Name**: `Controlled Frontend Verification Execution Recipe`
- **Feature Type**: `execution reliability / frontend validation / external-agent guardrails`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Related Features**:
  - `056-browser-verification-auto-integration`
  - `059-browser-verification-completion-enforcement`
  - `060-system-owned-frontend-verification-orchestration`
  - `061-external-execution-closeout-orchestration`
- **Implementation Date**: `2026-04-20`

---

## 1. Problem Statement

Features 060 and 061 improve ownership of frontend verification and external execution closeout, but they do **not** fully solve a more immediate upstream execution problem:

> The external agent often starts the frontend dev server and then stops progressing.

In real runs, the agent may do something like:

- run `npm run build`,
- run `npm run dev`,
- confirm the dev server prints a local URL,
- then stop without:
  - opening the page,
  - running browser verification,
  - writing a structured `ExecutionResult`,
  - reaching a terminal execution outcome.

This failure mode is not primarily a closeout ownership bug. It is an **execution recipe bug**.

The current system still leaves too much freedom to the external agent in how frontend validation should be performed. That causes repeated issues such as:

- foreground-blocking dev server commands,
- inconsistent or broken backgrounding behavior,
- readiness checks that stop at “server is up,”
- browser verification never actually being invoked,
- result artifacts never being written,
- verification behavior varying from run to run.

This feature introduces a **controlled execution recipe** for frontend verification work so that external agents follow a more deterministic, system-aligned flow.

---

## 2. Goal

Define and implement a **controlled frontend verification execution recipe** that external agents must follow when validating frontend work.

The recipe must ensure the agent does **not** stop at server startup and instead proceeds through a required sequence:

1. prepare or detect verification target,
2. start the dev server in a controlled way,
3. confirm readiness through a bounded probe,
4. run browser verification,
5. persist a structured execution result,
6. emit a terminal outcome.

The system should reduce agent improvisation for frontend verification tasks and replace it with a more reliable execution contract.

---

## 3. Non-Goals

This feature does **not** aim to:

- replace Feature 060 system-owned orchestration,
- replace Feature 061 external closeout orchestration,
- redesign Playwright/browser verification internals,
- create a new UI test framework,
- introduce product-specific scripted test plans for every frontend app,
- solve all external-agent reliability issues unrelated to frontend verification.

This feature is specifically about **how the external agent executes frontend verification**, not about the entire lifecycle after the fact.

---

## 4. Core Design Principle

### 4.1 Recipe Over Improvisation

For frontend verification work, the agent must not freely invent its own sequence of shell commands every time.

Instead, the system should provide a **canonical recipe** with explicit expectations for:

- server startup,
- readiness checks,
- verification invocation,
- result writing,
- failure handling.

### 4.2 Controlled but Reusable

The recipe should be:

- reusable across frontend projects,
- generic enough for common React/Vite/Next-style workflows,
- strict enough to prevent the known “server started and then nothing happened” failure mode.

### 4.3 Execution Discipline Before Closeout Discipline

Features 060 and 061 handle orchestration and closeout ownership.  
Feature 062 hardens the **upstream execution behavior** so that those features receive more consistent, usable inputs.

---

## 5. Target Outcomes

After this feature is complete, frontend verification runs executed by an external agent should behave more like this:

1. determine the frontend verification command set,
2. start the server using a controlled helper or approved pattern,
3. probe readiness with a timeout,
4. invoke browser verification using the canonical verification path,
5. write structured result data,
6. exit with explicit success or failure.

The agent should no longer treat “dev server printed a local URL” as an acceptable stopping point.

---

## 6. Required Functional Changes

### 6.1 Define a Canonical Frontend Verification Recipe

The system must define a canonical execution recipe for frontend verification tasks.

At minimum, that recipe must require these stages:

1. **Server startup stage**
2. **Readiness probe stage**
3. **Browser verification stage**
4. **Structured result persistence stage**
5. **Terminal completion stage**

This recipe must be represented in executable behavior, not only in prose documentation.

### 6.2 Controlled Dev Server Startup

The agent must not rely on ad hoc foreground execution of commands like:

- `npm run dev`
- `pnpm dev`
- `yarn dev`

when those commands block the shell and prevent forward progress.

The implementation must provide a controlled startup approach, such as:

- a helper utility,
- a wrapped command execution path,
- or a standardized runtime entry point

that can:

- start the server in a controllable way,
- capture logs,
- detect assigned port / URL when possible,
- avoid leaving the agent stuck in a foreground session.

This feature must explicitly reduce dependence on fragile shell job control patterns like `%1`, `&`, and environment-specific behavior.

### 6.3 Bounded Readiness Probe

After startup, the agent must run a readiness probe instead of assuming success from logs alone.

The readiness probe must be:

- bounded by timeout,
- based on structured success criteria where possible,
- able to fail clearly if the app never becomes reachable.

Possible checks may include:

- HTTP response from target URL,
- expected status code or content signal,
- configured port reachability,
- canonical frontend target availability.

The system must not accept “server said ready” as equivalent to “verification complete.”

### 6.4 Mandatory Browser Verification Step

Once readiness succeeds, the recipe must proceed to browser verification.

This step must use the canonical browser verification path already established by the system, rather than leaving the agent to stop after readiness.

The recipe must make it impossible, or at least clearly non-compliant, for the external agent to finish the frontend verification task without actually invoking browser verification.

### 6.5 Mandatory Structured Result Write

After browser verification, the recipe must require the agent or the system-integrated path to write a structured result artifact.

This artifact must reflect:

- whether verification was attempted,
- whether it succeeded,
- whether the server started successfully,
- whether readiness succeeded,
- any failure or timeout reason,
- terminal execution classification.

This is essential so that downstream closeout logic does not have to infer completion from raw console logs.

### 6.6 Explicit Failure Path

If any stage fails, the recipe must still produce a structured terminal outcome rather than simply stopping.

The recipe must define explicit behavior for failures such as:

- server failed to start,
- readiness timed out,
- browser verification failed,
- result write failed,
- unexpected runtime error.

A failed run must still attempt to leave behind a machine-readable execution result wherever feasible.

### 6.7 Integrate Recipe Into External-Agent Guidance and Runtime Hooks

The recipe must be reflected in both:

- runtime or command helpers used by the agent,
- and canonical agent instructions / execution guidance.

However, this feature must **not** be reduced to AGENTS.md text alone.  
At least one meaningful runtime or helper-level enforcement point must exist.

---

## 7. Detailed Requirements

## 7.1 Canonical Invocation Path

The feature should define a single preferred invocation path for frontend verification work, such as:

- a helper command,
- a runtime module,
- or a CLI subcommand

for example:

- `asyncdev frontend-verify-run`
- `runtime/frontend_verification_recipe.py`
- `cli/commands/frontend_verify_run.py`

The exact name may vary, but the system should move toward **one canonical recipe entry point** rather than loosely coordinated shell snippets.

## 7.2 Recipe Inputs

The recipe should accept structured inputs such as:

- project/workspace path,
- frontend command metadata,
- verification target URL or port,
- verification type,
- timeout configuration,
- execution ID / artifact paths.

These inputs should be sufficient to let the recipe run predictably without the agent inventing missing pieces ad hoc.

## 7.3 Generic Frontend Support

The recipe should support the common class of local frontend apps used in async-dev dogfooding, including cases where:

- build command exists separately from dev command,
- dev server uses dynamic fallback port selection,
- target URL needs to be detected from output or config,
- frontend verification is local-browser based.

The system does not need to solve every framework-specific edge case, but it must handle the common development workflow better than freeform shelling.

## 7.4 Log and Lifecycle Capture

The recipe should capture enough lifecycle information to support debugging, such as:

- startup command used,
- selected or detected URL,
- readiness attempts,
- verification invocation marker,
- result write attempt,
- terminal state.

This data can be persisted directly or surfaced via execution artifacts/logging depending on current repo conventions.

## 7.5 Deterministic Stage Transitions

The recipe must explicitly define transitions such as:

- `server_starting -> readiness_probing`
- `readiness_probing -> browser_verification`
- `browser_verification -> result_persisting`
- `result_persisting -> completed_success`
- any stage -> `completed_failure`

The implementation does not need a full workflow engine, but these semantics must be clear in code and tests.

## 7.6 Compatibility With Features 060 and 061

This feature must fit cleanly into the architecture already established:

- Feature 060 remains the canonical frontend verification orchestration layer.
- Feature 061 remains the canonical external closeout orchestration layer.
- Feature 062 improves the quality and determinism of the **external agent’s execution behavior before closeout completes**.

The feature must reuse existing verification capabilities rather than re-implementing browser testing logic.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch files in categories like these.

### 8.1 New Runtime / CLI Components

Potential new files:

- `runtime/frontend_verification_recipe.py`
- `cli/commands/frontend_verify_run.py`

Possible companion models:

- `runtime/frontend_recipe_state.py`
- `runtime/frontend_recipe_result.py`

### 8.2 Existing Integrations

Likely updates:

- `AGENTS.md`
- `README.md`
- `cli/commands/run_day.py`
- `cli/commands/resume_next_day.py` if relevant for recovery compatibility
- `runtime/browser_verification_orchestrator.py`
- `runtime/dev_server_manager.py`
- execution result / artifact models
- docs describing external agent execution patterns

### 8.3 Documentation Updates

Must update canonical docs so that frontend verification instructions reflect the new controlled recipe rather than ad hoc shell steps.

---

## 9. Acceptance Criteria

## AC-001 Canonical Recipe Exists
A canonical controlled frontend verification recipe exists in code, not just documentation.

## AC-002 Controlled Server Startup
The recipe uses a controlled dev-server startup strategy that avoids common foreground blocking / fragile job control failure modes.

## AC-003 Bounded Readiness Probe
The recipe performs a readiness probe with timeout before browser verification.

## AC-004 Browser Verification Mandatory
The recipe explicitly proceeds from readiness to browser verification and does not stop at “server ready.”

## AC-005 Structured Result Persistence
The recipe produces or updates structured execution result data that downstream orchestration can consume.

## AC-006 Failure Still Produces Terminal Outcome
Server/startup/readiness/verification failures produce structured terminal outcomes rather than silent stops.

## AC-007 External-Agent Guidance Updated
Canonical agent instructions are updated to direct frontend verification through the controlled recipe.

## AC-008 Reuse Existing Verification Stack
The implementation reuses existing verification and orchestration modules rather than duplicating the stack.

## AC-009 Tests Added
Automated tests cover success, startup failure, readiness timeout, verification failure, and result persistence behavior.

---

## 10. Test Requirements

At minimum, the feature should include tests for these scenarios.

### 10.1 Happy Path
- controlled server startup succeeds,
- readiness probe succeeds,
- browser verification runs,
- structured result is written,
- terminal success is emitted.

### 10.2 Server Startup Failure
- server cannot be started or startup helper fails,
- structured failure result is written,
- no indefinite blocking occurs.

### 10.3 Readiness Timeout
- server command launched but target never becomes reachable,
- readiness probe times out,
- structured failure/timeout result is written.

### 10.4 Browser Verification Failure
- readiness succeeds,
- browser verification fails,
- terminal failure result is persisted.

### 10.5 Result Persistence Failure Handling
- verification completes but result persistence path errors,
- failure is surfaced clearly,
- behavior remains observable and testable.

### 10.6 Dynamic Port Handling
- server binds to a fallback or dynamically selected port,
- recipe still determines target URL or fails explicitly with a clear reason.

---

## 11. Implementation Guidance

## 11.1 Preferred Strategy

Recommended implementation order:

1. define recipe state/result model,
2. implement controlled startup + readiness handling,
3. integrate browser verification invocation,
4. integrate structured result persistence,
5. wire the recipe into external-agent execution guidance,
6. add tests,
7. update docs.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- relying on shell job control tricks as the main strategy,
- stopping after readiness instead of verification,
- leaving result persistence optional,
- solving the issue only by adding more prompt instructions,
- duplicating browser verification logic already present elsewhere,
- treating console output as the only proof of completion.

## 11.3 Backward Compatibility

The feature should minimize disruption to non-frontend workflows.

Where possible, the new controlled recipe should be applied to frontend-scoped validation paths without forcing unnecessary changes onto unrelated tasks.

---

## 12. Risks and Mitigations

### Risk 1: The recipe becomes too framework-specific
**Mitigation:** keep the recipe generic and centered on common local dev-server + readiness + browser verification flows.

### Risk 2: Overlap with Feature 060 responsibilities
**Mitigation:** keep 060 focused on orchestration/gating and 062 focused on controlled execution behavior.

### Risk 3: Dynamic port discovery remains flaky
**Mitigation:** capture startup logs, allow explicit target input, and fail clearly when URL resolution is ambiguous.

### Risk 4: External agent bypasses the recipe
**Mitigation:** update canonical instructions and integrate at least one runtime/helper-level preferred path that is easier and more reliable than ad hoc shelling.

### Risk 5: Result persistence still gets skipped
**Mitigation:** make structured result writing an explicit required stage in the recipe and cover it in tests.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- controlled frontend verification recipe implementation
- controlled dev-server startup path
- readiness probe with timeout
- mandatory browser verification step
- structured result persistence
- explicit failure handling
- updated agent guidance
- automated tests
- documentation updates

---

## 14. Definition of Done

This feature is considered done only when:

1. external agents no longer commonly stop at dev-server startup for frontend verification tasks,
2. the preferred frontend verification flow moves through startup, readiness, verification, and result writing,
3. failures produce structured terminal outcomes,
4. Features 060 and 061 receive more reliable upstream execution results,
5. the new recipe is covered by tests and reflected in canonical docs.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as an **execution recipe hardening feature**,
- focus on replacing ad hoc frontend shell behavior with a canonical controlled path,
- reuse existing verification/orchestration modules,
- do not solve this with AGENTS text only.

Recommended planning questions:

- what is the canonical recipe entry point?
- how should dynamic URL/port discovery work?
- what is the minimum structured result contract for downstream closeout?
- what startup helper pattern is robust across current dogfooding targets?
- how should failures be recorded when startup or persistence breaks?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- what the canonical frontend verification recipe entry point is,
- how dev-server startup is now controlled,
- where readiness probing occurs,
- where browser verification becomes mandatory,
- where structured result persistence happens,
- why the old “server started then stop” failure mode is now materially harder to hit.

It should not claim completion merely because AGENTS instructions were strengthened.

---

## 17. Summary

Feature 062 addresses the remaining execution-layer weakness behind repeated frontend validation stalls.

- Feature 060 made frontend verification system-owned.
- Feature 061 made external closeout system-owned.
- Feature 062 makes the **frontend verification execution recipe** more controlled and deterministic.

Together, these features move async-dev toward a frontend validation flow that is not only well-orchestrated at the end, but also well-executed from the start.
