# Feature 081 — Phase 4: Unified Platform Shell

## Metadata

- **Document Type**: `feature spec`
- **Status**: `Implemented`
- **Feature ID**: `081`
- **Platform Phase**: `Phase 4`
- **Owner**: `async-dev`
- **Scope**: `operator-facing unification layer`
- **Purpose**: `Define and implement the unified platform shell that integrates operator surfaces into a coherent navigation experience`
- **Target**: `kernel + 2+ operator surfaces stable (precondition met)`
- **Implementation Date**: `2026-05-30`

---

## Acceptance Criteria Status

| AC | Description | Status |
|----|-------------|--------|
| AC-081-01 | Drill-Down Navigation | ✅ Implemented |
| AC-081-02 | Cross-Surface Links | ✅ Implemented |
| AC-081-03 | Blocking State Prominent | ✅ Implemented |
| AC-081-04 | Unified Recovery Dashboard | ✅ Implemented |
| AC-081-05 | State-Aware Navigation | ✅ Implemented |
| AC-081-06 | Interactive Attention Navigator | ✅ Implemented |
| AC-081-07 | Backward Compatibility | ✅ Verified |
| AC-081-08 | No Surface Replacement | ✅ Verified |

**All tests passed**: 1988 tests

---

## 1. Problem Statement

### 1.1 Current State

async-dev has multiple stable operator surfaces:

| Surface | Entry Point | Purpose |
|---------|-------------|---------|
| Recovery Console | `asyncdev recovery` | Execution recovery |
| Decision Inbox | `asyncdev decision` | Human decisions |
| Session Start | `asyncdev session-start` | Blocking state check |
| Execution Observer | `asyncdev observe-runs` | Supervision findings |
| Verification Console | `asyncdev verification` | Browser verification |
| Acceptance Console | `asyncdev acceptance` | Acceptance validation |
| Evidence Console | `asyncdev evidence` | Evidence rollup |
| Operator Home | `asyncdev home show` | Lightweight overview |

### 1.2 Fragmentation Problem

Despite individual surface quality, the platform feels fragmented:

```
Problem 1: No integrated navigation
- home shows "attention items" but routes via suggested CLI commands
- Operator must manually copy-paste commands to drill down

Problem 2: Cross-surface isolation
- Recovery Console doesn't link to Decision Inbox
- Acceptance status doesn't link to Verification Console
- Observer findings don't route to relevant surfaces

Problem 3: Blocking state disconnect
- session-start check runs separately
- home overview doesn't prominently surface blocking state
- operator must check multiple places for blocking

Problem 4: Recovery state scattered
- recovery list shows execution recovery
- acceptance status shows acceptance recovery
- observe-runs shows observer recovery recommendations
- Three surfaces, no unified recovery view

Problem 5: Action routing is text-only
- home shows "suggested_command" as text
- No drill-down commands
- No menu-driven navigation
```

### 1.3 Quote from Architecture

> "Only after the kernel and one or two operator surfaces are stable should async-dev move toward a unified platform shell."  
> — `docs/architecture.md`, Platform Evolution Phases

**Precondition Status**: ✅ MET
- Kernel: Stable (026-036 milestone verified)
- Recovery Console: Implemented (Feature 066)
- Decision Inbox: Implemented
- Session Start: Implemented (Feature 065)
- Observer: Implemented (Feature 067)

---

## 2. Solution: Unified Platform Shell

### 2.1 Definition

**Unified Platform Shell** is a navigation and routing layer that:

1. Provides drill-down commands from home into specific surfaces
2. Adds cross-surface links so operators can navigate between related surfaces
3. Prominently integrates blocking state into the overview
4. Offers a unified recovery dashboard aggregating all recovery aspects
5. Enables state-aware navigation (context passes between surfaces)

### 2.2 What It Is NOT

- NOT a replacement for individual surfaces (Recovery Console, Decision Inbox, etc.)
- NOT a giant all-in-one dashboard
- NOT a GUI/UI (remains CLI-based)
- NOT a new surface — it's an **integration layer**

### 2.3 Design Principle

> **"Overview first, drill-down second, surfaces remain authoritative."**

The shell makes the platform coherent without replacing the specialized surfaces beneath it.

---

## 3. Core Features

### 3.1 Drill-Down Navigation Commands

Add sub-commands to `home` that route directly into surface details:

```bash
# Current (text-only routing)
asyncdev home show
# Output: "Recovery needed: exec-001. Suggested: asyncdev recovery show --execution exec-001"

# Phase 4 (drill-down command)
asyncdev home recovery show --execution exec-001
# Directly shows recovery detail, no copy-paste

asyncdev home decision list --filter pending
# Directly shows pending decisions

asyncdev home attention
# Shows all items needing attention with numbered options
# Operator picks number -> drills into that item
```

### 3.2 Cross-Surface Links

Each surface adds links to related surfaces:

