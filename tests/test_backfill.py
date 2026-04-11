"""Tests for Feature 013 - Historical Archive Backfill."""

from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner

from runtime.archive_pack_builder import (
    build_backfill_archive_pack,
    check_backfill_eligibility,
    save_archive_pack,
    load_archive_pack,
)
from cli.commands.backfill import app as backfill_app


runner = CliRunner()


class TestBuildBackfillArchivePack:
    """Test backfill archive pack generation."""

    def test_builds_minimal_backfill_pack(self):
        """build_backfill_archive_pack should create pack with backfill markers."""
        pack = build_backfill_archive_pack(
            feature_id="001-test",
            product_id="test-product",
        )
        
        assert pack["feature_id"] == "001-test"
        assert pack["product_id"] == "test-product"
        assert pack["archived_via_backfill"] is True
        assert pack["backfilled_at"] is not None
        assert "known_gaps" in pack

    def test_includes_backfill_metadata(self):
        """Backfill pack should have required metadata fields."""
        pack = build_backfill_archive_pack(
            feature_id="002-test",
            product_id="test-product",
            title="Test Feature",
        )
        
        assert pack["archived_via_backfill"] is True
        assert pack["backfill_source"] == "manual-backfill-command"
        assert pack["backfill_confidence"] == "medium"
        assert len(pack["known_gaps"]) >= 1

    def test_includes_delivered_outputs(self):
        """Backfill pack should capture delivered outputs."""
        pack = build_backfill_archive_pack(
            feature_id="003-test",
            product_id="test-product",
            delivered_outputs=["schema.yaml", "template.md"],
        )
        
        assert len(pack["delivered_outputs"]) == 2
        assert pack["delivered_outputs"][0]["name"] == "schema.yaml"

    def test_includes_lessons_and_patterns(self):
        """Backfill pack should parse lessons and patterns."""
        pack = build_backfill_archive_pack(
            feature_id="004-test",
            product_id="test-product",
            lessons_input="Small tasks work,Test early",
            patterns_input="Schema-first approach,Iterative testing",
        )
        
        assert len(pack["lessons_learned"]) == 2
        assert len(pack["reusable_patterns"]) == 2

    def test_includes_historical_notes(self):
        """Backfill pack should include historical notes if provided."""
        pack = build_backfill_archive_pack(
            feature_id="005-test",
            product_id="test-product",
            historical_notes="Completed before archive system existed",
        )
        
        assert pack["historical_notes"] == "Completed before archive system existed"


class TestCheckBackfillEligibility:
    """Test backfill eligibility checking."""

    def test_eligible_for_unarchived_feature(self, setup_test_project):
        """Feature without archive should be eligible."""
        eligibility = check_backfill_eligibility(
            feature_id="001-test",
            product_id="test-product",
            projects_path=setup_test_project,
        )
        
        assert eligibility["eligible"] is True
        assert "not yet archived" in eligibility["reasons"][0]

    def test_not_eligible_for_archived_feature(self, setup_archived_feature):
        """Feature with archive should not be eligible."""
        eligibility = check_backfill_eligibility(
            feature_id="001-archived",
            product_id="test-product",
            projects_path=setup_archived_feature,
        )
        
        assert eligibility["eligible"] is False
        assert "Already archived" in eligibility["reasons"][0]

    def test_not_eligible_for_nonexistent_feature(self, setup_test_project):
        """Nonexistent feature should not be eligible."""
        eligibility = check_backfill_eligibility(
            feature_id="999-nonexistent",
            product_id="test-product",
            projects_path=setup_test_project,
        )
        
        assert eligibility["eligible"] is False
        assert "does not exist" in eligibility["reasons"][0]

    def test_detects_feature_spec(self, setup_feature_with_spec):
        """Eligibility check should detect feature-spec.yaml."""
        eligibility = check_backfill_eligibility(
            feature_id="001-spec",
            product_id="test-product",
            projects_path=setup_feature_with_spec,
        )
        
        assert eligibility.get("has_spec") is True
        assert eligibility.get("spec_path") is not None


