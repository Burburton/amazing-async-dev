# Feature 043 Phase A Implementation Plan
## Decision Application & Continuation Resume Integration

---

## Overview

Phase A addresses the critical gap identified in `feature-021-to-040-gap-analysis.md`: Feature 021's email decision channel and RunState operate as disconnected systems. This plan defines the integration architecture and implementation steps.

---

## Goals

1. **Sync DecisionRequestStore ↔ RunState.decisions_needed** - bidirectional sync
2. **Integrate resume_next_day with DecisionRequestStore** - read from both sources
3. **Map reply commands to RunState actions** - enable continuation from email

---

## Architecture Changes

### Current Architecture (Disconnected)

```
DecisionRequestStore (.runtime/decision-requests/*.json)
         ↓
    email_decision CLI
         ↓
    Email send/reply
         ↓
    DecisionRequestStore.status = resolved
    
RunState.decisions_needed (projects/{project}/runstate.md)
         ↓
    resume_next_day CLI
         ↓
    Process decisions_needed directly
    
    ❌ NO SYNC BETWEEN SYSTEMS ❌
```

### Target Architecture (Integrated)

```
┌─────────────────────────────────────────────────────────────┐
│                   DECISION SYNC LAYER                       │
│                                                             │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │DecisionRequestStore│ ←──→ │ RunState           │        │
│  │                    │ SYNC │ decisions_needed[] │        │
│  │                    │      │ decision_pending   │        │
│  └────────────────────┘      └────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         ↓                              ↓
    email_decision CLI             resume_next_day CLI
         ↓                              ↓
    1. Create request               1. Load RunState
    2. CALL sync layer              2. CALL sync layer
    3. Send email                   3. Reconcile sources
         ↓                              ↓
    Reply received                  4. Process unified state
         ↓                              ↓
    1. Parse reply                  5. Update both stores
    2. CALL sync layer              6. Continue execution
    3. Update RunState
    
    ✅ SYNCED SYSTEM ✅
```

---

## Implementation Components

### Component 1: Decision Sync Layer

**Purpose**: Provide bidirectional sync between DecisionRequestStore and RunState.

**Location**: `runtime/decision_sync.py` (new file)

**Key Functions**:

```python
def sync_decision_to_runstate(
    request: dict[str, Any],
    runstate: dict[str, Any],
) -> dict[str, Any]:
    """
    Sync a decision request to RunState.decisions_needed.
    
    - Creates decision entry in decisions_needed
    - Sets decision_request_pending = request_id
    - Sets current_phase = blocked if needed
    
    Returns updated RunState.
    """
    
def sync_reply_to_runstate(
    request_id: str,
    reply: dict[str, Any],
    runstate: dict[str, Any],
) -> dict[str, Any]:
    """
    Sync email reply resolution to RunState.
    
    - Removes matching entry from decisions_needed
    - Sets last_decision_resolution = reply
    - Sets phase for continuation based on reply
    
    Returns updated RunState.
    """

def reconcile_decision_sources(
    project_path: Path,
) -> dict[str, Any]:
    """
    Reconcile DecisionRequestStore and RunState.
    
    - Load pending requests from DecisionRequestStore
    - Load RunState.decisions_needed
    - Identify discrepancies
    - Return unified state
    
    Returns unified decision state.
    """

def get_pending_decision_count(project_path: Path) -> int:
    """Get count of pending decisions from both sources."""
```

### Component 2: RunState Schema Extension

**Purpose**: Add fields to RunState schema for decision request tracking.

**Location**: `schemas/runstate.schema.yaml` (extension)

**New Fields**:

```yaml
decision_request_pending:
  type: string
  description: ID of active decision request awaiting reply
  example: "dr-20260416-001"
  required: false

decision_request_sent_at:
  type: datetime
  description: When decision email was sent
  required: false

last_decision_resolution:
  type: object
  description: Last resolved decision from email reply
  properties:
    request_id: string
    reply_command: string
    resolved_at: datetime
    applied_action: string
  required: false
```

