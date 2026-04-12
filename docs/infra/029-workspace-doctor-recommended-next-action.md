# 029 — Workspace Doctor / Recommended Next Action

## Status
Proposed

## Type
Cross-repo usability consolidation feature (async-dev primary, advisor compatibility-aware)

## Summary
Add a lightweight operator guidance layer on top of the workspace snapshot so a user can tell not only **where the workspace is**, but also **what to do next**, **why that action is recommended**, and **when not to auto-proceed**.

This feature must remain aligned with the current ecosystem model:
- `amazing-async-dev` remains the execution OS and primary implementation surface.
- `amazing-skill-pack-advisor` remains an optional first-party ecosystem component.
- Starter-pack initialization remains supported but optional.
- Guidance must work for both **direct/manual mode** and **starter-pack mode**.

The goal is not to introduce a heavy orchestration layer or autonomous recovery engine. The goal is to reduce operator ambiguity after status becomes visible via Feature 028.

---

## Background
Recent features established the following baseline:
- Optional advisor integration positioning was clarified.
- Direct/manual initialization and starter-pack initialization are both valid first-class paths.
- A verification entry exists for confirming initialization health.
- A workspace snapshot exists to expose current operating state.

After these steps, the main remaining usability gap is interpretation:
- Users can see current status, but may still be unsure what command to run next.
- Users may not know whether the workspace is healthy, blocked, or needs attention.
- Users may not know whether an issue should be handled inside async-dev or by returning to advisor/starter-pack generation.

Feature 029 closes that gap by adding a lightweight “doctor” layer.

---

## Problem Statement
Workspace status visibility alone is not enough.

Even with a snapshot, operators still have to manually interpret:
- whether the current state is healthy,
- whether progress is blocked,
- whether verification failure is recoverable locally,
- whether an async decision is pending,
- whether the next correct action is to continue, review, archive, repair, or regenerate inputs.

This creates ongoing cognitive load and slows down routine operation.

---

## Goal
Provide a simple, explicit, operator-facing diagnosis and next-action recommendation layer for the current workspace.

The feature should answer:
1. Is the current workspace healthy?
2. Is it blocked or attention-needed?
3. What is the next recommended action?
4. What exact command should the operator run next?
5. Why is that recommendation being made?
6. When should the operator avoid auto-proceeding?

---

## Non-Goals
This feature must **not**:
- introduce a new required control plane,
- auto-execute multi-step repairs,
- create hidden orchestration across repositories,
- make advisor a required dependency,
- replace existing verification or snapshot features,
- become a full dashboard or web UI,
- silently mutate workspace state.

This is a recommendation layer, not an autonomous repair system.

---

## Product Principle
`amazing-async-dev` should help the user determine the next safe action with minimal ambiguity, while preserving explicit operator control.

---

## Scope

### In Scope
- A workspace doctor command or equivalent guidance entry in `amazing-async-dev`
- Interpretation of workspace snapshot information
- Clear health classification
- A recommended next action
- An exact suggested command
- A short explanation for the recommendation
- Mode-aware guidance for both direct/manual mode and starter-pack mode
- Clear indication when an issue is likely starter-pack/provider-related versus local workspace-related
- Supporting docs and examples

### Out of Scope
- Automatic execution of recommended commands
- Automatic cross-repo remediation
- Rich UI/dashboard implementation
- New starter-pack schema changes unless strictly required
- Replacing existing verify flow

---

## Primary User Stories

### User Story 1 — Basic Orientation
As a solo operator,
I want to run a single command,
so that I can understand whether my workspace is healthy and what to do next.

### User Story 2 — Blocked Flow
As a user with a blocked workspace,
I want the system to tell me whether I am waiting on a human decision,
so that I do not waste time guessing which command to run.

### User Story 3 — Verification Failure
As a user whose initialization verification failed,
I want the doctor output to indicate whether the issue is local or starter-pack related,
so that I know whether to repair in async-dev or return to advisor/input generation.

### User Story 4 — Completion Hygiene
As a user who finished a feature,
I want the doctor to recommend archive or closeout actions,
so that completed work does not remain in an ambiguous state.

---

## Proposed UX

### Command Surface
Preferred option:
```bash
asyncdev doctor
```

Optional compatible variant:
```bash
asyncdev status --guidance
```

The command should be lightweight, readable, and safe to run frequently.

### Suggested Output Shape
The output should include at minimum:
- overall health
- initialization mode
- current product
- current feature
- current phase
- verification state
- pending decision state
- recommended next action
- exact command to run
- rationale
- warnings / no-auto-proceed conditions

Example structure:

```text
Workspace Health: ATTENTION_NEEDED
Initialization Mode: starter-pack
Current Feature: 028-repo-linked-workspace-snapshot
Current Phase: verify_failed
Verification Status: failed (compatibility mismatch)
Pending Decisions: none

Recommended Next Action:
Re-check starter-pack compatibility metadata and re-run verification.

Suggested Command:
asyncdev verify starter-pack ./starter-pack.yaml

Why:
The current workspace initialized from a starter pack, but the recorded compatibility metadata does not match the expected async-dev version requirement.

Do Not Auto-Proceed:
Do not continue feature execution until initialization verification succeeds.
```

---

## Health Model
The doctor should classify workspace status into a small, stable set.

Recommended initial states:
- `HEALTHY`
- `ATTENTION_NEEDED`
- `BLOCKED`
- `COMPLETED_PENDING_CLOSEOUT`
- `UNKNOWN`

