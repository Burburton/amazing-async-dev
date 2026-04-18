"""Tests for Feature 055 - CLI Project-Link Awareness."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from runtime.project_link_loader import (
    OwnershipMode,
    ProjectLinkContext,
    load_project_link,
    parse_project_link_config,
    detect_ownership_mode,
    get_product_repo_path,
    get_orchestration_repo_path,
    is_mode_b,
    validate_project_link,
    get_project_link_summary,
)
from runtime.artifact_router import (
    ArtifactType,
    RoutingResult,
    is_product_owned,
    is_orchestration_owned,
    route_artifact,
    get_feature_spec_path,
    get_execution_pack_path,
    get_runstate_path,
    route_new_feature,
    get_routing_summary,
)


class TestOwnershipMode:
    def test_ownership_modes(self):
        assert OwnershipMode.SELF_HOSTED.value == "self_hosted"
        assert OwnershipMode.MANAGED_EXTERNAL.value == "managed_external"


class TestProjectLinkContext:
    def test_context_creation(self):
        context = ProjectLinkContext(
            product_id="test-product",
            ownership_mode=OwnershipMode.SELF_HOSTED,
        )
        assert context.product_id == "test-product"
        assert context.ownership_mode == OwnershipMode.SELF_HOSTED


class TestLoadProjectLink:
    def test_no_project_link(self, tmp_path):
        result = load_project_link(tmp_path)
        assert result is None
    
    def test_with_project_link(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("""
product_id: test-product
ownership_mode: managed_external
product_repo:
  path: /tmp/product
""")
        
        result = load_project_link(tmp_path)
        
        assert result is not None
        assert result.product_id == "test-product"
        assert result.ownership_mode == OwnershipMode.MANAGED_EXTERNAL


class TestParseProjectLinkConfig:
    def test_parse_self_hosted(self):
        config = {
            "product_id": "test",
            "ownership_mode": "self_hosted",
        }
        result = parse_project_link_config(config, Path("test.yaml"))
        
        assert result.ownership_mode == OwnershipMode.SELF_HOSTED
    
    def test_parse_managed_external(self):
        config = {
            "product_id": "test",
            "ownership_mode": "managed_external",
            "product_repo": {"path": "/tmp/product"},
        }
        result = parse_project_link_config(config, Path("test.yaml"))
        
        assert result.ownership_mode == OwnershipMode.MANAGED_EXTERNAL
        assert result.product_repo_path == Path("/tmp/product")
    
    def test_parse_invalid_mode_defaults_to_self_hosted(self):
        config = {
            "product_id": "test",
            "ownership_mode": "invalid_mode",
        }
        result = parse_project_link_config(config, Path("test.yaml"))
        
        assert result.ownership_mode == OwnershipMode.SELF_HOSTED


class TestDetectOwnershipMode:
    def test_no_project_link_returns_self_hosted(self, tmp_path):
        mode = detect_ownership_mode(tmp_path)
        assert mode == OwnershipMode.SELF_HOSTED
    
    def test_with_project_link_returns_correct_mode(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("ownership_mode: managed_external\n")
        
        mode = detect_ownership_mode(tmp_path)
        assert mode == OwnershipMode.MANAGED_EXTERNAL


class TestIsModeB:
    def test_no_project_link_is_not_mode_b(self, tmp_path):
        assert is_mode_b(tmp_path) is False
    
    def test_self_hosted_is_not_mode_b(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("ownership_mode: self_hosted\n")
        
        assert is_mode_b(tmp_path) is False
    
    def test_managed_external_is_mode_b(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("ownership_mode: managed_external\n")
        
        assert is_mode_b(tmp_path) is True


class TestValidateProjectLink:
    def test_no_project_link_is_valid(self, tmp_path):
        is_valid, issues = validate_project_link(tmp_path)
        assert is_valid is True
        assert issues == []
    
    def test_managed_external_without_path_is_invalid(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("""
