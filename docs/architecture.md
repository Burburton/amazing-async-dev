# Architecture

This document explains how the six core objects connect and support the async day loop.

---

## Object Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CORE OBJECTS                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ProductBrief ─────► FeatureSpec ─────► RunState                   │
│   (product idea)      (bounded feature)  (execution state)           │
│                                                                      │
│                           │                                          │
│                           ▼                                          │
│                                                                      │
│                     ExecutionPack ─────► ExecutionResult             │
│                     (bounded task)       (execution outcome)         │
│                                                                      │
│                           │                                          │
│                           ▼                                          │
│                                                                      │
│                     DailyReviewPack                                  │
│                     (nightly summary)                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Object Relationships

### Hierarchy

```
ProductBrief
    └── FeatureSpec (multiple)
            ├── RunState (one per feature)
            ├── ExecutionPack (daily)
            ├── ExecutionResult (daily)
            └── DailyReviewPack (daily)
```

### Flow

```
ProductBrief ──► defines ──► FeatureSpec
FeatureSpec ──► produces ──► ExecutionPack
ExecutionPack ──► executed ──► ExecutionResult
ExecutionResult ──► updates ──► RunState
ExecutionResult ──► generates ──► DailyReviewPack
DailyReviewPack ──► reviewed by ──► Human
Human decision ──► updates ──► RunState
RunState ──► drives ──► next ExecutionPack
```

---

## Day Loop Flow

### Morning: plan-day

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ ProductBrief│────►│ FeatureSpec │────►│  RunState   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ExecutionPack│
                                        └─────────────┘
```

**Inputs**: ProductBrief, FeatureSpec, current RunState
**Outputs**: Updated RunState, ExecutionPack

### Daytime: run-day

```
┌─────────────┐     ┌─────────────┐
│ExecutionPack│────►│  Execution  │────► RunState updates
└─────────────┘     │   (AI)      │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ExecutionResult│
                    └─────────────┘
```

**Inputs**: ExecutionPack
**Outputs**: ExecutionResult, updated RunState

### Evening: review-night

```
┌─────────────┐     ┌─────────────┐
│ExecutionResult│───►│Review Pack  │
│  RunState     │    │  Builder    │
└─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │DailyReviewPack│
                    └─────────────┘
```

**Inputs**: ExecutionResult, RunState
**Outputs**: DailyReviewPack

### Night: Human Review

```
┌─────────────┐     ┌─────────────┐
│DailyReviewPack│───►│   Human    │────► Decisions
└─────────────┘     │  Reviewer  │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Decision   │
                    │   Record    │
                    └─────────────┘
```

**Inputs**: DailyReviewPack
**Outputs**: Decision record (approve/revise/defer/redefine)

### Next Morning: resume-next-day

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Decision   │────►│  RunState   │────►│ExecutionPack│
│   Record    │     │ (updated)   │     │   (new)     │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Inputs**: Decision record, RunState
**Outputs**: New ExecutionPack

---

## Object Responsibilities

### ProductBrief
| Responsibility | Description |
|----------------|-------------|
| Define scope | Bound what the product tries to do |
| Set constraints | Limit scope drift |
| Identify target | Who is this for |
| Signal success | What indicates completion |

**Created by**: Human or planning workflow
**Updated**: Infrequently (major changes)
**Consumed by**: plan-day, feature planning

### FeatureSpec
| Responsibility | Description |
|----------------|-------------|
| Bound feature | Define what's in/out of scope |
| Set acceptance | Define completion criteria |
| Estimate effort | Day-sized task count |
| Identify dependencies | What blocks start |

**Created by**: Feature planning
**Updated**: When scope changes
**Consumed by**: plan-day, execution

### RunState
| Responsibility | Description |
|----------------|-------------|
| Track progress | What's done, pending, blocked |
| Enable pause | State survives interruption |
| Enable resume | Work continues from state |
| Flag blockers | What's stopping progress |
| Request decisions | What needs human input |

**Created by**: plan-day
**Updated**: Every action (high frequency)
**Consumed by**: All workflows

### ExecutionPack
| Responsibility | Description |
|----------------|-------------|
| Bound execution | Define task scope |
| Set deliverables | What must be produced |
| Set constraints | What must not be violated |
| Set stop conditions | When to pause |
| Set verification | How to check outputs |

**Created by**: plan-day
**Updated**: Never (immutable)
**Consumed by**: run-day

### ExecutionResult
| Responsibility | Description |
|----------------|-------------|
| Report completion | What was done |
| Report artifacts | What was created |
| Report verification | What passed/failed |
| Report blockers | What stopped progress |
| Report decisions | What needs human input |
| Recommend next | What to do next |

**Created by**: run-day
**Updated**: Never (immutable)
**Consumed by**: review-night, resume-next-day

### DailyReviewPack
| Responsibility | Description |
|----------------|-------------|
| Compress progress | Summarize for fast review |
| Present evidence | Link to artifacts |
| Present decisions | Options for human choice |
| Recommend actions | AI suggestions |
| Propose tomorrow | Next day plan |

**Created by**: review-night
**Updated**: Never (immutable)
**Consumed by**: Human reviewer

---

## State Flow Details

### RunState Update Sequence

```
Before plan-day:
RunState: {
  current_phase: reviewing (from previous night)
  decisions_needed: [items from human review]
  task_queue: []
}

