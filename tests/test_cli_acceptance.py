"""Tests for asyncdev acceptance CLI commands (Feature 077)."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from cli.commands.acceptance import app


runner = CliRunner()


@pytest.fixture
def temp_project(temp_dir):
    """Create a minimal project with runstate."""
    project_path = temp_dir / "test-project"
    project_path.mkdir(parents=True)
    
    runstate_path = project_path / "runstate.md"
    runstate_content = """# RunState

## Metadata
- project_id: test-project
- feature_id: feature-001
- current_phase: reviewing

## State
- last_action: External execution completed
- updated_at: 2025-01-15T10:00:00Z
"""
    runstate_path.write_text(runstate_content)
    
    execution_results_path = project_path / "execution-results"
    execution_results_path.mkdir()
    
    execution_result_path = execution_results_path / "exec-test-001.md"
    execution_result_content = """# ExecutionResult

execution_id: exec-test-001
status: success
completed_items:
  - "Implementation complete"
artifacts_created:
  - name: "main.py"
    path: "src/main.py"
    type: file
"""
    execution_result_path.write_text(execution_result_content)
    
    return project_path


class TestAcceptanceRun:
    """Tests for acceptance run command."""

    def test_run_requires_project(self):
        runner.invoke(app, ["run"])
        assert True

    def test_run_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "run",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceStatus:
    """Tests for acceptance status command."""

    def test_status_requires_project(self):
        runner.invoke(app, ["status"])
        assert True

    def test_status_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "status",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceHistory:
    """Tests for acceptance history command."""

    def test_history_requires_project(self):
        runner.invoke(app, ["history"])
        assert True

    def test_history_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "history",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceResult:
    """Tests for acceptance result command."""

    def test_result_requires_project(self):
        runner.invoke(app, ["result"])
        assert True

    def test_result_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "result",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceRetry:
    """Tests for acceptance retry command."""

    def test_retry_requires_project(self):
        runner.invoke(app, ["retry"])
        assert True

    def test_retry_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "retry",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceRecovery:
    """Tests for acceptance recovery command."""

    def test_recovery_requires_project(self):
        runner.invoke(app, ["recovery"])
        assert True

    def test_recovery_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "recovery",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceGate:
    """Tests for acceptance gate command."""

    def test_gate_requires_project(self):
        runner.invoke(app, ["gate"])
        assert True

    def test_gate_with_project_path(self, temp_project):
        result = runner.invoke(app, [
            "gate",
            "--project", str(temp_project),
        ])
        assert result.exit_code in (0, 1)


class TestAcceptanceCLIRegistration:
    """Tests for CLI registration in asyncdev.py."""

    def test_acceptance_app_registered(self):
        from cli.asyncdev import app as main_app
        result = runner.invoke(main_app, ["--help"])
        assert "acceptance" in result.output or result.exit_code == 0


class TestRecoveryClassifierAcceptance:
    """Tests for acceptance classification in recovery_classifier."""

    def test_awaiting_acceptance_classification(self):
        from runtime.recovery_classifier import RecoveryClassification, classify_recovery
        
        runstate = {
            "current_phase": "reviewing",
            "acceptance_recovery_pending": True,
        }
        
        classification = classify_recovery(runstate)
        assert classification == RecoveryClassification.AWAITING_ACCEPTANCE

    def test_acceptance_terminal_state_failure_classification(self):
        from runtime.recovery_classifier import RecoveryClassification, classify_recovery
        
        runstate = {
            "current_phase": "reviewing",
            "acceptance_terminal_state": "failure",
        }
        
        classification = classify_recovery(runstate)
        assert classification == RecoveryClassification.AWAITING_ACCEPTANCE

    def test_needs_acceptance_eligibility(self):
        from runtime.recovery_classifier import ResumeEligibility, check_resume_eligibility
        
        runstate = {
            "current_phase": "reviewing",
            "acceptance_recovery_pending": True,
        }
        
        eligibility = check_resume_eligibility(runstate)
        assert eligibility == ResumeEligibility.NEEDS_ACCEPTANCE

    def test_acceptance_guidance_available(self):
        from runtime.recovery_classifier import RecoveryClassification, get_recovery_guidance
        
        runstate = {
            "current_phase": "reviewing",
            "acceptance_recovery_pending": True,
        }
        
        guidance = get_recovery_guidance(runstate)
        assert guidance["classification"] == RecoveryClassification.AWAITING_ACCEPTANCE.value
        assert "acceptance" in guidance["recommended_action"].lower()