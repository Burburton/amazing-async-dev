"""Tests for asyncdev run-day command and Feature 036."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from cli.commands.run_day import app, _extract_execution_intent, _check_drift_warnings
from runtime.state_store import StateStore


runner = CliRunner()


@pytest.fixture
def setup_product(temp_dir):
    """Create a product with runstate for testing."""
    from cli.commands.new_product import app as new_product_app
    
    runner.invoke(new_product_app, [
        "create",
        "--product-id", "test-product",
        "--name", "Test Product",
        "--path", str(temp_dir),
    ])
    
    yield temp_dir / "test-product"


class TestRunDayExecute:
    """Tests for run-day execute command."""

    def test_mock_mode_executes(self):
        """run-day mock should execute without error."""
        result = runner.invoke(app, [
            "execute",
            "--mode", "mock",
        ])
        
        assert result.exit_code == 0
        assert "Mock" in result.output or "mock" in result.output.lower()

    def test_dry_run_does_not_modify(self):
        """run-day with dry-run should not modify state."""
        result = runner.invoke(app, [
            "execute",
            "--mode", "mock",
            "--dry-run",
        ])
        
        assert "Dry run" in result.output

    def test_project_parameter_with_valid_project(self, setup_product):
        """run-day --project should scope execution to specified project."""
        project_path = setup_product
        
        result = runner.invoke(app, [
            "execute",
            "--project", "test-product",
            "--mode", "mock",
            "--path", str(project_path.parent),
        ])
        
        assert result.exit_code == 0

    def test_project_parameter_with_invalid_project(self, temp_dir):
        """run-day --project with invalid project should error."""
        result = runner.invoke(app, [
            "execute",
            "--project", "nonexistent-project",
            "--mode", "mock",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Project not found" in result.output

    def test_project_parameter_in_help(self):
        """run-day execute --help should show --project parameter."""
        result = runner.invoke(app, ["execute", "--help"])
        
        assert result.exit_code == 0
        assert "--project" in result.output

    def test_fallback_without_project(self):
        """run-day without --project should use default behavior."""
        result = runner.invoke(app, [
            "execute",
            "--mode", "mock",
        ])
        
        assert result.exit_code == 0


class TestExecutionIntentHelpers:
    """Tests for execution intent helper functions - Feature 036."""

    def test_extract_intent_from_planning_mode(self):
        """_extract_execution_intent should extract planning_mode."""
        execution_pack = {
            "planning_mode": "continue_work",
            "goal": "Execute: Test task",
            "prior_doctor_status": "HEALTHY",
        }
        
        intent = _extract_execution_intent(execution_pack)
        
        assert intent.get("planning_mode") == "continue_work"
        assert intent.get("has_planning_context") is True
        assert intent.get("bounded_target") == "Execute: Test task"

    def test_extract_intent_without_planning_mode(self):
        """_extract_execution_intent should handle missing planning_mode."""
        execution_pack = {
            "goal": "Execute: Test task",
        }
        
        intent = _extract_execution_intent(execution_pack)
        
        assert intent.get("has_planning_context") is False
        assert intent.get("planning_mode") == ""

    def test_extract_intent_with_recovery_flag(self):
        """_extract_execution_intent should extract recovery_flag."""
        execution_pack = {
            "planning_mode": "recover_and_continue",
            "plan_recovery_flag": True,
        }
        
        intent = _extract_execution_intent(execution_pack)
        
        assert intent.get("recovery_flag") is True

    def test_extract_intent_with_closeout_flag(self):
        """_extract_execution_intent should extract closeout_flag."""
        execution_pack = {
            "planning_mode": "closeout_first",
            "plan_closeout_flag": True,
        }
        
        intent = _extract_execution_intent(execution_pack)
        
        assert intent.get("closeout_flag") is True

    def test_extract_intent_with_blocked_flag(self):
        """_extract_execution_intent should detect blocked flag."""
        execution_pack = {
            "planning_mode": "blocked_waiting_for_decision",
            "safe_to_execute": False,
        }
        
        intent = _extract_execution_intent(execution_pack)
        
        assert intent.get("blocked_flag") is True

    def test_extract_intent_with_prior_recommendation(self):
        """_extract_execution_intent should extract prior recommendation."""
        execution_pack = {
            "planning_mode": "continue_work",
            "prior_recommended_next_action": "Continue execution",
        }
        
        intent = _extract_execution_intent(execution_pack)
        
        assert intent.get("prior_recommendation") == "Continue execution"


class TestDriftWarningHelpers:
    """Tests for drift warning helper functions."""

    def test_check_drift_blocked_mode(self):
        """_check_drift_warnings should warn for blocked mode."""
        intent = {"planning_mode": "blocked_waiting_for_decision", "blocked_flag": True}
        execution_pack = {"task_scope": ["Implement feature"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert len(warnings) > 0
        assert any("blocked" in w.lower() for w in warnings)

    def test_check_drift_closeout_expansion(self):
        """_check_drift_warnings should warn for closeout + expansion."""
        intent = {"planning_mode": "closeout_first"}
        execution_pack = {"task_scope": ["Implement new feature"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert any("closeout" in w.lower() or "expansion" in w.lower() for w in warnings)

    def test_check_drift_verification_non_verification(self):
        """_check_drift_warnings should warn for verification_first + non-verification."""
        intent = {"planning_mode": "verification_first"}
        execution_pack = {"task_scope": ["Build new component"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert any("verification" in w.lower() for w in warnings)

    def test_check_drift_recovery_no_recovery_task(self):
        """_check_drift_warnings should warn for recovery mode without recovery task."""
        intent = {"planning_mode": "recover_and_continue"}
        execution_pack = {"task_scope": ["Implement feature"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert any("recovery" in w.lower() for w in warnings)

    def test_check_drift_prior_blocked_status(self):
        """_check_drift_warnings should warn for prior BLOCKED status."""
        intent = {"planning_mode": "continue_work", "prior_doctor_status": "BLOCKED"}
        execution_pack = {"task_scope": ["Continue work"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert any("blocked" in w.lower() or "blocker" in w.lower() for w in warnings)

    def test_check_drift_no_warnings_aligned(self):
        """_check_drift_warnings should return empty for aligned execution."""
        intent = {"planning_mode": "continue_work"}
        execution_pack = {"task_scope": ["Execute normal task"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert len(warnings) == 0

    def test_check_drift_closeout_with_closeout_task(self):
        """_check_drift_warnings should not warn for closeout task."""
        intent = {"planning_mode": "closeout_first"}
        execution_pack = {"task_scope": ["Archive feature", "Complete closeout"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert len(warnings) == 0

    def test_check_drift_verification_with_verification_task(self):
        """_check_drift_warnings should not warn for verification task."""
        intent = {"planning_mode": "verification_first"}
        execution_pack = {"task_scope": ["Verify implementation", "Run tests"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert len(warnings) == 0

    def test_check_drift_recovery_with_recovery_task(self):
        """_check_drift_warnings should not warn when recovery task is present."""
        intent = {"planning_mode": "recover_and_continue", "recovery_flag": True}
        execution_pack = {"task_scope": ["Fix verification issue", "Resolve blocker"]}
        
        warnings = _check_drift_warnings(intent, execution_pack)
        
        assert len(warnings) == 0


class TestPlanningModeIntent:
    """Tests for planning mode intent mapping."""

    def test_continue_work_intent(self):
        """continue_work mode should map to correct intent."""
        from cli.commands.run_day import PLANNING_MODE_INTENT
        
        assert PLANNING_MODE_INTENT.get("continue_work") is not None
        assert "Normal" in PLANNING_MODE_INTENT.get("continue_work", "")

    def test_recover_and_continue_intent(self):
        """recover_and_continue mode should map to recovery intent."""
        from cli.commands.run_day import PLANNING_MODE_INTENT
        
        assert PLANNING_MODE_INTENT.get("recover_and_continue") is not None
        assert "Recovery" in PLANNING_MODE_INTENT.get("recover_and_continue", "")

    def test_verification_first_intent(self):
        """verification_first mode should map to verification intent."""
        from cli.commands.run_day import PLANNING_MODE_INTENT
        
        assert PLANNING_MODE_INTENT.get("verification_first") is not None
        assert "verification" in PLANNING_MODE_INTENT.get("verification_first", "").lower()

    def test_closeout_first_intent(self):
        """closeout_first mode should map to closeout intent."""
        from cli.commands.run_day import PLANNING_MODE_INTENT
        
        assert PLANNING_MODE_INTENT.get("closeout_first") is not None
        assert "closeout" in PLANNING_MODE_INTENT.get("closeout_first", "").lower()

    def test_blocked_waiting_intent(self):
        """blocked_waiting_for_decision mode should map to blocked intent."""
        from cli.commands.run_day import PLANNING_MODE_INTENT
        
        assert PLANNING_MODE_INTENT.get("blocked_waiting_for_decision") is not None
        assert "blocked" in PLANNING_MODE_INTENT.get("blocked_waiting_for_decision", "").lower()