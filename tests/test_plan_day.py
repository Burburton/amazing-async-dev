"""Tests for asyncdev plan-day command."""

import pytest
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