# Operating Model

This document describes how `amazing-async-dev` operates in practice — the daily rhythms, roles, and interactions between AI and human.

---

## Core Rhythm

```
┌─────────────────────────────────────────────────────────────────┐
│                        DAY LOOP                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   MORNING                                                       │
│   ┌─────────────┐                                               │
│   │ plan-day    │  Human defines today's bounded task           │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────┐                                               │
│   │ ExecutionPack │ Generated for AI                           │
│   └─────────────┘                                               │
│         ↓                                                       │
│   DAYTIME                                                       │
│   ┌─────────────┐                                               │
│   │ run-day     │  AI executes autonomously                     │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────┐                                               │
│   │ ExecutionResult │ AI delivers structured output            │
│   └─────────────┘                                               │
│         ↓                                                       │
│   EVENING                                                       │
│   ┌─────────────┐                                               │
│   │ review-night │ Generate review pack                         │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────┐                                               │
│   │ DailyReviewPack │ Human reviews in 20–30 min               │
│   └─────────────┘                                               │
│         ↓                                                       │
│   NIGHT                                                         │
│   Human makes decisions, updates direction                      │
│         ↓                                                       │
│   NEXT MORNING                                                  │
│   ┌─────────────┐                                               │
│   │ resume-next-day │ Continue from state                      │
│   └─────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Roles

### Human Role

| Phase | Responsibility |
|-------|----------------|
| Morning | Define today's goal, set boundaries |
| Night | Review progress, make decisions, redirect |
| Anytime | Handle blockers, resolve decisions |

**Time investment target**: 20–30 minutes per day (review + decisions)

### AI Role

| Phase | Responsibility |
|-------|----------------|
| Daytime | Execute within defined scope |
| Daytime | Produce deliverables, leave evidence |
| Daytime | Update RunState continuously |
| Daytime | Flag blockers, request decisions |
| Evening | Generate review pack |

**Autonomy target**: 4+ hours without human intervention

---

## Phase Details

### 1. plan-day

**Trigger**: Morning, or after previous day's decisions

**Inputs**:
- ProductBrief (product context)
- FeatureSpec (feature context)
- RunState (current state)

**Outputs**:
- Updated RunState (with new task_queue)
- ExecutionPack (bounded task for today)

**Rules**:
- Only one main goal per day
- Task must fit in half-day to one-day
- Over-large tasks are split
- Do not start if key decisions are pending

**Human action**: Approve or adjust the proposed plan

---

### 2. run-day

**Trigger**: ExecutionPack ready, human approved

**Inputs**:
- ExecutionPack (bounded task definition)

**Outputs**:
- ExecutionResult (structured outcome)
- Updated RunState

**AI must**:
- Stay inside task_scope
- Complete deliverables, then stop
- Stop at stop_conditions
- Leave evidence (files, logs, artifacts)
- Output recommended_next_step

**AI must not**:
- Expand scope without human approval
- Make architectural decisions alone
- Skip verification steps
- Leave blocked items unreported

**Human action**: None (autonomous execution)

---

### 3. review-night

**Trigger**: Daytime execution completed or stopped

**Inputs**:
- ExecutionResult
- RunState

**Outputs**:
- DailyReviewPack (human-readable summary)

**Purpose**: Compress all daytime activity into a 20–30 minute review

**Pack structure**:
- What was completed (with evidence)
- Problems found
- Blocked items
- Decisions needed (with options)
- Tomorrow's plan

**Human action**: Read, decide, annotate

---

### 4. resume-next-day

**Trigger**: Human decisions recorded

**Inputs**:
- Human decisions (approve/revise/defer/redefine)
- Latest RunState

**Outputs**:
- New ExecutionPack
- Updated RunState

**Purpose**: Continue from state, not from explanation

**Human action**: Confirm continuation plan

---

## State Management

### RunState is the heartbeat

`RunState` is updated throughout every phase:

| When | What updates |
|------|--------------|
| plan-day | task_queue, active_task, next_recommended_action |
| run-day | completed_outputs, artifacts, blocked_items, decisions_needed |
| review-night | decisions_needed (resolved or noted) |
| resume-next-day | current_phase, active_task, task_queue |

### Continuity guarantee

If RunState is lost:
- Work cannot resume properly
- Context must be reconstructed manually
- Day loop breaks

Therefore:
- RunState is saved to disk after every action
- RunState includes updated_at timestamp
- RunState is the single source of truth for "where we are"

---

## Decision Flow

### Decision categories

| Type | Human action | AI action |
|------|--------------|-----------|
| Execution decision | Approve plan | Execute |
| Scope expansion | Approve/reject | Request permission |
| Technical choice | Choose from options | Implement chosen path |
| Blocked item | Resolve or defer | Report and wait |
| Acceptance check | Confirm or revise | Verify and report |

### Decision compression

The system aims to minimize human decisions per day:

| Target | ≤ 3 meaningful decisions per day |
|--------|-----------------------------------|

"Meaningful" means: choices that affect direction, not implementation details.

---

## Failure Handling

### Execution blocked

| Scenario | Response |
|----------|----------|
| External dependency missing | Report in blocked_items, wait |
| Technical uncertainty | Request decision with options |
| Scope ambiguity | Stop, request clarification |
| Unexpected error | Log, continue if safe, otherwise stop |

### AI goes off-track

| Detection | Response |
|-----------|----------|
| Scope expansion without approval | Stop, flag violation |
| Missing deliverables | Flag in review pack |
| No evidence left | Flag in review pack |
| Decision made without human | Flag violation |

---

## Night Review Process

### Human workflow

```
1. Open DailyReviewPack
2. Scan completed outputs (with evidence)
3. Review problems and blockers
4. Read decisions_needed (with options)
5. Make decisions (approve/revise/defer/redefine)
6. Confirm tomorrow's plan
```

### Target time: 20–30 minutes

| Activity | Target time |
|----------|-------------|
| Scan completion | 5 min |
| Review problems | 5 min |
| Make decisions | 10–15 min |
| Confirm next plan | 2–3 min |

---

## Multi-day Patterns

### Healthy progression

```
Day 1: Setup + first implementation
Day 2: Continue implementation, first verification
Day 3: Fix issues, polish
Day 4: Complete, verify, ready for integration
```

### Blocked progression

```
Day 1: Start, hit blocker
Day 2: (Human resolves blocker overnight) Resume
Day 3: Continue, new blocker
Day 4: (Human defers blocker) Work on alternative path
```

### Scope drift (violation)

```
Day 1: Start feature X
Day 2: AI expands to feature Y without approval → STOP, flag violation
Day 3: (Human corrects scope) Restart feature X only
```

---

## Artifact Lifecycle

| Artifact | Created | Updated | Read |
|----------|---------|---------|------|
| ProductBrief | Human (initial) | Rarely | Every phase |
| FeatureSpec | Human or plan workflow | When scope changes | Every phase |
| RunState | plan-day | Every action | Every phase |
| ExecutionPack | plan-day | Never (immutable per day) | run-day |
| ExecutionResult | run-day | Never | review-night |
| DailyReviewPack | review-night | Never (immutable) | Human at night |

---

## Constraints

### Hard constraints

1. No scope expansion without human approval
2. No decision-making without human involvement
3. No state loss (RunState must persist)
4. No execution without defined ExecutionPack
5. No day-end without review pack

### Soft constraints

1. Prefer small tasks over large tasks
2. Prefer explicit evidence over implicit completion
3. Prefer blocking on decisions over guessing
4. Prefer recording over remembering

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Human time per day | ≤ 30 minutes |
| Decisions per day | ≤ 3 meaningful |
| AI autonomous time | ≥ 4 hours |
| Resume accuracy | Start from RunState, no re-explanation |
| Completion rate | ≥ 80% of planned deliverables |
| Blocker resolution | ≤ 1 day (human resolves overnight) |

---

## What makes this model work

1. **Boundaries**: AI cannot drift because scope is explicit
2. **State**: Continuity survives because RunState persists
3. **Compression**: Human can review fast because review pack is focused
4. **Decisions**: Human time is leveraged because only meaningful choices appear
5. **Evidence**: Progress is verifiable because outputs are documented

---

## First implementation priority

The first working system must demonstrate:
- A valid ExecutionPack generated
- AI executes for ≥ 1 hour without intervention
- A DailyReviewPack produced
- Human reviews in ≤ 30 minutes
- Next day resumes from RunState

Start with Feature 001 (Core Object System).
Then Feature 002 (Day Loop CLI).
Then Feature 003 (Single Feature Demo).