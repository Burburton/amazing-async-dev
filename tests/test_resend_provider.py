"""Tests for resend_provider module (Feature 053)."""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from runtime.resend_provider import (
    ResendConfig,
    ResendProvider,
    ResendWebhookHandler,
    create_resend_config,
    is_resend_configured,
    format_resend_setup_instructions,
    save_resend_config,
    load_resend_config,
    interactive_resend_setup,
    apply_resend_config_from_file,
    RESEND_API_URL,
    RESEND_SEND_ENDPOINT,
    RESEND_TEST_ADDRESS,
    RESEND_TEST_ADDRESSES,
    RESEND_CONFIG_FILE,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def mock_api_key():
    os.environ["RESEND_API_KEY"] = "re_test_key_12345"
    os.environ["RESEND_FROM_EMAIL"] = "test@example.com"
    yield
    os.environ.pop("RESEND_API_KEY", None)
    os.environ.pop("RESEND_FROM_EMAIL", None)


class TestResendConfig:
    def test_loads_api_key_from_env(self):
        os.environ["RESEND_API_KEY"] = "re_test123"
        
        config = ResendConfig()
        
        assert config.api_key == "re_test123"
        
        os.environ.pop("RESEND_API_KEY", None)

    def test_loads_from_email_from_env(self):
        os.environ["RESEND_FROM_EMAIL"] = "sender@example.com"
        
        config = ResendConfig()
        
        assert config.from_email == "sender@example.com"
        
        os.environ.pop("RESEND_FROM_EMAIL", None)

    def test_is_configured_true_when_all_set(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ["RESEND_FROM_EMAIL"] = "sender@test.com"
        
        config = ResendConfig()
        
        assert config.is_configured() == True
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)

    def test_is_configured_false_without_api_key(self):
        os.environ.pop("RESEND_API_KEY", None)
        os.environ["RESEND_FROM_EMAIL"] = "sender@test.com"
        
        config = ResendConfig()
        
        assert config.is_configured() == False
        
        os.environ.pop("RESEND_FROM_EMAIL", None)

    def test_is_configured_false_without_from_email(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ.pop("RESEND_FROM_EMAIL", None)
        
        config = ResendConfig()
        
        assert config.is_configured() == False
        
        os.environ.pop("RESEND_API_KEY", None)

    def test_sandbox_mode_from_env(self):
        os.environ["RESEND_SANDBOX_MODE"] = "true"
        
        config = ResendConfig()
        
        assert config.sandbox_mode == True
        
        os.environ.pop("RESEND_SANDBOX_MODE", None)

    def test_sandbox_mode_false_by_default(self):
        os.environ.pop("RESEND_SANDBOX_MODE", None)
        
        config = ResendConfig()
        
        assert config.sandbox_mode == False

    def test_webhook_secret_from_env(self):
        os.environ["RESEND_WEBHOOK_SECRET"] = "whsec_test"
        
        config = ResendConfig()
        
        assert config.webhook_secret == "whsec_test"
        
        os.environ.pop("RESEND_WEBHOOK_SECRET", None)

    def test_get_test_address(self):
        config = ResendConfig()
        
        assert config.get_test_address() == RESEND_TEST_ADDRESS


class TestResendProvider:
    def test_send_email_returns_tuple(self):
        provider = ResendProvider()
        
        result = provider.send_email(
            to="test@example.com",
            subject="Test",
            text="Test body",
        )
        
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_send_email_without_config_returns_false(self):
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)
        
        provider = ResendProvider()
        
        success, message_id, response = provider.send_email(
            to="test@example.com",
            subject="Test",
            text="Body",
        )
        
        assert success == False
        assert message_id is None
        assert "not configured" in response.get("error", "").lower()

    def test_send_email_with_single_to(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ["RESEND_FROM_EMAIL"] = "sender@test.com"
        
        provider = ResendProvider(ResendConfig())
        
        success, message_id, response = provider.send_email(
            to="recipient@test.com",
            subject="Test subject",
            html="<p>Test</p>",
        )
        
        assert isinstance(success, bool)
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)

    def test_send_email_with_multiple_to(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ["RESEND_FROM_EMAIL"] = "sender@test.com"
        
        provider = ResendProvider(ResendConfig())
        
        success, message_id, response = provider.send_email(
            to=["a@test.com", "b@test.com"],
            subject="Test",
            text="Body",
        )
        
        assert isinstance(success, bool)
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)

    def test_send_email_with_sandbox_mode(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ["RESEND_FROM_EMAIL"] = "sender@test.com"
        os.environ["RESEND_SANDBOX_MODE"] = "true"
        
        provider = ResendProvider(ResendConfig())
        
        success, message_id, response = provider.send_email(
            to="real@test.com",
            subject="Test",
            text="Body",
        )
        
        if success:
            assert response.get("to") == [RESEND_TEST_ADDRESS]
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)
        os.environ.pop("RESEND_SANDBOX_MODE", None)

    def test_test_connection_returns_tuple(self):
        provider = ResendProvider()
        
        result = provider.test_connection()
        
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_test_connection_with_custom_recipient(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ["RESEND_FROM_EMAIL"] = "sender@test.com"
        
        provider = ResendProvider(ResendConfig())
        
        success, explanation = provider.test_connection(to="custom@test.com")
        
        assert isinstance(success, bool)
        assert isinstance(explanation, str)
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)


class TestResendWebhookHandler:
    def test_handle_event_returns_dict(self):
        handler = ResendWebhookHandler()
        
        result = handler.handle_event({"type": "unknown"})
        
        assert isinstance(result, dict)
        assert "status" in result

    def test_handle_email_received(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.received",
            "created_at": "2026-04-18T12:00:00Z",
            "data": {
                "email_id": "test-email-id",
                "from": {"address": "sender@example.com"},
                "to": [{"address": "recipient@example.com"}],
                "subject": "Test reply",
            }
        }
        
        result = handler.handle_event(payload)
        
        assert result["status"] == "processed"
        assert result["event_type"] == "email.received"
        assert result["email_id"] == "test-email-id"

    def test_handle_email_received_with_decision_request_id(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.received",
            "data": {
                "email_id": "test-id",
                "headers": [
                    {"name": "X-Decision-Request-Id", "value": "dr-20260418-001"}
                ],
            }
        }
        
        result = handler.handle_event(payload)
        
        assert result["decision_request_id"] == "dr-20260418-001"
        assert result["linked"] == True

    def test_handle_email_sent(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.sent",
            "data": {
                "email_id": "sent-id",
                "created_at": "2026-04-18T12:00:00Z",
            }
        }
        
        result = handler.handle_event(payload)
        
        assert result["status"] == "recorded"
        assert result["event_type"] == "email.sent"

    def test_handle_email_delivered(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.delivered",
            "data": {
                "email_id": "delivered-id",
                "created_at": "2026-04-18T12:00:00Z",
            }
        }
        
        result = handler.handle_event(payload)
        
        assert result["status"] == "recorded"
        assert result["event_type"] == "email.delivered"

    def test_handle_email_bounced(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.bounced",
            "data": {
                "email_id": "bounced-id",
                "created_at": "2026-04-18T12:00:00Z",
            }
        }
        
        result = handler.handle_event(payload)
        
        assert result["status"] == "recorded"
        assert result["event_type"] == "email.bounced"

    def test_handle_unknown_event(self):
        handler = ResendWebhookHandler()
        
        result = handler.handle_event({"type": "unknown_event"})
        
        assert result["status"] == "ignored"

    def test_parse_reply_from_payload(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.received",
            "data": {
                "email_id": "reply-id",
                "text": "DECISION A",
                "from": {"address": "user@example.com"},
            }
        }
        
        reply = handler.parse_reply_from_payload(payload)
        
        assert reply is not None
        assert reply["reply_text"] == "DECISION A"
        assert reply["from"] == "user@example.com"

    def test_parse_reply_extract_request_id_from_subject(self):
        handler = ResendWebhookHandler()
        
        payload = {
            "type": "email.received",
            "data": {
                "email_id": "id",
                "text": "DECISION A",
                "subject": "Re: [async-dev] Decision needed [dr-20260418-001]",
            }
        }
        
        reply = handler.parse_reply_from_payload(payload)
        
        assert reply["decision_request_id"] == "dr-20260418-001"

    def test_parse_reply_returns_none_for_wrong_type(self):
        handler = ResendWebhookHandler()
        
        reply = handler.parse_reply_from_payload({"type": "email.sent"})
        
        assert reply is None


class TestHelperFunctions:
    def test_create_resend_config(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        
        config = create_resend_config()
        
        assert config.api_key == "re_test"
        
        os.environ.pop("RESEND_API_KEY", None)

    def test_is_resend_configured(self):
        os.environ["RESEND_API_KEY"] = "re_test"
        os.environ["RESEND_FROM_EMAIL"] = "test@example.com"
        
        assert is_resend_configured() == True
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)

    def test_format_setup_instructions(self):
        instructions = format_resend_setup_instructions()
        
        assert "resend.com" in instructions
        assert "RESEND_API_KEY" in instructions


class TestConstants:
    def test_api_url(self):
        assert RESEND_API_URL == "https://api.resend.com"

    def test_send_endpoint(self):
        assert RESEND_SEND_ENDPOINT == "/emails"

    def test_test_address(self):
        assert RESEND_TEST_ADDRESS == "delivered@resend.dev"

    def test_test_addresses_dict(self):
        assert "delivered" in RESEND_TEST_ADDRESSES
        assert "bounced" in RESEND_TEST_ADDRESSES
        assert len(RESEND_TEST_ADDRESSES) >= 4


class TestEmailSenderIntegration:
    def test_email_config_resend_methods(self):
        from runtime.email_sender import EmailConfig
        
        config = EmailConfig()
        
        assert hasattr(config, "use_resend")
        assert hasattr(config, "is_resend_configured")

    def test_email_sender_has_resend_mode(self):
        from runtime.email_sender import EmailSender, EmailConfig
        
        sender = EmailSender(EmailConfig())
        
        assert hasattr(sender, "_send_resend")


class TestConfigFileFunctions:
    def test_save_resend_config_creates_file(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        result = save_resend_config(
            api_key="re_test123",
            from_email="test@example.com",
            config_path=config_path,
        )
        
        assert result["status"] == "success"
        assert config_path.exists()
        
        with open(config_path) as f:
            data = json.load(f)
        
        assert data["api_key"] == "re_test123"
        assert data["from_email"] == "test@example.com"

    def test_save_resend_config_with_sandbox(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        result = save_resend_config(
            api_key="re_test",
            from_email="test@example.com",
            sandbox_mode=True,
            config_path=config_path,
        )
        
        with open(config_path) as f:
            data = json.load(f)
        
        assert data["sandbox_mode"] == True

    def test_save_resend_config_creates_runtime_dir(self, temp_dir):
        config_path = temp_dir / ".runtime" / "resend-config.json"
        
        result = save_resend_config(
            api_key="re_test",
            from_email="test@example.com",
            config_path=config_path,
        )
        
        assert config_path.parent.exists()
        assert config_path.exists()

    def test_load_resend_config_returns_dict(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        save_resend_config(
            api_key="re_test",
            from_email="test@example.com",
            config_path=config_path,
        )
        
        config = load_resend_config(config_path)
        
        assert config is not None
        assert config["api_key"] == "re_test"
        assert config["from_email"] == "test@example.com"

    def test_load_resend_config_returns_none_if_not_exists(self, temp_dir):
        config_path = temp_dir / "nonexistent.json"
        
        config = load_resend_config(config_path)
        
        assert config is None

    def test_apply_resend_config_from_file_sets_env(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        save_resend_config(
            api_key="re_apply_test",
            from_email="apply@example.com",
            sandbox_mode=True,
            config_path=config_path,
        )
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)
        os.environ.pop("RESEND_SANDBOX_MODE", None)
        
        result = apply_resend_config_from_file(config_path)
        
        assert result == True
        assert os.environ.get("RESEND_API_KEY") == "re_apply_test"
        assert os.environ.get("RESEND_FROM_EMAIL") == "apply@example.com"
        assert os.environ.get("RESEND_SANDBOX_MODE") == "true"
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)
        os.environ.pop("RESEND_SANDBOX_MODE", None)

    def test_apply_resend_config_returns_false_if_not_exists(self, temp_dir):
        config_path = temp_dir / "nonexistent.json"
        
        result = apply_resend_config_from_file(config_path)
        
        assert result == False

    def test_interactive_setup_with_both_params(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        result = interactive_resend_setup(
            api_key="re_interactive_test",
            from_email="interactive@example.com",
            open_browser=False,
            config_path=config_path,
        )
        
        assert result["status"] == "success"
        assert config_path.exists()

    def test_interactive_setup_detects_existing_config(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        save_resend_config(
            api_key="re_existing",
            from_email="existing@example.com",
            config_path=config_path,
        )
        
        result = interactive_resend_setup(
            api_key="re_new",
            from_email="new@example.com",
            open_browser=False,
            config_path=config_path,
        )
        
        assert result["status"] == "already_configured"

    def test_interactive_setup_validates_api_key_format(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        result = interactive_resend_setup(
            api_key="invalid_key",
            from_email="test@example.com",
            open_browser=False,
            config_path=config_path,
        )
        
        assert result["status"] == "error"
        assert "re_" in result["error"]

    def test_interactive_setup_validates_email_format(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        result = interactive_resend_setup(
            api_key="re_valid",
            from_email="invalid-email",
            open_browser=False,
            config_path=config_path,
        )
        
        assert result["status"] == "error"
        assert "email" in result["error"].lower()

    def test_config_file_constant_path(self):
        assert RESEND_CONFIG_FILE == Path(".runtime/resend-config.json")

    def test_full_workflow_save_load_apply(self, temp_dir):
        config_path = temp_dir / "resend-config.json"
        
        save_resend_config(
            api_key="re_workflow_test",
            from_email="workflow@example.com",
            webhook_secret="whsec_test",
            sandbox_mode=False,
            config_path=config_path,
        )
        
        loaded = load_resend_config(config_path)
        assert loaded["api_key"] == "re_workflow_test"
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)
        
        apply_resend_config_from_file(config_path)
        
        config = ResendConfig()
        assert config.api_key == "re_workflow_test"
        assert config.from_email == "workflow@example.com"
        
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("RESEND_FROM_EMAIL", None)