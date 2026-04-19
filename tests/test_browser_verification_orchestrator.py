"""Tests for Feature 060 - System-Owned Frontend Verification Orchestration."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from runtime.browser_verification_orchestrator import (
    OrchestrationTerminalState,
    OrchestrationResult,
    BrowserVerificationOrchestrator,
    orchestrate_for_run_day,
    orchestrate_post_external,
    can_mark_execution_success_with_orchestration,
)
from runtime.browser_verifier import (
    BrowserVerificationStatus,
    BrowserVerificationResult,
    ExceptionReason,
)
from runtime.verification_classifier import VerificationType


class TestOrchestrationTerminalState:
    def test_all_states_exist(self):
        assert OrchestrationTerminalState.NOT_REQUIRED.value == "not_required"
        assert OrchestrationTerminalState.REQUIRED_NOT_STARTED.value == "required_not_started"
        assert OrchestrationTerminalState.IN_PROGRESS.value == "in_progress"
        assert OrchestrationTerminalState.SUCCESS.value == "success"
        assert OrchestrationTerminalState.FAILURE.value == "failure"
        assert OrchestrationTerminalState.TIMEOUT.value == "timeout"
        assert OrchestrationTerminalState.EXCEPTION_ACCEPTED.value == "exception_accepted"
        assert OrchestrationTerminalState.SKIPPED_BY_POLICY.value == "skipped_by_policy"

    def test_state_from_string(self):
        state = OrchestrationTerminalState("success")
        assert state == OrchestrationTerminalState.SUCCESS


class TestOrchestrationResult:
    def test_result_creation(self):
        result = OrchestrationResult(
            terminal_state=OrchestrationTerminalState.NOT_REQUIRED,
            verification_required=False,
            verification_started=False,
            verification_completed=False,
            dev_server_started=False,
        )
        assert result.terminal_state == OrchestrationTerminalState.NOT_REQUIRED
        assert result.verification_required is False

    def test_result_to_dict(self):
        result = OrchestrationResult(
            terminal_state=OrchestrationTerminalState.SUCCESS,
            verification_required=True,
            verification_started=True,
            verification_completed=True,
            dev_server_started=True,
            dev_server_url="http://localhost:3000",
            elapsed_seconds=30.0,
            session_id="vs-001",
        )
        dict_result = result.to_dict()
        
        assert dict_result["orchestration_terminal_state"] == "success"
        assert dict_result["verification_required"] is True
        assert dict_result["dev_server_url"] == "http://localhost:3000"
        assert "browser_verification" in dict_result

    def test_is_valid_terminal_state(self):
        valid_states = [
            OrchestrationTerminalState.NOT_REQUIRED,
            OrchestrationTerminalState.SUCCESS,
            OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            OrchestrationTerminalState.SKIPPED_BY_POLICY,
        ]
        
        for state in valid_states:
            result = OrchestrationResult(
                terminal_state=state,
                verification_required=False,
                verification_started=False,
                verification_completed=False,
                dev_server_started=False,
            )
            assert result.is_valid_terminal_state() is True
        
        invalid_states = [
            OrchestrationTerminalState.REQUIRED_NOT_STARTED,
            OrchestrationTerminalState.IN_PROGRESS,
            OrchestrationTerminalState.FAILURE,
            OrchestrationTerminalState.TIMEOUT,
        ]
        
        for state in invalid_states:
            result = OrchestrationResult(
                terminal_state=state,
                verification_required=True,
                verification_started=True,
                verification_completed=False,
                dev_server_started=False,
            )
            assert result.is_valid_terminal_state() is False

    def test_get_gate_status(self):
        result = OrchestrationResult(
            terminal_state=OrchestrationTerminalState.SUCCESS,
            verification_required=True,
            verification_started=True,
            verification_completed=True,
            dev_server_started=True,
        )
        assert result.get_gate_status() == "allowed"
        
        result = OrchestrationResult(
            terminal_state=OrchestrationTerminalState.FAILURE,
            verification_required=True,
            verification_started=True,
            verification_completed=True,
            dev_server_started=True,
        )
        assert result.get_gate_status() == "blocked"


class TestBrowserVerificationOrchestrator:
    def test_determine_verification_required_backend_only(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        execution_pack = {"verification_type": "backend_only"}
        required, vt = orchestrator.determine_verification_required(execution_pack=execution_pack)
        
        assert required is False
        assert vt == VerificationType.BACKEND_ONLY

    def test_determine_verification_required_frontend_interactive(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        execution_pack = {"verification_type": "frontend_interactive"}
        required, vt = orchestrator.determine_verification_required(execution_pack=execution_pack)
        
        assert required is True
        assert vt == VerificationType.FRONTEND_INTERACTIVE

    def test_determine_verification_required_from_files(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        changed_files = ["src/components/Button.tsx"]
        required, vt = orchestrator.determine_verification_required(changed_files=changed_files)
        
        assert required is True
        assert vt == VerificationType.FRONTEND_INTERACTIVE

    def test_determine_verification_required_default(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        required, vt = orchestrator.determine_verification_required()
        
        assert required is False
        assert vt == VerificationType.BACKEND_ONLY

    def test_get_success_gate_status_backend_only(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        execution_result = {"status": "success"}
        verification_type = "backend_only"
        
        can_mark, reason = orchestrator.get_success_gate_status(execution_result, verification_type)
        
        assert can_mark is True
        assert "not required" in reason

    def test_get_success_gate_status_frontend_with_success_state(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        execution_result = {
            "status": "success",
            "orchestration_terminal_state": "success",
            "browser_verification": {"executed": True, "passed": 3, "failed": 0},
        }
        verification_type = "frontend_interactive"
        
        can_mark, reason = orchestrator.get_success_gate_status(execution_result, verification_type)
        
        assert can_mark is True
        assert "Valid terminal state" in reason

    def test_get_success_gate_status_frontend_blocked(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        
        execution_result = {
            "status": "success",
            "orchestration_terminal_state": "failure",
        }
        verification_type = "frontend_interactive"
        
        can_mark, reason = orchestrator.get_success_gate_status(execution_result, verification_type)
        
        assert can_mark is False
        assert "not completed" in reason

    def test_cleanup(self, tmp_path):
        orchestrator = BrowserVerificationOrchestrator(tmp_path)
        orchestrator.dev_server_manager = Mock()
        orchestrator.session_manager = Mock()
        orchestrator.session_manager.active_session = Mock()
        
        orchestrator.cleanup()
        
        orchestrator.dev_server_manager.stop.assert_called_once()
        orchestrator.session_manager.clear_session.assert_called_once()


class TestOrchestrateForRunDay:
    def test_backend_only_returns_not_required(self, tmp_path):
        execution_pack = {"verification_type": "backend_only", "execution_id": "exec-001"}
        
        with patch.object(BrowserVerificationOrchestrator, 'determine_verification_required', return_value=(False, VerificationType.BACKEND_ONLY)):
            result = orchestrate_for_run_day(
                project_path=tmp_path,
                execution_pack=execution_pack,
                project_id="test-project",
            )
        
        assert result.terminal_state == OrchestrationTerminalState.NOT_REQUIRED


class TestOrchestratePostExternal:
    def test_already_verified_returns_result(self, tmp_path):
        execution_pack = {"verification_type": "frontend_interactive"}
        execution_result = {
            "browser_verification": {
                "executed": True,
                "passed": 3,
                "failed": 0,
            }
        }
        
        result = orchestrate_post_external(
            project_path=tmp_path,
            project_id="test-project",
            execution_pack=execution_pack,
            execution_result=execution_result,
        )
        
        assert result.verification_completed is True

    def test_exception_accepted_returns_result(self, tmp_path):
        execution_pack = {"verification_type": "frontend_interactive"}
        execution_result = {
            "browser_verification": {
                "executed": False,
                "exception_reason": "playwright_unavailable",
                "exception_details": "No Playwright",
            }
        }
        
        result = orchestrate_post_external(
            project_path=tmp_path,
            project_id="test-project",
            execution_pack=execution_pack,
            execution_result=execution_result,
        )
        
        assert result.terminal_state == OrchestrationTerminalState.EXCEPTION_ACCEPTED


class TestCanMarkExecutionSuccessWithOrchestration:
    def test_backend_only_allowed(self, tmp_path):
        execution_result = {"status": "success"}
        
        can_mark, reason = can_mark_execution_success_with_orchestration(
            project_path=tmp_path,
            execution_result=execution_result,
            verification_type="backend_only",
        )
        
        assert can_mark is True

    def test_frontend_with_valid_terminal_state_allowed(self, tmp_path):
        execution_result = {
            "status": "success",
            "orchestration_terminal_state": "success",
            "browser_verification": {"executed": True},
        }
        
        can_mark, reason = can_mark_execution_success_with_orchestration(
            project_path=tmp_path,
            execution_result=execution_result,
            verification_type="frontend_interactive",
        )
        
        assert can_mark is True


class TestTerminalStateValidity:
    def test_timeout_not_valid_for_success(self):
        result = OrchestrationResult(
            terminal_state=OrchestrationTerminalState.TIMEOUT,
            verification_required=True,
            verification_started=True,
            verification_completed=False,
            dev_server_started=True,
        )
        
        assert result.is_valid_terminal_state() is False
        assert result.get_gate_status() == "blocked"

    def test_exception_accepted_valid_for_success(self):
        result = OrchestrationResult(
            terminal_state=OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            verification_required=True,
            verification_started=True,
            verification_completed=False,
            dev_server_started=False,
            exception_reason=ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
            exception_details="No Playwright",
        )
        
        assert result.is_valid_terminal_state() is True
        assert result.get_gate_status() == "allowed"