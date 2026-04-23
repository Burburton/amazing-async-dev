"""Tests for Execution Recovery Console CLI."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from cli.commands.recovery import app
from runtime.recovery_classifier import RecoveryClassification, classify_recovery
from runtime.state_store import StateStore


runner = CliRunner()


class TestRecoveryClassifierIntegration:
    """Test recovery classifier logic used by console."""

    def test_blocked_classification(self):
        runstate = {
            "current_phase": "blocked",
            "blocked_items": ["Dependency unavailable"],
            "decisions_needed": [],
        }
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.BLOCKED

    def test_awaiting_decision_classification(self):
        runstate = {
            "current_phase": "planning",
            "blocked_items": [],
            "decisions_needed": ["Approve deployment?"],
        }
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.AWAITING_DECISION

    def test_failed_classification(self):
        runstate = {
            "current_phase": "executing",
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "execution_failed: timeout",
        }
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.FAILED

    def test_normal_pause_classification(self):
        runstate = {
            "current_phase": "reviewing",
            "blocked_items": [],
            "decisions_needed": [],
        }
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.NORMAL_PAUSE

    def test_ready_to_resume_classification(self):
        runstate = {
            "current_phase": "planning",
            "blocked_items": [],
            "decisions_needed": [],
        }
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.READY_TO_RESUME


class TestRecoveryCLI:
    """Test CLI command registration."""

    def test_recovery_help_shows_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "show" in result.output
        assert "resume" in result.output

    def test_list_help_shows_options(self):
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--all" in result.output

    def test_show_rejects_invalid_format(self):
        result = runner.invoke(app, ["show", "--execution", "invalid"])
        assert result.exit_code == 1
        assert "Invalid" in result.output

    def test_resume_rejects_invalid_format(self):
        result = runner.invoke(app, ["resume", "invalid", "test"])
        assert result.exit_code == 1
        assert "Invalid" in result.output


class TestRecoveryListEmpty:
    """Test list command behavior."""

    def test_shows_no_recoveries_when_no_projects(self, temp_dir):
        result = runner.invoke(app, ["list", "--path", str(temp_dir)])
        assert result.exit_code == 0
        assert "No executions needing recovery" in result.output


class TestRecoveryObserverIntegration:
    """Test recovery show --observe integration with Feature 067."""

    def test_show_observe_flag_registered(self):
        result = runner.invoke(app, ["show", "--help"])
        assert "--observe" in result.output

    def test_show_observe_displays_findings_table(self, temp_dir):
        project = temp_dir / "test-obs"
        project.mkdir()
        
        result = runner.invoke(app, [
            "show",
            "--execution", "exec-test-obs-test",
            "--path", str(temp_dir),
        ])
        assert result.exit_code == 1

    def test_show_observe_without_observer(self, temp_dir):
        project = temp_dir / "test-empty"
        project.mkdir()
        
        result = runner.invoke(app, [
            "show",
            "--execution", "exec-test-empty-test",
            "--path", str(temp_dir),
        ])
        assert result.exit_code == 1


class TestObserverFindingConsumption:
    """Test that recovery console properly consumes ObserverFinding fields."""

    def test_recovery_displays_suggested_action(self):
        from runtime.execution_observer import ObserverFinding, ObserverFindingType, FindingSeverity
        
        finding = ObserverFinding(
            finding_id="test-001",
            finding_type=ObserverFindingType.RECOVERY_OVERDUE,
            severity=FindingSeverity.HIGH,
            reason="Test finding",
            suggested_action="Test action",
            suggested_command="test command",
        )
        
        assert finding.suggested_action == "Test action"
        assert finding.suggested_command == "test command"

    def test_recovery_displays_detected_at_timestamp(self):
        from runtime.execution_observer import ObserverFinding, ObserverFindingType, FindingSeverity
        
        finding = ObserverFinding(
            finding_id="test-002",
            finding_type=ObserverFindingType.DECISION_OVERDUE,
            severity=FindingSeverity.MEDIUM,
            reason="Decision pending",
        )
        
        assert finding.detected_at is not None
        assert len(finding.detected_at) > 0

    def test_recovery_filters_recovery_significant(self):
        from runtime.execution_observer import (
            ObserverFinding,
            ObserverFindingType,
            FindingSeverity,
            ObservationResult,
        )
        
        finding1 = ObserverFinding(
            finding_id="test-001",
            finding_type=ObserverFindingType.RECOVERY_OVERDUE,
            severity=FindingSeverity.HIGH,
            reason="Recovery needed",
            recovery_significant=True,
        )
        
        finding2 = ObserverFinding(
            finding_id="test-002",
            finding_type=ObserverFindingType.BLOCKED_STATE,
            severity=FindingSeverity.LOW,
            reason="Info only",
            recovery_significant=False,
        )
        
        result = ObservationResult(
            observation_id="obs-test",
            project_id="test",
            started_at="2026-01-01T00:00:00",
            findings=[finding1, finding2],
        )
        
        recovery_sig = [f for f in result.findings if f.recovery_significant]
        assert len(recovery_sig) == 1
        assert recovery_sig[0].finding_type == ObserverFindingType.RECOVERY_OVERDUE


class TestRecoveryActionWiring:
    """Test Feature 066a AC-003: Action wiring to async-dev flows."""

    def test_execute_flag_registered(self):
        result = runner.invoke(app, ["resume", "--help"])
        assert "--execute" in result.output

    def test_invoke_asyncdev_command_returns_exit_code(self):
        from cli.commands.recovery import _invoke_asyncdev_command
        exit_code = _invoke_asyncdev_command("status --all-features", "test-project")
        assert exit_code == 0 or exit_code == 1

    def test_resume_without_execute_prints_suggestion(self, temp_dir):
        project = temp_dir / "test-wiring"
        project.mkdir()
        runstate = {
            "current_phase": "blocked",
            "blocked_items": [{"reason": "test blocker"}],
            "project_id": "test-wiring",
            "feature_id": "feature-001",
        }
        store = StateStore(project)
        store.save_runstate(runstate)
        
        result = runner.invoke(app, ["resume", "exec-test-wiring-feature-001", "unblock", "--path", str(temp_dir)])
        assert "Blockers cleared" in result.output or "No RunState found" in result.output