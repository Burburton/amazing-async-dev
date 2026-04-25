# Feature 079 — Project Artifacts and Evidence Rollup

## Metadata

- **Feature ID**: `079-project-artifacts-and-evidence-rollup`
- **Feature Name**: `Project Artifacts and Evidence Rollup`
- **Feature Type**: `platform foundation / artifact coherence / evidence layer consolidation`
- **Priority**: `High`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Target Branch**: `platform/foundation`
- **Related Features**:
  - `063-execution-observer-foundation`
  - `066-execution-recovery-console`
  - `066a-recovery-console-integration-into-async-dev`
  - `069-acceptance-artifact-model-foundation`
  - `072-acceptance-findings-to-recovery-integration`
  - `077-acceptance-cli-and-mainflow-integration`
  - `078-acceptance-recovery-console-integration`

---

## 1. Problem Statement

The platform now includes a substantial execution and operator stack:

- execution kernel
- verification / closeout
- observer findings
- recovery state
- acceptance packs/results/history
- completion blocking
- Recovery Console integration
- CLI and mainflow integration

However, after real dogfooding, a common platform problem becomes increasingly important:

> the platform has many truths, but they are not yet rolled up cleanly into a unified project-level evidence layer.

In practice, this can lead to issues such as:

- artifacts being spread across multiple locations,
- “latest truth” being hard to identify,
- acceptance evidence and recovery evidence feeling separate,
- observer findings not naturally sitting beside the execution they explain,
- operators still needing to inspect multiple files manually,
- future platform overview surfaces needing to reconstruct the same truth repeatedly,
- docs, CLI, and operator UI lacking a single clean evidence hierarchy to consume.

This is no longer mainly an execution problem. It is now a **platform evidence coherence problem**.

Feature 079 addresses that problem by rolling up project/feature evidence into a cleaner, canonical artifact structure so the platform has a stronger shared fact layer.

---

## 2. Goal

Create a coherent **project artifacts and evidence rollup** so that async-dev has a clearer canonical truth layer for each project and feature.

After this feature, the platform should make it much easier to answer questions such as:

- What is the latest execution truth for this feature?
- What is the latest acceptance result?
- What observer findings matter most?
- Is recovery currently active?
- Is completion currently blocked?
- Where are the relevant artifacts for this feature/project?

The goal is to make project-level evidence easier for both machines and operators to consume.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the execution kernel,
- redesign acceptance logic,
- replace the Recovery Console,
- create a giant new UI,
- refactor all artifact schemas from scratch,
- solve all operator experience issues in one pass.

This feature is specifically about **artifact hierarchy, evidence rollup, and canonical fact organization**.

---

## 4. Core Design Principle

### 4.1 One Coherent Evidence Layer

The platform should provide a cleaner answer to:

> where is the evidence for this project/feature/run?

### 4.2 Latest Truth Must Be Easy to Find

Operators and platform components should not have to guess which artifact is the most current or authoritative.

### 4.3 Roll Up, Do Not Randomly Duplicate

The feature should improve discoverability and canonical referencing without creating uncontrolled duplication of artifacts.

### 4.4 Serve Both Human and Machine Consumers

The rolled-up artifact structure should be useful to:

- CLI commands
- Recovery Console
- future operator overview surfaces
- docs/status rollups
- debugging and audit flows
- humans reading project state directly

---

## 5. Target Outcomes

After this feature is complete, async-dev should support a clearer project/feature evidence structure that makes the following easy:

1. locate latest execution result,
2. locate latest acceptance result and acceptance history,
3. locate current recovery status,
4. locate relevant observer findings,
5. identify whether completion is blocked,
6. understand the current feature/project state from a compact rolled-up view,
7. let operator surfaces reuse this evidence layer instead of rebuilding it ad hoc.

---

## 6. Required Functional Changes

### 6.1 Canonical Project/Feature Evidence Structure

Define or refine a canonical artifact hierarchy for project/feature evidence.

This may include project-level and feature-level organization.

The exact directory shape may vary, but it should clearly organize evidence such as:

- latest execution result
- execution history references
- latest acceptance result
- acceptance attempt history references
- observer findings
- recovery/remediation summaries
- completion gate/block summary
- latest overall status snapshot

### 6.2 Latest-Pointer / Summary Artifacts

Introduce a lightweight canonical way to identify the latest relevant truth.

Examples may include:

- `latest-execution-result`
- `latest-acceptance-result`
- `latest-observer-findings`
- `latest-recovery-state`
- `latest-status-summary`

These can be symlinks, index files, summary JSON/markdown, or another canonical approach depending on repo conventions.

