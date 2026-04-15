"""Tests for Feature 038: Interactive Frontend Verification Gate."""

import pytest
from pathlib import Path
import tempfile

from runtime.verification_gate import (
    requires_browser_verification,
    is_valid_exception_reason,
    validate_browser_verification,
    get_completion_gate_status,
    classify_verification_type,
    BROWSER_REQUIRED_TYPES,
    VALID_EXCEPTION_REASONS,
)
from runtime.engines.external_tool_engine import ExternalToolEngine


class TestVerificationTypeClassification:
    """Test verification_type classification logic."""

    def test_backend_only_not_requires_browser(self):
        """backend_only should not require browser verification."""
        assert requires_browser_verification("backend_only") is False

    def test_frontend_noninteractive_not_requires_browser(self):
        """frontend_noninteractive should not require browser verification."""
        assert requires_browser_verification("frontend_noninteractive") is False

    def test_frontend_interactive_requires_browser(self):
        """frontend_interactive should require browser verification."""
        assert requires_browser_verification("frontend_interactive") is True

    def test_frontend_visual_behavior_requires_browser(self):
        """frontend_visual_behavior should require browser verification."""
        assert requires_browser_verification("frontend_visual_behavior") is True

    def test_mixed_app_workflow_requires_browser(self):
        """mixed_app_workflow should require browser verification."""
        assert requires_browser_verification("mixed_app_workflow") is True

    def test_all_browser_required_types(self):
        """All BROWSER_REQUIRED_TYPES should return True."""
        for vt in BROWSER_REQUIRED_TYPES:
            assert requires_browser_verification(vt) is True


class TestExceptionReasonValidation:
    """Test exception_reason validation."""

    def test_playwright_unavailable_is_valid(self):
        """playwright_unavailable should be valid exception."""
        assert is_valid_exception_reason("playwright_unavailable") is True

    def test_environment_blocked_is_valid(self):
        """environment_blocked should be valid exception."""
        assert is_valid_exception_reason("environment_blocked") is True

    def test_browser_install_failed_is_valid(self):
        """browser_install_failed should be valid exception."""
        assert is_valid_exception_reason("browser_install_failed") is True

    def test_ci_container_limitation_is_valid(self):
        """ci_container_limitation should be valid exception."""
        assert is_valid_exception_reason("ci_container_limitation") is True

    def test_missing_credentials_is_valid(self):
        """missing_credentials should be valid exception."""
        assert is_valid_exception_reason("missing_credentials") is True

    def test_deterministic_blocker_is_valid(self):
        """deterministic_blocker should be valid exception."""
        assert is_valid_exception_reason("deterministic_blocker") is True

    def test_reclassified_noninteractive_is_valid(self):
        """reclassified_noninteractive should be valid exception."""
        assert is_valid_exception_reason("reclassified_noninteractive") is True

    def test_all_valid_exception_reasons(self):
        """All VALID_EXCEPTION_REASONS should be valid."""
        for reason in VALID_EXCEPTION_REASONS:
            assert is_valid_exception_reason(reason) is True

    def test_invalid_reason_returns_false(self):
        """Invalid reason should return False."""
        assert is_valid_exception_reason("some_random_reason") is False

    def test_empty_reason_returns_false(self):
        """Empty reason should return False."""
        assert is_valid_exception_reason("") is False


