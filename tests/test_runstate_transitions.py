"""Tests for RunState phase transitions."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from runtime.state_store import StateStore, update_runstate_from_result


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


class TestPlanningToExecuting:
    """Tests for planning → executing transition."""

    def test_plan_day_sets_executing_phase(self, setup_product):
        """plan-day create should transition from planning to executing."""
        from cli.commands.plan_day import app as plan_app
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"

        result = runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "executing"

    def test_plan_day_updates_active_task(self, setup_product):
        """plan-day create should set active_task."""
        from cli.commands.plan_day import app as plan_app
        
        runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature X",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["active_task"] == "Implement feature X"


class TestExecutingToReviewing:
    """Tests for executing → reviewing transition."""

    def test_review_night_sets_reviewing_phase(self, setup_product):
        """review-night generate should transition to reviewing."""
        from cli.commands.plan_day import app as plan_app
        from cli.commands.review_night import app as review_app
        
        runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "Implement feature",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "executing"

        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "success",
            "completed_items": ["Done"],
            "artifacts_created": [],
            "verification_result": {"passed": 1, "failed": 0},
            "issues_found": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Continue",
        }
        store.save_execution_result(execution_result)

        result = runner.invoke(review_app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "reviewing"


class TestExecutingToBlocked:
    """Tests for executing → blocked transition."""

    def test_blocked_result_sets_blocked_phase(self, setup_product):
        """blocked ExecutionResult should transition to blocked."""
        from runtime.state_store import update_runstate_from_result
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "executing"
        store.save_runstate(runstate)

        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "blocked",
            "completed_items": [],
            "blocked_reasons": [{"reason": "API unavailable"}],
            "decisions_required": [],
            "recommended_next_step": "Wait for API",
        }

        updated = update_runstate_from_result(runstate, execution_result)

        assert updated["current_phase"] == "blocked"
        assert len(updated["blocked_items"]) >= 1

    def test_blocked_result_preserves_blocked_items(self, setup_product):
        """blocked result should add to blocked_items."""
        from runtime.state_store import update_runstate_from_result
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "executing"
        runstate["blocked_items"] = []
        store.save_runstate(runstate)

        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "blocked",
            "blocked_reasons": [
                {"reason": "Dependency missing", "impact": "Cannot proceed"}
            ],
        }

        updated = update_runstate_from_result(runstate, execution_result)

        assert len(updated["blocked_items"]) == 1


class TestBlockedToPlanning:
    """Tests for blocked → planning transition."""

    def test_unblock_sets_planning_phase(self, setup_product):
        """resume-next-day unblock should transition to planning."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [{"reason": "Dependency missing"}]
        store.save_runstate(runstate)

        result = runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--reason", "Dependency resolved",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"
        assert runstate["blocked_items"] == []

    def test_unblock_clears_blocked_items(self, setup_product):
        """unblock should clear blocked_items list."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [
            {"reason": "Issue 1"},
            {"reason": "Issue 2"},
        ]
        store.save_runstate(runstate)

        runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["blocked_items"] == []


class TestReviewingToPlanning:
    """Tests for reviewing → planning transition."""

    def test_continue_loop_sets_planning_phase(self, setup_product):
        """resume-next-day continue-loop should transition to planning."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "reviewing"
        runstate["decisions_needed"] = []
        store.save_runstate(runstate)

        result = runner.invoke(resume_app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product.parent),
        ])

        assert result.exit_code == 0
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"

    def test_continue_loop_sets_next_recommended_action(self, setup_product):
        """continue-loop should set next_recommended_action."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "reviewing"
        runstate["task_queue"] = ["Task A", "Task B"]
        runstate["decisions_needed"] = []
        store.save_runstate(runstate)

        runner.invoke(resume_app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product.parent),
        ])

        store = StateStore(setup_product)
        runstate = store.load_runstate()
        assert runstate["next_recommended_action"] == "Execute: Task A"


class TestUpdateRunstateFromResult:
    """Tests for update_runstate_from_result function."""

    def test_success_result_sets_reviewing(self, setup_product):
        """success status should set phase to reviewing."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "executing"
        
        execution_result = {
            "execution_id": "exec-test",
            "status": "success",
            "completed_items": ["Item 1"],
            "recommended_next_step": "Next task",
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert updated["current_phase"] == "reviewing"

    def test_partial_result_sets_reviewing(self, setup_product):
        """partial status should set phase to reviewing."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "executing"
        
        execution_result = {
            "execution_id": "exec-test",
            "status": "partial",
            "completed_items": ["Item 1"],
            "recommended_next_step": "Continue",
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert updated["current_phase"] == "reviewing"

    def test_failed_result_stays_executing(self, setup_product):
        """failed status should stay in executing."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["current_phase"] = "executing"
        
        execution_result = {
            "execution_id": "exec-test",
            "status": "failed",
            "recommended_next_step": "Retry",
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert updated["current_phase"] == "executing"

    def test_accumulates_completed_outputs(self, setup_product):
        """should accumulate completed_items into completed_outputs."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["completed_outputs"] = ["Previous item"]
        
        execution_result = {
            "execution_id": "exec-test",
            "status": "success",
            "completed_items": ["New item"],
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert "Previous item" in updated["completed_outputs"]
        assert "New item" in updated["completed_outputs"]

    def test_accumulates_decisions_needed(self, setup_product):
        """should accumulate decisions_required into decisions_needed."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["decisions_needed"] = []
        
        execution_result = {
            "execution_id": "exec-test",
            "status": "blocked",
            "decisions_required": [
                {"decision": "Choose approach", "options": ["A", "B"]}
            ],
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert len(updated["decisions_needed"]) == 1
        assert updated["decisions_needed"][0]["decision"] == "Choose approach"

    def test_sets_last_action(self, setup_product):
        """should update last_action field."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        
        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "success",
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert "exec-20240101-001" in updated["last_action"]

    def test_sets_updated_at(self, setup_product):
        """should set updated_at timestamp."""
        store = StateStore(setup_product)
        runstate = store.load_runstate()
        runstate["updated_at"] = ""
        
        execution_result = {
            "execution_id": "exec-test",
            "status": "success",
        }

        updated = update_runstate_from_result(runstate, execution_result)
        assert updated["updated_at"] != ""


class TestPhaseTransitionSequence:
    """Tests for full phase transition sequence."""

    def test_full_day_loop_sequence(self, setup_product):
        """Test complete day loop: planning → executing → reviewing → planning."""
        from cli.commands.plan_day import app as plan_app
        from cli.commands.review_night import app as review_app
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(setup_product)
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "planning"

        runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "Task 1",
            "--path", str(setup_product.parent),
        ])
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "executing"

        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "success",
            "completed_items": ["Task 1 done"],
            "artifacts_created": [],
            "verification_result": {"passed": 1, "failed": 0},
            "issues_found": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Continue",
        }
        store.save_execution_result(execution_result)

        runner.invoke(review_app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_product.parent),
        ])
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "reviewing"

        runner.invoke(resume_app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "approve",
            "--path", str(setup_product.parent),
        ])
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "planning"

    def test_blocked_loop_sequence(self, setup_product):
        """Test blocked sequence: executing → blocked → planning."""
        from cli.commands.plan_day import app as plan_app
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(setup_product)
        
        runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "Task 1",
            "--path", str(setup_product.parent),
        ])
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "executing"

        runstate = store.load_runstate()
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [{"reason": "API down"}]
        store.save_runstate(runstate)
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "blocked"

        runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--reason", "API restored",
            "--path", str(setup_product.parent),
        ])
        
        phase = store.load_runstate()["current_phase"]
        assert phase == "planning"