class TestBackfillCLI:
    """Test backfill CLI commands."""

    def test_create_shows_preview(self, setup_feature_with_spec):
        """backfill create should show preview."""
        result = runner.invoke(backfill_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-spec",
            "--dry-run",
            "--path", str(setup_feature_with_spec),
        ])
        
        assert result.exit_code == 0
        assert "Backfill Archive Preview" in result.output
        assert "archived_via_backfill" in result.output

    def test_create_saves_archive_pack(self, setup_feature_with_spec):
        """backfill create should save archive-pack.yaml."""
        result = runner.invoke(backfill_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-spec",
            "--path", str(setup_feature_with_spec),
        ])
        
        assert result.exit_code == 0
        
        archive_path = setup_feature_with_spec / "test-product" / "archive" / "001-spec" / "archive-pack.yaml"
        assert archive_path.exists()

    def test_create_rejects_archived_feature(self, setup_archived_feature):
        """backfill create should reject already archived feature."""
        result = runner.invoke(backfill_app, [
            "create",
            "--project", "test-product",
            "--feature", "001-archived",
            "--path", str(setup_archived_feature),
        ])
        
        assert result.exit_code == 1
        assert "not eligible" in result.output

    def test_check_shows_eligibility(self, setup_feature_with_spec):
        """backfill check should show eligibility status."""
        result = runner.invoke(backfill_app, [
            "check",
            "--project", "test-product",
            "--feature", "001-spec",
            "--path", str(setup_feature_with_spec),
        ])
        
        assert result.exit_code == 0
        assert "eligible" in result.output

    def test_list_shows_features(self, setup_multiple_features):
        """backfill list should show all features."""
        result = runner.invoke(backfill_app, [
            "list",
            "--project", "test-product",
            "--path", str(setup_multiple_features),
        ])
        
        assert result.exit_code == 0
        assert "Features Status" in result.output or "Backfill Candidates" in result.output


class TestBackfillArchivePackFields:
    """Test backfill archive pack field requirements."""

    def test_has_all_required_fields(self):
        """Backfill pack should have all minimum required fields."""
        pack = build_backfill_archive_pack(
            feature_id="001-fields",
            product_id="test-product",
        )
        
        required_fields = [
            "feature_id",
            "product_id",
            "title",
            "final_status",
            "delivered_outputs",
            "decisions_made",
            "lessons_learned",
            "reusable_patterns",
            "archived_at",
            "archived_via_backfill",
            "backfilled_at",
        ]
        
        for field in required_fields:
            assert field in pack

    def test_backfill_marker_is_true(self):
        """archived_via_backfill must be True."""
        pack = build_backfill_archive_pack(
            feature_id="002-marker",
            product_id="test-product",
        )
        
        assert pack["archived_via_backfill"] is True

    def test_backfilled_at_timestamp_present(self):
        """backfilled_at should have valid timestamp."""
        pack = build_backfill_archive_pack(
            feature_id="003-timestamp",
            product_id="test-product",
        )
        
        assert pack["backfilled_at"] is not None
        assert "T" in pack["backfilled_at"]  # ISO format


import pytest


@pytest.fixture
def setup_test_project():
    """Create test project structure."""
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "test-product"
    project_dir.mkdir()
    
    (project_dir / "features").mkdir()
    (project_dir / "archive").mkdir()
    
    feature_dir = project_dir / "features" / "001-test"
    feature_dir.mkdir()
    
    yield temp_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def setup_archived_feature():
    """Create test project with archived feature."""
    import yaml
    
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "test-product"
    project_dir.mkdir()
    
    features_dir = project_dir / "features"
    features_dir.mkdir()
    feature_dir = features_dir / "001-archived"
    feature_dir.mkdir()
    
    archive_dir = project_dir / "archive" / "001-archived"
    archive_dir.mkdir(parents=True)
    
    archive_pack = {
        "feature_id": "001-archived",
        "product_id": "test-product",
        "title": "Already Archived",
        "final_status": "completed",
        "archived_at": "2024-01-01",
    }
    save_archive_pack(archive_pack, archive_dir / "archive-pack.yaml")
    
    yield temp_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def setup_feature_with_spec():
    """Create test project with feature-spec.yaml."""
    import yaml
    
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "test-product"
    project_dir.mkdir()
    
    (project_dir / "features").mkdir()
    feature_dir = project_dir / "features" / "001-spec"
    feature_dir.mkdir()
    
    spec = {
        "feature_id": "001-spec",
        "name": "Test Feature With Spec",
        "description": "A test feature",
    }
    with open(feature_dir / "feature-spec.yaml", "w") as f:
        yaml.dump(spec, f)
    
    yield temp_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def setup_multiple_features():
    """Create test project with multiple features."""
    import yaml
    
    temp_dir = Path(tempfile.mkdtemp())
    project_dir = temp_dir / "test-product"
    project_dir.mkdir()
    
    (project_dir / "features").mkdir()
    (project_dir / "archive").mkdir()
    
    for i in range(3):
        feature_dir = project_dir / "features" / f"00{i}-feature"
        feature_dir.mkdir()
        
        spec = {"feature_id": f"00{i}-feature", "name": f"Feature {i}"}
        with open(feature_dir / "feature-spec.yaml", "w") as f:
            yaml.dump(spec, f)
    
    yield temp_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)