product_id: test
ownership_mode: managed_external
""")
        
        is_valid, issues = validate_project_link(tmp_path)
        assert is_valid is False
        assert "product_repo path" in issues[0]


class TestArtifactType:
    def test_artifact_types(self):
        assert ArtifactType.FEATURE_SPEC.value == "feature_spec"
        assert ArtifactType.EXECUTION_PACK.value == "execution_pack"
        assert ArtifactType.RUNSTATE.value == "runstate"


class TestIsProductOwned:
    def test_feature_spec_is_product_owned(self):
        assert is_product_owned(ArtifactType.FEATURE_SPEC) is True
    
    def test_product_brief_is_product_owned(self):
        assert is_product_owned(ArtifactType.PRODUCT_BRIEF) is True
    
    def test_execution_pack_is_not_product_owned(self):
        assert is_product_owned(ArtifactType.EXECUTION_PACK) is False


class TestIsOrchestrationOwned:
    def test_execution_pack_is_orchestration_owned(self):
        assert is_orchestration_owned(ArtifactType.EXECUTION_PACK) is True
    
    def test_runstate_is_orchestration_owned(self):
        assert is_orchestration_owned(ArtifactType.RUNSTATE) is True
    
    def test_feature_spec_is_not_orchestration_owned(self):
        assert is_orchestration_owned(ArtifactType.FEATURE_SPEC) is False


class TestRouteArtifact:
    def test_route_feature_spec_mode_a(self, tmp_path):
        result = route_artifact(ArtifactType.FEATURE_SPEC, tmp_path)
        
        assert result.is_product_owned is True
        assert result.target_path == tmp_path
    
    def test_route_execution_pack_mode_a(self, tmp_path):
        result = route_artifact(ArtifactType.EXECUTION_PACK, tmp_path)
        
        assert result.is_product_owned is False
        assert result.target_path == tmp_path
    
    def test_route_feature_spec_mode_b(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("""
product_id: test
ownership_mode: managed_external
product_repo:
  path: /tmp/product
""")
        
        result = route_artifact(ArtifactType.FEATURE_SPEC, tmp_path)
        
        assert result.is_product_owned is True
        assert result.ownership == "product"


class TestGetFeatureSpecPath:
    def test_mode_a_path(self, tmp_path):
        path = get_feature_spec_path(tmp_path, "001-test")
        
        assert "001-test" in str(path)
        assert "feature-spec" in str(path)


class TestGetExecutionPackPath:
    def test_always_orchestration(self, tmp_path):
        path = get_execution_pack_path(tmp_path, "exec-001")
        
        assert "execution-packs" in str(path)
        assert "exec-001" in str(path)


class TestGetRunstatePath:
    def test_always_orchestration(self, tmp_path):
        path = get_runstate_path(tmp_path)
        
        assert path.name == "runstate.md"


class TestRouteNewFeature:
    def test_mode_a_routing(self, tmp_path):
        spec_path, feature_dir = route_new_feature(tmp_path, "001-test")
        
        assert "001-test" in str(feature_dir)
        assert "feature-spec" in str(spec_path)


class TestGetRoutingSummary:
    def test_no_project_link(self, tmp_path):
        summary = get_routing_summary(tmp_path)
        
        assert summary["mode"] == "self_hosted"
        assert summary["all_artifacts_local"] is True
    
    def test_with_project_link(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("""
product_id: test
ownership_mode: managed_external
product_repo:
  path: /tmp/product
""")
        
        summary = get_routing_summary(tmp_path)
        
        assert summary["mode"] == "managed_external"
        assert "routing_rules" in summary


class TestGetProjectLinkSummary:
    def test_no_project_link(self, tmp_path):
        summary = get_project_link_summary(tmp_path)
        
        assert summary["has_project_link"] is False
        assert summary["ownership_mode"] == "self_hosted"
    
    def test_with_project_link(self, tmp_path):
        project_link = tmp_path / "project-link.yaml"
        project_link.write_text("""
product_id: test-product
ownership_mode: managed_external
current_phase: phase-1
""")
        
        summary = get_project_link_summary(tmp_path)
        
        assert summary["has_project_link"] is True
        assert summary["product_id"] == "test-product"
        assert summary["current_phase"] == "phase-1"