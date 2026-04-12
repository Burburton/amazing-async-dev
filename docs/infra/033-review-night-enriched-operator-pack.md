# 033-review-night-enriched-operator-pack

## Title
Review-Night Enriched Operator Pack / Nightly Decision Hub

## Summary
Enhance `review-night` so it becomes the primary nightly operator entry point for understanding current workspace state, execution risks, next actions, recovery guidance, verification signals, and optional feedback-handoff context.

This feature should consolidate the operator-facing intelligence introduced in Features 028–032 into the existing nightly review flow, without turning `review-night` into a heavy UI layer or a separate orchestration system.

## Goal
Make `review-night` produce a more actionable nightly operator pack so a solo builder can quickly answer:

- what happened today?
- where is the workspace right now?
- is anything blocked or attention-needed?
- what should happen next?
- is recovery needed?
- is verification healthy?
- is anything worth handing off into feedback?

The goal is to reduce nightly interpretation cost and strengthen the main async-dev loop:

- `plan-day`
- `run-day`
- `review-night`
- `resume-next-day`

## Why
Features 028–032 have already added meaningful operator-facing capabilities:

- 028: workspace snapshot
- 029: doctor status + recommended next action
- 030: recovery playbooks
- 031: doctor-to-feedback handoff
- 032: doctor-to-feedback prefill / handoff draft

These capabilities are valuable, but currently risk remaining too distributed across separate commands and outputs.

`review-night` is already the most natural place to consolidate them, because async-dev is intended to support a day-sized execution cycle followed by a focused human nightly review.

Feature 033 should pull those signals back into the main review flow so the system feels more like a cohesive async development OS rather than a collection of adjacent operator tools.

## Core Principle
`review-night` should become a stronger decision artifact, not a heavier control plane.

This feature should:
- consolidate existing operator signals
- preserve explicit user control
- remain artifact-first
- avoid introducing heavy UI or automation creep

## Scope
Implement an enriched nightly operator pack for `review-night` in `amazing-async-dev`.

This feature should:
1. Extend review-night output with selected signals from Features 028–032
2. Present those signals in an operator-friendly nightly summary
3. Keep the enriched pack concise and decision-oriented
4. Preserve the current review-night role as a nightly review artifact
5. Avoid duplicating logic by reusing existing snapshot/doctor/recovery/handoff outputs where possible

## Non-Goals
Do not:
- redesign the core day loop
- replace `doctor` as a standalone command
- replace `status` / snapshot views
- add a heavy dashboard or GUI layer
- automatically run recovery, verification, or feedback capture
- automatically escalate issues or create feedback records
- require advisor or starter-pack mode

## Main User Experience
After a day run, the operator should be able to use `review-night` and get a single enriched nightly artifact that answers:

### 1. Workspace Position
- initialization mode: direct / starter-pack
- current product
- current feature
- current phase

### 2. Health and Risk
- doctor status
- runstate health status
- verification status
- pending blocked conditions / pending decisions

### 3. Recommended Next Move
- recommended next action
- suggested command
- whether safe continuation is likely or not

### 4. Recovery Context
Shown only when applicable:
- likely cause
- what to check
- recovery steps
- fallback next step

### 5. Feedback Opportunity
Shown only when applicable:
- feedback suggestion
- feedback reason
- feedback draft summary
- suggested feedback command

### 6. Closeout Signals
Shown when relevant:
- completed pending closeout
- archive/review/finalization reminders

## Design Rule
The enriched operator pack should be:
- concise
- layered
- readable in one sitting
- useful for making the next-day decision

It should not become a verbose dump of all possible internal state.

## Output Structure (Suggested)
The nightly operator pack should be structured into a small set of sections such as:

1. `Execution Summary`
2. `Workspace Snapshot`
3. `Doctor Assessment`
4. `Recovery Guidance` (conditional)
5. `Verification Status`
6. `Feedback Handoff` (conditional)
7. `Recommended Next Action`

Exact naming may follow existing repository conventions, but the result should remain clearly operator-facing.

## Reuse Rule
This feature should prefer reusing already-existing operator logic rather than re-implementing it.

Examples:
- reuse workspace snapshot derivation
- reuse doctor status derivation
- reuse recovery hint selection
- reuse feedback handoff logic
- reuse feedback draft summary logic

`review-night` should assemble and present these signals as a nightly artifact, not define a second competing copy of the same logic.

## Conditional Display Rules
To keep the pack focused:

### Always show
- current workspace summary
- current doctor status
- runstate health status
- recommended next action
- suggested command when available

