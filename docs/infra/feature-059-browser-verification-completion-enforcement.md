# Feature 059 — Browser Verification Completion Enforcement

## Status
`complete`

## Objective

Force AI agents to complete browser verification workflows, preventing the pattern of "starting dev server but never verifying" that blocks frontend project progress.

---

## Problem Statement

During dogfood session for amazing-briefing-viewer, we observed a critical workflow failure:

1. **AI starts dev server** - `npm run dev` → server running on port 3002
2. **AI attempts Playwright** - calls `browser_navigate`
3. **Connection fails** - server not ready / wrong port
4. **AI stops** - never retries, never uses correct CLI, verification incomplete
5. **Progress blocked** - cannot complete dogfood, cannot write report

**This pattern repeats**: Server started → verification attempted → fails → AI stops → no timeout → no fallback → stuck.

**The root cause**: Feature 056 provides CLI tools but no enforcement mechanism. AI agents can:
- Start dev server and forget to verify
- Attempt manual Playwright instead of CLI
- Fail and not retry with correct approach
- No timeout forces completion
- No state tracks "verification pending"

---

## Why This Matters

This is not a minor UX issue. It **blocks all frontend project progress**:

1. briefing-viewer dogfood stuck
2. Any frontend feature with UI changes stuck
3. Feature 038 verification gate cannot be enforced
4. ExecutionResult `browser_verification` field never populated correctly
5. Human sees "server ready" but no actual verification evidence

---

## Scope

### In Scope

1. **Timeout enforcement**
   - Max wait time after dev server start (default: 120 seconds)
   - Auto-record exception if timeout exceeded
   - Force completion even on failure

2. **Verification state tracking**
   - New state: `verification_pending` between server start and verification complete
   - Lock ExecutionResult status during pending state
   - System reminders to AI agent to continue verification

3. **CLI auto-trigger**
   - When `verification_type = frontend_*`, auto-trigger `asyncdev browser-test`
   - Dev server manager integrated into run-day execution
   - No manual Playwright needed

4. **Fallback enforcement**
   - If Playwright MCP fails → fallback to CLI
   - If CLI fails → record exception with specific reason
   - Never stuck in "started but not verified" state

5. **Port auto-discovery**
   - Try ports 3000-3006 sequentially
   - Wait for each port to be ready
   - Don't fail on first connection error

### Out of Scope

1. Visual regression testing
2. Multi-browser testing
3. Performance benchmarks
4. Mobile viewport testing

---

## Architecture

### State Flow (Enforced)

```
dev_server_started (timestamp T0)
          ↓
verification_pending (max timeout T0 + 120s)
          ↓
┌─────────────────────────────────────────────┐
│ MUST complete within timeout:                │
│                                              │
│ Option A: Playwright MCP verification        │
│   browser_navigate → snapshot → screenshot   │
│                                              │
│ Option B: CLI verification                   │
│   asyncdev browser-test --url <port>         │
│                                              │
│ Option C: Exception (if blocked)             │
│   record exception_reason + details          │
└─────────────────────────────────────────────┘
          ↓
verification_complete OR verification_timeout
          ↓
ExecutionResult.browser_verification populated
          ↓
Can now mark status: success/partial
```

### Timeout Mechanism

```python
@dataclass
class VerificationSession:
    session_id: str
    project_id: str
    started_at: datetime
    timeout_seconds: int = 120
    dev_server_url: str | None = None
    verification_attempted: bool = False
    verification_complete: bool = False
    exception_reason: str | None = None

def check_verification_timeout(session: VerificationSession) -> bool:
    elapsed = (datetime.now() - session.started_at).total_seconds()
    return elapsed > session.timeout_seconds

def enforce_verification_completion(session: VerificationSession) -> dict:
    if session.verification_complete:
        return {"status": "complete"}
    
    if check_verification_timeout(session):
        return {
            "status": "timeout",
            "exception_reason": "verification_timeout",
            "exception_details": f"Dev server started but no verification completed within {session.timeout_seconds}s",
        }
    
    # Still pending - must continue
    return {"status": "pending", "reminder": "Verification session active - must complete browser verification"}
```

### System Reminder Hook

When `verification_pending` state exists and AI agent stops without completion:

```
[SYSTEM REMINDER - VERIFICATION PENDING]
Dev server is running at http://localhost:3002
Verification session started at 12:20:00
Timeout: 120 seconds (expires at 12:22:00)
Elapsed: 45 seconds

YOU MUST:
1. Run browser verification: asyncdev browser-test --url http://localhost:3002
2. OR record exception if blocked
3. DO NOT stop until verification_complete OR timeout

Current blocking: None detected
Recommended action: Continue with browser verification
```

---

## Deliverables

1. `runtime/verification_session.py` - Session tracking with timeout
2. `runtime/verification_enforcer.py` - Enforcement logic
3. Updated `AGENTS.md` Section 9 - Mandatory completion rule
4. Updated `cli/commands/browser_test.py` - Auto-trigger support
5. `tests/test_verification_enforcement.py` - Enforcement tests
6. Feature spec + ExecutionResult

---

## AGENTS.md Amendment (Section 9.8)

```markdown
### 9.8 Verification Completion Enforcement (Feature 059)

**MANDATORY**: After dev server startup for frontend verification, AI agent MUST:

1. Continue to browser verification stage immediately
2. NOT stop at "server ready" without running verification
3. Complete verification within timeout (default: 120 seconds)
4. If blocked, record exception_reason in ExecutionResult

**Anti-Pattern (FORBIDDEN)**:
- Starting dev server → stopping → claiming "ready"
- Attempting manual Playwright → failing → not retrying with CLI
- Leaving verification_pending state without completion

**Timeout Behavior**:
- If 120s elapsed without verification → auto-record timeout exception
- ExecutionResult.browser_verification.executed = false
- exception_reason = "verification_timeout"

**Enforcement Hook**:
- System sends reminder if AI stops during verification_pending
- ExecutionResult cannot be marked success while verification_pending
```

---

## Acceptance Criteria

### Must Pass

1. ✅ Dev server start creates `verification_pending` session
2. ✅ Timeout enforced (120s default)
3. ✅ System reminder sent if AI stops during pending
4. ✅ ExecutionResult locked during pending state
5. ✅ Auto-trigger CLI verification for frontend tasks
6. ✅ Port auto-discovery (3000-3006)
7. ✅ Exception recorded on timeout

### Should Pass

1. ✅ Retry mechanism for connection failures
2. ✅ Fallback from Playwright MCP to CLI
3. ✅ Configurable timeout
4. ✅ Tests pass

---

## Implementation Phases

### Phase A: Session Tracking
- Create `verification_session.py`
- Timeout check logic
- State transitions

### Phase B: Enforcement Logic
- Create `verification_enforcer.py`
- Reminder hook mechanism
- ExecutionResult locking

### Phase C: AGENTS.md Update
- Add Section 9.8
- Define mandatory completion rule
- Document anti-patterns

### Phase D: CLI Integration
- Auto-trigger in browser_test.py
- Port discovery
- Retry logic

---

## Estimated Effort

- Phase A: 1-2 hours
- Phase B: 1-2 hours
- Phase C: 30 minutes
- Phase D: 1-2 hours
- Tests: 1 hour
- Total: 4-6 hours

---

## Priority

**P0 - Critical**

This blocks all frontend progress. Without enforcement, Feature 056 tools are useless because AI agents don't use them consistently.