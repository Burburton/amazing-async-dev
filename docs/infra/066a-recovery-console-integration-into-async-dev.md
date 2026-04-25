# 066a — Recovery Console Integration into async-dev

## Metadata

- **Feature ID**: `066a-recovery-console-integration-into-async-dev`
- **Feature Name**: `Recovery Console Integration into async-dev`
- **Feature Type**: `integration / operator surface hardening / platform wiring`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Related Features**:
  - `063-execution-observer-foundation`
  - `066-execution-recovery-console`

---

## 1. Problem Statement

Feature 066 introduced the **Execution Recovery Console** as the first focused operator-facing product surface for async-dev platformization.

However, even if the Recovery Console UI/product surface exists, it is not truly useful unless it is integrated back into async-dev’s canonical runtime, state, and operator flows.

Without integration, the Recovery Console risks becoming only a partially useful side product:

- it may display mock or fragmented data rather than canonical async-dev state,
- it may not consume observer findings reliably,
- it may not trigger real recovery actions,
- it may not be reachable from the main async-dev operator flow,
- it may behave more like a viewer than a real operator console.

That leads to a platform gap:

> the Recovery Console may exist, but it is not yet fully part of async-dev.

This feature closes that gap by integrating the Recovery Console into async-dev in four core ways:

1. canonical data integration,
2. observer finding integration,
3. recovery action wiring,
4. platform entrypoint and documentation integration.

---

## 2. Goal

Make the Recovery Console a **real, usable operator surface inside async-dev**, not a disconnected product artifact.

After this feature, the Recovery Console should:

- read canonical async-dev recovery-relevant state,
- display real observer findings,
- surface real linked artifacts,
- trigger or prepare actual async-dev recovery actions,
- fit into the documented main operator workflow.

The result should be an operator surface that is both visible and operationally useful.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the Recovery Console product from scratch,
- replace the execution kernel,
- replace the observer foundation,
- introduce a giant platform shell,
- solve every operator-facing workflow in one integration step,
- fully redesign all artifact schemas unless a small canonicalization improvement is needed.

This feature is specifically about **wiring the Recovery Console into async-dev properly**.

---

## 4. Core Design Principle

### 4.1 Integration Over Isolation

The Recovery Console must consume async-dev’s canonical runtime truth rather than inventing its own parallel state model.

### 4.2 Actionability Over Display

A console that only shows recovery information is not enough. It must either:

- trigger real actions, or
- prepare precise actions that async-dev can consume directly.

### 4.3 Observer as First-Class Input

Feature 063 observer findings are a core input to recovery operations and should be treated as such inside the integrated console.

### 4.4 Minimize Split Source of Truth

The integration must avoid situations where:

- the runtime says one thing,
- artifacts say another thing,
- the console says a third thing.

The console should read from a canonical data adapter or service that reflects async-dev truth consistently.

---

## 5. Target Outcomes

After this feature is complete, the operator should be able to:

1. open the Recovery Console from an async-dev-supported entrypoint,
2. view real recovery-relevant executions from canonical state,
3. inspect real observer findings and artifact links,
4. understand the suggested next action,
5. trigger or concretely prepare a real recovery action,
6. trust that the console reflects async-dev’s actual current state.

The Recovery Console should no longer feel like a detached adjunct tool.

---

## 6. Required Functional Changes

### 6.1 Canonical Recovery Data Adapter

Introduce or formalize a canonical adapter/service layer that provides Recovery Console data from async-dev state.

This adapter should aggregate and normalize recovery-relevant inputs such as:

- run metadata,
- execution result,
- recovery state,
- verification state,
- closeout state,
- observer findings,
- artifact references.

The Recovery Console should use this adapter rather than reading many files directly in ad hoc UI code.

### 6.2 Observer Finding Integration

The integrated Recovery Console must consume Feature 063 outputs directly or through the canonical adapter.

The console should surface observer inputs such as:

- finding type,
- severity,
- summary,
- reason,
- recommended action,
- detection time,
- artifact references,
- recovery significance.

These findings should be first-class signals in list and detail views.

### 6.3 Recovery Action Wiring

The console must connect recovery actions back into async-dev.

At minimum, supported actions should include one or more of:

- `continue`
- `resume`
- `retry`
- `escalate`
- `inspect-artifacts`
- `open-related-result`
- `open-related-finding`

Depending on current architecture and safety constraints, action wiring may take one of these forms:

