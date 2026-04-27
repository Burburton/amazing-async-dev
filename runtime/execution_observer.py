"""Execution Observer Foundation - Feature 067.

Provides execution supervision layer for async-dev platform.

Observer watches work:
- Periodic inspection of active executions
- Detection of stall/timeout/missing-artifact conditions
- Structured findings for downstream consumption
- Recommended actions for recovery workflows

This foundation enables later operator surfaces (Recovery Console, etc).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ObserverFindingType(str, Enum):
    """Types of findings the observer can detect (per Feature 067 AC-004)."""
    
    # Core anomaly types (067 spec)
    RUN_TIMEOUT = "run_timeout"
    VERIFICATION_STALL = "verification_stall"
    CLOSEOUT_STALL = "closeout_stall"
    MISSING_EXECUTION_RESULT = "missing_execution_result"
    RECOVERY_OVERDUE = "recovery_overdue"
    DECISION_OVERDUE = "decision_overdue"
    
    # Additional useful types
    BLOCKED_STATE = "blocked_state"
    STALLED_EXECUTION = "stalled_execution"
    
    # Acceptance readiness types (Feature 070)
    ACCEPTANCE_READY = "acceptance_ready"
    ACCEPTANCE_BLOCKED = "acceptance_blocked"
    ACCEPTANCE_OVERDUE = "acceptance_overdue"


class FindingSeverity(str, Enum):
    """Severity levels for observer findings."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ObserverFinding:
    """Single finding from execution observation.
    
    Captures an anomaly or issue detected during execution monitoring.
    """
    
    finding_id: str
    finding_type: ObserverFindingType
    severity: FindingSeverity
    execution_id: str | None = None
    project_id: str | None = None
    feature_id: str | None = None
    
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    
    suggested_action: str = ""
    suggested_command: str = ""
    
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    related_artifacts: list[str] = field(default_factory=list)
    
    resolved: bool = False
    resolved_at: str | None = None
    resolution_action: str | None = None
    
    recovery_significant: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type.value,
            "severity": self.severity.value,
            "execution_id": self.execution_id,
            "project_id": self.project_id,
            "feature_id": self.feature_id,
            "reason": self.reason,
            "details": self.details,
            "suggested_action": self.suggested_action,
            "suggested_command": self.suggested_command,
            "detected_at": self.detected_at,
            "related_artifacts": self.related_artifacts,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "resolution_action": self.resolution_action,
            "recovery_significant": self.recovery_significant,
        }
    
    def is_recovery_significant(self) -> bool:
        return self.recovery_significant


@dataclass
class ObservationResult:
    """Result of execution observation run.
    
    Contains all findings detected in a single observation pass.
    """
    
    observation_id: str
    project_id: str
    started_at: str
    finished_at: str | None = None
    
    findings: list[ObserverFinding] = field(default_factory=list)
    
    execution_state_analyzed: bool = False
    artifacts_checked: bool = False
    verification_state_checked: bool = False
    closeout_state_checked: bool = False
    acceptance_readiness_checked: bool = False
    
    summary: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "project_id": self.project_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "execution_state_analyzed": self.execution_state_analyzed,
            "artifacts_checked": self.artifacts_checked,
            "verification_state_checked": self.verification_state_checked,
            "closeout_state_checked": self.closeout_state_checked,
            "acceptance_readiness_checked": self.acceptance_readiness_checked,
            "summary": self.summary,
        }
    
    def has_critical_findings(self) -> bool:
        return any(f.severity == FindingSeverity.CRITICAL for f in self.findings)
    
    def has_recovery_significant(self) -> bool:
        return any(f.recovery_significant for f in self.findings)
    
    def has_recovery_required(self) -> bool:
        return any(f.finding_type == ObserverFindingType.RECOVERY_OVERDUE for f in self.findings)


