# 034-resume-next-day-decision-pack-alignment

## Title
Resume-Next-Day Decision Pack Alignment

## Summary
Align `resume-next-day` with the enriched nightly operator pack introduced in Feature 033, so the system can carry forward the previous night's human-readable decision context into the next day's recovery and continuation flow.

This feature strengthens the core async-dev loop by making the transition from:

- `review-night`
to
- `resume-next-day`

more direct, less interpretive, and less repetitive for a solo operator.

## Relationship to Earlier Features

### 026 — Optional Advisor Integration Positioning
Feature 026 clarified that advisor is an optional ecosystem component and that async-dev must remain independently usable.

Relevance to 034:
- `resume-next-day` must work cleanly for both direct mode and starter-pack mode
- decision-pack alignment must not assume advisor is present
- initialization context may be surfaced, but must remain optional and non-blocking

### 027 — Optional Initialization Verification
Feature 027 established the verification entry and smoke validation path.

Relevance to 034:
- `resume-next-day` should be able to surface whether verification is still relevant to the next step
- if review-night already captured verification concerns, resume should reuse that signal instead of forcing the operator to rediscover it

### 028 — Repo-linked Workspace Snapshot
Feature 028 introduced a unified workspace snapshot / operator status view.

Relevance to 034:
- the nightly decision pack already depends on a readable workspace summary
- `resume-next-day` should reuse this workspace state awareness rather than rebuild a disconnected view

### 029 — Workspace Doctor / Recommended Next Action
Feature 029 introduced doctor status, operator-facing interpretation, and recommended next action.

Relevance to 034:
- `resume-next-day` should recognize and reuse the prior doctor conclusion when it is still valid
- the next-day entry point should not feel detached from last night's doctor guidance

### 030 — Doctor Fix Hints / Recovery Playbooks
Feature 030 introduced recovery guidance for problematic scenarios.

Relevance to 034:
- when recovery guidance was relevant the night before, resume-next-day should surface the relevant portion so the operator can continue without re-deriving the same recovery path

### 031 — Doctor-to-Feedback Handoff
Feature 031 added explicit, optional handoff suggestions from doctor to feedback.

Relevance to 034:
- next-day resume may need to preserve awareness that a workflow friction issue was identified
- but it must not auto-capture feedback or escalate anything

### 032 — Doctor-to-Feedback Prefill / Handoff Draft
Feature 032 added lightweight handoff draft / prefill behavior.

Relevance to 034:
- if a handoff draft was already prepared, resume-next-day may remind the operator that it exists
- but it must remain optional and user-invoked

### 033 — Review-Night Enriched Operator Pack
Feature 033 made `review-night` the primary nightly operator artifact, consolidating:
- workspace snapshot
- doctor status
- recommended next action
- recovery guidance
- verification signals
- optional feedback handoff context
- closeout reminders

Relevance to 034:
- Feature 034 exists specifically to connect this enriched nightly artifact to the next morning's resume flow
- without 034, the nightly pack is useful but not fully integrated into the next-day continuation path

## Why Feature 034 Matters
Async-dev's main value is not just artifact generation. Its value comes from supporting a practical solo async development loop:

- plan the day
- run the day
- review at night
- resume the next day from real state, not reconstructed memory

Feature 033 strengthened the nightly review side of that loop.

Feature 034 should strengthen the next-morning continuation side, so the enriched nightly decision artifact is not just informative, but operationally useful.

This reduces:
- repeated interpretation
- duplicated diagnosis
- re-reading multiple artifacts to figure out where to continue
- friction between nightly judgment and next-day action

## Goal
Make `resume-next-day` aware of the enriched nightly operator pack so it can:

1. detect and reuse the most relevant prior-night decision context
2. present a concise continuation-oriented summary
3. guide the operator into the next safe action
4. preserve explicit human control
5. avoid duplicating doctor/recovery/review logic

## Core Principle
`review-night` is where the system helps the operator decide.