class TestBrowserVerificationValidation:
    """Test browser_verification field validation."""

    def test_backend_only_always_valid(self):
        """backend_only should always be valid regardless of browser_verification."""
        result = validate_browser_verification("backend_only", {})
        assert result["valid"] is True
        assert result["browser_required"] is False

    def test_frontend_interactive_with_executed_true(self):
        """frontend_interactive with executed=true should be valid."""
        execution_result = {
            "browser_verification": {
                "executed": True,
                "passed": 5,
                "failed": 0,
            }
        }
        result = validate_browser_verification("frontend_interactive", execution_result)
        assert result["valid"] is True
        assert result["browser_required"] is True
        assert result["passed"] == 5

    def test_frontend_interactive_with_valid_exception(self):
        """frontend_interactive with valid exception should be valid."""
        execution_result = {
            "browser_verification": {
                "executed": False,
                "exception_reason": "playwright_unavailable",
            }
        }
        result = validate_browser_verification("frontend_interactive", execution_result)
        assert result["valid"] is True
        assert result["exception"] == "playwright_unavailable"

    def test_frontend_interactive_without_browser_verification_invalid(self):
        """frontend_interactive without browser_verification should be invalid."""
        result = validate_browser_verification("frontend_interactive", {})
        assert result["valid"] is False
        assert result["browser_required"] is True

    def test_frontend_interactive_with_invalid_exception_invalid(self):
        """frontend_interactive with invalid exception should be invalid."""
        execution_result = {
            "browser_verification": {
                "executed": False,
                "exception_reason": "some_invalid_reason",
            }
        }
        result = validate_browser_verification("frontend_interactive", execution_result)
        assert result["valid"] is False

    def test_frontend_interactive_executed_false_no_exception_invalid(self):
        """frontend_interactive with executed=false and no exception should be invalid."""
        execution_result = {
            "browser_verification": {
                "executed": False,
            }
        }
        result = validate_browser_verification("frontend_interactive", execution_result)
        assert result["valid"] is False


class TestCompletionGateStatus:
    """Test completion gate status determination."""

    def test_backend_only_status_allowed(self):
        """backend_only should always be allowed."""
        assert get_completion_gate_status("backend_only", {}) == "allowed"

    def test_frontend_interactive_executed_allowed(self):
        """frontend_interactive with executed should be allowed."""
        execution_result = {
            "browser_verification": {
                "executed": True,
                "passed": 1,
            }
        }
        assert get_completion_gate_status("frontend_interactive", execution_result) == "allowed"

    def test_frontend_interactive_exception_allowed(self):
        """frontend_interactive with valid exception should be allowed."""
        execution_result = {
            "browser_verification": {
                "exception_reason": "environment_blocked",
            }
        }
        assert get_completion_gate_status("frontend_interactive", execution_result) == "allowed"

    def test_frontend_interactive_missing_blocked(self):
        """frontend_interactive without browser_verification should be blocked."""
        assert get_completion_gate_status("frontend_interactive", {}) == "blocked"


class TestHeuristicClassification:
    """Test heuristic classification for plan-day workflow."""

    def test_backend_task_classified_correctly(self):
        """Backend-only task should be classified as backend_only."""
        result = classify_verification_type(
            "Create database schema",
            ["Add user table", "Create migration file"]
        )
        assert result == "backend_only"

    def test_frontend_static_component_classified_noninteractive(self):
        """Frontend static component (display only) should be frontend_noninteractive."""
        result = classify_verification_type(
            "Create UI header",
            ["Build header component", "Add styling", "Display title"]
        )
        assert result == "frontend_noninteractive"

    def test_frontend_click_interaction_classified_interactive(self):
        """Frontend with click interaction should be frontend_interactive."""
        result = classify_verification_type(
            "Build login page",
            ["Create login form", "Add click handler for submit button"]
        )
        assert result == "frontend_interactive"

    def test_navigation_with_route_changes_classified_interactive(self):
        """Navigation with route changes should be frontend_interactive."""
        result = classify_verification_type(
            "Implement navigation system",
            ["Add navigation menu", "Handle navigate to different pages", "Route changes"]
        )
        assert result == "frontend_interactive"

    def test_form_submission_classified_interactive(self):
        """Form submission should be frontend_interactive."""
        result = classify_verification_type(
            "Create registration form",
            ["Build form UI", "Implement form submission"]
        )
        assert result == "frontend_interactive"

    def test_modal_dialog_classified_interactive(self):
        """Modal dialog should be frontend_interactive."""
        result = classify_verification_type(
            "Add modal component",
            ["Create modal UI", "Handle modal open/close"]
        )
        assert result == "frontend_interactive"


