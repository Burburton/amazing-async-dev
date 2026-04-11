# Feature 019b — Workflow Feedback Triage

## 1. Feature Summary

### Feature ID
`019b-workflow-feedback-triage`

### Title
Workflow Feedback Triage

### Goal
Add a structured triage layer on top of captured workflow feedback so `amazing-async-dev` can better distinguish product issues from async-dev issues, assess confidence, and decide which feedback items need follow-up or escalation.

### Why this matters
Feature 019a introduced the first workflow feedback capture layer.  
That means the system can now preserve workflow/system issues discovered during real usage instead of silently losing them.

However, capture alone is not enough.

Once workflow feedback starts accumulating, the system still needs to answer:

- is this actually an async-dev problem or a product problem?
- how confident is that judgment?
- does this issue matter enough to review later?
- should it just be tracked, or should it become a candidate for a formal issue?

Without a triage layer, workflow feedback remains noisy and hard to act on.

This feature exists to make captured feedback more usable, more trustworthy, and more operationally meaningful.

---

## 2. Objective

Create a lightweight triage layer for workflow feedback so captured feedback items can be classified, reviewed, and prioritized more intelligently.

This feature should make it possible to:

1. distinguish workflow issues from product issues at a clearer level
2. represent uncertainty when the classification is not obvious
3. indicate confidence in the classification
4. indicate whether an item should be ignored, tracked, reviewed, or considered for escalation
5. improve nightly review and later system hardening decisions

This feature is intentionally narrower than full issue management.

It is **not** trying to implement:
- full issue lifecycle management
- GitHub issue automation
- advanced root-cause analysis
- automatic bug ownership assignment

---

## 3. Scope

### In scope
- add a triage layer for existing workflow feedback records
- define domain classification for feedback items
- define confidence levels for triage judgments
- define escalation recommendation levels
- support later review of triaged workflow feedback
- improve nightly review visibility using triage results
- document the intended triage model

### Out of scope
- automatic GitHub issue creation
- bug tracker synchronization
- full issue workflow
- advanced AI-based root-cause analysis
- broad severity systems
- team ownership or assignee logic
- multi-user triage workflow

---

## 4. Success Criteria

This feature is successful when:

1. workflow feedback items can be triaged in a structured way
2. product issues and async-dev issues are more clearly distinguished
3. uncertain cases can be represented honestly
4. nightly review can surface more meaningful workflow feedback status
5. the operator can identify which items are worth following up
6. the feedback system becomes more actionable without becoming too heavy

---

## 5. Core Design Principles

### 5.1 Triage should improve signal quality
The goal is to reduce ambiguity, not to create bureaucracy.

### 5.2 Uncertainty must be allowed
Not every item can be classified confidently at first sight.

### 5.3 Escalation is not issue creation
A feedback item can be a candidate for escalation without immediately becoming a formal issue.

### 5.4 Keep the model lightweight
The first triage layer should remain simple enough to use in real workflows.

### 5.5 Support real operator judgment
The system should help structure triage, not pretend to know everything automatically.

---

## 6. Main Capabilities

## 6.1 Problem domain classification

### Purpose
Classify whether a feedback item appears to belong primarily to:
- the product being built
- `amazing-async-dev` itself
- an uncertain domain

### Recommended initial values
- `product`
- `async_dev`
- `uncertain`

### Notes
This is one of the most important outputs of triage.
It must remain honest and practical.

---

## 6.2 Confidence level

### Purpose
Represent how reliable the current triage judgment is.

### Recommended initial values
- `low`
- `medium`
- `high`

### Notes
A useful triage layer should not force false certainty.

---

## 6.3 Escalation recommendation

### Purpose
Indicate how much follow-up attention a feedback item deserves.

### Recommended initial values
- `ignore`
- `track_only`
- `review_needed`
- `candidate_issue`

### Meaning
- `ignore`: low-value or not worth action
- `track_only`: keep recorded, but no active action needed
- `review_needed`: should be checked by the operator in later review
- `candidate_issue`: likely worth turning into a formal async-dev issue later

### Notes
This does **not** create the issue.  
It only marks the item’s likely next handling path.

---

## 6.4 Triage visibility in nightly review

### Purpose
Improve how workflow feedback is surfaced in nightly management review.