- direct invocation of async-dev commands,
- creation of structured action intent files,
- prepared exact commands for operator execution,
- dispatch through an internal action service.

The key requirement is that actions must be real and async-dev-aligned, not purely conceptual.

### 6.4 Platform Entry Integration

The Recovery Console must be reachable through an async-dev platform entrypoint or clearly documented operator flow.

Possible integrations include:

- CLI entrypoint that launches or opens the console,
- platform documentation / operator guide linking to it,
- local web app launcher,
- menu or route integration in an existing operator shell if one exists.

The operator should not have to guess how to access it.

### 6.5 Documentation Integration

Documentation must explain:

- what the Recovery Console is,
- how it consumes runtime truth and observer findings,
- what actions it can trigger,
- how it fits into async-dev’s operator workflow,
- when an operator should use it instead of manually reading artifacts.

### 6.6 State Alignment Review

As part of integration, the implementation must review whether a small amount of schema normalization or adapter normalization is needed to make:

- recovery reason,
- recovery category,
- suggested action,
- blocked status,
- artifact references

consistent enough for the console to be trustworthy.

This feature may improve canonicalization where necessary, but should avoid a broad schema rewrite unless absolutely needed.

---

## 7. Detailed Requirements

## 7.1 Canonical Data Sources

The integration should define which canonical sources feed the Recovery Console.

These may include:

- run state records,
- execution results,
- observer findings,
- artifact indexes,
- recovery summaries.

The spec/implementation must explicitly document the intended truth sources.

## 7.2 Recovery Item Integration Model

The integrated Recovery Console should expose a normalized recovery item model with fields such as:

- `run_id`
- `execution_id`
- `product_id`
- `title`
- `status`
- `recovery_required`
- `recovery_reason`
- `recovery_category`
- `suggested_action`
- `verification_status`
- `closeout_status`
- `observer_findings`
- `linked_artifacts`
- `last_updated_at`

This model should be built from canonical async-dev data.

## 7.3 Action Semantics

The integration must define what happens when an operator chooses an action.

Examples:

- `continue` -> invoke or prepare canonical continue flow
- `resume` -> invoke or prepare canonical resume flow
- `retry` -> invoke or prepare canonical retry flow
- `escalate` -> create or surface escalation intent
- `inspect-artifacts` -> resolve and open the right artifacts

The first version can choose direct invocation or prepared command flow, but the semantics must be clear and testable.

## 7.4 Error Handling

If canonical state is incomplete or a recovery action cannot be executed, the console must fail clearly rather than silently.

Examples:

- missing execution result,
- stale or unreadable finding record,
- unsupported action,
- inconsistent recovery state.

The console should surface actionable error messaging or fallback behavior.

## 7.5 Operator Workflow Integration

The integrated workflow should be recognizable and coherent.

Example operator path:

1. observer detects anomaly,
2. anomaly/finding is persisted,
3. Recovery Console lists the affected execution,
4. operator opens detail view,
5. operator selects recommended action,
6. async-dev executes or prepares the action.

This end-to-end path should be explicit in docs and design.

---

## 8. Expected File Changes

The exact file list may vary depending on repo structure, but implementation is expected to touch categories like the following.

### 8.1 Recovery Console Integration Code

Potential areas:

- recovery console data service / adapter
- observer finding integration layer
- action dispatcher / command preparation layer
- UI entrypoint wiring
- route/launcher integration

### 8.2 Existing Runtime / Platform Integration

Likely updates:

- execution artifact readers/indexers
- observer finding readers
- recovery state summarization helpers
- action dispatch / command helpers
- operator docs / README / platform guide
- platform entrypoint or launcher scripts

### 8.3 Documentation Updates

Must update documentation to reflect:

- how to access the Recovery Console,
- what data it reads,
- what actions it supports,
- how it fits into async-dev’s operator flow.

---

## 9. Acceptance Criteria

## AC-001 Canonical Data Integration Exists
The Recovery Console reads real async-dev canonical recovery-relevant data rather than isolated mock/demo data.

## AC-002 Observer Findings Are Integrated
Feature 063 observer findings appear inside the Recovery Console in a meaningful, usable way.

## AC-003 Action Wiring Exists
The console can trigger or concretely prepare at least a meaningful subset of real async-dev recovery actions.

## AC-004 Artifacts Are Properly Linked
The console can resolve and display useful artifact links from async-dev state.

## AC-005 Platform Entry Exists
There is a clear supported way to access the Recovery Console from the async-dev platform flow.

