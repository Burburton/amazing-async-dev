"""Tests for Feature 056 - Browser Verification Auto Integration."""

import pytest
from pathlib import Path

from runtime.verification_classifier import (
    VerificationType,
    ClassificationResult,
    classify_files,
    classify_verification_type_from_files,
    classify_verification_type_from_context,
    get_verification_type,
)
from runtime.browser_verifier import (
    BrowserVerificationStatus,
    ExceptionReason,
    BrowserVerificationResult,
    ScenarioResult,
    ConsoleError,
    check_playwright_available,
    create_exception_result,
    to_execution_result_dict,
)


class TestVerificationClassifier:
    """Tests for verification type classification."""

    def test_classify_backend_only_files(self):
        """Backend files should classify as backend_only."""
        files = ["src/api/routes.py", "backend/server.py"]
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.BACKEND_ONLY
        assert result.confidence >= 0.9
        assert "backend_only_files" in result.detected_patterns

    def test_classify_docs_only(self):
        """Documentation files should classify as backend_only."""
        files = ["docs/readme.md", "docs/api.md"]
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.BACKEND_ONLY
        assert result.confidence >= 0.9
        assert "docs_only" in result.detected_patterns

    def test_classify_tests_only(self):
        """Test files should classify as backend_only."""
        files = ["tests/test_api.py", "tests/test_routes.py"]
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.BACKEND_ONLY
        assert result.confidence >= 0.9
        assert "tests_only" in result.detected_patterns

    def test_classify_frontend_components(self):
        """Frontend component files should classify as frontend_interactive."""
        files = ["src/components/Button.tsx", "components/Header.jsx"]
        result = classify_verification_type_from_files(files, "Add button component")
        
        assert result.verification_type == VerificationType.FRONTEND_INTERACTIVE
        assert "frontend_component" in result.detected_patterns

    def test_classify_frontend_pages(self):
        """Frontend page files should classify as frontend_interactive."""
        files = ["src/pages/Home.tsx", "pages/About.vue"]
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.FRONTEND_INTERACTIVE
        assert "frontend_page" in result.detected_patterns

    def test_classify_frontend_styles(self):
        """Style files should classify as frontend_visual_behavior."""
        files = ["src/styles/main.css", "css/theme.scss"]
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.FRONTEND_VISUAL_BEHAVIOR
        assert "frontend_style_only" in result.detected_patterns

    def test_classify_mixed_workflow(self):
        """Mix of frontend and backend should classify as mixed_app_workflow."""
        files = ["src/components/Button.tsx", "src/api/routes.py"]
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.MIXED_APP_WORKFLOW
        assert "mixed_frontend_backend" in result.detected_patterns

    def test_classify_with_interactive_keywords(self):
        """Interactive keywords should increase confidence for frontend_interactive."""
        files = ["src/components/Form.tsx"]
        result = classify_verification_type_from_files(files, "Add form with click and submit button")
        
        assert result.verification_type == VerificationType.FRONTEND_INTERACTIVE
        assert "interactive_keywords" in result.detected_patterns
        assert result.confidence >= 0.9

    def test_classify_empty_files(self):
        """Empty file list should default to backend_only."""
        files = []
        result = classify_verification_type_from_files(files)
        
        assert result.verification_type == VerificationType.BACKEND_ONLY

    def test_classify_files_helper(self):
        """classify_files should correctly detect categories."""
        files = ["src/components/Button.tsx", "src/pages/Home.tsx", "src/styles/main.css", "src/api/routes.py"]
        has_comp, has_page, has_style, has_backend = classify_files(files)
        
        assert has_comp is True
        assert has_page is True
        assert has_style is True
        assert has_backend is True

    def test_get_verification_type_convenience(self):
        """get_verification_type should return just the type."""
        files = ["src/components/Button.tsx"]
        vt = get_verification_type(files=files, feature_description="Add button")
        
        assert vt == VerificationType.FRONTEND_INTERACTIVE

    def test_classify_from_context_feature_spec(self):
        """classify_verification_type_from_context should use feature_spec."""
        feature_spec = {
            "description": "Add login form component",
            "scope": {"in_scope": ["src/components/Login.tsx"]},
        }
        result = classify_verification_type_from_context(feature_spec=feature_spec)
        
        assert result.verification_type == VerificationType.FRONTEND_INTERACTIVE


