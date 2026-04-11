"""Tests for asyncdev new-feature command."""

import pytest
from pathlib import Path
import yaml
from typer.testing import CliRunner
from cli.commands.new_feature import app
from cli.commands.new_product import app as product_app


runner = CliRunner()


class TestNewFeatureCreate:
    """Tests for new-feature create command."""

    def test_creates_feature_directory(self, temp_dir):
        """new-feature should create feature directory."""
        # Create product first
        runner.invoke(product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        # Create feature
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert (temp_dir / "test-product" / "features" / "001-test").exists()

    def test_creates_feature_spec_yaml(self, temp_dir):
        """new-feature should create feature-spec.yaml."""
        runner.invoke(product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--goal", "Test goal",
            "--path", str(temp_dir),
        ])

        spec_path = temp_dir / "test-product" / "features" / "001-test" / "feature-spec.yaml"
        assert spec_path.exists()

        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        assert spec["feature_id"] == "001-test"
        assert spec["name"] == "Test Feature"

    def test_updates_runstate(self, temp_dir):
        """new-feature should update runstate with feature context."""
        from runtime.state_store import StateStore

        runner.invoke(product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])

        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()

        assert runstate["feature_id"] == "001-test"
        assert runstate["current_phase"] == "planning"

    def test_fails_if_product_not_found(self, temp_dir):
        """new-feature should fail if product doesn't exist."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "nonexistent",
            "--feature-id", "001-test",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_fails_if_feature_exists(self, temp_dir):
        """new-feature should fail if feature already exists."""
        runner.invoke(product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        # Create feature once
        runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        # Try to create again
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "already exists" in result.output


class TestNewFeatureList:
    """Tests for new-feature list command."""

    def test_lists_features(self, temp_dir):
        """new-feature list should show features."""
        runner.invoke(product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Feature 1",
            "--path", str(temp_dir),
        ])

        result = runner.invoke(app, [
            "list",
            "--product-id", "test-product",
            "--path", str(temp_dir),
        ])

        assert "001-test" in result.output

    def test_shows_empty_when_no_features(self, temp_dir):
        """new-feature list should show empty message."""
        runner.invoke(product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--path", str(temp_dir),
        ])

        result = runner.invoke(app, [
            "list",
            "--product-id", "test-product",
            "--path", str(temp_dir),
        ])

        assert "No features" in result.output