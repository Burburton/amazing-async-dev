"""Tests for Evidence Rollup - Feature 079."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from runtime.evidence_rollup import (
    FeatureEvidenceSummary,
    ProjectEvidenceSummary,
    LatestTruthResolver,
    build_feature_evidence_summary,
    build_project_evidence_summary,
    save_feature_evidence_summary,
    save_project_evidence_summary,
    load_feature_evidence_summary,
)
from runtime.state_store import StateStore


class TestFeatureEvidenceSummary:
    def test_summary_creation(self):
        summary = FeatureEvidenceSummary(
            feature_id="001-test-feature",
            latest_execution_result_ref="exec-20260425-001",
            latest_execution_status="success",
        )
        
        assert summary.feature_id == "001-test-feature"
        assert summary.latest_execution_result_ref == "exec-20260425-001"
        assert summary.latest_execution_status == "success"
    
    def test_summary_to_dict(self):
        summary = FeatureEvidenceSummary(
            feature_id="001-test",
            latest_execution_status="success",
            recovery_required=False,
        )
        
        data = summary.to_dict()
        
        assert data["feature_id"] == "001-test"
        assert data["latest_execution_status"] == "success"
        assert data["recovery_required"] is False
    
    def test_is_healthy(self):
        healthy = FeatureEvidenceSummary(
            feature_id="001-healthy",
            latest_execution_status="success",
            recovery_required=False,
            completion_blocked=False,
        )
        
        unhealthy = FeatureEvidenceSummary(
            feature_id="002-unhealthy",
            latest_execution_status="failed",
            recovery_required=True,
        )
        
        assert healthy.is_healthy() is True
        assert unhealthy.is_healthy() is False
    
    def test_needs_attention(self):
        needs_attention = FeatureEvidenceSummary(
            feature_id="001-attention",
            recovery_required=True,
        )
        
        no_attention = FeatureEvidenceSummary(
            feature_id="002-ok",
            recovery_required=False,
            observer_high_severity_count=0,
        )
        
        assert needs_attention.needs_attention() is True
        assert no_attention.needs_attention() is False


class TestProjectEvidenceSummary:
    def test_summary_creation(self):
        summary = ProjectEvidenceSummary(
            project_id="test-project",
            current_phase="executing",
        )
        
        assert summary.project_id == "test-project"
        assert summary.current_phase == "executing"
    
    def test_summary_with_features(self):
        feature = FeatureEvidenceSummary(feature_id="001-test")
        summary = ProjectEvidenceSummary(
            project_id="test-project",
            features=[feature],
            total_features=1,
        )
        
        assert len(summary.features) == 1
        assert summary.total_features == 1
    
    def test_to_dict_includes_features(self):
        feature = FeatureEvidenceSummary(feature_id="001-test")
        summary = ProjectEvidenceSummary(
            project_id="test-project",
            features=[feature],
        )
        
        data = summary.to_dict()
        
        assert "features" in data
        assert len(data["features"]) == 1
        assert data["features"][0]["feature_id"] == "001-test"


class TestLatestTruthResolver:
    def test_get_latest_execution_result_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            resolver = LatestTruthResolver(project_path)
            
            result_id, result_path = resolver.get_latest_execution_result()
            
            assert result_id == ""
            assert result_path is None
    
    def test_get_latest_execution_result_single(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir()
            
            result_file = results_dir / "exec-20260425-001.md"
            result_file.write_text("# ExecutionResult\n\n```yaml\nstatus: success\n```", encoding="utf-8")
            
            resolver = LatestTruthResolver(project_path)
            result_id, result_path = resolver.get_latest_execution_result()
            
            assert result_id == "exec-20260425-001"
            assert result_path == result_file
    
    def test_get_latest_execution_result_multiple(self):
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir()
            
            older = results_dir / "exec-20260424-001.md"
            older.write_text("# Old", encoding="utf-8")
            
            time.sleep(0.1)
            
            newer = results_dir / "exec-20260425-001.md"
            newer.write_text("# New", encoding="utf-8")
            
            resolver = LatestTruthResolver(project_path)
            result_id, result_path = resolver.get_latest_execution_result()
            
            assert result_id == "exec-20260425-001"
    
    def test_get_latest_acceptance_result_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            resolver = LatestTruthResolver(project_path)
            
            result_id, result_path = resolver.get_latest_acceptance_result()
            
            assert result_id == ""
            assert result_path is None
    
    def test_get_latest_artifact_unknown_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            resolver = LatestTruthResolver(project_path)
            
            result_id, result_path = resolver.get_latest_artifact("unknown_type")
            
            assert result_id == ""
            assert result_path is None


class TestBuildFeatureEvidenceSummary:
    def test_build_with_empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "001-test",
                "project_id": "test-project",
            })
            
            summary = build_feature_evidence_summary(project_path, "001-test")
            
            assert summary.feature_id == "001-test"
            assert summary.latest_execution_result_ref == ""
    
    def test_build_with_execution_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            results_dir = project_path / "execution-results"
            results_dir.mkdir()
            
            result_file = results_dir / "exec-20260425-001.md"
            result_file.write_text("# ExecutionResult\n\n```yaml\nstatus: success\nexecution_id: exec-20260425-001\n```", encoding="utf-8")
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "001-test",
                "project_id": "test-project",
            })
            
            summary = build_feature_evidence_summary(project_path, "001-test")
            
            assert summary.feature_id == "001-test"
            assert summary.latest_execution_result_ref == "exec-20260425-001"


class TestBuildProjectEvidenceSummary:
    def test_build_empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            summary = build_project_evidence_summary(project_path)
            
            assert summary.project_id == project_path.name
            assert summary.total_features == 0
    
    def test_build_with_runstate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "001-test",
                "project_id": project_path.name,
                "current_phase": "executing",
            })
            
            summary = build_project_evidence_summary(project_path)
            
            assert summary.current_phase == "executing"


class TestSaveAndLoadEvidenceSummary:
    def test_save_feature_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            summary = FeatureEvidenceSummary(
                feature_id="001-test",
                latest_execution_status="success",
            )
            
            output_path = save_feature_evidence_summary(project_path, summary)
            
            assert output_path.exists()
            assert output_path.name == "001-test-evidence-summary.md"
    
    def test_save_project_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            summary = ProjectEvidenceSummary(project_id=project_path.name)
            
            output_path = save_project_evidence_summary(project_path, summary)
            
            assert output_path.exists()
            assert output_path.name == "evidence-summary.md"
    
    def test_load_feature_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            summary = FeatureEvidenceSummary(
                feature_id="001-test",
                latest_execution_status="success",
            )
            
            save_feature_evidence_summary(project_path, summary)
            
            loaded = load_feature_evidence_summary(project_path, "001-test")
            
            assert loaded is not None
            assert loaded.feature_id == "001-test"
            assert loaded.latest_execution_status == "success"
    
    def test_load_missing_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            loaded = load_feature_evidence_summary(project_path, "missing-feature")
            
            assert loaded is None


class TestArtifactRouterExtensions:
    def test_acceptance_pack_type_exists(self):
        from runtime.artifact_router import ArtifactType
        
        assert ArtifactType.ACCEPTANCE_PACK.value == "acceptance_pack"
        assert ArtifactType.ACCEPTANCE_RESULT.value == "acceptance_result"
        assert ArtifactType.ACCEPTANCE_RECOVERY_PACK.value == "acceptance_recovery_pack"
        assert ArtifactType.EVIDENCE_SUMMARY.value == "evidence_summary"
    
    def test_acceptance_artifacts_orchestration_owned(self):
        from runtime.artifact_router import (
            ArtifactType,
            is_orchestration_owned,
        )
        
        assert is_orchestration_owned(ArtifactType.ACCEPTANCE_PACK)
        assert is_orchestration_owned(ArtifactType.ACCEPTANCE_RESULT)
        assert is_orchestration_owned(ArtifactType.ACCEPTANCE_RECOVERY_PACK)
        assert is_orchestration_owned(ArtifactType.EVIDENCE_SUMMARY)
    
    def test_get_acceptance_result_path(self):
        from runtime.artifact_router import get_acceptance_result_path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result_path = get_acceptance_result_path(project_path, "ar-20260425-001")
            
            assert "acceptance-results" in str(result_path)
            assert result_path.name == "ar-20260425-001.md"
    
    def test_get_evidence_summary_path_feature(self):
        from runtime.artifact_router import get_evidence_summary_path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            feature_path = get_evidence_summary_path(project_path, "001-test")
            
            assert "evidence-summaries" in str(feature_path)
            assert feature_path.name == "001-test-evidence-summary.md"
    
    def test_get_evidence_summary_path_project(self):
        from runtime.artifact_router import get_evidence_summary_path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            project_summary_path = get_evidence_summary_path(project_path)
            
            assert project_summary_path.name == "evidence-summary.md"


class TestDirectoryInconsistencyFix:
    def test_acceptance_recovery_adapter_correct_directory(self):
        from runtime.acceptance_recovery_adapter import AcceptanceRecoveryAdapter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            adapter = AcceptanceRecoveryAdapter(project_path)
            
            assert adapter.project_path == project_path