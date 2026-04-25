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

## Persistence Layer: Files vs SQLite

Feature 009 introduced SQLite as a structured persistence backbone while keeping file artifacts as human-readable first-class objects.

### Design Philosophy

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DUAL PERSISTENCE MODEL                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   FILES (Human-readable)          SQLITE (Structured)               │
│   ─────────────────────          ──────────────────                │
│   • feature-spec.yaml            • current feature status           │
│   • execution-pack.yaml/.md      • latest runstate metadata         │
│   • execution-result.md          • event history                    │
│   • daily-review-pack.md         • transition history               │
│   • archive-pack.yaml            • archive metadata/index           │
│                                                                      │
│   Purpose: Human review           Purpose: Query & recovery         │
│   Format: Markdown/YAML          Format: Relational tables          │
│   Access: File read/write        Access: SQL queries                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Files: Human-Readable Artifacts

**Purpose**: Enable human review, inspection, and manual editing.

| Artifact | Why File? |
|----------|-----------|
| feature-spec.yaml | Human defines scope, reads during review |
| execution-pack.yaml | Human approves bounded task |
| execution-result.md | Human reviews outcome |
| daily-review-pack.md | Human reads nightly summary |
| archive-pack.yaml | Human accesses lessons for future features |

**Characteristics**:
- Immutable after creation (except RunState)
- Markdown/YAML format for readability
- Stored in project directories for visibility
- Can be edited manually if needed

### SQLite: Structured Persistence

**Purpose**: Enable queries, recovery, and history tracking.

| Table | Purpose |
|-------|---------|
| products | Product registry |
| features | Feature status tracking |
| runstate_snapshots | Point-in-time state recovery |
| execution_events | Event history for debugging |
| lifecycle_transitions | Phase transition audit trail |
| archive_records | Archive metadata index |

**Characteristics**:
- Updated on every state change
- JSON fields for complex data (task_queue, blocked_items)
- Timestamps for temporal queries
- Foreign key relationships for integrity

### SQLiteStateStore: Dual Writer

```python
# SQLiteStateStore mirrors StateStore interface
store = SQLiteStateStore(project_path)

# Writes to BOTH file AND SQLite
store.save_runstate(runstate)
# → writes runstate.md (file)
# → writes runstate_snapshots table (SQLite)
# → writes execution_events table (SQLite)
# → updates features table phase

# Reads from file (human-readable)
runstate = store.load_runstate()
# → reads runstate.md

# Queries from SQLite (structured)
info = store.get_recovery_info(feature_id)
# → queries runstate_snapshots, execution_events, lifecycle_transitions
```

### When to Use Each

| Scenario | Use | Why |
|----------|-----|-----|
| Human reads feature spec | File | Markdown readable |
| Human edits execution pack | File | YAML editable |
| AI queries recovery info | SQLite | Structured query |
| AI checks phase transitions | SQLite | History table |
| AI finds archived features | SQLite | Archive index |
| System logs execution event | SQLite | Event table |

### Database Location

```
projects/{product_id}/.runtime/amazing_async_dev.db
```

Or globally:
```
.runtime/amazing_async_dev.db
```

### CLI Access

```bash
# SQLite queries (structured)
asyncdev sqlite history --project {id} --feature {id}
asyncdev sqlite transitions --project {id}
asyncdev sqlite recovery --project {id} --feature {id}
asyncdev sqlite features --project {id}
asyncdev sqlite snapshot --project {id}
```

### Recovery Example

```python
# AI needs to resume after interruption
info = store.get_recovery_info("001-auth")

# Returns structured recovery data:
{
    "latest_snapshot": {...},      # Last known state
    "recent_events": [...],        # Recent actions
    "transitions": [...],          # Phase changes
    "can_resume": True             # Recovery possible?
}
```

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

## Live API Mode

Feature 011 introduced Live API Mode hardening for resilient AI-driven execution.

### Overview