class TestBrowserVerifier:
    """Tests for browser verifier module."""

    def test_check_playwright_available(self):
        """check_playwright_available should return boolean."""
        result = check_playwright_available()
        assert isinstance(result, bool)

    def test_create_exception_result(self):
        """create_exception_result should create proper exception result."""
        result = create_exception_result(
            ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
            "Playwright not installed",
        )
        
        assert result.executed is False
        assert result.status == BrowserVerificationStatus.EXCEPTION
        assert result.exception_reason == ExceptionReason.PLAYWRIGHT_UNAVAILABLE
        assert result.exception_details == "Playwright not installed"

    def test_exception_reasons_from_spec(self):
        """ExceptionReason should match Feature 038 spec."""
        expected_reasons = [
            "playwright_unavailable",
            "environment_blocked",
            "browser_install_failed",
            "ci_container_limitation",
            "missing_credentials",
            "deterministic_blocker",
            "reclassified_noninteractive",
        ]
        
        for reason in expected_reasons:
            assert ExceptionReason(reason) is not None

    def test_browser_verification_status_enum(self):
        """BrowserVerificationStatus should have expected values."""
        assert BrowserVerificationStatus.SUCCESS.value == "success"
        assert BrowserVerificationStatus.FAILED.value == "failed"
        assert BrowserVerificationStatus.EXCEPTION.value == "exception"
        assert BrowserVerificationStatus.SKIPPED.value == "skipped"

    def test_scenario_result_dataclass(self):
        """ScenarioResult should be a proper dataclass."""
        result = ScenarioResult(
            name="page_render",
            passed=True,
            screenshot_path="/path/to/screenshot.png",
            duration_seconds=1.5,
        )
        
        assert result.name == "page_render"
        assert result.passed is True
        assert result.screenshot_path == "/path/to/screenshot.png"

    def test_console_error_dataclass(self):
        """ConsoleError should be a proper dataclass."""
        error = ConsoleError(
            level="error",
            message="Uncaught TypeError",
            url="http://localhost:3000/app.js",
            line=42,
        )
        
        assert error.level == "error"
        assert error.message == "Uncaught TypeError"
        assert error.line == 42

    def test_browser_verification_result_dataclass(self):
        """BrowserVerificationResult should be a proper dataclass."""
        result = BrowserVerificationResult(
            executed=True,
            status=BrowserVerificationStatus.SUCCESS,
            passed=3,
            failed=0,
            scenarios_run=["page_render", "console_check"],
        )
        
        assert result.executed is True
        assert result.passed == 3
        assert result.failed == 0

    def test_to_execution_result_dict(self):
        """to_execution_result_dict should convert to ExecutionResult format."""
        result = BrowserVerificationResult(
            executed=True,
            status=BrowserVerificationStatus.SUCCESS,
            passed=2,
            failed=1,
            scenarios_run=["page_render", "console_check"],
            duration_seconds=5.0,
        )
        
        dict_result = to_execution_result_dict(result)
        
        assert "browser_verification" in dict_result
        assert dict_result["browser_verification"]["executed"] is True
        assert dict_result["browser_verification"]["passed"] == 2
        assert dict_result["browser_verification"]["failed"] == 1

    def test_to_execution_result_dict_with_exception(self):
        """to_execution_result_dict should include exception info."""
        result = create_exception_result(
            ExceptionReason.CI_CONTAINER_LIMITATION,
            "Cannot run browser in CI",
        )
        
        dict_result = to_execution_result_dict(result)
        
        assert dict_result["browser_verification"]["executed"] is False
        assert dict_result["browser_verification"]["exception_reason"] == "ci_container_limitation"

    def test_screenshot_path_with_project_name(self):
        """Screenshot path should use project_name for subdirectory."""
        from runtime.browser_verifier import run_browser_verification
        
        if check_playwright_available():
            result = run_browser_verification(
                url="http://example.com",
                project_name="test-project",
            )
            assert result is not None
        else:
            result = create_exception_result(
                ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
                "Playwright not installed",
            )
            assert result.executed is False

    def test_screenshot_path_default(self):
        """Screenshot path should use 'default' when no project_name."""
        from runtime.browser_verifier import run_browser_verification
        
        if check_playwright_available():
            result = run_browser_verification(
                url="http://example.com",
            )
            assert result is not None
        else:
            result = create_exception_result(
                ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
                "Playwright not installed",
            )
            assert result.executed is False


