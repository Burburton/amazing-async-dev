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


class TestEnrichedReviewPack:
    """Tests for Feature 033 - Enriched Review Pack with Doctor signals."""

    def test_healthy_workspace_enriched_pack(self, setup_with_execution_result):
        """Enriched pack should include doctor assessment."""
        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert result.exit_code == 0
        assert "Doctor Assessment" in result.output
        assert "Status:" in result.output

    def test_enriched_pack_includes_initialization_mode(self, setup_with_execution_result):
        """Enriched pack should show initialization mode."""
        result = runner.invoke(app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "exec-20240101-001",
            "--path", str(setup_with_execution_result.parent),
        ])

        assert result.exit_code == 0
        assert "Initialization" in result.output or "initialization_mode" in result.output.lower()

    def test_blocked_workspace_enriched_pack(self, temp_dir):
        """Enriched pack should show blocked status clearly."""
        from cli.commands.new_product import app as new_product_app
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "blocked-product",
            "--name", "Blocked Product",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "blocked-product")
        runstate = store.load_runstate()
        runstate["decisions_needed"] = [{"decision": "test", "options": ["A", "B"]}]
        store.save_runstate(runstate)
        
        execution_result = {
            "execution_id": "exec-001",
            "status": "blocked",
            "completed_items": [],
            "decisions_required": [{"decision": "Choose", "options": ["A", "B"], "recommendation": "A"}],
            "recommended_next_step": "Resolve blocker",
        }
        store.save_execution_result(execution_result)
        
        result = runner.invoke(app, [
            "generate",
            "--project", "blocked-product",
            "--execution-id", "exec-001",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 0
        assert "BLOCKED" in result.output or "blocked" in result.output.lower()

    def test_attention_needed_with_recovery(self, temp_dir):
        """Enriched pack should include recovery guidance for ATTENTION_NEEDED."""
        from cli.commands.new_product import app as new_product_app
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "attention-product",
            "--name", "Attention Product",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "attention-product")
        
        (store.execution_results_path).mkdir(exist_ok=True)
        (store.execution_results_path / "exec-fail.md").write_text("""---
```yaml
execution_id: exec-fail
status: failed
completed_items: []
issues_found:
  - Verification mismatch
```
---
""")
        
        execution_result = {
            "execution_id": "exec-fail",
            "status": "failed",
            "completed_items": [],
            "issues_found": ["Verification failed"],
            "recommended_next_step": "Fix verification",
        }
        store.save_execution_result(execution_result)
        
        result = runner.invoke(app, [
            "generate",
            "--project", "attention-product",
            "--execution-id", "exec-fail",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 0

    def test_show_includes_doctor_assessment(self, setup_with_execution_result):
        """review-night show should display doctor assessment."""
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

        assert "Doctor Assessment" in result.output

    def test_show_includes_recommended_action(self, setup_with_execution_result):
        """review-night show should display recommended action."""
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

        assert "Recommended Action" in result.output or "recommended" in result.output.lower()


class TestEnrichedReviewPackBuilder:
    """Tests for review_pack_builder enriched functionality."""

    def test_build_daily_review_pack_with_project_path(self, temp_dir):
        """build_daily_review_pack should include doctor_assessment when project_path provided."""
        from runtime.review_pack_builder import build_daily_review_pack
        from cli.commands.new_product import app as new_product_app
        from runtime.state_store import StateStore
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "builder-test",
            "--name", "Builder Test",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "builder-test")
        
        execution_result = {
            "execution_id": "exec-001",
            "status": "success",
            "completed_items": ["Test item"],
            "recommended_next_step": "Continue",
        }
        store.save_execution_result(execution_result)
        
        runstate = store.load_runstate()
        
        review_pack = build_daily_review_pack(
            execution_result,
            runstate,
            project_path=temp_dir / "builder-test"
        )
        
        assert "doctor_assessment" in review_pack
        assert review_pack["doctor_assessment"].get("doctor_status") is not None

    def test_build_daily_review_pack_without_project_path(self, temp_dir):
        """build_daily_review_pack should work without project_path (backward compat)."""
        from runtime.review_pack_builder import build_daily_review_pack
        
        execution_result = {
            "execution_id": "exec-001",
            "status": "success",
            "completed_items": ["Test"],
            "recommended_next_step": "Next",
        }
        
        runstate = {"project_id": "test", "feature_id": "feature-001"}
        
        review_pack = build_daily_review_pack(execution_result, runstate)
        
        assert "doctor_assessment" not in review_pack
        assert "date" in review_pack

    def test_doctor_assessment_includes_recovery_for_attention_needed(self, temp_dir):
        """doctor_assessment should include recovery_summary for ATTENTION_NEEDED."""
        from runtime.review_pack_builder import build_daily_review_pack, _build_doctor_assessment
        from pathlib import Path
        
        project_path = temp_dir / "recovery-test"
        project_path.mkdir()
        
        (project_path / "execution-results").mkdir()
        (project_path / "execution-results" / "exec-fail.md").write_text("""---
```yaml
execution_id: exec-fail
status: failed
completed_items: []
issues_found:
  - Contract mismatch
```
---
""")
        
        (project_path / "runstate.md").write_text("""---
```yaml
project_id: recovery-test
feature_id: feature-001
current_phase: executing
decisions_needed: []
```
---
""")
        
        (project_path / "product-brief.yaml").write_text("product_id: recovery-test\nname: Recovery Test\n")
        
        assessment = _build_doctor_assessment(project_path)
        
        assert assessment is not None
        assert assessment.get("doctor_status") == "ATTENTION_NEEDED"
        assert "recovery_summary" in assessment

    def test_doctor_assessment_includes_feedback_handoff(self, temp_dir):
        """doctor_assessment should include feedback_handoff when applicable."""
        from runtime.review_pack_builder import _build_doctor_assessment
        from pathlib import Path
        
        project_path = temp_dir / "feedback-test"
        project_path.mkdir()
        
        (project_path / "execution-results").mkdir()
        (project_path / "execution-results" / "exec-fail.md").write_text("""---
```yaml
execution_id: exec-fail
status: failed
completed_items: []
```
---
""")
        
        (project_path / "runstate.md").write_text("""---
```yaml
project_id: feedback-test
feature_id: feature-001
current_phase: executing
decisions_needed: []
```
---
""")
        
        (project_path / "product-brief.yaml").write_text("product_id: feedback-test\nname: Feedback Test\n")
        
        assessment = _build_doctor_assessment(project_path)
        
        assert assessment is not None
        assert "feedback_handoff" in assessment
        assert assessment["feedback_handoff"].get("suggestion") is not None