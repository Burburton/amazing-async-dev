"""Notification event model for Feature 080 - Auto Email Notification.

Provides structured notification event types, severity levels, status tracking,
and dedupe key strategy for preventing duplicate notifications.

Design based on patterns from:
- Sentry NotificationMessage model
- django-notifications AbstractNotification
- Ops Intelligence Agent dedupe patterns
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any
import hashlib
import json


class NotificationEventType(StrEnum):
    """Canonical notification event types for async-dev platform.
    
    Based on Feature 080 spec Section 6.1 requirements.
    """
    
    # Decision-related events
    MAJOR_DECISION_REQUIRED = "major_decision_required"
    BLOCKED_WAITING_FOR_HUMAN = "blocked_waiting_for_human"
    DECISION_RESOLVED = "decision_resolved"
    
    # Escalation events
    CRITICAL_ESCALATION_REQUIRED = "critical_escalation_required"
    EXECUTION_FAILED = "execution_failed"
    VERIFICATION_FAILED = "verification_failed"
    
    # Day-end events
    DAY_END_SUMMARY_READY = "day_end_summary_ready"
    
    # Acceptance events
    ACCEPTANCE_READY = "acceptance_ready"
    ACCEPTANCE_BLOCKED = "acceptance_blocked"
    
    # Session events
    SESSION_BLOCKED = "session_blocked"


class NotificationSeverity(StrEnum):
    """Severity levels for notification prioritization.
    
    Determines urgency, dedupe window, and routing behavior.
    """
    
    CRITICAL = "critical"    # Always send, no dedupe window, multiple channels
    HIGH = "high"            # Send immediately, 1hr dedupe, email + optional channel
    MEDIUM = "medium"        # Policy-gated send, 4hr dedupe, email only
    LOW = "low"              # Policy-gated, 24hr dedupe, optional email
    INFORMATIONAL = "info"   # No email, console/log only


class NotificationStatus(StrEnum):
    """Delivery status tracking for notifications.
    
    Lifecycle: pending → sent → delivered/failed/skipped.
    """
    
    PENDING = "pending"          # Created, awaiting send
    SENT = "sent"                # Email sent via Resend/other
    DELIVERED = "delivered"      # Delivery confirmed via webhook
    FAILED = "failed"            # Send failed, needs attention
    RETRY_NEEDED = "retry_needed"  # Failed, awaiting retry
    SKIPPED = "skipped"          # Dedupe/policy suppression
    EXPIRED = "expired"          # Dedupe window passed without send


class NotificationChannel(StrEnum):
    """Delivery channels for notifications."""
    
    EMAIL = "email"
    CONSOLE = "console"
    MOCK_FILE = "mock_file"
    RESEND = "resend"


# Event type to severity mapping (from research patterns)
EVENT_TYPE_SEVERITY_MAP: dict[NotificationEventType, NotificationSeverity] = {
    NotificationEventType.MAJOR_DECISION_REQUIRED: NotificationSeverity.HIGH,
    NotificationEventType.BLOCKED_WAITING_FOR_HUMAN: NotificationSeverity.HIGH,
    NotificationEventType.CRITICAL_ESCALATION_REQUIRED: NotificationSeverity.CRITICAL,
    NotificationEventType.EXECUTION_FAILED: NotificationSeverity.HIGH,
    NotificationEventType.VERIFICATION_FAILED: NotificationSeverity.MEDIUM,
    NotificationEventType.DAY_END_SUMMARY_READY: NotificationSeverity.MEDIUM,
    NotificationEventType.DECISION_RESOLVED: NotificationSeverity.LOW,
    NotificationEventType.ACCEPTANCE_READY: NotificationSeverity.MEDIUM,
    NotificationEventType.ACCEPTANCE_BLOCKED: NotificationSeverity.HIGH,
    NotificationEventType.SESSION_BLOCKED: NotificationSeverity.HIGH,
}

# Dedupe window by severity (seconds)
SEVERITY_DEDUPE_WINDOWS: dict[NotificationSeverity, int] = {
    NotificationSeverity.CRITICAL: 0,       # No dedupe - always send
    NotificationSeverity.HIGH: 3600,        # 1 hour
    NotificationSeverity.MEDIUM: 14400,     # 4 hours
    NotificationSeverity.LOW: 86400,        # 24 hours
    NotificationSeverity.INFORMATIONAL: 86400,  # 24 hours
}

# Dedupe window by event type (overrides severity-based)
EVENT_TYPE_DEDUPE_WINDOWS: dict[NotificationEventType, int] = {
    NotificationEventType.DAY_END_SUMMARY_READY: 86400,  # Once per day max
    NotificationEventType.MAJOR_DECISION_REQUIRED: 1800,  # 30 min - decisions need quick attention
}


@dataclass
class NotificationEvent:
    """Canonical notification event model for async-dev notifications."""
    
    event_id: str
    event_type: NotificationEventType
    dedupe_key: str
    severity: NotificationSeverity = NotificationSeverity.MEDIUM
    dedupe_window_seconds: int = 3600
    product_id: str = ""
    feature_id: str = ""
    run_id: str | None = None
    request_id: str | None = None
    reason: str = ""
    title: str = ""
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    email_required: bool = True
    email_sent: bool = False
    email_sent_at: datetime | None = None
    resend_message_id: str | None = None
    delivery_status: NotificationStatus = NotificationStatus.PENDING
    delivery_channel: NotificationChannel = NotificationChannel.MOCK_FILE
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    related_artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set defaults based on event type."""
        # Set severity from event type if not explicitly set
        if self.severity == NotificationSeverity.MEDIUM:
            self.severity = EVENT_TYPE_SEVERITY_MAP.get(
                self.event_type, NotificationSeverity.MEDIUM
            )
        
        # Set dedupe window from event type or severity
        if self.event_type in EVENT_TYPE_DEDUPE_WINDOWS:
            self.dedupe_window_seconds = EVENT_TYPE_DEDUPE_WINDOWS[self.event_type]
        elif self.severity in SEVERITY_DEDUPE_WINDOWS:
            self.dedupe_window_seconds = SEVERITY_DEDUPE_WINDOWS[self.severity]
        
        # Set expires_at based on dedupe window
        if self.expires_at is None and self.dedupe_window_seconds > 0:
            self.expires_at = self.created_at + timedelta(
                seconds=self.dedupe_window_seconds
            )
        
        # Critical severity always requires email
        if self.severity == NotificationSeverity.CRITICAL:
            self.email_required = True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "dedupe_key": self.dedupe_key,
            "dedupe_window_seconds": self.dedupe_window_seconds,
            "product_id": self.product_id,
            "feature_id": self.feature_id,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "reason": self.reason,
            "title": self.title,
            "message": self.message,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "email_required": self.email_required,
            "email_sent": self.email_sent,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None,
            "resend_message_id": self.resend_message_id,
            "delivery_status": self.delivery_status.value,
            "delivery_channel": self.delivery_channel.value,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "related_artifacts": self.related_artifacts,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationEvent":
        """Create from dict loaded from JSON."""
        # Parse datetime fields
        created_at = data.get("created_at")
        if created_at:
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()
        
        expires_at = data.get("expires_at")
        if expires_at:
            expires_at = datetime.fromisoformat(expires_at)
        
        email_sent_at = data.get("email_sent_at")
        if email_sent_at:
            email_sent_at = datetime.fromisoformat(email_sent_at)
        
        return cls(
            event_id=data["event_id"],
            event_type=NotificationEventType(data["event_type"]),
            severity=NotificationSeverity(data.get("severity", "medium")),
            dedupe_key=data["dedupe_key"],
            dedupe_window_seconds=data.get("dedupe_window_seconds", 3600),
            product_id=data.get("product_id", ""),
            feature_id=data.get("feature_id", ""),
            run_id=data.get("run_id"),
            request_id=data.get("request_id"),
            reason=data.get("reason", ""),
            title=data.get("title", ""),
            message=data.get("message", ""),
            context=data.get("context", {}),
            created_at=created_at,
            expires_at=expires_at,
            email_required=data.get("email_required", True),
            email_sent=data.get("email_sent", False),
            email_sent_at=email_sent_at,
            resend_message_id=data.get("resend_message_id"),
            delivery_status=NotificationStatus(data.get("delivery_status", "pending")),
            delivery_channel=NotificationChannel(data.get("delivery_channel", "mock_file")),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            related_artifacts=data.get("related_artifacts", []),
            metadata=data.get("metadata", {}),
        )


