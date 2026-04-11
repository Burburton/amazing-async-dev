"""Tests for asyncdev review-night command."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from cli.commands.review_night import app
from runtime.state_store import StateStore


runner = CliRunner()


@pytest.fixture
def setup_with_execution_result(temp_dir):
    """Create product, runstate, and execution result for testing."""
    from cli.commands.new_product import app as new_product_app
    
    runner.invoke(new_product_app, [
        "create",
        "--product-id", "test-product",
        "--name", "Test Product",
        "--path", str(temp_dir),
    ])
    
    store = StateStore(temp_dir / "test-product")
    runstate = store.load_runstate()
    runstate["task_queue"] = ["Task 1"]
    runstate["active_task"] = "Task 1"
    store.save_runstate(runstate)
    
    execution_result = {
        "execution_id": "exec-20240101-001",
        "status": "success",
        "completed_items": ["Implemented feature"],
        "artifacts_created": [{"name": "output.md", "path": "output.md", "type": "file"}],
        "verification_result": {"passed": 1, "failed": 0, "skipped": 0},
        "issues_found": [],
        "blocked_reasons": [],
        "decisions_required": [],
        "recommended_next_step": "Continue with next task",
        "metrics": {"files_read": 5, "files_written": 1},
    }
    store.save_execution_result(execution_result)
    
    yield temp_dir / "test-product"


class TestReviewNightGenerate:
    """Tests for review-night generate command."""

    def test_generates_review_pack(self, setup_with_execution_result):
        """review-night generate should create DailyReviewPack."""
        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert result.exit_code == 0
        assert "Review-Night Complete" in result.output or "DailyReviewPack" in result.output

    def test_saves_review_pack_file(self, setup_with_execution_result):
        """review-night generate should save review pack file."""
        runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        store = StateStore(setup_with_execution_result)
        reviews = list(store.reviews_path.glob("*-review.md"))
        assert len(reviews) >= 1

    def test_updates_phase_to_reviewing(self, setup_with_execution_result):
        """review-night generate should set phase to reviewing."""
        runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        store = StateStore(setup_with_execution_result)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "reviewing"

    def test_fails_without_runstate(self, temp_dir):
        """review-night generate should fail if no RunState."""
        result = runner.invoke(app, [
            "generate",
            "--project", "nonexistent",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output

    def test_fails_without_execution_result(self, temp_dir):
        """review-night generate should fail if no ExecutionResult."""
        from cli.commands.new_product import app as new_product_app
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "No ExecutionResult found" in result.output

    def test_dry_run_does_not_save(self, setup_with_execution_result):
        """review-night generate with dry-run should not save."""
        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--dry-run",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert "Dry run - not saving" in result.output

        store = StateStore(setup_with_execution_result)
        reviews = list(store.reviews_path.glob("*-review.md"))
        assert len(reviews) == 0

    def test_displays_decisions_needed(self, temp_dir):
        """review-night generate should show decisions if present."""
        from cli.commands.new_product import app as new_product_app
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        store = StateStore(temp_dir / "test-product")
        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "blocked",
            "completed_items": [],
            "decisions_required": [
                {"decision": "Choose approach", "options": ["A", "B"], "recommendation": "A"}
            ],
            "recommended_next_step": "",
        }
        store.save_execution_result(execution_result)

        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(temp_dir),
        ])

        assert "Decisions Needed" in result.output
        assert "Choose approach" in result.output

    def test_uses_latest_execution_result_by_default(self, setup_with_execution_result):
        """review-night generate should use latest ExecutionResult if no --execution-id."""
        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert result.exit_code == 0


class TestReviewNightShow:
    """Tests for review-night show command."""

    def test_shows_latest_review_pack(self, setup_with_execution_result):
        """review-night show should display latest DailyReviewPack."""
        runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        result = runner.invoke(app, [
            "show",
            "--project", "test-product",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert result.exit_code == 0
        assert "DailyReviewPack" in result.output

    def test_shows_no_review_message(self, temp_dir):
        """review-night show should handle missing review pack."""
        from cli.commands.new_product import app as new_product_app
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        result = runner.invoke(app, [
            "show",
            "--project", "test-product",
            "--path", str(temp_dir),
        ])

        assert "No DailyReviewPack found" in result.output

    def test_displays_tomorrow_plan(self, setup_with_execution_result):
        """review-night show should show tomorrow's plan."""
        runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        result = runner.invoke(app, [
            "show",
            "--project", "test-product",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert "Tomorrow" in result.output