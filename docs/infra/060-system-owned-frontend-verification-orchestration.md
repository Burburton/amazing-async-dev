# Feature 060 — System-Owned Frontend Verification Orchestration

## Metadata

- **Feature ID**: `060-system-owned-frontend-verification-orchestration`
- **Feature Name**: `System-Owned Frontend Verification Orchestration`
- **Feature Type**: `infrastructure / execution reliability / verification orchestration`
- **Priority**: `High`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Related Features**:
  - `056-browser-verification-auto-integration`
  - `059-browser-verification-completion-enforcement`

---

## 1. Problem Statement

Feature 056 introduced browser verification capability and dev-server management primitives. Feature 059 added enforcement-oriented verification session logic and completion safeguards. However, the current system still does **not** fully solve the core execution failure mode for frontend validation tasks:

> The agent starts the frontend application or dev server, then stops progressing, and browser verification is never actually executed to completion.

In the current state, browser verification exists largely as a **tool capability** and a **policy expectation**, but not yet as a **system-owned orchestration responsibility** inside the main async-dev execution loop.

This leaves a structural gap:

- the system can provide a `browser-test` command,
- the system can describe enforcement expectations,
- but the system does **not yet reliably take over verification execution** after frontend startup,
- and success/review progression can still occur without guaranteed browser verification completion in the main execution lifecycle.

This produces a repeated failure pattern:

1. frontend task is identified,
2. app/server is started,
3. execution stalls or exits,
4. Playwright/browser verification is not actually completed,
5. the task may remain hanging, incomplete, or ambiguously marked.

This feature closes that gap by making frontend verification **system-owned**, not agent-optional.

---

## 2. Goal

Establish a **system-owned frontend verification orchestration layer** that guarantees:

- frontend verification is triggered automatically by async-dev when required,
- browser verification execution is orchestrated by the runtime, not delegated solely to the agent,
- verification results are captured in structured execution state,
- success and review progression are blocked unless required verification has either:
  - completed successfully, or
  - failed with an explicit, structured, policy-accepted exception outcome.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the Playwright/browser verification implementation itself,
- replace existing `browser-test` verification logic,
- add new browser automation frameworks,
- introduce visual regression testing,
- implement product-specific test scenarios beyond current verification scope,
- solve arbitrary backend/service validation unrelated to frontend/browser flows.

This feature is about **execution ownership and orchestration**, not about inventing a new browser test engine.

---

## 4. Core Design Principle

### 4.1 Shift of Ownership

The most important architectural change is:

**Frontend verification must become system-owned rather than agent-owned.**

That means:

- the agent may still write code, prepare commands, or propose verification details,
- but async-dev itself must own the lifecycle of:
  - deciding whether verification is required,
  - starting or attaching to the dev server,
  - running browser verification,
  - collecting results,
  - enforcing success gating.

### 4.2 Architectural Reframing

The overall model must be:

- **Feature 056** = capability layer
- **Feature 059** = policy / enforcement primitives
- **Feature 060** = orchestration integration layer

Feature 060 is the integration feature that finally binds those layers into the actual run-day execution path.

---

## 5. Target Outcomes

After this feature is complete, async-dev must behave as follows for frontend-scoped work:

1. Detect that the task requires frontend/browser verification.
2. Ensure dev server readiness through system-managed orchestration.
3. Execute browser verification automatically.
4. Persist structured verification results into execution artifacts.
5. Prevent success completion if verification was required but never executed.
6. Prevent silent hangs after frontend startup.
7. Surface explicit status when verification fails, times out, or is skipped via an accepted exception path.

---

## 6. Required Functional Changes

### 6.1 Introduce Verification Orchestrator

Add a dedicated orchestration module, for example:

- `runtime/browser_verification_orchestrator.py`

This module is responsible for high-level verification lifecycle management, not low-level browser scripting.

Its responsibilities must include:

- determine whether frontend verification is required for the current execution,
- create and manage verification session state,
- invoke dev server preparation / readiness handling,
- invoke browser verification execution,
- capture structured results,
- apply timeout / stall / reminder policies,
- return a final orchestration result to run-day or equivalent main execution flow.

This module must act as the primary integration point between:

- existing browser verification capability,
- existing session/enforcement logic,
- main runtime execution orchestration.

### 6.2 Integrate Into Main Execution Flow

The orchestrator must be integrated into the real execution paths, rather than remaining a side command.

At minimum, the feature must review and integrate with the main run-day lifecycle, including the relevant execution modes currently used by async-dev.

Expected touchpoints include:

- `cli/commands/run_day.py`
- live execution path(s)
- mock execution path(s), where applicable
- external execution result handling / post-execution verification stage

The critical requirement is:

> If the execution is frontend-scoped and requires browser verification, the main execution flow must call the orchestrator directly.

No successful frontend execution path should rely on “the agent remembered to run browser verification manually.”

### 6.3 External Mode Post-Execution Verification

Special care must be taken for external execution mode.

In external mode, agents or external tools may:

- modify code,
- start dev servers,
- stop at “server ready,”
- fail to complete browser verification.

Feature 060 must ensure that async-dev itself performs a system-owned verification phase after external work returns control, rather than trusting the external tool to have completed end-to-end verification.

This means the orchestration design must support:

- post-external-execution verification initiation,
- local system-owned verification execution,
- explicit failure classification if the external flow did not produce a valid verification result.

### 6.4 Structured Verification Result Persistence

Execution artifacts must include structured browser verification state.

At minimum, execution results must record fields equivalent to:

- whether verification was required,
- whether verification was started,
- whether verification completed,
- whether verification succeeded,
- failure reason / timeout reason / exception reason,
- dev server start / attach outcome,
- timestamps or lifecycle markers sufficient for debugging.

This state must be persisted in a stable, machine-readable structure so that:

- success gating can use it,
- audit / review flows can inspect it,
- future workflow automation can reason over it.

### 6.5 Hard Success Gate

Success must be blocked when:

- the task requires frontend/browser verification,
- verification did not execute to a terminal state,
- and no structured exception path authorizes bypass.

This must become a **runtime-enforced gate**, not merely an instruction in prompts or documentation.

Acceptable terminal states must be explicit, for example:

- `verified_success`
- `verified_failure`
- `verification_timeout`
- `verification_exception_accepted`
- `verification_skipped_by_policy` (only if explicitly supported and justified)

Unacceptable ambiguous states must include:

- server started but verification never run,
- verification required but status missing,
- verification session created but never finalized,
- success marked without browser verification evidence.

### 6.6 Anti-Stall Handling

The orchestration layer must explicitly address the “server started, then nothing happens” failure mode.

It must include logic for:

- max wait windows,
- heartbeat / lifecycle progress tracking where appropriate,
- timeout escalation,
- clear terminal failure emission instead of indefinite hanging.

The system must prefer an explicit failure outcome over silent non-termination.

---

## 7. Detailed Requirements

## 7.1 Verification Requirement Detection

The system must determine whether the current task requires frontend verification using structured signals, not only prompt prose.

Potential sources may include:

- verification type metadata,
- task classification,
- pack metadata,
- execution mode flags,
- explicit frontend / UI / browser scope markers.

The design must document the canonical source of truth and the precedence order if multiple signals exist.

## 7.2 Orchestrator API Contract

The new orchestrator should expose a stable internal contract, such as:

- input:
  - execution context
  - task / pack metadata
  - verification requirements
  - working directory / project context
- output:
  - orchestration result object
  - structured verification result
  - terminal status classification
  - optional remediation guidance

The exact Python interface may vary, but the feature must define a clear internal API boundary.

## 7.3 Dev Server Lifecycle Integration

The orchestrator must reuse existing dev server management functionality where appropriate rather than duplicating startup logic.

It must support:

- start server if needed,
- attach to already-running server if supported,
- wait for readiness,
- fail clearly if readiness cannot be achieved,
- teardown or preserve lifecycle according to current runtime policy.

