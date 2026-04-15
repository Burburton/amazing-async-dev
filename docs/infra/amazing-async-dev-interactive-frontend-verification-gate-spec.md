# amazing-async-dev — Interactive Frontend Verification Gate
## Repair / Enhancement Spec

- **Spec ID:** `amazing-async-dev-interactive-frontend-verification-gate`
- **Recommended Feature ID:** `038-interactive-frontend-verification-gate`
- **Type:** Repair / Enhancement
- **Priority:** High
- **Status Intent:** Ready for canonical feature execution
- **Origin:** Derived from real dogfooding behavior where a frontend app server was started for testing, but browser-level interaction verification did not actually run. The gap was only discovered after manual follow-up.

---

## 1. Problem Statement

`amazing-async-dev` currently shows that it can:

- build frontend projects
- start local dev or preview servers
- recognize that frontend behavior should be tested
- sometimes have Playwright or equivalent browser automation capability available

However, the current workflow allows an invalid completion pattern:

1. server is started
2. test phase appears to progress
3. no real browser-level interaction verification is executed
4. the task may still be treated as if testing meaningfully occurred

This creates a serious verification gap for interactive frontend work.

For UI and interaction-oriented features, **starting a server is not the same as verifying behavior**.

A system that claims to have tested an interactive frontend feature must ensure that browser-level verification actually happened, or else explicitly record why it could not happen.

---

## 2. Why This Matters

This is not a minor procedural issue. It affects trust in delivery quality.

If frontend verification can terminate at server startup, then the system can falsely appear to have completed validation while skipping the most important part: actual interaction testing.

Consequences include:

1. **False confidence**
   - features may be reported as tested when only the runtime environment was prepared

2. **Broken quality gates**
   - interactive regressions can slip through without detection

3. **Weak dogfooding value**
   - UI-heavy products depend on real navigation, click flow, state changes, and rendering verification

4. **Workflow ambiguity**
   - the system may not distinguish setup steps from actual validation steps

5. **Poor auditability**
   - a reviewer cannot reliably determine whether UI behavior was truly exercised

This is especially important for products like `amazing-visual-map`, where product value depends heavily on real interactive behavior.

---

## 3. Goal

Introduce an explicit **Interactive Frontend Verification Gate** so that:

- frontend validation does not terminate at server startup
- browser-level verification becomes mandatory for interaction-oriented work unless explicitly impossible
- Playwright or equivalent browser automation is invoked when required
- setup, readiness, execution, and evidence capture are treated as distinct stages
- test completion cannot be claimed without verification evidence or an explicit exception reason

---

## 4. Non-Goals

This spec does **not** aim to:

- require Playwright for every backend-only project
- require browser automation for purely static or non-interactive deliverables
- force brittle end-to-end suites for trivial changes with no interaction impact
- replace all unit and integration testing with browser testing
- require zero-failure E2E behavior in flaky environments without exception handling

The goal is not maximal testing everywhere.
The goal is **correct verification semantics for interactive frontend work**.

---

## 5. Target Behavioral Change

### Current undesired pattern
1. interactive feature implemented
2. app server started
3. test phase reported or implied
4. browser automation not actually executed
5. task appears more validated than it really is

### Desired pattern
1. interactive feature implemented
2. verification stage classifies required validation type
3. local server started if needed
4. server readiness confirmed
5. Playwright or equivalent browser verification executed
6. evidence captured
7. completion only allowed if:
   - browser verification passed, or
   - a valid exception was recorded

---

## 6. Core Design Principle

> **For interactive frontend work, environment setup is not verification.**

And more specifically:

> **Server startup is a prerequisite step, not a validation result.**

---

## 7. Scope of the Gate

The gate should apply when a feature or task includes any of the following:

- page interaction
- multi-step user flow
- click/tap navigation
- form entry or submission
- panel expansion/collapse
- filtering/sorting/search interaction
- visual state transitions
- route changes
- modal/drawer behavior
- canvas or map interaction
- drag/drop or gesture interaction
- cross-surface navigation
- UI state synchronization
- narrative or guided flow behavior
- user-visible animation or interaction logic

If a change meaningfully affects how a user interacts with the interface, this gate should be considered in scope.

---

## 8. Functional Requirements

## FR-1: Interactive Verification Classification
The system must classify whether a task/feature requires browser-level verification.

