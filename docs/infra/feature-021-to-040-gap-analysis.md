# Gap Analysis: Feature 021 → Roadmap Features 040-043

## Document Purpose

Compare existing Feature 021 (Email Decision Channel) implementation against Roadmap Spec (Features 040-043) requirements to identify gaps requiring refinement before proceeding to Feature 044+.

---

## Executive Summary

**Critical Finding**: Feature 021 (Email Decision Channel) and `RunState.decisions_needed` operate as **two separate, non-integrated systems**.

- `DecisionRequestStore` stores decision requests in `.runtime/decision-requests/*.json`
- `RunState.decisions_needed` is an array managed directly by `resume_next_day`
- Email reply processing updates `DecisionRequestStore` only
- Resume logic reads `RunState.decisions_needed` only
- **No synchronization between the two systems**

This disconnect means:
1. Email decision channel works for outbound/inbound
2. But decisions don't affect RunState
3. Resume logic ignores email decision state
4. Canonical loop cannot continue from email replies

---

## Gap Analysis by Feature

### Feature 040 — Foundation Gaps

| Roadmap Requirement | Feature 021 Status | Gap Level | Notes |
|---------------------|-------------------|-----------|-------|
| Email-first channel concept | ✅ Implemented | NONE | Concept exists |
| Decision-request object/schema | ✅ Implemented | NONE | `decision-request.schema.yaml` complete |
| Decision-request artifact location | ✅ Implemented | NONE | `.runtime/decision-requests/*.json` |
| Minimal email template for decision requests | ✅ Implemented | NONE | `email_sender._build_body()` |
| Minimal status-report template | ❌ NOT IMPLEMENTED | **HIGH** | Only decision emails, no pure status reports |
| Send mechanism | ✅ Implemented | NONE | SMTP + mock_file + console |
| Linkage to project/run/execution context | ⚠️ Partial | **HIGH** | Missing RunState sync |
| Distinguish email types | ⚠️ Partial | **MEDIUM** | Only decision emails implemented |

**Gaps for Feature 040:**
1. **Status-report email template missing** - roadmap distinguishes "informational report" vs "decision request" vs "approval request" vs "blocker notice"
2. **RunState linkage missing** - decision requests not synced with `RunState.decisions_needed`

---

### Feature 041 — Decision Request Content Contract Gaps

| Roadmap Requirement | Feature 021 Status | Gap Level | Notes |
|---------------------|-------------------|-----------|-------|
| Required sections for decision requests | ✅ Implemented | NONE | Schema has all required fields |
| Required sections for blocker emails | ⚠️ Partial | **LOW** | Schema supports, but no blocker-specific template |
| Option list structure | ✅ Implemented | NONE | `options[]` with id, label, description |
| Recommended option structure | ✅ Implemented | NONE | `recommendation` field |
| Timeout/default behavior field | ✅ Implemented | NONE | `expires_at` field |
| Reply instruction field | ✅ Implemented | NONE | `reply_format_hint` field |
| Concise executive summary rule | ⚠️ Partial | **MEDIUM** | Email body could be more concise |
| Anti-patterns for noisy emails | ❌ NOT DOCUMENTED | **LOW** | No explicit anti-pattern guidance |

**Gaps for Feature 041:**
1. **Email content could be more concise** - matches roadmap's "one-screen summary target"
2. **No explicit blocker email template** - roadmap distinguishes blocker notices
3. **No content contract documentation** - roadmap asks for lint/check rules

---

### Feature 042 — Reply Parsing & Decision Extraction Gaps

| Roadmap Requirement | Feature 021 Status | Gap Level | Notes |
|---------------------|-------------------|-----------|-------|
| Define supported reply intents | ✅ Implemented | NONE | DECISION, APPROVE, DEFER, RETRY, CONTINUE |
| Define reply grammar/parsing rules | ✅ Implemented | NONE | `reply_parser.py` with regex patterns |
| Parse structured replies | ✅ Implemented | NONE | `parse_reply()` function |
| Validate against request | ✅ Implemented | NONE | `validate_reply()` checks options |
| Persist parsed decision artifact | ✅ Implemented | NONE | `create_reply_record()` |
| Record confidence/parse status | ✅ Implemented | NONE | `validation_status` field |
| Detect ambiguous replies | ✅ Implemented | NONE | Invalid syntax handling |

**Gaps for Feature 042:**
- **No significant gaps** - implementation matches roadmap requirements

---

### Feature 043 — Decision Application & Continuation Resume Gaps (CRITICAL)

| Roadmap Requirement | Feature 021 Status | Gap Level | Notes |
|---------------------|-------------------|-----------|-------|
| Map parsed decision to continuation behavior | ❌ NOT DONE | **CRITICAL** | No mapping logic |
| Update runstate from reply | ❌ NOT DONE | **CRITICAL** | Reply updates DecisionRequestStore only |
| Update continuation state | ❌ NOT DONE | **CRITICAL** | No sync mechanism |
| Record decision provenance | ⚠️ Partial | **HIGH** | Stored in DecisionRequestStore, not RunState |
| Continue canonical loop after valid reply | ❌ NOT DONE | **CRITICAL** | Resume logic ignores email decisions |
| Preserve low-interruption model | ⚠️ Partial | **HIGH** | Manual reply command needed |

