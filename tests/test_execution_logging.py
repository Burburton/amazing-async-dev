"""Tests for execution logging and recovery classification."""

import pytest
from pathlib import Path
import tempfile
import shutil

from runtime.execution_event_types import ExecutionEventType, get_event_description, get_recovery_hint
from runtime.recovery_classifier import (
    classify_recovery,
    check_resume_eligibility,
    get_recovery_guidance,
    RecoveryClassification,
    ResumeEligibility,
)
from runtime.execution_logger import ExecutionLogger


@pytest.fixture
def temp_project_dir():
    dir_path = tempfile.mkdtemp()
    project_path = Path(dir_path) / "test-project"
    project_path.mkdir()
    (project_path / ".runtime").mkdir(parents=True, exist_ok=True)
    yield project_path
    try:
        shutil.rmtree(dir_path, ignore_errors=True)
    except PermissionError:
        pass


class TestExecutionEventType:
    """Tests for ExecutionEventType enum."""

    def test_event_types_defined(self):
        """ExecutionEventType should have required lifecycle events."""
        assert ExecutionEventType.PLAN_DAY_STARTED.value == "plan-day-started"
        assert ExecutionEventType.PLAN_DAY_COMPLETED.value == "plan-day-completed"
        assert ExecutionEventType.RUN_DAY_STARTED.value == "run-day-started"
        assert ExecutionEventType.BLOCKED_ENTERED.value == "blocked-entered"
        assert ExecutionEventType.BLOCKED_RESOLVED.value == "blocked-resolved"
        assert ExecutionEventType.FAILED_ENTERED.value == "failed-entered"
        assert ExecutionEventType.NORMAL_STOP.value == "normal-stop"
        assert ExecutionEventType.DECISION_APPROVED.value == "decision-approved"

    def test_get_event_description(self):
        """get_event_description should return readable text."""
        desc = get_event_description(ExecutionEventType.PLAN_DAY_STARTED)
        assert "planning" in desc.lower() or "started" in desc.lower()

    def test_get_recovery_hint(self):
        """get_recovery_hint should return actionable hint."""
        hint = get_recovery_hint(ExecutionEventType.BLOCKED_ENTERED)
        assert hint is not None
        assert "unblock" in hint.lower()


class TestRecoveryClassification:
    """Tests for recovery classification."""

    def test_classifies_normal_pause(self):
        """Reviewing phase should classify as normal_pause."""
        runstate = {"current_phase": "reviewing", "blocked_items": [], "decisions_needed": []}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.NORMAL_PAUSE

    def test_classifies_blocked(self):
        """Blocked phase should classify as blocked."""
        runstate = {"current_phase": "blocked", "blocked_items": [{"reason": "API down"}], "decisions_needed": []}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.BLOCKED

    def test_classifies_blocked_by_items(self):
        """Blocked items should classify as blocked even in executing phase."""
        runstate = {"current_phase": "executing", "blocked_items": [{"reason": "X"}], "decisions_needed": []}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.BLOCKED

    def test_classifies_awaiting_decision(self):
        """Pending decisions should classify as awaiting_decision."""
        runstate = {"current_phase": "reviewing", "blocked_items": [], "decisions_needed": [{"decision": "X"}]}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.AWAITING_DECISION

    def test_classifies_ready_to_resume(self):
        """Planning phase with no blockers should classify as ready_to_resume."""
        runstate = {"current_phase": "planning", "blocked_items": [], "decisions_needed": []}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.READY_TO_RESUME

    def test_classifies_already_completed(self):
        """Completed phase should classify as already_completed."""
        runstate = {"current_phase": "completed", "blocked_items": [], "decisions_needed": []}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.ALREADY_COMPLETED

    def test_classifies_already_archived(self):
        """Archived phase should classify as already_archived."""
        runstate = {"current_phase": "archived", "blocked_items": [], "decisions_needed": []}
        result = classify_recovery(runstate)
        assert result == RecoveryClassification.ALREADY_ARCHIVED


