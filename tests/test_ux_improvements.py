"""Tests for Feature 012 - UX/Ergonomics Improvements."""

import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner

from cli.asyncdev import app as main_app
from cli.utils.path_formatter import get_relative_path, format_path
from cli.utils.output_formatter import print_next_step, print_success_panel


runner = CliRunner()


class TestPathFormatter:

    def test_get_relative_path_under_root(self):
        """Relative path should be computed correctly."""
        root = Path("/workspace/project")
        path = Path("/workspace/project/subdir/file.txt")
        
        relative = get_relative_path(path, root)
        assert relative.replace("\\", "/") == "subdir/file.txt"

    def test_get_relative_path_not_under_root(self):
        """Path not under root should return absolute."""
        root = Path("/workspace/project")
        path = Path("/other/location/file.txt")
        
        relative = get_relative_path(path, root)
        assert relative == str(path)

    def test_format_path_with_root_hint(self):
        """Format path should show root hint."""
        root = Path("/workspace")
        path = Path("/workspace/project/file.txt")
        
        formatted = format_path(path, root, show_root_hint=True)
        assert "project" in formatted and "file.txt" in formatted
        assert "root:" in formatted


class TestOutputFormatter:

    def test_print_next_step_shows_command(self, tmp_path):
        """print_next_step should display command."""
        from rich.console import Console
        
        console = Console()
        print_next_step(
            action="Test action",
            command="asyncdev test",
        )

    def test_print_success_panel_shows_message(self, tmp_path):
        """print_success_panel should display message."""
        print_success_panel(
            message="Test message",
            title="Test Title",
        )


class TestEnhancedStatusCommand:

    def test_status_help_shows_new_options(self):
        """status --help should show --all and --feature options."""
        result = runner.invoke(main_app, ["status", "--help"])
        
        assert result.exit_code == 0
        assert "--all" in result.output
        assert "--feature" in result.output

    def test_status_default_shows_current_runstate(self, setup_test_project):
        """status without options should show current RunState."""
        result = runner.invoke(main_app, [
            "status",
            "--path", str(setup_test_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "RunState" in result.output or "Phase" in result.output

    def test_status_all_shows_products_summary(self, setup_test_project):
        """status --all should show all products."""
        result = runner.invoke(main_app, [
            "status",
            "--all",
            "--path", str(setup_test_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "test-product" in result.output or "Products" in result.output

    def test_status_feature_requires_project(self):
        """status --feature without --project should error."""
        result = runner.invoke(main_app, [
            "status",
            "--feature", "001-test",
        ])
        
        assert result.exit_code == 1
        assert "--project required" in result.output


class TestPathDisplayInCommands:

    def test_plan_day_shows_relative_paths(self, setup_test_project):
        """plan-day should show relative paths with root hint."""
        from cli.commands.plan_day import app as plan_app
        
        result = runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "test-task",
            "--path", str(setup_test_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "root:" in result.output or "Plan-Day" in result.output

    def test_complete_feature_shows_paths(self, setup_test_project):
        """complete-feature should show paths."""
        from cli.commands.complete_feature import app as complete_app
        
        result = runner.invoke(complete_app, [
            "mark",
            "--project", "test-product",
            "--path", str(setup_test_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "Complete-Feature" in result.output


class TestNextStepPanel:

    def test_next_step_shows_after_plan_day(self, setup_test_project):
        """plan-day should show next-step panel."""
        from cli.commands.plan_day import app as plan_app
        
        result = runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--task", "test-task",
            "--path", str(setup_test_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "Next Step" in result.output

    def test_next_step_shows_after_review_night(self, setup_with_execution_result):
        """review-night should show next-step panel."""
        from cli.commands.review_night import app as review_app
        
        result = runner.invoke(review_app, [
            "generate",
            "--project", "test-product",
            "--path", str(setup_with_execution_result.parent),
        ])
        
        assert result.exit_code == 0
        assert "resume-next-day" in result.output or "Next Step" in result.output


import pytest


@pytest.fixture
def setup_test_project():
    """Create test project with RunState."""
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "test-product"
    project_dir.mkdir()
    
    (project_dir / "execution-packs").mkdir()
    (project_dir / "execution-results").mkdir()
    (project_dir / "reviews").mkdir()
    (project_dir / "features").mkdir()
    
    runstate_content = """# RunState

```yaml
project_id: test-product
feature_id: 001-test
current_phase: planning
active_task: ""
task_queue: ["test-task"]
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Initialized
updated_at: "2024-01-01"
```
"""
    (project_dir / "runstate.md").write_text(runstate_content)
    
    yield project_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def setup_with_execution_result():
    """Create test project with execution result."""
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "test-product"
    project_dir.mkdir()
    
    (project_dir / "execution-packs").mkdir()
    (project_dir / "execution-results").mkdir()
    (project_dir / "reviews").mkdir()
    (project_dir / "features").mkdir()
    
    runstate_content = """# RunState

```yaml
project_id: test-product
feature_id: 001-test
current_phase: reviewing
active_task: ""
task_queue: []
completed_outputs: ["test-output"]
blocked_items: []
decisions_needed: []
last_action: Execution completed
updated_at: "2024-01-01"
```
"""
    (project_dir / "runstate.md").write_text(runstate_content)
    
    exec_result_content = """# ExecutionResult

```yaml
execution_id: exec-20240101-001
status: success
completed_items: ["test-output"]
artifacts_created: []
```
"""
    (project_dir / "execution-results" / "exec-20240101-001.md").write_text(exec_result_content)
    
    yield project_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)