class ExecutionObserver:
    """Observer that monitors async-dev execution state.
    
    Scans execution artifacts and state to detect anomalies requiring attention.
    """
    
    STALLED_THRESHOLD_SECONDS = 300  # 5 minutes no progress = stalled
    TIMEOUT_THRESHOLD_SECONDS = 120  # 2 minutes over expected = timeout
    DECISION_OVERDUE_THRESHOLD_SECONDS = 3600  # 1 hour waiting = overdue
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.findings: list[ObserverFinding] = []
    
    def observe(self) -> ObservationResult:
        """Run observation on project execution state.
        
        Returns ObservationResult with all detected findings.
        """
        observation_id = f"obs-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        started_at = datetime.now().isoformat()
        
        self.findings = []
        
        self._check_execution_state()
        self._check_artifacts()
        self._check_verification_state()
        self._check_closeout_state()
        self._check_decisions()
        self._check_acceptance_readiness()
        
        finished_at = datetime.now().isoformat()
        
        summary = self._generate_summary()
        
        return ObservationResult(
            observation_id=observation_id,
            project_id=self.project_path.name,
            started_at=started_at,
            finished_at=finished_at,
            findings=self.findings,
            execution_state_analyzed=True,
            artifacts_checked=True,
            verification_state_checked=True,
            closeout_state_checked=True,
            acceptance_readiness_checked=True,
            summary=summary,
        )
    
    def _check_execution_state(self) -> None:
        from runtime.state_store import StateStore
        
        store = StateStore(self.project_path)
        runstate = store.load_runstate()
        
        if runstate is None:
            return
        
        phase = runstate.get("current_phase", "")
        blocked_items = runstate.get("blocked_items", [])
        updated_at_str = runstate.get("updated_at", "")
        
        if phase == "blocked" and blocked_items:
            self._add_finding(
                finding_type=ObserverFindingType.BLOCKED_STATE,
                severity=FindingSeverity.HIGH,
                reason=f"Execution blocked: {blocked_items}",
                suggested_action="Resolve blocker before continuing",
                suggested_command="asyncdev recovery show --execution <id>",
            )
        
        if phase == "executing" and updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
                elapsed = (datetime.now() - updated_at).total_seconds()
                
                if elapsed > self.STALLED_THRESHOLD_SECONDS:
                    self._add_finding(
                        finding_type=ObserverFindingType.STALLED_EXECUTION,
                        severity=FindingSeverity.HIGH,
                        reason=f"No progress for {elapsed:.0f} seconds",
                        details={"elapsed_seconds": elapsed},
                        suggested_action="Inspect execution state",
                        suggested_command="asyncdev recovery show --execution <id>",
                    )
            except (ValueError, TypeError):
                pass
    
    def _check_artifacts(self) -> None:
        results_dir = self.project_path / "execution-results"
        
        if not results_dir.exists():
            return
        
        result_files = list(results_dir.glob("*.md"))
        
        for result_file in result_files:
            content = result_file.read_text(encoding="utf-8")
            
            if "status: failed" in content.lower():
                self._add_finding(
                    finding_type=ObserverFindingType.RECOVERY_OVERDUE,
                    severity=FindingSeverity.HIGH,
                    reason="Execution result shows failure status",
                    suggested_action="Review failure details and decide recovery path",
                    suggested_command="asyncdev recovery show --execution <id>",
                    related_artifacts=[str(result_file)],
                    recovery_significant=True,
                )
    
    def _check_verification_state(self) -> None:
        results_dir = self.project_path / "execution-results"
        
        if not results_dir.exists():
            return
        
        for result_file in results_dir.glob("*.md"):
            content = result_file.read_text(encoding="utf-8")
            
            if "browser_verification" in content and "executed: false" in content.lower():
                if "frontend_interactive" in content or "frontend_visual" in content:
                    self._add_finding(
                        finding_type=ObserverFindingType.VERIFICATION_STALL,
                        severity=FindingSeverity.MEDIUM,
                        reason="Frontend verification not executed",
                        suggested_action="Run frontend verification",
                        suggested_command="asyncdev verification retry --execution <id>",
                        related_artifacts=[str(result_file)],
                        recovery_significant=True,
                    )
    
    def _check_closeout_state(self) -> None:
        results_dir = self.project_path / "execution-results"
        
        if not results_dir.exists():
            return
        
        for result_file in results_dir.glob("*.md"):
            content = result_file.read_text(encoding="utf-8")
            
            if "closeout_state" in content and "timeout" in content.lower():
                self._add_finding(
                    finding_type=ObserverFindingType.CLOSEOUT_STALL,
                    severity=FindingSeverity.HIGH,
                    reason="Closeout timed out",
                    suggested_action="Retry closeout or manual inspection",
                    suggested_command="asyncdev recovery resume --execution <id> --action retry",
                    related_artifacts=[str(result_file)],
                    recovery_significant=True,
                )
            
            if "closeout_state" in content and "recovery_required" in content.lower():
                self._add_finding(
                    finding_type=ObserverFindingType.CLOSEOUT_STALL,
                    severity=FindingSeverity.HIGH,
                    reason="Closeout incomplete, recovery required",
                    suggested_action="Complete closeout manually",
                    suggested_command="asyncdev recovery show --execution <id>",
                    related_artifacts=[str(result_file)],
                    recovery_significant=True,
                )
    
    def _check_decisions(self) -> None:
        from runtime.state_store import StateStore
        
        store = StateStore(self.project_path)
        runstate = store.load_runstate()
        
        if runstate is None:
            return
        
        decision_request_sent_at = runstate.get("decision_request_sent_at", "")
        
        if decision_request_sent_at:
            try:
                sent_at = datetime.fromisoformat(decision_request_sent_at)
                elapsed = (datetime.now() - sent_at).total_seconds()
                
                if elapsed > self.DECISION_OVERDUE_THRESHOLD_SECONDS:
                    self._add_finding(
                        finding_type=ObserverFindingType.DECISION_OVERDUE,
                        severity=FindingSeverity.MEDIUM,
                        reason=f"Decision pending for {elapsed:.0f} seconds",
                        details={"elapsed_seconds": elapsed},
                        suggested_action="Check decision inbox or provide reply",
                        suggested_command="asyncdev decision wait --request <id>",
                    )
            except (ValueError, TypeError):
                pass
    
    def _check_acceptance_readiness(self) -> None:
        from runtime.acceptance_readiness import check_acceptance_readiness, AcceptanceTriggerPolicyMode
        
        results_dir = self.project_path / "execution-results"
        
        if not results_dir.exists():
            return
        
        for result_file in results_dir.glob("*.md"):
            content = result_file.read_text(encoding="utf-8")
            
            execution_id = self._extract_execution_id(result_file.name)
            
            if execution_id and "status: success" in content.lower():
                try:
                    readiness_result = check_acceptance_readiness(
                        self.project_path,
                        execution_id,
                        AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY,
                    )
                    
                    if readiness_result.readiness.value == "ready":
                        self._add_finding(
                            finding_type=ObserverFindingType.ACCEPTANCE_READY,
                            severity=FindingSeverity.INFO,
                            reason="Execution ready for acceptance validation",
                            details={"prerequisites_failed": readiness_result.prerequisites_failed},
                            suggested_action="Trigger acceptance validation",
                            suggested_command="asyncdev acceptance trigger --execution <id>",
                            related_artifacts=[str(result_file)],
                        )
                    elif readiness_result.readiness.value == "blocked":
                        self._add_finding(
                            finding_type=ObserverFindingType.ACCEPTANCE_BLOCKED,
                            severity=FindingSeverity.HIGH,
                            reason="Acceptance blocked by missing prerequisites",
                            details={"prerequisites_failed": readiness_result.prerequisites_failed, "blocking_reasons": readiness_result.blocking_reasons},
                            suggested_action="Resolve blockers before acceptance",
                            suggested_command="asyncdev recovery show --execution <id>",
                            related_artifacts=[str(result_file)],
                            recovery_significant=True,
                        )
                except Exception:
                    pass
    
    def _extract_execution_id(self, filename: str) -> str | None:
        if filename.endswith(".md"):
            return filename[:-3]
        return None
    
    def _add_finding(
        self,
        finding_type: ObserverFindingType,
        severity: FindingSeverity,
        reason: str,
        suggested_action: str = "",
        suggested_command: str = "",
        details: dict[str, Any] = {},
        related_artifacts: list[str] = [],
        recovery_significant: bool = False,
    ) -> None:
        from runtime.state_store import StateStore
        
        store = StateStore(self.project_path)
        runstate = store.load_runstate() or {}
        
        finding_id = f"find-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.findings)}"
        
        finding = ObserverFinding(
            finding_id=finding_id,
            finding_type=finding_type,
            severity=severity,
            execution_id=runstate.get("active_task", ""),
            project_id=runstate.get("project_id", self.project_path.name),
            feature_id=runstate.get("feature_id", ""),
            reason=reason,
            details=details,
            suggested_action=suggested_action,
            suggested_command=suggested_command,
            related_artifacts=related_artifacts,
            recovery_significant=recovery_significant,
        )
        
        self.findings.append(finding)
    
    def _generate_summary(self) -> str:
        if not self.findings:
            return "No issues detected. Execution state appears healthy."
        
        critical = sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)
        high = sum(1 for f in self.findings if f.severity == FindingSeverity.HIGH)
        medium = sum(1 for f in self.findings if f.severity == FindingSeverity.MEDIUM)
        
        return f"Detected {len(self.findings)} findings: {critical} critical, {high} high, {medium} medium"


def run_observer(project_path: Path, persist: bool = True) -> ObservationResult:
    """Run observation on a project, optionally persisting result.
    
    Args:
        project_path: Path to project directory
        persist: Whether to persist findings to disk (default True)
        
    Returns:
        ObservationResult with all detected findings
    """
    observer = ExecutionObserver(project_path)
    result = observer.observe()
    
    if persist:
        from runtime.observer_finding_store import save_observation_result
        save_observation_result(result, project_path)
    
    return result