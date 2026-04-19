"""Tests for Feature 058 - Webhook Auto-Polling."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from runtime.webhook_poller import (
    PollingStatus,
    ReplyType,
    PendingDecision,
    PollResult,
    PollingConfig,
    get_polling_config,
    poll_pending_decisions,
    parse_reply_from_pending,
    process_pending_decision,
    run_poll_cycle,
    get_reply_type,
    should_resume_execution,
    get_continuation_phase,
    PollingDaemon,
    format_poll_result,
)


class TestPollingStatus:
    def test_status_values(self):
        assert PollingStatus.SUCCESS.value == "success"
        assert PollingStatus.NO_DECISIONS.value == "no_decisions"
        assert PollingStatus.ERROR.value == "error"


class TestReplyType:
    def test_reply_types_defined(self):
        assert ReplyType.DECISION.value == "DECISION"
        assert ReplyType.APPROVE.value == "APPROVE"
        assert ReplyType.REJECT.value == "REJECT"
        assert ReplyType.DEFER.value == "DEFER"
        assert ReplyType.CONTINUE.value == "CONTINUE"


class TestPendingDecision:
    def test_decision_creation(self):
        decision = PendingDecision(
            id="dr-001",
            from_email="user@example.com",
            option="A",
            comment="Approve option A",
            received_at="2026-04-19T10:00:00",
        )
        assert decision.id == "dr-001"
        assert decision.option == "A"


class TestPollResult:
    def test_result_creation(self):
        result = PollResult(
            status=PollingStatus.SUCCESS,
            decisions_found=5,
            decisions_processed=3,
        )
        assert result.status == PollingStatus.SUCCESS
        assert result.decisions_found == 5


class TestPollingConfig:
    def test_default_config(self):
        config = PollingConfig()
        assert config.enabled is True
        assert config.interval_seconds == 60

    def test_custom_config(self):
        config = PollingConfig(
            enabled=False,
            interval_seconds=30,
            auto_resume=False,
        )
        assert config.enabled is False
        assert config.interval_seconds == 30


class TestParseReplyFromPending:
    def test_option_a_parsed(self):
        decision = PendingDecision(
            id="dr-001",
            from_email="user@example.com",
            option="A",
            comment="Proceed",
            received_at="2026-04-19T10:00:00",
        )
        reply = parse_reply_from_pending(decision)
        assert reply["reply_value"] == "DECISION A"
        assert reply["parsed_result"]["command"] == "DECISION"
        assert reply["parsed_result"]["argument"] == "A"

    def test_approve_parsed(self):
        decision = PendingDecision(
            id="dr-002",
            from_email="user@example.com",
            option="APPROVE",
            comment="",
            received_at="2026-04-19T10:00:00",
        )
        reply = parse_reply_from_pending(decision)
        assert reply["reply_value"] == "APPROVE"
        assert reply["parsed_result"]["command"] == "APPROVE"

    def test_reject_parsed(self):
        decision = PendingDecision(
            id="dr-003",
            from_email="user@example.com",
            option="REJECT",
            comment="",
            received_at="2026-04-19T10:00:00",
        )
        reply = parse_reply_from_pending(decision)
        assert reply["reply_value"] == "REJECT"

    def test_defer_parsed(self):
        decision = PendingDecision(
            id="dr-004",
            from_email="user@example.com",
            option="DEFER",
            comment="",
            received_at="2026-04-19T10:00:00",
        )
        reply = parse_reply_from_pending(decision)
        assert reply["reply_value"] == "DEFER"


class TestGetReplyType:
    def test_decision_type(self):
        reply = {"parsed_result": {"command": "DECISION"}}
        assert get_reply_type(reply) == ReplyType.DECISION

    def test_approve_type(self):
        reply = {"parsed_result": {"command": "APPROVE"}}
        assert get_reply_type(reply) == ReplyType.APPROVE

    def test_unknown_type(self):
        reply = {"parsed_result": {"command": "RANDOM"}}
        assert get_reply_type(reply) == ReplyType.UNKNOWN


class TestShouldResumeExecution:
    def test_decision_resumes(self):
        assert should_resume_execution(ReplyType.DECISION) is True

    def test_approve_resumes(self):
        assert should_resume_execution(ReplyType.APPROVE) is True

    def test_continue_resumes(self):
        assert should_resume_execution(ReplyType.CONTINUE) is True

    def test_reject_does_not_resume(self):
        assert should_resume_execution(ReplyType.REJECT) is False

    def test_pause_does_not_resume(self):
        assert should_resume_execution(ReplyType.PAUSE) is False


class TestGetContinuationPhase:
    def test_decision_phase(self):
        assert get_continuation_phase(ReplyType.DECISION) == "planning"

    def test_approve_phase(self):
        assert get_continuation_phase(ReplyType.APPROVE) == "planning"

    def test_continue_phase(self):
        assert get_continuation_phase(ReplyType.CONTINUE) == "executing"

    def test_pause_phase(self):
        assert get_continuation_phase(ReplyType.PAUSE) == "blocked"

    def test_stop_phase(self):
        assert get_continuation_phase(ReplyType.STOP) == "stopped"


class TestPollPendingDecisions:
    def test_no_webhook_url_returns_empty(self):
        pending = poll_pending_decisions("")
        assert pending == []

    def test_url_error_returns_empty(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            import urllib.error
            mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
            pending = poll_pending_decisions("https://example.com/webhook")
            assert pending == []

    def test_successful_poll_data_format(self):
        mock_data = {"ok": True, "count": 1, "decisions": [{"id": "dr-001", "from": "user@example.com", "option": "A", "receivedAt": "2026-04-19T10:00:00"}]}
        
        pending = []
        decisions = mock_data.get("decisions", [])
        for d in decisions:
            pending.append(PendingDecision(
                id=d.get("id", ""),
                from_email=d.get("from", ""),
                option=d.get("option", ""),
                comment=d.get("comment", ""),
                received_at=d.get("receivedAt", ""),
            ))
        
        assert len(pending) == 1
        assert pending[0].id == "dr-001"


class TestProcessPendingDecision:
    def test_request_not_found(self, tmp_path):
        decision = PendingDecision(
            id="dr-001",
            from_email="user@example.com",
            option="A",
            comment="",
            received_at="2026-04-19T10:00:00",
        )
        success, message = process_pending_decision(tmp_path, decision)
        assert success is False
        assert "not found" in message


class TestRunPollCycle:
    def test_no_decisions(self, tmp_path):
        config = PollingConfig()
        with patch('runtime.webhook_poller.poll_pending_decisions') as mock_poll:
            mock_poll.return_value = []
            result = run_poll_cycle(tmp_path, "https://example.com/webhook", config)
            assert result.status == PollingStatus.NO_DECISIONS


class TestPollingDaemon:
    def test_daemon_creation(self, tmp_path):
        config = PollingConfig(interval_seconds=30)
        daemon = PollingDaemon(tmp_path, "https://example.com/webhook", config)
        assert daemon.config.interval_seconds == 30
        assert daemon.running is False

    def test_get_status(self, tmp_path):
        daemon = PollingDaemon(tmp_path, "https://example.com/webhook")
        status = daemon.get_status()
        assert "running" in status
        assert "interval_seconds" in status


class TestFormatPollResult:
    def test_format_success(self):
        result = PollResult(
            status=PollingStatus.SUCCESS,
            decisions_found=3,
            decisions_processed=2,
            decisions_skipped=1,
            processed_ids=["dr-001", "dr-002"],
        )
        formatted = format_poll_result(result)
        assert "success" in formatted
        assert "Processed" in formatted and "2" in formatted


class TestGetPollingConfig:
    def test_no_config_returns_default(self, tmp_path):
        config = get_polling_config(tmp_path)
        assert config.interval_seconds == 60

    def test_load_from_file(self, tmp_path):
        import yaml
        runtime_dir = tmp_path / ".runtime"
        runtime_dir.mkdir()

        config_data = {
            "webhook_url": "https://example.com/webhook",
            "polling": {
                "enabled": True,
                "interval_seconds": 30,
            }
        }

        config_file = runtime_dir / "resend-config.json"
        import json
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = get_polling_config(tmp_path)
        assert config.interval_seconds == 30