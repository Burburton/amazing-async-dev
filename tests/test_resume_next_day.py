"""Tests for asyncdev resume-next-day command."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typer.testing import CliRunner
from cli.commands.resume_next_day import app
from runtime.state_store import StateStore


runner = CliRunner()


@pytest.fixture
def setup_product_with_runstate(temp_dir):
    """Create product with runstate for testing."""
    from cli.commands.new_product import app as new_product_app
    
    runner.invoke(new_product_app, [
        "create",
        "--product-id", "test-product",
        "--name", "Test Product",
        "--path", str(temp_dir),
    ])
    
    yield temp_dir / "test-product"


class TestResumeContinueLoop:
    """Tests for resume-next-day continue-loop command."""

    def test_continues_with_approve(self, setup_product_with_runstate):
        """continue-loop with approve should clear decisions."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = [
            {"decision": "Test decision", "options": ["A", "B"]}
        ]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "All decisions approved" in result.output

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["decisions_needed"] == []

    def test_sets_phase_to_planning(self, setup_product_with_runstate):
        """continue-loop should set phase to planning."""
        runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"

    def test_revise_requires_choice(self, setup_product_with_runstate):
        """continue-loop with revise requires --revise-choice."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = [
            {"decision": "Choose approach", "options": ["A", "B"], "recommendation": "A"}
        ]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "revise",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 1
        assert "Must specify --revise-choice" in result.output

    def test_revise_with_choice(self, setup_product_with_runstate):
        """continue-loop with revise and choice should work."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = [
            {"decision": "Choose approach", "options": ["A", "B"], "recommendation": "A"}
        ]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "revise",
            "--revise-choice", "Option A",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "revised to: Option A" in result.output

    def test_defer_keeps_decision(self, setup_product_with_runstate):
        """continue-loop with defer should note deferred."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = [
            {"decision": "Choose approach", "options": ["A", "B"], "recommendation": "A"}
        ]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "defer",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "deferred" in result.output.lower()

    def test_dry_run_does_not_save(self, setup_product_with_runstate):
        """continue-loop with dry-run should not save."""
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--dry-run",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert "Dry run - not saving" in result.output

    def test_fails_without_runstate(self, temp_dir):
        """continue-loop should fail if no RunState."""
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "nonexistent",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output

    def test_no_decisions_message(self, setup_product_with_runstate):
        """continue-loop should note no pending decisions."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = []
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert "No pending decisions" in result.output


