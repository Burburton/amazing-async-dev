"""Tests for Execution Observer Foundation - Feature 067."""

import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import yaml

import pytest

from runtime.execution_observer import (
    ObserverFindingType,
    FindingSeverity,
    ObserverFinding,
    ObservationResult,
    ExecutionObserver,
    run_observer,
)


class TestObserverFindingType:
    def test_finding_type_enum_values(self):
        assert ObserverFindingType.RUN_TIMEOUT.value == "run_timeout"
        assert ObserverFindingType.VERIFICATION_STALL.value == "verification_stall"
        assert ObserverFindingType.CLOSEOUT_STALL.value == "closeout_stall"
        assert ObserverFindingType.MISSING_EXECUTION_RESULT.value == "missing_execution_result"
        assert ObserverFindingType.RECOVERY_OVERDUE.value == "recovery_overdue"
        assert ObserverFindingType.DECISION_OVERDUE.value == "decision_overdue"
        assert ObserverFindingType.BLOCKED_STATE.value == "blocked_state"
        assert ObserverFindingType.STALLED_EXECUTION.value == "stalled_execution"


class TestFindingSeverity:
    def test_severity_enum_values(self):
        assert FindingSeverity.CRITICAL.value == "critical"
        assert FindingSeverity.HIGH.value == "high"
        assert FindingSeverity.MEDIUM.value == "medium"
        assert FindingSeverity.LOW.value == "low"
        assert FindingSeverity.INFO.value == "info"


class TestObserverFinding:
    def test_finding_creation(self):
        finding = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.STALLED_EXECUTION,
            severity=FindingSeverity.HIGH,
            reason="No progress for 300 seconds",
        )
        
        assert finding.finding_id == "find-001"
        assert finding.finding_type == ObserverFindingType.STALLED_EXECUTION
        assert finding.severity == FindingSeverity.HIGH
        assert finding.resolved is False
    
    def test_finding_to_dict(self):
        finding = ObserverFinding(
            finding_id="find-002",
            finding_type=ObserverFindingType.BLOCKED_STATE,
            severity=FindingSeverity.CRITICAL,
            project_id="test-project",
            reason="Network unavailable",
            suggested_action="Resolve blocker",
            suggested_command="asyncdev recovery resume --action unblock",
        )
        
        data = finding.to_dict()
        
        assert data["finding_id"] == "find-002"
        assert data["finding_type"] == "blocked_state"
        assert data["severity"] == "critical"
        assert data["project_id"] == "test-project"
        assert data["recovery_significant"] is False
    
    def test_finding_resolution(self):
        finding = ObserverFinding(
            finding_id="find-003",
            finding_type=ObserverFindingType.CLOSEOUT_STALL,
            severity=FindingSeverity.HIGH,
            reason="Closeout timeout",
        )
        
        finding.resolved = True
        finding.resolved_at = datetime.now().isoformat()
        finding.resolution_action = "Retry closeout"
        
        assert finding.resolved
        assert finding.resolution_action == "Retry closeout"


class TestObservationResult:
    def test_result_creation(self):
        result = ObservationResult(
            observation_id="obs-001",
            project_id="test-project",
            started_at=datetime.now().isoformat(),
        )
        
        assert result.observation_id == "obs-001"
        assert result.project_id == "test-project"
        assert len(result.findings) == 0
    
    def test_result_with_findings(self):
        finding1 = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.STALLED_EXECUTION,
            severity=FindingSeverity.HIGH,
            reason="No progress",
        )
        
        finding2 = ObserverFinding(
            finding_id="find-002",
            finding_type=ObserverFindingType.RECOVERY_OVERDUE,
            severity=FindingSeverity.CRITICAL,
            reason="Critical failure",
            recovery_significant=True,
        )
        
        result = ObservationResult(
            observation_id="obs-002",
            project_id="test-project",
            started_at=datetime.now().isoformat(),
            findings=[finding1, finding2],
        )
        
        assert len(result.findings) == 2
        assert result.has_critical_findings() is True
    
    def test_result_to_dict(self):
        finding = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.RECOVERY_OVERDUE,
            severity=FindingSeverity.HIGH,
            reason="Recovery needed",
        )
        
        result = ObservationResult(
            observation_id="obs-003",
            project_id="test-project",
            started_at="2026-01-01T10:00:00",
            finished_at="2026-01-01T10:00:05",
            findings=[finding],
            summary="Detected 1 findings",
        )
        
        data = result.to_dict()
        
        assert data["observation_id"] == "obs-003"
        assert data["findings_count"] == 1
        assert data["summary"] == "Detected 1 findings"
    
    def test_has_recovery_required(self):
        finding1 = ObserverFinding(
            finding_id="find-001",
            finding_type=ObserverFindingType.RECOVERY_OVERDUE,
            severity=FindingSeverity.HIGH,
            reason="Recovery needed",
            recovery_significant=True,
        )
        
        result = ObservationResult(
            observation_id="obs-004",
            project_id="test-project",
            started_at=datetime.now().isoformat(),
            findings=[finding1],
        )
        
        assert result.has_recovery_significant()


