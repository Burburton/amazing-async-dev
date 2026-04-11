# Feature 010 — Execution Logging & Recovery Hardening

## 1. Feature Summary

### Feature ID
`010-execution-logging-and-recovery-hardening`

### Title
Execution Logging & Recovery Hardening

### Goal
Strengthen `amazing-async-dev` by making execution history more inspectable and recovery from interruption, failure, or blocked work more reliable and explicit.

### Why this matters
`amazing-async-dev` now has:

- artifact-first workflow
- day loop orchestration
- external tool execution flow
- decision / blocker / failure handling
- completion and archive flow
- automated tests for the core workflow
- SQLite-backed state persistence

This means the system already has a meaningful operational backbone.

However, once the repository starts being used for real work over time, two practical weaknesses become more important:

1. **execution history is not yet rich enough**
2. **recovery behavior is not yet strong enough**

For real async development, the system should answer questions like:

- what exactly happened during the last execution cycle?
- where did the workflow stop?
- what failed, and why?
- what is safe to resume?
- what should happen next after interruption?

This feature exists to make the system more dependable in real use, not just in successful demo paths.

---

## 2. Objective

Improve the operational reliability of `amazing-async-dev` by adding stronger execution logging and more explicit, safer recovery behavior.

This feature should make it easier to:

1. inspect recent execution activity
2. understand the latest workflow stop point
3. distinguish normal pause, blocked state, and failure state
4. recover or resume work safely
5. reduce ambiguity in real-world interrupted workflows

---

## 3. Scope

### In scope
- improve structured logging of execution lifecycle events
- define what should be logged during key workflow actions
- improve recovery-oriented state inspection
- improve resume behavior after interruption, blocked state, or failure
- define recovery guidance rules
- strengthen consistency between runtime state, logs, and persisted DB state
- document recovery semantics and operational expectations

### Out of scope
- live API mode
- dashboard visualization
- distributed workers
- remote execution control
- advanced observability stack
- full event replay engine
- multi-user collaboration recovery logic

---

## 4. Success Criteria

This feature is successful when:

1. meaningful execution activity is stored in a structured and inspectable way
2. interrupted workflows are easier to diagnose
3. blocked and failed states are easier to distinguish and recover from
4. resume behavior is safer and more predictable
5. the system gives better guidance about what should happen next
6. the repository becomes more reliable for ongoing real-world usage

---

## 5. Core Design Principles

### 5.1 Logging should support action, not just history
Logs are not only for record keeping.  
They should help the user decide what to do next.

### 5.2 Recovery should be explicit
The system should not silently guess its way out of bad state.  
Recovery decisions should be inspectable and understandable.

### 5.3 Keep logging structured and lightweight
Do not overbuild a huge observability framework.  
The goal is practical workflow support.

### 5.4 Distinguish stop types clearly
Normal stop, blocked stop, and failed stop must remain meaningfully different.

### 5.5 Resume should be safe by default
When uncertain, the system should prefer explicit recovery guidance over unsafe automatic continuation.

---

## 6. Main Capabilities

## 6.1 Execution lifecycle logging

### Purpose
Record the important lifecycle actions that occur as a feature moves through the async development loop.

### Events to prioritize
- `plan-day-started`
- `plan-day-completed`
- `run-day-started`
- `run-day-dispatched`
- `external-execution-triggered`
- `execution-result-collected`
- `review-night-generated`
- `resume-next-day-started`
- `blocked-entered`
- `blocked-resolved`
- `failed-entered`
- `complete-feature`
- `archive-feature`

### Notes
The first version does not need exhaustive event coverage, but the main workflow path should become inspectable.

---

## 6.2 Stop-point visibility

### Purpose
Make it easy to determine where the workflow last stopped and under what condition.

### Expected visibility
The system should be able to answer:
- what was the last significant action?
- did the system stop normally, block, or fail?
- what artifact/result was last produced?
- is the workflow currently resumable?
- what follow-up is required before continuing?

### Notes
This should work through a combination of DB state, logs, and current artifact context.

---

## 6.3 Recovery classification

### Purpose
Clarify how different interruption scenarios should be treated.

### Recovery classes to distinguish
- **normal pause**
- **blocked**
- **failed**
- **awaiting decision**
- **ready to resume**
- **unsafe to resume**

### Notes
This classification should be used consistently in state inspection and resume guidance.

---

## 6.4 Safer resume behavior

