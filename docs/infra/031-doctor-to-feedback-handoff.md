# 031-doctor-to-feedback-handoff

## Title
Doctor-to-Feedback Handoff (Explicit, Optional)

## Summary
Establish a lightweight, explicit bridge from `doctor` output to the existing workflow feedback mechanism, so operator-facing diagnosis can suggest when a problem may be worth capturing as feedback, without duplicating feedback capture, triage, or escalation logic.

## Goal
Help users distinguish between:
- issues that only need local recovery right now
- issues that may indicate recurring friction or a systemic workflow problem worth capturing into the existing feedback pipeline

This feature should allow `doctor` to recommend a feedback handoff in appropriate scenarios, while preserving a strict separation of responsibilities.

## Why
Features 028–030 have strengthened operator usability:

- 028: workspace snapshot
- 029: doctor status + recommended next action
- 030: recovery playbooks

At this point, the operator can see:
- where they are
- what to do next
- how to recover

What is still missing is a disciplined way to answer:
- should this issue just be resolved locally?
- or is it likely recurring/systemic enough to be captured as workflow feedback?

The existing 019-series feedback mechanisms already handle:
- capture
- triage
- promotion / escalation

Feature 031 should not recreate those systems. It should only provide a small, explicit handoff from doctor to feedback when warranted.

## Core Principle
`doctor` is for diagnosis and recovery.

The feedback mechanism is for persistent learning and system improvement.

Feature 031 creates a bridge between them, but does not merge them.

## Scope
Implement a lightweight doctor-to-feedback handoff layer in `amazing-async-dev`.

This feature should:
1. Define when doctor should suggest feedback handoff
2. Surface an optional feedback suggestion in doctor output
3. Provide a recommended feedback capture command when appropriate
4. Document the boundary between diagnosis/recovery and feedback systems
5. Keep all handoff behavior explicit and user-invoked

## Non-Goals
Do not:
- automatically create feedback records
- automatically run triage
- automatically promote or escalate issues
- duplicate the 019-series workflow feedback logic
- turn doctor into a long-term issue tracking or problem management system
- require advisor or starter-pack mode

## Required Design Rule
Feature 031 must preserve the following separation:

- `doctor` answers: what is happening now, what should I do next, and how do I recover?
- `feedback` answers: what should be recorded for future improvement and how should it be triaged/escalated?

The handoff must remain:
- explicit
- optional
- operator-controlled

## User Experience
Doctor output may include a feedback suggestion section only when the current situation appears likely to be recurring friction or a systemic problem.

Example:

- Doctor Status: `ATTENTION_NEEDED`
- Why: initialization verification failed again for the same contract mismatch
- Next Action: inspect compatibility fields and rerun verification
- Suggested Command: `asyncdev verify`
- Feedback Suggestion: this may be worth capturing as workflow feedback
- Suggested Feedback Command: `asyncdev feedback capture ...`

If the situation does not meet handoff criteria, no feedback suggestion should be shown.

## Handoff Criteria (Initial Version)
Implement a conservative first-pass set of conditions.

Doctor may suggest feedback handoff when one or more of the following are true:

### 1. Repeated verification failure
- verification failed more than once
- or the same verification issue appears to recur
- especially if recovery guidance exists but the issue persists

### 2. Repeated blocked state
- the workspace repeatedly enters `BLOCKED`
- or a pending-decision / blocked pattern appears more than once for the same workflow area

### 3. Repeated unknown or incomplete state
- `UNKNOWN` status recurs
- or required state/artifacts are repeatedly missing/unreadable

### 4. Recovery playbook indicates likely systemic friction
- the selected recovery scenario is known to often represent tooling/process/documentation friction rather than a one-off user error

### 5. Explicit future-improvement signal
- doctor can identify that the current issue appears resolvable now, but likely represents a repeatable pain point worth improving later

## Conservative Default
Do not suggest feedback for every warning or blocked condition.

The initial implementation should bias toward under-suggesting rather than over-suggesting.

