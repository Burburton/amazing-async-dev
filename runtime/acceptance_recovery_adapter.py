"""Acceptance Recovery Adapter - Feature 078.

Adapter that summarizes acceptance state for Recovery Console consumption.
Provides normalized acceptance recovery data for operator visibility.

Integration with:
- Feature 072 (AcceptanceRecovery)
- Feature 073 (ReAcceptanceLoop)
- Feature 074 (AcceptanceConsole)
- Feature 066a (RecoveryDataAdapter)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.acceptance_runner import (
    load_acceptance_result,
    AcceptanceTerminalState,
)
from runtime.acceptance_pack_builder import load_acceptance_pack
from runtime.acceptance_recovery import (
    get_recovery_items_for_feature,
    RecoveryCategory,
    RecoveryPriority,
)
from runtime.acceptance_gating import check_completion_gate, CompletionGateResult
from runtime.reacceptance_loop import load_attempt_history, get_acceptance_lineage
from runtime.recovery_classifier import RecoveryClassification


class AcceptanceRecoveryCategory(str):
    """Categories for acceptance-related recovery in Recovery Console."""
    
    ACCEPTANCE_FAILED = "acceptance_failed"
    ACCEPTANCE_BLOCKED = "acceptance_blocked"
    AWAITING_ACCEPTANCE = "awaiting_acceptance"
    REACCEPTANCE_REQUIRED = "reacceptance_required"
    ACCEPTANCE_ESCALATION_NEEDED = "acceptance_escalation_needed"
    CONDITIONAL_ACCEPTANCE = "conditional_acceptance"


@dataclass
class AcceptanceRecoverySummary:
    """Summary of acceptance state for Recovery Console (Feature 078 AC-001)."""
    
    latest_status: str = "no_acceptance"
    attempt_count: int = 0
    latest_terminal_state: str = ""
    latest_failed_criteria: list[str] = field(default_factory=list)
    latest_remediation_summary: list[dict[str, Any]] = field(default_factory=list)
    
    is_blocking_completion: bool = False
    completion_gate_result: str = ""
    needs_reacceptance: bool = False
    reacceptance_required_reason: str = ""
    
    recommended_action: str = ""
    suggested_command: str = ""
    
    acceptance_result_id: str = ""
    acceptance_recovery_pack_id: str = ""
    
    recovery_significant: bool = False
    recovery_category: str = ""
    recovery_priority: str = ""
    
    validated_at: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "latest_status": self.latest_status,
            "attempt_count": self.attempt_count,
            "latest_terminal_state": self.latest_terminal_state,
            "latest_failed_criteria": self.latest_failed_criteria,
            "latest_remediation_summary": self.latest_remediation_summary,
            "is_blocking_completion": self.is_blocking_completion,
            "completion_gate_result": self.completion_gate_result,
            "needs_reacceptance": self.needs_reacceptance,
            "reacceptance_required_reason": self.reacceptance_required_reason,
            "recommended_action": self.recommended_action,
            "suggested_command": self.suggested_command,
            "acceptance_result_id": self.acceptance_result_id,
            "acceptance_recovery_pack_id": self.acceptance_recovery_pack_id,
            "recovery_significant": self.recovery_significant,
            "recovery_category": self.recovery_category,
            "recovery_priority": self.recovery_priority,
            "validated_at": self.validated_at,
            "checked_at": self.checked_at,
        }


class AcceptanceRecoveryAdapter:
    """Adapter for acceptance recovery data in Recovery Console (Feature 078).
    
    Consumes canonical acceptance artifacts:
    - AcceptanceResult (Feature 069)
    - AcceptanceRecoveryPack (Feature 072)
    - AttemptHistory (Feature 073)
    - CompletionGate (Feature 075)
    
    Produces AcceptanceRecoverySummary for Recovery Console consumption.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def get_acceptance_recovery_summary(
        self,
        feature_id: str,
        runstate: dict[str, Any] | None = None,
    ) -> AcceptanceRecoverySummary:
        """Get acceptance recovery summary for a feature (Feature 078 AC-002)."""
        
        lineage = get_acceptance_lineage(self.project_path, feature_id)
        attempt_count = sum(e.get("total_attempts", 0) for e in lineage)
        
        latest_result_id = ""
        latest_terminal_state = ""
        latest_failed_criteria: list[str] = []
        latest_remediation_summary: list[dict[str, Any]] = []
        validated_at = ""
        
        acceptance_results_dir = self.project_path / "acceptance-results"
        if acceptance_results_dir.exists():
            results = sorted(
                acceptance_results_dir.glob("*.md"),
                key=lambda r: r.stat().st_mtime,
                reverse=True,
            )
            
            if results:
                latest_result = load_acceptance_result(self.project_path, results[0].stem)
                if latest_result:
                    latest_result_id = latest_result.acceptance_result_id
                    latest_terminal_state = latest_result.terminal_state.value
                    latest_failed_criteria = latest_result.failed_criteria
                    validated_at = latest_result.validated_at
                    
                    for remediation in latest_result.remediation_guidance:
                        latest_remediation_summary.append({
                            "criterion_id": remediation.criterion_id,
                            "issue_type": remediation.issue_type,
                            "suggested_fix": remediation.suggested_fix,
                            "priority": remediation.priority,
                        })
        
        gate_check = check_completion_gate(self.project_path, feature_id)
        is_blocking_completion = not gate_check.is_allowed
        completion_gate_result = gate_check.result.value
        
        needs_reacceptance = False
        reacceptance_required_reason = ""
        
        if latest_terminal_state in ["rejected", "failure", "recovery_required"]:
            needs_reacceptance = True
            reacceptance_required_reason = "Acceptance rejected - remediation and re-validation required"
        elif is_blocking_completion and latest_terminal_state in ["manual_review", "escalated"]:
            needs_reacceptance = True
            reacceptance_required_reason = "Completion blocked - acceptance requires resolution"
        
        recovery_significant, recovery_category, recovery_priority = self._classify_recovery_significance(
            latest_terminal_state,
            is_blocking_completion,
            attempt_count,
            gate_check,
        )
        
        latest_status = self._determine_latest_status(
            latest_terminal_state,
            attempt_count,
            is_blocking_completion,
        )
        
        recommended_action, suggested_command = self._derive_action(
            latest_terminal_state,
            needs_reacceptance,
            recovery_category,
            latest_result_id,
            feature_id,
        )
        
        recovery_pack_id = ""
        acceptance_recovery_packs_dir = self.project_path / "acceptance-recovery"
        if acceptance_recovery_packs_dir.exists():
            packs = sorted(
                acceptance_recovery_packs_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if packs:
                recovery_pack_id = packs[0].stem
        
        return AcceptanceRecoverySummary(
            latest_status=latest_status,
            attempt_count=attempt_count,
            latest_terminal_state=latest_terminal_state,
            latest_failed_criteria=latest_failed_criteria,
            latest_remediation_summary=latest_remediation_summary,
            is_blocking_completion=is_blocking_completion,
            completion_gate_result=completion_gate_result,
            needs_reacceptance=needs_reacceptance,
            reacceptance_required_reason=reacceptance_required_reason,
            recommended_action=recommended_action,
            suggested_command=suggested_command,
            acceptance_result_id=latest_result_id,
            acceptance_recovery_pack_id=recovery_pack_id,
            recovery_significant=recovery_significant,
            recovery_category=recovery_category,
            recovery_priority=recovery_priority,
            validated_at=validated_at,
        )
    
    def _classify_recovery_significance(
        self,
        terminal_state: str,
        is_blocking_completion: bool,
        attempt_count: int,
        gate_check: Any,
    ) -> tuple[bool, str, str]:
        """Determine if acceptance is recovery-significant."""
        
        if not terminal_state:
            return False, "", ""
        
        recovery_significant_states = [
            "rejected",
            "failure",
            "recovery_required",
            "escalated",
            "manual_review",
        ]
        
        if terminal_state in recovery_significant_states:
            if terminal_state == "rejected" or is_blocking_completion:
                return True, AcceptanceRecoveryCategory.ACCEPTANCE_FAILED, "high"
            elif terminal_state == "escalated":
                return True, AcceptanceRecoveryCategory.ACCEPTANCE_ESCALATION_NEEDED, "critical"
            elif terminal_state == "manual_review":
                return True, AcceptanceRecoveryCategory.AWAITING_ACCEPTANCE, "high"
            elif terminal_state == "conditional":
                return True, AcceptanceRecoveryCategory.CONDITIONAL_ACCEPTANCE, "medium"
        
        if is_blocking_completion and attempt_count > 2:
            return True, AcceptanceRecoveryCategory.REACCEPTANCE_REQUIRED, "high"
        
        if gate_check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED:
            return True, AcceptanceRecoveryCategory.ACCEPTANCE_BLOCKED, "high"
        
        return False, "", ""
    
    def _determine_latest_status(
        self,
        terminal_state: str,
        attempt_count: int,
        is_blocking_completion: bool,
    ) -> str:
        """Determine latest acceptance status string."""
        
        if not terminal_state:
            if attempt_count == 0:
                return "no_acceptance"
            return "acceptance_pending"
        
        status_map = {
            "accepted": "accepted",
            "conditional": "conditional",
            "rejected": "rejected",
            "failure": "failed",
            "recovery_required": "recovery_needed",
            "manual_review": "manual_review_required",
            "escalated": "escalated",
        }
        
        base_status = status_map.get(terminal_state, terminal_state)
        
        if is_blocking_completion:
            return f"{base_status}_blocking"
        
        return base_status
    
    def _derive_action(
        self,
        terminal_state: str,
        needs_reacceptance: bool,
        recovery_category: str,
        latest_result_id: str,
        feature_id: str,
    ) -> tuple[str, str]:
        """Derive recommended action and command."""
        
        if terminal_state in ["accepted"]:
            return "No action needed - acceptance passed", ""
        
        if needs_reacceptance:
            if terminal_state == "rejected":
                action = "Apply remediation fixes and retry acceptance"
                cmd = f"asyncdev acceptance retry --feature {feature_id}"
            elif terminal_state == "manual_review":
                action = "Review acceptance findings and resolve"
                cmd = f"asyncdev acceptance result --id {latest_result_id}"
            elif terminal_state == "escalated":
                action = "Address escalation and retry"
                cmd = f"asyncdev acceptance retry --feature {feature_id}"
            else:
                action = "Re-run acceptance validation"
                cmd = f"asyncdev acceptance run --feature {feature_id}"
            
            return action, cmd
        
        if recovery_category == AcceptanceRecoveryCategory.ACCEPTANCE_BLOCKED:
            return "Resolve blockers before acceptance", "asyncdev acceptance status"
        
        if terminal_state == "conditional":
            return "Review conditional acceptance before completion", f"asyncdev acceptance result --id {latest_result_id}"
        
        return "Check acceptance status", "asyncdev acceptance status"


def get_acceptance_recovery_for_project(
    project_path: Path,
    feature_id: str,
    runstate: dict[str, Any] | None = None,
) -> AcceptanceRecoverySummary | None:
    """Get acceptance recovery summary for a project."""
    
    adapter = AcceptanceRecoveryAdapter(project_path)
    summary = adapter.get_acceptance_recovery_summary(feature_id, runstate)
    
    if summary.latest_status == "no_acceptance":
        return None
    
    return summary


def is_acceptance_recovery_significant(
    project_path: Path,
    feature_id: str,
) -> bool:
    """Check if acceptance is recovery-significant for a feature."""
    
    adapter = AcceptanceRecoveryAdapter(project_path)
    summary = adapter.get_acceptance_recovery_summary(feature_id)
    
    return summary.recovery_significant