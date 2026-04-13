# 036-run-day-intent-alignment-executionpack-to-run-guardrails

## Title
Run-Day Intent Alignment / ExecutionPack-to-Run Guardrails

## Summary
Align `run-day` with the planning intent and bounded execution target produced by Feature 035, so day execution follows the shaped plan more faithfully and avoids drifting into actions that do not match the current daily objective.

This feature should strengthen the main async-dev loop by making the transition from:

- `review-night`
- `resume-next-day`
- `plan-day`
to
- `run-day`

more operationally consistent.

## Relationship to Earlier Features

### 026 — Optional Advisor Integration Positioning
Feature 026 clarified that advisor is optional and that async-dev must remain independently usable.

Relevance to 036:
- run-day guardrails must work for both direct mode and starter-pack mode
- no dependency on advisor should be introduced
- initialization context may inform execution intent, but must remain optional

### 027 — Optional Initialization Verification
Feature 027 established explicit initialization verification.

Relevance to 036:
- if the current day's plan is verification-first, run-day should respect that and avoid drifting into unrelated execution
- unresolved verification concerns should shape execution behavior when the plan says they matter

### 028 — Repo-linked Workspace Snapshot
Feature 028 introduced a unified workspace snapshot / operator status view.

Relevance to 036:
- run-day should execute with awareness of current workspace state and current execution target
- guardrails should rely on already-known state rather than inventing a separate execution-state worldview

### 029 — Workspace Doctor / Recommended Next Action
Feature 029 introduced operator-facing diagnosis and next-action guidance.

Relevance to 036:
- run-day should not contradict the most relevant guidance when the day plan was explicitly shaped from it
- the execution path should remain compatible with operator-facing intent

### 030 — Doctor Fix Hints / Recovery Playbooks
Feature 030 introduced recovery guidance.

Relevance to 036:
- if today's plan is recovery-oriented, run-day should prioritize recovery-compatible actions rather than normal feature expansion

### 031 — Doctor-to-Feedback Handoff
Feature 031 introduced optional feedback handoff suggestions.

Relevance to 036:
- run-day may preserve awareness of recurring friction context
- but execution must not automatically trigger feedback capture or escalation

### 032 — Doctor-to-Feedback Prefill / Handoff Draft
Feature 032 added feedback draft / prefill support.

Relevance to 036:
- if feedback context exists, it may remain visible as context
- but run-day must not treat it as an execution objective unless the operator explicitly decides so

### 033 — Review-Night Enriched Operator Pack
Feature 033 made `review-night` the primary nightly decision artifact.

Relevance to 036:
- run-day guardrails ultimately depend on the fact that planning intent is already connected to nightly decision context through later features

### 034 — Resume-Next-Day Decision Pack Alignment
Feature 034 aligned resume-next-day with the nightly pack.

Relevance to 036:
- by the time run-day begins, continuation context should already have been carried forward into planning
- run-day should respect the resulting plan, not bypass it

### 035 — Plan-Day from Resume Context / Morning Replan Alignment
Feature 035 made `plan-day` context-aware and capable of shaping a bounded daily plan based on resumed context.

Relevance to 036:
- Feature 035 produces planning intent / bounded execution direction
- Feature 036 exists to make run-day honor that intent in practice

## Why Feature 036 Matters
After Feature 035, the system can produce a more context-aware bounded daily plan.

What is still missing is stronger alignment between:
- what the day plan says
and
- what day execution actually does

Without Feature 036, planning intent risks becoming mostly advisory:
- the operator sees a good plan
- but `run-day` may still execute too generically
- or allow drift into actions that do not match the day's intended mode

Feature 036 should reduce that gap by making planning intent a meaningful execution guardrail.

## Goal
Make `run-day` aware of the current ExecutionPack's planning mode / bounded target so it can:

1. surface the intended execution mode clearly
2. prioritize execution consistent with the daily plan
3. avoid obvious drift from the day's objective
4. preserve human control
5. remain lightweight and practical

## Core Principle
`plan-day` decides today's bounded execution target.

`run-day` should execute in alignment with that target.

Feature 036 should improve alignment without:
- turning run-day into a heavy policy engine
- replacing operator judgment
- recreating doctor/review/planning logic inside execution

