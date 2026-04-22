# Decision Inbox — Specification

## Metadata

- **Document Type**: `operator surface specification`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `operator-facing product`
- **Related Architecture**: `docs/infra/async-dev-platform-architecture-product-positioning.md` (Phase 3)
- **Related Features**: Feature 021 (email-decision), Feature 064 (blocking protocol)
- **Date**: `2026-04-22`

---

## 1. Purpose

The Decision Inbox is the recommended **second operator surface** (Phase 3) for async-dev, providing unified human-facing control and visibility for pending decisions across projects.

Per the platform architecture document (Phase 3):

> "Add Decision Inbox to support low-interruption human-in-the-loop operation."

This complements the Recovery Console (Phase 2) by providing a dedicated surface for decision management rather than scattering decision-related commands under `email-decision`.

---

## 2. Core Responsibilities

From architecture doc Section 4.2 Layer B:

1. List pending decisions across all projects
2. Show decision context (question, options, recommendation, blocking state)
3. Process replies from CLI or webhook
4. Poll for asynchronous replies (blocking protocol integration)
5. Show decision history and resolution status

---

## 3. Current Infrastructure (Already Exists)

The system already has comprehensive decision infrastructure:

| Component | File | Status | Purpose |
|-----------|------|--------|---------|
| DecisionRequestStore | `runtime/decision_request_store.py` | ✅ | Decision request lifecycle |
| decision_sync | `runtime/decision_sync.py` | ✅ | Bidirectional RunState sync |
| decision_waiting_session | `runtime/decision_waiting_session.py` | ✅ | Blocking protocol check |
| email-decision CLI | `cli/commands/email_decision.py` | ✅ | Feature-oriented commands |
| Blocking Protocol | `docs/infra/decision-email-blocking-protocol.md` | ✅ | AGENTS.md Section 3.5A |

**Gap**: Current `email-decision` CLI is feature-oriented (requires `--project`). Decision Inbox provides **operator surface** pattern (cross-project visibility, unified namespace).

---

## 4. Proposed CLI Commands

### 4.1 `asyncdev decision list`

List all pending decisions across projects (operator visibility).

```
asyncdev decision list [--project <project_id>] [--all] [--status <status>]
```

**Output Format**:
```
Pending Decisions:

| Request ID        | Project         | Question                    | Status    | Blocking | Sent      |
|-------------------|-----------------|-----------------------------|-----------|----------|-----------|
| dr-20260422-001   | amazing-async   | Continue or pause?          | sent      | blocked  | 2026-04-22 23:30 |
| dr-20260421-003   | demo-project    | Use React or Vue?           | sent      | waiting  | 2026-04-21 18:15 |
```

**Key difference from `email-decision list`**:
- `--all` flag for cross-project listing
- Shows blocking state (blocked/waiting/clear)
- Operator-focused output format

### 4.2 `asyncdev decision show`

Show detailed decision context with blocking state.

```
asyncdev decision show --request <request_id> [--project <project_id>]
```

**Output Sections**:
- Decision request details (question, options, recommendation)
- Blocking state (BLOCKED/WAITING_DECISION/CLEAR)
- RunState integration (decisions_needed, decision_request_pending)
- Reply format hint
- Linked artifacts (ExecutionPack, RunState)
- Resolution status (if resolved)

### 4.3 `asyncdev decision reply`

Process a reply to a decision request (operator action).

```
asyncdev decision reply --request <request_id> --command "DECISION A" [--project <project_id>]
```

**Behavior**:
- Validates reply against request options
- Updates DecisionRequestStore status to RESOLVED
- Syncs to RunState via `sync_reply_to_runstate`
- Clears blocking state if all decisions resolved
- Shows next recommended action

**Note**: This wraps existing `email-decision reply` functionality with operator-friendly interface.

### 4.4 `asyncdev decision wait`

Poll for decision reply (blocking protocol integration).

```
asyncdev decision wait --request <request_id> [--project <project_id>] [--interval 60] [--timeout 3600]
```

**Behavior** (per Feature 064 blocking protocol):
- Polls webhook for reply at specified interval
- Blocks terminal until reply received or timeout
- Auto-processes reply when found
- Updates RunState and clears blocking state
- Returns when resolved

**Key**: This provides the blocking protocol's `decision-wait` command suggested in Feature 064 spec.

### 4.5 `asyncdev decision history`

Show resolved decision history.

```
asyncdev decision history [--project <project_id>] [--all] [--limit 10]
```