class TestExecutionObserver:
    def test_observer_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            observer = ExecutionObserver(project_path)
            
            assert observer.project_path == project_path
            assert len(observer.findings) == 0
    
    def test_observer_empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            observer = ExecutionObserver(project_path)
            
            result = observer.observe()
            
            assert len(result.findings) == 0
            assert "No issues detected" in result.summary
    
    def test_observer_blocked_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            runstate_content = """# RunState

```yaml
project_id: test-project
feature_id: test-feature
current_phase: blocked
blocked_items:
- Network unavailable
updated_at: '2026-01-01T10:00:00'
```
"""
            (project_path / "runstate.md").write_text(runstate_content)
            
            observer = ExecutionObserver(project_path)
            result = observer.observe()
            
            blocked_findings = [f for f in result.findings if f.finding_type == ObserverFindingType.BLOCKED_STATE]
            assert len(blocked_findings) >= 1
    
    def test_observer_failed_execution_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            failed_result = {
                "execution_id": "exec-001",
                "status": "failed",
                "verification_type": "backend_only",
            }
            
            content = f"""# ExecutionResult

```yaml
{yaml.dump(failed_result, default_flow_style=False)}
```
"""
            (results_dir / "exec-001.md").write_text(content)
            
            observer = ExecutionObserver(project_path)
            result = observer.observe()
            
            recovery_findings = [f for f in result.findings if f.finding_type == ObserverFindingType.RECOVERY_OVERDUE]
            assert len(recovery_findings) >= 1
    
    def test_observer_verification_not_executed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            result_data = {
                "execution_id": "exec-002",
                "status": "success",
                "verification_type": "frontend_interactive",
                "browser_verification": {
                    "executed": False,
                },
            }
            
            content = f"""# ExecutionResult

```yaml
{yaml.dump(result_data, default_flow_style=False)}
```
"""
            (results_dir / "exec-002.md").write_text(content)
            
            observer = ExecutionObserver(project_path)
            result = observer.observe()
            
            verification_findings = [f for f in result.findings if f.finding_type == ObserverFindingType.VERIFICATION_STALL]
            assert len(verification_findings) >= 1
    
    def test_observer_closeout_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            results_dir = project_path / "execution-results"
            results_dir.mkdir(parents=True)
            
            result_data = {
                "execution_id": "exec-003",
                "status": "partial",
                "closeout_state": "closeout_timeout",
            }
            
            content = f"""# ExecutionResult

```yaml
{yaml.dump(result_data, default_flow_style=False)}
```
"""
            (results_dir / "exec-003.md").write_text(content)
            
            observer = ExecutionObserver(project_path)
            result = observer.observe()
            
            timeout_findings = [f for f in result.findings if f.finding_type == ObserverFindingType.CLOSEOUT_STALL]
            assert len(timeout_findings) >= 1


class TestRunObserver:
    def test_run_observer_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result = run_observer(project_path)
            
            assert isinstance(result, ObservationResult)
            assert result.project_id == project_path.name


class TestObserverThresholds:
    def test_stalled_threshold_defined(self):
        assert ExecutionObserver.STALLED_THRESHOLD_SECONDS == 300
    
    def test_timeout_threshold_defined(self):
        assert ExecutionObserver.TIMEOUT_THRESHOLD_SECONDS == 120
    
    def test_decision_overdue_threshold_defined(self):
        assert ExecutionObserver.DECISION_OVERDUE_THRESHOLD_SECONDS == 3600