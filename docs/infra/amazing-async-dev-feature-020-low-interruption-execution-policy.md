# Feature 020 — Low-Interruption Execution Policy / Autopilot Rules

## 1. Feature Summary

### Feature ID
`020-low-interruption-execution-policy`

### Title
Low-Interruption Execution Policy / Autopilot Rules

### Goal
Reduce unnecessary operator interruptions in `amazing-async-dev` by introducing a clear policy for which workflow transitions can proceed automatically and which situations must still pause for human confirmation.

### Why this matters
`amazing-async-dev` has been designed with explicit checkpoints across:
- planning
- execution
- review
- resume
- completion
- archive
- workflow feedback

That explicitness was useful during early system design and validation because it made state transitions visible and easy to inspect.

However, once the system is used in real product development, a new friction becomes obvious:

- too many normal workflow transitions still trigger operator prompts
- routine steps are treated like decisions
- the operator is repeatedly asked to confirm actions that should usually be automatic
- the system feels overly cautious instead of smoothly stateful

This weakens one of the original product goals:

- AI/tools should make progress during the day
- the human should return mainly for important decisions
- ordinary workflow continuation should not require constant approval

This feature exists to solve that problem.

---

## 2. Objective

Introduce a policy layer that distinguishes:

1. **normal workflow continuation**
2. **true decision points**
3. **risky external actions**
4. **blocked or uncertain states**

This feature should make it possible for `amazing-async-dev` to continue routine work automatically while still pausing for the right kinds of human intervention.

The result should be:
- fewer interruptions
- better operator trust
- smoother day-to-day execution
- clearer decision boundaries

---

## 3. Scope

### In scope
- define a low-interruption execution policy
- define which workflow transitions should default to automatic continuation
- define which situations require human confirmation
- define which actions are risky enough to require pause
- support operator-facing autopilot/interrupt policy behavior
- document the policy clearly
- improve workflow smoothness without removing important control points

### Out of scope
- full autonomous long-running daemon mode
- multi-feature concurrent scheduling
- automatic GitHub issue creation
- full external system automation
- advanced policy learning
- broad multi-user approval systems
- fully unattended long-horizon execution

---

## 4. Success Criteria

This feature is successful when:

1. ordinary safe workflow steps no longer interrupt the operator unnecessarily
2. the operator is asked only for meaningful decisions or risky actions
3. the system still pauses correctly when blockers, uncertainty, or high-impact actions appear
4. the workflow feels smoother and more production-usable
5. the day execution / night review model becomes more realistic in practice

---

## 5. Core Design Principles

### 5.1 Default to continuity for safe transitions
Normal state progression should not require unnecessary approval.

### 5.2 Preserve human judgment for true decisions
The system should still stop for:
- meaningful decisions
- blocker handling
- scope changes
- risky external actions

### 5.3 Be explicit about why a pause happens
The operator should understand why the system interrupted.

### 5.4 Keep policy understandable
This should not become a hidden black-box autonomy layer.

### 5.5 Optimize for reduced cognitive overhead
The operator should be interrupted less often, but with better quality.

---

## 6. Main Capabilities

## 6.1 Workflow continuation policy

### Purpose
Define which normal workflow transitions should proceed automatically.

### Example candidates for auto-continuation
- execution success → generate review artifact
- standard review artifact generation after successful execution
- move to next safe planning step when no blocker or decision is present
- ordinary non-destructive internal artifact creation

### Notes
The first version should keep this bounded and predictable.

---

## 6.2 Human-interrupt rules

### Purpose
Define which situations must interrupt the operator.

### Example cases that should still require pause
- `decisions_needed` is not empty
- unresolved blocker
- scope change
- unclear/unsafe next step
- risky external mutation such as GitHub push
- suspected workflow defect that may mislead future runs

### Notes
This is the most important boundary in the feature.

---

## 6.3 Risky action policy

### Purpose
Separate ordinary internal workflow steps from risky actions.

### Example risky actions
- pushing code to GitHub
- changing externally visible state
- destructive batch operations
- unsafe promotion/escalation actions
- irreversible archive-related operations where review is still needed

### Notes
The policy should treat these differently from safe internal transitions.

---

## 6.4 Interruption reason visibility

### Purpose
Make the reason for a pause clear and actionable.

### Expected support
When the system interrupts, it should clearly indicate:
- why it stopped
- whether the stop is due to a blocker, decision, risk, or policy boundary
- what must happen before continuation