### Purpose
Improve the logic behind resuming work after interruption.

### Expected behavior
Resume-related flows should:
- inspect persisted state and recent events
- determine whether resume is allowed
- explain when resume is unsafe
- distinguish between automatic continuation and explicit manual recovery
- guide the user toward the correct action when recovery is not straightforward

### Notes
This feature is about making resume safer, not making it magically automatic.

---

## 6.5 Recovery guidance

### Purpose
Provide better operational guidance when things stop unexpectedly.

### Example guidance questions
- should the user rerun `plan-day`?
- should the feature stay blocked?
- should the user use an unblock/resume command?
- should the workflow be marked failed?
- should the feature be completed or archived instead of resumed?

### Notes
The system does not need to become a decision engine.
It does need to produce clearer operational suggestions.

---

## 7. Logging Model Expectations

The exact logging format may vary, but the system should support structured records with fields such as:

- event type
- timestamp
- product ID
- feature ID
- run/execution context ID if available
- status/result classification
- short summary
- optional recovery hint
- optional artifact link/reference

### Notes
This should remain queryable and human-comprehensible.

---

## 8. Recovery Model Expectations

The system should define and document what recovery means in practice.

### Key cases
- resume after a normal end-of-day stop
- resume after blocked state has been resolved
- inspect and handle failed execution
- inspect missing or malformed execution result
- resume after completion is already reached
- prevent resume after archive

### Notes
Recovery behavior should be explicit and rule-based enough to be trusted.

---

## 9. Runtime Integration Expectations

This feature should integrate with:

- `state_store.py`
- SQLite event/history persistence
- `orchestrator.py`
- `resume-next-day`
- blocker/failure handling logic
- completion/archive transitions

### Notes
This should be an operational hardening layer, not a total rewrite.

---

## 10. Deliverables

This feature must add:

### 10.1 Structured execution logging
A practical structured logging layer for key workflow events.

### 10.2 Recovery-aware state inspection
The ability to inspect current and recent workflow state with recovery relevance.

### 10.3 Safer resume logic
Improved logic for deciding whether and how a workflow can be resumed.

### 10.4 Recovery guidance behavior
Clearer guidance when interruption or failure occurs.

### 10.5 Documentation
At least one document or section explaining:
- what gets logged
- how stop types are classified
- how recovery works
- what users should do in common recovery cases

---

## 11. Acceptance Criteria

- [ ] meaningful workflow events are stored in a structured way
- [ ] stop points are easier to inspect
- [ ] blocked, failed, and paused states are clearly distinguishable
- [ ] resume behavior is safer and more explicit
- [ ] recovery guidance is available for common interruption cases
- [ ] logging/recovery expectations are documented
- [ ] the feature improves practical trust in long-running real usage

---

## 12. Risks

### Risk 1 — Turning logs into noise
Too many low-value events may reduce usefulness.

**Mitigation:** log important lifecycle events first and keep them structured.

### Risk 2 — Unsafe recovery assumptions
If resume logic becomes too optimistic, it may continue from a bad state.

**Mitigation:** prefer conservative resume rules and explicit guidance.

### Risk 3 — Confusing multiple stop types
If blocked, failed, and paused are not clearly separated, users will not trust recovery behavior.

**Mitigation:** define explicit stop classifications and use them consistently.

### Risk 4 — Overbuilding a monitoring system
The feature could drift into observability complexity.

**Mitigation:** keep focus on workflow reliability, not monitoring sophistication.

---

## 13. Recommended Implementation Order

1. define execution event categories
2. persist meaningful workflow events
3. add stop-point inspection logic
4. classify recovery states explicitly
5. harden `resume-next-day` and related recovery flows
6. add recovery guidance behavior
7. document operational recovery semantics

---

## 14. Suggested Operational Questions

This feature should make the system better at answering:

- what just happened?
- where did the workflow stop?
- is it safe to continue?
- what must be fixed before continuing?
- should the user resume, unblock, retry, or stop?

If the system still cannot answer those questions clearly, this feature is not done.

---

## 15. Definition of Done

Feature 010 is done when:

- execution history is more structured and inspectable
- stop conditions and stop reasons are clearer
- recovery paths are safer and more explicit
- resume behavior is more trustworthy
- real-world interruptions are easier to handle without confusion

If workflow interruption still leaves the user unsure what happened or what to do next, this feature is not done.
