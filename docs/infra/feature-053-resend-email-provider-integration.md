# Feature 053 — Resend Email Provider Integration

## Status
`complete`

## Objective
Integrate Resend as the real email transport/provider for the existing Email-First Human Decision & Reporting Channel, so the system can actually send and receive email through a production-oriented service.

---

## Problem Statement

The current email decision/reporting channel logic is complete (Features 043-049), but lacks a concrete production-oriented provider integration:

- Gmail OAuth2 SMTP blocked in restricted network environments (GFW interference)
- No real inbound email handling for reply processing
- Provider-specific metadata not persisted for audit trail
- Webhook/reply linkage not defined

---

## Scope

### In Scope
1. **Outbound email sending via Resend API**
   - Decision requests
   - Status reports
   - Blocker emails

2. **Inbound webhook handling**
   - Receive email.received events from Resend
   - Parse replies and link to original decision requests
   - Connect to existing reply pipeline (Feature 043)

3. **Provider metadata persistence**
   - Resend message ID (`id` from API response)
   - Sent timestamp
   - Delivered/opened events (optional)
   - Webhook event correlation

4. **Configuration & secrets**
   - `RESEND_API_KEY` environment variable
   - `RESEND_FROM_EMAIL` verified sender address
   - Webhook endpoint configuration

5. **Testing modes**
   - Mock/sandbox mode for development
   - Dry-run mode for preview

6. **Failure handling integration**
   - Connect to Feature 049 failure handling
   - Record Resend API errors
   - Handle rate limits

### Out of Scope
- Multi-provider abstraction (Feature 052 handles this)
- Other providers (Sendgrid, Mailgun, etc.)
- Email template customization (Feature 044 handles report format)

---

## Dependencies

| Dependency | Feature | Status |
|------------|---------|--------|
| Decision request store | Feature 021 | ✅ Complete |
| Reply parser | Feature 021 | ✅ Complete |
| Decision sync layer | Feature 043 | ✅ Complete |
| Status report builder | Feature 044 | ✅ Complete |
| Failure handling | Feature 049 | ✅ Complete |
| Audit trail | Feature 047 | ✅ Complete |

---

## Deliverables

1. `runtime/resend_provider.py` - Resend API client module
2. `runtime/resend_webhook_handler.py` - Inbound webhook processor
3. `cli/commands/resend_auth.py` - CLI commands for Resend setup
4. `tests/test_resend_provider.py` - Provider tests
5. `schemas/resend-config.schema.yaml` - Configuration schema
6. Updated `runtime/email_sender.py` - Add Resend delivery mode
7. Updated roadmap spec

---

## Acceptance Criteria

### Must Pass
1. ✅ Outbound emails sent via Resend API
2. ✅ Decision requests, status reports, blocker emails all supported
3. ✅ Resend message ID persisted in decision request record
4. ✅ Webhook handler receives and parses inbound replies
5. ✅ Reply linked to original decision request via message ID
6. ✅ Integration with existing reply pipeline (Feature 043)
7. ✅ API errors handled via Feature 049 failure handling
8. ✅ Mock/sandbox mode available for testing
9. ✅ Configuration via environment variables
10. ✅ Tests pass for all functionality
11. ✅ Interactive setup CLI with browser launch
12. ✅ Config file persistence (.runtime/resend-config.json)
13. ✅ Auto-load from config file on CLI commands

### Should Pass
1. 📋 Rate limit handling with retry
2. 📋 Delivered/opened event tracking (optional)
3. 📋 Webhook signature verification

---

## Architecture

### Outbound Flow

```
DecisionRequest → EmailSender → ResendProvider → Resend API
                                                      ↓
                                              Message ID returned
                                                      ↓
                                          Persisted in request record
```

### Inbound Flow

```
Resend Webhook → resend_webhook_handler → Parse reply → Find original request
                                              ↓
                                     Link via message ID → Reply pipeline
```

### Configuration

```yaml
# Environment variables
RESEND_API_KEY=re_xxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_WEBHOOK_SECRET=whsec_xxx (optional)

# Delivery mode
ASYNCDEV_DELIVERY_MODE=resend

# Config file (auto-created by interactive setup)
.runtime/resend-config.json
```

### Interactive Setup

```bash
# Interactive setup with browser launch
asyncdev resend-auth setup

# Direct setup (skip prompts)
asyncdev resend-auth setup --api-key re_xxx --from-email noreply@domain.com

# Check status (auto-loads from config file)
asyncdev resend-auth status

# Test connection
asyncdev resend-auth test
```

The config file is saved to `.runtime/resend-config.json` and excluded from git via `.gitignore`.

---

## Implementation Phases

### Phase A: Outbound Integration
- ResendProvider class
- EmailSender integration
- Message ID persistence
- Mock mode

### Phase B: Inbound Handling
- Webhook endpoint
- Reply parsing
- Request linking
- Integration with reply pipeline

### Phase C: Robustness & Testing
- Failure handling
- Tests
- Documentation

---

## Constraints

1. **Keep Resend-first** - No multi-provider abstraction
2. **Build on existing channel** - Preserve Features 043-049 compatibility
3. **Audit trail integrity** - Message ID linkage first-class
4. **Continuation compatibility** - Reply processing unchanged

---

## Risks

| Risk | Mitigation |
|------|------------|
| API key exposure | Store in env vars, never in code |
| Webhook endpoint security | Verify signatures |
| Rate limits | Implement retry with backoff |
| Network restrictions | Resend uses HTTPS (443), should pass |

---

## Estimated Effort

- Phase A: 2-3 hours
- Phase B: 2-3 hours
- Phase C: 1-2 hours
- Total: 5-8 hours

---

## References

- Resend API Docs: https://resend.com/docs
- Resend Python SDK: https://github.com/resend/resend-python
- Webhook Events: https://resend.com/docs/dashboard/webhooks