`resume-next-day` is where the system helps the operator continue from that decision.

Feature 034 should connect those two responsibilities without:
- creating a second diagnostic system
- re-running full nightly analysis by default
- turning resume into a heavy orchestration layer

## Scope
Implement decision-pack-aware resume behavior in `amazing-async-dev`.

This feature should:
1. detect the latest usable nightly decision pack
2. extract the most relevant continuation signals from it
3. present a concise next-day resume summary
4. align resume behavior with the prior recommended next action when appropriate
5. preserve fallback behavior when no nightly decision pack is available

## Non-Goals
Do not:
- redesign the entire resume-next-day command family
- replace `review-night` as the source of nightly judgment
- duplicate doctor derivation logic inside resume
- automatically run verify, recovery, feedback capture, or closeout commands
- require advisor or starter-pack mode
- add a heavy UI/dashboard layer
- introduce new long-term memory/history tracking systems

## Main User Experience
When the operator starts the next day, `resume-next-day` should help answer:

- what did last night's review conclude?
- is the workspace healthy, blocked, or attention-needed?
- what was the recommended next action?
- are there recovery steps I still need?
- is verification still relevant?
- is there a closeout task I should finish first?
- was there a feedback handoff suggestion I may still want to act on?

The operator should not need to manually open several artifacts just to regain context.

## Decision Pack Consumption Rules

### Rule 1: Prefer the latest valid nightly decision pack
If a recent enriched review-night artifact exists and is structurally usable, `resume-next-day` should consume it.

### Rule 2: Use decision-pack context as a guide, not a hard lock
The prior nightly decision pack should inform resume behavior, but must not rigidly constrain the operator if workspace state has changed.

### Rule 3: Prioritize concise continuation context
Resume output should focus on:
- previous conclusion
- current continuation relevance
- next action

It should not dump the full nightly pack again.

### Rule 4: Fall back gracefully
If no usable nightly decision pack exists, resume-next-day should continue to work with existing state-based fallback behavior.

## Suggested Resume Summary Content
The next-day resume summary should include a concise subset of the nightly pack such as:

- prior review timestamp
- initialization mode (direct / starter-pack) when relevant
- current feature / current phase
- prior doctor status
- prior recommended next action
- suggested command
- recovery summary (only if still relevant)
- verification concern (only if still relevant)
- feedback handoff reminder (only if still relevant)
- closeout reminder (only if still relevant)

## Relevance Rules
To keep the resume experience useful and compact:

### Always show
- prior review reference or timestamp when available
- current feature and/or current phase when available
- prior recommended next action when available

### Show conditionally
- doctor status if non-trivial or decision-shaping
- recovery summary if the prior pack indicated a problematic scenario
- verification reminder only if verification concern remains relevant
- feedback handoff reminder only if a handoff suggestion existed
- closeout reminder only if closeout is still pending

### Omit by default
- long explanatory sections from the prior nightly pack
- full recovery playbooks
- full feedback draft fields
- duplicate raw snapshot detail already visible elsewhere

## Freshness / Staleness Guidance
Resume-next-day should not blindly trust stale nightly data.

Suggested behavior:
- if the nightly decision pack is recent and workspace state appears compatible, use it normally
- if the nightly decision pack appears stale relative to changed workspace state, surface that it may be outdated
- if state has materially changed, prefer current workspace reality while still optionally referencing the prior pack

This should remain lightweight and heuristic-based, not a heavy consistency engine.

## Integration Approach
This feature should integrate into the existing `resume-next-day` flow rather than creating a separate resume mode.

Recommended direction:
- extend the current resume entry point
- detect the latest nightly decision pack if available
- synthesize a continuation-oriented summary from the pack + current state
- keep one canonical resume path

## Reuse Rule
Prefer reuse over duplication.

Feature 034 should reuse:
- the enriched nightly artifact from Feature 033
- existing workspace state awareness
- existing doctor/recovery/handoff summaries where already computed