class TestExternalToolEngineBrowserOutput:
    """Test ExternalToolEngine Markdown output for browser verification."""

    def setup_method(self):
        """Setup temp directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "execution-packs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.engine = ExternalToolEngine(output_dir=self.output_dir)

    def teardown_method(self):
        """Cleanup temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backend_only_no_browser_section(self):
        """backend_only should not have browser verification section."""
        pack = {
            "execution_id": "exec-20240115-001",
            "goal": "Test backend task",
            "task_scope": ["Create schema"],
            "constraints": [],
            "must_read": [],
            "deliverables": [{"item": "schema.yaml", "path": "schemas/", "type": "file"}],
            "verification_steps": ["Check output"],
            "stop_conditions": ["Complete"],
            "verification_type": "backend_only",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "Browser Verification (MANDATORY)" not in content
        assert "frontend_interactive" not in content

    def test_frontend_interactive_has_browser_section(self):
        """frontend_interactive should have browser verification section."""
        pack = {
            "execution_id": "exec-20240115-002",
            "goal": "Test frontend interactive task",
            "task_scope": ["Build login form", "Handle click events"],
            "constraints": [],
            "must_read": [],
            "deliverables": [{"item": "login.tsx", "path": "src/", "type": "file"}],
            "verification_steps": ["Verify form works"],
            "stop_conditions": ["Complete"],
            "verification_type": "frontend_interactive",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "Browser Verification (MANDATORY)" in content
        assert "frontend_interactive" in content
        assert "Invoke `/playwright` skill" in content

    def test_frontend_interactive_has_exception_reasons(self):
        """frontend_interactive should list valid exception reasons."""
        pack = {
            "execution_id": "exec-20240115-003",
            "goal": "Test frontend task",
            "task_scope": ["Build UI"],
            "constraints": [],
            "must_read": [],
            "deliverables": [],
            "verification_steps": [],
            "stop_conditions": [],
            "verification_type": "frontend_interactive",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "playwright_unavailable" in content
        assert "environment_blocked" in content
        assert "browser_install_failed" in content

    def test_frontend_interactive_must_rules(self):
        """frontend_interactive should have browser MUST rules."""
        pack = {
            "execution_id": "exec-20240115-004",
            "goal": "Test frontend task",
            "task_scope": ["Build UI"],
            "constraints": [],
            "must_read": [],
            "deliverables": [],
            "verification_steps": [],
            "stop_conditions": [],
            "verification_type": "frontend_interactive",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "- Invoke `/playwright` skill after server is ready (FR-9)" in content
        assert "- Run at least one browser scenario" in content

    def test_frontend_interactive_must_not_rules(self):
        """frontend_interactive should have browser MUST NOT rules."""
        pack = {
            "execution_id": "exec-20240115-005",
            "goal": "Test frontend task",
            "task_scope": ["Build UI"],
            "constraints": [],
            "must_read": [],
            "deliverables": [],
            "verification_steps": [],
            "stop_conditions": [],
            "verification_type": "frontend_interactive",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "- Stop at \"server started\" without browser run" in content
        assert "- Claim `success` without `browser_verification.executed: true`" in content

    def test_frontend_visual_behavior_has_browser_section(self):
        """frontend_visual_behavior should have browser verification section."""
        pack = {
            "execution_id": "exec-20240115-006",
            "goal": "Test visual behavior task",
            "task_scope": ["Add animations"],
            "constraints": [],
            "must_read": [],
            "deliverables": [],
            "verification_steps": [],
            "stop_conditions": [],
            "verification_type": "frontend_visual_behavior",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "Browser Verification (MANDATORY)" in content

    def test_mixed_app_workflow_has_browser_section(self):
        """mixed_app_workflow should have browser verification section."""
        pack = {
            "execution_id": "exec-20240115-007",
            "goal": "Test mixed workflow",
            "task_scope": ["Build API and frontend"],
            "constraints": [],
            "must_read": [],
            "deliverables": [],
            "verification_steps": [],
            "stop_conditions": [],
            "verification_type": "mixed_app_workflow",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "Browser Verification (MANDATORY)" in content

    def test_browser_verification_in_execution_result_format(self):
        """frontend_interactive should include browser_verification in format."""
        pack = {
            "execution_id": "exec-20240115-008",
            "goal": "Test frontend task",
            "task_scope": ["Build UI"],
            "constraints": [],
            "must_read": [],
            "deliverables": [],
            "verification_steps": [],
            "stop_conditions": [],
            "verification_type": "frontend_interactive",
        }
        self.engine._save_markdown(pack, self.output_dir / "test.md")
        content = (self.output_dir / "test.md").read_text()
        assert "browser_verification:" in content
        assert "executed: true|false" in content


class TestSchemaFieldPresence:
    """Test that schema files contain new fields."""

    def test_execution_pack_schema_has_verification_type(self):
        """execution-pack.schema.yaml should have verification_type."""
        import yaml
        schema_path = Path("schemas/execution-pack.schema.yaml")
        schema = yaml.safe_load(schema_path.read_text())
        
        assert "verification_type" in schema.get("optional", [])
        assert "verification_type" in schema.get("fields", {})
        
        vt_field = schema["fields"]["verification_type"]
        assert vt_field["type"] == "enum"
        assert "backend_only" in vt_field["values"]
        assert "frontend_interactive" in vt_field["values"]

    def test_execution_result_schema_has_browser_verification(self):
        """execution-result.schema.yaml should have browser_verification."""
        import yaml
        schema_path = Path("schemas/execution-result.schema.yaml")
        schema = yaml.safe_load(schema_path.read_text())
        
        assert "browser_verification" in schema.get("optional", [])
        assert "browser_verification" in schema.get("fields", {})
        
        bv_field = schema["fields"]["browser_verification"]
        assert bv_field["type"] == "object"
        assert "executed" in bv_field.get("properties", {})

    def test_execution_pack_template_has_verification_type(self):
        """execution-pack.template.md should mention verification_type."""
        template_path = Path("templates/execution-pack.template.md")
        content = template_path.read_text()
        
        assert "verification_type" in content
        assert "frontend_interactive" in content

    def test_execution_result_template_has_browser_verification(self):
        """execution-result.template.md should mention browser_verification."""
        template_path = Path("templates/execution-result.template.md")
        content = template_path.read_text()
        
        assert "browser_verification" in content
        assert "executed" in content


class TestAgentsMdSection9:
    """Test that AGENTS.md has Section 9."""

    def test_agents_md_has_section_9(self):
        """AGENTS.md should have Section 9."""
        agents_path = Path("AGENTS.md")
        content = agents_path.read_text()
        
        assert "## 9. Interactive Frontend Verification Gate" in content

    def test_agents_md_has_fr7_completion_gate(self):
        """AGENTS.md should have FR-7 Completion Gate."""
        agents_path = Path("AGENTS.md")
        content = agents_path.read_text()
        
        assert "FR-7" in content
        assert "Completion Gate" in content

    def test_agents_md_has_fr9_playwright_policy(self):
        """AGENTS.md should have FR-9 Playwright invocation policy."""
        agents_path = Path("AGENTS.md")
        content = agents_path.read_text()
        
        assert "FR-9" in content
        assert "/playwright" in content

    def test_agents_md_has_exception_reasons_table(self):
        """AGENTS.md should have exception reasons table."""
        agents_path = Path("AGENTS.md")
        content = agents_path.read_text()
        
        assert "playwright_unavailable" in content
        assert "environment_blocked" in content

    def test_agents_md_has_core_principle(self):
        """AGENTS.md should have core principle statement."""
        agents_path = Path("AGENTS.md")
        content = agents_path.read_text()
        
        assert "environment setup is not verification" in content