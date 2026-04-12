# 030 — Doctor Fix Hints / Recovery Playbooks

## Title
Doctor Fix Hints / Recovery Playbooks

## Status
Proposed

## Owner Repo
Primary: `amazing-async-dev`

## Related Features
- 019a Workflow Feedback Capture
- 019b Workflow Feedback Triage
- 019c Feedback Promotion / Issue Escalation
- 027 Optional Initialization Verification
- 028 Repo-linked Workspace Snapshot
- 029 Workspace Doctor / Recommended Next Action

## Background
`amazing-async-dev` is positioned as a narrow async development OS for solo builders, not a heavy orchestration platform or UI-first system. Its core workflow remains artifact-first, day-sized, and state-driven, with human review concentrated at night. The current repo state and README still frame the product around a practical single-builder async development loop. citeturn0view0

By 029, the system can already:
- show workspace state
- derive an operator-facing `doctor_status`
- explain the current situation
- recommend a next action

What is still missing is a short, structured recovery layer for common unhealthy or ambiguous situations. Today, a user may know the next command, but still not know:
- why this state happened
- what to inspect first
- which artifact or file is most relevant
- what to do if the recommended command does not resolve the issue

## Problem
`doctor` can tell the user **what** to do next, but not yet **how to recover** when the situation is non-trivial.

That creates three usability gaps:
1. recommended commands may be too thin for real recovery
2. repeated friction still requires manual interpretation
3. common failure patterns are not yet turned into reusable operator guidance

## Goal
Add a lightweight recovery guidance layer on top of `doctor` so that common `doctor_status` scenarios provide:
- likely cause
- what to check first
- short recovery steps
- fallback next step if the first recommendation fails

This must remain a **guidance feature**, not an automation or issue-management feature.

## Non-Goals
This feature must **not**:
- auto-run `verify`
- auto-fix workspace state
- auto-create feedback records
- auto-triage incidents into feedback categories
- auto-promote problems into GitHub issues
- replace 019-series feedback mechanisms
- introduce a heavy UI/dashboard
- turn `doctor` into a generic orchestration engine

## Core Boundary
This feature is intentionally separate from the existing feedback mechanism:

- **019-series** handles capture, triage, and escalation of recurring or important workflow problems
- **030** handles immediate operator-facing recovery guidance for the current workspace state

One is for **system improvement**.
The other is for **current recovery**.

## Target User Experience
A user runs:

```bash
asyncdev doctor
```

And sees not only:
- `doctor_status`
- explanation
- recommended next action
- suggested command

But also, when relevant:
- likely cause
- what to check
- recovery steps
- if this fails, try next

For machine-readable use, structured output should continue to work through:

```bash
asyncdev doctor --format yaml
```

## Feature Scope
Implement a first version of recovery playbooks for the most common operator-facing situations.

### In Scope
1. Recovery hints integrated into `asyncdev doctor`
2. A small playbook model or rule layer
3. YAML output support for recovery fields
4. Documentation for supported playbooks
5. Tests for recovery hint selection and output

### Out of Scope
1. Full remediation workflows
2. Automatic repair actions
3. Learning-based diagnosis
4. New feedback capture or issue escalation flows
5. Cross-repo automation into advisor

## Recommended CLI Behavior
### Primary command
```bash
asyncdev doctor
```

### Structured output
```bash
asyncdev doctor --format yaml
```

### Optional detail flag
A detail flag may be added if helpful, but is not required for v1:

```bash
asyncdev doctor --details
```

Default output should stay compact; recovery details should appear when they materially help the user.

## Recovery Playbook Model
Add a lightweight derived guidance structure, for example:
- `likely_cause`
- `what_to_check`
- `recovery_steps`
- `fallback_next_step`

This model should be derived from:
- `doctor_status`
- `RunState.health_status`
- verification state
- pending decision state
- closeout/archive state
- state/artifact availability

It must remain deterministic and testable.

## Required Initial Scenarios
V1 should cover these scenarios.

### 1. BLOCKED + pending async decision
#### Trigger
- `doctor_status = BLOCKED`
- pending decision exists

#### Expected hints
- likely cause: workflow cannot safely continue until human decision is resolved
- what to check: decision request, blocking phase, latest review context
- recovery steps:
  1. inspect pending decision
  2. confirm required human input
  3. resolve or resume with explicit command
- fallback next step: review latest nightly pack or unblock instructions

### 2. ATTENTION_NEEDED + verification not run
#### Trigger
- `doctor_status = ATTENTION_NEEDED`
- verification status = not run

#### Expected hints
- likely cause: initialization or integration state has not been validated
- what to check: verification docs, starter-pack/direct initialization mode
- recovery steps:
  1. run verification
  2. inspect result summary
  3. continue only if verification is acceptable
- fallback next step: inspect workspace snapshot and initialization inputs

### 3. ATTENTION_NEEDED + verification failed
#### Trigger
- `doctor_status = ATTENTION_NEEDED`
- verification status = failed

#### Expected hints
- likely cause: contract mismatch, missing artifact, invalid initialization, or configuration drift
- what to check: latest verification output, starter-pack compatibility, required files
- recovery steps:
  1. inspect verification failure details
  2. correct mismatch or missing inputs
  3. rerun verification
