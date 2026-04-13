# run-day-project-parameter-hardening

## Title
run-day `--project` Parameter Hardening

## Summary
Add a `--project` parameter to `run-day` so it aligns with the canonical operator loop and behaves consistently with the other core loop commands.

This is a small hardening task, not a new capability feature.

## Why
During multi-day dogfooding of the 026–036 loop, one recurring UX issue appeared on 3 consecutive days:

- `run-day` lacks `--project`
- other canonical loop commands already support project-scoped operation
- this creates avoidable inconsistency in the main operator flow

The loop itself is stable and validated.
This task exists to improve UX consistency and reduce friction.

## Background
The validated canonical loop is:

- `review-night`
- `resume-next-day`
- `plan-day`
- `run-day`

Dogfooding results showed:
- no true capability gaps
- one recurring medium-severity UX issue
- this issue was specifically that `run-day` did not align with the project-scoped behavior of the other loop commands

## Goal
Make `run-day` accept a `--project` argument so users can run it in the same project-scoped way they already use for the rest of the canonical loop.

## Scope
This hardening task should:

1. add `--project` support to `run-day`
2. make project selection behavior consistent with adjacent loop commands where reasonable
3. update CLI help and documentation
4. add tests for project-scoped `run-day` usage
5. preserve existing behavior when `--project` is omitted, unless current repo conventions already require explicit project selection

## Non-Goals
Do not:
- redesign run-day execution
- change planning intent alignment behavior from Feature 036
- add multi-project orchestration
- introduce new execution modes
- open a new feature line
- change unrelated CLI semantics

## UX Requirement
The goal is consistency, not novelty.

A user should be able to use:
- `review-night --project <id>`
- `resume-next-day --project <id>`
- `plan-day ... --project <id>`
- `run-day --project <id>`

without feeling that `run-day` is the odd command out.

## Expected Behavior
### When `--project` is provided
`run-day` should:
- scope execution to the specified project
- resolve the correct active/project-specific context
- behave consistently with existing project-scoped loop commands

### When `--project` is omitted
Use the repository's current fallback pattern, for example:
- active/default project resolution
- existing current-project behavior
- or existing no-project fallback

This task should not invent a brand-new fallback model.

## Implementation Guidance
Follow existing CLI conventions already used by nearby commands.

Prefer:
- matching argument naming
- matching project resolution behavior
- matching help-text style
- matching error behavior for unknown/missing projects

## Suggested Areas to Update
Adjust names/locations to match the repository.

Likely areas include:
- `run-day` CLI argument parsing
- project resolution/loading path for run-day
- help text / command docs
- tests for project-scoped execution

## Documentation Requirements
Update relevant docs/help so users can clearly see that `run-day` now supports `--project`.

Likely updates:
- CLI help output
- run-day usage docs
- any canonical loop docs where command examples are shown

## Test Requirements
Add focused tests for:

1. `run-day --project <id>` works for a valid project
2. invalid project id produces the expected error behavior
3. omitted `--project` preserves expected fallback behavior
4. help text includes the new parameter
5. project-scoped run-day remains compatible with current execution intent behavior

## Acceptance Criteria

### AC1
`run-day` accepts a `--project` parameter.

### AC2
Project-scoped `run-day` behavior is consistent with the canonical loop's project-scoped command style.

### AC3
CLI help and docs reflect the new parameter.

### AC4
Tests cover valid, invalid, and fallback cases.

### AC5
No unrelated run-day behavior is changed.

## Definition of Done
This hardening task is done when:
- `run-day --project` works
- the canonical loop feels more consistent
- docs/help/tests are updated
- no new feature surface is introduced beyond this UX consistency fix

## Priority
Medium.

Reason:
- recurring issue observed across 3 consecutive dogfooding days
- not blocking
- improves canonical loop consistency
- suitable as a small post-validation hardening task
