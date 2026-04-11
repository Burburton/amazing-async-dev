# Feature 019a — Workflow Feedback Capture

## 1. Feature Summary

### Feature ID
`019a-workflow-feedback-capture`

### Title
Workflow Feedback Capture

### Goal
Add a lightweight first-class mechanism to capture `amazing-async-dev` workflow issues discovered during real usage, so those issues are not silently corrected and forgotten.

### Why this matters
`amazing-async-dev` is now being used in increasingly real development scenarios.

At this stage, a new class of problem becomes important:

- the system may expose defects in its own workflow behavior
- those defects may be noticed during execution or review
- the issue may be worked around or self-corrected
- but the defect may never be recorded for later investigation

Examples:
- `ExecutionPack` points to the wrong feature sequence
- execution assumptions are wrong but corrected manually
- nightly summary misses an important state
- workflow output is inconsistent with the actual runtime context

If these issues are not captured explicitly, the system can appear healthier than it really is.

This feature exists to create the first lightweight capture layer for such issues.

---

## 2. Objective

Create the smallest useful version of a workflow feedback system for `amazing-async-dev`.

This feature should make it possible to:

1. record workflow/system issues when they are noticed
2. distinguish them from ordinary product issues at a basic level
3. preserve them even when the run continues
4. surface them in nightly review
5. make them available for later hardening work

This feature is intentionally narrow.

It is **not** trying to solve:
- full defect triage
- deep root cause analysis
- automatic GitHub issue creation
- advanced workflow classification

Those belong to later features.

---

## 3. Scope

### In scope
- define a lightweight `WorkflowFeedback` object
- support recording workflow feedback explicitly
- support minimal useful issue classification
- support indicating whether an issue was self-corrected
- support indicating whether follow-up is needed
- support storing workflow feedback in a structured way
- support surfacing workflow feedback in nightly review
- provide basic CLI access for capture and inspection
- document when and how workflow feedback should be recorded

### Out of scope
- advanced triage logic
- confidence scoring
- deep problem-domain arbitration
- automated GitHub issue creation
- bug tracker synchronization
- complex issue lifecycle management
- large taxonomy design
- root cause automation

---

## 4. Success Criteria

This feature is successful when:

1. workflow issues in `amazing-async-dev` can be recorded explicitly
2. self-corrected issues are not silently lost
3. the operator can inspect recorded workflow feedback
4. nightly review can show workflow feedback discovered during the day
5. real usage starts producing usable system-improvement signals
6. the mechanism stays lightweight and practical

---

## 5. Core Design Principles

### 5.1 Capture first, triage later
The first priority is to preserve signal.  
Do not block capture on perfect classification.

### 5.2 Keep the model lightweight
This is not yet a full issue management system.

### 5.3 Record even self-corrected defects
A hidden defect is still useful to track even if the immediate run continued.

### 5.4 Preserve review value
The captured feedback should help nightly review, not create noise.

### 5.5 Avoid over-design
Use only the minimum structure needed to be useful in real practice.

---

## 6. Main Capabilities

## 6.1 Workflow feedback record

### Purpose
Represent a workflow/system issue discovered during real usage.

### Typical examples
- feature sequencing inconsistency
- incorrect execution assumptions
- state mismatch in generated artifacts
- missing or misleading summary output
- repo linkage confusion
- workflow guidance inconsistency

### Notes
This record should be simple and practical.

---

## 6.2 Basic classification

### Purpose
Support a small amount of useful categorization.

### Suggested initial categories
- `sequencing`
- `planning`
- `execution_pack`
- `state_mismatch`
- `summary_review`
- `archive_history`
- `repo_integration`
- `recovery_logic`
- `other`

### Notes
This category set is intentionally moderate in size.
It can be refined later.

---

## 6.3 Self-corrected and follow-up semantics

### Purpose
Distinguish:
- issues that were noticed and worked around
- issues that still need future attention

### Expected support
Each feedback item should indicate:
- whether it was self-corrected
- whether follow-up is required

### Notes
This is one of the most important parts of the first version.

---

## 6.4 Nightly visibility

### Purpose
Make workflow/system issues visible in the existing nightly review flow.

### Expected output
Nightly review should be able to answer:
- what workflow issues were detected today?
- were they self-corrected?
- which ones still need follow-up?

