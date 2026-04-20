"""Tests for Feature 061 - External Execution Closeout Orchestration."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import yaml
import time

from runtime.external_closeout_state import (
    CloseoutState,
    CloseoutTerminalClassification,
    CloseoutResult,
    DEFAULT_CLOSEOUT_TIMEOUT_SECONDS,
    DEFAULT_POLL_INTERVAL_SECONDS,
)
from runtime.external_execution_closeout import (
    ExternalExecutionCloseoutOrchestrator,
    orchestrate_external_closeout,
    check_closeout_recovery_needed,
)


class TestCloseoutState:
    def test_all_states_exist(self):
        assert CloseoutState.EXTERNAL_EXECUTION_TRIGGERED.value == "external_execution_triggered"
        assert CloseoutState.EXTERNAL_EXECUTION_PENDING.value == "external_execution_pending"
        assert CloseoutState.EXTERNAL_EXECUTION_RESULT_DETECTED.value == "external_execution_result_detected"
        assert CloseoutState.POST_EXTERNAL_VERIFICATION_REQUIRED.value == "post_external_verification_required"
        assert CloseoutState.POST_EXTERNAL_VERIFICATION_RUNNING.value == "post_external_verification_running"
        assert CloseoutState.POST_EXTERNAL_VERIFICATION_COMPLETED.value == "post_external_verification_completed"
        assert CloseoutState.EXTERNAL_EXECUTION_STALLED.value == "external_execution_stalled"
        assert CloseoutState.CLOSEOUT_TIMEOUT.value == "closeout_timeout"
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS.value == "closeout_completed_success"
        assert CloseoutState.CLOSEOUT_COMPLETED_FAILURE.value == "closeout_completed_failure"
        assert CloseoutState.CLOSEOUT_RECOVERY_REQUIRED.value == "closeout_recovery_required"

    def test_state_from_string(self):
        state = CloseoutState("closeout_completed_success")
        assert state == CloseoutState.CLOSEOUT_COMPLETED_SUCCESS

    def test_terminal_states_method(self):
        terminal = CloseoutState.terminal_states()
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS in terminal
        assert CloseoutState.CLOSEOUT_COMPLETED_FAILURE in terminal
        assert CloseoutState.CLOSEOUT_TIMEOUT in terminal
        assert CloseoutState.CLOSEOUT_RECOVERY_REQUIRED in terminal
        assert CloseoutState.EXTERNAL_EXECUTION_PENDING not in terminal

    def test_is_terminal(self):
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS.is_terminal() is True
        assert CloseoutState.CLOSEOUT_TIMEOUT.is_terminal() is True
        assert CloseoutState.EXTERNAL_EXECUTION_PENDING.is_terminal() is False
        assert CloseoutState.POST_EXTERNAL_VERIFICATION_REQUIRED.is_terminal() is False

    def test_is_success(self):
        assert CloseoutState.CLOSEOUT_COMPLETED_SUCCESS.is_success() is True
        assert CloseoutState.CLOSEOUT_COMPLETED_FAILURE.is_success() is False
        assert CloseoutState.CLOSEOUT_TIMEOUT.is_success() is False


class TestCloseoutTerminalClassification:
    def test_all_classifications_exist(self):
        assert CloseoutTerminalClassification.SUCCESS.value == "success"
        assert CloseoutTerminalClassification.FAILURE.value == "failure"
        assert CloseoutTerminalClassification.VERIFICATION_FAILURE.value == "verification_failure"
        assert CloseoutTerminalClassification.CLOSEOUT_TIMEOUT.value == "closeout_timeout"
        assert CloseoutTerminalClassification.STALLED.value == "stalled"
        assert CloseoutTerminalClassification.RECOVERY_REQUIRED.value == "recovery_required"

    def test_allows_success_progression(self):
        assert CloseoutTerminalClassification.SUCCESS.allows_success_progression() is True
        assert CloseoutTerminalClassification.FAILURE.allows_success_progression() is False
        assert CloseoutTerminalClassification.VERIFICATION_FAILURE.allows_success_progression() is False
        assert CloseoutTerminalClassification.CLOSEOUT_TIMEOUT.allows_success_progression() is False


class TestCloseoutResult:
    def test_result_creation(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_TRIGGERED,
            timeout_seconds=120,
        )
        assert result.closeout_state == CloseoutState.EXTERNAL_EXECUTION_TRIGGERED
        assert result.timeout_seconds == 120
        assert result.execution_result_detected is False

    def test_result_to_dict(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            terminal_classification=CloseoutTerminalClassification.SUCCESS,
            execution_result_detected=True,
            execution_result_valid=True,
            verification_required=True,
            verification_completed=True,
            verification_terminal_state="success",
            poll_attempts=3,
            elapsed_seconds=45.2,
            timeout_seconds=120,
            started_at="2026-04-20T10:00:00",
            finished_at="2026-04-20T10:00:45",
        )
        dict_result = result.to_dict()
        
        assert dict_result["closeout_state"] == "closeout_completed_success"
        assert dict_result["closeout_terminal_state"] == "success"
        assert dict_result["execution_result_detected"] is True
        assert dict_result["poll_attempts"] == 3
        assert dict_result["elapsed_seconds"] == 45.2

    def test_is_complete(self):
        result = CloseoutResult(closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS)
        assert result.is_complete() is True
        
        result = CloseoutResult(closeout_state=CloseoutState.EXTERNAL_EXECUTION_PENDING)
        assert result.is_complete() is False

    def test_allows_success_progression(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            terminal_classification=CloseoutTerminalClassification.SUCCESS,
        )
        assert result.allows_success_progression() is True
        
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_FAILURE,
            terminal_classification=CloseoutTerminalClassification.FAILURE,
        )
        assert result.allows_success_progression() is False
        
        result = CloseoutResult(closeout_state=CloseoutState.EXTERNAL_EXECUTION_PENDING)
        assert result.allows_success_progression() is False

    def test_get_gate_status(self):
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            terminal_classification=CloseoutTerminalClassification.SUCCESS,
        )
        assert result.get_gate_status() == "allowed"
        
        result = CloseoutResult(
            closeout_state=CloseoutState.CLOSEOUT_TIMEOUT,
            terminal_classification=CloseoutTerminalClassification.CLOSEOUT_TIMEOUT,
        )
        assert result.get_gate_status() == "blocked"


class TestExternalExecutionCloseoutOrchestrator:
    def test_orchestrator_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            orchestrator = ExternalExecutionCloseoutOrchestrator(
                project_path=project_path,
                timeout_seconds=60,
                poll_interval_seconds=5,
            )
            assert orchestrator.project_path == project_path
            assert orchestrator.timeout_seconds == 60
            assert orchestrator.poll_interval_seconds == 5

    def test_orchestrate_timeout_scenario(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            orchestrator = ExternalExecutionCloseoutOrchestrator(
                project_path=project_path,
                timeout_seconds=1,
                poll_interval_seconds=1,
            )
            
            execution_pack = {
                "execution_id": "exec-test-001",
                "verification_type": "backend_only",
            }
            
            result = orchestrator.orchestrate_external_closeout(
                execution_id="exec-test-001",
                execution_pack=execution_pack,
                project_id="test-project",
            )
            
            assert result.closeout_state == CloseoutState.CLOSEOUT_TIMEOUT
            assert result.terminal_classification == CloseoutTerminalClassification.CLOSEOUT_TIMEOUT
            assert result.stall_detected is True
            assert result.recovery_required is True

    def test_orchestrate_success_backend_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            execution_result_content = """# ExecutionResult: exec-test-002

