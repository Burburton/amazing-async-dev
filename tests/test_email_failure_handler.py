"""Tests for email_failure_handler module (Feature 049)."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from runtime.email_failure_handler import (
    FailureType,
    TimeoutBehavior,
    RecoveryAction,
    FailureRecordStore,
    handle_send_failure,
    handle_timeout,
    handle_invalid_reply,
    detect_duplicate_reply,
    check_partial_state,
    get_recovery_recommendation,
    format_failure_summary,
    get_timeout_policy,
    validate_state_consistency,
    DEFAULT_TIMEOUT_HOURS,
    DEFAULT_MAX_RETRIES,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestFailureType:
    def test_all_failure_types_defined(self):
        assert FailureType.SEND_FAILED.value == "send_failed"
        assert FailureType.TIMEOUT_NO_REPLY.value == "timeout_no_reply"
        assert FailureType.INVALID_REPLY_SYNTAX.value == "invalid_reply_syntax"
        assert FailureType.DUPLICATE_REPLY.value == "duplicate_reply"

    def test_failure_type_count(self):
        assert len(FailureType) >= 9


class TestTimeoutBehavior:
    def test_all_timeout_behaviors_defined(self):
        assert TimeoutBehavior.WAIT.value == "wait"
        assert TimeoutBehavior.DEFER.value == "defer"
        assert TimeoutBehavior.DEFAULT_OPTION.value == "default_option"
        assert TimeoutBehavior.ESCALATE.value == "escalate"

    def test_timeout_behavior_count(self):
        assert len(TimeoutBehavior) >= 5


class TestRecoveryAction:
    def test_all_recovery_actions_defined(self):
        assert RecoveryAction.RETRY_SEND.value == "retry_send"
        assert RecoveryAction.PAUSE_FOR_HUMAN.value == "pause_for_human"
        assert RecoveryAction.MARK_BLOCKED.value == "mark_blocked"

    def test_recovery_action_count(self):
        assert len(RecoveryAction) >= 6


class TestFailureRecordStore:
    def test_store_creates_failures_path(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        assert store.failures_path.exists()

    def test_record_failure(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        record = store.record_failure(
            request_id="dr-001",
            failure_type=FailureType.SEND_FAILED,
            details={"error": "Connection refused"},
        )
        
        assert record["failure_id"].startswith("fail-")
        assert record["request_id"] == "dr-001"
        assert record["failure_type"] == "send_failed"
        assert record["resolved"] == False

    def test_load_failure(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        created = store.record_failure("dr-001", FailureType.SEND_FAILED)
        loaded = store.load_failure(created["failure_id"])
        
        assert loaded is not None
        assert loaded["request_id"] == "dr-001"

    def test_list_failures(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        store.record_failure("dr-001", FailureType.SEND_FAILED)
        store.record_failure("dr-002", FailureType.TIMEOUT_NO_REPLY)
        
        all_failures = store.list_failures()
        assert len(all_failures) == 2
        
        dr001_failures = store.list_failures(request_id="dr-001")
        assert len(dr001_failures) == 1

    def test_list_unresolved_only(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        record = store.record_failure("dr-001", FailureType.SEND_FAILED)
        store.resolve_failure(record["failure_id"], RecoveryAction.RETRY_SEND)
        store.record_failure("dr-002", FailureType.TIMEOUT_NO_REPLY)
        
        unresolved = store.list_failures(unresolved_only=True)
        assert len(unresolved) == 1
        assert unresolved[0]["request_id"] == "dr-002"

    def test_resolve_failure(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        record = store.record_failure("dr-001", FailureType.SEND_FAILED)
        resolved = store.resolve_failure(record["failure_id"], RecoveryAction.RETRY_SEND)
        
        assert resolved["resolved"] == True
        assert resolved["resolution_action"] == "retry_send"
        assert resolved["resolved_at"] is not None


class TestHandleSendFailure:
    def test_first_failure_suggests_retry(self):
        request = {"decision_request_id": "dr-001"}
        
        failure_type, recovery, explanation = handle_send_failure(
            request, "Connection refused", retry_count=0, max_retries=3
        )
        
        assert failure_type == FailureType.SEND_FAILED
        assert recovery == RecoveryAction.RETRY_SEND
        assert "attempt 1/3" in explanation

    def test_retry_exceeded_pause(self):
        request = {"decision_request_id": "dr-001"}
        
        failure_type, recovery, explanation = handle_send_failure(
            request, "Connection refused", retry_count=3, max_retries=3
        )
        
        assert failure_type == FailureType.SEND_RETRY_EXCEEDED
        assert recovery == RecoveryAction.PAUSE_FOR_HUMAN
        assert "3 attempts" in explanation


class TestHandleTimeout:
    def test_timeout_wait_behavior(self):
        request = {"sent_at": (datetime.now() - timedelta(hours=50)).isoformat()}
        
        failure_type, recovery, explanation, details = handle_timeout(
            request, TimeoutBehavior.WAIT
        )
        
        assert failure_type == FailureType.TIMEOUT_NO_REPLY
        assert recovery == RecoveryAction.PAUSE_FOR_HUMAN
        assert "Waiting" in explanation

    def test_timeout_defer_behavior(self):
        request = {"sent_at": (datetime.now() - timedelta(hours=50)).isoformat()}
        
        failure_type, recovery, explanation, details = handle_timeout(
            request, TimeoutBehavior.DEFER
        )
        
        assert failure_type == FailureType.TIMEOUT_NO_REPLY
        assert recovery == RecoveryAction.USE_DEFAULT_PATH
        assert "deferring" in explanation
        assert details["resolution"] == "DEFER"

    def test_timeout_default_option_behavior(self):
        request = {"sent_at": (datetime.now() - timedelta(hours=50)).isoformat()}
        
        failure_type, recovery, explanation, details = handle_timeout(
            request, TimeoutBehavior.DEFAULT_OPTION, default_option="A"
        )
        
        assert recovery == RecoveryAction.USE_DEFAULT_PATH
        assert "default option A" in explanation
        assert details["resolution_value"] == "A"

    def test_timeout_no_default_option(self):
        request = {"sent_at": (datetime.now() - timedelta(hours=50)).isoformat()}
        
        failure_type, recovery, explanation, details = handle_timeout(
            request, TimeoutBehavior.DEFAULT_OPTION, default_option=None
        )
        
        assert recovery == RecoveryAction.MARK_BLOCKED
        assert "no default option" in explanation

    def test_timeout_escalate_behavior(self):
        request = {"sent_at": (datetime.now() - timedelta(hours=50)).isoformat()}
        
        failure_type, recovery, explanation, details = handle_timeout(
            request, TimeoutBehavior.ESCALATE
        )
        
        assert recovery == RecoveryAction.REQUEST_NEW_DECISION
        assert "escalating" in explanation


class TestHandleInvalidReply:
    def test_invalid_syntax(self):
        request = {"options": [{"id": "A"}, {"id": "B"}]}
        
        failure_type, recovery, explanation = handle_invalid_reply(
            request, "INVALID COMMAND", "Invalid syntax"
        )
        
        assert failure_type == FailureType.INVALID_REPLY_SYNTAX
        assert recovery == RecoveryAction.PAUSE_FOR_HUMAN

    def test_invalid_option(self):
        request = {"options": [{"id": "A"}, {"id": "B"}]}
        
        failure_type, recovery, explanation = handle_invalid_reply(
            request, "DECISION X", "Invalid option X"
        )
        
        assert failure_type == FailureType.INVALID_REPLY_OPTION

    def test_expired_request(self):
        request = {"options": [{"id": "A"}]}
        
        failure_type, recovery, explanation = handle_invalid_reply(
            request, "DECISION A", "Request expired"
        )
        
        assert failure_type == FailureType.EXPIRED_REQUEST

    def test_guidance_included(self):
        request = {"options": [{"id": "A"}]}
        
        failure_type, recovery, explanation = handle_invalid_reply(
            request, "BAD", "Invalid", guidance="Use DECISION A"
        )
        
        assert "Guidance: Use DECISION A" in explanation


class TestDetectDuplicateReply:
    def test_resolved_request_is_duplicate(self):
        request = {"status": "resolved", "resolution": "DECISION A"}
        
        is_dup, prev = detect_duplicate_reply(request, "DECISION A")
        
        assert is_dup == True
        assert prev is not None
        assert prev["resolution"] == "DECISION A"

    def test_unresolved_not_duplicate(self):
        request = {"status": "sent"}
        
        is_dup, prev = detect_duplicate_reply(request, "DECISION A")
        
        assert is_dup == False

    def test_previous_replies_match(self):
        request = {"status": "reply_received"}
        previous = [{"reply_raw_text": "DECISION A", "received_at": "2026-04-01"}]
        
        is_dup, prev = detect_duplicate_reply(request, "DECISION A", previous)
        
        assert is_dup == True
        assert prev is not None


class TestCheckPartialState:
    def test_complete_state(self):
        request = {
            "decision_request_id": "dr-001",
            "product_id": "test",
            "feature_id": "001",
            "question": "Test?",
            "options": [{"id": "A"}],
            "status": "sent",
        }
        
        is_partial, missing, explanation = check_partial_state(request)
        
        assert is_partial == False
        assert len(missing) == 0

    def test_partial_state(self):
        request = {
            "decision_request_id": "dr-001",
            "question": "Test?",
        }
        
        is_partial, missing, explanation = check_partial_state(request)
        
        assert is_partial == True
        assert "product_id" in missing
        assert "feature_id" in missing

    def test_custom_expected_fields(self):
        request = {"decision_request_id": "dr-001"}
        
        is_partial, missing, explanation = check_partial_state(
            request, expected_fields=["decision_request_id", "resolution"]
        )
        
        assert is_partial == True
        assert "resolution" in missing


class TestGetRecoveryRecommendation:
    def test_send_failed_low_interruption(self):
        request = {"recommendation": "A"}
        
        action, explanation = get_recovery_recommendation(
            FailureType.SEND_FAILED, request, "low_interruption"
        )
        
        assert action == RecoveryAction.CONTINUE_AUTONOMOUSLY
        assert "Low interruption" in explanation

    def test_send_failed_standard(self):
        request = {}
        
        action, explanation = get_recovery_recommendation(
            FailureType.SEND_FAILED, request, "balanced"
        )
        
        assert action == RecoveryAction.RETRY_SEND

    def test_timeout_conservative(self):
        request = {}
        
        action, explanation = get_recovery_recommendation(
            FailureType.TIMEOUT_NO_REPLY, request, "conservative"
        )
        
        assert action == RecoveryAction.PAUSE_FOR_HUMAN

    def test_timeout_low_interruption_with_recommendation(self):
        request = {"recommendation": "A"}
        
        action, explanation = get_recovery_recommendation(
            FailureType.TIMEOUT_NO_REPLY, request, "low_interruption"
        )
        
        assert action == RecoveryAction.USE_DEFAULT_PATH
        assert "recommendation A" in explanation

    def test_invalid_reply(self):
        request = {}
        
        action, explanation = get_recovery_recommendation(
            FailureType.INVALID_REPLY_SYNTAX, request, "balanced"
        )
        
        assert action == RecoveryAction.PAUSE_FOR_HUMAN

    def test_duplicate_reply(self):
        request = {}
        
        action, explanation = get_recovery_recommendation(
            FailureType.DUPLICATE_REPLY, request, "balanced"
        )
        
        assert action == RecoveryAction.CONTINUE_AUTONOMOUSLY

    def test_expired_request(self):
        request = {}
        
        action, explanation = get_recovery_recommendation(
            FailureType.EXPIRED_REQUEST, request, "low_interruption"
        )
        
        assert action == RecoveryAction.REQUEST_NEW_DECISION


class TestFormatFailureSummary:
    def test_format_includes_failure_type(self):
        summary = format_failure_summary(
            FailureType.SEND_FAILED,
            RecoveryAction.RETRY_SEND,
            "Test explanation",
        )
        
        assert "send_failed" in summary
        assert "retry_send" in summary
        assert "Test explanation" in summary

    def test_format_shows_resolved_status(self):
        summary = format_failure_summary(
            FailureType.SEND_FAILED,
            RecoveryAction.RETRY_SEND,
            "Test",
            resolved=True,
        )
        
        assert "Resolved" in summary

    def test_format_shows_unresolved_status(self):
        summary = format_failure_summary(
            FailureType.SEND_FAILED,
            RecoveryAction.RETRY_SEND,
            "Test",
            resolved=False,
        )
        
        assert "Unresolved" in summary


class TestGetTimeoutPolicy:
    def test_critical_request_escalates(self):
        behavior = get_timeout_policy("balanced", "critical")
        assert behavior == TimeoutBehavior.ESCALATE

    def test_approval_request_escalates(self):
        behavior = get_timeout_policy("balanced", "approval")
        assert behavior == TimeoutBehavior.ESCALATE

    def test_conservative_mode_waits(self):
        behavior = get_timeout_policy("conservative", "technical")
        assert behavior == TimeoutBehavior.WAIT

    def test_low_interruption_routine_default_option(self):
        behavior = get_timeout_policy("low_interruption", "routine")
        assert behavior == TimeoutBehavior.DEFAULT_OPTION

    def test_low_interruption_technical_default_option(self):
        behavior = get_timeout_policy("low_interruption", "technical")
        assert behavior == TimeoutBehavior.DEFAULT_OPTION

    def test_low_interruption_other_defer(self):
        behavior = get_timeout_policy("low_interruption", "other")
        assert behavior == TimeoutBehavior.DEFER

    def test_balanced_mode_mark_unresolved(self):
        behavior = get_timeout_policy("balanced", "technical")
        assert behavior == TimeoutBehavior.MARK_UNRESOLVED


class TestValidateStateConsistency:
    def test_consistent_states(self):
        request = {"decision_request_id": "dr-001", "status": "resolved"}
        runstate = {"decisions_needed": []}
        
        is_consistent, inconsistencies, explanation = validate_state_consistency(
            request, runstate
        )
        
        assert is_consistent == True
        assert len(inconsistencies) == 0

    def test_request_resolved_but_in_decisions_needed(self):
        request = {"decision_request_id": "dr-001", "status": "resolved"}
        runstate = {"decisions_needed": [{"request_id": "dr-001"}]}
        
        is_consistent, inconsistencies, explanation = validate_state_consistency(
            request, runstate
        )
        
        assert is_consistent == False
        assert any("resolved" in i for i in inconsistencies)

    def test_request_pending_not_in_decisions_needed(self):
        request = {"decision_request_id": "dr-001", "status": "sent"}
        runstate = {"decisions_needed": []}
        
        is_consistent, inconsistencies, explanation = validate_state_consistency(
            request, runstate
        )
        
        assert is_consistent == False
        assert any("pending" in i for i in inconsistencies)

    def test_request_id_mismatch(self):
        request = {"decision_request_id": "dr-001", "status": "sent"}
        runstate = {"decision_request_pending": "dr-002"}
        
        is_consistent, inconsistencies, explanation = validate_state_consistency(
            request, runstate
        )
        
        assert is_consistent == False
        assert any("mismatch" in i for i in inconsistencies)


class TestEndToEndFailureHandling:
    def test_full_send_failure_flow(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        request = {"decision_request_id": "dr-001"}
        failure_type, recovery, explanation = handle_send_failure(
            request, "SMTP error", retry_count=0
        )
        
        assert recovery == RecoveryAction.RETRY_SEND
        
        record = store.record_failure("dr-001", failure_type, {"error": "SMTP error"})
        assert record["failure_type"] == "send_failed"
        
        resolved = store.resolve_failure(record["failure_id"], recovery)
        assert resolved["resolved"] == True

    def test_full_timeout_flow(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        request = {"sent_at": (datetime.now() - timedelta(hours=50)).isoformat()}
        failure_type, recovery, explanation, details = handle_timeout(
            request, TimeoutBehavior.DEFER
        )
        
        assert recovery == RecoveryAction.USE_DEFAULT_PATH
        
        record = store.record_failure("dr-001", failure_type, details)
        resolved = store.resolve_failure(record["failure_id"], recovery)
        
        assert resolved["resolved"] == True

    def test_full_invalid_reply_flow(self, temp_dir):
        store = FailureRecordStore(temp_dir)
        
        request = {"options": [{"id": "A"}]}
        failure_type, recovery, explanation = handle_invalid_reply(
            request, "DECISION X", "Invalid option X"
        )
        
        assert failure_type == FailureType.INVALID_REPLY_OPTION
        assert recovery == RecoveryAction.PAUSE_FOR_HUMAN
        
        record = store.record_failure("dr-001", failure_type, {"reply": "DECISION X"})
        
        unresolved = store.list_failures(unresolved_only=True)
        assert len(unresolved) == 1