## AC-006 Documentation Is Updated
Operator documentation explains where the console fits and how to use it.

## AC-007 State Alignment Is Sufficient
Recovery-related fields are normalized enough that the console reflects trustworthy platform truth.

## AC-008 Errors Are Clear
Missing/inconsistent state and unsupported actions are surfaced clearly.

## AC-009 Tests Added
Automated tests cover data adaptation, observer integration, action wiring, and key failure handling paths.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Canonical Data Load
- Recovery Console loads recovery items from real async-dev state sources.

### 10.2 Observer Finding Display
- observer findings associated with an execution are surfaced correctly in the integrated console.

### 10.3 Suggested Action Rendering
- suggested action is preserved or computed correctly from integrated state.

### 10.4 Recovery Action Preparation / Trigger
- selecting a supported action produces the correct async-dev-aligned action output or trigger behavior.

### 10.5 Missing Artifact Handling
- when a linked artifact is missing or unreadable, the console fails clearly and predictably.

### 10.6 Inconsistent State Handling
- inconsistent recovery/verification/closeout state is surfaced clearly rather than silently hidden.

### 10.7 Platform Entrypoint Path
- the console can be reached through its intended integrated entry mechanism.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. define canonical recovery console adapter/service,
2. integrate observer findings,
3. wire artifact resolution,
4. wire recovery actions,
5. add platform entrypoint integration,
6. add tests,
7. update documentation.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- leaving the console on demo/mock data,
- keeping observer findings outside the console,
- providing buttons that do not map to real async-dev actions,
- duplicating runtime truth in the UI,
- requiring operators to still manually reconstruct everything from files,
- hiding integration gaps behind a polished interface.

## 11.3 Backward Compatibility

This integration should preserve the underlying Recovery Console concept and reuse existing runtime artifacts where possible.

Where normalization is needed, prefer adapter or summary-layer improvements unless a modest schema cleanup is clearly justified.

---

## 12. Risks and Mitigations

### Risk 1: Canonical state is too fragmented for a clean console feed
**Mitigation:** introduce a dedicated adapter/service layer rather than spreading aggregation into UI code.

### Risk 2: Action wiring is unsafe or incomplete
**Mitigation:** allow v1 to support a smaller set of real actions and use prepared commands/intents where direct invocation is not yet safe.

### Risk 3: Observer findings are noisy
**Mitigation:** summarize and prioritize findings in the adapter layer while preserving links to raw details.

### Risk 4: The console remains too passive
**Mitigation:** prioritize action wiring and suggested next actions over purely informational integration.

### Risk 5: Integration triggers schema churn
**Mitigation:** keep schema changes focused and justified; prefer normalization layers over broad rewrites.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- canonical data adapter/service for Recovery Console
- observer finding integration
- artifact link resolution integration
- recovery action wiring
- platform entrypoint integration
- updated operator documentation
- automated tests
- sufficient recovery state normalization for trustworthy rendering

---

## 14. Definition of Done

This feature is considered done only when:

1. the Recovery Console is reading real async-dev platform truth,
2. observer findings are visible and useful in the console,
3. operators can trigger or concretely prepare real recovery actions,
4. the console is reachable through an async-dev-supported flow,
5. the Recovery Console has transitioned from a standalone product surface into a real integrated async-dev capability.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as an integration-hardening feature,
- focus on platform wiring rather than redoing the console UI,
- prioritize canonical truth alignment and actionability,
- use observer outputs as first-class inputs,
- make the console genuinely usable inside async-dev.

Recommended planning questions:

- what are the exact canonical data sources?
- what adapter shape is needed for trustworthy recovery items?
- which recovery actions are safe and worthwhile in v1?
- what is the operator entrypoint path?
- what state normalization is required for clean rendering?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- what canonical sources feed the Recovery Console,
- how observer findings are integrated,
- what real recovery actions are supported,
- how the operator reaches the console from async-dev,
- how this changes the console from a detached viewer into an integrated operator capability.

It should not claim completion merely because the UI renders.

---

## 17. Summary

Feature 066a integrates the Recovery Console back into async-dev as a real operator capability.

It ensures that:

- the console reads canonical runtime truth,
- observer findings are visible,
- artifact links are meaningful,
- recovery actions are real,
- the console fits into the platform’s actual operator workflow.

In short:

> **066a turns the Recovery Console from “built” into “usable inside async-dev.”**