### Notes
This is important for operator trust.

---

## 6.5 Optional policy mode setting

### Purpose
Allow a future-facing way to choose how conservative or smooth the system should be.

### Example initial modes
- `conservative`
- `balanced`
- `low-interruption`

### Notes
The first version does not need a very rich configuration surface, but a simple mode model may be useful.

---

## 7. Policy Model Expectations

The exact implementation may vary, but the policy layer should likely encode rules for:

### 7.1 Safe automatic continuation
Which transitions can proceed without asking

### 7.2 Mandatory pause conditions
Which conditions always require human review

### 7.3 Conditional pause conditions
Which situations may pause depending on selected policy mode

### Notes
The model must remain transparent and understandable.

---

## 8. Candidate Workflow Rules

The feature should likely formalize rules such as:

### Auto-continue
- execution finished successfully
- no unresolved blocker
- no active decision-needed item
- next step is safe and bounded
- no risky external side effect is pending

### Must pause
- true decision-required item exists
- blocker not resolved
- risky external action requested
- workflow feedback indicates possible async-dev defect requiring human review
- next step is unsafe or ambiguous

### Notes
These are guidance examples, not the final required wording.

---

## 9. Integration Expectations

This feature should integrate with:

- `RunState`
- nightly management summary
- `decisions_needed`
- blocker/recovery logic
- next-day recommendation
- workflow feedback system
- command execution flow
- external action handling

### Notes
This feature is a policy layer on top of the existing workflow engine, not a replacement of the engine.

---

## 10. CLI / Operator Experience Expectations

The system should provide clearer behavior such as:

- fewer unnecessary confirmation prompts
- clearer messages when a pause is required
- clearer indication of “safe to continue automatically”
- optional policy mode selection if implemented

### Example direction
The operator experience should move from:
- “checkpoint-heavy mode”
toward
- “low-interruption mode with explicit high-value pauses”

---

## 11. Deliverables

This feature must add:

### 11.1 Execution interruption policy
A clear rule set for what auto-continues vs what interrupts.

### 11.2 Pause reason model
A structured explanation of why the system paused.

### 11.3 Workflow integration
The policy integrated into the main execution/review/resume flow.

### 11.4 Documentation
At least one document or section explaining:
- when async-dev should continue automatically
- when it should interrupt
- which actions are considered risky
- how the policy supports the intended user workflow

---

## 12. Acceptance Criteria

- [ ] ordinary safe transitions interrupt the operator less often
- [ ] true decisions still cause pause
- [ ] blockers still cause pause
- [ ] risky external actions still require explicit confirmation
- [ ] interruption reasons are clearer
- [ ] workflow smoothness is improved without sacrificing important control

---

## 13. Risks

### Risk 1 — Over-automation
If the policy is too aggressive, the system may continue past points where human judgment is needed.

**Mitigation:** keep blocker/decision/risky-action pauses strict.

### Risk 2 — Hidden policy behavior
If the policy is too implicit, operators may lose trust.

**Mitigation:** show clear pause reasons and document the rules.

### Risk 3 — Not reducing enough friction
If the policy remains too conservative, the feature will not solve the core problem.

**Mitigation:** focus on removing interruptions from normal safe workflow transitions first.

### Risk 4 — Policy complexity explosion
Too many modes or exceptions may make the system harder to reason about.

**Mitigation:** start with a small number of simple policy rules.

---

## 14. Recommended Implementation Order

1. identify current interruption-heavy workflow points
2. define safe auto-continue cases
3. define mandatory pause cases
4. define risky-action pause rules
5. integrate interruption reasons into operator output
6. optionally add a simple policy mode
7. validate the new behavior in real product execution

---

## 15. Suggested Validation Questions

This feature should make the system better able to answer:

- why am I being interrupted right now?
- could this step have continued automatically?
- is this a real decision or just a routine transition?
- is this action risky enough to require my confirmation?
- can the system continue ordinary work without repeatedly asking me?

If the system still pauses on many routine safe transitions with little added value, this feature is not done.

---

## 16. Definition of Done

Feature 020 is done when:

- async-dev interrupts the operator less often for routine safe workflow steps
- true decision points and risky actions still require human review
- pause reasons are clear
- the system better supports a realistic day execution / night decision workflow

If routine work still feels overly checkpoint-heavy and the operator is asked for too many low-value confirmations, this feature is not done.
