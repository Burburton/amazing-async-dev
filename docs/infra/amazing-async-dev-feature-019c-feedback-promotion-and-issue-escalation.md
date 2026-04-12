# Feature 019c — Feedback Promotion / Issue Escalation

## 1. Feature Summary

### Feature ID
`019c-feedback-promotion-and-issue-escalation`

### Title
Feedback Promotion / Issue Escalation

### Goal
Add a controlled mechanism for promoting triaged workflow feedback into formal async-dev follow-up work, without introducing automatic GitHub issue creation yet.

### Why this matters
Feature 019a introduced workflow feedback capture.
Feature 019b introduced workflow feedback triage.

That means `amazing-async-dev` can now:

- capture workflow/system issues
- distinguish likely async-dev issues from product issues
- record uncertainty
- indicate which items may deserve escalation

However, the system still needs a clear next step for items marked as important.

At this stage, operators still need a structured way to answer:

- which workflow feedback items should become formal follow-up work?
- how should a candidate issue be promoted?
- what information should carry over into formal follow-up?
- how can the system preserve reviewability without auto-creating noisy issues?

This feature exists to provide that missing promotion step.

---

## 2. Objective

Create a lightweight, explicit promotion layer so triaged workflow feedback can be turned into formal async-dev follow-up records in a controlled way.

This feature should make it possible to:

1. identify which triaged workflow feedback items deserve formal follow-up
2. promote them explicitly
3. preserve the original feedback context during promotion
4. create a stable handoff into async-dev improvement work
5. avoid premature or noisy automatic issue creation

This feature is intentionally narrower than GitHub issue automation.

It is **not** trying to solve:
- automatic external issue tracker creation
- full bug workflow management
- ownership assignment
- automatic prioritization systems
- external sync to GitHub/Jira

---

## 3. Scope

### In scope
- define explicit promotion of workflow feedback items
- define what a promoted issue/candidate record looks like
- support promotion from triaged workflow feedback
- preserve linkage between original feedback and promoted record
- support inspection of promoted items
- support promotion visibility in review and follow-up flows
- document the intended promotion model

### Out of scope
- automatic GitHub issue creation
- automatic external tracker sync
- complete issue lifecycle platform
- assignee workflows
- advanced prioritization engines
- team collaboration workflow

---

## 4. Success Criteria

This feature is successful when:

1. triaged workflow feedback can be explicitly promoted
2. promotion preserves enough context to support follow-up work
3. promotion is controlled and reviewable
4. the system can distinguish captured feedback from formal follow-up records
5. async-dev improvement work can be sourced more systematically from real usage
6. the system avoids jumping straight from feedback to noisy automatic issue creation

---

## 5. Core Design Principles

### 5.1 Promotion must be explicit
A feedback item should not become formal follow-up silently.

### 5.2 Preserve traceability
Promoted records must remain linked to the original workflow feedback.

### 5.3 Keep the first version lightweight
The first promotion layer should stay simple and practical.

### 5.4 Distinguish feedback from formal follow-up
Captured signals and promoted follow-up records serve different roles.

### 5.5 Delay automation until the signal is trustworthy
Automatic issue creation should wait until promotion quality is proven in practice.

---

## 6. Main Capabilities

## 6.1 Promotion trigger

### Purpose
Allow an operator or workflow to promote a feedback item into formal follow-up.

### Expected inputs
- triaged workflow feedback item
- optional promotion note
- optional target follow-up category

### Notes
The first version should prefer explicit manual promotion.

---

## 6.2 Promoted follow-up record

### Purpose
Represent the promoted form of a workflow feedback item.

### Expected contents
- promoted record ID
- source feedback ID
- source triage information
- summary
- reason for promotion
- promotion timestamp
- promotion note
- current follow-up status

### Notes
This is not yet an external GitHub issue.
It is an internal formalized follow-up object.

---

## 6.3 Linkage preservation

### Purpose
Preserve the relationship between:
- original workflow feedback
- triage result
- promoted follow-up record

### Expected support
The system should make it easy to answer:
- which feedback item produced this promoted record?
- was this based on a self-corrected issue or unresolved issue?
- what triage information justified promotion?

### Notes
This traceability is one of the main reasons to separate promotion from raw capture.

---

## 6.4 Inspection and filtering

### Purpose
Allow promoted follow-up records to be reviewed clearly.

### Expected support
- list promoted records
- inspect a promoted record
- filter by follow-up status
- filter by source domain or promotion reason if useful

### Notes
Keep the inspection model CLI-friendly and simple.

