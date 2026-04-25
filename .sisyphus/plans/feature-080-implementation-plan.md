# Feature 080 Implementation Plan
## Auto Email Notification for Decision and Day-End Events

**Feature ID**: 080-auto-email-notification-for-decision-and-day-end-events  
**Status**: Planning  
**Created**: 2026-04-25

---

## 1. Executive Summary

Feature 080 transforms async-dev's email capability from manual invocation to automatic event-driven notification. The platform already has robust email infrastructure (Features 053, 054, 048, 049) but lacks:

1. **Day-end summary auto-email** (review-night has no auto-email)
2. **Notification event model** (structured tracking of all notification types)
3. **Dedupe mechanism** (prevent duplicate notifications for unresolved events)
4. **Complete mainflow integration** (auto-trigger only hooked in mock mode)

This plan adds automatic email triggering for:
- Major decision-required events
- Day-end review summary delivery
- Critical escalation-worthy states

---

## 2. Current Infrastructure Analysis

### 2.1 Existing Components (Reuse/Extend)

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| `auto_email_trigger.py` | runtime/ | Auto-trigger for decision emails | Feature 054 COMPLETE - hooked only in mock mode |
| `email_sender.py` | runtime/ | Email sending abstraction | Complete - supports mock/console/resend/smtp |
| `resend_provider.py` | runtime/ | Resend API integration | Feature 053 COMPLETE |
| `email_escalation_policy.py` | runtime/ | Policy-based trigger governance | Feature 048 COMPLETE |
| `email_failure_handler.py` | runtime/ | Failure handling + persistence | Feature 049 COMPLETE |
| `decision_request_store.py` | runtime/ | Decision request lifecycle | Complete - JSON file persistence |
| `decision_sync.py` | runtime/ | RunState sync for decisions | Complete - sets blocking state |
| `state_store.py` | runtime/ | Blocking alert generation | Feature 065 COMPLETE |

### 2.2 Gap Analysis

| Gap | Current State | Required for Feature 080 |
|-----|---------------|-------------------------|
| Day-end auto-email | None - review-night only saves pack | Auto-send after DailyReviewPack generation |
| Notification event model | Only `TriggerResult` for decisions | Structured `NotificationEvent` for all types |
| Dedupe mechanism | Checks `decision_request_pending` only | Dedupe key strategy for all notification types |
| Mainflow hooks | Only `run_day.py` mock mode (line 820) | Hook into live/external/review-night/resume |
| Day-end state persistence | DecisionRequestStore only | NotificationStore for all notification types |

---

## 3. Implementation Architecture

### 3.1 New Components

```
runtime/
├── notification_event.py          # NEW - Notification event model + dedupe
├── notification_store.py          # NEW - Notification state persistence
├── auto_day_end_email.py          # NEW - Day-end summary auto-email
├── notification_orchestrator.py   # NEW - Unified notification trigger manager
└── notification_payload_builder.py # NEW - Email payload builders

cli/commands/
├── review_night.py                # MODIFY - Add day-end auto-email hook
├── run_day.py                     # MODIFY - Extend auto-trigger to all modes
├── resume_next_day.py             # MODIFY - Add auto-email for new blockers
└── notification.py                # NEW - Notification CLI commands (optional)
```

### 3.2 Integration Points

```
┌─────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│   run_day.py    │───►│ notification_        │───►│   EmailSender    │
│  (all modes)    │    │   orchestrator.py    │    │   (existing)     │
└─────────────────┘    └──────────────────────┘    └──────────────────┘
                               │
┌─────────────────┐            │                       ┌──────────────────┐
│ review_night.py │───────────►│                       │ NotificationStore│
│ (day-end hook)  │            │                       │   (NEW)          │
└─────────────────┘            │                       └──────────────────┘
                               │
┌─────────────────┐            │                       ┌──────────────────┐
│resume_next_day.py│──────────►│                       │ ResendProvider   │
│(blocker escalation)│         │                       │   (existing)     │
└─────────────────┘            └──────────────────────┘    └──────────────────┘
```

---

## 4. Detailed Implementation Steps

### Phase 1: Notification Event Model (AC-001)