### Component 3: Reply → Action Mapping

**Purpose**: Map reply commands to RunState continuation actions.

**Location**: `runtime/reply_action_mapper.py` (new file)

**Mapping Rules**:

```python
REPLY_ACTION_MAP = {
    ReplyCommand.DECISION: {
        "runstate_action": "select_option",
        "continuation": "proceed_with_selected_option",
    },
    ReplyCommand.APPROVE: {
        "runstate_action": "approve_risky_action",
        "continuation": "execute_approved_action",
    },
    ReplyCommand.DEFER: {
        "runstate_action": "defer_decision",
        "continuation": "proceed_with_alternative",
    },
    ReplyCommand.RETRY: {
        "runstate_action": "mark_retry_needed",
        "continuation": "retry_current_step",
    },
    ReplyCommand.CONTINUE: {
        "runstate_action": "clear_blocker",
        "continuation": "continue_execution",
    },
}

def map_reply_to_action(
    reply: ParsedReply,
    request: dict[str, Any],
) -> dict[str, Any]:
    """
    Map parsed reply to RunState action.
    
    Returns:
        - runstate_action: action to apply to RunState
        - continuation_phase: phase to set for continuation
        - next_recommended: next recommended action
        - instruction: specific instruction for execution
    """
```

### Component 4: resume_next_day Integration

**Purpose**: Update resume_next_day to read from both sources.

**Location**: `cli/commands/resume_next_day.py` (modification)

**Changes**:

1. **Import decision sync layer**:
```python
from runtime.decision_sync import reconcile_decision_sources
from runtime.decision_request_store import DecisionRequestStore
```

2. **Reconcile sources at resume start**:
```python
def continue_loop(...):
    # Existing: load RunState
    runstate = store.load_runstate()
    
    # NEW: reconcile with DecisionRequestStore
    unified_state = reconcile_decision_sources(project_path)
    
    # NEW: check for email decisions
    if unified_state.get("pending_email_decisions"):
        console.print("[cyan]Email decisions pending:[/cyan]")
        for req in unified_state["pending_email_decisions"]:
            console.print(f"  {req['decision_request_id']}: {req['question'][:40]}")
```

3. **Process email reply resolution**:
```python
def continue_loop(...):
    # NEW: if decision comes from email
    if unified_state.get("email_decision_resolved"):
        from runtime.decision_sync import sync_reply_to_runstate
        runstate = sync_reply_to_runstate(
            unified_state["resolved_request_id"],
            unified_state["resolved_reply"],
            runstate,
        )
```

### Component 5: email_decision Integration

**Purpose**: Update email_decision CLI to sync with RunState.

**Location**: `cli/commands/email_decision.py` (modification)

**Changes**:

1. **Sync on creation**:
```python
def create(...):
    # Existing: create request
    request = store.create_request(...)
    
    # NEW: sync to RunState
    from runtime.decision_sync import sync_decision_to_runstate
    runstate_store = StateStore(project_path)
    runstate = runstate_store.load_runstate() or {}
    runstate = sync_decision_to_runstate(request, runstate)
    runstate_store.save_runstate(runstate)
    
    # NEW: log event
    console.print("[cyan]Synced to RunState.decisions_needed[/cyan]")
```

2. **Sync on reply**:
```python
def reply(...):
    # Existing: process reply
    parsed = parse_reply(command)
    # ... validation ...
    
    # NEW: sync resolution to RunState
    from runtime.decision_sync import sync_reply_to_runstate
    runstate_store = StateStore(project_path)
    runstate = runstate_store.load_runstate() or {}
    reply_record = create_reply_record(request_id, parsed, validation_status)
    runstate = sync_reply_to_runstate(request_id, reply_record, runstate)
    runstate_store.save_runstate(runstate)
    
    # NEW: set continuation phase
    from runtime.reply_action_mapper import map_reply_to_action
    action = map_reply_to_action(parsed, request)
    console.print(f"[green]Action: {action['runstate_action']}[/green]")
    console.print(f"[green]Next: {action['continuation']}[/green]")
```