Live API Mode allows AI to execute tasks directly through LLM API calls, enabling autonomous progress without external tool integration. This mode requires robust error handling to survive transient failures.

### API Failure Classification

```
┌─────────────────────────────────────────────────────────────────────┐
│                     API FAILURE CLASSIFICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   RETRYABLE (Auto-retry with backoff)                               │
│   ─────────────────────────────────────                             │
│   • PROVIDER_NETWORK_FAILURE   → Network/connection issues           │
│   • TIMEOUT_FAILURE            → Request timeout                     │
│   • RATE_LIMIT_FAILURE         → Provider rate limit hit             │
│   • MODEL_ERROR                → Transient model errors              │
│                                                                      │
│   NON-RETRYABLE (Stop and report)                                   │
│   ─────────────────────────────────────                             │
│   • AUTH_CONFIG_FAILURE        → Missing/invalid API key             │
│   • MALFORMED_RESPONSE         → Invalid JSON from provider          │
│   • VALIDATION_FAILURE         → Response schema mismatch            │
│   • UNSAFE_RESUME              → Unknown error (default)             │
│   • CONTENT_FILTER_FAILURE     → Content policy violation            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Retry Behavior

```
BailianLLMAdapter Retry Flow:

1. API call attempted
2. Failure detected
3. Classify error → APIFailureClassification
4. Check retryable?
   ── YES → Retry with exponential backoff (max_retries=3, delay=1s→2s→4s)
   ── NO  → Stop, report failure in ExecutionResult
5. All retries exhausted → Report as non-retryable failure
```

### ExecutionLogger Integration

LiveAPIEngine integrates with ExecutionLogger for structured event recording:

```python
# LiveAPIEngine initialization
engine = LiveAPIEngine(
    project_path=project_path,  # Required for SQLite logging
    execution_pack=pack,
    adapter=BailianLLMAdapter()
)

# Events logged to SQLite:
# - execution_start
# - api_call_attempt (each retry)
# - api_call_success / api_call_failure
# - execution_complete / execution_error

# Engine close ensures events flushed
engine.close()
```

### ExecutionResult Enhancement

Live API execution results include `api_failure_classification`:

```yaml
execution_id: "2025-01-15-001"
status: "failed"
api_failure_classification: "RATE_LIMIT_FAILURE"  # NEW field
completed_items: []
issues_found:
  - "API rate limit exceeded after 3 retries"
recommended_next_step: "Wait 60s and retry, or switch to external tool mode"
```

### Recovery Integration

Failed API calls are classified and stored for recovery guidance:

```python
# Recovery info includes API failure context
info = store.get_recovery_info("001-auth")