def generate_dedupe_key(
    event_type: NotificationEventType,
    primary_id: str,
    scope: str | None = None,
) -> str:
    """Generate dedupe key for notification event.
    
    Format: {event_type}:{scope}:{primary_id}
    
    Examples:
    - major_decision_required:decision:dr-20260425-001
    - day_end_summary_ready:review:2026-04-25
    - blocked_waiting_for_human:blocker:blocker-001
    
    Args:
        event_type: Notification event type
        primary_id: Primary identifier (request_id, date, execution_id, etc.)
        scope: Optional scope qualifier (decision, review, blocker, etc.)
        
    Returns:
        Dedupe key string
    """
    if scope:
        return f"{event_type.value}:{scope}:{primary_id}"
    return f"{event_type.value}:{primary_id}"


def generate_content_hash(context: dict[str, Any]) -> str:
    """Generate content-based fingerprint for dedupe.
    
    Used when dedupe should be based on content similarity
    rather than entity identity.
    
    Args:
        context: Context dict to hash
        
    Returns:
        16-character hash fingerprint
    """
    content = json.dumps(context, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def generate_event_id(
    notifications_path: str | None = None,
) -> str:
    """Generate unique notification event ID.
    
    Format: notif-{YYYYMMDD}-{###}
    
    Args:
        notifications_path: Path to notifications directory for counter
        
    Returns:
        Unique event ID
    """
    from pathlib import Path
    
    date_str = datetime.now().strftime("%Y%m%d")
    counter = 1
    
    if notifications_path:
        path = Path(notifications_path)
        if path.exists():
            existing = list(path.glob(f"notif-{date_str}-*.json"))
            if existing:
                counter = len(existing) + 1
    
    return f"notif-{date_str}-{counter:03d}"


def should_send_notification(
    event: NotificationEvent,
    policy_mode: str = "balanced",
    existing_pending: list[dict[str, Any]] | None = None,
) -> tuple[bool, str | None]:
    """Check if notification should be sent based on policy.
    
    Policy rules:
    - Critical severity: Always send
    - High severity: Send unless similar pending
    - Medium/Low: Check policy mode and dedupe
    
    Args:
        event: Notification event to check
        policy_mode: Policy mode (conservative/balanced/low_interruption)
        existing_pending: List of existing pending notifications
        
    Returns:
        Tuple of (should_send, skip_reason)
    """
    # Critical always sends
    if event.severity == NotificationSeverity.CRITICAL:
        return True, None
    
    # Check for existing pending with same dedupe key
    if existing_pending:
        for pending in existing_pending:
            if pending.get("dedupe_key") == event.dedupe_key:
                if pending.get("delivery_status") in ["pending", "sent"]:
                    return False, f"Duplicate pending: {event.dedupe_key}"
    
    # Policy mode filtering
    if policy_mode == "low_interruption":
        if event.severity in [NotificationSeverity.LOW, NotificationSeverity.INFORMATIONAL]:
            return False, f"Low interruption mode: skipping {event.severity.value}"
        if event.event_type == NotificationEventType.DAY_END_SUMMARY_READY:
            # Only send day-end if there are decisions or blockers
            context = event.context
            decisions = context.get("decisions_needed", [])
            blocked = context.get("blocked_items", [])
            if not decisions and not blocked:
                return False, "Low interruption: day-end has no critical items"
    
    elif policy_mode == "conservative":
        # Conservative sends everything except informational
        if event.severity == NotificationSeverity.INFORMATIONAL:
            return False, "Conservative mode: skipping informational"
    
    # Default: send if email_required
    return event.email_required, None


def get_severity_for_event_type(
    event_type: NotificationEventType,
) -> NotificationSeverity:
    """Get default severity for event type."""
    return EVENT_TYPE_SEVERITY_MAP.get(event_type, NotificationSeverity.MEDIUM)


def get_dedupe_window_for_event(
    event_type: NotificationEventType,
    severity: NotificationSeverity,
) -> int:
    """Get dedupe window in seconds for event.
    
    Event type-specific windows override severity-based.
    """
    if event_type in EVENT_TYPE_DEDUPE_WINDOWS:
        return EVENT_TYPE_DEDUPE_WINDOWS[event_type]
    return SEVERITY_DEDUPE_WINDOWS.get(severity, 3600)


@dataclass
class NotificationTriggerResult:
    """Result of notification trigger attempt.
    
    Similar to TriggerResult from auto_email_trigger.py but
    for general notifications.
    """
    
    triggered: bool
    event_id: str | None = None
    resend_message_id: str | None = None
    skipped_reason: str | None = None
    error_message: str | None = None
    event_type: NotificationEventType | None = None
    severity: NotificationSeverity | None = None
    policy_mode_at_trigger: str = "balanced"
    triggered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "triggered": self.triggered,
            "event_id": self.event_id,
            "resend_message_id": self.resend_message_id,
            "skipped_reason": self.skipped_reason,
            "error_message": self.error_message,
            "event_type": self.event_type.value if self.event_type else None,
            "severity": self.severity.value if self.severity else None,
            "policy_mode_at_trigger": self.policy_mode_at_trigger,
            "triggered_at": self.triggered_at.isoformat(),
        }