Minimum required classifications:
- `backend_only`
- `frontend_noninteractive`
- `frontend_interactive`
- `frontend_visual_behavior`
- `mixed_app_workflow`

For `frontend_interactive`, `frontend_visual_behavior`, and relevant `mixed_app_workflow` cases, browser-level verification is required unless explicitly waived with a recorded reason.

---

## FR-2: Setup vs Verification Stage Separation
The system must distinguish these stages:

1. build/setup
2. server start
3. server readiness check
4. browser automation execution
5. evidence/result capture
6. completion decision

A stage-2 or stage-3 success must never be treated as completion of stage 4 or stage 5.

---

## FR-3: Browser Verification Enforcement
When browser-level verification is required, the system must actually invoke Playwright or an equivalent browser automation path.

This must not remain optional if:
- the feature is interactive
- the environment supports execution
- no explicit exception condition exists

If the system reaches "server ready" and no browser run follows, verification must be marked incomplete.

---

## FR-4: Explicit Incomplete Verification State
The system must support an explicit state such as:
- `verification_incomplete`
- `browser_verification_missing`
- `awaiting_e2e_execution`

This prevents setup-only progress from being misrepresented as completed testing.

---

## FR-5: Valid Exception Handling
If browser verification cannot run, the system must record an explicit reason.

Valid reasons may include:
- Playwright tooling unavailable
- unsupported environment constraints
- browser install failure
- CI/container limitation
- missing credentials for required test path
- deterministic local blocker preventing meaningful browser run
- feature truly does not require browser interaction after reclassification

The exception must be structured and inspectable. It must not be silently implied.

---

## FR-6: Evidence Capture
For browser-level verification, the system should capture verifiable evidence such as:
- test results
- visited routes
- executed scenario names
- screenshots
- trace or report artifacts
- failure logs
- assertions performed

The exact evidence can vary, but successful verification must be supported by more than "server started."

---

## FR-7: Completion Gate
A frontend-interactive task must not be marked fully tested unless one of the following is true:

1. browser-level verification executed successfully
2. a valid structured exception was recorded and the task was explicitly classified as partially verified or verification-blocked

This gate must apply to summaries, completion reports, and continuation decisions.

---

## FR-8: Summary and Reporting Integrity
Session summaries and completion reports must explicitly distinguish:
- server was started
- server readiness confirmed
- browser verification ran
- browser verification passed/failed/skipped
- reason for skip/incomplete status

Avoid ambiguous wording such as:
- "tested frontend"
- "verified UI"
when only setup occurred.

---

## FR-9: Playwright Skill Invocation Policy
Where Playwright is the expected browser verification method, the workflow must treat it as the default required tool for qualifying interactive frontend features.

The system should not wait for the human to explicitly remind it to use Playwright after server startup.

---

## FR-10: Orchestration Continuation After Server Start
If a verification flow starts a server process, the orchestration must continue into the next verification stage rather than silently halting at the running server.

This includes handling cases where:
- the server process is long-running
- readiness must be polled
- Playwright must be launched in a separate execution path
- cleanup may be needed after verification

---

## 9. Quality Requirements

## QR-1: Verification Correctness
Interactive frontend features should be considered tested only when real interaction verification occurred or a valid exception is recorded.

## QR-2: Auditability
A reviewer should be able to inspect what was actually verified.

## QR-3: Low-Ambiguity Reporting
Reports should clearly distinguish setup from verification.

## QR-4: Continuation Safety
Long-running local server processes should not cause the workflow to stall silently.

## QR-5: Reusability
The verification gate should work across multiple frontend products, not only the current dogfood case.

---

## 10. Proposed Design Directions

### Direction A: Add Verification-Type Resolution
At task planning or test planning time, determine whether browser-level verification is required.

### Direction B: Introduce a Verification State Machine
Suggested states:
- `verification_not_started`
- `setup_in_progress`
- `server_starting`
- `server_ready`
- `browser_verification_running`
- `browser_verification_passed`
- `browser_verification_failed`
- `verification_incomplete`
- `verification_blocked`
- `verification_skipped_with_reason`

### Direction C: Add a Serve-Then-Verify Contract
If the workflow starts a frontend server for verification purposes, the orchestration must:
1. wait for readiness
2. execute browser verification
3. capture evidence
4. then summarize outcome

### Direction D: Tighten Completion Reporting
Require summaries to say exactly which verification stage was reached.