### Suggested interpretation examples
- `HEALTHY`:
  current feature active, no pending decision, verification passed, no unresolved blockers
- `ATTENTION_NEEDED`:
  verification failed, missing expected artifact, drift detected, no fatal block yet
- `BLOCKED`:
  explicit pending async decision or unresolved required input
- `COMPLETED_PENDING_CLOSEOUT`:
  implementation/review done but archive or closeout step missing
- `UNKNOWN`:
  insufficient workspace metadata to make a reliable recommendation

---

## Recommendation Rules
The initial rules should stay simple and deterministic.

### Rule Group A — No current feature
If no active feature exists:
- classify as `ATTENTION_NEEDED`
- recommend creating or selecting a feature
- provide the next command

### Rule Group B — Pending async decision
If a required human decision is pending:
- classify as `BLOCKED`
- recommend reviewing decision status or resuming after resolution
- warn against continuing execution blindly

### Rule Group C — Verification failure
If verification failed:
- classify as `ATTENTION_NEEDED`
- recommend re-running verify or checking compatibility details
- if starter-pack mode, mention potential provider/input issue

### Rule Group D — Healthy active flow
If feature is active and verification is good:
- classify as `HEALTHY`
- recommend the next operational command appropriate to the phase

### Rule Group E — Done but not closed out
If feature work appears complete but archive/closeout is missing:
- classify as `COMPLETED_PENDING_CLOSEOUT`
- recommend archive or final review command

### Rule Group F — Missing required state
If the workspace lacks enough metadata:
- classify as `UNKNOWN`
- recommend the most conservative next inspection step

---

## Mode Awareness
Feature 029 must preserve the optional nature of advisor integration.

### Direct/Manual Mode
Guidance must work fully without advisor.
No recommendation may assume that advisor exists.

### Starter-Pack Mode
If the workspace was initialized from a starter pack, the doctor may surface:
- provider name (if recorded)
- contract version
- compatibility metadata state
- recommendation to re-check or regenerate starter pack when appropriate

But it must not assume advisor is the only provider.
It should refer to the issue as a **starter-pack/provider/input issue** first, with advisor-specific wording only when confidently known.

---

## Cross-Repo Boundary

### async-dev responsibilities
- implement doctor/guidance logic
- consume current workspace state and snapshot data
- generate recommendations
- render operator-facing output
- document behavior and examples

### advisor responsibilities
No mandatory code changes required.
Optional compatibility note only if helpful in docs.

This feature should not require advisor changes to be useful.

---

## Deliverables

### In `amazing-async-dev`
- doctor command or guidance entry
- supporting guidance logic
- `docs/doctor.md`
- example scenarios under `examples/`
- README links to doctor guidance where appropriate

### Optional documentation touchups
- small cross-link from verify or snapshot docs to doctor docs

### In `amazing-skill-pack-advisor`
- no required code changes
- optional documentation note only if needed

---

## Acceptance Criteria

### AC1 — Single-command guidance entry exists
A user can run a single documented command to receive workspace diagnosis and next-action guidance.

### AC2 — Health state is explicit
The output clearly classifies workspace health using a documented status model.

### AC3 — Next action is explicit
The output includes a recommended next action and an exact suggested command.

### AC4 — Rationale is present
The output explains why the recommendation is being made.

### AC5 — Blocked states are safe
When a human decision is pending or another hard block exists, the output clearly warns against auto-proceeding.

### AC6 — Direct/manual mode is fully supported
The feature works correctly even when no starter pack or advisor linkage exists.

### AC7 — Starter-pack mode is compatibility-aware
When starter-pack metadata exists, the feature can surface relevant compatibility/provider clues without making advisor mandatory.

### AC8 — Example-driven onboarding exists
At least one example scenario demonstrates doctor output for:
- healthy flow
- blocked flow
- verification failure
- completion pending closeout

### AC9 — No hidden mutation
Running the doctor command does not mutate workspace state.

---

## Suggested Implementation Notes
- Reuse Feature 028 snapshot/state structures where possible.
- Keep logic deterministic and easy to reason about.
- Prefer conservative recommendations over aggressive inference.
- Use plain, operator-oriented language.
- Avoid coupling guidance logic to a single provider implementation.

---

## Risks

### Risk 1 — Overreach into orchestration
If the feature begins auto-repairing or auto-running commands, it will blur the control boundary.

Mitigation:
Keep this feature recommendation-only.

### Risk 2 — Provider coupling
If the feature assumes advisor for all starter-pack cases, optionality is weakened.

Mitigation:
Use provider-neutral wording by default.

### Risk 3 — False confidence
If recommendations are too aggressive, users may trust an incorrect next step.

Mitigation:
Support `UNKNOWN` and conservative fallback recommendations.

---

## Success Criteria
The feature is successful if:
- users can run one command and immediately understand their next safe step,
- fewer operations require manual interpretation of snapshot data,
- blocked vs healthy vs closeout-needed states become obvious,
- starter-pack-related issues are easier to route without turning advisor into a mandatory dependency.

---

## Recommended Sequencing
This feature should follow Feature 028 because it depends on snapshot/state visibility, but it should remain smaller than a full repair engine.

Potential future follow-up after 029:
- optional fix-it hints,
- richer closeout guidance,
- lightweight machine-readable doctor output,
- optional automation hooks built on top of explicit recommendation states.

