"""Tests for Feature 052 - Future Adapter Readiness."""

import pytest
from pathlib import Path

from runtime.channel_adapter import (
    ChannelType,
    ChannelConfig,
    ChannelMessage,
    ChannelResult,
    ChannelAdapter,
    ChannelRegistry,
    get_message_for_channel,
    is_channel_portable,
    get_canonical_channel,
)


class TestChannelType:
    def test_channel_types_defined(self):
        assert ChannelType.EMAIL.value == "email"
        assert ChannelType.SLACK.value == "slack"
        assert ChannelType.TELEGRAM.value == "telegram"
        assert ChannelType.WEBHOOK.value == "webhook"
        assert ChannelType.PUSH.value == "push"
        assert ChannelType.CONSOLE.value == "console"


class TestChannelConfig:
    def test_default_config(self):
        config = ChannelConfig()
        assert config.channel_type == ChannelType.EMAIL
        assert config.enabled is True
        assert config.priority == 1

    def test_custom_config(self):
        config = ChannelConfig(
            channel_type=ChannelType.SLACK,
            enabled=False,
            priority=2,
            extra_settings={"channel": "#decisions"},
        )
        assert config.channel_type == ChannelType.SLACK
        assert config.enabled is False
        assert config.extra_settings["channel"] == "#decisions"


class TestChannelMessage:
    def test_message_creation(self):
        message = ChannelMessage(
            message_id="msg-001",
            message_type="decision_request",
            subject="Decision Required",
            body="Please approve",
            recipient="user@example.com",
        )
        assert message.message_id == "msg-001"
        assert message.message_type == "decision_request"
        assert message.subject == "Decision Required"

    def test_message_with_metadata(self):
        message = ChannelMessage(
            message_id="msg-002",
            message_type="status_report",
            subject="Status",
            body="Progress update",
            recipient="",
            metadata={"report_type": "milestone"},
        )
        assert message.metadata["report_type"] == "milestone"


class TestChannelResult:
    def test_success_result(self):
        result = ChannelResult(
            success=True,
            channel_type=ChannelType.EMAIL,
            message_id="msg-001",
        )
        assert result.success is True
        assert result.channel_type == ChannelType.EMAIL

    def test_failure_result(self):
        result = ChannelResult(
            success=False,
            channel_type=ChannelType.EMAIL,
            error_message="Connection failed",
        )
        assert result.success is False
        assert result.error_message == "Connection failed"


class TestChannelRegistry:
    def test_registry_empty_initially(self):
        assert ChannelType.EMAIL not in ChannelRegistry._adapters

    def test_register_adapter(self):
        class MockAdapter(ChannelAdapter):
            def get_channel_type(self):
                return ChannelType.EMAIL
            def send_message(self, message):
                return ChannelResult(success=True, channel_type=ChannelType.EMAIL)
            def validate_config(self):
                return True, []
            def get_status(self):
                return {"enabled": True}

        ChannelRegistry.register(ChannelType.EMAIL, MockAdapter)
        assert ChannelType.EMAIL in ChannelRegistry.list_available()

    def test_get_adapter_registered(self):
        class MockAdapter(ChannelAdapter):
            def get_channel_type(self):
                return ChannelType.CONSOLE
            def send_message(self, message):
                return ChannelResult(success=True, channel_type=ChannelType.CONSOLE)
            def validate_config(self):
                return True, []
            def get_status(self):
                return {"enabled": True}

        ChannelRegistry.register(ChannelType.CONSOLE, MockAdapter)
        config = ChannelConfig(channel_type=ChannelType.CONSOLE)
        adapter = ChannelRegistry.get_adapter(ChannelType.CONSOLE, config)
        assert adapter is not None
        assert adapter.get_channel_type() == ChannelType.CONSOLE

    def test_get_adapter_not_registered(self):
        config = ChannelConfig(channel_type=ChannelType.TELEGRAM)
        adapter = ChannelRegistry.get_adapter(ChannelType.TELEGRAM, config)
        assert adapter is None

    def test_list_available(self):
        available = ChannelRegistry.list_available()
        assert isinstance(available, list)

    def test_is_registered(self):
        assert ChannelRegistry.is_registered(ChannelType.CONSOLE) is True
        assert ChannelRegistry.is_registered(ChannelType.TELEGRAM) is False


class TestGetMessageForChannel:
    def test_from_decision_request(self):
        request = {
            "decision_request_id": "dr-001",
            "question": "Approve deployment?",
            "options": ["A: Yes", "B: No"],
            "recommendation": "A",
            "delivery_recipient": "user@example.com",
        }
        message = get_message_for_channel(decision_request=request)
        assert message.message_type == "decision_request"
        assert "Approve" in message.subject

    def test_from_status_report(self):
        report = {
            "report_id": "sr-001",
            "summary": "Progress update",
            "current_state": "executing",
            "what_changed": ["Completed tests"],
        }
        message = get_message_for_channel(status_report=report)
        assert message.message_type == "status_report"
        assert "Status" in message.subject

    def test_from_digest(self):
        digest = {
            "digest_id": "digest-001",
            "digest_mode": "daily",
            "body": "Daily summary",
        }
        message = get_message_for_channel(digest=digest)
        assert message.message_type == "digest"
        assert "Digest" in message.subject

    def test_empty_message(self):
        message = get_message_for_channel()
        assert message.message_type == "empty"


class TestIsChannelPortable:
    def test_portable_decision_request(self):
        artifact = {"message_type": "decision_request", "question": "Test"}
        assert is_channel_portable(artifact) is True

    def test_not_portable_missing_type(self):
        artifact = {"question": "Test"}
        assert is_channel_portable(artifact) is False

    def test_portable_status_report(self):
        artifact = {"message_type": "status_report", "summary": "Test"}
        assert is_channel_portable(artifact) is True


class TestGetCanonicalChannel:
    def test_email_is_canonical(self):
        channel = get_canonical_channel()
        assert channel == ChannelType.EMAIL


class TestFormatDecisionRequestBody:
    def test_format_basic(self):
        from runtime.channel_adapter import format_decision_request_body
        request = {
            "question": "Approve?",
            "options": [{"label": "Yes"}, {"label": "No"}],
            "recommendation": "Yes",
        }
        body = format_decision_request_body(request)
        assert "Approve?" in body
        assert "Yes" in body


class TestFormatStatusReportBody:
    def test_format_basic(self):
        from runtime.channel_adapter import format_status_report_body
        report = {
            "summary": "Progress",
            "current_state": "executing",
            "what_changed": ["Tests passed"],
        }
        body = format_status_report_body(report)
        assert "Progress" in body
        assert "executing" in body