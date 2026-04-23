"""Tests for External Execution Closeout (Feature 061).

Tests for closeout lifecycle orchestration:
- CloseoutState transitions
- CloseoutTerminalClassification validation
- CloseoutResult serialization
- ExternalExecutionCloseoutOrchestrator lifecycle
"""

import tempfile
from pathlib import Path
import yaml

import pytest

from runtime.external_closeout_state import (
    CloseoutState,
    CloseoutTerminalClassification,
    CloseoutResult,
    DEFAULT_CLOSEOUT_TIMEOUT_SECONDS,
    DEFAULT_POLL_INTERVAL_SECONDS,
    MAX_POLL_ATTEMPTS,
)
from runtime.external_execution_closeout import ExternalExecutionCloseoutOrchestrator


class TestCloseoutState:
    def test_closeout_state_enum_values(self):
        assert CloseoutState.EXTERNAL_EXECUTION_TRIGGERED.value == "external_execution_triggered"
        assert CloseoutState.EXTERNAL_EXECUTION_PENDING.value == "external_execution_pending"
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS.value == "closeout_completed_success"
    
    def test_terminal_states(self):
        terminal_states = CloseoutState.terminal_states()
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS in terminal_states
        assert CloseoutState.CLOSEOUT_COMPLETED_FAILURE in terminal_states
        assert CloseoutState.CLOSEOUT_TIMEOUT in terminal_states
        assert CloseoutState.CLOSEOUT_RECOVERY_REQUIRED in terminal_states
        assert CloseoutState.EXTERNAL_EXECUTION_PENDING not in terminal_states
    
    def test_success_terminal_states(self):
        success_states = CloseoutState.success_terminal_states()
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS in success_states
        assert CloseoutState.CLOSEOUT_COMPLETED_FAILURE not in success_states
    
    def test_is_terminal(self):
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS.is_terminal()
        assert CloseoutState.EXTERNAL_EXECUTION_PENDING.is_terminal() is False
    
    def test_is_success(self):
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS.is_success()
        assert CloseoutState.CLOSEOUT_COMPLETED_FAILURE.is_success() is False


class TestCloseoutTerminalClassification:
    def test_classification_enum_values(self):
        assert CloseoutTerminalClassification.SUCCESS.value == "success"
        assert CloseoutTerminalClassification.FAILURE.value == "failure"
        assert CloseoutTerminalClassification.VERIFICATION_FAILURE.value == "verification_failure"
    
    def test_allows_success_progression(self):
        assert CloseoutTerminalClassification.SUCCESS.allows_success_progression()
        assert CloseoutTerminalClassification.FAILURE.allows_success_progression() is False
        assert CloseoutTerminalClassification.RECOVERY_REQUIRED.allows_success_progression() is False


class TestCloseoutResult:
    def test_closeout_result_creation(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_TRIGGERED,
        )
        assert result.closeout_state == CloseoutState.EXTERNAL_EXECUTION_TRIGGERED
        assert result.execution_result_detected is False
        assert result.verification_required is False
    
    def test_closeout_result_to_dict(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            terminal_classification=CloseoutTerminalClassification.SUCCESS,
            execution_result_detected=True,
            verification_required=True,
            verification_completed=True,
            poll_attempts=5,
            elapsed_seconds=50.0,
        )
        
        data = result.to_dict()
        
        assert data["closeout_state"] == "closeout_completed_success"
        assert data["closeout_terminal_state"] == "success"
        assert data["execution_result_detected"] is True
        assert data["verification_completed"] is True
        assert data["poll_attempts"] == 5
    
    def test_closeout_result_is_complete(self):
        result = CloseoutResult(closeout_state=CloseoutState.EXTERNAL_EXECUTION_PENDING)
        assert result.is_complete() is False
        
        result.closeout_state = CloseoutState.CLOSEOUT_COMPLETED_SUCCESS
        assert result.is_complete()
    
    def test_closeout_result_allows_success_progression(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            terminal_classification=CloseoutTerminalClassification.SUCCESS,
        )
        assert result.allows_success_progression()
        
        result.terminal_classification = CloseoutTerminalClassification.FAILURE
        assert result.allows_success_progression() is False
    
    def test_closeout_result_get_gate_status(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            terminal_classification=CloseoutTerminalClassification.SUCCESS,
        )
        assert result.get_gate_status() == "allowed"
        
        result.terminal_classification = CloseoutTerminalClassification.FAILURE
        assert result.get_gate_status() == "blocked"


class TestDefaultConstants:
    def test_default_timeout(self):
        assert DEFAULT_CLOSEOUT_TIMEOUT_SECONDS == 120
    
    def test_default_poll_interval(self):
        assert DEFAULT_POLL_INTERVAL_SECONDS == 10
    
    def test_max_poll_attempts(self):
        assert MAX_POLL_ATTEMPTS == 12


