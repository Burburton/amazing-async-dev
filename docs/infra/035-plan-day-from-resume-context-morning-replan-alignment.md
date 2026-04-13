# 035-plan-day-from-resume-context-morning-replan-alignment

## Title
Plan-Day from Resume Context / Morning Replan Alignment

## Summary
Align `plan-day` with the continuation context surfaced by Features 033 and 034, so the next day's bounded execution plan can be informed by:

- the prior night's enriched operator pack
- the next-morning resume summary
- the current workspace state

This feature should strengthen the main async-dev operating loop by reducing the amount of manual interpretation required between:

- `review-night`
- `resume-next-day`
- `plan-day`

## Relationship to Earlier Features

### 026 — Optional Advisor Integration Positioning
Feature 026 clarified that advisor is optional and that async-dev must remain independently usable.

Relevance to 035:
- plan-day alignment must work for both direct mode and starter-pack mode
- any initialization-mode context should remain optional
- no dependence on advisor should be introduced

### 027 — Optional Initialization Verification
Feature 027 established verification as an explicit initialization validation path.

Relevance to 035:
- if verification concerns remain relevant at morning planning time, plan-day should be able to surface or carry that concern into the next bounded plan
- plan-day should not force the operator to rediscover unresolved verification signals manually

### 028 — Repo-linked Workspace Snapshot
Feature 028 added a unified workspace snapshot / operator status view.

Relevance to 035:
- morning planning should reuse the workspace state picture rather than re-derive a disconnected planning context
- snapshot context helps determine whether the new daily plan should continue, recover, close out, or verify

### 029 — Workspace Doctor / Recommended Next Action
Feature 029 added doctor status and recommended next action.

Relevance to 035:
- morning planning should consider the latest meaningful doctor conclusion when it still applies
- plan-day should not ignore operator-facing guidance already derived by the system

### 030 — Doctor Fix Hints / Recovery Playbooks
Feature 030 added recovery guidance for problematic scenarios.

Relevance to 035:
- if the workspace still requires recovery, plan-day should reflect that rather than planning a normal forward-progress task
- recovery-relevant mornings may require a bounded "repair/recovery day" plan rather than a normal implementation plan

### 031 — Doctor-to-Feedback Handoff
Feature 031 added explicit, optional handoff suggestions from doctor to feedback.

Relevance to 035:
- morning planning may preserve awareness that a recurring/systemic issue was identified
- but planning must not auto-capture feedback or escalate anything

### 032 — Doctor-to-Feedback Prefill / Handoff Draft
Feature 032 added a lightweight feedback draft / prefill layer.

Relevance to 035:
- if a feedback handoff draft exists, plan-day may optionally remind the operator about it
- but the draft remains secondary to the bounded daily execution goal

### 033 — Review-Night Enriched Operator Pack
Feature 033 made `review-night` the primary nightly decision artifact.

Relevance to 035:
- the nightly pack now contains the prior-day decision context
- plan-day should ultimately benefit from that enriched context rather than starting "cold" each morning

### 034 — Resume-Next-Day Decision Pack Alignment
Feature 034 made `resume-next-day` consume the enriched nightly operator pack and present a concise continuation-oriented summary.

Relevance to 035:
- Feature 034 produces the immediate morning continuation context
- Feature 035 should allow plan-day to consume that context and turn it into a bounded daily plan

## Why Feature 035 Matters
Async-dev's core value is a practical solo builder loop, not isolated commands.

After Feature 034, the system can:
- carry the previous night's decision context into the next morning
- show the operator what likely matters next

What remains missing is:
- converting that resumed context into today's bounded daily plan

Without Feature 035, the loop still has a manual gap:
- the operator reads nightly context
- resumes the workspace
- then mentally reconstructs how today's plan should differ

Feature 035 should reduce that gap by helping `plan-day` start from resumed context rather than from a mostly standalone planning entry point.

## Goal
Make `plan-day` aware of morning resume context so it can produce a more relevant bounded daily plan that reflects:

1. prior-night conclusions
2. next-morning continuation signals
3. current workspace reality
4. unresolved blockers/recovery/verification/closeout context
5. explicit human control over final planning decisions

