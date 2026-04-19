# Feature 054 — Auto Email Decision Trigger

## Status
`complete`

## Objective
Automatically trigger email decision requests when `decisions_needed` becomes non-empty, eliminating the need for manual `email-decision create --send` calls. This enables true low-interruption canonical loop execution where AI can pause for human decisions without manual intervention.

---

## Problem Statement

During the amazing-briefing-viewer development session, we observed that:

1. **Manual trigger required**: When AI encounters a decision point and populates `RunState.decisions_needed`, it must manually call `email-decision create --send` to actually send the email
2. **No automatic integration**: The roadmap and canonical loop documentation don't define how email decisions should be auto-triggered
3. **Semi-automated loop**: The loop is "semi-automatic" - AI pauses, but human must manually check RunState and trigger email send
4. **False "low-interruption"**: The system claims low-interruption but requires manual email triggering at each decision point

**The gap**: Feature 053 completed the resend transport layer, but the integration layer (when to auto-send) remains undefined.

---

## Scope

### In Scope

1. **Auto-trigger mechanism**
   - Detect when `RunState.decisions_needed` becomes non-empty
   - Automatically create and send email decision request
   - Set `decision_request_pending` and `decision_request_sent_at`

2. **Policy mode integration**
   - Respect `policy_mode` (conservative/balanced/low_interruption)
   - Conservative: always auto-send
   - Balanced: auto-send for blockers and scope changes, prompt for technical decisions
   - Low-interruption: auto-send, use timeout defaults if no reply

3. **Trigger conditions**
   - `pause_reason_category` determines trigger behavior
   - Categories: `decision_required`, `blocker`, `scope_change`, `architecture`, `external_dependency`

4. **Integration points**
   - `run-day execute` should auto-trigger email when decisions_needed populated
   - `plan-day create` may generate decisions that need immediate escalation
   - External tool mode (OpenCode/Claude Code) should have same auto-trigger behavior

5. **Audit trail**
   - Record auto-trigger events in decision request store
   - Track trigger source (run-day, plan-day, manual)

### Out of Scope

1. Real-time webhook push to RunState (Feature 058 - future)
2. Mobile push notifications
3. Multi-channel decision routing (Slack, etc.)
4. Decision priority queuing

---

## Dependencies

| Dependency | Feature | Status |
|------------|---------|--------|
| Decision request store | Feature 021 | ✅ Complete |
| Email sender | Feature 021 | ✅ Complete |
| Decision sync layer | Feature 043 | ✅ Complete |
| Resend provider | Feature 053 | ✅ Complete |
| Policy mode | Feature 020 | ✅ Complete |
| RunState schema | Core | ✅ Complete |

---

## Deliverables

1. `runtime/auto_email_trigger.py` - Auto-trigger detection and execution module
2. `cli/commands/run_day.py` update - Add auto-trigger integration
3. `cli/commands/plan_day.py` update - Add auto-trigger for planning decisions
4. `tests/test_auto_email_trigger.py` - Trigger logic tests
5. Updated `AGENTS.md` - Document auto-trigger behavior in canonical loop
6. Feature spec execution result

---

## Architecture

### Trigger Detection Flow

```
RunState.decisions_needed populated
         ↓
auto_email_trigger.check_and_trigger()
         ↓
┌─────────────────────────────────────┐
│ Policy Mode Check                   │
│ - conservative: always send         │
│ - balanced: check category          │
│ - low_interruption: always send     │
└─────────────────────────────────────┘
         ↓ (if should_send)
DecisionRequestStore.create_request()
         ↓
EmailSender.send_decision_request()
         ↓
sync_decision_to_runstate()
         ↓
RunState.decision_request_pending = request_id
RunState.decision_request_sent_at = timestamp
RunState.current_phase = blocked
```

### Policy Mode Behavior

| Policy | decision_required | blocker | scope_change | technical |
|--------|-------------------|---------|--------------|-----------|
| conservative | auto-send | auto-send | auto-send | auto-send |
| balanced | auto-send | auto-send | auto-send | manual (optional) |
| low_interruption | auto-send | auto-send | auto-send | auto-send + timeout default |

### Trigger Source Tracking

```yaml
trigger_source: "run_day_auto" | "plan_day_auto" | "manual_cli"
triggered_at: timestamp
policy_mode_at_trigger: "conservative" | "balanced" | "low_interruption"
auto_triggered: true | false
```

---

## Acceptance Criteria

### Must Pass

1. ✅ `decisions_needed` populated → email auto-sent (conservative mode)
2. ✅ Policy mode respected (balanced skips some categories)
3. ✅ Trigger source recorded in decision request
4. ✅ RunState updated with `decision_request_pending`
5. ✅ No duplicate emails for same decision entry
6. ✅ Manual CLI `email-decision create` still works as override
7. ✅ Tests pass for trigger logic

### Should Pass

1. ✅ External tool mode has same auto-trigger behavior
2. ✅ AGENTS.md documents auto-trigger integration
3. ✅ Timeout default behavior for low_interruption mode

---

## Implementation Phases

### Phase A: Core Trigger Logic
- Create `auto_email_trigger.py` module
- Implement `check_and_trigger()` function
- Policy mode filtering logic
- Trigger source tracking

### Phase B: Run-Day Integration
- Update `run_day.py` to call auto-trigger after state update
- Handle external tool mode integration
- Test with mock decisions

### Phase C: Plan-Day Integration
- Update `plan_day.py` for planning-phase decisions
- Handle decisions generated during planning

### Phase D: Documentation & Testing
- AGENTS.md updates
- Test suite
- Execution result

---

## Risks

| Risk | Mitigation |
|------|------------|
| Duplicate triggers | Check `decision_request_pending` before sending |
| Policy mode confusion | Clear documentation of each mode's behavior |
| Email flood (many decisions) | Batch decisions into single email or rate-limit |
| External tool mode disconnect | AGENTS.md clear rules for AI execution |

---

## Estimated Effort

- Phase A: 2-3 hours
- Phase B: 1-2 hours
- Phase C: 1-2 hours
- Phase D: 1-2 hours
- Total: 5-8 hours (1 day loop)

---

## Notes

This feature is critical for achieving the claimed "low-interruption" canonical loop. Without auto-trigger, the system requires manual intervention at every decision point, contradicting the design intent.

Priority: **P1** - Should be implemented before using async-dev for real product development.