## Scope
Implement planning-intent-aware run-day guardrails in `amazing-async-dev`.

This feature should:
1. read planning intent / mode from the current ExecutionPack
2. show concise execution-intent context before or during run-day
3. apply lightweight guardrails against obvious plan drift
4. shape execution priority according to the day's mode
5. fall back gracefully when no planning intent is present

## Non-Goals
Do not:
- redesign the full run-day execution model
- build a complex execution policy framework
- replace Feature 020 low-interruption policy
- auto-rewrite the day's plan
- auto-run recovery, verification, closeout, or feedback actions beyond normal run-day behavior
- introduce heavy UI or orchestration layers
- require advisor or starter-pack mode
- create a second competing execution-planning system

## Main User Experience
Before or during run-day, the operator should be able to understand:

- what today's execution intent is
- what kind of day this is
- what should be prioritized first
- what kinds of execution drift should be avoided
- whether the system believes execution is aligned or potentially off-track

The operator should not need to manually remember what `plan-day` concluded in order to keep execution bounded.

## Execution Alignment Rules

### Rule 1: Respect planning mode when available
If the current ExecutionPack has a planning mode or equivalent bounded intent, run-day should treat it as the primary execution context.

### Rule 2: Prefer lightweight guardrails over heavy enforcement
The initial implementation should bias toward:
- visible alignment notes
- prioritized next steps
- warnings on obvious mismatch

rather than complex execution blocking.

### Rule 3: Allow operator override / control
Run-day should remain explicitly operator-controlled.
The system may warn or steer, but it should not become a rigid autonomous controller.

### Rule 4: Graceful fallback remains required
If no planning mode / intent is available, run-day should continue with existing behavior.

## Suggested Planning Modes to Support
The initial implementation should align with the planning modes introduced or implied by Feature 035, for example:

- `continue_work`
- `recover_and_continue`
- `verification_first`
- `closeout_first`
- `blocked_waiting_for_decision`

If exact names differ in implementation, use the repository's actual planning-mode representation.

## Expected Run-Day Behavior by Mode

### continue_work
- prioritize normal bounded execution toward today's target
- no special warning unless drift is detected

### recover_and_continue
- prioritize recovery-compatible execution first
- warn if the run appears to jump into unrelated implementation before recovery concerns are addressed

### verification_first
- prioritize verification-compatible execution
- warn if execution appears to begin unrelated implementation work before verification is handled

### closeout_first
- prioritize archive/review/finalization/closure-compatible execution
- warn if new expansion work is attempted before closeout steps are addressed

### blocked_waiting_for_decision
- surface that the workspace is blocked or decision-constrained
- discourage normal forward execution
- suggest the appropriate decision-oriented next step or wait posture

## Guardrail Style
The initial implementation should use lightweight guardrails such as:

- execution intent summary
- prioritized next step reminder
- mismatch warning when obvious drift is detected
- concise recommended command when helpful

Avoid:
- heavy interactive wizards
- automatic policy escalation
- complicated hard-stop logic beyond already-established policy mechanisms

## Drift Detection Guidance
Keep drift detection simple in the first implementation.

Good first-pass signals include:
- planning mode vs attempted execution category mismatch
- blocked mode with continued forward-progress execution
- verification-first mode with non-verification execution
- closeout-first mode with new implementation-expansion execution
- recovery-first mode with unrelated feature expansion before recovery

Use lightweight rule-based checks rather than broad semantic interpretation.

## Output Expectations
Run-day output should remain execution-oriented, but include concise alignment context.

Suggested output elements:
- current planning mode
- short execution intent summary
- bounded target reminder
- alignment status (e.g. aligned / caution / blocked-context)
- warning or note when drift is detected
- suggested next command or first step when relevant

Keep the output useful and compact.

## Conditional Display Rules

### Always show when planning intent exists
- planning mode / intent summary
- bounded target reminder

### Show when relevant
- mismatch / drift warning
- blocked-context warning
- verification-first reminder
- recovery-first reminder
- closeout-first reminder

### Keep minimal when healthy and aligned
If execution is clearly aligned with a normal continuation day, output should remain concise.

## Integration Approach
This feature should extend the existing `run-day` path rather than creating a parallel execution command.