class TestResumeEligibility:
    """Tests for resume eligibility."""

    def test_eligible_for_normal_pause(self):
        """Normal pause should be eligible to resume."""
        runstate = {"current_phase": "reviewing", "blocked_items": [], "decisions_needed": []}
        result = check_resume_eligibility(runstate)
        assert result == ResumeEligibility.ELIGIBLE

    def test_eligible_for_ready_to_resume(self):
        """Planning phase should be eligible."""
        runstate = {"current_phase": "planning", "blocked_items": [], "decisions_needed": []}
        result = check_resume_eligibility(runstate)
        assert result == ResumeEligibility.ELIGIBLE

    def test_needs_decision(self):
        """Pending decisions should require decision."""
        runstate = {"current_phase": "reviewing", "blocked_items": [], "decisions_needed": [{"decision": "X"}]}
        result = check_resume_eligibility(runstate)
        assert result == ResumeEligibility.NEEDS_DECISION

    def test_needs_unblock(self):
        """Blocked state should need unblock."""
        runstate = {"current_phase": "blocked", "blocked_items": [{"reason": "X"}], "decisions_needed": []}
        result = check_resume_eligibility(runstate)
        assert result == ResumeEligibility.NEEDS_UNBLOCK

    def test_not_resumable_archived(self):
        """Archived should not be resumable."""
        runstate = {"current_phase": "archived", "blocked_items": [], "decisions_needed": []}
        result = check_resume_eligibility(runstate)
        assert result == ResumeEligibility.NOT_RESUMABLE


class TestRecoveryGuidance:
    """Tests for recovery guidance."""

    def test_provides_guidance_for_blocked(self):
        """Blocked state should get unblock guidance."""
        runstate = {"current_phase": "blocked", "blocked_items": [{"reason": "API down"}], "decisions_needed": []}
        guidance = get_recovery_guidance(runstate)
        assert guidance["classification"] == "blocked"
        assert "unblock" in guidance["recommended_action"].lower()
        assert guidance["blocked_count"] == 1

    def test_provides_guidance_for_decision(self):
        """Awaiting decision should get decision guidance."""
        runstate = {"current_phase": "reviewing", "blocked_items": [], "decisions_needed": [{"decision": "X"}]}
        guidance = get_recovery_guidance(runstate)
        assert guidance["classification"] == "awaiting_decision"
        assert guidance["decisions_count"] == 1

    def test_provides_guidance_with_warnings(self):
        """Guidance should include warnings when appropriate."""
        runstate = {"current_phase": "blocked", "blocked_items": [{"reason": "X"}], "decisions_needed": []}
        guidance = get_recovery_guidance(runstate)
        assert len(guidance["warnings"]) > 0


class TestExecutionLogger:
    """Tests for execution logger."""

    def test_logger_initializes(self, temp_project_dir):
        """ExecutionLogger should initialize with project path."""
        logger = ExecutionLogger(temp_project_dir)
        assert logger.project_path == temp_project_dir
        logger.close()

    def test_logger_logs_event(self, temp_project_dir):
        """ExecutionLogger should log events to SQLite."""
        logger = ExecutionLogger(temp_project_dir)
        logger.log_event(
            ExecutionEventType.PLAN_DAY_STARTED,
            feature_id="001-test",
            product_id="test-product",
            event_data={"test": "data"},
        )
        logger.close()

    def test_logger_logs_transition(self, temp_project_dir):
        """ExecutionLogger should log transitions to SQLite."""
        logger = ExecutionLogger(temp_project_dir)
        logger.log_transition(
            from_phase="planning",
            to_phase="executing",
            feature_id="001-test",
            product_id="test-product",
            reason="Test transition",
        )
        logger.close()


class TestInspectStopCLI:
    """Tests for inspect-stop CLI commands."""

    def test_show_command_works(self, temp_project_dir):
        """inspect-stop show should display recovery info."""
        from typer.testing import CliRunner
        from cli.commands.inspect_stop import app

        from runtime.state_store import StateStore
        store = StateStore(temp_project_dir)
        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
            "current_phase": "planning",
            "active_task": "",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Test",
            "next_recommended_action": "Test",
            "updated_at": "2026-01-01T00:00:00",
        }
        store.save_runstate(runstate)

        runner = CliRunner()
        result = runner.invoke(app, ["show", "--project", "test-project", "--path", str(temp_project_dir.parent)])

        assert result.exit_code == 0
        assert "planning" in result.output

    def test_guidance_command_works(self, temp_project_dir):
        """inspect-stop guidance should provide recovery advice."""
        from typer.testing import CliRunner
        from cli.commands.inspect_stop import app

        from runtime.state_store import StateStore
        store = StateStore(temp_project_dir)
        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
            "current_phase": "blocked",
            "active_task": "",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [{"reason": "API down"}],
            "decisions_needed": [],
            "last_action": "Blocked",
            "next_recommended_action": "Unblock",
            "updated_at": "2026-01-01T00:00:00",
        }
        store.save_runstate(runstate)

        runner = CliRunner()
        result = runner.invoke(app, ["guidance", "--project", "test-project", "--path", str(temp_project_dir.parent)])

        assert result.exit_code == 0
        assert "blocked" in result.output.lower()
        assert "unblock" in result.output.lower()