### Notes
This should not require a new major UI layer.

---

## 6.5 Basic inspection capability

### Purpose
Allow operators to review recorded workflow feedback later.

### Expected support
- list recorded workflow feedback
- inspect one workflow feedback item
- view unresolved/follow-up-needed items

### Notes
This should stay simple and CLI-friendly.

---

## 7. Object Model Expectations

The exact schema may vary, but a useful first version should support fields such as:

- `feedback_id`
- `issue_type`
- `detected_by`
- `detected_in`
- `product_id`
- `feature_id`
- `description`
- `impact`
- `self_corrected`
- `requires_followup`
- `artifact_reference`
- `detected_at`

### Optional but acceptable in v1
- `problem_domain`
- `status`

### Notes
Do not over-model this in the first version.

---

## 8. Storage Expectations

The first version should support structured storage in a way that fits the repository’s existing philosophy.

### Recommended approach
- project-level artifact storage for human readability
- optional SQLite/index support for lookup convenience

### Example artifact location
```text
projects/<product_id>/workflow-feedback/<feedback_id>.yaml
```

### Notes
This feature does not need to fully solve long-term storage architecture debates.
It only needs to store feedback reliably and visibly.

---

## 9. Integration Expectations

This feature should integrate with:

- `ExecutionResult` at least through summary/reference linkage
- nightly management summary
- review-night flow
- CLI/operator workflow

### Recommended first integration style
Keep the workflow feedback record as its own object, and expose references/summaries in relevant review artifacts.

### Notes
Avoid forcing a deep runtime redesign in this feature.

---

## 10. CLI Expectations

The first version should likely support a minimal command set such as:

```bash
asyncdev feedback record
asyncdev feedback list
asyncdev feedback show --feedback-id <id>
```

### Notes
A minimal CLI is enough.
This feature should not try to solve advanced issue workflow yet.

---

## 11. Deliverables

This feature must add:

### 11.1 WorkflowFeedback object
A lightweight structured record for workflow issues.

### 11.2 Capture mechanism
A practical way to record workflow feedback.

### 11.3 Inspection commands
A small CLI surface for recording and inspecting workflow feedback.

### 11.4 Nightly review visibility
Workflow feedback surfaced in nightly summary/review artifacts.

### 11.5 Documentation
At least one document or section explaining:
- what workflow feedback is
- when it should be recorded
- what the first version captures
- what later versions will handle separately

---

## 12. Acceptance Criteria

- [ ] workflow issues can be recorded explicitly
- [ ] self-corrected issues can be captured
- [ ] follow-up-needed issues can be marked
- [ ] recorded workflow feedback can be listed and inspected
- [ ] nightly review can show workflow feedback from the day
- [ ] documentation explains the first-layer mechanism clearly

---

## 13. Risks

### Risk 1 — Too much friction to record feedback
If recording is too heavy, operators will skip it.

**Mitigation:** keep the object and CLI minimal.

### Risk 2 — Over-designing the object model
A too-complex schema will slow adoption.

**Mitigation:** keep only the fields needed for first useful capture.

### Risk 3 — Confusing workflow issues with product issues
If the distinction is unclear, the signal becomes noisy.

**Mitigation:** document examples and intended usage clearly.

### Risk 4 — Trying to solve triage too early
The feature may grow into a larger process-defect platform too soon.

**Mitigation:** keep this feature focused on capture and nightly visibility only.

---

## 14. Recommended Implementation Order

1. define the minimal `WorkflowFeedback` schema
2. define the initial issue-type taxonomy
3. implement capture command
4. implement list/show inspection commands
5. add nightly review visibility
6. document the feature and usage boundaries

---

## 15. Suggested Validation Questions

This feature should make the system better able to answer:

- did async-dev itself expose a workflow issue today?
- was that issue captured?
- was it self-corrected or still important?
- does it require later follow-up?
- can I see it again during nightly review?

If the answer still depends only on the operator’s memory, this feature is not done.

---

## 16. Definition of Done

Feature 019a is done when:

- workflow issues can be captured explicitly
- self-corrected issues are not silently lost
- nightly review can surface workflow feedback
- the system begins producing structured self-improvement signals from real usage

If async-dev workflow defects can still occur, get patched around, and disappear without structured trace, this feature is not done.