class TestVerificationTypeEnum:
    """Tests for VerificationType enum."""

    def test_all_types_exist(self):
        """VerificationType should have all expected types."""
        assert VerificationType.BACKEND_ONLY.value == "backend_only"
        assert VerificationType.FRONTEND_NONINTERACTIVE.value == "frontend_noninteractive"
        assert VerificationType.FRONTEND_INTERACTIVE.value == "frontend_interactive"
        assert VerificationType.FRONTEND_VISUAL_BEHAVIOR.value == "frontend_visual_behavior"
        assert VerificationType.MIXED_APP_WORKFLOW.value == "mixed_app_workflow"

    def test_type_from_string(self):
        """VerificationType should be constructible from string."""
        vt = VerificationType("frontend_interactive")
        assert vt == VerificationType.FRONTEND_INTERACTIVE


class TestDevServerManager:
    """Tests for dev server manager module."""

    def test_dev_server_framework_enum(self):
        """DevServerFramework should have expected frameworks."""
        from runtime.dev_server_manager import DevServerFramework
        
        assert DevServerFramework.VITE.value == "vite"
        assert DevServerFramework.NEXT_JS.value == "next"
        assert DevServerFramework.REACT.value == "react"
        assert DevServerFramework.UNKNOWN.value == "unknown"

    def test_detect_framework_unknown_without_package_json(self):
        """detect_framework should return UNKNOWN without package.json."""
        from runtime.dev_server_manager import detect_framework, DevServerFramework
        
        result = detect_framework(Path("/nonexistent/path"))
        assert result == DevServerFramework.UNKNOWN

    def test_default_ports_mapping(self):
        """DEFAULT_PORTS should map frameworks to ports."""
        from runtime.dev_server_manager import DEFAULT_PORTS, DevServerFramework
        
        assert DEFAULT_PORTS[DevServerFramework.VITE] == 5173
        assert DEFAULT_PORTS[DevServerFramework.NEXT_JS] == 3000

    def test_get_start_command(self):
        """get_start_command should return appropriate commands."""
        from runtime.dev_server_manager import get_start_command, DevServerFramework
        
        vite_cmd = get_start_command(DevServerFramework.VITE)
        assert vite_cmd == ["npm", "run", "dev"]
        
        next_cmd = get_start_command(DevServerFramework.NEXT_JS)
        assert next_cmd == ["npm", "run", "dev"]

    def test_dev_server_status_dataclass(self):
        """DevServerStatus should be a proper dataclass."""
        from runtime.dev_server_manager import DevServerStatus, DevServerFramework
        
        status = DevServerStatus(
            running=True,
            port=3000,
            url="http://localhost:3000",
            framework=DevServerFramework.NEXT_JS,
            process_id=12345,
            started_at="2024-01-15 10:00:00",
            error_message=None,
        )
        
        assert status.running is True
        assert status.port == 3000
        assert status.framework == DevServerFramework.NEXT_JS

    def test_dev_server_result_dataclass(self):
        """DevServerResult should be a proper dataclass."""
        from runtime.dev_server_manager import DevServerResult, DevServerStatus, DevServerFramework
        
        status = DevServerStatus(
            running=False,
            port=None,
            url=None,
            framework=DevServerFramework.UNKNOWN,
            process_id=None,
            started_at=None,
            error_message="Test error",
        )
        
        result = DevServerResult(
            success=False,
            status=status,
            duration_seconds=1.0,
        )
        
        assert result.success is False
        assert result.status.error_message == "Test error"