| From Surface | Links To | When |
|-------------|---------|------|
| Recovery Console | Decision Inbox | When recovery blocked by pending decision |
| Recovery Console | Acceptance | When recovery needs acceptance retry |
| Decision Inbox | Recovery | When decision unblocks recovery item |
| Decision Inbox | Verification | When decision affects verification |
| Acceptance | Recovery | When acceptance failure suggests recovery |
| Acceptance | Observer | When acceptance findings correlate with observer |
| Observer | Recovery | When findings indicate recovery needed |
| Observer | Decision | When findings require human decision |

### 3.3 Unified Blocking State

Integrate blocking state into home overview:

```bash
asyncdev home show
# Now includes:
# ┌─────────────────────────────────────┐
# │ 🔴 BLOCKING STATE DETECTED         │
# │    Decision request: dr-20260530-001│
# │    Run: asyncdev decision reply ... │
# └─────────────────────────────────────┘
```

New command:
```bash
asyncdev home blocking
# Shows all blocking states across surfaces
# - Pending decisions
# - Session-start blocking
# - Acceptance escalation
# - Verification exceptions
```

### 3.4 Unified Recovery Dashboard

New command aggregating all recovery aspects:

```bash
asyncdev home recovery-dashboard
# Shows:
# ┌─────────────────────────────────────┐
# │ RECOVERY OVERVIEW                   │
# ├─────────────────────────────────────┤
# │ Execution Recovery (3)             │
# │   • exec-001: failed, retry available
# │   • exec-002: blocked, needs decision │
# │   • exec-003: stalled, needs abort   │
# ├─────────────────────────────────────┤
# │ Acceptance Recovery (1)            │
# │   • feature-042: rejected, 2 retries │
# ├─────────────────────────────────────┤
# │ Observer Recovery Signals (2)       │
# │   • RUN_TIMEOUT: exec-005          │
# │   • VERIFICATION_STALL: exec-007   │
# └─────────────────────────────────────┘
```

### 3.5 State-Aware Navigation

Context passes between surfaces:

```bash
# Start from attention item in home
asyncdev home attention
# Shows numbered list:
# [1] Recovery: exec-001 (failed)
# [2] Decision: dr-001 (pending)
# [3] Acceptance: feature-042 (rejected)

# Pick option 2
asyncdev decision show --request dr-001
# Shows decision details

# Decide to approve
asyncdev decision reply --request dr-001 --command "DECISION approve"
# System detects this unblocks exec-001
# Output: "Decision approved. Related: exec-001 now unblocked for retry."

# Now navigate to recovery
asyncdev recovery show --execution exec-001
# exec-001 is now in retryable state
```

---

## 4. Implementation Details

### 4.1 File Structure Changes

```
cli/commands/home.py          # Add drill-down subcommands
runtime/operator_home_adapter.py  # Add blocking state, recovery aggregation
cli/commands/recovery.py      # Add cross-surface links
cli/commands/decision.py     # Add cross-surface links
cli/commands/acceptance.py    # Add cross-surface links
cli/commands/observer.py      # Add cross-surface links

# New files
cli/commands/home_recovery.py   # Unified recovery dashboard
cli/commands/home_attention.py # Interactive attention navigator
runtime/unified_blocking.py     # Blocking state aggregator
```

### 4.2 New CLI Commands

| Command | Purpose |
|---------|---------|
| `asyncdev home show` | Enhanced overview with blocking state |
| `asyncdev home attention` | Interactive attention item navigator |
| `home recovery-dashboard` | Unified view of all recovery aspects |
| `home blocking` | All blocking states across surfaces |
| `home navigate <surface> <id>` | Direct navigation to surface detail |
| `recovery link <exec> <target>` | Show links FROM this execution |
| `decision link <req> <target>` | Show links FROM this decision |
| `acceptance link <feat> <target>` | Show links FROM this acceptance |

### 4.3 Cross-Surface Link Schema

```python
# Each surface tracks cross-surface relationships
@dataclass
class CrossSurfaceLink:
    source_type: str  # recovery | decision | acceptance | observer
    source_id: str
    target_type: str
    target_id: str
    link_reason: str
    suggested_action: str

# Store in SQLite: cross_surface_links table
```

### 4.4 Blocking State Integration

```python
# runtime/unified_blocking.py
def get_blocking_state(project_id: str) -> BlockingState:
    """Aggregates all blocking states from all surfaces."""
    return BlockingState(
        session_blocked=session_start_check(project_id),
        pending_decisions=decision_store.get_pending(project_id),
        acceptance_escalations=acceptance_store.get_escalations(project_id),
        verification_exceptions=verification_store.get_exceptions(project_id),
    )

# Add to OperatorHomeOverview
@dataclass
class OperatorHomeOverview:
    # ... existing fields ...
    blocking_state: BlockingState  # NEW
    unified_recovery_summary: RecoverySummary  # NEW
```

---

## 5. User Flows

### Flow 1: Morning Check

```
Operator runs: asyncdev home show
  ├─ Sees: active runs, attention items, blocking state
  ├─ Blocking alert prominent if present
  └─ Quick links now executable, not just text

If blocking: asyncdev home blocking
  ├─ Shows all blocking states
  └─ Each links to relevant surface
```

### Flow 2: Triage Attention

