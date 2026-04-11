# Feature 011 — Live API Mode Hardening

## 1. Feature Summary

### Feature ID
`011-live-api-mode-hardening`

### Title
Live API Mode Hardening

### Goal
Strengthen the existing Live API Mode in `amazing-async-dev` so it becomes a more reliable, inspectable, and operationally safe execution path alongside External Tool Mode.

### Why this matters
`amazing-async-dev` already has a meaningful execution system:

- artifact-first workflow
- day loop orchestration
- external tool mode
- completion and archive flow
- SQLite-backed state persistence
- execution logging and recovery hardening

At this point, Live API Mode should no longer be treated as a fragile side path or experimental capability.  
It should become a trustworthy execution option for bounded, real-world async development work.

The current risk is not the lack of an API connection.  
The current risk is that Live API Mode may still be weaker than External Tool Mode in areas such as:

- structured output reliability
- error classification
- observability during failure
- safe resume behavior after interruptions
- consistency with state persistence and lifecycle logic

This feature exists to make Live API Mode operationally dependable.

---

## 2. Objective

Harden Live API Mode so that it can be used confidently for real bounded execution tasks inside the `amazing-async-dev` workflow.

This feature should improve:

1. provider integration stability
2. structured `ExecutionResult` generation reliability
3. error and failure handling
4. integration with SQLite state and execution logging
5. safer recovery and resume behavior after API-driven execution

The goal is not to create a multi-provider platform.  
The goal is to make the current Live API path strong enough to be genuinely useful.

---

## 3. Scope

### In scope
- strengthen the current Live API execution path
- improve API request/response handling
- improve structured result parsing and validation
- improve Live API failure classification
- ensure proper integration with SQLite state and execution logs
- improve observability of API-triggered execution attempts
- improve resume/recovery semantics for API-driven runs
- document operational expectations for Live API Mode

### Out of scope
- adding many new providers
- building a large provider abstraction framework
- streaming UX
- dashboard work
- distributed execution
- advanced tool-calling ecosystems
- replacing External Tool Mode as the primary default
- large prompt-management framework redesign

---

## 4. Success Criteria

This feature is successful when:

1. Live API Mode can execute bounded tasks more reliably
2. `ExecutionResult` generation is more consistent and parseable
3. API failures are classified clearly
4. API-driven execution is logged and stateful in the same persistence model as the rest of the system
5. interrupted or failed Live API runs are easier to inspect and recover from
6. Live API Mode feels operationally trustworthy rather than experimental

---

## 5. Core Design Principles

### 5.1 Hardening over expansion
Do not widen scope into a provider platform.  
Make the existing path stronger first.

### 5.2 Structured outputs are mandatory
Live API Mode must remain strongly tied to `ExecutionResult` semantics.

### 5.3 Failures must become actionable
API failures should produce understandable next steps, not vague breakage.

### 5.4 Persistence and execution must align
Live API events, state changes, and recovery behavior should align with the SQLite-backed persistence model.

### 5.5 External Tool Mode remains a valid peer
This feature should strengthen Live API Mode without forcing it to replace External Tool Mode.

---

## 6. Main Capabilities

## 6.1 Live API request hardening

### Purpose
Make outbound API execution more stable and predictable.

### Expected improvements
- explicit provider configuration handling
- explicit model selection handling
- safer request construction
- clearer timeout/error boundaries
- more predictable behavior under malformed or partial responses

### Notes
The first focus should be the currently used provider path, not broad provider expansion.

---

## 6.2 Structured `ExecutionResult` reliability

### Purpose
Improve the consistency of turning model responses into valid `ExecutionResult` objects.

### Expected improvements
- stronger schema-aligned parsing
- clearer validation failures
- better handling of partial or malformed responses
- safer fallback behavior when output does not conform

### Notes
This is one of the most important parts of the feature.

---

## 6.3 Live API failure classification

### Purpose
Make Live API failures operationally meaningful instead of generic.

### Example failure classes
- authentication/configuration failure
- provider/network failure
- timeout
- malformed response
- response validation failure
- unsafe-to-resume execution failure
- partial result generated

### Notes
These classes do not need to be perfect, but they should be clear enough to support better recovery.

---