```yaml
execution_id: exec-test-002
status: success
completed_items:
  - "item-1"
artifacts_created:
  - name: "test"
    path: "test.md"
    type: file
verification_result:
  passed: 1
  failed: 0
issues_found: []
blocked_reasons: []
decisions_required: []
recommended_next_step: "Done"
```
"""
            result_path = results_dir / "exec-test-002.md"
            result_path.write_text(execution_result_content)
            
            orchestrator = ExternalExecutionCloseoutOrchestrator(
                project_path=project_path,
                timeout_seconds=5,
                poll_interval_seconds=1,
            )
            
            execution_pack = {
                "execution_id": "exec-test-002",
                "verification_type": "backend_only",
            }
            
            result = orchestrator.orchestrate_external_closeout(
                execution_id="exec-test-002",
                execution_pack=execution_pack,
                project_id="test-project",
            )
            
            assert result.closeout_state == CloseoutState.CLOSEOUT_COMPLETED_SUCCESS
            assert result.terminal_classification == CloseoutTerminalClassification.SUCCESS
            assert result.execution_result_detected is True
            assert result.execution_result_valid is True

    def test_check_closeout_recovery_needed_no_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            recovery_check = check_closeout_recovery_needed(
                project_path=project_path,
                execution_id="exec-no-result",
            )
            
            assert recovery_check["recovery_needed"] is True
            assert recovery_check["reason"] == "execution_result_not_found"

    def test_check_closeout_recovery_needed_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            execution_result_content = """# ExecutionResult: exec-success

