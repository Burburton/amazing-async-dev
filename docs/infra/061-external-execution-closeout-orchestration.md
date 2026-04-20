# Feature 061 — External Execution Closeout Orchestration

## Metadata

- **Feature ID**: `061-external-execution-closeout-orchestration`
- **Feature Name**: `External Execution Closeout Orchestration`
- **Feature Type**: `infrastructure / execution lifecycle / external-mode reliability`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Related Features**:
  - `056-browser-verification-auto-integration`
  - `059-browser-verification-completion-enforcement`
  - `060-system-owned-frontend-verification-orchestration`
- **Implementation Date**: `2026-04-20`

---

## 1. Problem Statement

Feature 060 established system-owned frontend verification orchestration, but its current practical behavior still leaves a critical gap in **external execution mode**.

Today, the system can detect missing browser verification and recover during `resume-next-day`, but that means the main external execution path is still effectively:

1. async-dev triggers external execution,
2. the external tool starts working,
3. the external tool may start the frontend server and then stall,
4. async-dev does not immediately close the loop,
5. browser verification is only recovered later via a separate resume step.

This creates a mismatch between the intended user experience and the actual runtime behavior:

- **Intended**: external execution should run through a full closeout path, including verification and terminal classification.
- **Actual**: external execution is still largely **fire-and-forget**, with verification recovery postponed to a later continuation step.

As a result, the original user-visible failure mode is still not fully solved:

> The frontend starts, but then nothing else happens.

Feature 060 improved ownership of verification logic, but the system still does **not** fully own the **external execution closeout lifecycle**.

---

## 2. Goal

Introduce a **closeout orchestration layer for external execution mode** so that async-dev can automatically carry an external run from trigger through terminal closeout, including post-external system-owned verification when required.

The system must no longer depend on `resume-next-day` as the primary path for finishing frontend verification after external execution.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the browser verification implementation,
- replace Feature 060 orchestration,
- eliminate `resume-next-day`,
- make external tools fully interactive or permanently supervised at every token,
- redesign the whole async-dev day loop,
- add unrelated backend verification features.

This feature specifically addresses the **gap between external trigger and terminal closeout**.

---

## 4. Core Design Principle

### 4.1 Primary Path vs Fallback Path

The architectural correction is:

- **Primary path**: `run-day` external execution must attempt to close out the execution in the same lifecycle.
- **Fallback path**: `resume-next-day` remains available only as a recovery / continuation path if the closeout flow was interrupted.

Today the system behaves roughly the other way around. This feature reverses that.

### 4.2 System-Owned Closeout

Once async-dev triggers external execution, it must also own the logic for deciding:

- whether external execution has truly reached a usable completion point,
- whether frontend verification is still missing,
- whether post-external verification must run now,
- whether the run has stalled,
- whether the execution should end in success, failure, timeout, or pending-recovery.

---

## 5. Target Outcomes

After this feature is complete, external mode should behave as follows:

1. `run-day --mode external --trigger` starts the external execution.
2. async-dev enters an **external closeout phase** rather than immediately treating the run as complete.
3. The system monitors for execution result availability / closeout readiness.
4. If frontend verification is required and missing, async-dev automatically runs **post-external system-owned verification** during the same closeout lifecycle.
5. The run reaches an explicit terminal or recoverable state.
6. `resume-next-day` is only needed if the closeout flow was interrupted, not as the normal completion mechanism.

---

## 6. Required Functional Changes

### 6.1 Introduce External Closeout Orchestrator

Add a dedicated orchestration component, for example:

- `runtime/external_execution_closeout.py`

This module is responsible for managing the post-trigger lifecycle of external execution.

Its responsibilities must include:

- waiting for external execution artifacts / result readiness,
- determining whether a valid execution result exists,
- determining whether required frontend verification is still missing,
- invoking Feature 060 post-external/system-owned verification when needed,
- classifying the final closeout state,
- persisting closeout-related status into execution artifacts.

