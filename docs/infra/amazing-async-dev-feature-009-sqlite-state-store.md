# Feature 009 — SQLite State Store

## 1. Feature Summary

### Feature ID
`009-sqlite-state-store`

### Title
SQLite State Store

### Goal
Introduce a lightweight SQLite-backed persistence layer for `amazing-async-dev` so the system can store workflow state, execution history, and lifecycle transitions more reliably than file-only storage.

### Why this matters
At the end of v0, `amazing-async-dev` has already achieved its core workflow goals:

- artifact-first workflow
- day-sized execution
- state-based resume
- nightly review packs
- failure / blocker / decision handling
- completion and archive flow
- validated test coverage for the main paths

This means the system is no longer only a proof of concept.  
It is ready for a stronger persistence foundation.

The current file-based approach is useful and should remain important for human-readable artifacts, but it is weak in areas such as:

- tracking the latest canonical state across many transitions
- recording execution history over time
- querying recent activity
- recovering from failed or interrupted execution
- maintaining stable state semantics as the repository grows

SQLite is the next appropriate step because it provides:
- local persistence
- low operational complexity
- structured querying
- enough durability for a solo async development workflow

---

## 2. Objective

Create the first SQLite-based persistence layer for `amazing-async-dev` that can support:

1. stable storage of current workflow state
2. execution history logging
3. lifecycle transition history
4. better failure recovery support
5. future evolution toward richer runtime capabilities

This feature should strengthen the system without replacing the artifact-first philosophy.

The repository should continue to use human-readable artifacts such as:
- `FeatureSpec`
- `ExecutionPack`
- `ExecutionResult`
- `DailyReviewPack`
- `ArchivePack`

SQLite should serve as the structured persistence backbone for state and event history.

---

## 3. Scope

### In scope
- introduce SQLite as a local persistence backend
- define the minimum data model for state and execution history
- add a repository-level database file strategy
- persist current feature/run state in SQLite
- log execution events and lifecycle transitions
- support reading the latest state from SQLite
- support basic failure recovery using stored state
- integrate SQLite storage into the current runtime/state layer
- document how file artifacts and SQLite state coexist

### Out of scope
- replacing all artifact files with database rows
- remote database support
- multi-user concurrency
- dashboard visualization
- advanced analytics
- full audit/event sourcing system
- cross-machine synchronization
- large migration framework
- live API mode implementation

---

## 4. Success Criteria

This feature is successful when:

1. the repository can persist current workflow state in SQLite
2. execution and lifecycle events are stored in SQLite
3. the system can reconstruct the latest state from the database
4. file artifacts and DB state have a clear coexistence model
5. interrupted or failed workflows are easier to inspect and recover
6. the persistence layer is lightweight and does not overcomplicate the repository

---

## 5. Core Design Principles

### 5.1 SQLite is a persistence backbone, not the whole system
Artifacts remain first-class.  
The database strengthens state management but does not replace readable project files.

### 5.2 Keep the schema minimal
Only store what is needed for state, history, and recovery.  
Avoid premature normalization or large schema sprawl.

### 5.3 Preserve inspectability
A user should still be able to understand repository work through artifacts.  
SQLite should improve reliability, not hide the system.

### 5.4 Prefer append-friendly history
Execution and transition history should be easy to record over time.

### 5.5 Make recovery practical
The database should help answer:
- what was the latest known state?
- what happened last?
- why did execution stop?
- what is safe to resume?

---

## 6. Main Capabilities

## 6.1 Current state persistence

### Purpose
Store the current known workflow state in SQLite so the system has a reliable structured source for active runtime state.

### Examples of state to persist
- product identifier
- feature identifier
- current phase
- active task
- blocked status
- decision-needed presence
- completion/archive markers
- timestamps for last update

### Notes
This should support the repository’s existing `RunState` behavior, not compete with it.

---

## 6.2 Execution history logging

### Purpose
Store a chronological history of meaningful execution events.

### Example events
- `init`
- `new-product`
- `new-feature`
- `plan-day`
- `run-day`
- `blocked`
- `resume`
- `complete-feature`
- `archive-feature`

### Notes
This does not need to become a full event-sourcing model in v1.  
A useful event log is enough.

---

## 6.3 Lifecycle transition history

### Purpose
Track important state transitions over time.

### Example transitions
- `planning` → `ready_for_execution`
- `ready_for_execution` → `executing`
- `executing` → `blocked`
- `blocked` → `executing`
- `executing` → `reviewing`
- `reviewing` → `completed`
- `completed` → `archived`

### Notes
This should make state transitions more inspectable and easier to debug.

---

## 6.4 Failure recovery support

### Purpose
Make it easier to recover from interrupted or failed work.

### Expected support
- inspect the last known state
- inspect recent events
- determine the last action taken
- identify whether the system stopped in blocked/failed/executing state
- support safer resume logic

