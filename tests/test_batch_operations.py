"""Tests for Feature 018 - Limited Batch Operations."""

from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner

import yaml


runner = CliRunner()


class TestBatchStatus:
    """Test batch status inspection."""

    def setup_method(self):
        """Create test project structure."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.projects_path = self.temp_dir / "projects"
        self.projects_path.mkdir(parents=True)
        
        self.project_path = self.projects_path / "test-product"
        self.project_path.mkdir()
        
        self.features_path = self.project_path / "features"
        self.features_path.mkdir()
        
        self.archive_path = self.project_path / "archive"
        self.archive_path.mkdir()
        
        self.runtime_path = self.project_path / ".runtime"
        self.runtime_path.mkdir()
        
        self.features_path.joinpath("001-feature-a").mkdir()
        self.features_path.joinpath("001-feature-a").joinpath("feature-spec.yaml").write_text(
            yaml.dump({"feature_id": "001-feature-a", "name": "Feature A", "status": "completed"})
        )
        
        self.features_path.joinpath("002-feature-b").mkdir()
        self.features_path.joinpath("002-feature-b").joinpath("feature-spec.yaml").write_text(
            yaml.dump({"feature_id": "002-feature-b", "name": "Feature B", "status": "planning"})
        )
        
        self.archive_path.joinpath("001-feature-a").mkdir()
        self.archive_path.joinpath("001-feature-a").joinpath("archive-pack.yaml").write_text(
            yaml.dump({"feature_id": "001-feature-a", "product_id": "test-product", "title": "Feature A"})
        )
        
        runstate_content = """# RunState
```yaml
project_id: test-product
feature_id: 002-feature-b
current_phase: planning
active_task: test-task
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Test
updated_at: '2024-01-01T10:00:00'
```
"""
        self.project_path.joinpath("runstate.md").write_text(runstate_content)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.temp_dir)

    def test_batch_status_requires_project(self):
        """--all-features should require --project."""
        from cli.asyncdev import app
        
        result = runner.invoke(app, ["status", "--all-features"])
        
        assert result.exit_code != 0
        assert "project required" in result.output.lower() or "required" in result.output.lower()

    def test_batch_status_shows_all_features(self):
        """--all-features should list all features in project."""
        from cli.asyncdev import app
        
        result = runner.invoke(app, ["status", "--all-features", "--project", "test-product", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "002-feature-b" in result.output or "Feature B" in result.output


class TestBatchBackfill:
    """Test batch backfill command."""

    def setup_method(self):
        """Create test project with multiple unarchived features."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.projects_path = self.temp_dir / "projects"
        self.projects_path.mkdir(parents=True)
        
        self.project_path = self.projects_path / "batch-test"
        self.project_path.mkdir()
        
        self.features_path = self.project_path / "features"
        self.features_path.mkdir()
        
        self.archive_path = self.project_path / "archive"
        self.archive_path.mkdir()
        
        for i in range(3):
            feature_id = f"00{i+1}-test-feature"
            feature_dir = self.features_path / feature_id
            feature_dir.mkdir()
            feature_dir.joinpath("feature-spec.yaml").write_text(
                yaml.dump({"feature_id": feature_id, "name": f"Test Feature {i+1}", "status": "completed"})
            )

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_batch_requires_all_flag(self):
        """batch should require --all flag for safety."""
        from cli.commands.backfill import app
        
        result = runner.invoke(app, ["batch", "--project", "batch-test", "--path", str(self.projects_path)])
        
        assert result.exit_code != 0
        assert "all" in result.output.lower() or "required" in result.output.lower()

    def test_batch_dry_run_shows_preview(self):
        """--dry-run should show preview without saving."""
        from cli.commands.backfill import app
        
        result = runner.invoke(app, ["batch", "--project", "batch-test", "--dry-run", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "dry run" in result.output.lower() or "preview" in result.output.lower()

    def test_batch_processes_eligible_features(self):
        """batch --all should process all eligible features."""
        from cli.commands.backfill import app
        
        result = runner.invoke(app, ["batch", "--project", "batch-test", "--all", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "backfilled" in result.output.lower()

    def test_batch_respects_limit(self):
        """--limit should cap batch size."""
        from cli.commands.backfill import app
        
        result = runner.invoke(app, ["batch", "--project", "batch-test", "--all", "--limit", "1", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        
        archived_count = len([f for f in self.archive_path.iterdir() if f.is_dir()])
        assert archived_count <= 1


class TestBatchSummary:
    """Test batch summary command."""

    def setup_method(self):
        """Create multiple test projects."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.projects_path = self.temp_dir / "projects"
        self.projects_path.mkdir(parents=True)
        
        for project_name in ["project-a", "project-b"]:
            project_path = self.projects_path / project_name
            project_path.mkdir()
            
            features_path = project_path / "features"
            features_path.mkdir()
            features_path.joinpath("001-test").mkdir()
            
            archive_path = project_path / "archive"
            archive_path.mkdir()
            
            runstate_content = """# RunState
```yaml
project_id: {}
feature_id: 001-test
current_phase: planning
active_task: test
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Init
updated_at: '2024-01-01T10:00:00'
```
""".format(project_name)
            project_path.joinpath("runstate.md").write_text(runstate_content)

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_all_projects_shows_portfolio_view(self):
        """all-projects should aggregate across all projects."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["all-projects", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "project" in result.output.lower()
        assert "phase" in result.output.lower()

    def test_all_projects_counts_totals(self):
        """all-projects should show aggregated metrics."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["all-projects", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "projects tracked" in result.output.lower() or "total" in result.output.lower()


class TestBatchArchiveList:
    """Test that archive list filters work correctly (Feature 014 + 018)."""

    def setup_method(self):
        """Create test archives with patterns and lessons."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.projects_path = self.temp_dir / "projects"
        self.projects_path.mkdir(parents=True)
        
        self.project_path = self.projects_path / "archive-test"
        self.project_path.mkdir()
        
        self.archive_path = self.project_path / "archive"
        self.archive_path.mkdir()
        
        feature_with_patterns = self.archive_path / "001-with-patterns"
        feature_with_patterns.mkdir()
        feature_with_patterns.joinpath("archive-pack.yaml").write_text(
            yaml.dump({
                "feature_id": "001-with-patterns",
                "product_id": "archive-test",
                "title": "Feature with Patterns",
                "reusable_patterns": [{"pattern": "Test pattern", "applicability": "Testing"}],
                "lessons_learned": [],
            })
        )
        
        feature_with_lessons = self.archive_path / "002-with-lessons"
        feature_with_lessons.mkdir()
        feature_with_lessons.joinpath("archive-pack.yaml").write_text(
            yaml.dump({
                "feature_id": "002-with-lessons",
                "product_id": "archive-test",
                "title": "Feature with Lessons",
                "reusable_patterns": [],
                "lessons_learned": [{"lesson": "Test lesson", "context": "Testing"}],
            })
        )

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_has_patterns_filter(self):
        """--has-patterns should filter archives with patterns."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, ["list", "--product", "archive-test", "--has-patterns", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "with-patt" in result.output or "Feature with Patterns" in result.output
        assert "with-less" not in result.output

    def test_has_lessons_filter(self):
        """--has-lessons should filter archives with lessons."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, ["list", "--product", "archive-test", "--has-lessons", "--path", str(self.projects_path)])
        
        assert result.exit_code == 0
        assert "with-less" in result.output or "Feature with Lessons" in result.output
        assert "with-patt" not in result.output