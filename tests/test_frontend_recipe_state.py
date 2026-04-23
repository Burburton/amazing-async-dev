"""Tests for Frontend Recipe State Model - Feature 062.

Tests for:
- FrontendRecipeStage transitions
- FrontendRecipeFailureReason validation
- ServerStartupInfo / ReadinessProbeInfo dataclasses
- FrontendRecipeResult serialization and gate status
"""

import pytest

from runtime.frontend_recipe_state import (
    FrontendRecipeStage,
    FrontendRecipeFailureReason,
    ServerStartupInfo,
    ReadinessProbeInfo,
    FrontendRecipeResult,
    DEFAULT_SERVER_START_TIMEOUT_SECONDS,
    DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS,
    DEFAULT_BROWSER_VERIFICATION_TIMEOUT_SECONDS,
)


class TestFrontendRecipeStage:
    def test_stage_enum_values(self):
        assert FrontendRecipeStage.INITIALIZING.value == "initializing"
        assert FrontendRecipeStage.SERVER_STARTING.value == "server_starting"
        assert FrontendRecipeStage.READINESS_PROBING.value == "readiness_probing"
        assert FrontendRecipeStage.BROWSER_VERIFICATION.value == "browser_verification"
        assert FrontendRecipeStage.RESULT_PERSISTING.value == "result_persisting"
        assert FrontendRecipeStage.COMPLETED_SUCCESS.value == "completed_success"
        assert FrontendRecipeStage.COMPLETED_FAILURE.value == "completed_failure"
    
    def test_terminal_stages(self):
        terminal = FrontendRecipeStage.terminal_stages()
        assert FrontendRecipeStage.COMPLETED_SUCCESS in terminal
        assert FrontendRecipeStage.COMPLETED_FAILURE in terminal
        assert FrontendRecipeStage.COMPLETED_TIMEOUT in terminal
        assert FrontendRecipeStage.SERVER_STARTING not in terminal
    
    def test_success_terminal(self):
        success = FrontendRecipeStage.success_terminal()
        assert FrontendRecipeStage.COMPLETED_SUCCESS in success
        assert FrontendRecipeStage.COMPLETED_FAILURE not in success
    
    def test_is_terminal(self):
        assert FrontendRecipeStage.COMPLETED_SUCCESS.is_terminal()
        assert FrontendRecipeStage.COMPLETED_FAILURE.is_terminal()
        assert FrontendRecipeStage.SERVER_STARTING.is_terminal() is False
    
    def test_is_success(self):
        assert FrontendRecipeStage.COMPLETED_SUCCESS.is_success()
        assert FrontendRecipeStage.COMPLETED_FAILURE.is_success() is False
    
    def test_stage_from_string(self):
        stage = FrontendRecipeStage("server_starting")
        assert stage == FrontendRecipeStage.SERVER_STARTING


class TestFrontendRecipeFailureReason:
    def test_failure_reason_enum_values(self):
        assert FrontendRecipeFailureReason.FRAMEWORK_UNKNOWN.value == "framework_unknown"
        assert FrontendRecipeFailureReason.SERVER_START_FAILED.value == "server_start_failed"
        assert FrontendRecipeFailureReason.SERVER_TIMEOUT.value == "server_timeout"
        assert FrontendRecipeFailureReason.PORT_DISCOVERY_FAILED.value == "port_discovery_failed"
        assert FrontendRecipeFailureReason.READINESS_TIMEOUT.value == "readiness_timeout"
        assert FrontendRecipeFailureReason.BROWSER_VERIFICATION_FAILED.value == "browser_verification_failed"
        assert FrontendRecipeFailureReason.RESULT_PERSISTENCE_FAILED.value == "result_persistence_failed"
        assert FrontendRecipeFailureReason.UNEXPECTED_ERROR.value == "unexpected_error"


class TestServerStartupInfo:
    def test_server_startup_creation(self):
        info = ServerStartupInfo(
            command=["npm", "run", "dev"],
            detected_port=5173,
            detected_url="http://localhost:5173",
        )
        assert info.command == ["npm", "run", "dev"]
        assert info.detected_port == 5173
        assert info.detected_url == "http://localhost:5173"
    
    def test_server_startup_defaults(self):
        info = ServerStartupInfo(command=["npm", "run", "dev"])
        assert info.detected_port is None
        assert info.detected_url is None
        assert info.stdout_capture == ""
        assert info.process_id is None
        assert info.startup_duration_seconds == 0.0


class TestReadinessProbeInfo:
    def test_readiness_probe_creation(self):
        info = ReadinessProbeInfo(
            target_url="http://localhost:5173",
            probe_attempts=3,
            successful_probe=True,
            http_status_code=200,
        )
        assert info.target_url == "http://localhost:5173"
        assert info.probe_attempts == 3
        assert info.successful_probe is True
        assert info.http_status_code == 200
    
    def test_readiness_probe_defaults(self):
        info = ReadinessProbeInfo(target_url="http://localhost:5173")
        assert info.probe_attempts == 0
        assert info.successful_probe is False
        assert info.http_status_code is None


