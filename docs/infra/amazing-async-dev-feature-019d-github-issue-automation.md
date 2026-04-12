# Feature 019d — GitHub Issue Automation (Future)

## 1. Feature Summary

### Feature ID
`019d-github-issue-automation`

### Title
GitHub Issue Automation

### Goal
Introduce a controlled future automation layer for turning promoted async-dev workflow feedback into GitHub issues, only after the feedback capture, triage, and promotion pipeline has proven reliable enough in real usage.

### Why this matters
By the time this feature is relevant, `amazing-async-dev` is expected to already support:

- workflow feedback capture
- workflow feedback triage
- feedback promotion / issue escalation
- nightly visibility of workflow defects
- structured internal follow-up records

That means the system will already have a meaningful internal workflow for:

- detecting async-dev problems
- classifying them
- judging whether they deserve follow-up
- promoting them into formal internal follow-up records

Only after that pipeline is stable does it make sense to consider GitHub issue automation.

Without this sequencing, automatic issue creation would likely create:
- noisy false positives
- weakly justified issues
- duplicate reports
- low operator trust

This feature exists to automate issue creation only when the signal quality is high enough.

---

## 2. Objective

Create a future automation layer that can convert promoted async-dev follow-up records into GitHub issues in a controlled and reviewable way.

This feature should make it possible to:

1. identify promotion records that are ready for external issue creation
2. generate issue content from structured promotion data
3. create GitHub issues in a controlled way
4. preserve linkage between feedback, promotion, and GitHub issue
5. avoid noisy or duplicate issue creation

This feature is deliberately future-facing.

It should only be implemented after:
- 019a capture is stable
- 019b triage is trustworthy
- 019c promotion is used successfully in real workflows

---

## 3. Scope

### In scope
- define readiness criteria for issue creation
- define a GitHub issue draft model based on promotion data
- define a controlled issue creation flow
- define linkage between promotion records and created GitHub issues
- support inspection of issue automation state
- document the automation boundaries and safeguards

### Out of scope
- generic bug tracker abstraction
- Jira/Linear/etc support
- full multi-provider ticketing system
- advanced issue deduplication engine
- broad workflow automation platform
- full ownership/assignee routing system
- advanced prioritization system

---

## 4. Success Criteria

This feature is successful when:

1. only high-signal promoted records are eligible for GitHub issue creation
2. issue automation preserves traceability back to the source promotion and feedback
3. automation remains reviewable and controlled
4. duplicate or low-value issue creation is minimized
5. async-dev can more systematically turn real usage defects into tracked improvement work
6. operator trust in the issue automation remains high

---

## 5. Core Design Principles

### 5.1 Automation must come after signal quality
Do not automate issue creation until the upstream workflow proves reliable.

### 5.2 Issue creation should be controlled, not magical
The system should make issue creation understandable and reviewable.

### 5.3 Preserve traceability end-to-end
A GitHub issue should remain linked to:
- source workflow feedback
- triage result
- promotion record

### 5.4 Prevent duplicates aggressively
Duplicate issue creation would quickly destroy trust.

### 5.5 Keep the first version narrow
This is not a full external integration platform.

---

## 6. Main Capabilities

## 6.1 Issue readiness criteria

### Purpose
Decide when a promoted record is eligible for GitHub issue creation.

### Suggested readiness signals
- source `problem_domain` is `async_dev`
- source `confidence` is sufficiently high
- source `escalation_recommendation` was `candidate_issue`
- promotion exists and is not already linked to an issue
- promoted record contains enough context for useful issue creation

### Notes
This feature should prefer under-automation to over-automation.

---

## 6.2 Issue draft generation

### Purpose
Generate a GitHub-issue-ready representation from a promoted record.

### Expected draft content
- title
- summary
- problem description
- relevant context
- reproduction hints if available
- source references
- promotion rationale

### Notes
Issue content should be derived from structured records, not improvised from thin metadata.

---

## 6.3 Controlled issue creation

### Purpose
Create GitHub issues in a way that avoids uncontrolled noise.

### Recommended first mode
- explicit/manual trigger
- or operator-confirmed creation from a prepared draft

### Notes
Automatic background issue creation should not be the first mode.

---

## 6.4 Traceability and linking

