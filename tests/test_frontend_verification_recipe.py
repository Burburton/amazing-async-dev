"""Tests for Feature 062 - Controlled Frontend Verification Execution Recipe."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import re

from runtime.frontend_recipe_state import (
    FrontendRecipeStage,
    FrontendRecipeFailureReason,
    FrontendRecipeResult,
    ServerStartupInfo,
    ReadinessProbeInfo,
    PORT_PATTERNS,
    DEFAULT_SERVER_START_TIMEOUT_SECONDS,
    DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS,
)
from runtime.frontend_verification_recipe import (
    parse_port_from_stdout,
    probe_port_availability,
    probe_url_readiness,
    find_port_by_probe,
    FrontendVerificationRecipe,
    execute_frontend_verification_recipe,
)


class TestFrontendRecipeStage:
    def test_all_stages_exist(self):
        assert FrontendRecipeStage.INITIALIZING.value == "initializing"
        assert FrontendRecipeStage.SERVER_STARTING.value == "server_starting"
        assert FrontendRecipeStage.READINESS_PROBING.value == "readiness_probing"
        assert FrontendRecipeStage.BROWSER_VERIFICATION.value == "browser_verification"
        assert FrontendRecipeStage.RESULT_PERSISTING.value == "result_persisting"
        assert FrontendRecipeStage.COMPLETED_SUCCESS.value == "completed_success"
        assert FrontendRecipeStage.COMPLETED_FAILURE.value == "completed_failure"
        assert FrontendRecipeStage.COMPLETED_TIMEOUT.value == "completed_timeout"

    def test_stage_from_string(self):
        stage = FrontendRecipeStage("completed_success")
        assert stage == FrontendRecipeStage.COMPLETED_SUCCESS

    def test_terminal_stages_method(self):
        terminal = FrontendRecipeStage.terminal_stages()
        assert FrontendRecipeStage.COMPLETED_SUCCESS in terminal
        assert FrontendRecipeStage.COMPLETED_FAILURE in terminal
        assert FrontendRecipeStage.COMPLETED_TIMEOUT in terminal
        assert FrontendRecipeStage.SERVER_STARTING not in terminal

    def test_is_terminal(self):
        assert FrontendRecipeStage.COMPLETED_SUCCESS.is_terminal() is True
        assert FrontendRecipeStage.COMPLETED_FAILURE.is_terminal() is True
        assert FrontendRecipeStage.SERVER_STARTING.is_terminal() is False
        assert FrontendRecipeStage.READINESS_PROBING.is_terminal() is False

    def test_is_success(self):
        assert FrontendRecipeStage.COMPLETED_SUCCESS.is_success() is True
        assert FrontendRecipeStage.COMPLETED_FAILURE.is_success() is False
        assert FrontendRecipeStage.COMPLETED_TIMEOUT.is_success() is False


class TestFrontendRecipeFailureReason:
    def test_all_reasons_exist(self):
        assert FrontendRecipeFailureReason.FRAMEWORK_UNKNOWN.value == "framework_unknown"
        assert FrontendRecipeFailureReason.SERVER_START_FAILED.value == "server_start_failed"
        assert FrontendRecipeFailureReason.SERVER_TIMEOUT.value == "server_timeout"
        assert FrontendRecipeFailureReason.PORT_DISCOVERY_FAILED.value == "port_discovery_failed"
        assert FrontendRecipeFailureReason.READINESS_TIMEOUT.value == "readiness_timeout"
        assert FrontendRecipeFailureReason.BROWSER_VERIFICATION_FAILED.value == "browser_verification_failed"
        assert FrontendRecipeFailureReason.RESULT_PERSISTENCE_FAILED.value == "result_persistence_failed"
        assert FrontendRecipeFailureReason.UNEXPECTED_ERROR.value == "unexpected_error"


class TestServerStartupInfo:
    def test_startup_info_creation(self):
        info = ServerStartupInfo(
            command=["npm", "run", "dev"],
            detected_port=5173,
            detected_url="http://localhost:5173",
            stdout_capture="VITE v5.0.0 ready",
            stderr_capture="",
            process_id=12345,
            startup_duration_seconds=3.5,
        )
        assert info.command == ["npm", "run", "dev"]
        assert info.detected_port == 5173
        assert info.detected_url == "http://localhost:5173"
        assert info.process_id == 12345


class TestReadinessProbeInfo:
    def test_probe_info_creation(self):
        info = ReadinessProbeInfo(
            target_url="http://localhost:3000",
            probe_attempts=10,
            successful_probe=True,
            probe_duration_seconds=5.0,
            http_status_code=200,
        )
        assert info.target_url == "http://localhost:3000"
        assert info.probe_attempts == 10
        assert info.successful_probe is True
        assert info.http_status_code == 200


class TestFrontendRecipeResult:
    def test_result_creation(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.INITIALIZING,
            execution_id="frontend-verify-001",
            project_path="/test/project",
            framework="vite",
        )
        assert result.stage == FrontendRecipeStage.INITIALIZING
        assert result.execution_id == "frontend-verify-001"
        assert result.framework == "vite"

    def test_result_to_dict(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="frontend-verify-002",
            project_path="/test/project",
            framework="next",
            browser_verification_executed=True,
            browser_verification_result={"passed": 3, "failed": 0},
            success=True,
            total_duration_seconds=45.0,
            result_persisted=True,
            result_artifact_path="/test/execution-results/frontend-verify-002.md",
        )
        dict_result = result.to_dict()
        
        assert dict_result["stage"] == "completed_success"
        assert dict_result["execution_id"] == "frontend-verify-002"
        assert dict_result["framework"] == "next"
        assert dict_result["browser_verification_executed"] is True
        assert dict_result["success"] is True
        assert dict_result["result_persisted"] is True

    def test_is_complete(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="frontend-verify-003",
            project_path="/test",
        )
        assert result.is_complete() is True
        
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.SERVER_STARTING,
            execution_id="frontend-verify-004",
            project_path="/test",
        )
        assert result.is_complete() is False

    def test_allows_success_progression(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="frontend-verify-005",
            project_path="/test",
            success=True,
        )
        assert result.allows_success_progression() is True
        
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_FAILURE,
            execution_id="frontend-verify-006",
            project_path="/test",
            success=False,
        )
        assert result.allows_success_progression() is False

    def test_get_gate_status(self):
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="frontend-verify-007",
            project_path="/test",
            success=True,
        )
        assert result.get_gate_status() == "allowed"
        
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_FAILURE,
            execution_id="frontend-verify-008",
            project_path="/test",
            success=False,
        )
        assert result.get_gate_status() == "blocked"


class TestParsePortFromStdout:
    def test_parse_vite_port(self):
        stdout = "VITE v5.0.0  ready in 300 ms\n\n  ➜  Local:   http://localhost:5173/"
        port = parse_port_from_stdout(stdout, "vite")
        assert port == 5173

    def test_parse_vite_fallback_port(self):
        stdout = "VITE v5.0.0  ready\n  ➜  Local:   http://localhost:5174/"
        port = parse_port_from_stdout(stdout, "vite")
        assert port == 5174

    def test_parse_next_port(self):
        stdout = "ready in 2.3s\n  Local:        http://localhost:3000"
        port = parse_port_from_stdout(stdout, "next")
        assert port == 3000

    def test_parse_react_port(self):
        stdout = "Compiled successfully!\nrunning on http://localhost:3001"
        port = parse_port_from_stdout(stdout, "react")
        assert port == 3001

    def test_parse_nuxt_port(self):
        stdout = "Nuxt 3.0.0\nLocal:   http://localhost:3000"
        port = parse_port_from_stdout(stdout, "nuxt")
        assert port == 3000

    def test_parse_generic_port(self):
        stdout = "Server started at localhost:8080"
        port = parse_port_from_stdout(stdout, "generic")
        assert port == 8080

    def test_parse_no_port_found(self):
        stdout = "Starting development server..."
        port = parse_port_from_stdout(stdout, "vite")
        assert port is None

    def test_parse_port_from_stderr(self):
        stderr = "Warning: Port 5173 in use, using 5174 instead\nLocal: http://localhost:5174"
        port = parse_port_from_stdout(stderr, "vite")
        assert port == 5174


class TestProbePortAvailability:
    @patch("socket.socket")
    def test_probe_port_available(self, mock_socket):
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect.return_value = None
        
        result = probe_port_availability(3000)
        assert result is True
        mock_sock.connect.assert_called_once()

    @patch("socket.socket")
    def test_probe_port_unavailable(self, mock_socket):
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect.side_effect = ConnectionRefusedError
        
        result = probe_port_availability(3000)
        assert result is False


class TestProbeUrlReadiness:
    @patch("urllib.request.urlopen")
    def test_probe_url_ready(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response
        
        ready, status = probe_url_readiness("http://localhost:3000", timeout=5)
        assert ready is True
        assert status == 200

    @patch("urllib.request.urlopen")
    @patch("time.sleep")
    def test_probe_url_timeout(self, mock_sleep, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        ready, status = probe_url_readiness("http://localhost:3000", timeout=1)
        assert ready is False
        assert status is None


class TestFrontendVerificationRecipe:
    def test_recipe_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            recipe = FrontendVerificationRecipe(
                project_path=project_path,
                execution_id="test-exec-001",
                server_start_timeout=30,
                readiness_probe_timeout=60,
                browser_verification_timeout=120,
            )
            assert recipe.project_path == project_path
            assert recipe.execution_id == "test-exec-001"
            assert recipe.server_start_timeout == 30

    @patch("runtime.frontend_verification_recipe.detect_framework")
    def test_recipe_framework_unknown(self, mock_detect):
        from runtime.dev_server_manager import DevServerFramework
        mock_detect.return_value = DevServerFramework.UNKNOWN
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            recipe = FrontendVerificationRecipe(
                project_path=project_path,
                execution_id="test-exec-002",
            )
            result = recipe.execute()
            
            assert result.stage == FrontendRecipeStage.COMPLETED_FAILURE
            assert result.failure_reason == FrontendRecipeFailureReason.FRAMEWORK_UNKNOWN


class TestPortPatterns:
    def test_port_patterns_defined(self):
        assert "vite" in PORT_PATTERNS
        assert "next" in PORT_PATTERNS
        assert "react" in PORT_PATTERNS
        assert "nuxt" in PORT_PATTERNS
        assert "sveltekit" in PORT_PATTERNS
        assert "generic" in PORT_PATTERNS

    def test_port_patterns_are_regex(self):
        for framework, patterns in PORT_PATTERNS.items():
            for pattern in patterns:
                # Verify pattern is valid regex
                re.compile(pattern)


class TestConvenienceFunction:
    @patch("runtime.frontend_verification_recipe.FrontendVerificationRecipe.execute")
    @patch("runtime.frontend_verification_recipe.FrontendVerificationRecipe.cleanup")
    def test_execute_frontend_verification_recipe(self, mock_cleanup, mock_execute):
        mock_result = FrontendRecipeResult(
            stage=FrontendRecipeStage.COMPLETED_SUCCESS,
            execution_id="test-exec-003",
            project_path="/test",
            framework="vite",
            success=True,
        )
        mock_execute.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = execute_frontend_verification_recipe(
                project_path=Path(tmpdir),
                execution_id="test-exec-003",
            )
            
            assert result.stage == FrontendRecipeStage.COMPLETED_SUCCESS


# Import urllib for tests
import urllib.request
import urllib.error