---

## 6.5 Review integration

### Purpose
Allow nightly/operator review to see whether workflow feedback has already been promoted.

### Expected value
This helps prevent:
- duplicate promotion
- forgotten candidate issues
- confusion about whether a problem is already being tracked formally

### Notes
The nightly layer should not become a full issue dashboard.
It only needs enough visibility to help the operator act correctly.

---

## 7. Promotion Model Expectations

The exact schema may vary, but the promoted record should likely support fields such as:

- `promotion_id`
- `source_feedback_id`
- `summary`
- `promotion_reason`
- `promotion_note`
- `promoted_at`
- `followup_status`

### Useful optional fields
- `source_problem_domain`
- `source_confidence`
- `source_escalation_recommendation`
- `candidate_feature_followup`
- `artifact_reference`

### Notes
The first version should keep follow-up status simple.

### Suggested initial `followup_status` values
- `open`
- `reviewed`
- `addressed`
- `closed`

---

## 8. Storage Expectations

The first version should support structured storage in a way consistent with the existing artifact + SQLite pattern.

### Recommended approach
- artifact form for human readability
- SQLite index/metadata for lookup and filtering

### Example artifact location
```text
.runtime/feedback-promotions/<promotion_id>.yaml
```

or another clearly documented location.

### Notes
The exact location can vary, but it should remain consistent and reviewable.

---

## 9. Integration Expectations

This feature should integrate with:

- workflow feedback records
- triage results
- nightly management summary where relevant
- CLI inspection flows
- later async-dev hardening workflow where useful

### Notes
This feature is the bridge between feedback capture/triage and future issue workflow.
It should remain narrower than full external integration.

---

## 10. CLI Expectations

The first version should likely support commands such as:

```bash
asyncdev feedback promote --feedback-id <id>
asyncdev feedback promotions list
asyncdev feedback promotions show --promotion-id <id>
```

### Notes
The exact command shape may vary, but the intent should stay clear and lightweight.

---

## 11. Deliverables

This feature must add:

### 11.1 Promotion mechanism
A practical way to promote triaged workflow feedback.

### 11.2 Promoted follow-up object
A structured record representing formalized follow-up.

### 11.3 Inspection support
A way to inspect promoted records and their linkage to original feedback.

### 11.4 Review visibility
Enough visibility to understand whether candidate workflow issues have already been promoted.

### 11.5 Documentation
At least one document or section explaining:
- what promotion is
- how it differs from raw feedback and triage
- how it differs from external issue creation
- when promotion should be used

---

## 12. Acceptance Criteria

- [ ] triaged workflow feedback can be explicitly promoted
- [ ] promoted records preserve linkage to source feedback
- [ ] promoted records are inspectable
- [ ] promoted records are distinguishable from raw feedback
- [ ] review flow can reflect promotion state where useful
- [ ] documentation explains promotion clearly

---

## 13. Risks

### Risk 1 — Promotion becomes too heavy
If promotion is too cumbersome, operators will skip it.

**Mitigation:** keep the model and CLI lightweight.

### Risk 2 — Promotion and triage become conflated
If promotion is not clearly distinct from triage, the workflow becomes confusing.

**Mitigation:** define clear stage boundaries: capture → triage → promotion.

### Risk 3 — Promotion is mistaken for external issue creation
This may create expectations of broader automation too early.

**Mitigation:** document that this is an internal formal follow-up layer only.

### Risk 4 — Duplicate promotions
Without enough visibility, the same issue may be promoted multiple times.

**Mitigation:** provide basic review visibility and linkage inspection.

---

## 14. Recommended Implementation Order

1. define promoted follow-up record model
2. define promotion linkage rules
3. implement explicit promotion command
4. implement list/show inspection for promoted records
5. add useful visibility in review flows
6. document the promotion model and boundaries

---

## 15. Suggested Validation Questions

This feature should make the system better able to answer:

- which workflow feedback items have become formal follow-up work?
- why was this item promoted?
- what original evidence supported the promotion?
- is this issue already being tracked formally?
- how is promoted follow-up different from raw captured feedback?

If the operator still has no clear formal step between feedback triage and external issue creation, this feature is not done.

---

## 16. Definition of Done

Feature 019c is done when:

- triaged workflow feedback can be explicitly promoted
- promotion is traceable and reviewable
- promoted follow-up records can be inspected
- the system has a clear bridge between raw workflow feedback and later issue handling

If the workflow still jumps from captured feedback directly to ad hoc issue handling with no formal intermediate step, this feature is not done.