After plan-day:
RunState: {
  current_phase: planning → executing
  active_task: task-001
  task_queue: [task-002, task-003]
  decisions_needed: [] (resolved)
}

During run-day (after each action):
RunState: {
  completed_outputs: [new items]
  last_action: "Created schema.yaml"
  updated_at: timestamp
}

After run-day:
RunState: {
  current_phase: reviewing
  next_recommended_action: "Continue with next schema"
}

After human review:
RunState: {
  current_phase: planning (for resume)
  decisions_needed: [] (if approved)
  OR
  decisions_needed: [refined items] (if revised)
}
```

---

## Data Flow Maps

### ExecutionResult → RunState

| ExecutionResult Field | RunState Field |
|----------------------|----------------|
| completed_items | completed_outputs (append) |
| artifacts_created | artifacts (update) |
| blocked_reasons | blocked_items (append) |
| decisions_required | decisions_needed (append) |
| recommended_next_step | next_recommended_action (set) |

### ExecutionResult → DailyReviewPack

| ExecutionResult Field | DailyReviewPack Field |
|----------------------|----------------------|
| completed_items | what_was_completed |
| artifacts_created | evidence |
| issues_found | problems_found |
| blocked_reasons | blocked_items |
| decisions_required | decisions_needed |
| recommended_next_step | tomorrow_plan |

### Human Decision → RunState

| Decision Action | RunState Update |
|-----------------|-----------------|
| approve | Remove from decisions_needed, proceed |
| revise | Update decision choice, proceed |
| defer | Keep in decisions_needed, skip task |
| redefine | Update feature scope, new task |

---

## Storage Locations

| Object | Location Pattern |
|--------|------------------|
| ProductBrief | `projects/{product_id}/product-brief.md` |
| FeatureSpec | `projects/{product_id}/features/{feature_id}/feature-spec.md` |
| RunState | `projects/{product_id}/runstate.md` |
| ExecutionPack | `projects/{product_id}/execution-packs/{execution_id}.md` |
| ExecutionResult | `projects/{product_id}/execution-results/{execution_id}.md` |
| DailyReviewPack | `projects/{product_id}/reviews/{date}-review.md` |

---

## Key Design Decisions

### Why RunState is Central
- Only object updated during execution
- Single source of truth for "where we are"
- Enables pause/resume without memory
- All other objects consume or produce it

### Why ExecutionPack is Immutable
- Prevents scope drift during execution
- Provides audit trail
- Enables comparison of plan vs result
- Enforces bounded execution

### Why DailyReviewPack is Compressed
- Targets 20-30 minute human review
- Limits decisions to ≤3 per day
- Aggregates minor items
- Links to evidence, not details

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem |
|--------------|---------|
| Updating ExecutionPack during execution | Scope drift |
| Skipping RunState updates | Context loss |
| More than 3 decisions in review pack | Review fatigue |
| Vague stop conditions | Execution runaway |
| Missing evidence links | Unverifiable progress |
| Unbounded task scope | AI drift |

---

## Success Indicators

| Indicator | Measure |
|-----------|---------|
| Resume works | Next day starts from RunState, no re-explanation |
| Scope honored | ExecutionResult matches ExecutionPack scope |
| Review efficient | Human review ≤30 minutes |
| Decisions leveraged | ≤3 meaningful decisions per day |
| Progress visible | Evidence links exist and verify |
| State persists | RunState survives interruption |

---

## Next Steps

After understanding this architecture:
1. Read schemas/ for field details
2. Read templates/ for usage patterns
3. Read examples/ for concrete instances
4. Try a day loop with demo product