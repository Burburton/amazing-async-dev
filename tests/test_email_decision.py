"""Tests for async decision channel (Feature 021)."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta

from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
    DecisionType,
    DeliveryChannel,
)
from runtime.reply_parser import (
    parse_reply,
    validate_reply,
    create_reply_record,
    ValidationStatus,
    ReplyCommand,
    ParsedReply,
)
from runtime.email_sender import EmailConfig, EmailSender, create_email_config


class TestDecisionRequestStatus:
    """Tests for DecisionRequestStatus enum."""

    def test_status_values(self):
        """Status enum should have expected values."""
        assert DecisionRequestStatus.PENDING.value == "pending"
        assert DecisionRequestStatus.SENT.value == "sent"
        assert DecisionRequestStatus.RESOLVED.value == "resolved"
        assert DecisionRequestStatus.EXPIRED.value == "expired"


class TestDecisionType:
    """Tests for DecisionType enum."""

    def test_decision_type_values(self):
        """DecisionType enum should have expected values."""
        assert DecisionType.TECHNICAL.value == "technical"
        assert DecisionType.SCOPE.value == "scope"
        assert DecisionType.RISKY_CONFIRMATION.value == "risky_confirmation"


class TestDecisionRequestStore:
    """Tests for DecisionRequestStore."""

    def test_generate_request_id(self, temp_dir):
        """generate_request_id should produce valid ID pattern."""
        store = DecisionRequestStore(temp_dir)
        request_id = store.generate_request_id()
        assert request_id.startswith("dr-")
        assert len(request_id) == 15

    def test_create_request(self, temp_dir):
        """create_request should create valid request."""
        store = DecisionRequestStore(temp_dir)
        
        request = store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Use YAML or JSON?",
            options=[
                {"id": "A", "label": "YAML", "description": "Human-readable"},
                {"id": "B", "label": "JSON", "description": "Machine-readable"},
            ],
            recommendation="A - YAML is more readable",
        )
        
        assert request["product_id"] == "test-product"
        assert request["feature_id"] == "feature-001"
        assert request["decision_type"] == "technical"
        assert request["status"] == "pending"
        assert len(request["options"]) == 2

    def test_save_and_load_request(self, temp_dir):
        """save_request and load_request should work."""
        store = DecisionRequestStore(temp_dir)
        
        request = store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Test question",
            options=[{"id": "A", "label": "Option A"}],
            recommendation="A",
        )
        
        request_id = request["decision_request_id"]
        loaded = store.load_request(request_id)
        
        assert loaded is not None
        assert loaded["question"] == "Test question"

    def test_list_requests(self, temp_dir):
        """list_requests should return all requests."""
        store = DecisionRequestStore(temp_dir)
        
        store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question 1",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        
        store.create_request(
            product_id="test-product",
            feature_id="feature-002",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question 2",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        
        requests = store.list_requests()
        assert len(requests) == 2

    def test_list_requests_filter_by_status(self, temp_dir):
        """list_requests should filter by status."""
        store = DecisionRequestStore(temp_dir)
        
        request = store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        
        store.update_request_status(request["decision_request_id"], DecisionRequestStatus.SENT)
        
        pending = store.list_requests(status=DecisionRequestStatus.PENDING)
        sent = store.list_requests(status=DecisionRequestStatus.SENT)
        
        assert len(pending) == 0
        assert len(sent) == 1

    def test_update_request_status(self, temp_dir):
        """update_request_status should change status."""
        store = DecisionRequestStore(temp_dir)
        
        request = store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        
        updated = store.update_request_status(
            request["decision_request_id"],
            DecisionRequestStatus.RESOLVED,
            resolution="DECISION A",
        )
        
        assert updated["status"] == "resolved"
        assert updated["resolution"] == "DECISION A"

    def test_mark_sent(self, temp_dir):
        """mark_sent should update sent status."""
        store = DecisionRequestStore(temp_dir)
        
        request = store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        
        updated = store.mark_sent(
            request["decision_request_id"],
            mock_path=".runtime/email-outbox/test.md",
        )
        
        assert updated["status"] == "sent"
        assert updated["email_sent_mock_path"] == ".runtime/email-outbox/test.md"

    def test_get_pending_for_product(self, temp_dir):
        """get_pending_for_product should filter by product."""
        store = DecisionRequestStore(temp_dir)
        
        req_a = store.create_request(
            product_id="product-A",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question A",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        store.mark_sent(req_a["decision_request_id"])
        
        req_b = store.create_request(
            product_id="product-B",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question B",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        store.mark_sent(req_b["decision_request_id"])
        
        pending_A = store.get_pending_for_product("product-A")
        pending_B = store.get_pending_for_product("product-B")
        
        assert len(pending_A) == 1
        assert len(pending_B) == 1

    def test_get_statistics(self, temp_dir):
        """get_statistics should return counts."""
        store = DecisionRequestStore(temp_dir)
        
        stats = store.get_statistics()
        assert stats.get("pending", 0) == 0
        
        store.create_request(
            product_id="test-product",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Question",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
        )
        
        stats = store.get_statistics()
        assert stats.get("pending", 0) == 1


class TestReplyParser:
    """Tests for reply parser."""

    def test_parse_decision_command(self):
        """parse_reply should parse DECISION command."""
        parsed = parse_reply("DECISION A")
        assert parsed.command == ReplyCommand.DECISION
        assert parsed.argument == "A"
        assert parsed.is_valid == True

    def test_parse_approve_command(self):
        """parse_reply should parse APPROVE command."""
        parsed = parse_reply("APPROVE PUSH")
        assert parsed.command == ReplyCommand.APPROVE
        assert parsed.argument == "PUSH"
        assert parsed.is_valid == True

    def test_parse_defer_command(self):
        """parse_reply should parse DEFER command."""
        parsed = parse_reply("DEFER")
        assert parsed.command == ReplyCommand.DEFER
        assert parsed.argument is None
        assert parsed.is_valid == True

    def test_parse_retry_command(self):
        """parse_reply should parse RETRY command."""
        parsed = parse_reply("RETRY")
        assert parsed.command == ReplyCommand.RETRY
        assert parsed.is_valid == True

    def test_parse_continue_command(self):
        """parse_reply should parse CONTINUE command."""
        parsed = parse_reply("CONTINUE")
        assert parsed.command == ReplyCommand.CONTINUE
        assert parsed.is_valid == True

    def test_parse_invalid_syntax(self):
        """parse_reply should reject invalid syntax."""
        parsed = parse_reply("INVALID COMMAND")
        assert parsed.command is None
        assert parsed.is_valid == False

    def test_parse_case_insensitive(self):
        """parse_reply should be case insensitive."""
        parsed = parse_reply("decision a")
        assert parsed.command == ReplyCommand.DECISION
        assert parsed.is_valid == True

    def test_parse_whitespace_flexible(self):
        """parse_reply should handle extra whitespace."""
        parsed = parse_reply("  DECISION   A  ")
        assert parsed.command == ReplyCommand.DECISION
        assert parsed.argument == "A"
        assert parsed.is_valid == True


class TestValidateReply:
    """Tests for reply validation."""

    def test_validate_valid_decision(self):
        """validate_reply should accept valid option."""
        request = {
            "decision_request_id": "dr-001",
            "status": "sent",
            "options": [{"id": "A", "label": "Option A"}, {"id": "B", "label": "Option B"}],
        }
        parsed = parse_reply("DECISION A")
        
        is_valid, status, error = validate_reply(parsed, request)
        assert is_valid == True
        assert status == ValidationStatus.VALID

    def test_validate_invalid_option(self):
        """validate_reply should reject invalid option."""
        request = {
            "decision_request_id": "dr-001",
            "status": "sent",
            "options": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
        }
        parsed = parse_reply("DECISION C")
        
        is_valid, status, error = validate_reply(parsed, request)
        assert is_valid == False
        assert status == ValidationStatus.INVALID_OPTION

    def test_validate_duplicate_reply(self):
        """validate_reply should reject duplicate."""
        request = {
            "decision_request_id": "dr-001",
            "status": "resolved",
            "options": [{"id": "A", "label": "A"}],
        }
        parsed = parse_reply("DECISION A")
        
        is_valid, status, error = validate_reply(parsed, request)
        assert is_valid == False
        assert status == ValidationStatus.DUPLICATE_REPLY

    def test_validate_expired_request(self):
        """validate_reply should reject expired."""
        request = {
            "decision_request_id": "dr-001",
            "status": "expired",
            "options": [{"id": "A", "label": "A"}],
        }
        parsed = parse_reply("DECISION A")
        
        is_valid, status, error = validate_reply(parsed, request)
        assert is_valid == False
        assert status == ValidationStatus.EXPIRED_REQUEST


class TestCreateReplyRecord:
    """Tests for create_reply_record."""

    def test_create_reply_record(self):
        """create_reply_record should create valid record."""
        parsed = parse_reply("DECISION A")
        record = create_reply_record(
            request_id="dr-001",
            parsed=parsed,
            validation_status=ValidationStatus.VALID,
        )
        
        assert record["decision_request_id"] == "dr-001"
        assert record["reply_value"] == "DECISION A"
        assert record["validation_status"] == "valid"


class TestEmailConfig:
    """Tests for EmailConfig."""

    def test_default_config(self):
        """EmailConfig should have default values."""
        config = EmailConfig()
        assert config.delivery_mode == "mock_file"
        assert config.smtp_port == 587
        assert config.subject_prefix == "[async-dev]"

    def test_env_override(self):
        """EmailConfig should use env variables."""
        import os
        os.environ["ASYNCDEV_DELIVERY_MODE"] = "console"
        os.environ["ASYNCDEV_SMTP_PORT"] = "465"
        
        config = EmailConfig()
        assert config.delivery_mode == "console"
        assert config.smtp_port == 465
        
        del os.environ["ASYNCDEV_DELIVERY_MODE"]
        del os.environ["ASYNCDEV_SMTP_PORT"]

    def test_is_smtp_configured(self):
        """is_smtp_configured should check required fields."""
        config = EmailConfig()
        assert config.is_smtp_configured() == False
        
        import os
        os.environ["ASYNCDEV_SMTP_HOST"] = "smtp.example.com"
        os.environ["ASYNCDEV_SMTP_USERNAME"] = "user"
        os.environ["ASYNCDEV_SMTP_PASSWORD"] = "pass"
        
        config = EmailConfig()
        assert config.is_smtp_configured() == True
        
        del os.environ["ASYNCDEV_SMTP_HOST"]
        del os.environ["ASYNCDEV_SMTP_USERNAME"]
        del os.environ["ASYNCDEV_SMTP_PASSWORD"]


class TestEmailSender:
    """Tests for EmailSender."""

    def test_send_mock(self, temp_dir):
        """send_decision_request should write mock file."""
        config = EmailConfig()
        config.mock_outbox_path = temp_dir / "outbox"
        sender = EmailSender(config)
        
        request = {
            "decision_request_id": "dr-001",
            "product_id": "test-product",
            "feature_id": "feature-001",
            "question": "Test question?",
            "options": [{"id": "A", "label": "A"}],
            "recommendation": "A",
            "reply_format_hint": "Reply with: DECISION A, DEFER",
            "sent_at": datetime.now().isoformat(),
        }
        
        success, mock_path = sender.send_decision_request(request)
        assert success == True
        assert mock_path is not None
        
        mock_file = Path(mock_path)
        assert mock_file.exists()
        
        content = mock_file.read_text()
        assert "Test question?" in content
        assert "DECISION A" in content

    def test_send_console(self, temp_dir):
        """send_decision_request should output to console."""
        config = EmailConfig()
        config.delivery_mode = "console"
        sender = EmailSender(config)
        
        request = {
            "decision_request_id": "dr-001",
            "product_id": "test-product",
            "feature_id": "feature-001",
            "question": "Console test?",
            "options": [{"id": "A", "label": "A"}],
            "recommendation": "A",
            "reply_format_hint": "DECISION A",
            "sent_at": datetime.now().isoformat(),
        }
        
        success, _ = sender.send_decision_request(request)
        assert success == True

    def test_build_subject(self, temp_dir):
        """_build_subject should format correctly."""
        config = EmailConfig()
        sender = EmailSender(config)
        
        request = {
            "product_id": "my-app",
            "feature_id": "feature-001",
            "decision_request_id": "dr-001",
        }
        
        subject = sender._build_subject(request)
        assert "[async-dev]" in subject
        assert "my-app" in subject
        assert "dr-001" in subject

    def test_build_body(self, temp_dir):
        """_build_body should contain all fields."""
        config = EmailConfig()
        sender = EmailSender(config)
        
        request = {
            "decision_request_id": "dr-001",
            "question": "What format?",
            "options": [{"id": "A", "label": "YAML"}, {"id": "B", "label": "JSON"}],
            "recommendation": "A",
            "defer_impact": "Can proceed",
            "reply_format_hint": "DECISION A or B",
            "recommended_next_action_after_reply": "Continue",
            "sent_at": datetime.now().isoformat(),
        }
        
        body = sender._build_body(request)
        assert "What format?" in body
        assert "[A] YAML" in body
        assert "[B] JSON" in body
        assert "DECISION A or B" in body


class TestCLI:
    """Tests for CLI commands."""

    def test_email_decision_list(self, temp_dir):
        """email-decision list should work."""
        from typer.testing import CliRunner
        from cli.commands.email_decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--project", "test-project", "--path", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "No decision requests" in result.output or "Decision Requests" in result.output

    def test_email_decision_stats(self, temp_dir):
        """email-decision stats should work."""
        from typer.testing import CliRunner
        from cli.commands.email_decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["stats", "--project", "test-product", "--path", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "Statistics" in result.output


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)