**Output Format**:
```
Resolved Decisions:

| Request ID        | Project         | Resolution      | Resolved At          |
|-------------------|-----------------|-----------------|----------------------|
| dr-20260422-001   | amazing-async   | DECISION A      | 2026-04-22 23:45     |
| dr-20260421-003   | demo-project    | DECISION B      | 2026-04-21 19:00     |
```

---

## 5. Integration Points

### 5.1 Existing Infrastructure

| Component | Integration Method |
|-----------|-------------------|
| DecisionRequestStore | Direct usage for listing/loading requests |
| decision_sync | `sync_reply_to_runstate` for reply processing |
| decision_waiting_session | `check_blocking_state` for blocking state display |
| webhook_poller | `PollingDaemon` for wait command |
| email-decision CLI | `decision reply` wraps `email-decision reply` |

### 5.2 Data Sources

- **DecisionRequestStore** (`.runtime/decision-requests/*.json`) - Decision request files
- **RunState** (`projects/{project_id}/runstate.md`) - Blocking state, decisions_needed
- **Webhook** (resend inbound webhook) - Async reply polling

### 5.3 State Flow

```
Decision request sent → RunState.phase = blocked
                        → RunState.decision_request_pending set
                        → Decision Inbox surfaces to operator
                        → Operator replies or polls for reply
                        → Reply processed → RunState.phase = planning
                        → Execution continues
```

---

## 6. Implementation Approach

### 6.1 Phase A — CLI Foundation

Create CLI command module:
- `cli/commands/decision.py`
- Implement `list`, `show`, `reply`, `wait`, `history` commands
- Integrate with existing `decision_request_store`, `decision_sync`, `decision_waiting_session`

### 6.2 Phase B — Cross-Project Query

- Scan all projects in `projects/` directory for decision requests
- Aggregate pending decisions across projects
- Show blocking state from each project's RunState

### 6.3 Phase C — Blocking Protocol Integration

- Wire `wait` command to `poll_and_wait` from `decision_waiting_session`
- Integrate with webhook poller for async reply detection
- Update RunState after reply received

---

## 7. Acceptance Criteria

### AC-001 Cross-Project Listing
`asyncdev decision list --all` shows pending decisions from all projects.

### AC-002 Blocking State Display
`asyncdev decision show` displays blocking state (BLOCKED/WAITING_DECISION/CLEAR).

### AC-033 Reply Processing
`asyncdev decision reply` updates DecisionRequestStore and RunState.

### AC-004 Wait Command
`asyncdev decision wait` polls webhook and processes reply when found.

### AC-005 History Query
`asyncdev decision history` shows resolved decision records.

### AC-006 Operator Namespace
Commands under `asyncdev decision` namespace (not `email-decision`).

---

## 8. Non-Goals

This feature does NOT:
- Replace `email-decision` commands (both namespaces coexist)
- Create a dashboard UI (CLI-only for Phase 1)
- Implement new decision types (uses existing DecisionType)
- Handle automatic decision escalation (uses existing escalation policy)

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Cross-project scan slow | Use efficient glob patterns, limit to pending status |
| Blocking state inconsistent | Show last known state, allow reconciliation |
| Webhook unavailable | Fallback to manual reply command |

---

## 10. Definition of Done

The Decision Inbox is complete when:
1. All five CLI commands implemented
2. Cross-project decision listing works
3. Blocking state display integrated
4. Wait command polls webhook successfully
5. Tests cover list/show/reply/wait/history scenarios
6. Documentation updated in README.md

---

## 11. Architecture Alignment

This spec aligns with the platform architecture (Phase 3):

> "Phase 3 — Decision Surface: Add Decision Inbox to support low-interruption human-in-the-loop operation."

The Decision Inbox provides the recommended second operator surface that:
- Complements Recovery Console (Phase 2)
- Integrates blocking protocol (Feature 064)
- Unifies decision visibility across projects
- Supports asynchronous human-in-the-loop operation

---

## 12. Namespace Design

| Namespace | Purpose | Commands |
|-----------|---------|----------|
| `asyncdev email-decision` | Feature-oriented (send requests) | create, send, check-replies, stats |
| `asyncdev decision` | Operator-oriented (manage decisions) | list, show, reply, wait, history |

**Design rationale**: Two namespaces coexist - `email-decision` for feature-level actions (creating/sending), `decision` for operator-level actions (managing/resolving).

---

## 13. Suggested Implementation Order

1. Create `cli/commands/decision.py` with `list` command
2. Implement `show` command with blocking state integration
3. Implement `reply` command (wraps email-decision reply)
4. Implement `wait` command with webhook polling
5. Implement `history` command for resolved decisions
6. Add tests
7. Update documentation

---

## 14. Status

**Proposed** — Ready for implementation decision.