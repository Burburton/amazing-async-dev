"""Tests for Feature 054 - Auto Email Decision Trigger."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from runtime.auto_email_trigger import (
    TriggerSource,
    TriggerResult,
    should_auto_trigger,
    create_auto_decision_request,
    auto_trigger_decision_email,
    check_and_trigger,
)
from runtime.execution_policy import PolicyMode


class TestShouldAutoTrigger:
    def test_no_decisions_needed(self):
        runstate = {"decisions_needed": [], "policy_mode": "conservative"}
        should, reason = should_auto_trigger(runstate)
        assert should is False
        assert "No decisions_needed" in reason
    
    def test_already_pending_request(self):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "decision_request_pending": "dr-001",
            "policy_mode": "conservative",
        }
        should, reason = should_auto_trigger(runstate)
        assert should is False
        assert "already pending" in reason
    
    def test_conservative_mode_always_triggers(self):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "conservative",
        }
        should, reason = should_auto_trigger(runstate)
        assert should is True
        assert reason is None
    
    def test_low_interruption_mode_triggers(self):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "low_interruption",
        }
        should, reason = should_auto_trigger(runstate)
        assert should is True
        assert reason is None
    
    def test_balanced_mode_triggers_for_blocker(self):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "balanced",
        }
        should, reason = should_auto_trigger(runstate, pause_category="blocker")
        assert should is True
    
    def test_balanced_mode_skips_technical(self):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "balanced",
        }
        should, reason = should_auto_trigger(runstate, pause_category="technical")
        assert should is False
        assert "Balanced mode skips" in reason
    
    def test_balanced_mode_triggers_without_category(self):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "balanced",
        }
        should, reason = should_auto_trigger(runstate)
        assert should is True


class TestTriggerResult:
    def test_triggered_result(self):
        result = TriggerResult(
            triggered=True,
            request_id="dr-001",
            trigger_source=TriggerSource.RUN_DAY_AUTO,
            policy_mode_at_trigger=PolicyMode.CONSERVATIVE,
        )
        assert result.triggered is True
        assert result.request_id == "dr-001"
        assert result.trigger_source == TriggerSource.RUN_DAY_AUTO
    
    def test_skipped_result(self):
        result = TriggerResult(
            triggered=False,
            skipped_reason="No decisions needed",
        )
        assert result.triggered is False
        assert result.skipped_reason == "No decisions needed"
    
    def test_error_result(self):
        result = TriggerResult(
            triggered=False,
            error_message="Failed to send",
        )
        assert result.triggered is False
        assert result.error_message == "Failed to send"


class TestTriggerSource:
    def test_trigger_sources(self):
        assert TriggerSource.RUN_DAY_AUTO.value == "run_day_auto"
        assert TriggerSource.PLAN_DAY_AUTO.value == "plan_day_auto"
        assert TriggerSource.MANUAL_CLI.value == "manual_cli"


class TestAutoTriggerDecisionEmail:
    def test_no_decisions_needed(self, tmp_path):
        runstate = {"decisions_needed": [], "policy_mode": "conservative"}
        result = auto_trigger_decision_email(tmp_path, runstate)
        assert result.triggered is False
        assert "No decisions_needed" in result.skipped_reason
    
    def test_already_pending(self, tmp_path):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "decision_request_pending": "dr-001",
            "policy_mode": "conservative",
        }
        result = auto_trigger_decision_email(tmp_path, runstate)
        assert result.triggered is False
        assert "already pending" in result.skipped_reason
    
    def test_balanced_skips_technical(self, tmp_path):
        runstate = {
            "decisions_needed": [{"decision": "test", "pause_reason_category": "technical"}],
            "policy_mode": "balanced",
        }
        result = auto_trigger_decision_email(tmp_path, runstate)
        assert result.triggered is False
    
    def test_conservative_triggers(self, tmp_path):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "conservative",
        }
        
        with patch('runtime.auto_email_trigger.create_auto_decision_request') as mock_create:
            with patch('runtime.auto_email_trigger.send_auto_decision_email') as mock_send:
                with patch('runtime.auto_email_trigger.sync_decision_to_runstate') as mock_sync:
                    mock_create.return_value = {"decision_request_id": "dr-001"}
                    mock_send.return_value = (True, "msg-001")
                    mock_sync.return_value = runstate
                    
                    result = auto_trigger_decision_email(tmp_path, runstate)
                    
                    assert result.triggered is True
                    assert result.request_id == "dr-001"


class TestCheckAndTrigger:
    def test_no_runstate(self, tmp_path):
        with patch('runtime.auto_email_trigger.StateStore') as mock_store:
            mock_instance = MagicMock()
            mock_store.return_value = mock_instance
            mock_instance.load_runstate.return_value = None
            
            result = check_and_trigger(tmp_path)
            assert result.triggered is False
            assert "No RunState" in result.skipped_reason
    
    def test_with_decisions_needed(self, tmp_path):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "conservative",
        }
        
        with patch('runtime.auto_email_trigger.StateStore') as mock_store:
            with patch('runtime.auto_email_trigger.auto_trigger_decision_email') as mock_trigger:
                mock_instance = MagicMock()
                mock_store.return_value = mock_instance
                mock_instance.load_runstate.return_value = runstate
                mock_trigger.return_value = TriggerResult(triggered=True, request_id="dr-001")
                
                result = check_and_trigger(tmp_path)
                
                assert result.triggered is True


class TestIntegrationWithPolicyMode:
    def test_policy_mode_preserved_in_result(self, tmp_path):
        runstate = {
            "decisions_needed": [{"decision": "test"}],
            "policy_mode": "balanced",
        }
        
        with patch('runtime.auto_email_trigger.create_auto_decision_request') as mock_create:
            with patch('runtime.auto_email_trigger.send_auto_decision_email') as mock_send:
                with patch('runtime.auto_email_trigger.sync_decision_to_runstate') as mock_sync:
                    mock_create.return_value = {"decision_request_id": "dr-001"}
                    mock_send.return_value = (True, "msg-001")
                    mock_sync.return_value = runstate
                    
                    result = auto_trigger_decision_email(tmp_path, runstate)
                    
                    assert result.policy_mode_at_trigger == PolicyMode.BALANCED