This module must be a real runtime orchestrator, not only a helper utility.

### 6.2 Integrate External Closeout Into Run-Day

`run-day` external mode must no longer stop at “triggered external execution”.

Instead, after trigger, the main flow must enter a **closeout-aware phase**.

That phase may:

- poll for result state,
- detect explicit completion markers,
- detect missing verification,
- invoke post-external verification,
- time out with structured terminal classification,
- emit a recoverable pending state if necessary.

This integration must happen in the real execution path, not only in docs or prompts.

### 6.3 Move Post-External Verification Forward

Post-external verification must no longer be primarily owned by `resume-next-day`.

Instead:

- `run-day` external closeout becomes the **primary location** for post-external verification,
- `resume-next-day` becomes a **fallback recovery path** if the closeout phase was interrupted or not completed.

This is the central behavioral shift of the feature.

### 6.4 External Closeout State Model

A structured closeout state model must be introduced.

Recommended states include:

- `external_execution_triggered`
- `external_execution_pending`
- `external_execution_result_detected`
- `post_external_verification_required`
- `post_external_verification_running`
- `post_external_verification_completed`
- `external_execution_stalled`
- `closeout_timeout`
- `closeout_completed_success`
- `closeout_completed_failure`
- `closeout_recovery_required`

Exact naming may vary, but the model must clearly separate:

- external execution lifecycle,
- verification lifecycle,
- terminal closeout outcome.

### 6.5 Terminal Classification

External-mode runs must no longer end in ambiguous states such as:

- external tool triggered, no closeout result,
- frontend server started, but verification never run,
- execution result partially written, but terminal meaning unclear.

The system must classify each run into an explicit terminal or recoverable state, such as:

- success,
- failure,
- verification failure,
- closeout timeout,
- stalled,
- recovery required.

### 6.6 Timeout and Stall Detection

The closeout layer must explicitly detect the common failure pattern where the external tool reaches a partial point like “dev server ready” and then makes no meaningful forward progress.

The system must define:

- maximum closeout wait window,
- polling or readiness check cadence,
- stall detection logic,
- terminal timeout behavior,
- recovery behavior if the process cannot be conclusively finished.

The system must prefer structured failure / recovery-required states over indefinite waiting.

### 6.7 Reuse Feature 060 Orchestration

This feature must not duplicate frontend verification orchestration.

Instead:

- Feature 060 remains the canonical system-owned frontend verification orchestration layer,
- Feature 061 decides **when** to invoke that orchestration inside external-mode closeout,
- Feature 061 handles the external lifecycle gap around it.

---

## 7. Detailed Requirements

## 7.1 Canonical Closeout Entry Point

The feature must define a single canonical entry point for external execution closeout, such as:

- `orchestrate_external_closeout(...)`

This entry point should take:

- execution context,
- execution pack / task metadata,
- product / workspace context,
- existing execution result if any,
- timeouts / policy configuration.

It should return:

- closeout result object,
- final external closeout state,
- updated verification result if applicable,
- whether recovery is required,
- terminal classification for the main loop.

## 7.2 Execution Result Discovery

The closeout flow must be able to detect whether external execution has produced a usable result.

This may involve:

- checking for execution result artifact existence,
- checking whether the artifact is valid and readable,
- determining whether browser verification fields are present,
- determining whether the result is terminal, partial, or insufficient.

The detection logic must be explicit and testable.

## 7.3 Missing Verification Detection

The closeout flow must reuse the same canonical rules for deciding whether browser verification is required and missing.

It must not rely on ad hoc log scanning or guesswork.

The system must be able to answer:

- was frontend verification required?
- was it already completed?
- if not, should system-owned post-external verification run now?

## 7.4 Post-External Verification Trigger Policy

The closeout orchestrator must define exactly when to invoke Feature 060 orchestration.

Recommended condition:

- external execution returned control or yielded a usable result artifact,
- frontend verification is required,
- verification is missing or non-terminal,
- policy allows system-owned recovery now.

This decision policy must be encoded in runtime behavior.

## 7.5 Main Loop Integration

`cli/commands/run_day.py` must be updated so that external mode includes:

1. trigger external execution,
2. enter closeout orchestration,
3. persist closeout result,
4. only then exit with a terminal or recovery-required classification.

It must no longer behave like a pure one-shot handoff when closeout logic is applicable.

## 7.6 Resume-Next-Day Fallback Semantics

`resume-next-day` must still support recovery, but its semantics should be explicitly updated:

- it is the fallback continuation path,
- it resumes an interrupted or incomplete closeout,
- it should not be described as the primary expected way to finish a normal external frontend run.

Documentation and code comments must reflect this change.

## 7.7 Artifact Persistence

Execution artifacts must persist enough state for closeout reasoning and later recovery, including:

- external closeout state,
- timestamps / lifecycle markers,
- verification requirement status,
- verification terminal state,
- whether closeout completed,
- whether fallback recovery is required.

This must be machine-readable and suitable for later auditing.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch areas like the following.

### 8.1 New Runtime Module

Potential new file:

- `runtime/external_execution_closeout.py`

Possible companion files if needed:

- `runtime/external_closeout_state.py`
- `runtime/external_closeout_result.py`

### 8.2 Existing CLI / Runtime Integration

Likely updates:

- `cli/commands/run_day.py`
- `cli/commands/resume_next_day.py`
- `runtime/browser_verification_orchestrator.py` or equivalent Feature 060 module
- execution result / artifact model files
- logging / trace helpers
- policy / timeout config files if such structure exists

### 8.3 Documentation Updates

Must update canonical docs, potentially including:

- `README.md`
- `AGENTS.md`
- docs describing external execution lifecycle
- docs describing resume-next-day semantics
- infra feature index / roadmap / status docs

---

## 9. Acceptance Criteria

## AC-001 External Closeout Orchestrator Exists
A dedicated runtime orchestration component exists for external execution closeout.

## AC-002 Run-Day Uses Closeout Flow
`run-day` external mode enters a closeout phase after triggering external execution, rather than stopping at the trigger handoff.

## AC-003 Primary Post-External Verification Path Moved Forward
When frontend verification is required and missing, post-external system-owned verification is triggered during external closeout in `run-day`, not only during `resume-next-day`.

## AC-004 Explicit Closeout State Persistence
Execution artifacts persist structured external closeout state and terminal/recovery classification.

## AC-005 Stall / Timeout Handling
The system detects stalled external closeout and emits an explicit structured outcome rather than hanging indefinitely.

## AC-006 Resume-Next-Day Is Fallback
`resume-next-day` still supports recovery, but no longer represents the primary intended path for ordinary post-external frontend verification completion.

## AC-007 Reuse Feature 060
The implementation invokes and reuses Feature 060 frontend verification orchestration rather than duplicating it.

## AC-008 Documentation Alignment
Canonical docs reflect the new ownership and lifecycle behavior.

## AC-009 Tests Added
Automated tests cover closeout success, missing verification recovery, stall/timeout behavior, and fallback recovery behavior.

---

## 10. Test Requirements

At minimum, automated tests should cover the following scenarios.

### 10.1 External Trigger to Successful Closeout
- external execution is triggered,
- execution result becomes available,
- verification is already valid or is completed during closeout,
- closeout reaches structured success.

### 10.2 External Trigger with Missing Frontend Verification
- external execution yields partial result,
- frontend verification is required but missing,
- closeout flow invokes Feature 060 verification,
- result is updated and persisted.

### 10.3 External Stall
- external execution never reaches valid closeout state,
- closeout wait exceeds timeout or stall threshold,
- system emits `stalled` or `closeout_timeout`,
- no indefinite hang occurs.

