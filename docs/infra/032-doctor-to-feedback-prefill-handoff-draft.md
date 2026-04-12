# 032-doctor-to-feedback-prefill-handoff-draft

## Title
Doctor-to-Feedback Prefill / Handoff Draft

## Summary
Make the explicit doctor-to-feedback handoff easier to execute by generating a lightweight prefilled feedback draft when doctor determines that the current situation may be worth capturing as workflow feedback.

This feature must reduce operator friction without changing the core boundary established in Feature 031:
- doctor may suggest feedback handoff
- feedback capture remains explicit and user-invoked
- no automatic triage, promotion, or escalation is introduced

## Goal
When `asyncdev doctor` identifies a situation that appears worth handing off to the feedback pipeline, provide a lightweight draft or prefilled payload so the operator does not need to manually restate the same context.

The goal is to improve handoff usability, not to automate the feedback system.

## Why
Feature 031 established a small, explicit bridge from doctor to the existing feedback pipeline.

That solves:
- should this issue be considered for feedback capture?

What remains awkward is:
- if the answer is yes, how do we make that handoff low-friction?

Feature 032 should address this by producing a draft that reuses already-known doctor context, such as:
- doctor status
- current phase
- likely cause
- recovery scenario
- verification state
- short operator-facing summary

This preserves the explicit handoff model while making the transition more practical.

## Core Principle
This feature improves the usability of doctor-to-feedback handoff.

It does not:
- create feedback automatically
- replace feedback capture
- replace feedback triage
- replace escalation/promotion
- turn doctor into a feedback management subsystem

## Scope
Implement a lightweight prefill/draft layer for doctor-to-feedback handoff inside `amazing-async-dev`.

This feature should:
1. Define a minimal feedback draft structure derived from doctor context
2. Generate draft content only when doctor handoff criteria are met
3. Surface the draft or a draft-backed capture suggestion in doctor output
4. Keep all feedback capture actions explicit and operator-controlled
5. Document the distinction between prefill and actual feedback capture

## Non-Goals
Do not:
- automatically create feedback records
- automatically run capture/triage/escalation
- introduce history-based recurrence tracking
- duplicate the existing feedback subsystem
- require advisor or starter-pack mode
- build a general-purpose issue drafting platform

## Relationship to Feature 031
Feature 031:
- decides whether doctor should suggest a feedback handoff

Feature 032:
- makes that suggested handoff easier by preparing reusable draft content

In short:
- 031 = should we hand off?
- 032 = if yes, how do we prefill the handoff cleanly?

## User Experience
When doctor output includes a feedback suggestion, it may also include a feedback draft summary or a prefilled capture hint.

Example:

- Doctor Status: `ATTENTION_NEEDED`
- Why: initialization verification failed
- Next Action: rerun verification after checking compatibility fields
- Suggested Command: `asyncdev verify`
- Feedback Suggestion: this may be worth capturing as workflow feedback
- Suggested Feedback Command: `asyncdev feedback capture ...`
- Feedback Draft Summary: verification failure in starter-pack initialization path with likely contract mismatch

The operator still decides whether to submit feedback.

## Initial Design Direction
Keep the first implementation conservative and simple.

The system should generate prefilled draft content only for cases where Feature 031 already recommends a feedback handoff.

Do not expand handoff criteria in this feature.

Reuse the conservative subset already established for 031:
- verification failed
- blocked phase / blocked state
- unknown or incomplete state

## Draft Content Requirements
The draft should be lightweight and practical.

Suggested draft fields:
- `source: doctor`
- `doctor_status`
- `runstate_health_status`
- `current_phase`
- `summary`
- `likely_cause`
- `recovery_scenario`
- `verification_status`
- `feedback_reason`
- `suggested_category`
- `suggested_tags`

All fields should be derived from already-available doctor/workspace context when possible.

Fields may be omitted when not available.

## Draft Quality Rule
The draft should help the operator avoid retyping context, but it should not pretend to be a final canonical feedback record.

It is acceptable for the draft to be:
- partial
- operator-editable
- best-effort
- scoped to current context