The ownership boundary between the orchestrator and `dev_server_manager` must be clearly documented.

## 7.4 Browser Verification Invocation

The orchestrator must invoke the existing browser verification capability through a reusable internal interface rather than shelling out blindly when avoidable.

If a CLI fallback is still necessary in some modes, that fallback must be:

- explicit,
- documented,
- observable in logs / execution artifacts.

Preferred architecture:

- runtime code calls runtime/browser verifier functions directly,
- CLI remains a human/operator entry point, not the primary orchestration mechanism.

## 7.5 Terminal State Model

A formal verification terminal state model must be defined.

Recommended states include:

- `not_required`
- `required_not_started`
- `in_progress`
- `success`
- `failure`
- `timeout`
- `exception_accepted`
- `skipped_by_policy`

The exact names may differ, but the feature must eliminate ambiguous “unknown” completion semantics.

## 7.6 Review / Audit Compatibility

The structured verification result must be easy for later audit or review steps to consume.

Reviewing flows must be able to answer:

- Was frontend verification required?
- Did it run?
- Did it finish?
- What was the outcome?
- If bypassed, why was bypass allowed?

This feature should not require reviewers to infer correctness from freeform logs.

---

## 8. Expected File Changes

The exact file list may vary, but the implementation is expected to touch files in categories like the following.

### 8.1 New Runtime Modules

Potential new files:

- `runtime/browser_verification_orchestrator.py`

Possible companion files if needed:

- `runtime/browser_verification_state.py`
- `runtime/browser_verification_result.py`

### 8.2 Existing Runtime / CLI Integrations

Likely updates:

- `cli/commands/run_day.py`
- `runtime/verification_enforcer.py`
- `runtime/verification_session.py`
- `runtime/browser_verifier.py`
- `runtime/dev_server_manager.py`
- execution result / artifact model files
- logging / trace helpers if present

### 8.3 Documentation Updates

Must update relevant canonical docs, potentially including:

- `README.md`
- `AGENTS.md`
- infra feature index / roadmap / status docs
- any execution lifecycle docs referencing frontend verification
- any canonical docs describing success gating or execution completion semantics

Documentation must reflect that frontend verification is now system-owned orchestration, not only a recommended agent behavior.

---

## 9. Acceptance Criteria

## AC-001 Orchestrator Exists
A dedicated runtime orchestration module for frontend verification exists and is used by the main execution path.

## AC-002 Run-Day Integration
The main execution flow invokes the verification orchestrator automatically for frontend/browser verification tasks.

## AC-003 External Mode Coverage
External execution mode includes a system-owned post-execution browser verification phase for frontend tasks.

## AC-004 Structured Result Persistence
Execution artifacts persist structured browser verification result data sufficient for gating, review, and debugging.

## AC-005 Hard Success Gate
A frontend task that requires verification cannot be marked successful unless verification reaches an accepted terminal state.

## AC-006 Anti-Stall Enforcement
The “server started and then nothing happens” scenario terminates as an explicit verification failure / timeout rather than hanging indefinitely.

## AC-007 Reuse Existing Capability
The implementation reuses existing 056 and 059 capability/policy logic rather than duplicating the entire browser verification stack.

## AC-008 Documentation Alignment
Canonical documentation is updated to reflect the new ownership model and runtime behavior.

## AC-009 Tests Added
Automated tests cover the new orchestration behavior, including success, timeout, missing verification, and external-mode cases.

---

## 10. Test Requirements

The feature must include automated test coverage for the orchestration layer and main integration paths.

At minimum, tests should cover:

### 10.1 Required Verification Success Path
- task classified as frontend verification required,
- dev server is prepared,
- browser verification runs,
- structured success result is recorded,
- execution may proceed to success.

### 10.2 Missing Verification Rejected
- frontend verification required,
- verification not executed,
- success attempt is rejected.

### 10.3 Timeout Path
- frontend server starts or partially starts,
- verification does not complete,
- orchestrator emits timeout terminal state,
- execution does not hang indefinitely.