`resume-next-day` should consume those outputs, not re-own the full logic.

## Data Model Guidance
If resume already has a structured output or summary model, extend it carefully with optional continuation fields rather than inventing a new parallel resume object.

Possible optional fields:
- `prior_review_timestamp`
- `prior_doctor_status`
- `prior_recommended_next_action`
- `prior_suggested_command`
- `resume_recovery_summary`
- `resume_verification_summary`
- `resume_feedback_handoff_summary`
- `resume_closeout_summary`
- `decision_pack_status` (e.g. found / missing / stale)

Prefer concise summaries and optional fields over deeply nested new structures.

## Code Location Guidance
Integrate near the existing `resume-next-day` implementation.

Likely integration points may include:
- resume CLI command handling
- resume state loading
- nightly artifact loading helper(s)
- small decision-pack selection helper(s)
- resume summary rendering / serialization

Keep the decision-pack consumption logic close to resume flow rather than creating a separate subsystem.

## Suggested Internal Responsibilities
A reasonable internal structure may look like:

- existing resume flow loads current state
- helper locates latest usable nightly review artifact
- helper extracts continuation-relevant fields
- resume command assembles a concise resume summary
- operator receives a clear next step without re-reading the entire nightly pack

## Documentation Requirements
Update resume / loop-related docs to explain:

1. `review-night` now creates the nightly decision artifact
2. `resume-next-day` can consume that artifact when available
3. this reduces repeated interpretation between days
4. resume still works without a nightly decision pack
5. the system remains explicit and operator-controlled

## Test Requirements
Add focused tests for decision-pack-aware resume behavior.

Minimum test coverage:

### Positive alignment tests
1. latest enriched nightly pack exists -> resume uses it
2. healthy nightly pack -> resume shows concise prior recommendation
3. attention-needed nightly pack -> resume includes relevant guidance
4. blocked nightly pack -> resume includes blocked context and suggested command
5. completed-pending-closeout nightly pack -> resume includes closeout reminder

### Conditional section tests
6. recovery summary included only when prior pack had relevant recovery context
7. feedback handoff reminder included only when prior pack had handoff context
8. verification reminder included only when still relevant

### Fallback tests
9. no nightly pack -> resume falls back gracefully
10. unreadable nightly pack -> resume falls back gracefully
11. stale or mismatched pack -> resume warns or degrades safely without breaking

### Output quality tests
12. resume summary is concise and not a full duplicate of review-night output
13. resume summary includes prior next action when available
14. resume does not auto-run commands

## Acceptance Criteria

### AC1
`resume-next-day` can detect and use the latest enriched nightly decision pack when available.

### AC2
Resume output includes a concise prior-night continuation summary rather than requiring the operator to manually reopen the full nightly pack.

### AC3
Recovery, verification, feedback handoff, and closeout reminders are shown only when relevant.

### AC4
Resume continues to work gracefully when no usable nightly decision pack exists.

### AC5
The implementation reuses existing nightly artifact data rather than duplicating full doctor/review logic.

### AC6
Docs clearly explain how review-night and resume-next-day now align.

### AC7
Tests cover aligned, fallback, and stale-pack scenarios.

## Definition of Done
This feature is done when:
- the enriched nightly decision artifact from Feature 033 meaningfully improves next-day resume
- resume-next-day becomes a better continuation entry point
- the operator no longer has to reconstruct last night's conclusions manually
- fallback behavior remains intact
- no automation creep or duplicated diagnostic system is introduced
- docs and tests are updated accordingly

## Implementation Guidance
Keep this feature practical and loop-centered.

This is not a new planning engine.

It is the missing alignment step between:
- a stronger nightly review artifact
and
- a smoother next-day continuation path

Prefer:
- concise continuation summaries
- reuse of existing enriched signals
- graceful fallbacks
- lightweight freshness checks
- explicit operator control