The important part is that “latest truth” becomes easy to resolve.

### 6.3 Evidence Summary Adapter or Snapshot

Introduce a rolled-up summary representation for project/feature evidence.

This summary should help answer, in one place:

- current execution status
- latest acceptance status
- latest recovery state
- latest observer significance
- completion blocked or not
- where the detailed artifacts live

This does not need to replace the underlying artifacts, but it should improve discoverability and consumption.

### 6.4 Acceptance Evidence Placement Hardening

Acceptance artifacts should become more naturally placed within the project/feature artifact hierarchy.

At minimum, this should improve discoverability of:

- `AcceptancePack`
- `AcceptanceResult`
- acceptance history
- latest acceptance pointer or summary

This is especially important now that acceptance is a platform-native capability.

### 6.5 Observer and Recovery Evidence Placement Hardening

Observer findings and recovery-related outputs should be easier to find in relation to the feature/project they affect.

This may include:

- finding references grouped under feature/project
- latest recovery summary
- remediation summary
- links between observer findings and acceptance/recovery artifacts

### 6.6 Completion Gate / Block Evidence

If completion is blocked due to acceptance or another platform gate, the evidence layer should make that visible.

A user or tool inspecting project artifacts should be able to tell:

- is this feature blocked?
- why is it blocked?
- what is the latest relevant gate evidence?

### 6.7 Reuse by Operator Surfaces and CLI

The rolled-up evidence structure should be designed so that:

- Recovery Console
- acceptance CLI/status/history
- future operator overview surfaces
- docs/status rollups

can all consume it more easily.

This feature does not need to implement every consumer update, but the evidence layer should be intentionally reusable.

---

## 7. Detailed Requirements

## 7.1 Canonical Artifact Questions

The new structure should make it easy to answer:

- What is the latest execution result?
- What is the latest acceptance result?
- How many acceptance attempts exist?
- Is there an active recovery condition?
- What observer findings matter now?
- Is completion blocked?
- What detailed artifact should I open next?

If the structure still makes these hard to answer, it is not strong enough.

## 7.2 Scope of Rollup

The rollup should operate at least at the **feature level**, and may also include **project-level** summary views if appropriate.

Suggested conceptual layers:

- **project evidence overview**
- **feature evidence bundle**
- **underlying detailed artifacts**

### Principle

Do not flatten everything into one folder; make the hierarchy useful.

## 7.3 Summary Artifact Contents

A project/feature evidence summary should ideally include fields such as:

- feature ID / title
- latest execution result ref
- latest acceptance result ref
- acceptance status
- acceptance attempt count
- recovery required
- latest recovery summary
- observer findings summary
- completion blocked
- updated timestamp

This may be represented as JSON, YAML, markdown, or a mixed approach consistent with repo conventions.

## 7.4 Canonical Naming and Placement

The feature should improve naming clarity so that future readers can quickly understand which artifact is:

- latest
- historical
- summary
- detailed
- blocking
- evidence vs raw output

This may require small naming cleanups or alias/index support.

## 7.5 Back-Reference Strategy

Where helpful, summary artifacts should include back-references to detailed artifacts, not just duplicated data.

This keeps the platform both readable and traceable.

## 7.6 Migration / Compatibility Strategy

If current artifact placement is already in use, the feature should define whether:

- old paths remain valid,
- new summaries/pointers are added on top,
- or a small migration/normalization step is introduced.

The goal should be improvement without unnecessary disruption.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch categories like the following.

### 8.1 Artifact Structure / Summary Files

Potential areas:

- project artifact hierarchy helpers
- feature evidence summary builders
- latest-pointer or index generation logic
- acceptance evidence placement helpers
- observer/recovery summary placement helpers

### 8.2 Existing Runtime / CLI / Operator Integration

Likely updates:

- artifact writing helpers
- acceptance result persistence paths
- observer finding persistence paths
- recovery summary generation
- CLI commands that resolve latest artifacts
- Recovery Console artifact resolution

### 8.3 Documentation Updates

Likely updates:

- README / platform docs
- artifact layout docs
- operator guidance
- acceptance / recovery / observer docs where artifact locations are described

---

## 9. Acceptance Criteria

## AC-001 Canonical Evidence Structure Exists
Project/feature evidence is organized into a clearer and more coherent canonical hierarchy.

## AC-002 Latest Truth Is Easy to Resolve
There is a reliable way to find the latest execution, acceptance, observer, and recovery truth for a feature/project.

## AC-003 Acceptance Evidence Is Better Placed
Acceptance artifacts are easier to locate and reason about within the project/feature hierarchy.

