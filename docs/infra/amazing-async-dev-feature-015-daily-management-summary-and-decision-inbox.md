# Feature 015 — Daily Management Summary / Decision Inbox

## 1. Feature Summary

### Feature ID
`015-daily-management-summary-and-decision-inbox`

### Title
Daily Management Summary / Decision Inbox

### Goal
Strengthen the nightly review layer in `amazing-async-dev` so that the operator can quickly understand what happened during the day, what problems occurred, what was resolved, what still requires attention, and what decisions must be made before the next day-run.

### Why this matters
`amazing-async-dev` already has strong workflow foundations:

- artifact-first execution
- day loop orchestration
- external tool mode
- live API mode hardening
- blocker / failure / decision handling
- completion and archive flow
- SQLite-backed persistence
- execution logging and recovery hardening
- archive query/history inspection

This means the system already contains many of the raw signals needed for effective nightly review.

However, those signals may still be distributed across:
- `ExecutionResult`
- `RunState`
- event logs
- recovery hints
- archive metadata
- next-step recommendations

For real use, the operator should not need to reconstruct the day manually from many objects.

The system should instead make it easy to answer, at night:

- what was done today?
- what went wrong?
- what was already resolved?
- what is still unresolved?
- what do I need to decide?
- what should tomorrow’s day-run do next?

This feature exists to turn existing workflow data into a practical nightly management layer.

---

## 2. Objective

Create a stronger management-oriented nightly summary and decision inbox so that `amazing-async-dev` better supports the user’s real async operating model:

- AI/tools make progress during the day
- the human reviews at night
- the human makes only the necessary high-value decisions
- the system can continue the next day with minimal re-contextualization

This feature should make nightly review:

1. faster
2. clearer
3. more actionable
4. more decision-focused
5. less cognitively heavy

---

## 3. Scope

### In scope
- improve the nightly summary layer
- aggregate today’s execution outcomes into a clearer management view
- explicitly surface unresolved issues and risk points
- explicitly surface decision-needed items in a cleaner inbox format
- improve the clarity of next-day recommendations
- improve the usability of nightly review artifacts
- define or strengthen a dedicated nightly management artifact if needed
- document the intended nightly operator workflow

### Out of scope
- full dashboard UI
- multi-project portfolio management
- semantic summarization across the full repository
- major redesign of archive/history structures
- replacing current execution/result objects
- fully automated decision-making by the system

---

## 4. Success Criteria

This feature is successful when:

1. the operator can understand the day’s outcomes quickly
2. unresolved issues are easier to identify
3. decision-needed items are clearer and easier to act on
4. next-day recommendations are more actionable
5. nightly review requires less manual reconstruction of context
6. the system better supports the intended “day execution / night review” operating model

---

## 5. Core Design Principles

### 5.1 Optimize for nightly management, not raw data completeness
The operator needs a useful management layer, not every underlying detail at once.

### 5.2 Surface action, not just information
The nightly summary should help the operator know what to do next.

### 5.3 Distinguish resolved from unresolved
The system should clearly separate:
- problems encountered
- problems already handled
- problems still requiring attention

### 5.4 Make decision load explicit and small
Decision items should be visible, structured, and limited to meaningful judgment calls.

### 5.5 Support the next day-run directly
The nightly layer should naturally feed the next day’s continuation.

---

## 6. Main Capabilities

## 6.1 Daily outcome summary

### Purpose
Provide a concise but useful summary of what actually happened during the day.

### Expected content
- original day goal
- what was completed
- which artifacts were produced
- what changed meaningfully
- whether the day-run was successful, partial, blocked, or failed

### Notes
This should feel like a management summary, not a raw dump of logs.

---

## 6.2 Issue / problem summary

### Purpose
Summarize the important problems that occurred during the day.

### Expected distinctions
- issues encountered
- issues resolved during the day
- issues still unresolved
- blocked items
- risk items that are not blocked yet but may matter soon

### Notes
This should prevent the operator from needing to infer issue status from multiple artifacts.

---

## 6.3 Decision inbox

### Purpose
Make decision-required items visible and easy to process.

### Expected content
- explicit decision items
- the question to be answered
- available options
- recommendation if available
- reason for the recommendation
- impact of deferring the decision

### Notes
The inbox should highlight only meaningful human decisions, not every implementation detail.

---

## 6.4 Next-day recommendation