**File**: `runtime/notification_event.py`

**Design**:
```python
class NotificationEventType(str, Enum):
    MAJOR_DECISION_REQUIRED = "major_decision_required"
    BLOCKED_WAITING_HUMAN = "blocked_waiting_for_human"
    CRITICAL_ESCALATION = "critical_escalation"
    DAY_END_SUMMARY_READY = "day_end_summary_ready"
    EXECUTION_FAILED = "execution_failed"
    ACCEPTANCE_READY = "acceptance_ready"

class NotificationSeverity(str, Enum):
    CRITICAL = "critical"      # Always send, no dedupe window
    HIGH = "high"              # Send immediately, 1hr dedupe
    MEDIUM = "medium"          # Send with policy check, 4hr dedupe
    LOW = "low"                # Policy-gated, 24hr dedupe

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY_NEEDED = "retry_needed"
    SKIPPED = "skipped"

@dataclass
class NotificationEvent:
    event_id: str              # Generated ID: notif-{YYYYMMDD}-{###}
    event_type: NotificationEventType
    severity: NotificationSeverity
    dedupe_key: str            # Key for duplicate suppression
    run_id: str | None         # Execution ID reference
    feature_id: str            # Feature context
    product_id: str            # Product context
    reason: str                # Why notification triggered
    created_at: datetime
    email_required: bool       # Policy decision
    email_sent: bool
    email_sent_at: datetime | None
    resend_message_id: str | None
    delivery_status: NotificationStatus
    related_artifacts: list[str]  # File paths
    metadata: dict[str, Any]   # Additional context
```

**Dedupe Key Strategy**:
```python
def generate_dedupe_key(event_type: NotificationEventType, context: dict) -> str:
    """
    Dedupe key format: {event_type}:{primary_identifier}
    
    Examples:
    - major_decision_required:dr-20260425-001
    - day_end_summary_ready:2026-04-25
    - blocked_waiting_human:blocker-001
    - critical_escalation:exec-001
    """
    primary_id = context.get("primary_id", "")
    return f"{event_type.value}:{primary_id}"
```

**Dedupe Logic**:
- Same dedupe_key + unresolved event → skip send
- Resolution clears dedupe (allows new notification for same entity)
- Time window: 4 hours for medium, 24 hours for low, no window for critical/high

---

### Phase 2: Notification State Persistence (AC-005)

**File**: `runtime/notification_store.py`

**Design**:
```python
class NotificationStore:
    DEFAULT_NOTIFICATIONS_PATH = ".runtime/notifications"
    
    def create_notification(self, event: NotificationEvent) -> dict:
        """Create notification record."""
        
    def load_notification(self, event_id: str) -> dict | None:
        """Load notification by ID."""
        
    def check_dedupe(self, dedupe_key: str) -> bool:
        """Check if notification already sent for this key."""
        
    def mark_sent(self, event_id: str, message_id: str) -> dict:
        """Mark notification as sent."""
        
    def mark_failed(self, event_id: str, error: str) -> dict:
        """Mark notification as failed."""
        
    def mark_delivered(self, event_id: str, webhook_data: dict) -> dict:
        """Update from webhook event."""
        
    def get_pending_notifications(self) -> list[dict]:
        """Get all pending notifications."""
        
    def get_unresolved_for_event(self, event_type: NotificationEventType, 
                                  dedupe_key: str) -> dict | None:
        """Get unresolved notification matching dedupe key."""
```

**File Structure**:
```
.runtime/notifications/
├── notif-20260425-001.json
├── notif-20260425-002.json
└── dedupe-index.json          # Quick lookup for dedupe check
```

---

### Phase 3: Day-End Summary Auto-Email (AC-003)

**File**: `runtime/auto_day_end_email.py`