## 6.4 Logging and persistence integration

### Purpose
Ensure Live API Mode participates fully in the runtime persistence model.

### Expected logging examples
- API execution started
- request sent
- response received
- parse succeeded
- parse failed
- execution-result persisted
- API run failed
- recovery hint generated

### Notes
This must integrate with the execution logging and SQLite foundation already established.

---

## 6.5 Recovery-aware API execution

### Purpose
Improve how the system behaves after interrupted or failed Live API runs.

### Expected support
- distinguish retryable vs non-retryable failures
- identify whether a partial result can be preserved
- provide safer resume guidance
- avoid unsafe silent continuation after ambiguous API failure

### Notes
The goal is safer operational behavior, not aggressive auto-retry logic.

---

## 7. Operational Expectations

Live API Mode should work well for:

- bounded single-task execution
- structured result generation
- repository-internal execution paths
- low-friction automation for small real tasks

Live API Mode should not yet assume:

- large autonomous multi-step loops
- many provider strategies
- heavy tool ecosystems
- broad platform orchestration

---

## 8. Runtime Integration Expectations

This feature should integrate with:

- `runtime/orchestrator.py`
- `runtime/engines/live_api_engine.py`
- `runtime/adapters/llm_api_adapter.py`
- SQLite state persistence
- execution event logging
- resume/recovery logic
- `ExecutionResult` validation and storage

### Notes
This should strengthen the existing runtime shape rather than replace it.

---

## 9. Deliverables

This feature must add:

### 9.1 Hardened Live API execution path
A more reliable implementation of Live API execution.

### 9.2 Stronger structured result handling
Clearer parsing, validation, and failure behavior for `ExecutionResult`.

### 9.3 Better API failure semantics
Operationally useful error classification and handling.

### 9.4 Logging + persistence integration
Live API events and state updates recorded consistently in the repository’s persistence model.

### 9.5 Documentation
At least one document or section explaining:
- how Live API Mode should be used
- what kinds of failures exist
- how to recover after API-driven failure
- how Live API Mode fits alongside External Tool Mode

---

## 10. Acceptance Criteria

- [ ] Live API execution path is more reliable than the earlier version
- [ ] `ExecutionResult` parsing/validation is strengthened
- [ ] common API failure types are classified explicitly
- [ ] Live API runs are logged consistently
- [ ] Live API state changes are persisted consistently
- [ ] recovery behavior after API failures is clearer and safer
- [ ] Live API Mode is documented as a supported execution path

---

## 11. Risks

### Risk 1 — Over-expanding provider scope
Trying to support too many providers too early will slow hardening.

**Mitigation:** focus on the currently relevant provider path first.

### Risk 2 — Weak output validation
If structured parsing remains loose, the execution loop will stay fragile.

**Mitigation:** tighten `ExecutionResult` validation and define clearer fallback behavior.

### Risk 3 — Retry behavior becoming unsafe
Automatic retries without meaningful classification may worsen state corruption.

**Mitigation:** prefer explicit classification and conservative recovery guidance.

### Risk 4 — Live API and External Tool Mode drifting apart
If state, logging, and semantics diverge too much, the system becomes harder to reason about.

**Mitigation:** enforce shared execution semantics and shared persistence behavior.

---

## 12. Recommended Implementation Order

1. review the current Live API integration path
2. strengthen request construction and configuration handling
3. harden `ExecutionResult` parsing and validation
4. define API failure classes
5. integrate logging and persistence events for Live API runs
6. improve recovery guidance after API failures
7. document the operational model

---

## 13. Suggested Validation Questions

This feature should make the system better able to answer:

- did the API execution actually start?
- did the model return something usable?
- if parsing failed, why?
- is the failure retryable?
- did the system persist enough information to recover safely?
- should the user retry, resume, unblock, or stop?

If those questions still cannot be answered clearly, this feature is not done.

---

## 14. Definition of Done

Feature 011 is done when:

- Live API Mode is materially more reliable
- structured result generation is stronger
- API failures are more understandable
- API runs participate cleanly in logging and persistence
- recovery after API-driven interruption is safer and clearer

If Live API Mode still feels noticeably brittle compared with External Tool Mode, this feature is not done.
