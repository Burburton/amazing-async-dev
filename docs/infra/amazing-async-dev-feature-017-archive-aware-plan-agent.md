# Feature 017 — Archive-aware Plan Agent

## 1. Feature Summary

### Feature ID
`017-archive-aware-plan-agent`

### Title
Archive-aware Plan Agent

### Goal
Improve `plan-day` so it can use archive history, reusable patterns, lessons learned, blocker context, and structured decision outcomes to generate better next-day planning recommendations.

### Why this matters
`amazing-async-dev` now has a strong operational foundation:

- artifact-first workflow
- day loop orchestration
- external tool mode
- live API mode hardening
- completion and archive flow
- historical archive backfill
- archive query / history inspection
- daily management summary
- decision template system

This means the system no longer lacks raw planning inputs.

It now has access to:
- current runtime state
- recent execution history
- blocked/failed/recovery context
- nightly decision outcomes
- archive lessons learned
- reusable patterns from prior features

However, `plan-day` may still behave too narrowly if it only looks at current state and immediate next-step fields.

This feature exists to improve planning quality by making planning:
- history-aware
- decision-aware
- blocker-aware
- pattern-aware

---

## 2. Objective

Strengthen the planning layer in `amazing-async-dev` so that `plan-day` can generate better bounded day-run proposals by incorporating archive and decision context instead of relying only on local current-state heuristics.

This feature should make it easier to:

1. choose a better next task for the day
2. avoid repeating known mistakes
3. reuse proven patterns from historical work
4. account for unresolved decisions and blockers
5. produce more trustworthy next-day recommendations

---

## 3. Scope

### In scope
- improve `plan-day` logic using archive/history data
- incorporate lessons learned and reusable patterns into planning
- incorporate decision template outcomes into planning
- incorporate blocker and recovery context into planning
- improve next-day proposal quality and explainability
- document how archive-aware planning works

### Out of scope
- full autonomous planning engine
- multi-feature concurrent scheduling
- multi-project portfolio planning
- semantic retrieval or embedding-based search
- dashboard UI
- large agent framework redesign
- replacing the existing workflow model

---

## 4. Success Criteria

This feature is successful when:

1. `plan-day` produces better next-day recommendations than before
2. planning can incorporate relevant archive lessons and reusable patterns
3. planning can account for unresolved or recently resolved decisions
4. planning can account for blocker and recovery context
5. planning output is more explainable and more trustworthy
6. the operator has to do less manual reasoning to choose the next day-run

---

## 5. Core Design Principles

### 5.1 Planning should remain bounded
This feature should improve next-day proposals, not turn planning into unconstrained autonomous orchestration.

### 5.2 Reuse history where it matters
Archive data should be used when it can materially improve planning quality, not just because it exists.

### 5.3 Respect current execution reality
Planning must remain grounded in current state, current blockers, and current decisions.

### 5.4 Explain why a recommendation is made
A better recommendation is more useful when the operator can understand why it was proposed.

### 5.5 Improve trust, not complexity
This feature should make `plan-day` feel smarter and more reliable without becoming opaque or over-engineered.

---

## 6. Main Capabilities

## 6.1 Archive-aware planning

### Purpose
Allow planning to use historical archive information when proposing the next day-run.

### Expected use of archive
- lessons learned from similar completed features
- reusable patterns from archived work
- prior completion outcomes
- previously successful task shapes

### Notes
The first version should stay practical and structured.
Do not attempt full semantic similarity planning.

---

## 6.2 Decision-aware planning

### Purpose
Allow planning to incorporate nightly decision outcomes and decision template structure.

### Expected support
- understand which decisions remain unresolved
- understand which decisions block tomorrow’s work
- prefer next actions that are safe to execute
- avoid proposing work that conflicts with pending decision constraints

### Notes
This is especially important after Feature 015 and Feature 016.

---

## 6.3 Blocker-aware planning

### Purpose
Improve planning around blocked and recently recovered work.

### Expected behavior
- do not propose clearly blocked work as the main next task
- recognize when a blocker has been cleared
- suggest alternative bounded work when direct continuation is unsafe
- incorporate recovery context into planning recommendations

### Notes
Planning should become more robust in real interrupted workflows.

---

## 6.4 Better next-day recommendation output

### Purpose
Improve the output quality of `plan-day`.

