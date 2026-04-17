# Feature 053 — Resend Email Provider Integration
## Implementation Plan

### Phase A: Outbound Integration (Priority: HIGH)

#### Task A1: Create ResendProvider module
- File: `runtime/resend_provider.py`
- Classes:
  - `ResendConfig` - API key, from_email, webhook_secret
  - `ResendProvider` - Send emails via Resend API
- Functions:
  - `send_email()` - POST to https://api.resend.com/emails
  - `build_email_payload()` - Construct JSON payload
  - `parse_response()` - Extract message ID
- Environment variables:
  - `RESEND_API_KEY`
  - `RESEND_FROM_EMAIL`

#### Task A2: Integrate with EmailSender
- Modify: `runtime/email_sender.py`
- Add `delivery_mode: resend`
- Add `_send_resend()` method
- Add `is_resend_configured()` to EmailConfig

#### Task A3: Persist message metadata
- Modify: `runtime/decision_request_store.py`
- Add `resend_message_id` field
- Add `resend_sent_at` field
- Add `mark_sent_via_resend()` method

#### Task A4: Create schema
- File: `schemas/resend-config.schema.yaml`
- Fields: api_key, from_email, webhook_secret, sandbox_mode

---

### Phase B: Inbound Handling (Priority: HIGH)

#### Task B1: Create webhook handler
- File: `runtime/resend_webhook_handler.py`
- Functions:
  - `handle_email_received_event()` - Parse inbound email
  - `extract_reply_from_webhook()` - Get reply text
  - `find_request_by_message_id()` - Link to original request
  - `verify_webhook_signature()` - Security check

#### Task B2: Connect to reply pipeline
- Import: `runtime.reply_parser`, `runtime.decision_sync`
- Flow:
  ```
  webhook → parse reply → find request → sync to RunState → reply pipeline
  ```

#### Task B3: Create webhook endpoint (optional)
- File: `cli/webhooks/resend.py` (if needed)
- Or document webhook configuration

---

### Phase C: CLI & Testing (Priority: HIGH)

#### Task C1: Create CLI commands
- File: `cli/commands/resend_auth.py`
- Commands:
  - `setup` - Configure API key
  - `test-send` - Send test email
  - `status` - Check configuration
  - `webhook-info` - Show webhook setup instructions

#### Task C2: Register CLI
- Modify: `cli/asyncdev.py`
- Add: `app.add_typer(resend_auth.app, name="resend-auth")`

#### Task C3: Create tests
- File: `tests/test_resend_provider.py`
- Tests:
  - ResendConfig loading
  - Payload building
  - Mock send (no real API call)
  - Webhook parsing
  - Message ID persistence

#### Task C4: Integration tests
- Test: EmailSender with resend mode
- Test: Failure handling integration

---

### Phase D: Documentation & Completion

#### Task D1: Update roadmap spec
- Add Feature 053 to roadmap
- Update recommended execution order

#### Task D2: Create execution result
- File: `docs/infra/feature-053-execution-result.md`
- Document: All deliverables, tests, verification

---

### Parallel Execution Opportunities

Tasks can be parallelized as follows:

| Parallel Group | Tasks |
|----------------|-------|
| Group 1 | A1, A4, C1 (create modules) |
| Group 2 | A2, A3 (integration) |
| Group 3 | B1, B2 (inbound) |
| Group 4 | C2, C3, C4 (CLI & tests) |
| Group 5 | D1, D2 (docs) |

---

### Implementation Order (Sequential)

```
A1 → A4 → A2 → A3 → B1 → B2 → C1 → C2 → C3 → C4 → D1 → D2
```

Or parallel:
```
[A1, A4, C1] → [A2, A3] → [B1, B2] → [C2, C3, C4] → [D1, D2]
```

---

### Verification Points

1. After A2: EmailSender can use resend mode
2. After A3: Message ID persisted correctly
3. After B2: Reply pipeline connected
4. After C3: All tests pass
5. After D2: Feature complete

---

### Expected Test Count

- ResendProvider: ~15 tests
- Webhook handler: ~10 tests
- Integration: ~5 tests
- Total new tests: ~30

---

### Dependencies on External Resources

- Resend API documentation (https://resend.com/docs)
- Resend Python SDK reference
- Webhook event payload format

---

### Estimated Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| A | A1-A4 | 1.5 hours |
| B | B1-B3 | 1.5 hours |
| C | C1-C4 | 1.5 hours |
| D | D1-D2 | 0.5 hours |
| **Total** | | **4.5 hours** |