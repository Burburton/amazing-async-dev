# Async Decision Channel - Email-first

Feature 021: Asynchronous Human Decision Channel (Email-first)

---

## Overview

The async decision channel enables `amazing-async-dev` to pause at true human-decision points, notify the operator asynchronously by email (or mock), accept structured replies, and continue execution without requiring synchronous terminal presence.

This feature works with Feature 020's policy layer to determine when to pause and send decision requests.

---

## Components

| Component | Purpose |
|-----------|---------|
| `DecisionRequestStore` | Lifecycle management for decision requests |
| `EmailSender` | SMTP + mock file delivery |
| `ReplyParser` | Strict grammar reply parsing |
| `EmailConfig` | Email configuration (env + config file) |

---

## Decision Request Lifecycle

```
pending → sent → reply_received → resolved
                    ↓
              reply_invalid → retry
                    ↓
              expired
```

---

## Reply Commands (Strict Grammar)

| Command | Syntax | Example |
|---------|--------|---------|
| DECISION | `DECISION <option-id>` | `DECISION A` |
| APPROVE | `APPROVE <action-type>` | `APPROVE PUSH` |
| DEFER | `DEFER` | `DEFER` |
| RETRY | `RETRY` | `RETRY` |
| CONTINUE | `CONTINUE` | `CONTINUE` |

Rules:
- Case insensitive
- Whitespace flexible
- Only one command per reply

---

## CLI Commands

```bash
# Create decision request
asyncdev email-decision create --project my-app --feature 001 \
    --question "Use YAML or JSON?" --options "A:YAML,B:JSON" \
    --recommendation "A" --send

# List requests
asyncdev email-decision list --project my-app
asyncdev email-decision list --project my-app --status sent

# Show details
asyncdev email-decision show --project my-app --id dr-20260412-001

# Send email
asyncdev email-decision send --project my-app --id dr-20260412-001

# Process reply
asyncdev email-decision reply --project my-app --id dr-20260412-001 --command "DECISION A"

# Check for replies
asyncdev email-decision check-replies --project my-app

# Mark expired
asyncdev email-decision expire --project my-app

# Statistics
asyncdev email-decision stats --project my-app
```

---

## Email Delivery Modes

| Mode | Description |
|------|-------------|
| `mock_file` | Write to `.runtime/email-outbox/` (default) |
| `console` | Output to stdout |
| `smtp` | Real SMTP send (requires config) |

---

## Configuration

### Non-sensitive config (`.runtime/email-config.yaml`)

```yaml
delivery_mode: mock_file
mock_outbox_path: .runtime/email-outbox
email_subject_prefix: "[async-dev]"
smtp_host: smtp.gmail.com  # optional
smtp_port: 587
smtp_use_tls: true
to_address: operator@example.com
```

### Sensitive config (environment variables)

```bash
ASYNCDEV_SMTP_HOST=smtp.gmail.com
ASYNCDEV_SMTP_PORT=587
ASYNCDEV_SMTP_USERNAME=your-email@gmail.com
ASYNCDEV_SMTP_PASSWORD=your-password
ASYNCDEV_FROM_ADDRESS=asyncdev@example.com
ASYNCDEV_TO_ADDRESS=operator@example.com
```

---

## Integration Points

- Feature 020 `pause_reason_category`
- Feature 020 `check_must_pause_conditions()`
- RunState `decisions_needed`
- Resume logic

---

## Acceptance Criteria

- ✅ True human decision pauses generate decision request
- ✅ Decision requests delivered by mock_file (first version)
- ✅ Operator can reply using structured format
- ✅ Valid replies parsed and applied
- ✅ Invalid replies rejected safely
- ✅ Workflow can continue after valid reply
- ✅ Documentation explains email-first decision loop

---

## Mock Email Example

File: `.runtime/email-outbox/dr-20260412-001.md`

```
Subject: [async-dev] Decision needed: my-app / feature-001 [dr-20260412-001]

Decision Request: dr-20260412-001

Question: Use YAML or JSON for schema format?

Options:
  [A] YAML - Human-readable, good for documentation
  [B] JSON - Machine-readable, better for tooling

Recommendation: A - YAML is more readable

If deferred: Can proceed with YAML temporarily

Reply format: DECISION A, DECISION B, DEFER, RETRY

---
Request ID: dr-20260412-001
Sent at: 2026-04-12T10:30:00
```

---

## Future Enhancements

- Real SMTP sending (requires email service)
- IMAP reply checking
- Slack/Telegram channels
- Natural language reply parsing