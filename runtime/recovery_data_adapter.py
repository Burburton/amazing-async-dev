"""Recovery Data Adapter - Feature 066a.

Canonical adapter layer that aggregates recovery-relevant data from async-dev state.
Provides normalized recovery items for Recovery Console consumption.

Per 066a Section 6.1:
- Aggregates run metadata, execution result, recovery state
- Integrates verification/closeout state
- Includes observer findings
- Normalizes recovery category, suggested action
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.state_store import StateStore
from runtime.recovery_classifier import (
    classify_recovery,
    get_recovery_guidance,
    RecoveryClassification,
)
from runtime.execution_observer import (
    run_observer,
    ObserverFinding,
    ObservationResult,
)


@dataclass
class RecoveryItem:
    """Normalized recovery item model for Recovery Console (066a Section 7.2)."""
    
    run_id: str
    execution_id: str
    product_id: str
    feature_id: str
    
    title: str = ""
    status: str = ""
    phase: str = ""
    
    recovery_required: bool = False
    recovery_reason: str = ""
    recovery_category: str = ""
    
    suggested_action: str = ""
    suggested_command: str = ""
    
    verification_status: str = "unknown"
    closeout_status: str = "unknown"
    
    observer_findings: list[ObserverFinding] = field(default_factory=list)
    linked_artifacts: list[str] = field(default_factory=list)
    
    blocked_items: list[str] = field(default_factory=list)
    decisions_needed: list[Any] = field(default_factory=list)
    
    last_updated_at: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "execution_id": self.execution_id,
            "product_id": self.product_id,
            "feature_id": self.feature_id,
            "title": self.title,
            "status": self.status,
            "phase": self.phase,
            "recovery_required": self.recovery_required,
            "recovery_reason": self.recovery_reason,
            "recovery_category": self.recovery_category,
            "suggested_action": self.suggested_action,
            "suggested_command": self.suggested_command,
            "verification_status": self.verification_status,
            "closeout_status": self.closeout_status,
            "observer_findings_count": len(self.observer_findings),
            "observer_findings": [f.to_dict() for f in self.observer_findings],
            "linked_artifacts": self.linked_artifacts,
            "blocked_items_count": len(self.blocked_items),
            "decisions_needed_count": len(self.decisions_needed),
            "last_updated_at": self.last_updated_at,
        }


class RecoveryDataAdapter:
    """Canonical adapter for Recovery Console data (066a AC-001).
    
    Reads from async-dev canonical state sources:
    - RunState (current execution state)
    - ExecutionResult artifacts
    - Observer findings (Feature 067)
    
    Provides normalized RecoveryItems for console consumption.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.state_store = StateStore(project_path)
    
    def get_recovery_item(self) -> RecoveryItem | None:
        """Get recovery item for project from canonical state.
        
        Returns None if project has no RunState or is in healthy state.
        """
        runstate = self.state_store.load_runstate()
        
        if runstate is None:
            return None
        
        classification = classify_recovery(runstate)
        
        recovery_needed_classifications = [
            RecoveryClassification.BLOCKED,
            RecoveryClassification.FAILED,
            RecoveryClassification.AWAITING_DECISION,
            RecoveryClassification.UNSAFE_TO_RESUME,
        ]
        
        if classification not in recovery_needed_classifications:
            return None
        
        guidance = get_recovery_guidance(runstate)
        
        product_id = runstate.get("project_id", self.project_path.name)
        feature_id = runstate.get("feature_id", "")
        execution_id = f"exec-{product_id}-{feature_id}"
        
        run_id = f"run-{product_id}-{feature_id}"
        
        title = f"{product_id}/{feature_id}"
        
        phase = runstate.get("current_phase", "")
        status = classification.value
        
        recovery_required = True
        recovery_reason = guidance.get("explanation", "")
        
        recovery_category = self._map_category(classification)
        
        suggested_action = guidance.get("recommended_action", "")
        
        suggested_command = self._derive_command(classification, execution_id)
        
        verification_status = self._check_verification_status()
        closeout_status = self._check_closeout_status()
        
        linked_artifacts = self._collect_artifacts()
        
        blocked_items = runstate.get("blocked_items", [])
        decisions_needed = runstate.get("decisions_needed", [])
        
        last_updated_at = runstate.get("updated_at", "")
        
        return RecoveryItem(
            run_id=run_id,
            execution_id=execution_id,
            product_id=product_id,
            feature_id=feature_id,
            title=title,
            status=status,
            phase=phase,
            recovery_required=recovery_required,
            recovery_reason=recovery_reason,
            recovery_category=recovery_category,
            suggested_action=suggested_action,
            suggested_command=suggested_command,
            verification_status=verification_status,
            closeout_status=closeout_status,
            linked_artifacts=linked_artifacts,
            blocked_items=blocked_items,
            decisions_needed=decisions_needed,
            last_updated_at=last_updated_at,
        )
    
    def get_recovery_item_with_observer(self) -> RecoveryItem | None:
        """Get recovery item including observer findings (066a AC-002)."""
        item = self.get_recovery_item()
        
        if item is None:
            return None
        
        obs_result = run_observer(self.project_path)
        
        item.observer_findings = obs_result.findings
        
        recovery_sig_findings = [f for f in obs_result.findings if f.recovery_significant]
        if recovery_sig_findings:
            item.recovery_required = True
            if not item.recovery_reason:
                item.recovery_reason = f"{len(recovery_sig_findings)} recovery-significant findings"
        
        for f in obs_result.findings[:3]:
            if f.related_artifacts:
                for artifact in f.related_artifacts:
                    if artifact not in item.linked_artifacts:
                        item.linked_artifacts.append(artifact)
        
        return item
    
    def _map_category(self, classification: RecoveryClassification) -> str:
        """Map RecoveryClassification to recovery category (066a Section 7.2)."""
        category_map = {
            RecoveryClassification.BLOCKED: "blocked",
            RecoveryClassification.FAILED: "failed",
            RecoveryClassification.AWAITING_DECISION: "decision_blocked",
            RecoveryClassification.UNSAFE_TO_RESUME: "manual_investigation",
        }
        return category_map.get(classification, "unknown")
    
    def _derive_command(self, classification: RecoveryClassification, execution_id: str) -> str:
        """Derive async-dev command for recovery action (066a AC-003)."""
        command_map = {
            RecoveryClassification.BLOCKED: f"asyncdev resume-next-day unblock --execution {execution_id}",
            RecoveryClassification.FAILED: f"asyncdev recovery resume --execution {execution_id} --action retry",
            RecoveryClassification.AWAITING_DECISION: f"asyncdev decision reply --request <request_id> --command DECISION A",
            RecoveryClassification.UNSAFE_TO_RESUME: f"asyncdev inspect-stop --execution {execution_id}",
        }
        return command_map.get(classification, f"asyncdev recovery show --execution {execution_id}")
    
    def _check_verification_status(self) -> str:
        """Check verification status from execution results."""
        results_dir = self.project_path / "execution-results"
        
        if not results_dir.exists():
            return "no_results"
        
        result_files = list(results_dir.glob("*.md"))
        
        if not result_files:
            return "no_results"
        
        latest_result = result_files[-1]
        content = latest_result.read_text(encoding="utf-8")
        
        if "browser_verification" in content:
            if "executed: true" in content.lower():
                if "passed" in content.lower():
                    return "verified"
                else:
                    return "failed"
            else:
                return "pending"
        
        if "verification_type: backend_only" in content.lower():
            return "not_required"
        
        return "unknown"
    
    def _check_closeout_status(self) -> str:
        """Check closeout status from execution results."""
        results_dir = self.project_path / "execution-results"
        
        if not results_dir.exists():
            return "no_results"
        
        result_files = list(results_dir.glob("*.md"))
        
        if not result_files:
            return "no_results"
        
        latest_result = result_files[-1]
        content = latest_result.read_text(encoding="utf-8")
        
        if "closeout_state" in content:
            if "closeout_completed_success" in content.lower():
                return "completed"
            elif "closeout_timeout" in content.lower():
                return "timeout"
            elif "recovery_required" in content.lower():
                return "recovery_needed"
            else:
                return "in_progress"
        
        if "status: success" in content.lower():
            return "completed"
        
        return "unknown"
    
    def _collect_artifacts(self) -> list[str]:
        """Collect linked artifacts from canonical sources (066a AC-004)."""
        artifacts = []
        
        runstate_path = self.project_path / "runstate.md"
        if runstate_path.exists():
            artifacts.append(str(runstate_path))
        
        execution_packs_dir = self.project_path / "execution-packs"
        if execution_packs_dir.exists():
            packs = sorted(execution_packs_dir.glob("*.md"))
            if packs:
                artifacts.append(str(packs[-1]))
        
        execution_results_dir = self.project_path / "execution-results"
        if execution_results_dir.exists():
            results = sorted(execution_results_dir.glob("*.md"))
            if results:
                artifacts.append(str(results[-1]))
        
        return artifacts


def get_recovery_item_for_project(project_path: Path, include_observer: bool = True) -> RecoveryItem | None:
    """Convenience function to get recovery item for a project."""
    adapter = RecoveryDataAdapter(project_path)
    
    if include_observer:
        return adapter.get_recovery_item_with_observer()
    
    return adapter.get_recovery_item()