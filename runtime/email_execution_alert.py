"""Execution failed notification handler for Feature 081.

Sends alerts when execution fails, with immediate notification (CRITICAL severity).
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
from runtime.email_sender import EmailSender, create_email_config, render_html_email
from runtime.resend_provider import apply_resend_config_from_file


def handle_execution_failed(
    project_path: Path,
    execution_id: str,
    error_summary: str,
    what_was_attempted: str = "",
    duration: str = "",
    impact: str = "",
) -> tuple[bool, str | None]:
    """Handle execution failed event - send alert email.

    Args:
        project_path: Project path
        execution_id: ID of failed execution
        error_summary: Brief summary of the error
        what_was_attempted: Description of what was being attempted
        duration: How long the execution ran before failing
        impact: Impact assessment

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
        NotificationEventType.EXECUTION_FAILED,
        execution_id,
        scope="execution"
    )

    notification = NotificationEvent(
        event_id=event_id,
        event_type=NotificationEventType.EXECUTION_FAILED,
        dedupe_key=dedupe_key,
        severity=NotificationSeverity.CRITICAL,
        product_id=product_id,
        feature_id=feature_id,
        run_id=execution_id,
        reason=error_summary,
        title=f"Execution Failed: {execution_id}",
        message=error_summary,
        context={
            "execution_id": execution_id,
            "error_summary": error_summary,
            "what_was_attempted": what_was_attempted,
            "duration": duration,
            "impact": impact,
        },
    )

    notification_store = NotificationStore(project_path)
    notification_store.save_notification(notification)

    success, message_id = _send_execution_failed_email(
        project_path=project_path,
        notification=notification,
        error_summary=error_summary,
        what_was_attempted=what_was_attempted,
        duration=duration,
        impact=impact,
    )

    if success:
        notification.email_sent = True
        notification.email_sent_at = datetime.now()
        notification.delivery_status = NotificationStatus.SENT
        notification.resend_message_id = message_id
        notification_store.save_notification(notification)
        notification_store.mark_sent(event_id, message_id or "")

    return success, event_id


def _send_execution_failed_email(
    project_path: Path,
    notification: NotificationEvent,
    error_summary: str,
    what_was_attempted: str,
    duration: str,
    impact: str,
) -> tuple[bool, str | None]:
    """Send execution failed email."""
    apply_resend_config_from_file()
    config = create_email_config(project_path)
    sender = EmailSender(config)

    request = {
        "decision_request_id": notification.event_id,
        "product_id": notification.product_id,
        "feature_id": notification.feature_id,
        "question": "Execution failed - requires attention",
        "options": [
            {"id": "retry", "label": "Retry Execution", "description": "Retry with same approach"},
            {"id": "abort", "label": "Abort", "description": "Stop and wait for instructions"},
            {"id": "continue", "label": "Continue", "description": "Continue despite failure"},
        ],
        "recommendation": "Review error details and decide",
        "reply_format_hint": "DECISION retry, abort, or continue",
        "execution_id": notification.run_id,
        "error_summary": error_summary,
        "what_was_attempted": what_was_attempted,
        "duration": duration,
        "impact": impact,
        "failed_at": notification.created_at.isoformat(),
        "retry_url": f"https://async-dev.example.com/retry/{notification.run_id}",
        "view_details_url": f"https://async-dev.example.com/execution/{notification.run_id}",
        "reply_base_url": "https://async-dev.example.com/reply",
    }

    return sender.send_decision_request(request)


def build_execution_failed_context(
    project_path: Path,
    execution_id: str,
    error_summary: str,
    what_was_attempted: str = "",
    duration: str = "",
    impact: str = "",
) -> dict[str, Any]:
    """Build context for execution failed email template.

    Returns context dict for HTML template rendering.
    """
    from runtime.state_store import StateStore

    store = StateStore(project_path)
    runstate = store.load_runstate()

    product_id = runstate.get("product_id", project_path.name) if runstate else project_path.name
    feature_id = runstate.get("feature_id", "unknown") if runstate else "unknown"

    return {
        "project_id": product_id,
        "feature_id": feature_id,
        "execution_id": execution_id,
        "error_summary": error_summary,
        "what_was_attempted": what_was_attempted,
        "duration": duration,
        "impact": impact,
        "failed_at": datetime.now().isoformat(),
        "retry_url": f"https://async-dev.example.com/retry/{execution_id}",
        "view_details_url": f"https://async-dev.example.com/execution/{execution_id}",
    }
