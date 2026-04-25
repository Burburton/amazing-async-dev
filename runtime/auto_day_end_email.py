"""Day-end summary auto-email for Feature 080.

Handles automatic sending of daily review summary emails when
review-night generates a DailyReviewPack with significant content.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import os

from runtime.notification_event import (
    NotificationEvent,
    NotificationEventType,
    NotificationSeverity,
    NotificationStatus,
    NotificationTriggerResult,
    NotificationChannel,
    should_send_notification,
)
from runtime.notification_store import (
    NotificationStore,
    create_day_end_notification,
)
from runtime.email_sender import EmailSender, create_email_config
from runtime.resend_provider import apply_resend_config_from_file
from runtime.execution_policy import PolicyMode, get_policy_mode


@dataclass
class DayEndEmailResult:
    """Result of day-end email trigger attempt."""
    
    triggered: bool
    notification_id: str | None = None
    resend_message_id: str | None = None
    skipped_reason: str | None = None
    error_message: str | None = None
    severity: NotificationSeverity = NotificationSeverity.MEDIUM
    policy_mode_at_trigger: PolicyMode = PolicyMode.BALANCED
    triggered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "triggered": self.triggered,
            "notification_id": self.notification_id,
            "resend_message_id": self.resend_message_id,
            "skipped_reason": self.skipped_reason,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "policy_mode_at_trigger": self.policy_mode_at_trigger.value,
            "triggered_at": self.triggered_at.isoformat(),
        }


def should_send_day_end_email(
    review_pack: dict[str, Any],
    runstate: dict[str, Any],
    notification_store: NotificationStore,
) -> tuple[bool, str | None]:
    """Check if day-end email should be sent based on policy.
    
    Policy rules:
    - Always send if decisions_needed or blocked_items present
    - Skip if already sent for this date (dedupe check)
    - Skip if low_interruption mode and no critical items
    - Conservative mode sends everything
    
    Args:
        review_pack: DailyReviewPack dict
        runstate: Current RunState
        notification_store: Notification store for dedupe check
        
    Returns:
        Tuple of (should_send, skip_reason)
    """
    policy_mode = get_policy_mode(runstate)
    date = review_pack.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    dedupe_key = f"{NotificationEventType.DAY_END_SUMMARY_READY.value}:review:{date}"
    is_dup, existing = notification_store.check_dedupe(dedupe_key)
    
    if is_dup:
        return False, f"Day-end email already sent for {date}"
    
    decisions_needed = review_pack.get("decisions_needed", [])
    blocked_items = review_pack.get("blocked_items", [])
    
    has_critical_content = bool(decisions_needed) or bool(blocked_items)
    
    if policy_mode == PolicyMode.LOW_INTERRUPTION:
        if not has_critical_content:
            return False, "Low interruption: no decisions or blockers to report"
    
    return True, None


def build_day_end_email_subject(
    review_pack: dict[str, Any],
    config: Any,
) -> str:
    """Build email subject for day-end summary."""
    project_id = review_pack.get("project_id", "unknown")
    date = review_pack.get("date", "")
    decisions_count = len(review_pack.get("decisions_needed", []))
    blocked_count = len(review_pack.get("blocked_items", []))
    
    status_suffix = ""
    if decisions_count > 0:
        status_suffix = f" [{decisions_count} decisions needed]"
    elif blocked_count > 0:
        status_suffix = f" [{blocked_count} blocked]"
    
    prefix = config.subject_prefix if hasattr(config, 'subject_prefix') else "[async-dev]"
    
    return f"{prefix} Daily Summary: {project_id} - {date}{status_suffix}"


def build_day_end_email_body(
    review_pack: dict[str, Any],
) -> str:
    """Build email body for day-end summary.
    
    Sections:
    - Summary header
    - Completed items
    - Blocked items with resolution hints
    - Decisions needed with options
    - Next day plan
    - Links to artifacts
    """
    lines = []
    
    date = review_pack.get("date", "")
    project_id = review_pack.get("project_id", "")
    feature_id = review_pack.get("feature_id", "")
    today_goal = review_pack.get("today_goal", "")
    
    lines.append(f"Daily Review Summary - {date}")
    lines.append(f"Project: {project_id}")
    if feature_id:
        lines.append(f"Feature: {feature_id}")
    lines.append("")
    
    if today_goal:
        lines.append(f"Today's Goal: {today_goal}")
        lines.append("")
    
    completed = review_pack.get("what_was_completed", [])
    if completed:
        lines.append("Completed Items:")
        for item in completed:
            lines.append(f"  ✓ {item}")
        lines.append("")
    
    blocked = review_pack.get("blocked_items", [])
    if blocked:
        lines.append("Blocked Items:")
        for block in blocked:
            reason = block.get("reason", block.get("item", "Unknown blocker"))
            lines.append(f"  ⚠ {reason}")
            if block.get("resolution"):
                lines.append(f"    Resolution: {block['resolution']}")
        lines.append("")
    
    decisions = review_pack.get("decisions_needed", [])
    if decisions:
        lines.append("Decisions Required:")
        for i, decision in enumerate(decisions, 1):
            question = decision.get("decision", "Decision needed")
            lines.append(f"  {i}. {question}")
            
            options = decision.get("options", [])
            if options:
                for opt in options:
                    if isinstance(opt, str):
                        lines.append(f"     [{opt}]")
                    elif isinstance(opt, dict):
                        opt_id = opt.get("id", "?")
                        label = opt.get("label", "")
                        lines.append(f"     [{opt_id}] {label}")
            
            recommendation = decision.get("recommendation", "")
            if recommendation:
                lines.append(f"     Recommended: {recommendation}")
        lines.append("")
    
    tomorrow_plan = review_pack.get("tomorrow_plan", "")
    if tomorrow_plan:
        lines.append(f"Tomorrow's Plan: {tomorrow_plan}")
        lines.append("")
    
    doctor_assessment = review_pack.get("doctor_assessment", {})
    if doctor_assessment:
        status = doctor_assessment.get("doctor_status", "")
        if status:
            lines.append(f"Workspace Status: {status}")
        recommended = doctor_assessment.get("recommended_action", "")
        if recommended:
            lines.append(f"Recommended Action: {recommended}")
        lines.append("")
    
    lines.append("---")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("Reply with your decisions:")
    lines.append("  DECISION A, DECISION B, DEFER, or RETRY")
    
    return "\n".join(lines)


def send_day_end_email(
    project_path: Path,
    notification: NotificationEvent,
    review_pack: dict[str, Any],
) -> tuple[bool, str | None]:
    """Send day-end summary email.
    
    Args:
        project_path: Project path
        notification: Notification event record
        review_pack: DailyReviewPack content
        
    Returns:
        Tuple of (success, message_id_or_error)
    """
    apply_resend_config_from_file()
    config = create_email_config(project_path)
    
    delivery_mode = os.getenv("ASYNCDEV_DELIVERY_MODE", "mock_file")
    if delivery_mode == "resend":
        delivery_channel = NotificationChannel.RESEND
    elif delivery_mode == "console":
        delivery_channel = NotificationChannel.CONSOLE
    else:
        delivery_channel = NotificationChannel.MOCK_FILE
    
    notification.delivery_channel = delivery_channel
    
    sender = EmailSender(config)
    
    subject = build_day_end_email_subject(review_pack, config)
    body = build_day_end_email_body(review_pack)
    
    email_data = {
        "decision_request_id": notification.event_id,
        "product_id": notification.product_id,
        "feature_id": notification.feature_id,
        "question": "Daily review summary",
        "options": [],
        "recommendation": "",
    }
    
    success, message_id = sender.send_decision_request(email_data)
    
    if success:
        notification.email_sent = True
        notification.email_sent_at = datetime.now()
        notification.resend_message_id = message_id
        notification.delivery_status = NotificationStatus.SENT
        
        store = NotificationStore(project_path)
        store.save_notification(notification)
        store.mark_sent(notification.event_id, message_id or "")
        
        return True, message_id
    
    return False, "Failed to send day-end email"


def auto_trigger_day_end_email(
    project_path: Path,
    review_pack: dict[str, Any],
    runstate: dict[str, Any],
) -> DayEndEmailResult:
    """Auto-trigger day-end summary email.
    
    Full flow:
    1. Check policy (should_send_day_end_email)
    2. Create notification record (create_day_end_notification)
    3. Send email via EmailSender
    4. Update notification state
    5. Return result
    
    Args:
        project_path: Project path
        review_pack: DailyReviewPack dict
        runstate: Current RunState
        
    Returns:
        DayEndEmailResult with outcome
    """
    policy_mode = get_policy_mode(runstate)
    notification_store = NotificationStore(project_path)
    
    should_send, skip_reason = should_send_day_end_email(
        review_pack, runstate, notification_store
    )
    
    if not should_send:
        return DayEndEmailResult(
            triggered=False,
            skipped_reason=skip_reason,
            policy_mode_at_trigger=policy_mode,
        )
    
    notification = create_day_end_notification(
        project_path, review_pack, runstate
    )
    
    if not notification:
        return DayEndEmailResult(
            triggered=False,
            skipped_reason="Failed to create notification record",
            policy_mode_at_trigger=policy_mode,
        )
    
    success, message_id = send_day_end_email(
        project_path, notification, review_pack
    )
    
    if not success:
        notification_store.mark_failed(notification.event_id, message_id or "Send failed")
        
        return DayEndEmailResult(
            triggered=False,
            notification_id=notification.event_id,
            error_message=message_id or "Failed to send day-end email",
            severity=notification.severity,
            policy_mode_at_trigger=policy_mode,
        )
    
    return DayEndEmailResult(
        triggered=True,
        notification_id=notification.event_id,
        resend_message_id=message_id,
        severity=notification.severity,
        policy_mode_at_trigger=policy_mode,
    )


def check_and_trigger_day_end(
    project_path: Path,
    review_pack: dict[str, Any],
) -> DayEndEmailResult:
    """Check and trigger day-end email if appropriate.
    
    Convenience function that loads RunState and triggers.
    
    Args:
        project_path: Project path
        review_pack: DailyReviewPack dict
        
    Returns:
        DayEndEmailResult with outcome
    """
    from runtime.state_store import StateStore
    
    state_store = StateStore(project_path)
    runstate = state_store.load_runstate() or {}
    
    return auto_trigger_day_end_email(project_path, review_pack, runstate)