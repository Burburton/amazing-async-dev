# Feature 008 — Completion & Archive Flow

## 1. Feature Summary

### Feature ID
`008-completion-and-archive-flow`

### Title
Completion & Archive Flow

### Goal
Extend `amazing-async-dev` from an active execution loop system into a fuller feature lifecycle system by defining how a feature is completed, archived, and turned into reusable development knowledge.

### Why this matters
The repository already supports the core active loop:

- define product and feature artifacts
- initialize project and feature structure
- plan the day
- run execution
- review at night
- resume the next day
- handle blocked, failed, and decision-needed states
- protect the main path with automated tests

What is still missing is a clear lifecycle ending.

Right now the system is strong at:
- moving work forward
- pausing and resuming
- handling execution states

But it is still weak at:
- knowing when a feature is truly done
- closing a feature cleanly
- preserving the final record of work
- extracting reusable lessons and patterns
- creating a reliable handoff into future work

This feature fills that gap.

---

## 2. Objective

Create the first completion and archive flow for `amazing-async-dev`, so that a feature can move from active execution into a stable archived state with explicit closeout artifacts.

This feature should make it possible to:

1. determine when a feature is ready for completion
2. explicitly mark a feature as completed
3. generate an archive artifact for long-term record keeping
4. preserve important outputs and decisions
5. extract useful lessons and reusable patterns
6. support a cleaner transition into future features

---

## 3. Scope

### In scope
- define feature completion criteria
- define a `complete-feature` action or command
- define an `ArchivePack` object
- define an `archive-feature` action or command
- capture final outputs, acceptance result, unresolved follow-ups, and decisions made
- capture lightweight lessons learned and reusable patterns
- define the archived state transition
- define file placement and directory conventions for archived features
- ensure archived features are no longer treated as active execution targets

### Out of scope
- full knowledge graph or advanced semantic search
- advanced analytics across many archived features
- dashboard visualization
- live API mode
- multi-project prioritization engine
- automated portfolio planning
- large-scale pattern mining across all archived work

---

## 4. Success Criteria

This feature is successful when:

1. a feature can be explicitly moved from active execution to completed
2. completed features can be archived in a consistent and inspectable way
3. an `ArchivePack` captures the essential closeout information
4. archived features stop participating in active day-loop execution
5. lessons learned and reusable patterns are preserved in a lightweight but useful way
6. a later contributor can understand what was delivered and what remains open

---

## 5. Core Design Principles

### 5.1 Completion must be explicit
A feature should not silently drift into a done state.

### 5.2 Archive must be artifact-based
Final state should be represented by explicit archive artifacts, not just directory moves or implicit conventions.

### 5.3 Keep closeout lightweight
Do not turn completion into heavy process overhead.  
It should be structured but still practical for a solo builder workflow.

### 5.4 Preserve future usefulness
Archive should not only record what happened; it should make future work easier.

### 5.5 Separate active state from historical state
Archived features should be clearly distinguishable from features still under active execution.

---

## 6. Main Capabilities

## 6.1 Completion criteria

### Purpose
Define when a feature is eligible to be completed.

### Expected conditions
At minimum, a feature should only be completable when:

- its acceptance criteria are marked satisfied or explicitly reviewed
- the required execution artifacts exist
- unresolved items are documented
- blocked items are either resolved or explicitly deferred
- decisions made during implementation are recorded
- the final status is no longer “actively executing”

### Notes
The first version does not need perfect automation.  
It does need a clear, inspectable rule set.

---

## 6.2 Complete-feature action

### Purpose
Provide an explicit transition from active lifecycle states into completed status.

### Suggested command
```bash
asyncdev complete-feature
```

### Responsibilities
- validate completion eligibility
- update `RunState` or equivalent final state marker
- record completion metadata
- prepare the feature for archiving

### Notes
This action should not yet be the full archive step.  
It is the completion boundary.

---

## 6.3 ArchivePack object

### Purpose
Represent the archived summary of a completed feature.

### Minimum fields
- `feature_id`
- `product_id`
- `title`
- `final_status`
- `delivered_outputs`
- `acceptance_result`
- `unresolved_followups`
- `decisions_made`
- `lessons_learned`
- `reusable_patterns`
- `artifact_links`
- `archived_at`

### Optional fields
- `implementation_summary`
- `risk_notes`
- `deferred_items`
- `related_features`
- `archive_version`

### Notes
`ArchivePack` should be a first-class object, not just an informal markdown note.

---

## 6.4 Archive-feature action

### Purpose
Move a completed feature into a stable archived state.