---

## Implementation Steps

### Step 1: Create Decision Sync Layer

**File**: `runtime/decision_sync.py`

**Tasks**:
- [ ] Define `sync_decision_to_runstate()` function
- [ ] Define `sync_reply_to_runstate()` function
- [ ] Define `reconcile_decision_sources()` function
- [ ] Define `get_pending_decision_count()` function
- [ ] Add unit tests in `tests/test_decision_sync.py`

### Step 2: Extend RunState Schema

**File**: `schemas/runstate.schema.yaml`

**Tasks**:
- [ ] Add `decision_request_pending` field
- [ ] Add `decision_request_sent_at` field
- [ ] Add `last_decision_resolution` field
- [ ] Update JSON schema section
- [ ] Validate schema changes

### Step 3: Create Reply Action Mapper

**File**: `runtime/reply_action_mapper.py`

**Tasks**:
- [ ] Define `REPLY_ACTION_MAP` dictionary
- [ ] Define `map_reply_to_action()` function
- [ ] Define continuation phase logic
- [ ] Add unit tests in `tests/test_reply_action_mapper.py`

### Step 4: Integrate email_decision CLI

**File**: `cli/commands/email_decision.py`

**Tasks**:
- [ ] Import decision sync layer in `create` command
- [ ] Add RunState sync on request creation
- [ ] Import decision sync layer in `reply` command
- [ ] Add RunState sync on reply resolution
- [ ] Import reply_action_mapper
- [ ] Display continuation action after reply
- [ ] Add integration tests

### Step 5: Integrate resume_next_day CLI

**File**: `cli/commands/resume_next_day.py`

**Tasks**:
- [ ] Import decision sync layer
- [ ] Add reconciliation at resume start
- [ ] Display email decisions status
- [ ] Handle email decision resolution
- [ ] Update decision processing flow
- [ ] Add integration tests

### Step 6: Update Existing Tests

**Tasks**:
- [ ] Update `tests/test_email_decision.py` for RunState sync
- [ ] Update `tests/test_resume_next_day.py` for decision store integration
- [ ] Add end-to-end test: create → send → reply → resume

---

## Testing Strategy

### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `test_decision_sync.py` | Sync functions |
| `test_reply_action_mapper.py` | Action mapping |
| `test_email_decision.py` | Updated CLI |
| `test_resume_next_day.py` | Updated CLI |

### Integration Tests

**Scenario 1: Full Decision Loop**
```
1. email_decision create → RunState.decisions_needed has entry
2. email_decision send → RunState.phase = blocked
3. email_decision reply → RunState.decisions_needed cleared, phase updated
4. resume_next_day → Reads from both, sees resolution, continues
```

**Scenario 2: Reconciliation**
```
1. RunState has decision entry (manual)
2. DecisionRequestStore has no matching request
3. resume_next_day → Reconciles, detects orphan, warns user
```

**Scenario 3: Orphaned Request**
```
1. DecisionRequestStore has pending request
2. RunState has no decisions_needed entry
3. resume_next_day → Reconciles, syncs, shows pending
```

---

## Validation Checklist

After implementation, verify:

- [ ] `email_decision create` updates RunState.decisions_needed
- [ ] `email_decision reply` updates RunState.last_decision_resolution
- [ ] `resume_next_day` reads from DecisionRequestStore
- [ ] Reconciliation handles orphaned entries
- [ ] Reply commands map to continuation actions
- [ ] Phase transitions correctly after reply
- [ ] End-to-end loop works: create → send → reply → resume → continue

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Sync race conditions | Always sync through unified layer, no direct updates |
| Orphaned entries | Reconciliation detects and reports discrepancies |
| Phase mismatch | Validation checks phase vs decision state |
| Duplicate processing | Idempotency checks in reply processing |

