"""Tests for Feature 059 - Browser Verification Completion Enforcement."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import json

from runtime.verification_session import (
    VerificationSessionStatus,
    TimeoutAction,
    VerificationSession,
    VerificationReminder,
    VerificationSessionManager,
    format_reminder,
    generate_session_id,
    DEFAULT_TIMEOUT,
)

from runtime.verification_enforcer import (
    create_verification_session,
    register_dev_server,
    begin_verification,
    complete_verification,
    check_verification_status,
    enforce_completion,
    get_browser_verification_for_execution_result,
    can_mark_execution_success,
)


class TestVerificationSessionStatus:
    def test_status_values(self):
        assert VerificationSessionStatus.PENDING.value == "pending"
        assert VerificationSessionStatus.SERVER_STARTED.value == "server_started"
        assert VerificationSessionStatus.TIMEOUT.value == "timeout"

    def test_all_statuses_defined(self):
        statuses = [
            VerificationSessionStatus.PENDING,
            VerificationSessionStatus.SERVER_STARTED,
            VerificationSessionStatus.VERIFICATION_IN_PROGRESS,
            VerificationSessionStatus.COMPLETE,
            VerificationSessionStatus.TIMEOUT,
            VerificationSessionStatus.EXCEPTION,
        ]
        assert len(statuses) == 6


class TestVerificationSession:
    def test_session_creation(self):
        session = VerificationSession(
            session_id="vs-001",
            project_id="test-project",
            started_at=datetime.now(),
        )
        assert session.session_id == "vs-001"
        assert session.status == VerificationSessionStatus.PENDING
        assert session.timeout_seconds == DEFAULT_TIMEOUT

    def test_session_with_custom_timeout(self):
        session = VerificationSession(
            session_id="vs-002",
            project_id="test-project",
            started_at=datetime.now(),
            timeout_seconds=60,
        )
        assert session.timeout_seconds == 60


class TestVerificationSessionManager:
    def test_create_session(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        session = manager.create_session("test-project")

        assert session.session_id.startswith("vs-")
        assert session.project_id == "test-project"
        assert session.status == VerificationSessionStatus.PENDING

    def test_register_dev_server(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")
        manager.start_dev_server("http://localhost:3000", 3000, 12345)

        assert manager.active_session.dev_server_url == "http://localhost:3000"
        assert manager.active_session.dev_server_port == 3000
        assert manager.active_session.status == VerificationSessionStatus.SERVER_STARTED

    def test_begin_verification(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")
        manager.start_dev_server("http://localhost:3000", 3000, 12345)
        manager.start_verification()

        assert manager.active_session.verification_attempted is True
        assert manager.active_session.attempts == 1
        assert manager.active_session.status == VerificationSessionStatus.VERIFICATION_IN_PROGRESS

    def test_complete_verification(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")
        manager.start_dev_server("http://localhost:3000", 3000, 12345)
        manager.start_verification()
        manager.complete_verification({"passed": 5, "failed": 0})

        assert manager.active_session.verification_complete is True
        assert manager.active_session.status == VerificationSessionStatus.COMPLETE
        assert manager.active_session.result["passed"] == 5

    def test_check_timeout_not_exceeded(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        session = manager.create_session("test-project")
        session.started_at = datetime.now()

        assert manager.check_timeout() is False

    def test_check_timeout_exceeded(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        session = manager.create_session("test-project", timeout_seconds=1)
        session.started_at = datetime.now() - timedelta(seconds=5)

        assert manager.check_timeout() is True

    def test_get_elapsed_seconds(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")

        elapsed = manager.get_elapsed_seconds()
        assert elapsed >= 0
        assert elapsed < 10

    def test_get_remaining_seconds(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project", timeout_seconds=120)

        remaining = manager.get_remaining_seconds()
        assert remaining > 100
        assert remaining <= 120

    def test_enforce_timeout(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        session = manager.create_session("test-project", timeout_seconds=1)
        session.started_at = datetime.now() - timedelta(seconds=5)

        result = manager.enforce_timeout()

        assert result["status"] == "timeout"
        assert result["executed"] is False
        assert result["exception_reason"] == "verification_timeout"

    def test_get_reminder(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")
        manager.start_dev_server("http://localhost:3000", 3000, 12345)

        reminder = manager.get_reminder()

        assert reminder is not None
        assert reminder.session_id.startswith("vs-")
        assert reminder.dev_server_url == "http://localhost:3000"

    def test_no_reminder_when_complete(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")
        manager.start_dev_server("http://localhost:3000", 3000, 12345)
        manager.start_verification()
        manager.complete_verification({"passed": 1})

        reminder = manager.get_reminder()

        assert reminder is None

    def test_session_persistence(self, tmp_path):
        manager1 = VerificationSessionManager(tmp_path)
        manager1.create_session("test-project")
        manager1.start_dev_server("http://localhost:3000", 3000, 12345)

        manager2 = VerificationSessionManager(tmp_path)
        assert manager2.active_session is not None
        assert manager2.active_session.dev_server_url == "http://localhost:3000"

    def test_clear_session(self, tmp_path):
        manager = VerificationSessionManager(tmp_path)
        manager.create_session("test-project")
        manager.clear_session()

        assert manager.active_session is None
        assert not manager.sessions_path.exists()


class TestFormatReminder:
    def test_format_contains_url(self):
        reminder = VerificationReminder(
            session_id="vs-001",
            elapsed_seconds=30,
            remaining_seconds=90,
            dev_server_url="http://localhost:3000",
            must_action="Continue browser verification",
        )
        formatted = format_reminder(reminder)

        assert "http://localhost:3000" in formatted
        assert "30s" in formatted
        assert "90s" in formatted


class TestVerificationEnforcer:
    def test_create_verification_session(self, tmp_path):
        result = create_verification_session(tmp_path, "test-project")

        assert "session_id" in result
        assert result["status"] == "pending"

    def test_check_verification_status_no_session(self, tmp_path):
        result = check_verification_status(tmp_path)

        assert result["status"] == "no_session"

    def test_check_verification_status_pending(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)

        result = check_verification_status(tmp_path)

        assert result["status"] == "pending"
        assert result["must_action"] == "continue_verification"

    def test_check_verification_status_complete(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)
        begin_verification(tmp_path)
        complete_verification(tmp_path, {"passed": 1})

        result = check_verification_status(tmp_path)

        assert result["status"] == "complete"

    def test_enforce_completion_no_session(self, tmp_path):
        result = enforce_completion(tmp_path)

        assert result["status"] == "no_session"
        assert result["enforced"] is False

    def test_enforce_completion_pending(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)

        result = enforce_completion(tmp_path)

        assert result["enforced"] is True
        assert result["must_continue"] is True

    def test_get_browser_verification_no_session(self, tmp_path):
        result = get_browser_verification_for_execution_result(tmp_path)

        assert result["executed"] is False
        assert result["exception_reason"] == "no_verification_session"

    def test_get_browser_verification_pending(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)

        result = get_browser_verification_for_execution_result(tmp_path)

        assert result["executed"] is False
        assert result["exception_reason"] == "verification_pending"
        assert result["must_complete"] is True

    def test_get_browser_verification_complete(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)
        begin_verification(tmp_path)
        complete_verification(tmp_path, {"executed": True, "passed": 5})

        result = get_browser_verification_for_execution_result(tmp_path)

        assert result["executed"] is True
        assert result["passed"] == 5

    def test_can_mark_execution_success_no_session(self, tmp_path):
        can_mark, reason = can_mark_execution_success(tmp_path)

        assert can_mark is True
        assert "No verification session" in reason

    def test_can_mark_execution_success_pending(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)

        can_mark, reason = can_mark_execution_success(tmp_path)

        assert can_mark is False
        assert "pending" in reason

    def test_can_mark_execution_success_complete(self, tmp_path):
        create_verification_session(tmp_path, "test-project")
        register_dev_server(tmp_path, "http://localhost:3000", 3000, 12345)
        begin_verification(tmp_path)
        complete_verification(tmp_path, {"passed": 1})

        can_mark, reason = can_mark_execution_success(tmp_path)

        assert can_mark is True
        assert "complete" in reason


class TestGenerateSessionId:
    def test_session_id_format(self):
        session_id = generate_session_id("test-project")

        assert session_id.startswith("vs-")
        assert "test-project" in session_id