### Suggested command
```bash
asyncdev archive-feature
```

### Responsibilities
- generate `ArchivePack`
- store archive artifact at a stable location
- mark feature as archived
- ensure archived feature is no longer selected for active execution
- preserve links to relevant execution artifacts

### Notes
This should be a controlled state transition, not an informal cleanup step.

---

## 6.5 Lessons learned and reusable patterns

### Purpose
Preserve practical development insight from completed features.

### Expected capture areas
- what kind of `ExecutionPack` worked well
- what blockers occurred frequently
- what decisions were repeatedly needed
- what review patterns were effective
- what implementation or process practices should be reused

### Notes
Keep this lightweight in v1.  
Do not overbuild a complex knowledge extraction system yet.

---

## 7. State Model Expectations

This feature should make the lifecycle more explicit.

### Example high-level state progression
- `planning`
- `ready_for_execution`
- `executing`
- `blocked`
- `reviewing`
- `completed`
- `archived`

### Key rule
A feature in `archived` state must not be treated as an active candidate for:
- `plan-day`
- `run-day`
- `resume-next-day`

---

## 8. Directory and Artifact Placement

### Suggested active feature location
```text
projects/<product_id>/features/<feature_id>/
```

### Suggested archive artifact location
Possible first version approaches:

#### Option A
Keep feature directory in place and add archive artifact inside:
```text
projects/<product_id>/features/<feature_id>/archive-pack.yaml
```

#### Option B
Move or copy archival summary into a dedicated archive area:
```text
projects/<product_id>/archive/<feature_id>/archive-pack.yaml
```

### Recommendation for v1
Prefer a lightweight approach that minimizes movement complexity while preserving clear archived status.

The implementation can choose either approach, but it must be consistent and documented.

---

## 9. Deliverables

This feature must add:

### 9.1 Archive object definition
- `archive-pack` schema
- `archive-pack` template
- at least one example archive pack

### 9.2 Completion flow
- a documented completion rule set
- a completion action or command

### 9.3 Archive flow
- an archive action or command
- consistent archive output placement
- archived-state handling

### 9.4 Documentation
At least one document or section explaining:
- when a feature is considered complete
- how completion differs from archive
- what gets preserved
- how archived features interact with the rest of the system

---

## 10. Acceptance Criteria

- [ ] completion criteria are explicitly defined
- [ ] a feature can be marked completed through a clear action
- [ ] `ArchivePack` is defined as a first-class object
- [ ] `archive-feature` exists or equivalent archive action is implemented
- [ ] archive output is stored in a consistent place
- [ ] archived features are excluded from active execution selection
- [ ] lessons learned are captured in a lightweight structured form
- [ ] reusable patterns are captured in a lightweight structured form
- [ ] documentation explains the completion/archive lifecycle clearly

---

## 11. Risks

### Risk 1 — Making closeout too heavy
If archive becomes too bureaucratic, it will not be used consistently.

**Mitigation:** keep required closeout fields focused and practical.

### Risk 2 — Blurring completion and archive
If “completed” and “archived” are not distinct enough, lifecycle semantics will become unclear.

**Mitigation:** define a clear boundary between completion and archival.

### Risk 3 — Archive without future usefulness
If archive only stores a final status and no practical insight, it will not help future work.

**Mitigation:** include lessons learned and reusable patterns in the first version.

### Risk 4 — Archived work still acting as active work
If archived features remain visible to active planning flows, state confusion will grow.

**Mitigation:** enforce clear exclusion rules in active execution selection.

---

## 12. Recommended Implementation Order

1. define completion criteria
2. define `ArchivePack` schema/template/example
3. implement `complete-feature`
4. implement `archive-feature`
5. mark archived features clearly in state and storage
6. add lightweight lessons/pattern capture
7. document the completion/archive lifecycle
8. verify archived features are excluded from active execution paths

---

## 13. Suggested Archive Philosophy

The archive layer should answer these questions for every completed feature:

- what was this feature trying to achieve?
- what was actually delivered?
- was acceptance achieved?
- what is still unresolved?
- what important decisions were made?
- what should be reused next time?
- where are the important artifacts?

If the archive cannot answer those questions, it is not yet useful enough.

---

## 14. Definition of Done

Feature 008 is done when:

- a feature can be completed explicitly
- a completed feature can be archived explicitly
- an archive artifact captures final status, outputs, decisions, and lessons
- archived features are clearly separated from active execution flow
- the repository now supports both active execution and lifecycle closeout

If the system can still push work forward but cannot clearly finish and preserve a feature, this feature is not done.
