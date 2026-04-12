# Execution Policy - Low-Interruption Workflow Automation

Feature 020: Low-Interruption Execution Policy / Autopilot Rules

---

## Overview

The execution policy system controls which workflow transitions can proceed automatically and which require human confirmation. This reduces unnecessary operator interruptions while preserving pause for meaningful decisions and risky actions.

---

## Policy Modes

| Mode | Description | Auto-Continue |
|------|-------------|---------------|
| `conservative` | Ask for confirmation on most transitions | execution_success only |
| `balanced` | Auto-continue safe transitions, pause for decisions/risky | safe transitions |
| `low_interruption` | Minimize interruptions, pause only blockers/risky | most transitions |

**Default mode: `balanced`**

---

## Auto-Continue Rules

### Conservative Mode
- `execution_success_to_review` - After successful execution, generate review pack

### Balanced Mode
- `execution_success_to_review` - After successful execution
- `review_pack_generated` - Review artifact ready
- `safe_state_advance` - Normal workflow progression
- `non_destructive_artifact_creation` - Safe internal artifact creation

### Low-Interruption Mode
- All balanced mode rules
- `next_safe_task_in_queue` - Proceed to next task
- `routine_cli_commands` - Routine CLI operations

---

## Must-Pause Conditions

These conditions **always pause** regardless of policy mode:

| Condition | Category | Required to Continue |
|-----------|----------|----------------------|
| Blocked items | blocker | Resolve blocker or alternative task |
| Scope change flag | scope_change | Acknowledge or revert |
| Git push requested | risky_action | Confirm push |
| Remote mutation | risky_action | Confirm external mutation |
| Irreversible archive | risky_action | Confirm archive operation |
| Batch multi-feature | risky_action | Confirm batch operation |
| External API side effect | risky_action | Confirm external action |
| Promotion externalization | risky_action | Confirm promotion |

### Decisions Handling
- In `conservative` and `balanced` mode: decisions pause workflow
- In `low_interruption` mode: decisions may auto-resolve

---

## Pause Reason Structure

When the system pauses, it provides structured information:

```
Category: decision_required
Summary: Pending decision on schema format
Why: RunState contains 1 unresolved decisions
Required to Continue: Make decision (approve/revise/defer) or use --force
Suggested Next Action: asyncdev resume-next-day continue-loop --decision approve
```

### Pause Categories

| Category | Color | Urgency | Icon |
|----------|-------|---------|------|
| decision_required | yellow | high | ⚠ |
| blocker | red | critical | 🔴 |
| risky_action | magenta | high | ⚡ |
| scope_change | orange | medium | ↔ |
| policy_boundary | blue | low | 📋 |

---

## CLI Commands

```bash
# Show current policy mode and rules
asyncdev policy show
asyncdev policy show --project my-app

# Set policy mode
asyncdev policy set --mode balanced
asyncdev policy set --project my-app --mode low_interruption

# List available modes
asyncdev policy modes

# Manage scope change flag
asyncdev policy scope-flag --set-flag true
asyncdev policy scope-flag --clear

# Manage pending risky actions
asyncdev policy risky-actions --list
asyncdev policy risky-actions --clear-all
```

---

## Integration Points

The policy system integrates with:

- `RunState.current_phase` - Phase-based transitions
- `RunState.decisions_needed` - Decision handling
- `RunState.blocked_items` - Blocker handling
- `RunState.scope_change_flag` - Scope change detection
- `RunState.policy_mode` - Current policy setting
- `RunState.pending_risky_actions` - Risky action queue
- `recovery_classifier` - Resume eligibility

---

## Example Workflow

### Conservative Mode (Default)
```
plan-day → manual confirmation → run-day → success → auto review → manual confirmation → resume-next-day
```

### Balanced Mode
```
plan-day → manual confirmation → run-day → success → auto review → auto safe state → resume-next-day (if no decisions)
```

### Low-Interruption Mode
```
plan-day → manual confirmation → run-day → success → auto review → auto next task (if no blockers/risky)
```

---

## Risky Action Detection

Risky actions are automatically detected and queued for confirmation:

| Action Type | Detection Trigger |
|-------------|-------------------|
| git_push | `action.type == git_push` |
| archive_irreversible | `action.irreversible == true` |
| batch_multi_feature | `action.scope == multi_feature` |
| external_api_mutation | `action.external == true && action.has_side_effects` |
| promotion_externalization | `action.type == promotion_externalization` |

---

## Scope Change Detection (v1)

Scope changes are detected via explicit flag in RunState:
- `scope_change_flag: true` - Task scope has changed
- Set via `asyncdev policy scope-flag --set-flag true`
- Clear via `asyncdev policy scope-flag --clear`

Future versions may include automatic diff detection.

---

## Acceptance Criteria (Feature 020)

- ✅ Ordinary safe transitions interrupt less often
- ✅ True decisions still cause pause (in conservative/balanced)
- ✅ Blockers still cause pause
- ✅ Risky external actions require explicit confirmation
- ✅ Interruption reasons are clearer (structured pause reason)
- ✅ Workflow smoothness improved without sacrificing control