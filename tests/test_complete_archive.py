"""Tests for complete-feature and archive-feature commands."""

import pytest
from pathlib import Path
import yaml
from typer.testing import CliRunner
from runtime.state_store import StateStore
from runtime.archive_pack_builder import build_archive_pack


runner = CliRunner()


@pytest.fixture
def setup_completed_feature(temp_dir):
    """Create a product with a feature in completed state."""
    from cli.commands.new_product import app as new_product_app
    from cli.commands.new_feature import app as new_feature_app
    
    runner.invoke(new_product_app, [
        "create",
        "--product-id", "test-product",
        "--name", "Test Product",
        "--path", str(temp_dir),
    ])
    
    runner.invoke(new_feature_app, [
        "create",
        "--product-id", "test-product",
        "--feature-id", "001-test",
        "--name", "Test Feature",
        "--path", str(temp_dir),
    ])
    
    store = StateStore(temp_dir / "test-product")
    runstate = store.load_runstate()
    runstate["current_phase"] = "completed"
    runstate["completed_outputs"] = ["schemas/test.schema.yaml", "templates/test.template.md"]
    runstate["decisions_needed"] = []
    runstate["blocked_items"] = []
    store.save_runstate(runstate)
    
    yield temp_dir / "test-product"


class TestCompleteFeature:
    """Tests for complete-feature command."""

    def test_marks_feature_as_completed(self, temp_dir):
        """complete-feature mark should set phase to completed."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.new_feature import app as new_feature_app
        from cli.commands.complete_feature import app as complete_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])
        
        runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        runstate["blocked_items"] = []
        runstate["decisions_needed"] = []
        store.save_runstate(runstate)
        
        result = runner.invoke(complete_app, [
            "mark",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 0
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "completed"

    def test_checks_eligibility(self, temp_dir):
        """complete-feature mark should check blockers and decisions."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.new_feature import app as new_feature_app
        from cli.commands.complete_feature import app as complete_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])
        
        runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        runstate["blocked_items"] = [{"item": "API", "reason": "Down"}]
        store.save_runstate(runstate)
        
        result = runner.invoke(complete_app, [
            "mark",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_dir),
        ])
        
        assert "Warning" in result.output

    def test_force_bypasses_checks(self, temp_dir):
        """complete-feature force should bypass eligibility checks."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.new_feature import app as new_feature_app
        from cli.commands.complete_feature import app as complete_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])
        
        runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        runstate["blocked_items"] = [{"item": "API", "reason": "Down"}]
        store.save_runstate(runstate)
        
        result = runner.invoke(complete_app, [
            "force",
            "--project", "test-product",
            "--feature", "001-test",
            "--reason", "Manual override",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 0
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "completed"

    def test_status_shows_eligibility(self, temp_dir):
        """complete-feature status should show eligibility."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.complete_feature import app as complete_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])
        
        result = runner.invoke(complete_app, [
            "status",
            "--project", "test-product",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 0
        assert "Phase" in result.output


class TestArchiveFeature:
    """Tests for archive-feature command."""

    def test_creates_archive_pack(self, setup_completed_feature):
        """archive-feature create should generate ArchivePack."""
        from cli.commands.archive_feature import app as archive_app
        
        result = runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--lessons", "Small tasks work better",
            "--path", str(setup_completed_feature.parent),
        ])
        
        assert result.exit_code == 0
        assert "ArchivePack saved" in result.output

    def test_saves_archive_pack_file(self, setup_completed_feature):
        """archive-feature create should save archive-pack.yaml."""
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(setup_completed_feature.parent),
        ])
        
        archive_path = setup_completed_feature / "archive" / "001-test" / "archive-pack.yaml"
        assert archive_path.exists()

    def test_sets_phase_to_archived(self, setup_completed_feature):
        """archive-feature create should set phase to archived."""
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(setup_completed_feature.parent),
        ])
        
        store = StateStore(setup_completed_feature)
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "archived"

    def test_archive_pack_contains_required_fields(self, setup_completed_feature):
        """ArchivePack should contain all required fields."""
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(setup_completed_feature.parent),
        ])
        
        archive_path = setup_completed_feature / "archive" / "001-test" / "archive-pack.yaml"
        with open(archive_path) as f:
            archive_pack = yaml.safe_load(f)
        
        assert archive_pack["feature_id"] == "001-test"
        assert archive_pack["product_id"] == "test-product"
        assert archive_pack["final_status"] == "completed"
        assert len(archive_pack["delivered_outputs"]) >= 1
        assert len(archive_pack["lessons_learned"]) >= 1
        assert len(archive_pack["reusable_patterns"]) >= 1
        assert archive_pack["archived_at"] is not None

    def test_fails_if_not_completed(self, temp_dir):
        """archive-feature create should fail if not completed."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.new_feature import app as new_feature_app
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])
        
        runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])
        
        result = runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_dir),
        ])
        
        assert result.exit_code == 1
        assert "must be marked completed" in result.output

    def test_list_shows_archived_features(self, setup_completed_feature):
        """archive-feature list should show archived features."""
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(setup_completed_feature.parent),
        ])
        
        result = runner.invoke(archive_app, [
            "list",
            "--project", "test-product",
            "--path", str(setup_completed_feature.parent),
        ])
        
        assert result.exit_code == 0
        assert "001-test" in result.output

    def test_show_displays_archive_details(self, setup_completed_feature):
        """archive-feature show should display archive pack details."""
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--lessons", "Keep scope small",
            "--path", str(setup_completed_feature.parent),
        ])
        
        result = runner.invoke(archive_app, [
            "show",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(setup_completed_feature.parent),
        ])
        
        assert result.exit_code == 0
        assert "Lessons Learned" in result.output

    def test_dry_run_does_not_save(self, setup_completed_feature):
        """archive-feature create with dry-run should not save."""
        from cli.commands.archive_feature import app as archive_app
        
        result = runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--dry-run",
            "--path", str(setup_completed_feature.parent),
        ])
        
        assert "Dry run" in result.output
        
        archive_path = setup_completed_feature / "archive" / "001-test" / "archive-pack.yaml"
        assert not archive_path.exists()


class TestArchivePackBuilder:
    """Tests for build_archive_pack function."""

    def test_builds_archive_pack_from_runstate(self, temp_dir):
        """build_archive_pack should create ArchivePack from RunState."""
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "completed_outputs": ["schemas/test.yaml", "templates/test.md"],
            "decisions_needed": [],
            "blocked_items": [],
        }
        
        archive_pack = build_archive_pack(
            runstate=runstate,
            feature_id="001-test",
            product_id="test-product",
        )
        
        assert archive_pack["feature_id"] == "001-test"
        assert archive_pack["product_id"] == "test-product"
        assert len(archive_pack["delivered_outputs"]) == 2

    def test_includes_lessons_and_patterns(self, temp_dir):
        """build_archive_pack should include provided lessons/patterns."""
        runstate = {
            "completed_outputs": [],
            "decisions_needed": [],
            "blocked_items": [],
        }
        
        archive_pack = build_archive_pack(
            runstate=runstate,
            feature_id="001-test",
            product_id="test-product",
            lessons_input="Keep scope small,Test early",
            patterns_input="Schema+Template pattern,Day-sized tasks",
        )
        
        assert len(archive_pack["lessons_learned"]) == 2
        assert len(archive_pack["reusable_patterns"]) == 2

    def test_handles_partial_status(self, temp_dir):
        """build_archive_pack should handle partial status."""
        runstate = {
            "completed_outputs": ["schemas/test.yaml"],
            "decisions_needed": [],
            "blocked_items": [{"item": "API", "reason": "Down"}],
        }
        
        archive_pack = build_archive_pack(
            runstate=runstate,
            feature_id="001-test",
            product_id="test-product",
            final_status="partial",
        )
        
        assert archive_pack["final_status"] == "partial"
        assert len(archive_pack["unresolved_followups"]) >= 1


class TestLifecycleSequence:
    """Tests for full completion/archive lifecycle."""

    def test_full_lifecycle_sequence(self, temp_dir):
        """Test complete lifecycle: planning → completed → archived."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.new_feature import app as new_feature_app
        from cli.commands.complete_feature import app as complete_app
        from cli.commands.archive_feature import app as archive_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])
        
        runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "planning"
        
        runstate["blocked_items"] = []
        runstate["decisions_needed"] = []
        runstate["completed_outputs"] = ["schemas/test.yaml"]
        store.save_runstate(runstate)
        
        runner.invoke(complete_app, [
            "mark",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "completed"
        
        runner.invoke(archive_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_dir),
        ])
        
        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()
        assert runstate["current_phase"] == "archived"