# Feature 058 — Webhook Auto-Polling & Decision Continuation

## Status
`complete`

## Objective
Automate the webhook polling and decision continuation loop, completing the async human decision channel. Currently, replies are stored in Cloudflare Worker KV but require manual CLI commands to process. This feature enables automatic polling, synchronization, and execution resume.

---

## Problem Statement

Current flow (manual gaps):
```
发送邮件 → 用户回复 → Webhook存储 → [手动check-inbox] → [手动process] → [手动resume]
```

Expected flow (automatic):
```
发送邮件 → 用户回复 → Webhook存储 → [自动轮询] → [自动同步RunState] → [自动resume]
```

**The gap**: Feature 053-054 completed outbound automation, but inbound automation remains manual.

---

## Scope

### In Scope

1. **Webhook polling module**
   - Poll Cloudflare Worker `/pending-decisions` endpoint
   - Configurable polling interval (default: 60 seconds)
   - Detect new replies and trigger processing

2. **Auto-sync to RunState**
   - On reply detected, call `sync_reply_to_runstate()`
   - Update DecisionRequestStore status to RESOLVED
   - Clear `decision_request_pending` field

3. **Continuation trigger**
   - After sync, trigger appropriate next action:
     - DECISION/APPROVE → resume execution
     - DEFER → adjust timeline
     - REJECT → pause/replan
   - Integration with `apply_email_resolution_to_runstate()`

4. **Listen CLI command**
   - `asyncdev listen` - continuous polling daemon
   - `asyncdev listen --once` - single poll cycle
   - `asyncdev listen --interval 30` - custom interval

5. **Polling configuration**
   - Add to resend-config.json: `polling_enabled`, `polling_interval`
   - Environment variable: `ASYNCDEV_POLLING_INTERVAL`

### Out of Scope

1. Real-time WebSocket push (future feature)
2. Mobile push notifications
3. Multi-channel polling (Slack, etc.)

---

## Dependencies

| Dependency | Feature | Status |
|------------|---------|--------|
| Webhook endpoint | Feature 053 | ✅ Complete |
| check_inbox CLI | Feature 053 | ✅ Complete |
| decision_sync | Feature 043 | ✅ Complete |
| reply_parser | Feature 042 | ✅ Complete |
| reply_action_mapper | Feature 043 | ✅ Complete |
| auto_email_trigger | Feature 054 | ✅ Complete |

---

## Architecture

### Polling Flow

```
asyncdev listen --project my-product
          ↓
┌─────────────────────────────────────┐
│ Poll Loop (every 60s)               │
│ GET webhook_url/pending-decisions   │
└─────────────────────────────────────┘
          ↓ (if decisions found)
┌─────────────────────────────────────┐
│ For each decision:                  │
│ - Match to request_id               │
│ - Parse reply                       │
│ - Call sync_reply_to_runstate()     │
│ - Update DecisionRequestStore       │
│ - Clear from Worker KV              │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│ Continuation Trigger                │
│ - Check reply type                  │
│ - Set current_phase                 │
│ - Log transition                    │
│ - Optionally trigger run-day        │
└─────────────────────────────────────┘
```

### Decision Processing

```python
pending_decision = {
    "id": "dr-20260418-001",
    "from": "user@example.com",
    "option": "A",
    "comment": "Proceed with Option A",
    "receivedAt": "2026-04-18T10:30:00"
}

# Match to request
request_id = pending_decision["id"]  # dr-20260418-001

# Parse reply
parsed = {
    "reply_value": "DECISION A",
    "parsed_result": {
        "command": "DECISION",
        "argument": "A",
    }
}

# Sync to RunState
runstate = sync_reply_to_runstate(request_id, parsed, runstate)

# Mark resolved
store.mark_resolved(request_id, resolution="DECISION A")

# Clear from webhook
DELETE webhook_url/pending-decisions/{request_id}
```

---

## Deliverables

1. `runtime/webhook_poller.py` - Polling and processing module
2. `cli/commands/listen.py` - Listen CLI command
3. Updated `runtime/resend_provider.py` - Add polling config fields
4. `tests/test_webhook_poller.py` - Poll logic tests
5. Feature spec execution result

---

## Acceptance Criteria

### Must Pass

1. ✅ Webhook polling detects new replies
2. ✅ Reply matched to correct decision request
3. ✅ RunState updated with reply resolution
4. ✅ DecisionRequestStore marked RESOLVED
5. ✅ Webhook KV cleared after processing
6. ✅ Phase transition set based on reply type
7. ✅ Tests pass for polling logic

### Should Pass

1. ✅ `asyncdev listen` runs continuously
2. ✅ `asyncdev listen --once` runs single cycle
3. ✅ Custom polling interval configurable
4. ✅ Graceful shutdown on SIGINT

---

## Implementation Phases

### Phase A: Polling Module
- Create `webhook_poller.py`
- Implement `poll_pending_decisions()`
- Implement `process_pending_decision()`
- Implement `run_poll_cycle()`

### Phase B: Auto-Sync Integration
- Connect to `decision_sync.sync_reply_to_runstate()`
- Connect to `DecisionRequestStore.mark_resolved()`
- Implement webhook KV clearing

### Phase C: Listen CLI
- Create `cli/commands/listen.py`
- Implement daemon mode
- Implement single-cycle mode
- Add signal handling

### Phase D: Configuration & Testing
- Add polling config to resend-config.json
- Test suite
- Execution result

---

## Risks

| Risk | Mitigation |
|------|------------|
| Duplicate processing | Check if request already RESOLVED |
| Network failures | Retry with exponential backoff |
| Race conditions | Lock RunState during sync |
| Missing request match | Skip unmatched decisions, log warning |

---

## Estimated Effort

- Phase A: 1-2 hours
- Phase B: 1 hour
- Phase C: 1-2 hours
- Phase D: 1 hour
- Total: 4-6 hours