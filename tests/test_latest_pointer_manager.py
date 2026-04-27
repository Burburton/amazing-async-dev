"""Tests for Latest Pointer Files - Feature 067 hardening (C-006).

Tests that pointer files enable faster latest-truth resolution.
"""

import pytest
from datetime import datetime
from pathlib import Path

from runtime.latest_pointer_manager import (
    create_latest_pointer,
    read_latest_pointer,
    update_pointer_after_observer_findings,
    get_all_pointers,
    pointer_exists,
    delete_pointer,
    POINTER_FILES,
)
from runtime.evidence_rollup import LatestTruthResolver


class TestLatestPointerManager:
    """Tests for pointer file management."""

    def test_create_latest_pointer_creates_file(self, tmp_path: Path):
        target_path = tmp_path / "execution-results" / "exec-001.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("# Test", encoding="utf-8")
        
        pointer_path = create_latest_pointer(
            tmp_path,
            "execution_result",
            "exec-001",
            target_path,
        )
        
        assert pointer_path.exists()
        assert pointer_path.name == "latest-execution-result.md"

    def test_read_latest_pointer_returns_target(self, tmp_path: Path):
        target_path = tmp_path / "execution-results" / "exec-002.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("# Test", encoding="utf-8")
        
        create_latest_pointer(tmp_path, "execution_result", "exec-002", target_path)
        
        target_id, resolved_path = read_latest_pointer(tmp_path, "execution_result")
        
        assert target_id == "exec-002"
        assert resolved_path == target_path

    def test_read_latest_pointer_missing_returns_none(self, tmp_path: Path):
        target_id, resolved_path = read_latest_pointer(tmp_path, "execution_result")
        
        assert target_id == ""
        assert resolved_path is None

    def test_read_latest_pointer_target_not_exists_returns_none(self, tmp_path: Path):
        pointer_path = tmp_path / "latest-execution-result.md"
        pointer_path.write_text("""# Latest Execution Result Pointer
```yaml
pointer_type: execution_result
target_id: exec-missing
target_path: execution-results/exec-missing.md
updated_at: 2026-04-27T12:00:00
```
""")
        
        target_id, resolved_path = read_latest_pointer(tmp_path, "execution_result")
        
        assert target_id == ""
        assert resolved_path is None

    def test_update_pointer_after_observer_findings(self, tmp_path: Path):
        from runtime.artifact_router import get_observer_findings_path
        from runtime.execution_observer import ObservationResult, ObserverFinding, ObserverFindingType, FindingSeverity
        
        findings_dir = tmp_path / "observer-findings"
        findings_dir.mkdir(parents=True, exist_ok=True)
        
        result = ObservationResult(
            observation_id="obs-001",
            project_id="test",
            started_at="2026-04-27T12:00:00",
            findings=[
                ObserverFinding(
                    finding_id="find-001",
                    finding_type=ObserverFindingType.BLOCKED_STATE,
                    severity=FindingSeverity.HIGH,
                    reason="Test",
                )
            ],
        )
        
        target_path = get_observer_findings_path(tmp_path, "obs-001")
        target_path.write_text("# Test", encoding="utf-8")
        
        pointer_path = update_pointer_after_observer_findings(tmp_path, "obs-001")
        
        assert pointer_path is not None
        assert pointer_path.exists()
        
        target_id, resolved = read_latest_pointer(tmp_path, "observer_findings")
        assert target_id == "obs-001"

    def test_get_all_pointers(self, tmp_path: Path):
        exec_target = tmp_path / "execution-results" / "exec-001.md"
        exec_target.parent.mkdir(parents=True, exist_ok=True)
        exec_target.write_text("# Test")
        create_latest_pointer(tmp_path, "execution_result", "exec-001", exec_target)
        
        accept_target = tmp_path / "acceptance-results" / "ar-001.md"
        accept_target.parent.mkdir(parents=True, exist_ok=True)
        accept_target.write_text("# Test")
        create_latest_pointer(tmp_path, "acceptance_result", "ar-001", accept_target)
        
        pointers = get_all_pointers(tmp_path)
        
        assert pointers["execution_result"][0] == "exec-001"
        assert pointers["acceptance_result"][0] == "ar-001"
        assert pointers["observer_findings"][0] == ""

    def test_pointer_exists(self, tmp_path: Path):
        assert not pointer_exists(tmp_path, "execution_result")
        
        target_path = tmp_path / "execution-results" / "exec-001.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("# Test")
        create_latest_pointer(tmp_path, "execution_result", "exec-001", target_path)
        
        assert pointer_exists(tmp_path, "execution_result")

    def test_delete_pointer(self, tmp_path: Path):
        target_path = tmp_path / "execution-results" / "exec-001.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text("# Test")
        create_latest_pointer(tmp_path, "execution_result", "exec-001", target_path)
        
        assert pointer_exists(tmp_path, "execution_result")
        
        deleted = delete_pointer(tmp_path, "execution_result")
        
        assert deleted
        assert not pointer_exists(tmp_path, "execution_result")

    def test_delete_pointer_not_exists_returns_false(self, tmp_path: Path):
        deleted = delete_pointer(tmp_path, "execution_result")
        assert not deleted