Recommended direction:
- extend current run-day flow
- load planning intent from the active ExecutionPack
- apply lightweight alignment checks
- surface concise execution-intent guidance
- preserve one canonical run-day entry point

## Reuse Rule
Prefer reuse over duplication.

Feature 036 should reuse:
- planning mode / bounded target from Feature 035
- current workspace state
- existing execution-state information
- established policy behaviors where already present

`run-day` should consume planning intent, not recreate the full planning/doctor/review pipeline.

## Data Model Guidance
If the current ExecutionPack or run-day-facing model already contains planning-related context, reuse and extend it incrementally rather than introducing a new large execution-guardrail schema.

Possible incremental fields:
- `planning_mode`
- `bounded_target`
- `execution_intent_summary`
- `alignment_status`
- `drift_warning`
- `suggested_first_step`

Prefer small optional fields and derived summaries over a new complex policy object.

## Code Location Guidance
Integrate near the existing `run-day` implementation.

Likely integration points may include:
- run-day CLI command handling
- ExecutionPack loading
- run execution preparation
- lightweight alignment helper functions
- output rendering / serialization

Keep intent-alignment helpers close to run-day rather than creating a new large runtime policy module in this feature.

## Suggested Internal Responsibilities
A reasonable internal structure may look like:

- existing run-day flow loads active ExecutionPack
- helper extracts planning mode / bounded target
- helper computes a lightweight alignment assessment
- run-day renders concise intent summary and warnings
- execution continues under operator control

The alignment layer should remain small and execution-facing.

## Documentation Requirements
Update run-day / loop-related docs to explain:

1. `plan-day` now shapes planning intent
2. `run-day` consumes that intent
3. run-day surfaces lightweight alignment guidance and drift warnings
4. this keeps execution more faithful to the day's bounded plan
5. run-day still works without explicit planning context

## Test Requirements
Add focused tests for planning-intent-aware run-day behavior.

Minimum test coverage:

### Positive alignment tests
1. continue_work mode -> run-day shows normal aligned execution summary
2. recover_and_continue mode -> run-day surfaces recovery-first guidance
3. verification_first mode -> run-day surfaces verification-first guidance
4. closeout_first mode -> run-day surfaces closeout-first guidance
5. blocked_waiting_for_decision mode -> run-day surfaces blocked-context warning

### Drift warning tests
6. verification-first mode + non-verification execution attempt -> drift warning appears
7. closeout-first mode + expansion-style execution attempt -> drift warning appears
8. recovery-first mode + unrelated implementation attempt -> drift warning appears
9. blocked mode + forward execution attempt -> strong caution appears

### Fallback tests
10. no planning mode in ExecutionPack -> run-day falls back gracefully
11. malformed planning intent -> run-day degrades safely without breaking execution

### Output quality tests
12. run-day output remains concise when aligned
13. run-day includes intent summary when planning context exists
14. run-day does not become a heavy interactive policy wizard

## Acceptance Criteria

### AC1
`run-day` can consume planning intent / mode from the current ExecutionPack when available.

### AC2
Run-day surfaces concise execution-intent context and bounded target reminders.

### AC3
Lightweight drift warnings appear for obvious mismatches between planning mode and execution direction.

### AC4
Run-day remains explicitly operator-controlled and does not become a heavy policy engine.

### AC5
Run-day continues to work gracefully when no planning intent exists.

### AC6
The implementation reuses ExecutionPack planning context from Feature 035 rather than duplicating planning logic.

### AC7
Docs clearly explain the new alignment between plan-day and run-day.

### AC8
Tests cover aligned, mismatched, blocked, and fallback scenarios.

## Definition of Done
This feature is done when:
- run-day meaningfully reflects the day's planning intent
- the operator can see whether execution is aligned or drifting
- bounded execution becomes more practical in the day loop
- fallback behavior remains intact
- no heavy policy/orchestration layer is introduced
- docs and tests are updated accordingly

## Implementation Guidance
Keep this feature practical and execution-centered.

This is not a new autonomous controller.

It is the next alignment step in the async-dev loop:

- nightly review improves decision context
- morning resume carries it forward
- day planning shapes a bounded target
- day execution follows that target more faithfully

Prefer:
- lightweight guardrails
- concise summaries
- rule-based drift warnings
- reuse of planning intent
- graceful fallbacks
- explicit operator control
