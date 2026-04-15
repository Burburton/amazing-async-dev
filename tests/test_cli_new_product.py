"""Tests for asyncdev new-product command."""

import pytest
from pathlib import Path
import yaml
from typer.testing import CliRunner
from cli.commands.new_product import app


runner = CliRunner()


class TestNewProductCreate:
    """Tests for new-product create command."""

    def test_creates_product_directory(self, temp_dir):
        """new-product should create product directory."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert (temp_dir / "test-product").exists()

    def test_creates_product_brief_yaml(self, temp_dir):
        """new-product should create product-brief.yaml."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        brief_path = temp_dir / "test-product" / "product-brief.yaml"
        assert brief_path.exists()

        with open(brief_path) as f:
            brief = yaml.safe_load(f)

        assert brief["product_id"] == "test-product"
        assert brief["name"] == "Test Product"

    def test_creates_runstate_md(self, temp_dir):
        """new-product should create runstate.md."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        runstate_path = temp_dir / "test-product" / "runstate.md"
        assert runstate_path.exists()

    def test_creates_subdirectories(self, temp_dir):
        """new-product should create required subdirectories."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        product_dir = temp_dir / "test-product"
        assert (product_dir / "execution-packs").exists()
        assert (product_dir / "execution-results").exists()
        assert (product_dir / "reviews").exists()
        assert (product_dir / "features").exists()

    def test_fails_if_product_exists(self, temp_dir):
        """new-product should fail if product already exists."""
        existing = temp_dir / "existing-product"
        existing.mkdir()

        result = runner.invoke(app, [
            "create",
            "--product-id", "existing-product",
            "--name", "Existing",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_sets_initial_phase_to_planning(self, temp_dir):
        """new-product should set RunState phase to planning."""
        from runtime.state_store import StateStore

        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        store = StateStore(temp_dir / "test-product")
        runstate = store.load_runstate()

        assert runstate["current_phase"] == "planning"


class TestNewProductGovernance:
    """Tests for --ownership-mode and --repo-url parameters (Feature 039)."""

    def test_default_is_self_hosted(self, temp_dir):
        """Default ownership mode should be self_hosted."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert "self_hosted" in result.output

    def test_no_project_link_for_self_hosted(self, temp_dir):
        """self_hosted mode should not create project-link.yaml."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])

        link_path = temp_dir / "test-product" / "project-link.yaml"
        assert not link_path.exists()

    def test_managed_external_creates_project_link(self, temp_dir):
        """managed_external mode should create project-link.yaml."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "visual-map",
            "--name", "Visual Map",
            "--ownership-mode", "managed_external",
            "--repo-url", "https://github.com/user/amazing-visual-map",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 0
        link_path = temp_dir / "visual-map" / "project-link.yaml"
        assert link_path.exists()

        with open(link_path) as f:
            link = yaml.safe_load(f)

        assert link["ownership_mode"] == "managed_external"
        assert link["repo_url"] == "https://github.com/user/amazing-visual-map"

    def test_managed_external_shows_governance_note(self, temp_dir):
        """managed_external mode should show governance guidance."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "visual-map",
            "--name", "Visual Map",
            "--ownership-mode", "managed_external",
            "--repo-url", "https://github.com/user/visual-map",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert "Governance note" in result.output
        assert "Product truth" in result.output

    def test_managed_external_without_repo_url_warns(self, temp_dir):
        """managed_external without --repo-url should show warning."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "visual-map",
            "--name", "Visual Map",
            "--ownership-mode", "managed_external",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 0
        assert "requires --repo-url" in result.output

    def test_invalid_ownership_mode_fails(self, temp_dir):
        """Invalid ownership_mode should fail."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test",
            "--ownership-mode", "invalid_mode",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "Invalid ownership_mode" in result.output

    def test_repo_name_defaults_to_product_id(self, temp_dir):
        """--repo-name should default to product_id if not provided."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "visual-map",
            "--name", "Visual Map",
            "--ownership-mode", "managed_external",
            "--repo-url", "https://github.com/user/visual-map",
            "--path", str(temp_dir),
        ])

        link_path = temp_dir / "visual-map" / "project-link.yaml"
        with open(link_path) as f:
            link = yaml.safe_load(f)

        assert link["repo_name"] == "visual-map"

    def test_repo_name_can_be_customized(self, temp_dir):
        """--repo-name can be set to different value."""
        result = runner.invoke(app, [
            "create",
            "--product-id", "visual-map",
            "--name", "Visual Map",
            "--ownership-mode", "managed_external",
            "--repo-url", "https://github.com/user/amazing-visual-map",
            "--repo-name", "amazing-visual-map",
            "--path", str(temp_dir),
        ])

        link_path = temp_dir / "visual-map" / "project-link.yaml"
        with open(link_path) as f:
            link = yaml.safe_load(f)

        assert link["repo_name"] == "amazing-visual-map"


class TestNewProductList:
    """Tests for new-product list command."""

    def test_lists_products_with_briefs(self, temp_dir):
        """new-product list should show products with names."""
        # Create two products
        runner.invoke(app, ["create", "--product-id", "p1", "--name", "Product 1", "--path", str(temp_dir)])
        runner.invoke(app, ["create", "--product-id", "p2", "--name", "Product 2", "--path", str(temp_dir)])

        result = runner.invoke(app, ["list", "--path", str(temp_dir)])

        assert "p1" in result.output
        assert "p2" in result.output

    def test_shows_empty_message_when_no_products(self, temp_dir):
        """new-product list should show empty message."""
        result = runner.invoke(app, ["list", "--path", str(temp_dir)])

        assert "No products" in result.output