class TestResumeStatus:
    """Tests for resume-next-day status command."""

    def test_shows_runstate_status(self, setup_product_with_runstate):
        """status should display RunState fields."""
        result = runner.invoke(app, [
            "status",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "Phase" in result.output
        assert "Project" in result.output

    def test_shows_pending_decisions(self, setup_product_with_runstate):
        """status should show pending decisions."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = [
            {"decision": "Test decision", "options": ["A", "B"]}
        ]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "status",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert "Pending Decisions" in result.output
        assert "Test decision" in result.output

    def test_shows_no_runstate_message(self, temp_dir):
        """status should handle missing RunState."""
        result = runner.invoke(app, [
            "status",
            "--project", "nonexistent",
            "--path", str(temp_dir),
        ])

        assert "No RunState found" in result.output


class TestResumeUnblock:
    """Tests for resume-next-day unblock command."""

    def test_unblock_from_blocked_state(self, setup_product_with_runstate):
        """unblock should transition from blocked to planning."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [{"reason": "Dependency missing"}]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "unblock",
            "--project", "test-product",
            "--reason", "Dependency resolved",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "Blocker resolved" in result.output

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"
        assert runstate["blocked_items"] == []

    def test_fails_if_not_blocked(self, setup_product_with_runstate):
        """unblock should fail if not in blocked state."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["current_phase"] = "planning"
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "unblock",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 1

    def test_retry_option(self, setup_product_with_runstate):
        """unblock with --retry should keep same task."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["current_phase"] = "blocked"
        runstate["active_task"] = "Task 1"
        runstate["blocked_items"] = [{"reason": "API down"}]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "unblock",
            "--project", "test-product",
            "--retry",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert "Will retry same task" in result.output

    def test_alternative_option(self, setup_product_with_runstate):
        """unblock with --alternative should change task."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [{"reason": "API down"}]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "unblock",
            "--project", "test-product",
            "--alternative", "Task 2",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert "Will try alternative: Task 2" in result.output

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["active_task"] == "Task 2"

    def test_fails_without_runstate(self, temp_dir):
        """unblock should fail if no RunState."""
        result = runner.invoke(app, [
            "unblock",
            "--project", "nonexistent",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output


class TestResumeHandleFailed:
    """Tests for resume-next-day handle-failed command."""

    def test_sets_blocked_by_default(self, setup_product_with_runstate):
        """handle-failed should set state to blocked."""
        result = runner.invoke(app, [
            "handle-failed",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "State set to blocked" in result.output

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "blocked"

    def test_escalate_sets_reviewing(self, setup_product_with_runstate):
        """handle-failed with --escalate should set reviewing."""
        result = runner.invoke(app, [
            "handle-failed",
            "--project", "test-product",
            "--escalate",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "Escalated to decision needed" in result.output

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "reviewing"
        assert len(runstate["decisions_needed"]) >= 1

    def test_abandon_moves_to_next(self, setup_product_with_runstate):
        """handle-failed with --abandon should move to next task."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["task_queue"] = ["Task 1", "Task 2"]
        runstate["active_task"] = "Task 1"
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "handle-failed",
            "--project", "test-product",
            "--abandon",
            "--path", str(setup_product_with_runstate.parent),
        ])

        assert result.exit_code == 0
        assert "Task abandoned" in result.output

        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"

    def test_fails_without_runstate(self, temp_dir):
        """handle-failed should fail if no RunState."""
        result = runner.invoke(app, [
            "handle-failed",
            "--project", "nonexistent",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output


class TestDecisionPackAlignment:
    """Tests for Feature 034 - Decision pack alignment in resume-next-day."""

    def test_continue_loop_with_healthy_review_pack(self, setup_product_with_runstate):
        """continue_loop should show prior context from healthy review pack."""
        store = StateStore(setup_product_with_runstate)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "project_id": "test-product",
            "feature_id": "feature-001",
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
                "health_status": "healthy",
                "initialization_mode": "direct",
                "current_phase": "reviewing",
                "recommended_action": "Continue execution",
                "suggested_command": "asyncdev plan-day create",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "Prior Night Context" in result.output
        assert "HEALTHY" in result.output

    def test_continue_loop_with_attention_needed_pack(self, setup_product_with_runstate):
        """continue_loop should show recovery guidance from attention-needed pack."""
        store = StateStore(setup_product_with_runstate)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "project_id": "test-product",
            "doctor_assessment": {
                "doctor_status": "ATTENTION_NEEDED",
                "health_status": "warning",
                "initialization_mode": "direct",
                "recommended_action": "Re-check initialization",
                "suggested_command": "asyncdev doctor",
                "recovery_summary": {
                    "likely_cause": "Contract mismatch",
                    "recovery_steps": ["Check starter-pack", "Rerun verification"],
                },
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "ATTENTION_NEEDED" in result.output
        assert "Prior Recovery" in result.output or "Recovery" in result.output

    def test_continue_loop_with_blocked_pack(self, setup_product_with_runstate):
        """continue_loop should show blocked context from blocked pack."""
        store = StateStore(setup_product_with_runstate)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "project_id": "test-product",
            "doctor_assessment": {
                "doctor_status": "BLOCKED",
                "health_status": "blocked",
                "recommended_action": "Resolve blockers",
                "suggested_command": "asyncdev resume-next-day unblock",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "BLOCKED" in result.output

    def test_continue_loop_with_closeout_reminder(self, setup_product_with_runstate):
        """continue_loop should show closeout reminder when applicable."""
        store = StateStore(setup_product_with_runstate)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "project_id": "test-product",
            "doctor_assessment": {
                "doctor_status": "COMPLETED_PENDING_CLOSEOUT",
                "health_status": "healthy",
                "recommended_action": "Archive completed feature",
                "closeout_reminder": {
                    "status": "Feature complete, pending archive",
                    "action": "Archive or start new feature",
                },
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "Closeout" in result.output or "COMPLETED" in result.output

    def test_continue_loop_without_review_pack(self, setup_product_with_runstate):
        """continue_loop should work gracefully without review pack."""
        store = StateStore(setup_product_with_runstate)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = []
        store.save_runstate(runstate)
        
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "Resume Summary" in result.output or "Ready to continue" in result.output

    def test_continue_loop_with_stale_pack(self, setup_product_with_runstate):
        """continue_loop should warn when review pack is stale."""
        store = StateStore(setup_product_with_runstate)
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        review_pack = {
            "date": yesterday,
            "project_id": "test-product",
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
                "recommended_action": "Continue",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "outdated" in result.output.lower() or "stale" in result.output.lower()

    def test_status_with_review_pack(self, setup_product_with_runstate):
        """status should show prior review summary."""
        store = StateStore(setup_product_with_runstate)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "project_id": "test-product",
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
                "recommended_action": "Continue execution",
                "suggested_command": "asyncdev plan-day",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "status",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "Prior Review" in result.output or "HEALTHY" in result.output

    def test_status_without_review_pack(self, setup_product_with_runstate):
        """status should work without review pack."""
        result = runner.invoke(app, [
            "status",
            "--project", "test-product",
            "--path", str(setup_product_with_runstate.parent),
        ])
        
        assert result.exit_code == 0
        assert "Phase" in result.output


class TestDecisionPackHelpers:
    """Tests for decision pack loading helpers."""

    def test_load_latest_review_pack_returns_none_when_no_reviews(self, temp_dir):
        """_load_latest_review_pack returns None when no reviews directory."""
        from cli.commands.resume_next_day import _load_latest_review_pack
        
        project_path = temp_dir / "no-reviews"
        project_path.mkdir()
        
        result = _load_latest_review_pack(project_path)
        assert result is None

    def test_load_latest_review_pack_returns_pack_when_exists(self, setup_product_with_runstate):
        """_load_latest_review_pack returns pack when valid review exists."""
        from cli.commands.resume_next_day import _load_latest_review_pack
        
        store = StateStore(setup_product_with_runstate)
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {"doctor_status": "HEALTHY"},
        }
        store.save_daily_review_pack(review_pack)
        
        result = _load_latest_review_pack(setup_product_with_runstate)
        assert result is not None
        assert result.get("doctor_assessment") is not None

    def test_extract_continuation_context_extract_key_fields(self, setup_product_with_runstate):
        """_extract_continuation_context extracts key continuation fields."""
        from cli.commands.resume_next_day import _extract_continuation_context
        
        review_pack = {
            "date": "2026-04-13",
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
                "recommended_action": "Continue",
                "suggested_command": "asyncdev plan-day",
            },
            "tomorrow_plan": "Execute next task",
        }
        
        context = _extract_continuation_context(review_pack)
        
        assert context.get("prior_doctor_status") == "HEALTHY"
        assert context.get("prior_recommended_action") == "Continue"
        assert context.get("prior_suggested_command") == "asyncdev plan-day"

    def test_extract_continuation_context_includes_recovery_when_present(self):
        """_extract_continuation_context includes recovery_summary when present."""
        from cli.commands.resume_next_day import _extract_continuation_context
        
        review_pack = {
            "date": "2026-04-13",
            "doctor_assessment": {
                "doctor_status": "ATTENTION_NEEDED",
                "recovery_summary": {
                    "likely_cause": "Contract mismatch",
                    "recovery_steps": ["Step 1", "Step 2"],
                },
            },
        }
        
        context = _extract_continuation_context(review_pack)
        
        assert context.get("prior_recovery_summary") is not None
        assert context["prior_recovery_summary"].get("likely_cause") == "Contract mismatch"

    def test_extract_continuation_context_includes_feedback_when_present(self):
        """_extract_continuation_context includes feedback_handoff when present."""
        from cli.commands.resume_next_day import _extract_continuation_context
        
        review_pack = {
            "date": "2026-04-13",
            "doctor_assessment": {
                "doctor_status": "ATTENTION_NEEDED",
                "feedback_handoff": {
                    "suggestion": "Capture as workflow feedback",
                    "reason": "Verification failure",
                },
            },
        }
        
        context = _extract_continuation_context(review_pack)
        
        assert context.get("prior_feedback_handoff") is not None