```yaml
execution_id: exec-success
status: success
closeout_state: closeout_completed_success
closeout_terminal_state: success
completed_items:
  - "item-1"
artifacts_created: []
verification_result:
  passed: 1
  failed: 0
issues_found: []
blocked_reasons: []
decisions_required: []
recommended_next_step: "Done"
```
"""
            result_path = results_dir / "exec-success.md"
            result_path.write_text(execution_result_content)
            
            recovery_check = check_closeout_recovery_needed(
                project_path=project_path,
                execution_id="exec-success",
            )
            
            assert recovery_check["recovery_needed"] is False
            assert recovery_check["reason"] == "closeout_complete"

    def test_check_closeout_recovery_needed_interrupted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            execution_result_content = """# ExecutionResult: exec-interrupted

```yaml
execution_id: exec-interrupted
status: partial
closeout_state: external_execution_pending
completed_items:
  - "item-1"
artifacts_created: []
verification_result:
  passed: 1
  failed: 0
issues_found: []
blocked_reasons: []
decisions_required: []
recommended_next_step: "Resume"
```
"""
            result_path = results_dir / "exec-interrupted.md"
            result_path.write_text(execution_result_content)
            
            recovery_check = check_closeout_recovery_needed(
                project_path=project_path,
                execution_id="exec-interrupted",
            )
            
            assert recovery_check["recovery_needed"] is True
            assert "closeout_interrupted" in recovery_check["reason"]


class TestConvenienceFunctions:
    def test_orchestrate_external_closeout_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            execution_result_content = """# ExecutionResult: exec-conv-test

```yaml
execution_id: exec-conv-test
status: success
completed_items:
  - "item-1"
artifacts_created:
  - name: "test"
    path: "test.md"
    type: file
verification_result:
  passed: 1
  failed: 0
issues_found: []
blocked_reasons: []
decisions_required: []
recommended_next_step: "Done"
```
"""
            result_path = results_dir / "exec-conv-test.md"
            result_path.write_text(execution_result_content)
            
            assert result_path.exists()
            
            result = orchestrate_external_closeout(
                project_path=project_path,
                execution_id="exec-conv-test",
                execution_pack={"execution_id": "exec-conv-test", "verification_type": "backend_only"},
                project_id="test-project",
                timeout_seconds=30,
                poll_interval_seconds=1,
            )
            
            assert result.closeout_state == CloseoutState.CLOSEOUT_COMPLETED_SUCCESS
            assert result.execution_result_detected is True


class TestMissingVerificationDetection:
    @patch("runtime.external_execution_closeout.orchestrate_post_external")
    def test_verification_required_and_missing(self, mock_orchestrate):
        mock_result = Mock()
        mock_result.terminal_state.value = "success"
        mock_result.verification_completed = True
        mock_result.to_dict.return_value = {
            "browser_verification": {"executed": True, "passed": 1, "failed": 0}
        }
        mock_orchestrate.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            execution_result_content = """# ExecutionResult: exec-frontend

```yaml
execution_id: exec-frontend
status: success
completed_items:
  - "item-1"
artifacts_created: []
verification_result:
  passed: 1
  failed: 0
issues_found: []
blocked_reasons: []
decisions_required: []
recommended_next_step: "Done"
```
"""
            result_path = results_dir / "exec-frontend.md"
            result_path.write_text(execution_result_content)
            
            orchestrator = ExternalExecutionCloseoutOrchestrator(
                project_path=project_path,
                timeout_seconds=5,
                poll_interval_seconds=1,
            )
            
            execution_pack = {
                "execution_id": "exec-frontend",
                "verification_type": "frontend_interactive",
            }
            
            result = orchestrator.orchestrate_external_closeout(
                execution_id="exec-frontend",
                execution_pack=execution_pack,
                project_id="test-project",
            )
            
            assert result.verification_required is True
            mock_orchestrate.assert_called_once()