## Core Principle
`review-night` helps decide.

`resume-next-day` helps continue.

`plan-day` should help translate that continuation context into today's bounded execution unit.

This feature should improve planning alignment without:
- turning plan-day into a heavy autonomous replanner
- replacing human judgment
- duplicating doctor/recovery/review logic

## Scope
Implement resume-context-aware day planning in `amazing-async-dev`.

This feature should:
1. detect and consume relevant morning resume context when available
2. use that context to shape plan-day recommendations or candidate plans
3. keep planning bounded and day-sized
4. preserve explicit operator approval/control
5. fall back gracefully when no resume context is available

## Non-Goals
Do not:
- redesign the full planning system
- replace review-night or resume-next-day
- build a general autonomous replanning engine
- auto-run execution commands
- auto-resolve blockers, verification, recovery, or feedback tasks
- require advisor or starter-pack mode
- introduce a heavy UI or orchestration layer
- create a second competing planning artifact system

## Main User Experience
In the morning, the operator should be able to run `plan-day` and get a plan that feels informed by current reality.

The operator should be able to answer:

- what did last night's review and this morning's resume imply?
- should today be a continuation day, recovery day, verification day, or closeout day?
- what is the bounded execution target for today?
- is there a blocker or attention-needed issue that should reshape the plan?
- should today's plan prioritize progress, recovery, verification, or closure?

The operator should not have to manually merge:
- nightly pack output
- resume summary
- current state
- doctor/recovery conclusions

before getting a useful plan proposal.

## Planning Alignment Rules

### Rule 1: Prefer current reality over stale context
Resume context should inform plan-day, but must not override current workspace reality if the state has materially changed.

### Rule 2: Use context to shape plan intent, not to hard-lock content
Morning context should influence the direction of the plan, such as:
- continue implementation
- unblock / recover
- rerun verification
- complete closeout

But the system should not rigidly force one path.

### Rule 3: Keep the plan day-sized and bounded
Even when context is rich, the resulting daily plan should remain narrow and executable within the intended daily loop.

### Rule 4: Graceful fallback remains required
If no usable resume context exists, plan-day should continue to work using current behavior.

## Suggested Planning Modes
The initial implementation may infer a small set of planning modes from morning context, for example:

- `continue_work`
- `recover_and_continue`
- `verification_first`
- `closeout_first`
- `blocked_waiting_for_decision`

These do not need to become a large formal subsystem in this feature, but they may help shape the resulting plan recommendation.

## Suggested Inputs to Plan-Day Alignment
Feature 035 may use available signals such as:

- prior recommended next action
- prior suggested command
- prior doctor status
- current phase
- resume recovery summary
- resume verification summary
- resume closeout summary
- resume feedback handoff reminder
- decision pack status (found / missing / stale)

Use only what is already available through 033/034 and current state.

Do not introduce heavy new state tracking.

## Output Expectations
Plan-Day should produce output that is still clearly a day plan, but more context-aware.

Expected qualities:
- bounded
- action-oriented
- aligned with current resume context
- explicit about why the plan shape was chosen
- concise enough for a solo operator to review quickly

The output may include:
- planning mode or intent
- short rationale
- proposed bounded target for today
- warnings when blockers/recovery/verification/closeout shape the plan
- suggested first command or first step

## Conditional Planning Guidance
To keep output useful:

### Always show
- proposed bounded daily plan
- short rationale
- suggested first next step when available

### Show conditionally
- recovery-oriented plan framing if recovery is still relevant
- verification-first framing if verification concern is still relevant
- closeout-first framing if closeout is pending
- blocked/decision-wait framing if safe continuation is not possible

### Keep minimal when healthy
If the workspace is healthy and continuation is straightforward, plan-day should not become verbose just because prior context exists.

## Integration Approach
This feature should extend the existing `plan-day` path rather than creating a new alternate planning command.

Recommended direction:
- extend current plan-day flow
- load usable resume context if available
- shape the day plan recommendation from resume context + current state
- preserve one canonical planning entry point

## Reuse Rule
Prefer reuse over duplication.

Feature 035 should reuse:
- the enriched nightly operator pack signals from 033
- the resume summary / decision-pack alignment from 034
- existing workspace state awareness
- existing doctor/recovery/verification/closeout summaries when already available

