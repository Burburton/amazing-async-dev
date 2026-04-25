"""Notification state persistence for Feature 080.

Manages notification lifecycle, dedupe checking, and delivery state tracking.
Follows existing patterns from DecisionRequestStore and FailureRecordStore.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
import json

from runtime.notification_event import (
    NotificationEvent,
    NotificationEventType,
    NotificationStatus,
    NotificationSeverity,
    generate_dedupe_key,
    generate_event_id,
    generate_content_hash,
)


class NotificationStore:
    """Store for notification state persistence and dedupe management.
    
    File structure:
    .runtime/notifications/
    ├── notif-YYYYMMDD-###.json
    └── dedupe-index.json (quick lookup)
    """
    
    DEFAULT_NOTIFICATIONS_PATH = ".runtime/notifications"
    DEFAULT_DUPE_INDEX_PATH = ".runtime/notifications/dedupe-index.json"
    
    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path
        self.notifications_path = project_path / self.DEFAULT_NOTIFICATIONS_PATH
        self.dedupe_index_path = project_path / self.DEFAULT_DUPE_INDEX_PATH
        self.notifications_path.mkdir(parents=True, exist_ok=True)
    
    def create_notification(
        self,
        event_type: NotificationEventType,
        primary_id: str,
        product_id: str,
        feature_id: str,
        reason: str,
        scope: str | None = None,
        run_id: str | None = None,
        request_id: str | None = None,
        context: dict[str, Any] | None = None,
        related_artifacts: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationEvent:
        """Create new notification event with dedupe key.
        
        Args:
            event_type: Type of notification event
            primary_id: Primary identifier for dedupe (request_id, date, etc.)
            product_id: Product context
            feature_id: Feature context
            reason: Why notification triggered
            scope: Optional scope qualifier for dedupe key
            run_id: Execution ID reference
            request_id: Decision request ID if applicable
            context: Additional context data
            related_artifacts: File paths to related artifacts
            metadata: Additional metadata
            
        Returns:
            Created NotificationEvent
        """
        event_id = generate_event_id(str(self.notifications_path))
        dedupe_key = generate_dedupe_key(event_type, primary_id, scope)
        
        event = NotificationEvent(
            event_id=event_id,
            event_type=event_type,
            dedupe_key=dedupe_key,
            product_id=product_id,
            feature_id=feature_id,
            run_id=run_id,
            request_id=request_id,
            reason=reason,
            context=context or {},
            related_artifacts=related_artifacts or [],
            metadata=metadata or {},
        )
        
        self.save_notification(event)
        self._update_dedupe_index(event)
        
        return event
    
    def save_notification(self, event: NotificationEvent) -> None:
        """Save notification event to file."""
        file_path = self.notifications_path / f"{event.event_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, indent=2)
    
    def load_notification(self, event_id: str) -> NotificationEvent | None:
        """Load notification by event ID."""
        file_path = self.notifications_path / f"{event_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        
        return NotificationEvent.from_dict(data)
    
    def load_notification_by_dedupe_key(
        self,
        dedupe_key: str,
    ) -> NotificationEvent | None:
        """Load notification by dedupe key.
        
        Returns most recent notification with this dedupe key.
        """
        index = self._load_dedupe_index()
        event_id = index.get(dedupe_key)
        
        if event_id:
            return self.load_notification(event_id)
        
        return None
    
    def check_dedupe(
        self,
        dedupe_key: str,
    ) -> tuple[bool, NotificationEvent | None]:
        """Check if notification already exists for this dedupe key.
        
        Args:
            dedupe_key: Dedupe key to check
            
        Returns:
            Tuple of (is_duplicate, existing_notification_if_found)
        """
        existing = self.load_notification_by_dedupe_key(dedupe_key)
        
        if existing:
            if existing.delivery_status in [
                NotificationStatus.PENDING,
                NotificationStatus.SENT,
                NotificationStatus.RETRY_NEEDED,
            ]:
                if existing.expires_at and datetime.now() < existing.expires_at:
                    return True, existing
        
        return False, None
    
    def mark_sent(
        self,
        event_id: str,
        message_id: str,
        delivery_channel: str = "mock_file",
    ) -> NotificationEvent | None:
        """Mark notification as sent.
        
        Args:
            event_id: Notification event ID
            message_id: Email message ID from provider
            delivery_channel: Channel used for delivery
            
        Returns:
            Updated notification or None if not found
        """
        event = self.load_notification(event_id)
        if not event:
            return None
        
        event.email_sent = True
        event.email_sent_at = datetime.now()
        event.resend_message_id = message_id
        event.delivery_status = NotificationStatus.SENT
        
        self.save_notification(event)
        return event
    
    def mark_delivered(
        self,
        event_id: str,
        webhook_data: dict[str, Any] | None = None,
    ) -> NotificationEvent | None:
        """Mark notification as delivered via webhook.
        
        Args:
            event_id: Notification event ID
            webhook_data: Webhook payload data
            
        Returns:
            Updated notification or None if not found
        """
        event = self.load_notification(event_id)
        if not event:
            return None
        
        event.delivery_status = NotificationStatus.DELIVERED
        
        if webhook_data:
            event.metadata["webhook_data"] = webhook_data
        
        self.save_notification(event)
        return event
    
    def mark_failed(
        self,
        event_id: str,
        error_message: str,
    ) -> NotificationEvent | None:
        """Mark notification as failed.
        
        Args:
            event_id: Notification event ID
            error_message: Error description
            
        Returns:
            Updated notification or None if not found
        """
        event = self.load_notification(event_id)
        if not event:
            return None
        
        event.delivery_status = NotificationStatus.FAILED
        event.error_message = error_message
        event.retry_count += 1
        
        if event.retry_count < event.max_retries:
            event.delivery_status = NotificationStatus.RETRY_NEEDED
        
        self.save_notification(event)
        return event
    
    def mark_skipped(
        self,
        event_id: str,
        skip_reason: str,
    ) -> NotificationEvent | None:
        """Mark notification as skipped (dedupe/policy).
        
        Args:
            event_id: Notification event ID
            skip_reason: Why notification was skipped
            
        Returns:
            Updated notification or None if not found
        """
        event = self.load_notification(event_id)
        if not event:
            return None
        
        event.delivery_status = NotificationStatus.SKIPPED
        event.email_sent = False
        event.metadata["skip_reason"] = skip_reason
        
        self.save_notification(event)
        return event
    
    def find_by_message_id(
        self,
        message_id: str,
    ) -> NotificationEvent | None:
        """Find notification by Resend message ID.
        
        Used for webhook correlation.
        
        Args:
            message_id: Resend message ID
            
        Returns:
            Matching notification or None
        """
        for file_path in self.notifications_path.glob("notif-*.json"):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            
            if data.get("resend_message_id") == message_id:
                return NotificationEvent.from_dict(data)
        
        return None
    
    def list_notifications(
        self,
        status: NotificationStatus | None = None,
        event_type: NotificationEventType | None = None,
        product_id: str | None = None,
        unresolved_only: bool = False,
    ) -> list[NotificationEvent]:
        """List notifications with optional filters.
        
        Args:
            status: Filter by delivery status
            event_type: Filter by event type
            product_id: Filter by product
            unresolved_only: Only show unresolved notifications
            
        Returns:
            List of matching notifications
        """
        notifications = []
        
        for file_path in self.notifications_path.glob("notif-*.json"):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            
            if status and data.get("delivery_status") != status.value:
                continue
            
            if event_type and data.get("event_type") != event_type.value:
                continue
            
            if product_id and data.get("product_id") != product_id:
                continue
            
            if unresolved_only:
                notification_status = data.get("delivery_status")
                if notification_status in [
                    NotificationStatus.DELIVERED.value,
                    NotificationStatus.SKIPPED.value,
                    NotificationStatus.EXPIRED.value,
                ]:
                    continue
            
            notifications.append(NotificationEvent.from_dict(data))
        
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)
    
    def get_pending_notifications(self) -> list[NotificationEvent]:
        """Get all pending notifications.
        
        Returns:
            List of notifications awaiting send
        """
        return self.list_notifications(status=NotificationStatus.PENDING)
    
    def get_unresolved_for_event(
        self,
        event_type: NotificationEventType,
        dedupe_key: str,
    ) -> NotificationEvent | None:
        """Get unresolved notification matching dedupe key.
        
        Args:
            event_type: Event type to match
            dedupe_key: Dedupe key to match
            
        Returns:
            Unresolved notification or None
        """
        notifications = self.list_notifications(
            event_type=event_type,
            unresolved_only=True,
        )
        
        for notification in notifications:
            if notification.dedupe_key == dedupe_key:
                return notification
        
        return None
    
    def get_statistics(self) -> dict[str, int]:
        """Get notification statistics by status."""
        stats = {}
        
        for status in NotificationStatus:
            count = len(self.list_notifications(status=status))
            stats[status.value] = count
        
        return stats
    
    def clear_expired_dedupe_keys(self) -> int:
        """Remove expired entries from dedupe index.
        
        Returns:
            Number of entries cleared
        """
        index = self._load_dedupe_index()
        cleared = 0
        
        for dedupe_key, event_id in list(index.items()):
            event = self.load_notification(event_id)
            if event:
                if event.expires_at and datetime.now() > event.expires_at:
                    del index[dedupe_key]
                    event.delivery_status = NotificationStatus.EXPIRED
                    self.save_notification(event)
                    cleared += 1
            else:
                del index[dedupe_key]
                cleared += 1
        
        self._save_dedupe_index(index)
        return cleared
    
    def _load_dedupe_index(self) -> dict[str, str]:
        """Load dedupe index from file."""
        if not self.dedupe_index_path.exists():
            return {}
        
        with open(self.dedupe_index_path, encoding="utf-8") as f:
            return json.load(f)
    
    def _save_dedupe_index(self, index: dict[str, str]) -> None:
        """Save dedupe index to file."""
        with open(self.dedupe_index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
    
    def _update_dedupe_index(self, event: NotificationEvent) -> None:
        """Update dedupe index with new event."""
        index = self._load_dedupe_index()
        index[event.dedupe_key] = event.event_id
        self._save_dedupe_index(index)


def create_day_end_notification(
    project_path: Path,
    review_pack: dict[str, Any],
    runstate: dict[str, Any],
) -> NotificationEvent | None:
    """Create day-end summary notification from review pack.
    
    Args:
        project_path: Project path
        review_pack: DailyReviewPack dict
        runstate: Current RunState
        
    Returns:
        Created notification or None if skipped
    """
    store = NotificationStore(project_path)
    
    date = review_pack.get("date", datetime.now().strftime("%Y-%m-%d"))
    product_id = review_pack.get("project_id", project_path.name)
    feature_id = review_pack.get("feature_id", "")
    
    dedupe_key = generate_dedupe_key(
        NotificationEventType.DAY_END_SUMMARY_READY,
        date,
        scope="review",
    )
    
    is_dup, existing = store.check_dedupe(dedupe_key)
    if is_dup:
        return None
    
    decisions_needed = review_pack.get("decisions_needed", [])
    blocked_items = review_pack.get("blocked_items", [])
    completed_items = review_pack.get("what_was_completed", [])
    
    context = {
        "date": date,
        "decisions_needed": decisions_needed,
        "blocked_items": blocked_items,
        "completed_items": completed_items,
        "today_goal": review_pack.get("today_goal", ""),
        "tomorrow_plan": review_pack.get("tomorrow_plan", ""),
    }
    
    event = store.create_notification(
        event_type=NotificationEventType.DAY_END_SUMMARY_READY,
        primary_id=date,
        scope="review",
        product_id=product_id,
        feature_id=feature_id,
        reason="Daily review summary ready for human attention",
        context=context,
        related_artifacts=[
            str(project_path / "runstate.md"),
            str(project_path / "reviews" / f"{date}-review.md"),
        ],
    )
    
    return event