```
Operator runs: asyncdev home attention
  ├─ Numbered list of all attention items
  ├─ Items grouped by category
  └─ Pick number -> drill into surface detail

Example:
  $ asyncdev home attention
  [1] Recovery: exec-001 (failed) - run-day execution
  [2] Decision: dr-001 (pending) - feature scope question
  [3] Acceptance: feature-042 (rejected) - auth criteria
  
  Select: 2
  --> asyncdev decision show --request dr-001
  
  After review:
  $ asyncdev decision reply --request dr-001 --command "DECISION revise C"
  --> "Decision recorded. Related recovery: exec-001 unblocked."
  
  Navigate to recovery:
  $ asyncdev home recovery exec-001
  --> Recovery detail with retry available
```

### Flow 3: Recovery Review

```
Operator runs: asyncdev home recovery-dashboard
  ├─ All recovery aspects in one view
  ├─ See: execution, acceptance, observer signals
  └─ Drill into specific recovery item

Select recovery item -> goes to Recovery Console detail
Recovery Console shows cross-links to related surfaces
```

---

## 6. Acceptance Criteria

### AC-081-01: Drill-Down Navigation
Operator can navigate from `home show` to surface detail without copy-paste.

### AC-081-02: Cross-Surface Links
All surfaces show links to related surfaces when relevant.

### AC-081-03: Blocking State Prominent
Blocking state appears prominently in `home show` output.

### AC-081-04: Unified Recovery Dashboard
Single command shows execution recovery + acceptance recovery + observer signals.

### AC-081-05: State-Aware Navigation
Decision approval triggers related recovery state update.

### AC-081-06: Interactive Attention Navigator
`home attention` allows numbered selection to drill into items.

### AC-081-07: Backward Compatibility
All existing surface commands continue to work unchanged.

### AC-081-08: No Surface Replacement
Shell remains integration layer, does not replicate surface functionality.

---

## 7. Non-Acceptance Criteria (Out of Scope)

- GUI/UI (remains CLI)
- Dashboard with charts/graphs
- Role-based access control
- Customizable views
- Mobile interface
- Non-CLI interaction

---

## 8. Implementation Order

### Phase 4.1: Blocking State Integration
1. Create `runtime/unified_blocking.py`
2. Add blocking state to `home show`
3. Add `home blocking` command
4. Test integration

### Phase 4.2: Drill-Down Commands
1. Add `home recovery` subcommand
2. Add `home decision` subcommand
3. Add `home attention` interactive navigator
4. Add `home navigate` direct routing

### Phase 4.3: Unified Recovery Dashboard
1. Create `home_recovery.py` command
2. Aggregate recovery from all surfaces
3. Add drill-through to surface detail

### Phase 4.4: Cross-Surface Links
1. Add link tracking to SQLite
2. Add `link` commands to each surface
3. Display links in surface output
4. Enable one-command navigation between surfaces

### Phase 4.5: Shell Completion & Polish
1. Update `cli/completion/` for new commands
2. Add tests for new commands
3. Update documentation

---

## 9. Dependencies

| Feature | Dependency |
|---------|-----------|
| Blocking state integration | Session Start (065), Decision Inbox |
| Drill-down commands | Recovery Console, Decision Inbox, etc. |
| Unified recovery dashboard | Recovery Console (066), Acceptance (077), Observer (067) |
| Cross-surface links | SQLite cross_surface_links table |
| State-aware navigation | All surfaces |

---

## 10. Risks and Mitigations

### Risk: Shell becomes overbuilt
**Mitigation**: Enforce "surfaces remain authoritative" principle. Shell only integrates, doesn't replicate.

### Risk: Cross-surface links create circular dependencies
**Mitigation**: Links are informational, not enforced. Circular references handled gracefully.

### Risk: Interactive navigator breaks in non-TTY
**Mitigation**: Provide non-interactive fallback (--select option) for script usage.

---

## 11. Metrics

| Metric | Measure |
|--------|---------|
| Navigation efficiency | Time to drill from home to surface detail |
| Cross-surface awareness | % of relevant cross-links shown |
| Blocking visibility | Blocking state prominence score |
| Operator satisfaction | Subjective coherence rating |

---

## 12. Deliverables

- [x] `cli/commands/home.py` - Enhanced with drill-down commands
- [x] `runtime/unified_blocking.py` - Blocking state aggregator
- [x] `runtime/operator_home_adapter.py` - Updated with blocking_state field
- [x] `runtime/cross_surface_links.py` - Cross-surface link helpers
- [x] Cross-surface links in: recovery, decision, observer
- [x] Shell completion updates (bash + zsh)
- [x] All tests pass (1988 tests)
- [x] This spec document (updated to Implemented status)

---

## 13. Definition of Done

Phase 4 is complete when:

1. Operator can navigate from `home show` to any surface detail without copy-paste
2. Blocking state is prominent and actionable in home overview
3. All recovery aspects (execution, acceptance, observer) visible in one command
4. Surfaces show cross-links to related surfaces
5. Decision actions update related surface state
6. All existing surface commands unchanged and functional
7. Shell completion works for all new commands
8. Tests pass for new functionality