It should not attempt to infer more than the doctor pipeline can reasonably justify.

## Output Behavior
When doctor recommends feedback handoff, output should optionally include one or more of:

- short human-readable draft summary
- structured draft fields in YAML mode
- suggested feedback capture command using prefilled values where feasible

When no handoff is recommended, no feedback draft should be shown.

## CLI Behavior
This feature should integrate into the existing `asyncdev doctor` command.

Recommended behavior:
- default text output: show a concise feedback draft summary only when handoff is recommended
- `--format yaml`: include structured feedback draft fields when handoff is recommended

Optional future enhancement:
- a dedicated flag such as `--show-feedback-draft`
But this is not required for the initial implementation if default output remains concise.

## Data Model Guidance
Extend the doctor diagnosis/output model with optional draft-related fields.

Suggested optional fields:
- `feedback_draft_summary: Optional[str]`
- `feedback_draft_fields: Optional[dict]`
- `suggested_feedback_command: Optional[str]`

These fields should only be populated when Feature 031 handoff criteria are met.

## Code Location Guidance
Keep the draft generation logic close to doctor logic for now.

Recommended location:
- extend `runtime/workspace_doctor.py`

Suggested internal helpers:
- `derive_doctor_status(...)`
- `build_doctor_diagnosis(...)`
- `select_recovery_hints(...)`
- `select_feedback_handoff(...)`
- `build_feedback_draft(...)`

This keeps the doctor-facing operator pipeline cohesive without prematurely creating a larger feedback-drafting subsystem.

## Suggested Capture Integration
Do not automatically run `feedback capture`.

Instead, when feasible, generate a suggested command that reuses the draft content.

Examples:
- a capture command with a short summary prefilled
- a capture command pointing to a generated YAML draft file
- a capture command accompanied by a structured YAML block the operator can reuse

The exact mechanism should follow existing repository conventions and keep the user in control.

## Documentation Requirements
Update doctor-related docs to state clearly:

1. doctor may prepare feedback draft content when handoff is recommended
2. this draft is a convenience layer, not the feedback system itself
3. feedback capture remains explicit and user-invoked
4. prefilled draft content may be partial and operator-editable
5. no automatic triage or escalation occurs

## Test Requirements
Add focused tests for prefill behavior.

Minimum test coverage:

### Positive draft tests
1. verification failure with handoff recommendation -> draft summary appears
2. blocked state with handoff recommendation -> draft fields appear
3. unknown/incomplete state with handoff recommendation -> draft fields appear

### Negative draft tests
4. healthy state -> no feedback draft
5. attention-needed state without handoff recommendation -> no feedback draft
6. completed-pending-closeout -> no feedback draft unless handoff criteria independently apply

### Output tests
7. text output includes concise feedback draft summary only when applicable
8. YAML output includes structured feedback draft fields only when applicable
9. suggested feedback command is included only when handoff is recommended
10. omitted/unavailable fields do not break output formatting

## Acceptance Criteria

### AC1
Doctor can produce lightweight prefilled feedback draft content when handoff is recommended.

### AC2
No feedback record is created automatically.

### AC3
Feedback capture remains explicit and user-invoked.

### AC4
Draft content is surfaced only when Feature 031 handoff criteria are met.

### AC5
Text and YAML outputs both support draft/prefill behavior in a concise, operator-friendly way.

### AC6
Docs explicitly distinguish feedback draft generation from actual feedback capture.

### AC7
Tests cover positive and negative draft-generation scenarios.

## Definition of Done
This feature is done when:
- doctor can prepare a lightweight feedback draft for selected handoff scenarios
- operators can reuse existing diagnostic context instead of retyping it manually
- no existing feedback subsystem responsibilities are duplicated
- the doctor-to-feedback bridge becomes easier to use without becoming automatic
- docs and tests are updated accordingly

## Implementation Guidance
Keep this feature small and disciplined.

This is not a new feedback subsystem.

It is a usability enhancement on top of Feature 031:
- from suggestion
- to reusable draft context

Prefer:
- minimal fields
- best-effort derivation
- concise default output
- structured YAML support
- explicit operator control
- no automation creep