**Design**:
```python
@dataclass
class DayEndEmailResult:
    triggered: bool
    notification_id: str | None
    resend_message_id: str | None
    skipped_reason: str | None
    error_message: str | None

def should_send_day_end_email(
    review_pack: dict,
    runstate: dict,
    notification_store: NotificationStore,
) -> tuple[bool, str | None]:
    """
    Check if day-end email should be sent.
    
    Policy:
    - Always send if decisions_needed or blocked_items present
    - Skip if already sent for this date (dedupe: day_end_summary_ready:{date})
    - Skip if policy_mode is low_interruption and nothing critical
    """
    date = review_pack.get("date", "")
    dedupe_key = f"day_end_summary_ready:{date}"
    
    # Check if already sent
    existing = notification_store.get_unresolved_for_event(
        NotificationEventType.DAY_END_SUMMARY_READY,
        dedupe_key
    )
    if existing and existing.get("email_sent"):
        return False, "Day-end summary email already sent for this date"
    
    # Check content significance
    decisions = review_pack.get("decisions_needed", [])
    blocked = review_pack.get("blocked_items", [])
    
    if not decisions and not blocked:
        policy_mode = runstate.get("policy_mode", "balanced")
        if policy_mode == "low_interruption":
            return False, "No critical items and low interruption mode"
    
    return True, None

def build_day_end_email_payload(review_pack: dict) -> dict:
    """
    Build email payload for day-end summary.
    
    Content:
    - What happened today (completed items)
    - Current platform/project status
    - Active or blocked items
    - Items needing attention (decisions_needed)
    - Next day recommended action
    """
    
def send_day_end_email(
    project_path: Path,
    review_pack: dict,
    runstate: dict,
) -> DayEndEmailResult:
    """
    Send day-end summary email.
    
    Flow:
    1. Check policy
    2. Create NotificationEvent
    3. Check dedupe
    4. Build payload
    5. Send via EmailSender
    6. Persist notification state
    """
```

---

### Phase 4: Notification Orchestrator (AC-007)

**File**: `runtime/notification_orchestrator.py`

**Design**:
```python
class NotificationOrchestrator:
    """
    Unified notification trigger manager.
    
    Replaces scattered auto-trigger calls with centralized orchestration.
    """
    
    def __init__(self, project_path: Path):
        self.store = NotificationStore(project_path)
        self.email_sender = EmailSender(create_email_config(project_path))
        self.escalation_policy = EmailEscalationPolicy()
        
    def trigger_decision_notification(
        self,
        decision_entry: dict,
        trigger_source: TriggerSource,
    ) -> NotificationEvent:
        """
        Trigger notification for decision-required event.
        
        Replaces auto_email_trigger.check_and_trigger() with
        notification-tracking version.
        """
        
    def trigger_day_end_notification(
        self,
        review_pack: dict,
        runstate: dict,
    ) -> NotificationEvent:
        """
        Trigger day-end summary notification.
        """
        
    def trigger_blocker_notification(
        self,
        blocker_entry: dict,
        runstate: dict,
    ) -> NotificationEvent:
        """
        Trigger notification for new blocker added.
        """
        
    def trigger_escalation_notification(
        self,
        escalation_type: str,
        context: dict,
    ) -> NotificationEvent:
        """
        Trigger notification for critical escalation.
        """
        
    def check_and_trigger_all(
        self,
        runstate: dict,
        trigger_source: TriggerSource,
    ) -> list[NotificationEvent]:
        """
        Check all potential triggers and fire notifications.
        
        Uses email_escalation_policy.get_appropriate_triggers_for_runstate()
        """
```

---

### Phase 5: Mainflow Integration

#### 5.1 review_night.py Integration

**Location**: After `store.save_daily_review_pack()` (line 83)

**Modification**:
```python
# In generate() function after saving review pack
from runtime.notification_orchestrator import NotificationOrchestrator

orchestrator = NotificationOrchestrator(project_path)
result = orchestrator.trigger_day_end_notification(review_pack, runstate)

if result.email_sent:
    console.print(f"[green]Day-end summary email sent: {result.resend_message_id}[/green]")
elif result.skipped_reason:
    console.print(f"[dim]Day-end email skipped: {result.skipped_reason}[/dim]")
elif result.error_message:
    console.print(f"[yellow]Day-end email failed: {result.error_message}[/yellow]")
```

#### 5.2 run_day.py Integration

**Current**: Only hooked in `_run_mock_mode()` at line 820