### 10.4 Verification Failure Path
- browser verification runs and fails,
- structured failure result is persisted,
- success is blocked.

### 10.5 External Mode Recovery Path
- external execution returns without valid browser verification completion,
- async-dev triggers system-owned verification,
- final result reflects actual verification outcome.

### 10.6 Exception / Bypass Path
- bypass is allowed only through an explicit structured rule,
- exception reason is persisted,
- auditing can distinguish this from normal success.

Tests may be split across unit, integration, and command-level suites depending on current repo conventions.

---

## 11. Implementation Guidance

## 11.1 Preferred Refactor Strategy

Implementation should proceed in this order:

1. define the orchestration state/result model,
2. introduce the runtime orchestrator,
3. integrate orchestrator into `run_day`,
4. connect success gating to structured verification terminal states,
5. add tests,
6. update docs.

This sequence minimizes the chance of another “policy exists but main loop does not actually use it” outcome.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- adding only more AGENTS instructions without runtime enforcement,
- relying only on CLI shell-outs from prompts,
- duplicating dev server logic outside the existing manager,
- duplicating browser verifier internals,
- introducing success conditions based on loose log-text matching,
- allowing ambiguous incomplete states to pass as success.

## 11.3 Backward Compatibility

The implementation should preserve existing non-frontend execution behavior as much as possible.

Tasks that do not require browser verification should not be forced through unnecessary verification orchestration.

---

## 12. Risks and Mitigations

### Risk 1: Integration complexity across multiple execution modes
**Mitigation:** introduce a single orchestrator boundary and route all relevant frontend flows through it.

### Risk 2: Duplicate logic between 056, 059, and 060
**Mitigation:** treat 056 as capability, 059 as enforcement primitives, and 060 as orchestration glue.

### Risk 3: Continued ambiguity in success semantics
**Mitigation:** define explicit terminal states and enforce them in runtime gating.

### Risk 4: External mode remains partially trusted
**Mitigation:** require system-owned post-external verification for frontend-scoped tasks.

### Risk 5: Test flakiness
**Mitigation:** keep orchestration tests layered; unit-test state transitions separately from heavier browser/dev-server integration tests.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- runtime frontend verification orchestrator
- run-day integration for required frontend verification
- structured verification result persistence
- hard success gating tied to terminal verification states
- timeout / anti-stall behavior
- external-mode verification ownership
- automated tests
- documentation updates

---

## 14. Definition of Done

This feature is considered done only when:

1. async-dev itself owns frontend verification orchestration,
2. frontend tasks cannot silently stop after server startup,
3. browser verification is no longer optional in practice for required frontend flows,
4. success progression is blocked without a valid verification terminal state,
5. the new behavior is covered by automated tests and reflected in canonical docs.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent for implementation:

- treat this as a **runtime orchestration repair + integration feature**, not a prompt-tuning change,
- prioritize real execution-path integration over documentation-only enforcement,
- prefer direct runtime calls over CLI indirection where feasible,
- preserve existing verification modules and wrap them in a stronger orchestration boundary.

Recommended planning emphasis:

- identify the current frontend verification decision point,
- identify where `run_day` currently returns control without guaranteed verification,
- design one canonical system-owned verification path,
- wire success gating to structured terminal states.

---

## 16. Suggested Commit / Completion Framing

When implemented, the completion report should explicitly demonstrate:

- where orchestration now starts,
- where run-day invokes it,
- how external mode is covered,
- how success gating now depends on structured verification state,
- how the anti-stall failure mode is prevented.

It should not claim completion merely because a browser-test command exists.

---

## 17. Summary

Feature 060 fixes the architectural gap left after Features 056 and 059 by introducing the missing integration layer:

- 056 provided capability,
- 059 provided enforcement primitives,
- 060 makes frontend verification part of the real runtime execution contract.

This feature is successful only when async-dev can no longer “start the frontend and stop there” for tasks that require browser validation.
