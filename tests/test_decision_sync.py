"""Tests for decision_sync module (Feature 043)."""

import tempfile
from pathlib import Path

import pytest

from runtime.decision_sync import (
    sync_decision_to_runstate,
    sync_reply_to_runstate,
    reconcile_decision_sources,
    get_pending_decision_count,
    get_decision_status_summary,
)
from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
    DecisionType,
    DeliveryChannel,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestSyncDecisionToRunstate:
    def test_sync_adds_decision_to_runstate(self, temp_dir):
        request = {
            "decision_request_id": "dr-20260416-001",
            "question": "Use YAML or JSON?",
            "options": [{"id": "A", "label": "YAML"}, {"id": "B", "label": "JSON"}],
            "recommendation": "A",
            "decision_type": "technical",
            "pause_reason_category": "decision_required",
            "sent_at": "2026-04-16T10:00:00",
        }
        runstate = {"decisions_needed": [], "current_phase": "executing"}
        
        result = sync_decision_to_runstate(request, runstate)
        
        assert len(result["decisions_needed"]) == 1
        assert result["decisions_needed"][0]["request_id"] == "dr-20260416-001"
        assert result["decision_request_pending"] == "dr-20260416-001"
        assert result["current_phase"] == "blocked"

    def test_sync_sets_blocked_phase_for_blocker_category(self, temp_dir):
        request = {
            "decision_request_id": "dr-001",
            "question": "Blocked by API?",
            "options": [{"id": "A", "label": "Wait"}],
            "recommendation": "A",
            "pause_reason_category": "blocker",
            "sent_at": "2026-04-16T10:00:00",
        }
        runstate = {"decisions_needed": [], "current_phase": "executing"}
        
        result = sync_decision_to_runstate(request, runstate)
        
        assert result["current_phase"] == "blocked"

    def test_sync_does_not_duplicate_existing_decision(self, temp_dir):
        request = {
            "decision_request_id": "dr-001",
            "question": "Test question?",
            "options": [{"id": "A", "label": "Option A"}],
            "recommendation": "A",
            "pause_reason_category": "decision_required",
            "sent_at": "2026-04-16T10:00:00",
        }
        runstate = {
            "decisions_needed": [{"request_id": "dr-001", "decision": "Existing"}],
            "current_phase": "blocked",
        }
        
        result = sync_decision_to_runstate(request, runstate)
        
        assert len(result["decisions_needed"]) == 1


class TestSyncReplyToRunstate:
    def test_sync_removes_decision_from_runstate(self, temp_dir):
        runstate = {
            "decisions_needed": [{"request_id": "dr-001", "decision": "Test"}],
            "current_phase": "blocked",
        }
        reply = {
            "reply_value": "DECISION A",
            "parsed_result": {"command": "DECISION", "argument": "A"},
            "received_at": "2026-04-16T14:00:00",
        }
        action = {
            "runstate_action": "select_option",
            "continuation_phase": "planning",
            "next_recommended": "Proceed",
        }
        
        result = sync_reply_to_runstate("dr-001", reply, runstate, action)
        
        assert len(result["decisions_needed"]) == 0
        assert result["decision_request_pending"] is None
        assert result["last_decision_resolution"]["request_id"] == "dr-001"
        assert result["current_phase"] == "planning"

    def test_sync_sets_phase_from_action(self, temp_dir):
        runstate = {"decisions_needed": [], "current_phase": "blocked"}
        reply = {"reply_value": "CONTINUE", "parsed_result": {"command": "CONTINUE"}}
        action = {"continuation_phase": "executing", "next_recommended": "Go"}
        
        result = sync_reply_to_runstate("dr-001", reply, runstate, action)
        
        assert result["current_phase"] == "executing"

    def test_sync_without_action_uses_default_phase(self, temp_dir):
        runstate = {"decisions_needed": [], "current_phase": "blocked"}
        reply = {"reply_value": "DECISION A", "parsed_result": {"command": "DECISION"}}
        
        result = sync_reply_to_runstate("dr-001", reply, runstate)
        
        assert result["current_phase"] == "planning"


class TestReconcileDecisionSources:
    def test_reconcile_with_no_decisions(self, temp_dir):
        result = reconcile_decision_sources(temp_dir)
        
        assert result["pending_count"] == 0
        assert result["resolved_count"] == 0
        assert result["has_discrepancies"] == False

    def test_reconcile_with_pending_email_request(self, temp_dir):
        store = DecisionRequestStore(temp_dir)
        request = store.create_request(
            product_id="test",
            feature_id="001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Test question?",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
            delivery_channel=DeliveryChannel.MOCK_FILE,
        )
        store.mark_sent(request["decision_request_id"])
        
        result = reconcile_decision_sources(temp_dir)
        
        assert result["pending_count"] == 1
        assert len(result["pending_email_decisions"]) == 1


class TestGetPendingDecisionCount:
    def test_count_with_no_decisions(self, temp_dir):
        count = get_pending_decision_count(temp_dir)
        assert count == 0

    def test_count_with_pending_request(self, temp_dir):
        store = DecisionRequestStore(temp_dir)
        request = store.create_request(
            product_id="test",
            feature_id="001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Test?",
            options=[{"id": "A", "label": "A"}],
            recommendation="A",
            delivery_channel=DeliveryChannel.MOCK_FILE,
        )
        store.mark_sent(request["decision_request_id"])
        
        count = get_pending_decision_count(temp_dir)
        assert count == 1


class TestGetDecisionStatusSummary:
    def test_summary_with_no_decisions(self, temp_dir):
        summary = get_decision_status_summary(temp_dir)
        
        assert summary["total_pending"] == 0
        assert summary["total_resolved"] == 0
        assert summary["has_discrepancies"] == False