"""Tests for Feature 080 - Auto Email Notification."""

from datetime import datetime, timedelta
from pathlib import Path
import json
import pytest

from runtime.notification_event import (
    NotificationEvent,
    NotificationEventType,
    NotificationSeverity,
    NotificationStatus,
    NotificationChannel,
    generate_dedupe_key,
    generate_event_id,
    generate_content_hash,
    should_send_notification,
    get_severity_for_event_type,
    get_dedupe_window_for_event,
    NotificationTriggerResult,
)
from runtime.notification_store import (
    NotificationStore,
    create_day_end_notification,
)
from runtime.auto_day_end_email import (
    DayEndEmailResult,
    should_send_day_end_email,
    build_day_end_email_subject,
    build_day_end_email_body,
)


class TestNotificationEventModel:
    """Tests for NotificationEvent model."""
    
    def test_event_type_enum_values(self):
        assert NotificationEventType.MAJOR_DECISION_REQUIRED.value == "major_decision_required"
        assert NotificationEventType.DAY_END_SUMMARY_READY.value == "day_end_summary_ready"
        assert NotificationEventType.BLOCKED_WAITING_FOR_HUMAN.value == "blocked_waiting_for_human"
    
    def test_severity_enum_values(self):
        assert NotificationSeverity.CRITICAL.value == "critical"
        assert NotificationSeverity.HIGH.value == "high"
        assert NotificationSeverity.MEDIUM.value == "medium"
        assert NotificationSeverity.LOW.value == "low"
    
    def test_status_enum_values(self):
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.FAILED.value == "failed"
        assert NotificationStatus.SKIPPED.value == "skipped"
    
    def test_event_creation(self):
        event = NotificationEvent(
            event_id="notif-20260425-001",
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            dedupe_key="major_decision_required:decision:dr-001",
            product_id="test-project",
            feature_id="test-feature",
            reason="Test decision required",
        )
        
        assert event.event_id == "notif-20260425-001"
        assert event.event_type == NotificationEventType.MAJOR_DECISION_REQUIRED
        assert event.delivery_status == NotificationStatus.PENDING
        assert event.email_required is True
    
    def test_event_to_dict_and_from_dict(self):
        event = NotificationEvent(
            event_id="notif-20260425-001",
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            dedupe_key="major:decision:001",
            severity=NotificationSeverity.HIGH,
            product_id="test-project",
            feature_id="test-feature",
            reason="Test",
        )
        
        data = event.to_dict()
        assert data["event_id"] == "notif-20260425-001"
        assert data["event_type"] == "major_decision_required"
        
        restored = NotificationEvent.from_dict(data)
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type
        assert restored.severity == event.severity
    
    def test_severity_auto_set_from_event_type(self):
        event = NotificationEvent(
            event_id="notif-001",
            event_type=NotificationEventType.CRITICAL_ESCALATION_REQUIRED,
            dedupe_key="critical:escalation:001",
        )
        
        assert event.severity == NotificationSeverity.CRITICAL
    
    def test_dedupe_window_set_from_severity(self):
        event_high = NotificationEvent(
            event_id="notif-001",
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            dedupe_key="major:decision:001",
        )
        
        assert event_high.dedupe_window_seconds == 1800  # 30 min from event type override
        
        event_medium = NotificationEvent(
            event_id="notif-002",
            event_type=NotificationEventType.DAY_END_SUMMARY_READY,
            dedupe_key="day_end:review:2026-04-25",
        )
        
        assert event_medium.dedupe_window_seconds == 86400  # 24 hours for day-end


class TestDedupeKeyGeneration:
    """Tests for dedupe key generation."""
    
    def test_generate_dedupe_key_with_scope(self):
        key = generate_dedupe_key(
            NotificationEventType.MAJOR_DECISION_REQUIRED,
            "dr-20260425-001",
            scope="decision",
        )
        
        assert key == "major_decision_required:decision:dr-20260425-001"
    
    def test_generate_dedupe_key_without_scope(self):
        key = generate_dedupe_key(
            NotificationEventType.DAY_END_SUMMARY_READY,
            "2026-04-25",
        )
        
        assert key == "day_end_summary_ready:2026-04-25"
    
    def test_generate_content_hash(self):
        context1 = {"decision": "test", "options": ["A", "B"]}
        context2 = {"decision": "test", "options": ["A", "B"]}
        context3 = {"decision": "different", "options": ["A", "B"]}
        
        hash1 = generate_content_hash(context1)
        hash2 = generate_content_hash(context2)
        hash3 = generate_content_hash(context3)
        
        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 16


