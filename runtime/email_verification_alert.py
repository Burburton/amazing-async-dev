"""Verification failed notification handler for Feature 081.

Sends alerts when browser verification fails (MEDIUM severity).
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.notification_event import (
    NotificationEvent,
    NotificationEventType,
    NotificationSeverity,
    NotificationStatus,
    NotificationChannel,
    generate_event_id,
    generate_dedupe_key,
)
from runtime.notification_store import NotificationStore
from runtime.email_sender import EmailSender, create_email_config
from runtime.resend_provider import apply_resend_config_from_file


def handle_verification_failed(
    project_path: Path,
    verification_id: str,
    failure_reason: str,
    what_was_verified: str = "",
    scenarios_run: int = 0,
    scenarios_passed: int = 0,
    screenshot_urls: list[str] | None = None,
) -> tuple[bool, str | None]:
    """Handle verification failed event - send alert email.

    Args:
        project_path: Project path
        verification_id: ID of failed verification
        failure_reason: Reason verification failed
        what_was_verified: Description of what was being verified
        scenarios_run: Number of test scenarios run
        scenarios_passed: Number that passed
        screenshot_urls: URLs to screenshots

    Returns:
        Tuple of (success, notification_id or error message)
    """
    from runtime.state_store import StateStore

    store = StateStore(project_path)
    runstate = store.load_runstate()

    product_id = runstate.get("product_id", project_path.name) if runstate else project_path.name
    feature_id = runstate.get("feature_id", "unknown") if runstate else "unknown"

    event_id = generate_event_id()
    dedupe_key = generate_dedupe_key(
        NotificationEventType.VERIFICATION_FAILED,
        verification_id,
        scope="verification"
    )

    notification = NotificationEvent(
        event_id=event_id,
        event_type=NotificationEventType.VERIFICATION_FAILED,
        dedupe_key=dedupe_key,
        severity=NotificationSeverity.MEDIUM,
        product_id=product_id,
        feature_id=feature_id,
        run_id=verification_id,
        reason=failure_reason,
        title=f"Verification Failed: {verification_id}",
        message=failure_reason,
        context={
            "verification_id": verification_id,
            "failure_reason": failure_reason,
            "what_was_verified": what_was_verified,
            "scenarios_run": scenarios_run,
            "scenarios_passed": scenarios_passed,
            "screenshot_urls": screenshot_urls or [],
        },
    )

    notification_store = NotificationStore(project_path)
    notification_store.save_notification(notification)

    success, message_id = _send_verification_failed_email(
        project_path=project_path,
        notification=notification,
        failure_reason=failure_reason,
        what_was_verified=what_was_verified,
        scenarios_run=scenarios_run,
        scenarios_passed=scenarios_passed,
        screenshot_urls=screenshot_urls or [],
    )

    if success:
        notification.email_sent = True
        notification.email_sent_at = datetime.now()
        notification.delivery_status = NotificationStatus.SENT
        notification.resend_message_id = message_id
        notification_store.save_notification(notification)
        notification_store.mark_sent(event_id, message_id or "")

    return success, event_id


def _send_verification_failed_email(
    project_path: Path,
    notification: NotificationEvent,
    failure_reason: str,
    what_was_verified: str,
    scenarios_run: int,
    scenarios_passed: int,
    screenshot_urls: list[str],
) -> tuple[bool, str | None]:
    """Send verification failed email."""
    apply_resend_config_from_file()
    config = create_email_config(project_path)
    sender = EmailSender(config)

    request = {
        "decision_request_id": notification.event_id,
        "product_id": notification.product_id,
        "feature_id": notification.feature_id,
        "question": "Verification failed - requires review",
        "options": [
            {"id": "retry", "label": "Retry Verification", "description": "Run verification again"},
            {"id": "skip", "label": "Skip Verification", "description": "Proceed without verification"},
            {"id": "fix", "label": "Fix and Retry", "description": "Fix issues then retry"},
        ],
        "recommendation": "Review failure reason and decide",
        "reply_format_hint": "DECISION retry, skip, or fix",
        "verification_id": notification.run_id,
        "failure_reason": failure_reason,
        "what_was_verified": what_was_verified,
        "scenarios_run": scenarios_run,
        "scenarios_passed": scenarios_passed,
        "screenshot_urls": screenshot_urls,
        "failed_at": notification.created_at.isoformat(),
        "retry_url": f"https://async-dev.example.com/verify/retry/{notification.run_id}",
        "view_details_url": f"https://async-dev.example.com/verify/{notification.run_id}",
        "reply_base_url": "https://async-dev.example.com/reply",
    }

    return sender.send_decision_request(request)