**Gaps for Feature 043 (CRITICAL):**
1. **RunState sync missing** - email reply doesn't update `RunState.decisions_needed`
2. **Resume integration missing** - `resume_next_day` doesn't read from `DecisionRequestStore`
3. **Continuation behavior missing** - no mapping from reply to next action
4. **Canonical loop disconnect** - email channel isolated from workflow engine

---

## Integration Architecture Analysis

### Current State (Disconnected)

```
┌─────────────────────────┐          ┌─────────────────────────┐
│ DecisionRequestStore    │          │ RunState                │
│ .runtime/               │   ❌      │ decisions_needed: []    │
│ decision-requests/*.json│ ← NO →   │ current_phase: executing│
│                         │   SYNC   │                         │
└─────────────────────────┘          └─────────────────────────┘
         ↓                                     ↓
    email_decision CLI                   resume_next_day CLI
         ↓                                     ↓
    Create Request → Send               Read RunState.decisions_needed
         ↓                                     ↓
    Reply Received →                     Process decision
    DecisionRequestStore.status=resolved         ↓
         ↓                                     ↓
    (DecisionRequestStore updated)       (RunState updated)
    
    ❌ DECISION NEVER REACHES RUNSTATE ❌
```

### Expected State (Connected)

```
┌─────────────────────────┐  SYNC   ┌─────────────────────────┐
│ DecisionRequestStore    │ ←───→   │ RunState                │
│ .runtime/               │         │ decisions_needed: []    │
│ decision-requests/*.json│         │ decision_request_pending│
│                         │         │ current_phase: blocked  │
└─────────────────────────┘         └─────────────────────────┘
         ↓                                     ↓
    Create Request                  Resume reads both
         ↓                                     ↓
    1. Save to DecisionRequestStore  1. Check DecisionRequestStore
    2. Append to RunState.decisions_needed  2. Check RunState.decisions_needed
    3. Set RunState.phase = blocked  3. Sync both sources
         ↓                                     ↓
    Email Sent                          Valid reply →
         ↓                                     ↓
    Reply Received                  1. Mark DecisionRequestStore resolved
         ↓                          2. Remove from RunState.decisions_needed
    DecisionRequestStore.status = resolved    3. Update RunState.last_action
                                              4. Set phase for continuation
         ↓                                     ↓
    ✅ DECISION PROPAGATES TO RUNSTATE ✅
```

---

## Required Refinements Summary

### High-Priority Refinements (Critical for Feature 043)

| Refinement | Description | Impact |
|------------|-------------|--------|
| **RunState sync** | Sync DecisionRequestStore with RunState.decisions_needed | Enables resume from email |
| **Resume integration** | `resume_next_day` reads from DecisionRequestStore | Enables canonical loop continuation |
| **Continuation mapping** | Map reply command to RunState action | Enables workflow continuation |

### Medium-Priority Refinements (Feature 040)

| Refinement | Description | Impact |
|------------|-------------|--------|
| **Status-report template** | Add pure status email template | Enables informational emails |
| **Email type distinction** | Mark emails as decision/info/blocker | Improves clarity |
| **Content conciseness** | Compress email body format | Improves readability |

### Low-Priority Refinements (Feature 041)

| Refinement | Description | Impact |
|------------|-------------|--------|
| **Blocker email template** | Specific template for blocker notices | Improves blocker handling |
| **Content contract docs** | Document anti-patterns and rules | Improves quality |

---

## Recommended Implementation Order

1. **Phase A: Core Integration (Feature 043)**
   - Implement RunState ↔ DecisionRequestStore sync
   - Update `resume_next_day` to read from both sources
   - Add reply → RunState action mapping
   - Test full loop: decision request → email → reply → resume

2. **Phase B: Foundation Refinement (Feature 040)**
   - Add status-report email template
   - Add email type classification
   - Link decision requests to RunState context

3. **Phase C: Content Quality (Feature 041)**
   - Refine email content format
   - Add blocker email template
   - Document content contract

---

## Validation Questions

After refinements, the system should answer:

1. ✅ Can a decision request sync to RunState.decisions_needed?
2. ✅ Can resume_next_day read from DecisionRequestStore?
3. ✅ Can an email reply update RunState?
4. ✅ Can the canonical loop continue after email reply?
5. ✅ Are informational status reports supported?

---

## Conclusion

Feature 021 provides a solid foundation but is **not integrated with the workflow engine**. The primary work needed is:

- **Sync mechanism** between DecisionRequestStore and RunState
- **Resume integration** for email decision continuation
- **Status-report support** for informational emails

Once these refinements are complete, Features 040-043 will be ready, and Feature 044 (High-Signal Reporting) can proceed.