class TestShouldSendNotification:
    """Tests for notification policy checks."""
    
    def test_critical_always_sends(self):
        event = NotificationEvent(
            event_id="notif-001",
            event_type=NotificationEventType.CRITICAL_ESCALATION_REQUIRED,
            severity=NotificationSeverity.CRITICAL,
            dedupe_key="critical:001",
        )
        
        should, reason = should_send_notification(event, "low_interruption")
        assert should is True
        assert reason is None
    
    def test_low_interrupted_mode_skips_low_severity(self):
        event = NotificationEvent(
            event_id="notif-002",
            event_type=NotificationEventType.DAY_END_SUMMARY_READY,
            severity=NotificationSeverity.LOW,
            dedupe_key="day_end:001",
            email_required=True,
        )
        
        should, reason = should_send_notification(event, "low_interruption")
        assert should is False
        assert "Low interruption" in reason
    
    def test_duplicate_pending_skips(self):
        event = NotificationEvent(
            event_id="notif-003",
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            dedupe_key="major:decision:001",
        )
        
        existing = [
            {"dedupe_key": "major:decision:001", "delivery_status": "pending"}
        ]
        
        should, reason = should_send_notification(event, "balanced", existing)
        assert should is False
        assert "Duplicate pending" in reason


class TestNotificationStore:
    """Tests for notification state persistence."""
    
    @pytest.fixture
    def temp_project_path(self, tmp_path):
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        return project_path
    
    def test_store_creation(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        assert store.notifications_path.exists()
    
    def test_create_notification(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        event = store.create_notification(
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            primary_id="dr-001",
            product_id="test-project",
            feature_id="test-feature",
            reason="Test notification",
            scope="decision",
        )
        
        assert event.event_id.startswith("notif-")
        assert event.event_type == NotificationEventType.MAJOR_DECISION_REQUIRED
        assert event.delivery_status == NotificationStatus.PENDING
        
        loaded = store.load_notification(event.event_id)
        assert loaded is not None
        assert loaded.event_id == event.event_id
    
    def test_check_dedupe(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        store.create_notification(
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            primary_id="dr-001",
            product_id="test",
            feature_id="test",
            reason="First",
            scope="decision",
        )
        
        is_dup, existing = store.check_dedupe("major_decision_required:decision:dr-001")
        
        assert is_dup is True
        assert existing is not None
    
    def test_mark_sent(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        event = store.create_notification(
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            primary_id="dr-002",
            product_id="test",
            feature_id="test",
            reason="Test",
        )
        
        updated = store.mark_sent(event.event_id, "msg-123")
        
        assert updated is not None
        assert updated.email_sent is True
        assert updated.resend_message_id == "msg-123"
        assert updated.delivery_status == NotificationStatus.SENT
    
    def test_mark_failed(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        event = store.create_notification(
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            primary_id="dr-003",
            product_id="test",
            feature_id="test",
            reason="Test",
        )
        
        updated = store.mark_failed(event.event_id, "SMTP error")
        
        assert updated.delivery_status == NotificationStatus.RETRY_NEEDED
        assert updated.error_message == "SMTP error"
        assert updated.retry_count == 1
    
    def test_list_notifications(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        store.create_notification(
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            primary_id="dr-004",
            product_id="test",
            feature_id="test",
            reason="Pending",
        )
        
        event = store.create_notification(
            event_type=NotificationEventType.DAY_END_SUMMARY_READY,
            primary_id="2026-04-25",
            product_id="test",
            feature_id="test",
            reason="Day-end",
            scope="review",
        )
        store.mark_sent(event.event_id, "msg-123")
        
        pending = store.list_notifications(status=NotificationStatus.PENDING)
        assert len(pending) >= 1
        
        sent = store.list_notifications(status=NotificationStatus.SENT)
        assert len(sent) >= 1
    
    def test_get_statistics(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        store.create_notification(
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            primary_id="dr-stats",
            product_id="test",
            feature_id="test",
            reason="Stats test",
        )
        
        stats = store.get_statistics()
        
        assert "pending" in stats
        assert stats["pending"] >= 1


class TestDayEndEmail:
    """Tests for day-end summary email logic."""
    
    @pytest.fixture
    def temp_project_path(self, tmp_path):
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        return project_path
    
    def test_should_send_day_end_with_decisions(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        review_pack = {
            "date": "2026-04-25",
            "decisions_needed": [{"decision": "Test decision"}],
            "blocked_items": [],
        }
        
        runstate = {"policy_mode": "balanced"}
        
        should, reason = should_send_day_end_email(review_pack, runstate, store)
        
        assert should is True
    
    def test_should_send_day_end_dedupe(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        review_pack = {
            "date": "2026-04-25",
            "decisions_needed": [{"decision": "Test"}],
        }
        
        runstate = {"policy_mode": "balanced"}
        
        should1, _ = should_send_day_end_email(review_pack, runstate, store)
        assert should1 is True
        
        store.create_notification(
            event_type=NotificationEventType.DAY_END_SUMMARY_READY,
            primary_id="2026-04-25",
            scope="review",
            product_id="test",
            feature_id="test",
            reason="Day-end",
        )
        
        should2, reason2 = should_send_day_end_email(review_pack, runstate, store)
        assert should2 is False
        assert "already sent" in reason2
    
    def test_should_send_day_end_low_interruption_no_critical(self, temp_project_path):
        store = NotificationStore(temp_project_path)
        
        review_pack = {
            "date": "2026-04-25",
            "decisions_needed": [],
            "blocked_items": [],
        }
        
        runstate = {"policy_mode": "low_interruption"}
        
        should, reason = should_send_day_end_email(review_pack, runstate, store)
        
        assert should is False
        assert "no decisions or blockers" in reason
    
    def test_build_day_end_email_body(self):
        review_pack = {
            "date": "2026-04-25",
            "project_id": "test-project",
            "feature_id": "test-feature",
            "today_goal": "Implement notification system",
            "what_was_completed": ["Created notification_event.py", "Created notification_store.py"],
            "blocked_items": [{"reason": "Waiting for decision"}],
            "decisions_needed": [{"decision": "Choose email provider", "options": ["A:Resend", "B:SMTP"]}],
            "tomorrow_plan": "Continue with integration tests",
        }
        
        body = build_day_end_email_body(review_pack)
        
        assert "2026-04-25" in body
        assert "test-project" in body
        assert "Completed Items:" in body
        assert "notification_event.py" in body
        assert "Blocked Items:" in body
        assert "Waiting for decision" in body
        assert "Decisions Required:" in body
        assert "Choose email provider" in body


class TestNotificationTriggerResult:
    """Tests for notification trigger result."""
    
    def test_result_triggered(self):
        result = NotificationTriggerResult(
            triggered=True,
            event_id="notif-001",
            resend_message_id="msg-123",
            event_type=NotificationEventType.MAJOR_DECISION_REQUIRED,
            severity=NotificationSeverity.HIGH,
        )
        
        data = result.to_dict()
        assert data["triggered"] is True
        assert data["event_id"] == "notif-001"
    
    def test_result_skipped(self):
        result = NotificationTriggerResult(
            triggered=False,
            skipped_reason="Duplicate pending",
        )
        
        assert result.triggered is False
        assert result.skipped_reason == "Duplicate pending"
    
    def test_result_failed(self):
        result = NotificationTriggerResult(
            triggered=False,
            event_id="notif-002",
            error_message="SMTP connection failed",
        )
        
        data = result.to_dict()
        assert data["triggered"] is False
        assert "SMTP" in data["error_message"]