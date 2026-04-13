"""Tests for asyncdev plan-day command."""

import pytest
from datetime import datetime
from pathlib import Path
import yaml
from typer.testing import CliRunner
from cli.commands.plan_day import app
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


class TestPlanDayCreate:
    """Tests for plan-day create command."""

    def test_creates_execution_pack_with_task(self, setup_product):
        """plan-day create should generate ExecutionPack from task."""
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        assert "ExecutionPack created" in result.output

    def test_creates_execution_pack_file(self, setup_product):
        """plan-day create should save ExecutionPack file."""
        runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        assert len(packs) >= 1

    def test_updates_phase_to_executing(self, setup_product):
        """plan-day create should set phase to executing."""
        runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        runstate = store.load_runstate()

        assert runstate["current_phase"] == "executing"

    def test_dry_run_does_not_save(self, setup_product):
        """plan-day create with dry-run should not save."""
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--dry-run",
            "--path", str(setup_product.parent),
        ])

        assert "Dry run - not saving" in result.output

        store = StateStore(setup_product)
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        assert len(packs) == 0

    def test_fails_without_task_and_empty_queue(self, temp_dir):
        """plan-day create should fail if no task and empty queue."""
        from cli.commands.new_product import app as new_product_app
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        runstate["task_queue"] = []
        runstate["active_task"] = ""
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "No tasks in queue" in result.output

    def test_execution_pack_has_correct_fields(self, setup_product):
        """plan-day create should generate ExecutionPack with required fields."""
        runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        
        pack = store.load_execution_pack(packs[0].stem)
        
        assert pack["execution_id"] is not None
        assert pack["feature_id"] is not None
        assert pack["task_id"] == "Implement feature X"
        assert pack["goal"] is not None
        assert pack["task_scope"] is not None
        assert pack["deliverables"] is not None
        assert pack["verification_steps"] is not None

    def test_uses_existing_task_queue(self, setup_product):
        """plan-day create should use existing task_queue if no --task."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["task_queue"] = ["Task 1", "Task 2"]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["active_task"] == "Task 1"


class TestPlanDayShow:
    """Tests for plan-day show command."""

    def test_shows_runstate_fields(self, setup_product):
        """plan-day show should display RunState fields."""
        result = runner.invoke(app, [
            "show",
            "--project", "test-product",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        assert "project_id" in result.output
        assert "current_phase" in result.output

    def test_shows_no_runstate_message(self, temp_dir):
        """plan-day show should handle missing RunState."""
        result = runner.invoke(app, [
            "show",
            "--project", "nonexistent",
            "--path", str(temp_dir),
        ])

        assert "No RunState found" in result.output

    def test_displays_task_queue_count(self, setup_product):
        """plan-day show should show task queue count."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["task_queue"] = ["Task A", "Task B", "Task C"]
        store.save_runstate(runstate)

        result = runner.invoke(app, [
            "show",
            "--project", "test-product",
            "--path", str(setup_product.parent),
        ])

        assert "task_queue" in result.output


class TestPlanDayResumeContextAlignment:
    """Tests for Feature 035 - Resume-context-aware planning."""

    def test_plan_with_healthy_resume_context(self, setup_product):
        """plan-day should infer continue_work mode from healthy resume context."""
        store = StateStore(setup_product)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
                "recommended_action": "Continue execution",
                "suggested_command": "asyncdev plan-day create",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--path", str(setup_product.parent),
        ])
        
        assert result.exit_code == 0
        assert "Resume Context" in result.output or "planning_mode" in result.output

    def test_plan_with_blocked_resume_context(self, setup_product):
        """plan-day should infer blocked_waiting mode from blocked resume context."""
        store = StateStore(setup_product)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {
                "doctor_status": "BLOCKED",
                "recommended_action": "Resolve blockers",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Resume work",
            "--path", str(setup_product.parent),
        ])
        
        assert result.exit_code == 0
        assert "blocked_waiting" in result.output or "BLOCKED" in result.output

    def test_plan_with_closeout_resume_context(self, setup_product):
        """plan-day should infer closeout_first mode from closeout resume context."""
        store = StateStore(setup_product)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {
                "doctor_status": "COMPLETED_PENDING_CLOSEOUT",
                "closeout_reminder": {
                    "status": "Feature complete, pending archive",
                    "action": "Archive or start new feature",
                },
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Archive feature",
            "--path", str(setup_product.parent),
        ])
        
        assert result.exit_code == 0
        assert "closeout_first" in result.output or "closeout" in result.output.lower()

    def test_plan_with_recovery_resume_context(self, setup_product):
        """plan-day should infer recover_and_continue mode from recovery resume context."""
        store = StateStore(setup_product)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {
                "doctor_status": "ATTENTION_NEEDED",
                "recovery_summary": {
                    "likely_cause": "Contract mismatch",
                    "recovery_steps": ["Check starter-pack", "Rerun verification"],
                },
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Fix verification issue",
            "--path", str(setup_product.parent),
        ])
        
        assert result.exit_code == 0
        assert "recover_and_continue" in result.output or "Recovery" in result.output

    def test_plan_without_resume_context(self, setup_product):
        """plan-day should work gracefully without resume context."""
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "New task",
            "--path", str(setup_product.parent),
        ])
        
        assert result.exit_code == 0
        assert "ExecutionPack created" in result.output

    def test_plan_with_stale_resume_context(self, setup_product):
        """plan-day should handle stale resume context gracefully."""
        store = StateStore(setup_product)
        
        yesterday_date = "2026-04-12"
        review_pack = {
            "date": yesterday_date,
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
                "recommended_action": "Continue",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        result = runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Continue work",
            "--path", str(setup_product.parent),
        ])
        
        assert result.exit_code == 0
        assert "outdated" in result.output.lower() or "stale" in result.output.lower() or "ExecutionPack" in result.output

    def test_execution_pack_includes_planning_mode(self, setup_product):
        """ExecutionPack should include planning_mode when resume context exists."""
        store = StateStore(setup_product)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {
                "doctor_status": "HEALTHY",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature",
            "--path", str(setup_product.parent),
        ])
        
        store = StateStore(setup_product)
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        pack = store.load_execution_pack(packs[0].stem)
        
        assert pack.get("planning_mode") is not None

    def test_execution_pack_includes_prior_doctor_status(self, setup_product):
        """ExecutionPack should include prior_doctor_status when resume context exists."""
        store = StateStore(setup_product)
        
        today = datetime.now().strftime("%Y-%m-%d")
        review_pack = {
            "date": today,
            "doctor_assessment": {
                "doctor_status": "ATTENTION_NEEDED",
            },
        }
        store.save_daily_review_pack(review_pack)
        
        runner.invoke(app, [
            "create",
            "--project", "test-product",
            "--task", "Fix issue",
            "--path", str(setup_product.parent),
        ])
        
        store = StateStore(setup_product)
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        pack = store.load_execution_pack(packs[0].stem)
        
        assert pack.get("prior_doctor_status") == "ATTENTION_NEEDED"