# Returns:
{
    "latest_snapshot": {...},
    "recent_events": [
        {"event_type": "api_call_failure", "classification": "RATE_LIMIT_FAILURE"},
        ...
    ],
    "can_resume": True,  # Retryable failures allow resume
    "recovery_hint": "Wait and retry, or use external tool mode"
}
```

### Error Handling Patterns

| Failure Type | Handling |
|--------------|----------|
| `RATE_LIMIT_FAILURE` | Wait + retry (up to 3), report if exhausted |
| `NETWORK_FAILURE` | Immediate retry with backoff |
| `AUTH_CONFIG_FAILURE` | Stop immediately, request config fix |
| `CONTENT_FILTER_FAILURE` | Stop immediately, review prompt content |

### When to Use Live API Mode

| Scenario | Recommended Mode |
|----------|------------------|
| Simple bounded tasks | Live API (autonomous) |
| Complex multi-file work | External tool (human-guided) |
| API unstable/rate-limited | External tool (more control) |
| Quick iteration/experiment | Live API (fast feedback) |

---

## Repository Modes (Feature 039)

Feature 039 introduced explicit governance boundaries for artifact ownership.

### Mode A: Self-Hosted Product Mode

The product being developed is the current repository itself.

**Examples:**
- `amazing-async-dev` developing `amazing-async-dev`
- `amazing-visual-map` developing itself in its own repo

**Characteristics:**
- Product repo == Working repo
- All artifacts may coexist in `projects/{product_id}/`
- No ownership boundary needed

### Mode B: Managed External Product Mode

`amazing-async-dev` orchestrates development of a separate real repository.

**Examples:**
- `amazing-async-dev` drives work on `amazing-visual-map`
- `amazing-async-dev` drives work on another app/tool/site repo

**Characteristics:**
- Product repo != Orchestration repo
- Artifact ownership must be split clearly
- Project-link.yaml defines the boundary

### Ownership Boundary

```
┌─────────────────────────────────────────────────────────────────────┐
│                     OWNERSHIP BOUNDARY (Mode B)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   PRODUCT REPO (Product Truth)         ASYNC-DEV (Orchestration)   │
│   ─────────────────────────            ────────────────────────     │
│   • ProductBrief                       • ExecutionPack              │
│   • FeatureSpec                        • ExecutionResult            │
│   • Feature completion reports         • Orchestration runstate     │
│   • Dogfood reports                    • Verification records       │
│   • Friction logs                      • Continuation state         │
│   • Phase summaries                    • Project-link.yaml          │
│   • Product memory                     • Orchestration telemetry    │
│   • North-star documents                                             │
│                                                                      │
│   Purpose: Product self-description   Purpose: How work was done   │
│   Survives async-dev removal          Survives product unchanged   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Principle

> **Product truth should live with the product. Orchestration truth should live with the orchestrator.**

### Decision Test

Before creating/storing an artifact:

1. **Does this describe the product?** → Product repo
2. **Does this describe async-dev execution?** → async-dev
3. **Would this matter if async-dev disappeared?** → Product repo
4. **Would this matter if async-dev workflow changed but product unchanged?** → async-dev

### Project-Link Metadata

For Mode B, async-dev maintains a linkage record:

```yaml
product_id: "amazing-visual-map"
repo_url: "https://github.com/Burburton/amazing-visual-map"
ownership_mode: "managed_external"
repo_local_path: "../amazing-visual-map"
```

This enables:
- Product repo owns its canonical documents
- async-dev owns orchestration metadata
- Clear boundary prevents archive overreach

### Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Problem |
|--------------|---------|
| Product Repo Hollowing | Product lacks its own canonical docs |
| Orchestrator Archive Overreach | async-dev becomes product archive |
| Mixed Ownership Without Boundary | Same artifact class stored unpredictably |

---

## Storage Locations (Extended)

### Mode A: Self-Hosted
| Object | Location Pattern |
|--------|------------------|
| ProductBrief | `projects/{product_id}/product-brief.md` |
| FeatureSpec | `projects/{product_id}/features/{feature_id}/feature-spec.md` |
| RunState | `projects/{product_id}/runstate.md` |
| ExecutionPack | `projects/{product_id}/execution-packs/{execution_id}.md` |
| ExecutionResult | `projects/{product_id}/execution-results/{execution_id}.md` |
| DailyReviewPack | `projects/{product_id}/reviews/{date}-review.md` |

### Mode B: Managed External
| Object | Product Repo | async-dev |
|--------|--------------|-----------|
| ProductBrief | `projects/{product_id}/product-brief.md` | — |
| FeatureSpec | `projects/{product_id}/features/{feature_id}/feature-spec.md` | — |
| Dogfood/Friction | `projects/{product_id}/dogfood/`, `friction/` | — |
| ExecutionPack | — | `projects/{product_id}/execution-packs/` |
| ExecutionResult | — | `projects/{product_id}/execution-results/` |
| RunState | — | `projects/{product_id}/runstate.md` |
| ProjectLink | — | `projects/{product_id}/project-link.yaml` |

---

## Platform Layer Model