class TestExternalExecutionCloseoutOrchestrator:
    def test_orchestrator_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            orchestrator = ExternalExecutionCloseoutOrchestrator(project_path)
            
            assert orchestrator.project_path == project_path
            assert orchestrator.timeout_seconds == 120
            assert orchestrator.poll_interval_seconds == 10
    
    def test_orchestrator_custom_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            orchestrator = ExternalExecutionCloseoutOrchestrator(
                project_path,
                timeout_seconds=60,
                poll_interval_seconds=5,
            )
            
            assert orchestrator.timeout_seconds == 60
            assert orchestrator.poll_interval_seconds == 5
    
    def test_orchestrator_closeout_without_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "execution-results").mkdir(parents=True)
            
            orchestrator = ExternalExecutionCloseoutOrchestrator(
                project_path,
                timeout_seconds=5,
                poll_interval_seconds=2,
            )
            
            execution_pack = {
                "verification_type": "backend_only",
            }
            
            result = orchestrator.orchestrate_external_closeout(
                execution_id="exec-test-001",
                execution_pack=execution_pack,
                project_id="test-project",
            )
            
            assert result.closeout_state == CloseoutState.CLOSEOUT_TIMEOUT
            assert result.execution_result_detected is False
    
    def test_orchestrator_closeout_with_backend_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            execution_result_data = {
                "execution_id": "exec-test-002",
                "status": "success",
                "verification_type": "backend_only",
            }
            
            result_file = results_dir / "exec-test-002.md"
            content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result_data, default_flow_style=False)}
```
"""
            result_file.write_text(content)
            
            orchestrator = ExternalExecutionCloseoutOrchestrator(project_path)
            
            execution_pack = {
                "verification_type": "backend_only",
            }
            
            result = orchestrator.orchestrate_external_closeout(
                execution_id="exec-test-002",
                execution_pack=execution_pack,
                project_id="test-project",
            )
            
            assert result.execution_result_detected is True
            assert result.verification_required is False


class TestCloseoutStateTransitions:
    def test_triggered_to_pending_transition(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_TRIGGERED,
        )
        assert result.closeout_state == CloseoutState.EXTERNAL_EXECUTION_TRIGGERED
        
        result.closeout_state = CloseoutState.EXTERNAL_EXECUTION_PENDING
        assert result.closeout_state == CloseoutState.EXTERNAL_EXECUTION_PENDING
    
    def test_pending_to_result_detected_transition(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_PENDING,
        )
        
        result.closeout_state = CloseoutState.EXTERNAL_EXECUTION_RESULT_DETECTED
        result.execution_result_detected = True
        
        assert result.closeout_state == CloseoutState.EXTERNAL_EXECUTION_RESULT_DETECTED
        assert result.execution_result_detected
    
    def test_result_detected_to_verification_required_transition(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_RESULT_DETECTED,
            execution_result_detected=True,
        )
        
        result.closeout_state = CloseoutState.POST_EXTERNAL_VERIFICATION_REQUIRED
        result.verification_required = True
        
        assert result.verification_required
    
    def test_verification_to_success_transition(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.POST_EXTERNAL_VERIFICATION_RUNNING,
            verification_required=True,
        )
        
        result.closeout_state = CloseoutState.CLOSEOUT_COMPLETED_SUCCESS
        result.verification_completed = True
        result.terminal_classification = CloseoutTerminalClassification.SUCCESS
        
        assert result.is_complete()
        assert result.allows_success_progression()


class TestCloseoutRecoveryScenarios:
    def test_recovery_required_state(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_RECOVERY_REQUIRED,
            recovery_required=True,
            recovery_reason="Execution stalled",
        )
        
        assert result.recovery_required
        assert result.recovery_reason == "Execution stalled"
        assert result.is_complete()
        assert result.allows_success_progression() is False
    
    def test_stall_detection(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_STALLED,
            stall_detected=True,
        )
        
        assert result.stall_detected
        assert result.closeout_state == CloseoutState.EXTERNAL_EXECUTION_STALLED


class TestCloseoutTimeoutHandling:
    def test_timeout_state(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_TIMEOUT,
            elapsed_seconds=120.0,
            poll_attempts=12,
        )
        
        assert result.elapsed_seconds == 120.0
        assert result.poll_attempts == 12
        assert result.is_complete()
        assert result.allows_success_progression() is False
    
    def test_timeout_classification(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_TIMEOUT,
            terminal_classification=CloseoutTerminalClassification.CLOSEOUT_TIMEOUT,
        )
        
        assert result.terminal_classification == CloseoutTerminalClassification.CLOSEOUT_TIMEOUT
        assert result.terminal_classification.allows_success_progression() is False