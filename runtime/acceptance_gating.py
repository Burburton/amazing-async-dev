"""Acceptance Policy and Gating - Feature 075.

Makes acceptance a first-class gate for feature completion.
Integrates acceptance validation into completion gating.

Integration with:
- Feature 069 (AcceptanceResult terminal states)
- Feature 074 (AcceptanceConsole)
- Feature 019 (Execution Policy)
- complete-feature command
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.acceptance_console import get_acceptance_summary
from runtime.acceptance_runner import AcceptanceTerminalState, load_acceptance_result
from runtime.acceptance_pack_builder import load_acceptance_pack


class CompletionGateResult(str, Enum):
    """Results of completion gate check."""
    
    ALLOWED = "allowed"
    BLOCKED_ACCEPTANCE_REQUIRED = "blocked_acceptance_required"
    BLOCKED_ACCEPTANCE_FAILED = "blocked_acceptance_failed"
    BLOCKED_ACCEPTANCE_PENDING = "blocked_acceptance_pending"
    BLOCKED_RECOVERY_ITEMS = "blocked_recovery_items"
    BYPASS_ALLOWED = "bypass_allowed"


class AcceptancePolicyMode(str, Enum):
    """Policy modes for acceptance gating."""
    
    STRICT = "strict"
    RELAXED = "relaxed"
    OPTIONAL = "optional"
    BYPASS_ALLOWED = "bypass_allowed"


@dataclass
class CompletionGateCheck:
    """Result of completion gate validation (Feature 075)."""
    
    result: CompletionGateResult
    feature_id: str
    
    acceptance_status: str = ""
    acceptance_result_id: str | None = None
    terminal_state: str | None = None
    
    blocking_reason: str = ""
    bypass_allowed: bool = False
    bypass_reason: str | None = None
    
    required_acceptance: bool = True
    
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.value,
            "feature_id": self.feature_id,
            "acceptance_status": self.acceptance_status,
            "acceptance_result_id": self.acceptance_result_id,
            "terminal_state": self.terminal_state,
            "blocking_reason": self.blocking_reason,
            "bypass_allowed": self.bypass_allowed,
            "bypass_reason": self.bypass_reason,
            "required_acceptance": self.required_acceptance,
            "checked_at": self.checked_at,
        }
    
    def is_allowed(self) -> bool:
        return self.result in [
            CompletionGateResult.ALLOWED,
            CompletionGateResult.BYPASS_ALLOWED,
        ]
    
    def requires_acceptance(self) -> bool:
        return self.result in [
            CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED,
            CompletionGateResult.BLOCKED_ACCEPTANCE_FAILED,
            CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING,
        ]


ACCEPTANCE_REQUIRED_POLICY = AcceptancePolicyMode.STRICT
BYPASS_SCENARIOS = [
    "no_acceptance_criteria",
    "feature_spec_missing",
    "manual_override",
]


def check_completion_gate(
    project_path: Path,
    feature_id: str,
    policy_mode: AcceptancePolicyMode = AcceptancePolicyMode.STRICT,
    bypass_requested: bool = False,
    bypass_reason: str | None = None,
) -> CompletionGateCheck:
    """Check if feature can be marked complete (Feature 075)."""
    acceptance_summary = get_acceptance_summary(project_path, feature_id)
    
    acceptance_status = acceptance_summary.get("status", "no_acceptance")
    acceptance_result_id = acceptance_summary.get("latest_result_id")
    terminal_state = acceptance_summary.get("latest_terminal_state")
    pending_recovery = acceptance_summary.get("pending_recovery_items", 0)
    
    if policy_mode == AcceptancePolicyMode.OPTIONAL:
        return CompletionGateCheck(
            result=CompletionGateResult.ALLOWED,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            acceptance_result_id=acceptance_result_id,
            terminal_state=terminal_state,
            required_acceptance=False,
        )
    
    if policy_mode == AcceptancePolicyMode.RELAXED:
        if acceptance_status in ["accepted", "conditional", "no_acceptance"]:
            return CompletionGateCheck(
                result=CompletionGateResult.ALLOWED,
                feature_id=feature_id,
                acceptance_status=acceptance_status,
            )
    
    if bypass_requested and policy_mode == AcceptancePolicyMode.BYPASS_ALLOWED:
        if bypass_reason in BYPASS_SCENARIOS:
            return CompletionGateCheck(
                result=CompletionGateResult.BYPASS_ALLOWED,
                feature_id=feature_id,
                acceptance_status=acceptance_status,
                bypass_allowed=True,
                bypass_reason=bypass_reason,
            )
    
    if acceptance_status == "no_acceptance":
        return CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            blocking_reason="No acceptance validation performed. Run acceptance before completion.",
            required_acceptance=True,
        )
    
    if acceptance_status == "rejected":
        return CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_ACCEPTANCE_FAILED,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            acceptance_result_id=acceptance_result_id,
            terminal_state=terminal_state,
            blocking_reason="Acceptance rejected. Address recovery items before completion.",
            required_acceptance=True,
        )
    
    if acceptance_status == "manual_review":
        return CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            blocking_reason="Acceptance pending manual review. Complete review before completion.",
            required_acceptance=True,
        )
    
    if acceptance_status == "escalated":
        return CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            blocking_reason="Acceptance escalated. Resolve escalation before completion.",
            required_acceptance=True,
        )
    
    if pending_recovery > 0 and acceptance_status in ["rejected", "conditional"]:
        return CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_RECOVERY_ITEMS,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            blocking_reason=f"{pending_recovery} pending recovery items. Resolve before completion.",
            required_acceptance=True,
        )
    
    if acceptance_status in ["accepted", "conditional"]:
        return CompletionGateCheck(
            result=CompletionGateResult.ALLOWED,
            feature_id=feature_id,
            acceptance_status=acceptance_status,
            acceptance_result_id=acceptance_result_id,
            terminal_state=terminal_state,
        )
    
    return CompletionGateCheck(
        result=CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED,
        feature_id=feature_id,
        acceptance_status=acceptance_status,
        blocking_reason="Unknown acceptance status. Verify acceptance state.",
    )


def validate_acceptance_for_completion(
    project_path: Path,
    feature_id: str,
) -> tuple[bool, str]:
    """Validate acceptance state for completion (convenience function)."""
    gate_check = check_completion_gate(project_path, feature_id)
    
    return (
        gate_check.is_allowed(),
        gate_check.blocking_reason if not gate_check.is_allowed() else "Ready for completion",
    )


def get_acceptance_gate_summary(
    project_path: Path,
    feature_id: str,
) -> dict[str, Any]:
    """Get summary of acceptance gate status."""
    gate_check = check_completion_gate(project_path, feature_id)
    acceptance_summary = get_acceptance_summary(project_path, feature_id)
    
    return {
        "feature_id": feature_id,
        "completion_allowed": gate_check.is_allowed(),
        "gate_result": gate_check.result.value,
        "acceptance_status": acceptance_summary.get("status"),
        "blocking_reason": gate_check.blocking_reason,
        "next_action": acceptance_summary.get("next_action"),
        "required_acceptance": gate_check.required_acceptance,
    }


def is_valid_terminal_state_for_completion(
    terminal_state: str | AcceptanceTerminalState,
) -> bool:
    """Check if terminal state allows completion."""
    valid_states = ["accepted", "conditional"]
    
    if isinstance(terminal_state, AcceptanceTerminalState):
        return terminal_state.value in valid_states
    
    return terminal_state in valid_states


def get_feature_completion_requirements(
    project_path: Path,
    feature_id: str,
) -> list[str]:
    """Get list of requirements for feature completion."""
    gate_check = check_completion_gate(project_path, feature_id)
    
    requirements: list[str] = []
    
    if gate_check.is_allowed():
        return requirements
    
    if gate_check.required_acceptance:
        requirements.append("Acceptance validation required")
    
    if gate_check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED:
        requirements.append("Run acceptance validation")
        requirements.append("Acceptance must pass or be conditional")
    
    if gate_check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_FAILED:
        requirements.append("Address recovery items")
        requirements.append("Re-run acceptance after fixes")
    
    if gate_check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING:
        requirements.append("Complete manual review or resolve escalation")
    
    if gate_check.result == CompletionGateResult.BLOCKED_RECOVERY_ITEMS:
        requirements.append("Resolve pending recovery items")
    
    return requirements