class TestLatestTruthResolverWithPointer:
    """Tests for LatestTruthResolver using pointer files."""

    def test_resolver_uses_pointer_when_available(self, tmp_path: Path):
        exec_target = tmp_path / "execution-results" / "exec-pointer.md"
        exec_target.parent.mkdir(parents=True, exist_ok=True)
        exec_target.write_text("# Pointer Test")
        create_latest_pointer(tmp_path, "execution_result", "exec-pointer", exec_target)
        
        other_target = tmp_path / "execution-results" / "exec-other.md"
        other_target.write_text("# Other Test")
        
        resolver = LatestTruthResolver(tmp_path, use_pointer=True)
        
        target_id, target_path = resolver.get_latest_execution_result()
        
        assert target_id == "exec-pointer"
        assert target_path == exec_target

    def test_resolver_fallback_without_pointer(self, tmp_path: Path):
        exec_target1 = tmp_path / "execution-results" / "exec-001.md"
        exec_target1.parent.mkdir(parents=True, exist_ok=True)
        exec_target1.write_text("# First")
        
        exec_target2 = tmp_path / "execution-results" / "exec-002.md"
        exec_target2.write_text("# Second")
        
        resolver = LatestTruthResolver(tmp_path, use_pointer=False)
        
        target_id, target_path = resolver.get_latest_execution_result()
        
        assert target_id in ["exec-001", "exec-002"]
        assert target_path is not None

    def test_resolver_pointer_missing_fallback(self, tmp_path: Path):
        exec_target = tmp_path / "execution-results" / "exec-fallback.md"
        exec_target.parent.mkdir(parents=True, exist_ok=True)
        exec_target.write_text("# Fallback")
        
        resolver = LatestTruthResolver(tmp_path, use_pointer=True)
        
        target_id, target_path = resolver.get_latest_execution_result()
        
        assert target_id == "exec-fallback"
        assert target_path == exec_target

    def test_resolver_get_latest_observer_findings_with_pointer(self, tmp_path: Path):
        from runtime.artifact_router import get_observer_findings_path
        
        findings_dir = tmp_path / "observer-findings"
        findings_dir.mkdir(parents=True, exist_ok=True)
        
        obs_target = get_observer_findings_path(tmp_path, "obs-pointer")
        obs_target.write_text("# Observer")
        
        create_latest_pointer(tmp_path, "observer_findings", "obs-pointer", obs_target)
        
        resolver = LatestTruthResolver(tmp_path, use_pointer=True)
        
        target_id, target_path = resolver.get_latest_observer_findings()
        
        assert target_id == "obs-pointer"
        assert target_path == obs_target


class TestPointerIntegration:
    """Integration tests for pointer auto-update."""

    def test_observer_persistence_auto_updates_pointer(self, tmp_path: Path):
        from runtime.execution_observer import ObservationResult, ObserverFinding, ObserverFindingType, FindingSeverity
        from runtime.observer_finding_store import save_observation_result
        
        result = ObservationResult(
            observation_id="obs-auto",
            project_id="test",
            started_at="2026-04-27T12:00:00",
            findings=[
                ObserverFinding(
                    finding_id="find-auto",
                    finding_type=ObserverFindingType.BLOCKED_STATE,
                    severity=FindingSeverity.HIGH,
                    reason="Auto pointer test",
                )
            ],
        )
        
        save_observation_result(result, tmp_path)
        
        assert pointer_exists(tmp_path, "observer_findings")
        
        target_id, _ = read_latest_pointer(tmp_path, "observer_findings")
        assert target_id == "obs-auto"