### Direction E: Add Browser Verification Evidence Hooks
Store or link artifacts that show what actually happened during browser testing.

---

## 11. Acceptance Criteria

## AC-1
For an interactive frontend feature, server startup alone cannot satisfy the test/verification requirement.

## AC-2
When browser verification is required and the environment allows it, Playwright or equivalent automation is actually executed.

## AC-3
If browser verification does not run, the result is marked incomplete or blocked, not silently treated as tested.

## AC-4
Completion reports explicitly distinguish:
- server started
- server ready
- browser verification ran
- browser verification result

## AC-5
A reviewer can inspect verification evidence or a structured skip/block reason.

## AC-6
The workflow no longer exhibits the pattern:
- start frontend server
- fail to run browser verification
- still imply that testing meaningfully occurred

## AC-7
At least one real dogfood case validates the corrected behavior on an interactive frontend project.

---

## 12. Example Desired Behavior

### Undesired behavior
- start local frontend server
- stop there
- no Playwright run
- only later discover that interaction testing never happened

### Desired behavior
- classify feature as interactive
- start local frontend server
- wait for health/readiness
- run Playwright scenarios
- capture outputs
- report pass/fail/blocked explicitly
- only then allow "tested" status

---

## 13. Suggested Implementation Breakdown

### Feature Track 1: Verification Classification
- classify feature types
- determine browser verification requirements

### Feature Track 2: Verification Orchestration
- handle server startup
- readiness detection
- browser run trigger
- cleanup handling

### Feature Track 3: Reporting and Evidence
- improve summaries
- store verification evidence
- add incomplete/blocked states

### Feature Track 4: Policy Enforcement
- prevent false completion
- require structured exception reasons

### Feature Track 5: Tests
- server started but browser not run => incomplete
- interactive feature with successful Playwright run => pass
- environment blocked => blocked with explicit reason
- noninteractive frontend feature => browser run not mandatory if properly classified

---

## 14. Testing Expectations

At minimum, add tests for:

1. **Interactive feature requires browser verification**
   - expected result: Playwright path required

2. **Server starts but browser run not triggered**
   - expected result: verification incomplete or failure state, not pass

3. **Server readiness followed by Playwright execution**
   - expected result: pass when scenarios succeed

4. **Playwright unavailable / environment blocked**
   - expected result: structured blocked/skip reason

5. **Noninteractive frontend change**
   - expected result: browser run may be waived if classification is correct

6. **Summary integrity**
   - expected result: report explicitly states what did and did not run

---

## 15. Risks and Failure Modes

### Risk 1: Over-enforcement
The gate could force browser testing for irrelevant frontend changes.
Mitigation:
- clear classification model
- explicit noninteractive path

### Risk 2: Flaky browser tests
Automation may introduce instability.
Mitigation:
- structured evidence
- blocked/failed distinction
- readiness checks
- bounded scenarios

### Risk 3: Long-running server orchestration issues
Server lifecycle may complicate execution.
Mitigation:
- explicit state model
- cleanup rules
- non-blocking orchestration

### Risk 4: Silent regressions in reporting
Summaries may remain vague.
Mitigation:
- reporting contract
- acceptance tests for summary wording/fields

---

## 16. Definition of Done

This enhancement is done when:

- interactive frontend work cannot be falsely reported as tested after only server startup
- browser-level verification is enforced when required
- Playwright or equivalent is actually invoked in qualifying cases
- incomplete/blocked verification is explicitly represented
- summaries clearly distinguish setup from validation
- at least one real dogfood frontend project confirms the corrected behavior

---

## 17. Recommended Validation Scenario

Use `amazing-visual-map` or another interaction-heavy frontend project as the validating dogfood case.

This is a good fit because it contains:
- navigation flows
- cross-surface interactions
- map-like UI behavior
- story-like guided viewing
- visual and interactive states that cannot be meaningfully validated by server startup alone

---

## 18. Requested Next Action

Use this spec to:
1. create a new feature in `amazing-async-dev`
2. implement interactive frontend verification gating
3. ensure Playwright/browser verification is executed when required
4. prevent false "tested" outcomes when only the server has been started
5. validate the fix through a real frontend dogfood workflow

---

## 19. Final Guiding Statement

> For interactive frontend work, the system must not confuse "the app is running" with "the behavior was verified."
