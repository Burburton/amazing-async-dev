# Feature 018 — Limited Batch Operations

## 1. Feature Summary

### Feature ID
`018-limited-batch-operations`

### Title
Limited Batch Operations

### Goal
Introduce a narrow, practical set of batch operations in `amazing-async-dev` to reduce repetitive operator effort without expanding into a full multi-feature execution system.

### Why this matters
`amazing-async-dev` now has a strong single-feature / single-product workflow foundation, including:

- artifact-first workflow
- execution and review loops
- completion and archive flow
- historical archive backfill
- archive query / history inspection
- nightly management summary
- decision template system
- archive-aware planning

At this stage, the next friction point is often not missing capability, but repeated manual operation across multiple features, archive entries, or products.

Typical friction now may include:
- checking many feature states one by one
- inspecting many archive entries individually
- backfilling historical items one by one
- producing repeated summaries manually
- navigating repetitive operator loops across a small set of related items

This feature exists to improve operational efficiency while staying within the current product philosophy.

---

## 2. Objective

Add a small, high-value set of batch operations that help operators work more efficiently across multiple features or archive records, while preserving the repository’s bounded and controlled workflow model.

This feature should make it easier to:

1. inspect multiple items at once
2. reduce repetitive command invocation
3. handle archive/history operations more efficiently
4. improve operator productivity for repeated maintenance tasks
5. prepare the system for broader portfolio use without jumping to concurrent execution

---

## 3. Scope

### In scope
- add a practical first set of batch-oriented commands or command modes
- support batch status inspection
- support batch archive inspection
- support batch historical archive backfill where appropriate
- support limited batch summary generation if clearly useful
- document the intended boundaries of batch operations

### Out of scope
- concurrent execution of many active features
- multi-feature autonomous orchestration
- multi-project scheduling engine
- full workflow queue manager
- distributed worker model
- large-scale portfolio planner
- broad bulk mutation without safeguards

---

## 4. Success Criteria

This feature is successful when:

1. repeated operator tasks can be performed more efficiently
2. batch capabilities remain bounded and understandable
3. the system reduces manual repetition without becoming overly complex
4. archive/history operations become easier to use at scale
5. batch operations improve real workflow ergonomics without destabilizing core semantics

---

## 5. Core Design Principles

### 5.1 Batch should reduce repetition, not increase execution risk
The first version should focus on read-heavy or low-risk operations.

### 5.2 Keep the scope deliberately narrow
Do not turn this into multi-feature parallel execution.

### 5.3 Prefer high-value operator workflows
Batch features should target common practical maintenance and inspection tasks.

### 5.4 Preserve explicitness
Even in batch mode, the operator should understand what the system is doing.

### 5.5 Favor safe operations first
Batch read, inspect, and summarize operations are safer than aggressive batch mutations.

---

## 6. Main Capability Areas

## 6.1 Batch status inspection

### Purpose
Allow operators to inspect the status of multiple features or products in one step.

### Expected support
- list multiple feature states
- inspect features by product
- inspect active/blocked/completed/archived distributions
- reduce the need to call single-item status repeatedly

### Notes
This is one of the highest-value first batch operations.

---

## 6.2 Batch archive inspection

### Purpose
Allow operators to inspect multiple archive records more efficiently.

### Expected support
- list multiple archive records with useful summary fields
- inspect recent archive activity
- inspect archive records with lessons or patterns
- inspect archive subsets by product

### Notes
This should build naturally on Feature 014.

---

## 6.3 Batch historical archive backfill

### Purpose
Allow operators to backfill more than one eligible historical feature without fully manual repetition.

### Expected support
- identify multiple eligible historical features
- run controlled backfill across a selected set
- clearly mark which records were backfilled
- preserve reviewability of batch archive outcomes

### Notes
This should remain safe and bounded.

---

## 6.4 Batch summary generation

### Purpose
Allow operators to generate summary views across a small set of features or archive entries.

### Possible examples
- daily or weekly summary across selected features
- summary of recent archive additions
- summary of blocked or unresolved items across a chosen product

### Notes
This should be introduced only if it is clearly useful and does not overexpand the feature.

---

## 7. CLI Expectations

The exact command shape may vary, but the first version should likely support bounded patterns such as:

```bash
asyncdev status --product <id> --all
asyncdev archive list --recent
asyncdev archive list --product <id> --has-patterns
asyncdev backfill --all
```

or equivalent small command extensions.

### Notes
The command set should remain coherent and not explode into many overlapping forms.

---

## 8. Safety Expectations

Batch behavior must remain safe and inspectable.

### Recommended first-step priorities
1. read / inspect batch operations
2. low-risk maintenance batch operations
3. only then controlled batch mutation flows

### Notes
The first version should avoid broad destructive or opaque batch actions.

---

## 9. Integration Expectations

This feature should integrate with:

- CLI status system
- archive query / history inspection
- historical archive backfill
- nightly/operator workflows where naturally helpful
- SQLite state/index support where useful

### Notes
This feature should make existing capabilities more efficient, not replace them.

---

## 10. Deliverables

This feature must add:

### 10.1 Batch status capability
A practical way to inspect multiple feature/product states in one operation.

### 10.2 Batch archive capability
A practical way to inspect multiple archive entries in one operation.

### 10.3 Batch backfill capability
A bounded way to backfill more than one historical feature where useful.

### 10.4 Documentation
At least one document or section explaining:
- what batch operations are supported
- which batch operations are intentionally not supported
- how to use them safely
- how they fit into the operator workflow

---

## 11. Acceptance Criteria

- [ ] multiple statuses can be inspected more efficiently
- [ ] multiple archive entries can be inspected more efficiently
- [ ] historical backfill can be run in a bounded batch mode where appropriate
- [ ] batch behavior remains explicit and understandable
- [ ] the feature reduces repetitive operator effort
- [ ] documentation explains batch boundaries clearly

---

## 12. Risks

### Risk 1 — Drifting into multi-feature orchestration
Batch capability could accidentally become a broad concurrent execution system.

**Mitigation:** keep the first version focused on inspection and safe maintenance workflows.

### Risk 2 — Overcomplicating the CLI
Too many batch options could reduce usability.

**Mitigation:** keep the command surface small and coherent.

### Risk 3 — Unsafe batch mutation
Bulk actions may become hard to inspect or reverse.

**Mitigation:** prioritize read and summary operations first, and keep mutation flows bounded.

### Risk 4 — Low actual value
Batch features may exist but not save real time.

**Mitigation:** focus only on repeated operator pain points already observed in practice.

---

## 13. Recommended Implementation Order

1. identify the highest-value repeated operator workflows
2. implement batch status inspection
3. implement batch archive inspection
4. implement controlled batch archive backfill if still needed
5. optionally add bounded batch summary generation
6. document supported batch patterns and safety rules

---

## 14. Suggested Validation Questions

This feature should make the system better able to answer:

- can I inspect many relevant items without repetitive command loops?
- can I review archive/history more efficiently?
- can I backfill historical archive records without one-by-one repetition?
- does the batch layer save time without adding confusion?
- does the system remain bounded and safe?

If batch usage still feels like repeated single-item command work with little improvement, this feature is not done.

---

## 15. Definition of Done

Feature 018 is done when:

- the system supports a small, useful set of bounded batch operations
- repetitive operator tasks are measurably easier
- archive/history workflows become more efficient at small scale
- the repository gains efficiency without drifting into uncontrolled multi-feature orchestration

If the operator still has to perform repetitive one-by-one flows for the most common maintenance and inspection tasks, this feature is not done.