- fallback next step: compare current workspace state with expected example or docs

### 4. COMPLETED_PENDING_CLOSEOUT + archive missing
#### Trigger
- `doctor_status = COMPLETED_PENDING_CLOSEOUT`
- feature complete but archive/closeout missing

#### Expected hints
- likely cause: execution is done but closure artifacts are incomplete
- what to check: completion marker, archive existence, final review artifacts
- recovery steps:
  1. confirm feature is actually complete
  2. create archive / closeout artifact
  3. verify workspace returns to healthy or idle state
- fallback next step: inspect review and completion commands

### 5. UNKNOWN + incomplete or unreadable state
#### Trigger
- `doctor_status = UNKNOWN`
- state is missing, unreadable, or inconsistent

#### Expected hints
- likely cause: required state files or runtime signals are missing or cannot be interpreted
- what to check: run state file, workspace metadata, expected artifact presence
- recovery steps:
  1. inspect missing/incomplete state
  2. restore or recreate minimum required state if possible
  3. rerun doctor and status checks
- fallback next step: use examples/docs to compare expected structure

## Output Requirements
### Human-readable output
When recovery hints are applicable, doctor output should include a compact section such as:

```text
Doctor Status: ATTENTION_NEEDED
Why: Latest verification failed, but no hard block is active.
Next Action: Fix verification mismatch and rerun verification.
Suggested Command: asyncdev verify
Likely Cause: Initialization inputs do not match expected verification assumptions.
What To Check:
- latest verification summary
- starter-pack compatibility
- required workspace artifacts
Recovery Steps:
1. Inspect verification output
2. Correct mismatch
3. Rerun verification
If This Fails, Try Next: Compare workspace state with the verification example and setup docs.
```

### YAML output
`--format yaml` should include stable keys when recovery hints are present, for example:

```yaml
doctor_status: ATTENTION_NEEDED
runstate_health_status: warning
verification_status: failed
recommended_next_action: Fix verification mismatch and rerun verification
suggested_command: asyncdev verify
likely_cause: Initialization inputs do not match expected verification assumptions
what_to_check:
  - latest verification summary
  - starter-pack compatibility
  - required workspace artifacts
recovery_steps:
  - Inspect verification output
  - Correct mismatch
  - Rerun verification
fallback_next_step: Compare workspace state with the verification example and setup docs
```

## Implementation Guidance
### Suggested components
Possible additions:
- recovery playbook selector / mapper
- recovery hint renderer for text output
- recovery hint serializer for YAML output

### Recommended design
Keep the recovery layer:
- deterministic
- rule-based
- small
- derived from existing state
- easy to test

Do not introduce a separate incident system.

## Suggested File Changes
Adjust names to match repo conventions.

Possible targets:
- `cli/doctor.py`
- `runtime/doctor_status.py`
- `runtime/recovery_playbooks.py`
- `docs/doctor.md`
- `examples/doctor-scenarios/`
- tests for doctor recovery hints

## Documentation Changes
Update doctor-related docs to clarify:
- what recovery playbooks are
- how they differ from feedback capture/triage/escalation
- what scenarios are currently supported
- that doctor remains diagnostic and recommendatory, not self-executing

## Test Requirements
Minimum test coverage should include:

### Playbook selection
1. blocked + pending decision -> blocked recovery playbook
2. attention needed + verification not run -> verification-not-run playbook
3. attention needed + verification failed -> verification-failed playbook
4. completed pending closeout + archive missing -> closeout playbook
5. unknown + incomplete state -> unknown-state playbook

### Output integration
6. human-readable doctor output includes recovery hints when applicable
7. yaml output includes `likely_cause`, `what_to_check`, `recovery_steps`, `fallback_next_step`
8. scenarios without a defined playbook still produce valid doctor output without crashing

### Boundary tests
9. doctor does not auto-run verify
10. doctor does not auto-create feedback capture records
11. doctor does not escalate directly into issue/promotion flow

## Acceptance Criteria
### AC1
`asyncdev doctor` can surface recovery hints for supported scenarios.

### AC2
Recovery hints are derived from current workspace state and doctor status, not manually injected ad hoc.

### AC3
`asyncdev doctor --format yaml` includes structured recovery fields when applicable.

### AC4
No verify execution is triggered automatically by doctor.

### AC5
No feedback capture, triage, or issue promotion is triggered automatically by doctor.

### AC6
Docs clearly distinguish immediate recovery playbooks from 019-series feedback mechanisms.

### AC7
At least the five required initial scenarios are covered by tests.

## Definition of Done
This feature is done when:
- doctor output can guide common recovery paths, not just name a next command
- recovery guidance remains lightweight and deterministic
- the feature does not duplicate feedback mechanisms
- structured and human-readable outputs both work
- tests and docs are added

## Rationale for Priority
Now that async-dev has:
- optional advisor positioning
- verification entry
- workspace snapshot
- doctor status and next-action recommendation

The next highest-leverage improvement is helping the operator recover from common blocked or degraded situations without turning the system into a heavy orchestration layer. That keeps the repo aligned with its narrow, practical single-builder async OS positioning. citeturn0view0