### Show only when applicable
- recovery guidance
- verification warning/failure details
- feedback handoff suggestion
- feedback draft summary
- closeout reminders

### Keep minimal when healthy
If the workspace is healthy and no special action is needed, `review-night` should remain lean rather than verbose.

## Integration Guidance
This feature should integrate naturally into the existing `review-night` flow.

Recommended behavior:
- standard review-night output becomes enriched by default
- the enriched operator pack remains readable in text form
- any structured output already used by the repo may be extended if needed
- do not require the user to separately run `status` and `doctor` just to understand the nightly situation

## Data Model Guidance
If the repository already has a nightly review artifact model (for example `DailyReviewPack` or equivalent), extend it carefully rather than introducing a parallel nightly object.

Suggested additions may include optional fields such as:
- `workspace_snapshot`
- `doctor_status`
- `runstate_health_status`
- `verification_status`
- `recommended_next_action`
- `suggested_command`
- `recovery_summary`
- `feedback_handoff_summary`
- `feedback_draft_summary`
- `closeout_summary`

Prefer optional fields and composed summaries over large new nested structures unless existing conventions already favor them.

## Code Location Guidance
Keep review-night assembly logic near the existing review-night implementation.

Expected integration areas may include:
- nightly review pack generation
- review-night CLI output
- artifact rendering / serialization code
- reuse of helpers from snapshot/doctor logic

If the repository already has modules for:
- review pack generation
- doctor logic
- snapshot logic

then Feature 033 should wire them together rather than duplicating internal logic.

## Suggested Internal Responsibilities
A healthy internal structure for this feature may look like:

- existing snapshot logic derives workspace summary
- existing doctor logic derives diagnosis and next action
- existing recovery logic provides conditional recovery hints
- existing handoff logic provides optional feedback suggestion and draft summary
- review-night assembles these into one nightly operator artifact

The nightly pack should remain an assembly layer, not the canonical owner of all diagnostic logic.

## Documentation Requirements
Update review-night-related docs to explain:

1. `review-night` is now the primary nightly operator pack
2. it consolidates snapshot + doctor + recovery + verification + handoff signals
3. it does not replace standalone `doctor` or `status`
4. recovery and feedback sections appear only when relevant
5. the purpose is to support nightly human decision-making in the async-dev loop

## Test Requirements
Add focused tests for enriched review-night behavior.

Minimum test coverage:

### Baseline tests
1. healthy workspace -> concise enriched pack with snapshot + doctor + next action
2. starter-pack initialization mode -> pack includes initialization context
3. direct mode -> pack includes initialization context correctly

### Doctor integration tests
4. attention-needed state -> pack includes doctor status and recommended next action
5. blocked state -> pack includes blocked signal and suggested command
6. completed-pending-closeout -> pack includes closeout reminder

### Recovery tests
7. problematic scenario -> recovery guidance appears
8. healthy scenario -> recovery guidance omitted

### Verification tests
9. failed verification -> verification section appears with clear signal
10. no verification issue -> verification section remains minimal

### Feedback tests
11. handoff suggested -> feedback section appears
12. no handoff suggested -> feedback section omitted
13. feedback draft summary appears only when available

### Output quality tests
14. enriched pack remains readable and non-duplicative
15. enriched pack does not require standalone doctor output to understand next action

## Acceptance Criteria

### AC1
`review-night` produces an enriched operator-facing nightly artifact.

### AC2
The nightly artifact includes snapshot, doctor status, and recommended next action by default.

### AC3
Recovery guidance appears only for relevant problematic scenarios.

### AC4
Feedback handoff and feedback draft summary appear only when applicable.

### AC5
Verification and closeout signals are surfaced clearly when relevant.

### AC6
The implementation reuses existing snapshot/doctor/recovery/handoff logic rather than duplicating it.

### AC7
Docs clearly position `review-night` as the primary nightly decision artifact.

### AC8
Tests cover healthy, blocked, verification-failed, closeout, and handoff scenarios.

## Definition of Done
This feature is done when:
- nightly review becomes a stronger operator entry point
- 028–032 signals are meaningfully consolidated into review-night
- the nightly pack helps a human quickly decide what to do next
- the pack remains concise and artifact-first
- no heavy UI or automation creep is introduced
- docs and tests are updated accordingly

## Implementation Guidance
Keep this feature disciplined.

This is not a dashboard project.

It is a consolidation feature that strengthens the main async-dev operating loop by making nightly human review more useful and less fragmented.

Prefer:
- reuse over duplication
- concise summaries over exhaustive dumps
- conditional sections over always-on verbosity
- operator readability over clever internal abstraction