### Purpose
Preserve linkage between:
- workflow feedback record
- triaged feedback
- promotion record
- GitHub issue

### Expected support
The system should make it easy to answer:
- which workflow feedback produced this GitHub issue?
- which promotion record created it?
- has this issue already been externalized?

### Notes
This is essential to avoid confusion and duplication.

---

## 6.5 Duplicate prevention

### Purpose
Prevent repeated creation of the same issue.

### Expected support
At minimum, the system should:
- detect whether a promotion record already has a linked GitHub issue
- block or warn on repeated issue creation attempts
- store created issue references

### Notes
The first version does not need full semantic duplicate detection.

---

## 7. Automation Model Expectations

The exact schema may vary, but this feature should likely introduce or extend fields such as:

### On promotion records
- `issue_creation_status`
- `github_issue_id`
- `github_issue_url`
- `issue_created_at`

### Optional future-friendly fields
- `issue_draft_hash`
- `issue_creation_attempts`
- `issue_creation_note`

### Notes
The first version should stay small and explicit.

---

## 8. Integration Expectations

This feature should integrate with:

- promoted follow-up records from 019c
- workflow feedback traceability chain
- optional GitHub repository configuration
- operator review flows where helpful

### Notes
This feature should not bypass the promotion layer.
Promotion remains the mandatory upstream gate.

---

## 9. CLI Expectations

The first version should likely support commands such as:

```bash
asyncdev feedback issue draft --promotion-id <id>
asyncdev feedback issue create --promotion-id <id>
asyncdev feedback issue show --promotion-id <id>
```

### Notes
Exact command shape may vary.
The key is that issue creation remains explicit and reviewable.

---

## 10. Deliverables

This feature must add:

### 10.1 Issue readiness model
A practical rule set for when promoted records may become GitHub issues.

### 10.2 Issue draft generation
A structured issue draft output derived from promotion data.

### 10.3 Controlled creation flow
A safe way to create GitHub issues from promoted records.

### 10.4 Traceability fields
Clear linkage between issue, promotion, and source feedback.

### 10.5 Documentation
At least one document or section explaining:
- when issue automation should be used
- why it is gated behind capture/triage/promotion
- how duplicate prevention works
- how to review issue creation safely

---

## 11. Acceptance Criteria

- [ ] only eligible promoted records can be used for issue creation
- [ ] issue draft content is generated from structured records
- [ ] created issues preserve traceability to promotion and source feedback
- [ ] duplicate creation is blocked or clearly warned
- [ ] issue creation remains controlled and reviewable
- [ ] documentation explains the automation boundary clearly

---

## 12. Risks

### Risk 1 — Automating too early
If issue automation is introduced before upstream signal quality is mature, noise will dominate.

**Mitigation:** explicitly gate this feature behind stable 019a/019b/019c workflows.

### Risk 2 — Duplicate issue spam
Repeated external issue creation would damage trust quickly.

**Mitigation:** require promotion linkage and explicit duplicate checks.

### Risk 3 — Weak issue content
If issues are created from thin or incomplete records, they will not be useful.

**Mitigation:** require sufficient context in promoted records before creation.

### Risk 4 — Confusing internal follow-up with external issue state
If these states are mixed, workflow becomes unclear.

**Mitigation:** keep promotion and external issue creation clearly separated.

---

## 13. Recommended Implementation Order

1. define readiness criteria for issue creation
2. define issue draft model
3. define traceability fields on promotion records
4. implement explicit issue draft generation
5. implement controlled issue creation
6. implement duplicate prevention
7. document automation safeguards and boundaries

---

## 14. Suggested Validation Questions

This feature should make the system better able to answer:

- is this promoted item really ready to become a GitHub issue?
- what issue content will be created?
- has this already been externalized?
- can the created issue be traced back to the original workflow defect?
- does the automation preserve trust instead of adding noise?

If issue creation still feels noisy, weakly justified, or hard to trace, this feature is not done.

---

## 15. Definition of Done

Feature 019d is done when:

- promoted workflow feedback can be turned into GitHub issues in a controlled way
- traceability is preserved end-to-end
- duplicate creation is prevented or strongly constrained
- the automation is trustworthy enough to reduce manual issue creation without creating noise

If the system still cannot safely externalize promoted workflow defects into GitHub issue tracking, this feature is not done.