class TestPlanningModeInference:
    """Tests for _infer_planning_mode helper."""

    def test_healthy_infers_continue_work(self):
        """HEALTHY doctor status should infer continue_work mode."""
        from cli.commands.plan_day import _infer_planning_mode
        
        resume_context = {"prior_doctor_status": "HEALTHY"}
        
        mode = _infer_planning_mode(resume_context)
        
        assert mode == "continue_work"

    def test_blocked_infers_blocked_waiting(self):
        """BLOCKED doctor status should infer blocked_waiting_for_decision mode."""
        from cli.commands.plan_day import _infer_planning_mode
        
        resume_context = {"prior_doctor_status": "BLOCKED"}
        
        mode = _infer_planning_mode(resume_context)
        
        assert mode == "blocked_waiting_for_decision"

    def test_completed_pending_closeout_infers_closeout_first(self):
        """COMPLETED_PENDING_CLOSEOUT should infer closeout_first mode."""
        from cli.commands.plan_day import _infer_planning_mode
        
        resume_context = {"prior_doctor_status": "COMPLETED_PENDING_CLOSEOUT"}
        
        mode = _infer_planning_mode(resume_context)
        
        assert mode == "closeout_first"

    def test_recovery_summary_infers_recover_and_continue(self):
        """prior_recovery_summary should infer recover_and_continue mode."""
        from cli.commands.plan_day import _infer_planning_mode
        
        resume_context = {
            "prior_doctor_status": "ATTENTION_NEEDED",
            "prior_recovery_summary": {"likely_cause": "test"},
        }
        
        mode = _infer_planning_mode(resume_context)
        
        assert mode == "recover_and_continue"

    def test_default_is_continue_work(self):
        """Empty context should default to continue_work mode."""
        from cli.commands.plan_day import _infer_planning_mode
        
        resume_context = {}
        
        mode = _infer_planning_mode(resume_context)
        
        assert mode == "continue_work"


class TestPlanningRationale:
    """Tests for _get_planning_rationale helper."""

    def test_rationale_includes_mode(self):
        """Rationale should include the planning mode."""
        from cli.commands.plan_day import _get_planning_rationale
        
        resume_context = {"prior_doctor_status": "HEALTHY"}
        
        rationale = _get_planning_rationale("continue_work", resume_context)
        
        assert rationale.get("mode") == "continue_work"

    def test_rationale_includes_doctor_status(self):
        """Rationale should include prior doctor status as reason."""
        from cli.commands.plan_day import _get_planning_rationale
        
        resume_context = {"prior_doctor_status": "BLOCKED"}
        
        rationale = _get_planning_rationale("blocked_waiting_for_decision", resume_context)
        
        assert any("BLOCKED" in r for r in rationale.get("reasons", []))

    def test_rationale_includes_prior_recommendation(self):
        """Rationale should include prior recommendation when present."""
        from cli.commands.plan_day import _get_planning_rationale
        
        resume_context = {
            "prior_doctor_status": "HEALTHY",
            "prior_recommended_action": "Continue execution",
        }
        
        rationale = _get_planning_rationale("continue_work", resume_context)
        
        assert rationale.get("prior_recommendation") == "Continue execution"

    def test_rationale_includes_stale_warning(self):
        """Rationale should include warning when context is stale."""
        from cli.commands.plan_day import _get_planning_rationale
        
        resume_context = {"prior_doctor_status": "HEALTHY", "is_stale": True}
        
        rationale = _get_planning_rationale("continue_work", resume_context)
        
        assert rationale.get("warnings") is not None