A good first version is one that only suggests feedback for clearly recurring or clearly systemic situations.

## Output Requirements
When handoff is triggered, doctor output should include:

- a short `feedback_suggestion` message
- a brief reason
- a recommended feedback capture command, when possible

Example fields:
- `feedback_suggestion`
- `feedback_reason`
- `suggested_feedback_command`

These fields should be omitted when no handoff is recommended.

## CLI Behavior
This feature should integrate into the existing `asyncdev doctor` command.

Recommended behavior:
- default doctor output may include feedback suggestion fields only when relevant
- no feedback action is executed automatically
- doctor remains a diagnosis/recovery command, not an execution wrapper for feedback flows

Optional future enhancement:
- an explicit flag such as `--suggest-feedback`
But this is not required for the initial implementation if the default output is already selective and minimal.

## Data Model Guidance
Extend the existing doctor diagnosis/output model with optional handoff fields rather than creating a separate problem-management subsystem.

Suggested optional fields:
- `feedback_suggestion: Optional[str]`
- `feedback_reason: Optional[str]`
- `suggested_feedback_command: Optional[str]`

These fields should be populated only when handoff criteria are met.

## Code Location Guidance
Keep the handoff selection logic close to doctor logic for now.

Recommended location:
- extend `runtime/workspace_doctor.py`

This keeps:
- doctor status
- diagnosis assembly
- recovery playbook selection
- feedback handoff suggestion

within the same operator-facing pipeline.

Only extract later if complexity materially grows.

## Suggested Internal Structure
Within `workspace_doctor.py`, keep logic lightly separated, for example:

- `derive_doctor_status(...)`
- `build_doctor_diagnosis(...)`
- `select_recovery_hints(...)`
- `select_feedback_handoff(...)`

This preserves cohesion without premature modularization.

## Documentation Requirements
Update doctor-related docs to state clearly:

1. doctor does not replace feedback capture
2. doctor may recommend a feedback handoff in selected cases
3. feedback capture remains explicit and user-invoked
4. this feature supports system improvement without coupling diagnosis to automatic escalation

## Test Requirements
Add focused tests for handoff behavior.

Minimum test coverage:

### Positive handoff tests
1. repeated verification failure -> feedback suggestion appears
2. repeated blocked condition -> feedback suggestion appears
3. recurring unknown/incomplete state -> feedback suggestion appears
4. recovery scenario marked as likely systemic friction -> feedback suggestion appears

### Negative handoff tests
5. one-off warning -> no feedback suggestion
6. one-off blocked condition with clear local recovery -> no feedback suggestion
7. healthy state -> no feedback suggestion
8. completed pending closeout -> no feedback suggestion unless there is separate recurring friction evidence

### Output tests
9. doctor text output includes feedback suggestion only when criteria are met
10. doctor YAML output includes feedback fields only when criteria are met
11. feedback fields are omitted or empty when not applicable

## Acceptance Criteria

### AC1
Doctor can recommend feedback handoff in selected recurring/systemic scenarios.

### AC2
No feedback record is created automatically.

### AC3
No triage or promotion/escalation is triggered automatically.

### AC4
Doctor output includes optional feedback handoff fields only when criteria are met.

### AC5
The separation between doctor diagnosis/recovery and the existing feedback mechanism is explicitly documented.

### AC6
Tests cover both positive and negative handoff scenarios.

## Definition of Done
This feature is done when:
- doctor can identify a small set of recurring/systemic situations worth surfacing as feedback candidates
- handoff remains explicit and optional
- no duplication of the 019-series feedback pipeline is introduced
- operator output becomes more useful for deciding whether to improve the system, not just recover locally
- docs and tests are updated accordingly

## Implementation Guidance
Keep this feature disciplined.

This is not a new problem-management subsystem.

It is a small bridge:
- from current diagnosis
- to optional future-improvement capture

Prefer:
- conservative criteria
- explicit output
- minimal automation
- clear separation of responsibility
- easy-to-test decision logic
