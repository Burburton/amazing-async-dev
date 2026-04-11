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