### 10.4 Verification Failure During Closeout
- closeout triggers Feature 060 verification,
- verification fails,
- closeout records structured failure,
- success is blocked.

### 10.5 Recovery Path
- closeout is interrupted,
- execution artifact records recoverable incomplete state,
- `resume-next-day` resumes and completes the leftover closeout or verification.

### 10.6 Non-Frontend External Run
- external execution does not require frontend verification,
- closeout logic does not force unnecessary browser verification,
- run still reaches proper terminal classification.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. define closeout state/result model,
2. implement external closeout orchestrator,
3. integrate it into `run_day` external mode,
4. connect missing-verification detection to Feature 060 orchestration,
5. update `resume-next-day` to fallback semantics,
6. add tests,
7. update docs.

## 11.2 Avoid These Failure Patterns

Implementation must avoid:

- leaving external mode as pure fire-and-forget,
- keeping `resume-next-day` as the only real verification recovery path,
- re-implementing browser verification logic inside closeout,
- relying on freeform text logs as primary closeout truth,
- allowing ambiguous partial results to appear “good enough”.

## 11.3 Backward Compatibility

The feature should preserve existing external-mode flows as much as possible for non-frontend work.

For frontend work, behavior should become more complete and more deterministic, not more manual.

---

## 12. Risks and Mitigations

### Risk 1: External tools may not produce clean completion signals
**Mitigation:** use structured artifact/result detection with timeout and recovery-required fallback states.

### Risk 2: Overlap between Feature 060 and 061 responsibilities
**Mitigation:** keep 060 focused on frontend verification orchestration and 061 focused on external closeout timing / lifecycle ownership.

### Risk 3: Overly long blocking closeout phase
**Mitigation:** define bounded wait windows and structured stall classification.

### Risk 4: Confusing user expectations around resume-next-day
**Mitigation:** update docs and CLI messaging so resume-next-day is presented as fallback continuation, not normal completion.

### Risk 5: Increased integration complexity in run-day
**Mitigation:** introduce a single canonical closeout orchestrator entry point and keep CLI logic thin.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- external execution closeout orchestrator
- run-day external-mode closeout integration
- primary-path post-external verification trigger during closeout
- structured closeout state persistence
- timeout / stall classification
- resume-next-day fallback semantics update
- automated tests
- documentation updates

---

## 14. Definition of Done

This feature is considered done only when:

1. external mode no longer behaves as pure fire-and-forget for frontend closeout-sensitive work,
2. post-external verification is attempted in the main closeout path,
3. a frontend external run cannot quietly stop after dev-server startup without structured closeout handling,
4. `resume-next-day` is no longer the primary expected way to finish a normal external frontend verification flow,
5. the new lifecycle is covered by tests and reflected in canonical docs.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as an **external lifecycle repair feature**,
- center the implementation on `run_day` closeout ownership,
- keep Feature 060 as the canonical frontend verification engine,
- make `resume-next-day` a continuation safety net, not the main happy path.

Recommended planning questions:

- where exactly does external mode return control today?
- what constitutes a valid closeout-ready result?
- what timer / polling strategy is acceptable?
- when does missing verification become eligible for immediate system-owned recovery?
- how should recovery-required state be surfaced to operators?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- where external closeout now begins,
- how run-day remains in control after trigger,
- when post-external verification is invoked automatically,
- how stall / timeout states are classified,
- what remains for resume-next-day as fallback only.

It should not claim completion merely because resume-next-day can still repair missing verification.

---

## 17. Summary

Feature 061 closes the next architectural gap after Feature 060.

- Feature 060 made frontend verification system-owned.
- Feature 061 makes **external execution closeout** system-owned.

Together, they move async-dev from:

- trigger external tool,
- hope it finishes,
- repair later with resume-next-day,

toward:

- trigger external tool,
- keep ownership of closeout,
- verify and classify in the same execution lifecycle,
- fall back to resume-next-day only when genuinely needed.