### Expected improvements
Nightly review should help answer:
- which workflow feedback items were async-dev related?
- which ones were uncertain?
- which ones deserve follow-up?
- which ones may later become formal issues?

### Notes
This should build naturally on the `workflow_feedback` section introduced after 019a.

---

## 6.5 Triage inspection support

### Purpose
Allow operators to inspect triaged workflow feedback more effectively.

### Expected support
- list triaged feedback
- filter by domain
- filter by escalation recommendation
- inspect one feedback item with triage fields visible

### Notes
The first version should remain CLI-friendly and practical.

---

## 7. Triage Model Expectations

The exact schema may vary, but the triage layer should likely add fields such as:

- `problem_domain`
- `confidence`
- `escalation_recommendation`
- `triaged_at`
- `triage_note`

### Optional future-friendly fields
- `triaged_by`
- `candidate_followup_feature`
- `root_cause_hint`

### Notes
Do not overbuild the schema in the first triage version.

---

## 8. Integration Expectations

This feature should integrate with:

- workflow feedback records from 019a
- nightly management summary
- feedback list/show inspection flows
- follow-up/hardening planning where appropriate

### Notes
This is a refinement of the workflow feedback system, not a rewrite of capture.

---

## 9. CLI Expectations

The first version should likely extend the feedback CLI with capabilities such as:

```bash
asyncdev feedback triage --feedback-id <id>
asyncdev feedback list --domain async_dev
asyncdev feedback list --escalation candidate_issue
asyncdev feedback show --feedback-id <id>
```

### Notes
The command shape can vary, but the triage flow should remain small and clear.

---

## 10. Deliverables

This feature must add:

### 10.1 Triage fields
A structured triage layer for workflow feedback records.

### 10.2 Triage action
A practical way to add or update triage information for a feedback item.

### 10.3 Inspection support
A way to list and inspect triaged feedback using meaningful filters.

### 10.4 Nightly review integration
Nightly summary should become more informative using triage results.

### 10.5 Documentation
At least one document or section explaining:
- what triage is for
- what `problem_domain` means
- what `confidence` means
- what `escalation_recommendation` means
- why this does not yet create formal issues automatically

---

## 11. Acceptance Criteria

- [ ] workflow feedback items can be triaged with `problem_domain`
- [ ] workflow feedback items can record `confidence`
- [ ] workflow feedback items can record `escalation_recommendation`
- [ ] uncertain classification is supported explicitly
- [ ] triage information is visible in nightly review
- [ ] triaged feedback can be listed and inspected meaningfully
- [ ] documentation explains triage clearly

---

## 12. Risks

### Risk 1 — Too much triage overhead
If triage is too heavy, the operator may stop using it.

**Mitigation:** keep the model compact and practical.

### Risk 2 — False certainty
If the system forces a definitive domain classification too early, it may mislead later decisions.

**Mitigation:** explicitly support `uncertain` and low confidence.

### Risk 3 — Confusing escalation with issue creation
If `candidate_issue` is interpreted as “already an issue,” workflow may become noisy.

**Mitigation:** document the distinction clearly and keep issue promotion separate.

### Risk 4 — Overcomplicating the feedback system
This feature could drift toward full issue management.

**Mitigation:** focus on classification and follow-up signal quality only.

---

## 13. Recommended Implementation Order

1. define triage fields
2. define allowed values for domain, confidence, and escalation
3. implement triage update flow
4. improve list/show inspection with triage filters
5. integrate triage visibility into nightly review
6. document the triage model and boundaries

---

## 14. Suggested Validation Questions

This feature should make the system better able to answer:

- is this more likely a product issue or an async-dev issue?
- how certain is that judgment?
- does this item need future attention?
- should it merely be tracked, or should it later become a formal issue?
- which workflow feedback items are the most important to review?

If the operator still sees a flat pile of captured feedback with no useful prioritization or domain clarity, this feature is not done.

---

## 15. Definition of Done

Feature 019b is done when:

- captured workflow feedback can be triaged in a useful structured way
- async-dev vs product problem boundaries are clearer
- uncertainty is handled honestly
- the system can distinguish between low-value records and candidate follow-up items
- nightly review becomes more actionable because of triage

If captured workflow feedback still lacks meaningful domain judgment and follow-up signal, this feature is not done.