class TestFrontendRecipeResult:
    def test_result_creation(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.INITIALIZING,
            execution_id="exec-test-001",
            project_path="/tmp/test-project",
            framework="vite",
        )
        assert result.stage == FrontendRecipeStage.INITIALIZING
        assert result.execution_id == "exec-test-001"
        assert result.framework == "vite"
        assert result.success is False
    
    def test_result_to_dict(self):
        server_info = ServerStartupInfo(
            command=["npm", "run", "dev"],
            detected_port=5173,
            detected_url="http://localhost:5173",
            startup_duration_seconds=2.5,
        )
        
        readiness_info = ReadinessProbeInfo(
            target_url="http://localhost:5173",
            probe_attempts=2,
            successful_probe=True,
        )
        
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="exec-test-002",
            project_path="/tmp/test-project",
            framework="vite",
            server_startup=server_info,
            readiness_probe=readiness_info,
            browser_verification_executed=True,
            success=True,
            total_duration_seconds=125.0,
        )
        
        data = result.to_dict()
        
        assert data["stage"] == "completed_success"
        assert data["execution_id"] == "exec-test-002"
        assert data["framework"] == "vite"
        assert data["success"] is True
        assert data["browser_verification_executed"] is True
        assert data["server_startup"]["detected_port"] == 5173
        assert data["readiness_probe"]["successful_probe"] is True
    
    def test_result_is_complete(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.SERVER_STARTING,
            execution_id="exec-test-003",
            project_path="/tmp/test-project",
        )
        assert result.is_complete() is False
        
        result.stage = FrontendRecipeStage.COMPLETED_SUCCESS
        assert result.is_complete()
    
    def test_result_allows_success_progression(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="exec-test-004",
            project_path="/tmp/test-project",
            success=True,
        )
        assert result.allows_success_progression()
        
        result.success = False
        assert result.allows_success_progression() is False
        
        result.stage = FrontendRecipeStage.SERVER_STARTING
        result.success = True
        assert result.allows_success_progression() is False
    
    def test_result_get_gate_status(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="exec-test-005",
            project_path="/tmp/test-project",
            success=True,
        )
        assert result.get_gate_status() == "allowed"
        
        result.success = False
        assert result.get_gate_status() == "blocked"
    
    def test_result_with_failure_reason(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_FAILURE,
            execution_id="exec-test-006",
            project_path="/tmp/test-project",
            success=False,
            failure_reason=FrontendRecipeFailureReason.SERVER_START_FAILED,
            error_message="npm run dev exited with code 1",
        )
        
        assert result.failure_reason == FrontendRecipeFailureReason.SERVER_START_FAILED
        assert result.error_message == "npm run dev exited with code 1"
        assert result.allows_success_progression() is False
        
        data = result.to_dict()
        assert data["failure_reason"] == "server_start_failed"


class TestStageTransitions:
    def test_initializing_to_server_starting(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.INITIALIZING,
            execution_id="exec-transition-001",
            project_path="/tmp/test",
        )
        
        result.stage = FrontendRecipeStage.SERVER_STARTING
        result.server_startup = ServerStartupInfo(command=["npm", "run", "dev"])
        
        assert result.stage == FrontendRecipeStage.SERVER_STARTING
        assert result.server_startup is not None
    
    def test_server_starting_to_readiness_probing(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.SERVER_STARTING,
            execution_id="exec-transition-002",
            project_path="/tmp/test",
            server_startup=ServerStartupInfo(
                command=["npm", "run", "dev"],
                detected_port=5173,
                detected_url="http://localhost:5173",
            ),
        )
        
        result.stage = FrontendRecipeStage.READINESS_PROBING
        result.readiness_probe = ReadinessProbeInfo(
            target_url="http://localhost:5173",
        )
        
        assert result.stage == FrontendRecipeStage.READINESS_PROBING
        assert result.readiness_probe.target_url == "http://localhost:5173"
    
    def test_readiness_to_browser_verification(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.READINESS_PROBING,
            execution_id="exec-transition-003",
            project_path="/tmp/test",
            readiness_probe=ReadinessProbeInfo(
                target_url="http://localhost:5173",
                successful_probe=True,
            ),
        )
        
        result.stage = FrontendRecipeStage.BROWSER_VERIFICATION
        result.browser_verification_executed = True
        
        assert result.stage == FrontendRecipeStage.BROWSER_VERIFICATION
        assert result.browser_verification_executed
    
    def test_browser_to_result_persisting(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.BROWSER_VERIFICATION,
            execution_id="exec-transition-004",
            project_path="/tmp/test",
            browser_verification_executed=True,
        )
        
        result.stage = FrontendRecipeStage.RESULT_PERSISTING
        
        assert result.stage == FrontendRecipeStage.RESULT_PERSISTING
    
    def test_persisting_to_completed_success(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.RESULT_PERSISTING,
            execution_id="exec-transition-005",
            project_path="/tmp/test",
        )
        
        result.stage = FrontendRecipeStage.COMPLETED_SUCCESS
        result.success = True
        result.result_persisted = True
        result.result_artifact_path = "/tmp/test/execution-results/exec-transition-005.md"
        
        assert result.is_complete()
        assert result.allows_success_progression()
    
    def test_any_stage_to_failure(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.SERVER_STARTING,
            execution_id="exec-failure-001",
            project_path="/tmp/test",
        )
        
        result.stage = FrontendRecipeStage.COMPLETED_FAILURE
        result.success = False
        result.failure_reason = FrontendRecipeFailureReason.SERVER_START_FAILED
        
        assert result.is_complete()
        assert result.allows_success_progression() is False


class TestTimeoutConstants:
    def test_server_start_timeout(self):
        assert DEFAULT_SERVER_START_TIMEOUT_SECONDS == 30
    
    def test_readiness_probe_timeout(self):
        assert DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS == 60
    
    def test_browser_verification_timeout(self):
        assert DEFAULT_BROWSER_VERIFICATION_TIMEOUT_SECONDS == 120