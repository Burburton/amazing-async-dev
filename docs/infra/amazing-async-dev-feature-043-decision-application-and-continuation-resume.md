# Feature 043 — Decision Application & Continuation Resume

## 1. Feature Summary

### Feature ID
`043-decision-application-and-continuation-resume`

### Title
Decision Application & Continuation Resume

### Goal
Enable `amazing-async-dev` to apply parsed email decision replies to RunState and continue execution from those resolutions, completing the async human decision loop.

### Why this matters
Feature 021 (Email Decision Channel) implemented email delivery and reply parsing, but the system remains **disconnected**:

- `DecisionRequestStore` stores email decision requests in `.runtime/decision-requests/*.json`
- `RunState.decisions_needed` is an array in `runstate.md` managed separately
- Email replies update `DecisionRequestStore` but NOT `RunState`
- `resume_next_day` reads `RunState` but NOT `DecisionRequestStore`

This disconnect means:
- email decisions are processed but don't affect workflow state
- resume logic ignores email decision state
- canonical loop cannot continue from email replies
- the async decision channel is incomplete

This feature exists to **integrate the email decision channel with the workflow engine**.

---

## 2. Objective

Connect the email decision system with RunState so that:

1. decision request creation syncs to `RunState.decisions_needed`
2. email reply resolution syncs to `RunState`
3. `resume_next_day` reads from both sources
4. reply commands map to continuation actions
5. workflow can continue after email decision resolution

This feature completes the email-first async decision loop.

---

## 3. Scope

### In scope
- define decision sync layer between DecisionRequestStore and RunState
- extend RunState schema with decision request tracking fields
- define reply-to-action mapping rules
- integrate email_decision CLI with RunState sync
- integrate resume_next_day with DecisionRequestStore
- support decision reconciliation when sources disagree
- map reply commands to continuation behavior
- test full decision loop: create → send → reply → resume

### Out of scope
- real IMAP email reply polling
- Slack/Telegram/etc channels
- natural language freeform reply understanding
- multi-user approval routing
- broad notification platform abstractions
- autonomous decision making without human reply
- advanced policy learning
- long-running background scheduler design

---

## 4. Success Criteria

This feature is successful when:

1. decision request creation updates `RunState.decisions_needed`
2. email reply resolution updates `RunState` and clears `decisions_needed`
3. `resume_next_day` reads from `DecisionRequestStore`
4. reconciliation detects orphaned entries and warns
5. reply commands map to continuation phases
6. workflow can continue after valid email reply
7. end-to-end decision loop works: create → send → reply → resume → continue

---

## 5. Core Design Principles

### 5.1 Sync through unified layer
All decision state changes must flow through the sync layer. No direct updates.

### 5.2 Reconciliation on resume
Always reconcile sources before proceeding. Detect and report discrepancies.

### 5.3 Idempotent reply handling
Same reply should not cause double-processing. Use status checks.

### 5.4 Preserve traceability
Decision request ID, reply, and RunState resolution must remain linked.

### 5.5 Phase-aware continuation
Continuation phase depends on reply command and decision context.

---

## 6. Main Capabilities

## 6.1 Decision sync layer

### Purpose
Provide bidirectional sync between DecisionRequestStore and RunState.

### Expected behavior
- sync decision request to `RunState.decisions_needed` on creation
- sync email reply resolution to `RunState` on reply
- reconcile both sources on resume
- detect orphaned entries and warn

### Components
- `runtime/decision_sync.py` (new module)
- `sync_decision_to_runstate()` function
- `sync_reply_to_runstate()` function
- `reconcile_decision_sources()` function

### Notes
This layer must be the ONLY pathway for decision state updates.

---

## 6.2 RunState schema extension

### Purpose
Add fields to RunState for email decision tracking.

### Expected new fields
- `decision_request_pending`: ID of active pending request
- `decision_request_sent_at`: timestamp of email send
- `last_decision_resolution`: record of last resolved decision

### Notes
These fields enable RunState to reference email decision context.

---

## 6.3 Reply-to-action mapping

### Purpose
Map reply commands to RunState continuation actions.

### Expected mapping rules
| Reply Command | RunState Action | Continuation Phase |
|---------------|-----------------|-------------------|
| `DECISION A` | select option A | `executing` with selected path |
| `APPROVE PUSH` | approve risky action | `executing` to continue push |
| `DEFER` | defer decision, use alternative | `planning` to find alternative |
| `RETRY` | mark retry needed | `executing` to retry step |
| `CONTINUE` | clear blocker | `executing` to continue |

