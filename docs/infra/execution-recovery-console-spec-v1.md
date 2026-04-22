# Execution Recovery Console — Specification

## Metadata

- **Document Type**: `operator surface specification`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `operator-facing product`
- **Related Architecture**: `docs/infra/async-dev-platform-architecture-product-positioning.md` (Section 12.1)
- **Date**: `2026-04-22`

---

## 1. Purpose

The Execution Recovery Console is the recommended **first operator surface** for async-dev, providing human-facing operational control and visibility for executions needing recovery.

Per the platform architecture document (Section 12.1):

> "This best complements current kernel work and addresses real operator pain."

---

## 2. Core Responsibilities

From architecture doc Section 12.1:

1. List executions in `recovery_required` state
2. Show why each execution needs recovery
3. Surface suggested next action
4. Allow continue/retry/resume actions
5. Show key linked artifacts and last known result state

---

## 3. Proposed CLI Commands

### 3.1 `asyncdev recovery list`

List all executions needing recovery across projects.

```
asyncdev recovery list [--project <project_id>] [--all]
```

**Output Format**:
```
Executions needing recovery:

| Execution ID     | Project      | Reason              | Suggested Action      | Last Updated |
|------------------|--------------|---------------------|-----------------------|--------------|
| exec-2026-0422-001 | amazing-async-dev | verification_timeout | retry_verification    | 2026-04-22 10:30 |
| exec-2026-0421-003 | demo-product | external_stalled    | resume_from_state     | 2026-04-21 18:15 |
```

### 3.2 `asyncdev recovery show`

Show detailed recovery information for a specific execution.

```
asyncdev recovery show --execution <execution_id>
```

**Output Sections**:
- Recovery classification (NORMAL_PAUSE, BLOCKED, FAILED, AWAITING_DECISION)
- Recovery reason details
- Last known RunState phase
- Last known ExecutionResult (if exists)
- Linked artifacts (ExecutionPack, ExecutionResult, verification artifacts)
- Recovery guidance (recommended actions)
- Available recovery actions (continue, retry, resume)

### 3.3 `asyncdev recovery resume`

Execute a recovery action to resume execution.

```
asyncdev recovery resume --execution <execution_id> --action <action>
```

**Supported Actions**:
- `continue` - Continue from current state (for NORMAL_PAUSE)
- `retry` - Retry failed step (for FAILED)
- `resume` - Resume from preserved state (for BLOCKED)
- `skip` - Skip and proceed (for AWAITING_DECISION with policy override)
- `abort` - Abort execution and clean up

---

## 4. Integration Points

### 4.1 Existing Recovery Infrastructure

The kernel already provides:

| Component | File | Purpose |
|-----------|------|---------|
| RecoveryClassification | `runtime/recovery_classifier.py` | State classification (NORMAL_PAUSE, BLOCKED, FAILED, AWAITING_DECISION, READY_TO_RESUME) |
| get_recovery_guidance() | `runtime/recovery_classifier.py` | Generate recommended actions |
| inspect_stop CLI | `cli/commands/inspect_stop.py` | Partial recovery surface (show, history, guidance) |
| RunState recovery fields | `schemas/runstate.schema.yaml` | `recovery_required`, `recovery_reason`, `suggested_action` |

### 4.2 Data Sources

- **RunState** (`projects/{project_id}/runstate.md`) - Recovery flags, last phase
- **ExecutionResult** (`projects/{project_id}/execution-results/*.md`) - Terminal state, verification status
- **ExecutionPack** (`projects/{project_id}/execution-packs/*.md`) - Original execution context
- **SQLite State Store** (`runtime/sqlite_state_store.py`) - Cross-project recovery state query

### 4.3 State Flow

```
Execution completes → ExecutionResult written → Closeout evaluates
                                                    ↓
                          RecoveryClassifier determines classification
                                                    ↓
                          RunState.recovery_required set (if needed)
                                                    ↓
                          Recovery Console surfaces to operator
                                                    ↓
                          Operator selects recovery action
                                                    ↓
                          resume_next_day executes action
```

---

## 5. Implementation Approach

### 5.1 Phase A — CLI Foundation

Create CLI command module:
- `cli/commands/recovery.py`
- Implement `list`, `show`, `resume` commands
- Integrate with existing `recovery_classifier.py`

### 5.2 Phase B — Cross-Project Query

- Query SQLite state store for all recovery_required executions
- Aggregate across projects
- Sort by urgency/age

### 5.3 Phase C — Action Execution

- Wire recovery actions to existing resume_next_day logic
- Handle each RecoveryClassification type appropriately
- Update RunState after action execution

---

## 6. Acceptance Criteria

### AC-001 List Recoveries
`asyncdev recovery list` shows all executions needing recovery with key details.

### AC-002 Show Recovery Details
`asyncdev recovery show --execution <id>` displays full recovery context.

### AC-003 Execute Recovery Action
`asyncdev recovery resume --execution <id> --action <action>` successfully resumes execution.

### AC-004 Cross-Project Visibility
With `--all`, lists recoveries across all managed projects.

### AC-005 Guidance Integration
Shows recovery guidance from existing `get_recovery_guidance()`.

### AC-006 Artifact Links
Displays linked ExecutionPack/ExecutionResult paths for context.

---

## 7. Non-Goals

This feature does NOT:
- Create a dashboard UI (CLI-only for Phase 1)
- Implement new recovery classifications (uses existing)
- Replace `inspect_stop` functionality (complements it)
- Handle automatic recovery (human-triggered only)

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Recovery state may be incomplete | Surface last known state, allow manual inspection |
| Multiple recovery options confusing | Show clear guidance from `get_recovery_guidance()` |
| Cross-project state query slow | Use SQLite for efficient aggregation |

---

## 9. Definition of Done

The Recovery Console is complete when:
1. All three CLI commands implemented
2. Cross-project recovery listing works
3. Recovery actions integrate with resume_next_day
4. Tests cover list/show/resume scenarios
5. Documentation updated in README.md

---

## 10. Architecture Alignment

This spec aligns with the platform architecture (Section 12.1):

> "A strong kernel without a usable operator surface remains difficult to manage in real use. This layer turns async-dev into an operable system."

The Recovery Console provides the recommended first operator surface that:
- Reflects kernel maturity needs
- Solves real operator pain
- Strengthens platform operability without overreaching

---

## 11. Suggested Implementation Order

1. Create `cli/commands/recovery.py` with `list` command
2. Implement `show` command with recovery classifier integration
3. Implement `resume` command with action execution
4. Add `--project` and `--all` filtering
5. Add tests
6. Update documentation

---

## 12. Status

**Proposed** — Ready for implementation decision.