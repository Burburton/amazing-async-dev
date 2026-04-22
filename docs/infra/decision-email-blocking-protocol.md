# Decision Email Blocking Protocol (Feature 064)

## Status

`Implemented` - Protocol for blocking progress when decision emails are pending.

---

## 1. Problem Statement

The current system has a critical gap:

1. **Email sent → Phase set to `blocked` → AI ignores and continues anyway**
2. **TODO CONTINUATION directive overrides blocking state**
3. **No background polling mechanism auto-starts**
4. **Cross-session state lost - AI forgets waiting duty**

This violates AGENTS.md Section 3.5:
> **Never proceed when blocked or awaiting decision**

---

## 2. Core Protocol Rules

### Rule 1: Email Sent = Mandatory Block

When `asyncdev email-decision create --send` succeeds:

```
Email sent → RunState.current_phase = blocked
           → RunState.decision_request_pending = <request_id>
           → STOP all further progress
           → AI MUST NOT continue TODO tasks
```

**Violation**: Proceeding with TODO tasks after sending decision email.

### Rule 2: Block Overrides TODO CONTINUATION

The blocking state takes precedence over system directives:

| Priority | Source | Behavior |
|----------|--------|----------|
| 1 | RunState.phase = blocked | STOP, wait |
| 2 | System Directive TODO | Ignored if blocked |
| 3 | Other tasks | Deferred until unblocked |

**Rule**: When RunState shows `blocked` or `decision_request_pending`, AI responds:
> "RunState is blocked. Cannot proceed. Waiting for decision reply."

### Rule 3: Background Polling Auto-Start

When decision email sent, system MUST:

```python
# Auto-start polling (pseudo-code)
if runstate.get("decision_request_pending"):
    start_background_poller(interval=60, timeout=3600)
    poll_until_resolved()
```

Implementation options:
- **Option A**: CLI daemon `asyncdev listen start --interval 60`
- **Option B**: Embedded poller in session startup
- **Option C**: Webhook notification triggers session resume

### Rule 4: Cross-Session State Preservation

When session ends with pending decision:

```yaml
# RunState preservation
current_phase: blocked
decision_request_pending: dr-YYYYMMDD-XXX
decision_poll_required: true
awaiting_human_reply: true
```

When new session starts:

1. Check `RunState.decision_request_pending`
2. If present: Run `check-inbox pending` immediately
3. If replies found: Process them before any other work
4. If no replies: Announce waiting status, block progress

---

## 3. Blocking Gate Implementation

### 3.1 Session Startup Hook

Before any TODO continuation:

```python
def check_blocking_state(runstate):
    if runstate.get("current_phase") == "blocked":
        return "BLOCKED", runstate.get("decision_request_pending")
    if runstate.get("decision_request_pending"):
        return "WAITING_DECISION", runstate.get("decision_request_pending")
    return "CLEAR", None

# At session start:
status, request_id = check_blocking_state(runstate)
if status in ["BLOCKED", "WAITING_DECISION"]:
    poll_for_reply(request_id)
    if not reply_found:
        announce("Waiting for decision reply to {request_id}")
        STOP()  # Do not proceed
```

### 3.2 TODO CONTINUATION Override

When TODO CONTINUATION directive arrives:

```
Check RunState:
  - If phase = blocked → Respond "Blocked, cannot continue TODO"
  - If decision_request_pending → Poll inbox first
  - If clear → Proceed with TODO
```

**Never**: Proceed with TODO while `decision_request_pending` exists.

---

## 4. Polling Behavior

### 4.1 Poll Interval

| State | Interval | Timeout |
|-------|----------|---------|
| Initial poll | 10s | 60s |
| Background daemon | 60s | 3600s (1 hour) |
| Extended wait | 300s | 86400s (24 hours) |

### 4.2 Poll Actions

Each poll cycle:

1. `asyncdev check-inbox pending` - Get pending replies from webhook
2. If replies found → Process via `email-decision reply`
3. Update RunState via `sync_reply_to_runstate`
4. If all decisions resolved → `current_phase = planning`
5. Continue execution

### 4.3 Timeout Behavior

If poll timeout exceeded:

```yaml
RunState:
  decision_poll_timeout: true
  decision_pending_duration: <hours>
  escalation: "Human reply overdue - manual intervention required"
```

---

## 5. CLI Integration

### 5.1 Auto-Poll Command

New command (recommended):

```bash
asyncdev decision-wait --request <id> --interval 60 --timeout 3600
```

Behavior:
- Polls webhook for reply
- Blocks terminal until reply received or timeout
- Auto-processes reply when found
- Returns when resolved

### 5.2 Session Start Auto-Check

Add to session initialization:

```python
# In session startup
from runtime.decision_sync import get_pending_decision_status

pending = get_pending_decision_status(project_path)
if pending:
    print(f"[BLOCKED] Decision pending: {pending['request_id']}")
    poll_and_wait(pending['request_id'])
```

---

## 6. Integration with AGENTS.md

Add to AGENTS.md Section 3.5:

```markdown
### 3.5A Decision Email Blocking Protocol (Feature 064)

**Mandatory**: After sending decision email:
1. Set RunState.current_phase = blocked
2. Set RunState.decision_request_pending = <id>
3. STOP all progress immediately
4. Poll webhook for reply (interval 60s)
5. Wait until reply received or timeout

**Violation**: Proceeding with TODO tasks while decision_request_pending exists.

**System Directives**: TODO CONTINUATION does NOT override blocked state.
```

---

## 7. Acceptance Criteria

### AC-001: Block After Email Sent
After `email-decision create --send`, RunState.phase must be `blocked` and AI must not proceed.

### AC-002: TODO Continuation Honors Block
When TODO CONTINUATION arrives during blocked state, AI responds "Blocked, waiting for decision" and does not proceed.

### AC-003: Auto-Poll on Session Start
When session starts with decision_request_pending, system polls inbox before any other work.

### AC-004: Cross-Session Preservation
If session ends with pending decision, next session resumes waiting state.

### AC-005: Reply Processing Pipeline
When reply detected via poll, auto-process via email-decision reply and update RunState.

---

## 8. Implementation Notes

### Priority

This is **HIGH priority** - critical for async-dev integrity.

### Files to Modify

- `AGENTS.md` - Add blocking protocol rules
- `cli/commands/email_decision.py` - Add auto-poll trigger
- `runtime/session_startup_check.py` (new) - Cross-session state check
- `runtime/decision_wait_orchestrator.py` (new) - Polling orchestration

### Tests Required

- Test: Email sent → blocked state → TODO ignored
- Test: Session start → pending decision → auto-poll
- Test: Reply received → auto-process → phase updated
- Test: Cross-session state preservation

---

## 9. Summary

**Core Principle**: 

> **Email decision sent = progress blocked until human replies.**
> **TODO continuation does not override blocking state.**
> **Background polling is mandatory, not optional.**

Without this protocol, async-dev's email decision channel is just notification, not control.