**Modification**: Extend to `_run_live_mode()` and `_handle_closeout_result()`

```python
# In _run_live_mode() after save_execution_result (line 687)
if result.get("decisions_required") or result.get("blocked_reasons"):
    orchestrator = NotificationOrchestrator(store.project_path)
    events = orchestrator.check_and_trigger_all(runstate, TriggerSource.RUN_DAY_AUTO)
    for event in events:
        if event.email_sent:
            console.print(f"[green]Notification sent: {event.event_type.value}[/green]")

# In _handle_closeout_result() for non-success terminal classification
if terminal_classification in [CloseoutTerminalClassification.FAILURE, 
                               CloseoutTerminalClassification.VERIFICATION_FAILURE]:
    orchestrator = NotificationOrchestrator(store.project_path)
    orchestrator.trigger_escalation_notification("closeout_failure", {
        "execution_id": execution_id,
        "classification": terminal_classification.value,
    })
```

#### 5.3 resume_next_day.py Integration

**Location**: After processing decisions that add new blockers

```python
# In continue_loop() when new decisions_needed added
if new_decisions_added:
    orchestrator = NotificationOrchestrator(project_path)
    for decision in new_decisions:
        orchestrator.trigger_decision_notification(decision, TriggerSource.RESUME_DAY_AUTO)
```

---

### Phase 6: Email Payload Builders (AC-002, AC-003)

**File**: `runtime/notification_payload_builder.py`

**Design**:
```python
def build_decision_email_payload(notification: NotificationEvent) -> dict:
    """
    Build payload for decision-required email.
    
    Reuse existing EmailSender._build_body() pattern but add:
    - Notification event context
    - Link to notification record
    - Severity indicator
    """
    
def build_day_end_email_payload(notification: NotificationEvent, 
                                review_pack: dict) -> dict:
    """
    Build payload for day-end summary email.
    
    Content sections:
    - Summary header: "Daily Summary for {project} - {date}"
    - Completed items: bulleted list
    - Blocked items: with resolution hints
    - Decisions needed: with options
    - Next day plan: recommended action
    - Links: RunState, ExecutionResult
    """
    
def build_blocker_email_payload(notification: NotificationEvent) -> dict:
    """
    Build payload for blocker notification.
    
    Content:
    - Blocker description
    - Impact assessment
    - Resolution options
    - Urgency indicator
    """
    
def build_escalation_email_payload(notification: NotificationEvent) -> dict:
    """
    Build payload for critical escalation.
    
    Content:
    - Escalation reason
    - Immediate action required
    - Context summary
    - Links to relevant artifacts
    """
```

---

### Phase 7: Delivery Failure Handling (AC-006)

**Extension**: Add webhook integration for notification events

**File**: Extend `runtime/resend_provider.py` webhook handler

```python
# In ResendWebhookHandler._handle_email_failed()
def _handle_email_failed(self, payload: dict) -> dict:
    """Handle email failed event."""
    data = payload.get("data", {})
    message_id = data.get("email_id")
    
    # Link to notification record
    notification_store = NotificationStore()
    notification = notification_store.find_by_message_id(message_id)
    
    if notification:
        notification_store.mark_failed(
            notification["event_id"],
            data.get("failed", {}).get("reason", "unknown")
        )
        
        # If critical severity, create retry-needed state
        if notification["severity"] in ["critical", "high"]:
            notification_store.mark_retry_needed(notification["event_id"])
            
    return {"status": "recorded", "notification_updated": True}
```

---

## 5. Acceptance Criteria Mapping

| AC | Requirement | Implementation |
|----|-------------|----------------|
| AC-001 | Notification Event Model Exists | `runtime/notification_event.py` - NotificationEvent dataclass with EventType enum |
| AC-002 | Major Decision Emails Auto-Send | `notification_orchestrator.trigger_decision_notification()` + mainflow hooks |
| AC-003 | Day-End Summary Emails Auto-Send | `auto_day_end_email.py` + `review_night.py` hook |
| AC-004 | Dedupe Works | `notification_store.check_dedupe()` + dedupe_key strategy |
| AC-005 | Delivery State Persists | `notification_store.py` - JSON file persistence |
| AC-006 | Failures Are Visible | Webhook handler extension + mark_failed() |
| AC-007 | Mainflow Integration Exists | Hooks in run_day.py, review_night.py, resume_next_day.py |
| AC-008 | Noise Is Controlled | Policy check in should_send_* functions |
| AC-009 | Documentation Updated | docs/email-notification.md, README update |
| AC-010 | Tests Added | tests/test_notification_*.py |