`plan-day` should consume these signals, not re-own the full logic.

## Data Model Guidance
If the repository already has a structured planning artifact or day-plan representation, extend it carefully with optional context-aware fields rather than inventing a new planning object hierarchy.

Possible optional fields:
- `planning_mode`
- `planning_rationale`
- `resume_context_status`
- `prior_doctor_status`
- `prior_recommended_next_action`
- `plan_recovery_flag`
- `plan_verification_flag`
- `plan_closeout_flag`
- `suggested_first_step`

Prefer incremental extensions and concise fields over a large new planning schema.

## Code Location Guidance
Integrate near the existing `plan-day` implementation.

Likely integration points may include:
- plan-day CLI command handling
- planning artifact generation
- loading or reading resume context from 034
- small helpers for plan shaping
- output rendering / serialization

Keep morning-context consumption logic close to plan-day rather than creating a large new planning subsystem.

## Suggested Internal Responsibilities
A reasonable internal structure may look like:

- existing plan-day flow loads current state
- helper reads the latest usable resume context if available
- helper determines the likely planning mode / plan intent
- plan-day assembles a bounded plan recommendation
- operator reviews and proceeds with explicit control

The planning layer should remain an assembly / shaping layer, not a replacement for the underlying state and diagnostic logic.

## Documentation Requirements
Update planning / loop-related docs to explain:

1. `review-night` creates the enriched nightly decision artifact
2. `resume-next-day` carries forward continuation context
3. `plan-day` can now shape today's bounded plan from that context
4. this reduces repeated interpretation between days
5. plan-day still works without resume context
6. final planning remains explicitly operator-controlled

## Test Requirements
Add focused tests for resume-context-aware planning behavior.

Minimum test coverage:

### Positive alignment tests
1. healthy resume context -> plan-day proposes straightforward continuation plan
2. recovery-relevant resume context -> plan-day proposes recovery-oriented bounded plan
3. verification-relevant resume context -> plan-day proposes verification-first plan
4. closeout-relevant resume context -> plan-day proposes closeout-first plan
5. blocked / decision-wait context -> plan-day reflects bounded blocked/waiting posture

### Conditional guidance tests
6. healthy case stays concise
7. recovery rationale appears only when relevant
8. verification framing appears only when relevant
9. closeout reminder appears only when relevant

### Fallback tests
10. no resume context -> plan-day falls back gracefully
11. unreadable resume context -> plan-day falls back gracefully
12. stale context -> plan-day degrades safely and prefers current state

### Output quality tests
13. plan-day output remains bounded and action-oriented
14. plan-day includes short rationale when context shaped the plan
15. plan-day does not auto-run execution commands

## Acceptance Criteria

### AC1
`plan-day` can use available resume context from Feature 034 when present.

### AC2
Plan-day output becomes more aligned with prior-night and morning continuation context.

### AC3
Recovery, verification, blocked, and closeout conditions can shape the bounded daily plan when relevant.

### AC4
Plan-day remains concise, day-sized, and explicitly operator-controlled.

### AC5
Plan-day continues to work gracefully when no usable resume context exists.

### AC6
The implementation reuses existing resume/review/doctor signals rather than duplicating them.

### AC7
Docs clearly explain the new alignment between review-night, resume-next-day, and plan-day.

### AC8
Tests cover healthy, recovery, verification, closeout, blocked, and fallback scenarios.

## Definition of Done
This feature is done when:
- morning resume context meaningfully improves daily planning
- the operator no longer has to reconstruct day-plan intent manually from prior-night artifacts
- plan-day remains bounded and practical
- fallback behavior remains intact
- no heavy replanning engine is introduced
- docs and tests are updated accordingly

## Implementation Guidance
Keep this feature practical and loop-centered.

This is not a new autonomous planner.

It is the next alignment step in the async-dev operating loop:

- nightly review produces better decision context
- morning resume carries that context forward
- day planning turns that context into a bounded plan

Prefer:
- bounded plans
- short rationale
- reuse of existing signals
- graceful fallbacks
- light contextual shaping instead of heavy planning abstraction
- explicit operator control
