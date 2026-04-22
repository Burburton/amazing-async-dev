# Decision Waiting Mechanism

## Status

Working - emails send via Resend, RunState blocks on pending decisions.

## Flow

```
email-decision create --send
    ↓
apply_resend_config_from_file() → sets ASYNCDEV_DELIVERY_MODE=resend
    ↓
EmailSender.send_decision_request() → calls Resend API
    ↓
Message ID returned → stored in decision_request.message_id
    ↓
sync_decision_to_runstate() → RunState.phase = blocked
    ↓
RunState.decisions_needed += decision entry
    ↓
RunState.decision_request_pending = request_id
```

## Blocking Check

```python
# recovery_classifier.py
if decisions_needed:
    return RecoveryClassification.AWAITING_DECISION

# resume eligibility
eligibility = NEEDS_DECISION  # blocks automatic resume
```

## Resolution Path

```
Human replies via email
    ↓
webhook_poller processes reply
    ↓
sync_reply_to_runstate() → removes from decisions_needed
    ↓
phase → planning (or based on reply command)
    ↓
resume_next_day → continues loop
```

## CLI Commands

```bash
# Send decision request
asyncdev email-decision create --project <id> --feature <id> \
    --question "..." --options "A:...,B:..." --recommendation A --send

# Check pending decisions
asyncdev email-decision list --project <id> --status sent

# Reply manually (if webhook not running)
asyncdev email-decision reply --project <id> --id <request_id> --command "DECISION A"

# Poll for replies (daemon mode)
asyncdev listen start --interval 60

# Resume after decision resolved
asyncdev resume-next-day continue-loop --project <id> --decision approve
```

## Key Fix Applied

`apply_resend_config_from_file()` now sets `ASYNCDEV_DELIVERY_MODE=resend` when config has valid api_key and from_email.

Previously: Only set RESEND_* vars, delivery_mode defaulted to mock_file.
Now: Automatically enables resend delivery mode.