---

## 6. Test Requirements

### 6.1 Unit Tests

| Test File | Coverage |
|-----------|----------|
| `test_notification_event.py` | Event model, dedupe key generation, severity mapping |
| `test_notification_store.py` | Create, dedupe check, mark_sent/failed, persistence |
| `test_auto_day_end_email.py` | Policy check, payload building, send flow |
| `test_notification_orchestrator.py` | Trigger functions, check_and_trigger_all |
| `test_notification_payload_builder.py` | Payload formatting for all types |

### 6.2 Integration Tests

| Test | Scenario |
|------|----------|
| Decision auto-email live mode | run_day live execution with decisions_required |
| Day-end auto-email | review-night generate with decisions_needed |
| Dedupe behavior | Repeated calls with same dedupe_key |
| Delivery failure handling | Webhook received for failed email |
| Policy filtering | Low interruption mode skips non-critical |

---

## 7. Implementation Order

**Recommended sequence** (matches Feature 080 spec Section 11.1):

1. **Phase 1**: Notification Event Model + Dedupe Strategy
2. **Phase 2**: Notification State Persistence
3. **Phase 3**: Day-End Summary Auto-Email
4. **Phase 4**: Notification Orchestrator
5. **Phase 5**: Mainflow Integration (review_night first, then run_day, resume)
6. **Phase 6**: Payload Builders (can parallelize)
7. **Phase 7**: Delivery Failure Handling
8. **Phase 8**: Tests
9. **Phase 9**: Documentation

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Email noise | Policy check in all trigger functions, dedupe keys |
| Delivery failures invisible | Webhook handler + notification_store.mark_failed |
| Mainflow hooks incomplete | Explicit hook checklist, line-by-line integration points |
| Payloads unhelpful | Template-based builders with actionable context |
| Resend config issues | Document required env vars, graceful degradation |

---

## 9. Questions to Clarify with User

1. **Notification CLI commands**: Should we add `asyncdev notification list/show` commands, or is the email_escalation_check sufficient?

2. **Webhook server**: Feature 080 requires webhook handling for delivery status. Should we:
   - Extend existing webhook_poller.py?
   - Create new webhook endpoint?
   - Use manual `asyncdev notification check-delivery` command?

3. **Day-end email timing**: Should day-end email be:
   - Sent immediately after review_night generate?
   - Deferred until operator runs specific command?
   - Sent at configured time (e.g., 6pm)?

4. **Multiple notifications per run**: If both decisions_needed AND blocked_items exist, should we:
   - Send one combined email?
   - Send separate emails per type?
   - Send only highest priority?

---

## 10. Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: Event Model | 2-3 hours | None |
| Phase 2: Persistence | 2-3 hours | Phase 1 |
| Phase 3: Day-End Email | 3-4 hours | Phase 1, 2 |
| Phase 4: Orchestrator | 2-3 hours | Phase 1, 2, 3 |
| Phase 5: Mainflow Hooks | 2-3 hours | Phase 4 |
| Phase 6: Payload Builders | 2-3 hours | Phase 1 |
| Phase 7: Failure Handling | 1-2 hours | Phase 2 |
| Phase 8: Tests | 3-4 hours | All phases |
| Phase 9: Documentation | 1-2 hours | All phases |

**Total**: ~20-25 hours across 9 phases

---

## 11. Next Immediate Action

**Begin Phase 1**: Create `runtime/notification_event.py` with:
- `NotificationEventType` enum
- `NotificationSeverity` enum  
- `NotificationStatus` enum
- `NotificationEvent` dataclass
- `generate_dedupe_key()` function

This establishes the canonical notification model that all other components depend on.