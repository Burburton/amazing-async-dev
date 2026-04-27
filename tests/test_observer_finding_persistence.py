"""Tests for Observer Finding Persistence - Feature 067 hardening.

Tests C-005 fix: Observer findings must be persisted to disk.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from runtime.execution_observer import (
    ExecutionObserver,
    ObserverFinding,
    ObserverFindingType,
    FindingSeverity,
    ObservationResult,
)
from runtime.observer_finding_store import (
    save_observation_result,
    load_observation_result,
    list_observation_results,
    get_latest_observation_result,
    get_cumulative_findings,
)
from runtime.artifact_router import get_observer_findings_path, get_observer_findings_dir


class TestObserverFindingPersistence:
    """Tests for observer finding persistence layer."""

    def test_save_observation_result_creates_file(self, tmp_path: Path):
        finding = ObserverFinding(
            finding_id="find-20260427120000-001",
            finding_type=ObserverFindingType.BLOCKED_STATE,
            severity=FindingSeverity.HIGH,
            execution_id="exec-test-001",
            project_id="test-project",
            feature_id="feat-001",
            reason="Execution blocked by missing decision",
            suggested_action="Resolve decision before continuing",
            suggested_command="asyncdev decision reply --request dr-001",
            recovery_significant=True,
        )
        
        result = ObservationResult(
            observation_id="obs-20260427120000",
            project_id="test-project",
            started_at=datetime.now().isoformat(),
            finished_at=datetime.now().isoformat(),
            findings=[finding],
            execution_state_analyzed=True,
            artifacts_checked=True,
            verification_state_checked=True,
            closeout_state_checked=True,
            acceptance_readiness_checked=True,
            summary="Detected 1 finding: 0 critical, 1 high, 0 medium",
        )
        
        saved_path = save_observation_result(result, tmp_path)
        
        assert saved_path.exists()
        assert saved_path.name == "obs-20260427120000.md"
        assert "observer-findings" in str(saved_path)

    def test_save_and_load_preserves_data(self, tmp_path: Path):
        finding = ObserverFinding(
            finding_id="find-20260427120000-001",
            finding_type=ObserverFindingType.RUN_TIMEOUT,
            severity=FindingSeverity.CRITICAL,
            execution_id="exec-test-002",
            project_id="test-project",
            reason="Execution exceeded timeout threshold",
            details={"elapsed_seconds": 180},
            suggested_action="Inspect execution state",
            suggested_command="asyncdev recovery show --execution exec-test-002",
            recovery_significant=True,
        )
        
        result = ObservationResult(
            observation_id="obs-20260427130000",
            project_id="test-project",
            started_at="2026-04-27T13:00:00",
            finished_at="2026-04-27T13:00:05",
            findings=[finding],
            execution_state_analyzed=True,
            artifacts_checked=True,
            verification_state_checked=False,
            closeout_state_checked=False,
            acceptance_readiness_checked=False,
            summary="Detected 1 critical finding",
        )
        
        save_observation_result(result, tmp_path)
        
        loaded = load_observation_result(tmp_path, "obs-20260427130000")
        
        assert loaded is not None
        assert loaded.observation_id == "obs-20260427130000"
        assert loaded.project_id == "test-project"
        assert len(loaded.findings) == 1
        assert loaded.findings[0].finding_type == ObserverFindingType.RUN_TIMEOUT
        assert loaded.findings[0].severity == FindingSeverity.CRITICAL

    def test_list_observation_results_returns_sorted(self, tmp_path: Path):
        finding = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.BLOCKED_STATE,
            severity=FindingSeverity.HIGH,
            reason="Test finding",
        )
        
        result1 = ObservationResult(
            observation_id="obs-20260427100000",
            project_id="test-project",
            started_at="2026-04-27T10:00:00",
            findings=[finding],
        )
        
        result2 = ObservationResult(
            observation_id="obs-20260427120000",
            project_id="test-project",
            started_at="2026-04-27T12:00:00",
            findings=[finding],
        )
        
        result3 = ObservationResult(
            observation_id="obs-20260427140000",
            project_id="test-project",
            started_at="2026-04-27T14:00:00",
            findings=[finding],
        )
        
        save_observation_result(result1, tmp_path)
        save_observation_result(result2, tmp_path)
        save_observation_result(result3, tmp_path)
        
        ids = list_observation_results(tmp_path)
        
        assert len(ids) == 3
        assert ids[0] == "obs-20260427140000"
        assert ids[1] == "obs-20260427120000"
        assert ids[2] == "obs-20260427100000"

    def test_get_latest_observation_result(self, tmp_path: Path):
        finding = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.STALLED_EXECUTION,
            severity=FindingSeverity.HIGH,
            reason="Test",
        )
        
        old_result = ObservationResult(
            observation_id="obs-20260427100000",
            project_id="test-project",
            started_at="2026-04-27T10:00:00",
            findings=[finding],
        )
        
        new_result = ObservationResult(
            observation_id="obs-20260427150000",
            project_id="test-project",
            started_at="2026-04-27T15:00:00",
            findings=[finding],
        )
        
        save_observation_result(old_result, tmp_path)
        save_observation_result(new_result, tmp_path)
        
        latest = get_latest_observation_result(tmp_path)
        
        assert latest is not None
        assert latest.observation_id == "obs-20260427150000"

    def test_get_cumulative_findings_aggregates(self, tmp_path: Path):
        finding1 = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.BLOCKED_STATE,
            severity=FindingSeverity.HIGH,
            reason="Finding 1",
        )
        
        finding2 = ObserverFinding(
            finding_id="find-002",
            finding_type=ObserverFindingType.RUN_TIMEOUT,
            severity=FindingSeverity.CRITICAL,
            reason="Finding 2",
        )
        
        finding3 = ObserverFinding(
            finding_id="find-003",
            finding_type=ObserverFindingType.DECISION_OVERDUE,
            severity=FindingSeverity.MEDIUM,
            reason="Finding 3",
        )
        
        result1 = ObservationResult(
            observation_id="obs-20260427100000",
            project_id="test-project",
            started_at="2026-04-27T10:00:00",
            findings=[finding1, finding2],
        )
        
        result2 = ObservationResult(
            observation_id="obs-20260427120000",
            project_id="test-project",
            started_at="2026-04-27T12:00:00",
            findings=[finding3],
        )
        
        save_observation_result(result1, tmp_path)
        save_observation_result(result2, tmp_path)
        
        cumulative = get_cumulative_findings(tmp_path, limit=2)
        
        assert len(cumulative) == 3
        assert any(f.finding_type == ObserverFindingType.BLOCKED_STATE for f in cumulative)
        assert any(f.finding_type == ObserverFindingType.RUN_TIMEOUT for f in cumulative)
        assert any(f.finding_type == ObserverFindingType.DECISION_OVERDUE for f in cumulative)

    def test_load_nonexistent_returns_none(self, tmp_path: Path):
        loaded = load_observation_result(tmp_path, "obs-nonexistent")
        
        assert loaded is None

    def test_list_empty_directory_returns_empty_list(self, tmp_path: Path):
        ids = list_observation_results(tmp_path)
        
        assert ids == []

    def test_latest_empty_directory_returns_none(self, tmp_path: Path):
        latest = get_latest_observation_result(tmp_path)
        
        assert latest is None


class TestArtifactRouterObserverPaths:
    """Tests for C-007: Artifact router observer path functions."""

    def test_get_observer_findings_path_returns_correct_path(self, tmp_path: Path):
        path = get_observer_findings_path(tmp_path, "obs-20260427120000")
        
        assert path == tmp_path / "observer-findings" / "obs-20260427120000.md"

    def test_get_observer_findings_dir_returns_correct_path(self, tmp_path: Path):
        path = get_observer_findings_dir(tmp_path)
        
        assert path == tmp_path / "observer-findings"

    def test_observer_findings_is_orchestration_owned(self):
        from runtime.artifact_router import ArtifactType, is_orchestration_owned
        
        assert is_orchestration_owned(ArtifactType.OBSERVER_FINDINGS)


class TestRunObserverIntegration:
    """Tests for run_observer integration with persistence."""

    def test_run_observer_persists_by_default(self, tmp_path: Path):
        runstate_content = """# RunState
```yaml
project_id: test-project
current_phase: blocked
blocked_items: ["missing decision"]
updated_at: '2026-04-27T12:00:00'
```
"""
        runstate_path = tmp_path / "runstate.md"
        runstate_path.write_text(runstate_content)
        
        from runtime.execution_observer import run_observer
        
        result = run_observer(tmp_path)
        
        findings_dir = tmp_path / "observer-findings"
        assert findings_dir.exists()
        
        files = list(findings_dir.glob("*.md"))
        assert len(files) >= 1

    def test_run_observer_skip_persist(self, tmp_path: Path):
        runstate_content = """# RunState
```yaml
project_id: test-project
current_phase: executing
updated_at: '2026-04-27T12:00:00'
```
"""
        runstate_path = tmp_path / "runstate.md"
        runstate_path.write_text(runstate_content)
        
        from runtime.execution_observer import run_observer
        
        result = run_observer(tmp_path, persist=False)
        
        findings_dir = tmp_path / "observer-findings"
        assert not findings_dir.exists()