async-dev is structured as a three-layer platform:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PLATFORM LAYER STRUCTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Layer C: Policy / Recipe                                          │
│   ─────────────────────────                                         │
│   • FrontendVerificationRecipe (Feature 062)                        │
│   • Browser verification orchestration (Features 059-060)           │
│   • External closeout policy (Feature 061)                          │
│   • Verification gating policy                                      │
│   • Human decision escalation policy (Feature 064)                  │
│   • Auto-continue execution policy                                  │
│                                                                      │
│   ───────────────────────────────────────────────────────────────   │
│                                                                      │
│   Layer B: Operator Surfaces                                        │
│   ─────────────────────────                                        │
│   • Recovery Console (Feature 066) → asyncdev recovery             │
│   • Decision Inbox → asyncdev decision                             │
│   • Session Start (Feature 065) → asyncdev session-start           │
│   • Execution Observer CLI (Feature 067) → asyncdev observe-runs   │
│   • Verification Console (proposed) → asyncdev verification        │
│                                                                      │
│   ───────────────────────────────────────────────────────────────   │
│                                                                      │
│   Layer A: Execution Kernel                                         │
│   ─────────────────────────────                                     │
│   • Day loop commands (plan-day, run-day, review-night, resume)    │
│   • ExecutionPack generation, ExecutionResult persistence          │
│   • SQLite state store, RunState management                        │
│   • Verification orchestration (Features 056-062)                  │
│   • Closeout handling                                               │
│   • Recovery flows                                                  │
│   • ExecutionObserver runtime (supervision foundation)             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Descriptions

| Layer | Name | Purpose | Maturity |
|-------|------|---------|----------|
| **Layer A** | Execution Kernel | Core execution engine, state management, day loop | Functional alpha, verified through dogfooding |
| **Layer B** | Operator Surfaces | Human-facing operational control/visibility | Implemented (066, 067, 065), functional alpha |
| **Layer C** | Policy/Recipe Layer | Work-type-specific execution policies | Partially implemented, hardening in progress |

### Layer Interactions

```
Operator (Layer B)          Kernel (Layer A)           Policy (Layer C)
      │                          │                           │
      │  ── observes ───────────►│                           │
      │                          │                           │
      │  ── triggers recovery ──►│◄── applies policy ────────│
      │                          │                           │
      │  ── requests decision ──►│◄── escalation rules ──────│
      │                          │                           │
      │                          │◄── verification recipe ───│
```

### Capability Mapping

| Capability | Layer | CLI Command |
|------------|-------|-------------|
| Day loop execution | Kernel | `asyncdev plan-day`, `run-day`, `review-night`, `resume-next-day` |
| State persistence | Kernel | Internal (SQLite, file artifacts) |
| Recovery Console | Operator | `asyncdev recovery list/show/resume` |
| Decision Inbox | Operator | `asyncdev decision list/show/reply/wait` |
| Session Start | Operator | `asyncdev session-start check/poll/status` |
| Execution Observer | Operator | `asyncdev observe-runs run/status/types` |
| Frontend verification | Policy | Internal (FrontendVerificationRecipe) |
| Browser verification | Policy | Internal (BrowserVerificationOrchestrator) |
| Closeout policy | Policy | Internal (ExternalExecutionCloseout) |

### Platform Evolution Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 0 | Platform definition, architecture | ✅ Complete |
| Phase 1 | Kernel stabilization, day loop hardening | ✅ Complete (026-036 milestone) |
| Phase 2 | First operator product (Recovery Console) | ✅ Implemented (Feature 066) |
| Phase 3 | Decision surface | ✅ Implemented (Decision Inbox) |
| Phase 4 | Unified platform shell | Future |

**Note**: Platform phases (0-4) are distinct from email/reporting roadmap phases (1-5) defined in the decision channel spec.

---

## Next Steps

After understanding this architecture:
1. Read schemas/ for field details
2. Read templates/ for usage patterns
3. Read examples/ for concrete instances
4. Try a day loop with demo product
5. For managed external products, read docs/infra/039-artifact-ownership-storage-boundary.md
6. For platform positioning, read docs/infra/async-dev-platform-architecture-product-positioning.md