### Purpose
Provide a practical answer to: “What should tomorrow’s day-run do next?”

### Expected content
- recommended next action
- required preconditions
- whether a decision is blocking tomorrow’s progress
- whether the next step is safe to execute
- whether the next step should be deferred or changed

### Notes
This is one of the highest-value outputs for the real operator workflow.

---

## 6.5 Nightly management artifact

### Purpose
Represent the management-facing nightly review in a more usable artifact form.

### Possible forms
- strengthen the existing `DailyReviewPack`
- introduce a new `DailyManagementPack`
- produce both machine-structured and human-readable forms

### Recommendation
Preserve structured data while ensuring the nightly artifact is easy to read at a glance.

### Notes
This feature does not need to replace all current objects.
It should strengthen the operator-facing nightly layer.

---

## 7. Content Model Expectations

The nightly management layer should be able to express at least these categories:

- today’s goal
- what was completed
- what artifacts exist
- what issues occurred
- what was resolved
- what remains unresolved
- what is blocked
- what decisions are needed
- what is recommended next
- what may become risky soon

### Notes
The exact object format may evolve, but the nightly management view should cover all of these.

---

## 8. Integration Expectations

This feature should integrate with existing repository elements such as:

- `ExecutionResult`
- `RunState`
- event logs
- recovery guidance
- `decisions_needed`
- `next_recommended_action`
- review-night flow
- resume-next-day flow

### Notes
This is a refinement and aggregation layer, not a replacement of the current execution system.

---

## 9. Deliverables

This feature must add:

### 9.1 Stronger nightly summary output
A clearer management-facing nightly summary artifact or view.

### 9.2 Decision inbox capability
A clearer way to present and inspect decision-needed items during nightly review.

### 9.3 Better unresolved/resolved issue clarity
A more explicit distinction between handled issues and remaining issues.

### 9.4 Better next-day recommendation visibility
A more operator-friendly next-step recommendation layer.

### 9.5 Documentation
At least one document or section explaining:
- how nightly management review works
- what the operator should look at
- how decisions are surfaced
- how the nightly layer supports the next day-run

---

## 10. Acceptance Criteria

- [ ] nightly review output is easier to understand
- [ ] completed work is summarized clearly
- [ ] unresolved issues are surfaced clearly
- [ ] resolved vs unresolved problems are distinguishable
- [ ] decision-needed items are clearer and more actionable
- [ ] next-day recommendations are more explicit
- [ ] the nightly layer better matches the intended operator workflow
- [ ] documentation explains the nightly management flow clearly

---

## 11. Risks

### Risk 1 — Repeating existing artifacts without improving usability
The feature may merely repackage existing fields without reducing cognitive load.

**Mitigation:** prioritize operator comprehension and actionability.

### Risk 2 — Too much detail in the nightly view
If the nightly artifact becomes too verbose, it will not help quick review.

**Mitigation:** emphasize summary and action layers, not full raw detail.

### Risk 3 — Decision overload
If too many low-value decisions are surfaced, the system will not reduce operator burden.

**Mitigation:** focus on meaningful decisions only.

### Risk 4 — Weak next-step guidance
If the system summarizes well but still does not make tomorrow’s next move clear, the feature underdelivers.

**Mitigation:** make next-day recommendation a first-class output.

---

## 12. Recommended Implementation Order

1. identify the current nightly review friction points
2. define the improved nightly management content model
3. strengthen summary of completed work
4. strengthen issue/resolution summary
5. strengthen decision inbox presentation
6. strengthen next-day recommendation visibility
7. update nightly workflow documentation
8. validate with real nightly review usage

---

## 13. Suggested Validation Questions

This feature should make the system better able to answer:

- what did the system accomplish today?
- what went wrong today?
- which problems were already handled?
- which problems still need attention?
- what exactly do I need to decide tonight?
- what should tomorrow’s day-run do next?

If the operator still has to reconstruct those answers manually from multiple artifacts, this feature is not done.

---

## 14. Definition of Done

Feature 015 is done when:

- nightly review feels more like a real management summary
- the decision inbox is clearer and more useful
- issue/resolution status is easier to understand
- the next day-run is easier to plan from the nightly view
- the system better fulfills its intended “day execution / night decision” operating model

If the operator still returns at night and has to manually piece together what happened and what to do next, this feature is not done.