### Expected output qualities
- clearer recommended action
- relevant preconditions
- rationale for recommendation
- indication of reused lesson or pattern where relevant
- safer understanding of whether the task is ready to execute

### Notes
This should align well with the nightly management summary and next-day recommendation structures already introduced.

---

## 6.5 Planning explainability

### Purpose
Make it clear why a particular next-day task was proposed.

### Expected explanation components
- which current-state factors matter
- which unresolved decisions matter
- which blocker/recovery signals matter
- which archive lesson or reusable pattern influenced the recommendation

### Notes
Explainability is important for trust in a planning layer.

---

## 7. Input Expectations

The planning layer should be able to use a combination of:

- current `RunState`
- recent execution events
- current blocker/failure/recovery status
- decision inbox state
- structured decision template outcomes
- archive records
- lessons learned
- reusable patterns

### Notes
The first version should stay selective and practical.
Not all available information must be used equally.

---

## 8. Output Expectations

`plan-day` should still produce a bounded, practical day-run proposal.

### Expected output components
- recommended next action
- preconditions
- safe-to-execute status
- blocker/decision constraints
- rationale
- estimated scope (`half-day` / `full-day` if still used)
- optional references to relevant archive lesson or pattern

### Notes
The output should remain operational, not overly theoretical.

---

## 9. Integration Expectations

This feature should integrate with:

- `plan-day`
- `RunState`
- execution logging/history
- blocker/recovery logic
- decision template system
- archive query/history inspection
- nightly summary / next-day recommendation logic

### Notes
This is a planning refinement layer, not a replacement for the execution engine.

---

## 10. Deliverables

This feature must add:

### 10.1 Archive-aware planning logic
A practical planning improvement that uses archive/history signals.

### 10.2 Decision-aware planning integration
Use of decision template outcomes and decision blockers in planning.

### 10.3 Blocker-aware planning refinement
Safer handling of blocked and recently recovered work in planning proposals.

### 10.4 Better planning output
A more explainable and trustworthy next-day proposal.

### 10.5 Documentation
At least one document or section explaining:
- what archive-aware planning means
- what signals are used
- how recommendation rationale is formed
- how this improves `plan-day`

---

## 11. Acceptance Criteria

- [ ] `plan-day` can use archive lessons/patterns in planning
- [ ] planning can account for unresolved decision constraints
- [ ] planning can account for blocker/recovery context
- [ ] next-day recommendation becomes more explainable
- [ ] planning output remains bounded and actionable
- [ ] documentation explains archive-aware planning clearly

---

## 12. Risks

### Risk 1 — Overusing archive data
If planning uses too much weakly relevant history, recommendations may become noisy or misleading.

**Mitigation:** keep history use selective and practical.

### Risk 2 — Planning opacity
If planning becomes smarter but less understandable, operator trust will fall.

**Mitigation:** include explicit rationale and recommendation explanation.

### Risk 3 — Hidden complexity
This feature could drift into a much larger planning-agent architecture.

**Mitigation:** keep the scope limited to improving `plan-day`.

### Risk 4 — Conflict between current state and historical patterns
Historical patterns may not fit current constraints.

**Mitigation:** current blocker/decision state must always take precedence over historical suggestions.

---

## 13. Recommended Implementation Order

1. define which archive signals are useful for planning
2. define which decision signals matter most for planning
3. define blocker/recovery planning rules
4. integrate archive and decision signals into `plan-day`
5. improve next-day recommendation rationale output
6. document the planning logic and intended use

---

## 14. Suggested Validation Questions

This feature should make the system better able to answer:

- what should tomorrow’s day-run do?
- why is that the best next step?
- what prior lesson or pattern supports this choice?
- is a pending decision blocking this plan?
- is a blocker still preventing this plan?
- is the proposed next step safe and bounded?

If `plan-day` still proposes the next action without meaningful awareness of archive, decisions, and blockers, this feature is not done.

---

## 15. Definition of Done

Feature 017 is done when:

- `plan-day` makes better use of archive and decision history
- next-day recommendations are more grounded and explainable
- blocker/recovery context is handled more intelligently
- the operator needs less manual reasoning to choose the next day-run

If planning still feels like a purely local next-step guess with little memory of past outcomes or current decision context, this feature is not done.