---

## Dependencies

| Dependency | Status |
|------------|--------|
| Feature 021 (DecisionRequestStore) | ✅ Implemented |
| Feature 021 (EmailSender) | ✅ Implemented |
| Feature 021 (ReplyParser) | ✅ Implemented |
| RunState schema | ✅ Existing |
| StateStore | ✅ Existing |
| resume_next_day CLI | ✅ Existing |

---

## Estimated Effort

| Component | Effort |
|-----------|--------|
| Decision Sync Layer | 2-3 hours |
| RunState Schema Extension | 30 min |
| Reply Action Mapper | 1-2 hours |
| email_decision CLI Integration | 2-3 hours |
| resume_next_day CLI Integration | 2-3 hours |
| Tests | 2-3 hours |
| **Total** | **10-12 hours** |

---

## Definition of Done

Phase A is complete when:

1. Decision request creation syncs to RunState.decisions_needed
2. Email reply resolution syncs to RunState
3. resume_next_day reads from DecisionRequestStore
4. Reconciliation detects orphaned entries
5. Reply commands map to continuation actions
6. End-to-end decision loop works
7. All tests pass
8. Documentation updated

---

## Next Phase Preview

After Phase A completion:

**Phase B (Feature 040)**:
- Add status-report email template
- Add email type classification
- Link to execution context

**Phase C (Feature 041)**:
- Refine email content format
- Add blocker-specific template
- Document content contract

---

## Appendix: Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION REQUEST FLOW                        │
│                                                                 │
│   email_decision create                                         │
│         │                                                       │
│         ├─→ DecisionRequestStore.create_request()               │
│         │                                                       │
│         ├─→ decision_sync.sync_decision_to_runstate()           │
│         │       │                                               │
│         │       ├─→ Append to RunState.decisions_needed         │
│         │       ├─→ Set RunState.decision_request_pending       │
│         │       └─→ Set RunState.current_phase = blocked        │
│         │                                                       │
│         ├─→ StateStore.save_runstate()                          │
│         │                                                       │
│         └─→ EmailSender.send_decision_request()                  │
│                                                                 │
│   email_decision reply                                          │
│         │                                                       │
│         ├─→ ReplyParser.parse_reply()                           │
│         │                                                       │
│         ├─→ ReplyParser.validate_reply()                        │
│         │                                                       │
│         ├─→ decision_sync.sync_reply_to_runstate()              │
│         │       │                                               │
│         │       ├─→ Remove from RunState.decisions_needed       │
│         │       ├─→ Set RunState.last_decision_resolution       │
│         │       ├─→ Set RunState.phase for continuation         │
│         │       └─→ Clear RunState.decision_request_pending     │
│         │                                                       │
│         ├─→ reply_action_mapper.map_reply_to_action()           │
│         │       │                                               │
│         │       └─→ Return continuation instruction              │
│         │                                                       │
│         └─→ StateStore.save_runstate()                          │
│                                                                 │
│   resume_next_day continue_loop                                 │
│         │                                                       │
│         ├─→ StateStore.load_runstate()                          │
│         │                                                       │
│         ├─→ decision_sync.reconcile_decision_sources()          │
│         │       │                                               │
│         │       ├─→ Load pending from DecisionRequestStore      │
│         │       ├─→ Load RunState.decisions_needed              │
│         │       ├─→ Detect discrepancies                        │
│         │       └─→ Return unified state                        │
│         │                                                       │
│         ├─→ Display pending/resolved email decisions            │
│         │                                                       │
│         ├─→ Process unified decision state                      │
│         │                                                       │
│         └─→ Continue execution based on resolution              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Status

**Plan Created**: 2026-04-16
**Status**: Ready for Implementation
**Next Action**: Begin Step 1 (Create Decision Sync Layer)