### Notes
Do not overbuild a full recovery orchestration engine yet.  
The goal is first to make recovery observable and practical.

---

## 7. Data Model Expectations

The exact schema may vary, but the first version should likely contain tables equivalent to:

### 7.1 products
Stores product-level identity and metadata references.

### 7.2 features
Stores feature-level identity and lifecycle status.

### 7.3 runstate_snapshots
Stores the latest structured runtime state, or versioned snapshots if needed.

### 7.4 execution_events
Stores chronological event records for actions and transitions.

### 7.5 archive_records
Stores archive metadata or archive references for completed features.

### Notes
The implementation may combine or simplify some tables, but the repository should support:
- current state lookup
- event history lookup
- archive-related lookup

---

## 8. Coexistence Model: Files vs SQLite

This feature must define the relationship between file artifacts and SQLite.

### Recommended v1 philosophy
- file artifacts remain the human-readable workflow objects
- SQLite stores structured runtime and history information
- artifacts continue to be used by tools and users
- SQLite becomes the structured persistence layer for state and events

### Example split
**Files**
- `feature-spec.yaml`
- `execution-pack.yaml`
- `execution-pack.md`
- `execution-result.md`
- `daily-review-pack.md`
- `archive-pack.yaml`

**SQLite**
- current feature status
- latest run state metadata
- event history
- transition history
- archive metadata/index

### Notes
This distinction must be documented clearly to avoid confusion.

---

## 9. Runtime Integration Expectations

This feature should integrate with the existing runtime/state layer.

### Expected touchpoints
- `state_store.py`
- `orchestrator.py`
- completion/archive handling
- resume logic
- result collection or execution event recording

### Notes
The integration should be incremental and should not force a total rewrite of the repository.

---

## 10. Database File Strategy

The feature should define a clear local DB location.

### Candidate approach
A repository-local SQLite file, for example:
```text
.runtime/amazing_async_dev.db
```

or another clearly documented path.

### Requirements
- stable location
- easy to ignore or include intentionally
- well documented
- not confused with project artifact paths

---

## 11. Deliverables

This feature must add:

### 11.1 SQLite-backed state store implementation
A working SQLite persistence module integrated into the repository.

### 11.2 Initial schema
A documented initial SQLite schema or schema initialization mechanism.

### 11.3 State + event persistence
Support for writing and reading current state and recent events.

### 11.4 Recovery-oriented query support
The ability to inspect latest state and recent event history for a feature.

### 11.5 Documentation
At least one document or section explaining:
- what goes into SQLite
- what remains in files
- where the DB lives
- how the persistence model supports resume and recovery

---

## 12. Acceptance Criteria

- [ ] SQLite is introduced as a working repository persistence layer
- [ ] current workflow state can be stored and read from SQLite
- [ ] execution events can be stored and queried
- [ ] lifecycle transitions are recorded in a structured way
- [ ] interrupted/failed state is easier to inspect through stored data
- [ ] file artifacts and SQLite have clearly separated responsibilities
- [ ] database location and usage are documented
- [ ] the implementation remains lightweight and practical

---

## 13. Risks

### Risk 1 — Overbuilding the data layer
A too-complex schema would slow down the project.

**Mitigation:** keep the first schema intentionally small and practical.

### Risk 2 — Creating two competing sources of truth
If files and SQLite both try to be canonical for everything, confusion will grow.

**Mitigation:** clearly define role boundaries between artifacts and DB state.

### Risk 3 — Premature migration complexity
Adding a large migration framework too early would increase maintenance burden.

**Mitigation:** keep initialization and schema evolution simple in v1.

### Risk 4 — Hiding the workflow behind infrastructure
If the DB becomes more important than the artifacts, the repository loses inspectability.

**Mitigation:** preserve artifact-first workflow and use SQLite only where structured persistence adds value.

---

## 14. Recommended Implementation Order

1. define persistence responsibilities between files and SQLite
2. choose DB location and initialization strategy
3. define initial schema
4. implement SQLite state store module
5. persist current state
6. persist execution/lifecycle events
7. integrate with resume/recovery-related paths
8. document the new persistence model

---

## 15. Suggested First-Step Philosophy

The first SQLite version should answer these questions reliably:

- what is the current known state of this feature?
- what was the most recent action taken?
- what events happened recently?
- is this feature blocked, active, completed, or archived?
- what state is safe to resume from?

If SQLite cannot answer those questions, it is not yet useful enough.

---

## 16. Definition of Done

Feature 009 is done when:

- `amazing-async-dev` has a lightweight SQLite persistence backbone
- the latest state and recent history are inspectable
- recovery and resume are better supported than in the file-only model
- the repository still preserves its artifact-first philosophy
- the system is ready for stronger v1 runtime capabilities without becoming operationally heavy

If the repository still depends only on scattered files to infer current state and recent history, this feature is not done.