## AC-004 Recovery and Observer Evidence Are Better Placed
Recovery and observer evidence can be found more naturally alongside the feature/project they affect.

## AC-005 Completion Block Evidence Is Visible
The evidence layer can clearly surface whether completion is blocked and why.

## AC-006 Summary Artifacts Exist
Feature/project-level summaries or equivalent rolled-up evidence artifacts exist and are useful.

## AC-007 Operator/CLI Reuse Is Improved
The new structure makes it easier for operator surfaces and CLI commands to resolve evidence consistently.

## AC-008 Documentation Updated
Artifact placement and evidence rollup are documented clearly enough for future contributors/operators.

## AC-009 Tests Added
Automated tests cover evidence summary generation, latest-truth resolution, and key artifact placement behavior.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Execution Evidence Resolution
- latest execution result can be resolved correctly from the rolled-up structure.

### 10.2 Acceptance Evidence Resolution
- latest acceptance result and acceptance history are discoverable correctly.

### 10.3 Recovery Evidence Resolution
- latest recovery status/summary is discoverable correctly.

### 10.4 Observer Evidence Resolution
- relevant observer findings are discoverable correctly.

### 10.5 Completion Block Summary
- blocked/unblocked state is surfaced correctly in the evidence summary.

### 10.6 Summary Artifact Integrity
- rolled-up summary does not become inconsistent with underlying artifact references.

### 10.7 Backward Compatibility / Existing Path Handling
- where applicable, existing artifact consumers are not broken unexpectedly.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. define the canonical evidence hierarchy,
2. define summary/latest-pointer model,
3. integrate acceptance artifact placement,
4. integrate observer/recovery evidence placement,
5. generate feature/project summary artifacts,
6. update artifact resolution consumers where needed,
7. add tests,
8. update docs.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- duplicating all artifact content everywhere,
- creating multiple competing “latest” concepts,
- making the hierarchy overly deep or confusing,
- rewriting everything when a summary/index layer would be enough,
- improving the structure only for one subsystem while leaving others inconsistent.

## 11.3 Backward Compatibility

Where possible, improve the evidence structure additively:

- add summaries,
- add latest pointers,
- add normalized placement,
- then gradually let consumers adopt the better structure.

Avoid unnecessary disruption to existing flows unless clearly justified.

---

## 12. Risks and Mitigations

### Risk 1: Artifact structure becomes too complex
**Mitigation:** prefer a small number of canonical summaries and latest references rather than a sprawling hierarchy.

### Risk 2: Summaries drift from underlying truth
**Mitigation:** generate summaries programmatically from canonical artifacts and test the relationship.

### Risk 3: Too much duplication
**Mitigation:** use summaries and references rather than copying full detailed data.

### Risk 4: Existing consumers break
**Mitigation:** introduce compatibility helpers and keep migration additive where possible.

### Risk 5: Feature scope expands into full platform overview UI
**Mitigation:** keep this focused on the evidence/fact layer, not on big UI work.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- canonical project/feature evidence hierarchy improvements
- latest-truth resolution support
- acceptance artifact placement hardening
- observer/recovery evidence rollup improvements
- completion block evidence summary
- reusable summary artifacts or equivalent rollup layer
- documentation updates
- automated tests

---

## 14. Definition of Done

This feature is considered done only when:

1. it is much easier to find the latest project/feature truth,
2. acceptance, observer, recovery, and execution evidence feel part of one fact layer,
3. operator surfaces and CLI can consume the evidence structure more consistently,
4. artifact spelunking is materially reduced,
5. the platform’s evidence layer feels more coherent and trustworthy.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as a fact-layer consolidation feature,
- focus on evidence discoverability and canonical truth,
- improve machine and operator consumption together,
- keep the solution additive and coherent,
- avoid turning this into premature UI work.

Recommended planning questions:

- what is the canonical project/feature evidence hierarchy?
- how should latest truth be represented?
- what summaries are truly worth having?
- how should acceptance/recovery/observer artifacts relate?
- what existing consumers need small adaptation?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- how project/feature evidence is now organized,
- how latest execution/acceptance/recovery truth is resolved,
- how completion block evidence is surfaced,
- how the new structure improves Recovery Console / CLI / docs consumption,
- how the platform now has a cleaner evidence layer.

It should not claim completion merely because a few files moved.

---

## 17. Summary

Feature 079 strengthens the platform by consolidating its fact layer.

It turns scattered execution, acceptance, observer, and recovery outputs into a more coherent project/feature evidence structure that both humans and platform components can consume more easily.

In short:

> **079 makes the platform’s evidence layer cleaner, more discoverable, and more trustworthy.**
