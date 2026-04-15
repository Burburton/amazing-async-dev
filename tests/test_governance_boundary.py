"""Tests for governance boundary functions in state_store.py.

Feature 039: Artifact ownership and storage boundary governance.
"""

import pytest
from pathlib import Path
import yaml
import tempfile
import shutil

from runtime.state_store import (
    load_project_link,
    get_ownership_mode,
    is_managed_external,
    get_product_repo_path,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


class TestLoadProjectLink:
    """Tests for load_project_link function."""

    def test_returns_none_when_no_project_link(self, temp_project_dir):
        """load_project_link should return None if project-link.yaml missing."""
        result = load_project_link(temp_project_dir)
        assert result is None

    def test_loads_project_link_yaml(self, temp_project_dir):
        """load_project_link should parse project-link.yaml."""
        project_link = {
            "product_id": "test-product",
            "repo_url": "https://github.com/user/test-product",
            "ownership_mode": "managed_external",
            "status": "active",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = load_project_link(temp_project_dir)
        assert result is not None
        assert result["product_id"] == "test-product"
        assert result["ownership_mode"] == "managed_external"

    def test_handles_empty_yaml(self, temp_project_dir):
        """load_project_link should handle empty YAML file."""
        link_path = temp_project_dir / "project-link.yaml"
        link_path.write_text("")
        
        result = load_project_link(temp_project_dir)
        assert result is None  # yaml.safe_load returns None for empty file


class TestGetOwnershipMode:
    """Tests for get_ownership_mode function."""

    def test_returns_self_hosted_by_default(self, temp_project_dir):
        """get_ownership_mode should return self_hosted when no project-link."""
        result = get_ownership_mode(temp_project_dir)
        assert result == "self_hosted"

    def test_returns_self_hosted_when_explicit(self, temp_project_dir):
        """get_ownership_mode should return self_hosted when specified."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = get_ownership_mode(temp_project_dir)
        assert result == "self_hosted"

    def test_returns_managed_external_when_specified(self, temp_project_dir):
        """get_ownership_mode should return managed_external when specified."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "managed_external",
            "repo_url": "https://github.com/user/test-product",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = get_ownership_mode(temp_project_dir)
        assert result == "managed_external"

    def test_defaults_to_self_hosted_when_key_missing(self, temp_project_dir):
        """get_ownership_mode should default to self_hosted if key missing."""
        project_link = {
            "product_id": "test-product",
            # ownership_mode key intentionally missing
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = get_ownership_mode(temp_project_dir)
        assert result == "self_hosted"


class TestIsManagedExternal:
    """Tests for is_managed_external function."""

    def test_returns_false_for_self_hosted(self, temp_project_dir):
        """is_managed_external should return False for self_hosted."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = is_managed_external(temp_project_dir)
        assert result is False

    def test_returns_false_when_no_project_link(self, temp_project_dir):
        """is_managed_external should return False when no project-link.yaml."""
        result = is_managed_external(temp_project_dir)
        assert result is False

    def test_returns_true_for_managed_external(self, temp_project_dir):
        """is_managed_external should return True for managed_external."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "managed_external",
            "repo_url": "https://github.com/user/test-product",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = is_managed_external(temp_project_dir)
        assert result is True


class TestGetProductRepoPath:
    """Tests for get_product_repo_path function."""

    def test_returns_none_for_self_hosted(self, temp_project_dir):
        """get_product_repo_path should return None for self_hosted mode."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
            "repo_local_path": "/some/path",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = get_product_repo_path(temp_project_dir)
        assert result is None

    def test_returns_none_when_no_project_link(self, temp_project_dir):
        """get_product_repo_path should return None when no project-link.yaml."""
        result = get_product_repo_path(temp_project_dir)
        assert result is None

    def test_returns_none_when_no_local_path(self, temp_project_dir):
        """get_product_repo_path should return None if repo_local_path missing."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "managed_external",
            "repo_url": "https://github.com/user/test-product",
            # repo_local_path intentionally missing
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = get_product_repo_path(temp_project_dir)
        assert result is None

    def test_returns_path_for_managed_external_with_local_path(self, temp_project_dir):
        """get_product_repo_path should return Path when repo_local_path set."""
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "managed_external",
            "repo_url": "https://github.com/user/test-product",
            "repo_local_path": "/local/repos/test-product",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        result = get_product_repo_path(temp_project_dir)
        assert result is not None
        assert result == Path("/local/repos/test-product")


class TestGovernanceBoundaryIntegration:
    """Integration tests for governance boundary functions."""

    def test_full_workflow_managed_external(self, temp_project_dir):
        """Test full workflow for managed_external mode."""
        # Create project-link.yaml for managed external product
        project_link = {
            "product_id": "amazing-visual-map",
            "repo_name": "amazing-visual-map",
            "repo_url": "https://github.com/user/amazing-visual-map",
            "repo_local_path": str(temp_project_dir / "repos" / "amazing-visual-map"),
            "ownership_mode": "managed_external",
            "status": "active",
            "created_at": "2025-01-01T00:00:00",
        }
        
        link_path = temp_project_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link, f, default_flow_style=False)
        
        # Verify all functions work together
        assert load_project_link(temp_project_dir) is not None
        assert get_ownership_mode(temp_project_dir) == "managed_external"
        assert is_managed_external(temp_project_dir) is True
        assert get_product_repo_path(temp_project_dir) == Path(
            str(temp_project_dir / "repos" / "amazing-visual-map")
        )

    def test_full_workflow_self_hosted(self, temp_project_dir):
        """Test full workflow for self_hosted mode."""
        # No project-link.yaml created
        
        # Verify all functions work together
        assert load_project_link(temp_project_dir) is None
        assert get_ownership_mode(temp_project_dir) == "self_hosted"
        assert is_managed_external(temp_project_dir) is False
        assert get_product_repo_path(temp_project_dir) is None