### Components
- `runtime/reply_action_mapper.py` (new module)
- `REPLY_ACTION_MAP` dictionary
- `map_reply_to_action()` function

### Notes
Mapping must be explicit and inspectable. No hidden magic.

---

## 6.4 email_decision CLI integration

### Purpose
Update email_decision CLI to sync with RunState.

### Expected changes
- on `create`: sync request to RunState, set phase to blocked if needed
- on `reply`: sync resolution to RunState, set continuation phase

### Notes
CLI must call sync layer, not update stores directly.

---

## 6.5 resume_next_day CLI integration

### Purpose
Update resume_next_day to read from DecisionRequestStore.

### Expected changes
- load RunState and reconcile with DecisionRequestStore
- display pending/resolved email decisions
- process unified decision state
- handle email decision resolution before continuing

### Notes
Resume must check both sources to handle edge cases.

---

## 7. State Model Expectations

This feature should enable these state transitions:

| Current State | Trigger | Next State |
|---------------|---------|------------|
| `executing` | decision needed → email sent | `blocked` |
| `blocked` + pending request | reply received | decision applying |
| decision applying | valid reply applied | `planning` or `executing` |
| `blocked` + expired request | timeout reached | default action applied |

### Notes
Phase should reflect decision state clearly.

---

## 8. Integration Expectations

This feature should integrate with:

- Feature 021 `DecisionRequestStore`
- Feature 021 `ReplyParser`
- Feature 021 `EmailSender`
- `RunState` schema
- `StateStore`
- `resume_next_day` CLI
- `email_decision` CLI
- execution policy (Feature 020 concepts)
- continuation semantics (Feature 037)

### Notes
This feature connects existing systems, not creates new ones.

---

## 9. Deliverables

This feature must add:

### 9.1 Decision sync module
`runtime/decision_sync.py` with sync functions.

### 9.2 Reply action mapper module
`runtime/reply_action_mapper.py` with mapping rules.

### 9.3 RunState schema extension
New fields in `schemas/runstate.schema.yaml`.

### 9.4 CLI integration
Updated `cli/commands/email_decision.py` and `cli/commands/resume_next_day.py`.

### 9.5 Tests
Unit tests for sync layer, mapper, and CLI integration.
End-to-end test for full decision loop.

### 9.6 Documentation
Updated `docs/async-decision-channel.md` to explain integration.

---

## 10. Acceptance Criteria

- [ ] decision request creation syncs to `RunState.decisions_needed`
- [ ] email reply resolution syncs to `RunState`
- [ ] `resume_next_day` reads from `DecisionRequestStore`
- [ ] reconciliation detects orphaned entries
- [ ] reply commands map to continuation actions
- [ ] workflow phase updates after reply
- [ ] end-to-end decision loop works
- [ ] tests pass for sync, mapper, CLI, and end-to-end

---

## 11. Risks

### Risk 1 — Sync race conditions
Direct updates bypassing sync layer could cause inconsistency.

**Mitigation:** enforce sync layer as only update path. Add validation checks.

### Risk 2 — Orphaned entries
Manual RunState edits could create orphaned decision entries.

**Mitigation:** reconciliation detects and reports. Warn user before proceeding.

### Risk 3 — Phase mismatch
Continuation phase may not match actual workflow state.

**Mitigation:** validate phase vs decision state before setting. Use policy rules.

### Risk 4 — Duplicate processing
Same reply could be processed twice.

**Mitigation:** idempotency checks. Only process requests in `sent` status.

---

## 12. Recommended Implementation Order

1. create decision sync layer module
2. extend RunState schema
3. create reply action mapper module
4. integrate email_decision CLI
5. integrate resume_next_day CLI
6. add unit tests
7. add end-to-end test
8. update documentation

---

## 13. Definition of Done

Feature 043 is done when:

- email decision request creation updates RunState
- email reply resolution updates RunState
- resume_next_day reads from DecisionRequestStore
- reconciliation detects discrepancies
- reply commands enable workflow continuation
- end-to-end decision loop works
- documentation explains the integration

If email decisions still don't affect workflow state, this feature is not done.

---

## 14. Source Documents

- `docs/infra/feature-021-to-040-gap-analysis.md`
- `docs/infra/feature-043-phase-a-implementation-plan.md`
- `docs/infra/amazing-async-dev-email-first-human-decision-and-reporting-channel-roadmap-spec.md`
- `docs/async-decision-channel.md`

---

## 15. Status

**Spec Created**: 2026-04-16
**Status**: Ready for Implementation
**Depends On**: Feature 021 (Email Decision Channel)
**Blocks**: Features 040-042 refinement, Feature 044+