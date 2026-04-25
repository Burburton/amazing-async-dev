"""Acceptance Readiness State Model - Feature 070.

Defines the structured state model for acceptance trigger readiness.
Determines when a feature or phase result is ready for independent acceptance validation.

Integration with:
- Feature 069 (AcceptancePack/AcceptanceResult artifacts)
- Feature 067 (Observer findings)
- Feature 061 (Closeout completion)
- Feature 020 (Policy pattern)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.state_store import StateStore
from runtime.artifact_router import get_feature_spec_path


class AcceptanceReadiness(str, Enum):
    """Acceptance readiness states (Feature 070 section 6.1)."""
    
    READY = "ready"                   # All prerequisites satisfied, can trigger
    NOT_READY = "not_ready"           # Prerequisites not met, cannot trigger
    BLOCKED = "blocked"               # Explicit blocker present
    POLICY_SKIPPED = "policy_skipped" # Policy mode prevents auto-trigger
    NO_CRITERIA = "no_criteria"       # Feature has no acceptance criteria defined


class AcceptanceTriggerPolicyMode(str, Enum):
    """Policy modes for acceptance triggering (per Feature 070 section 6.3)."""
    
    ALWAYS_TRIGGER = "always_trigger"
    FEATURE_COMPLETION_ONLY = "feature_completion_only"
    MANUAL_ONLY = "manual_only"


@dataclass
class PrerequisiteCheck:
    """Single prerequisite check result."""
    
    name: str
    description: str
    satisfied: bool
    failure_reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AcceptanceReadinessResult:
    """Result of acceptance readiness evaluation (Feature 070 section 7.1).
    
    Captures the complete readiness evaluation from prerequisite checks to policy decision.
    """
    
    readiness: AcceptanceReadiness
    execution_result_id: str
    feature_id: str | None = None
    product_id: str | None = None
    
    prerequisites_checked: list[PrerequisiteCheck] = field(default_factory=list)
    prerequisites_satisfied: list[str] = field(default_factory=list)
    prerequisites_failed: list[str] = field(default_factory=list)
    
    blocking_reasons: list[str] = field(default_factory=list)
    
    trigger_allowed: bool = False
    trigger_recommended: bool = False
    
    policy_mode: AcceptanceTriggerPolicyMode = AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY
    policy_decision: str = ""
    
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for storage or serialization."""
        return {
            "readiness": self.readiness.value,
            "execution_result_id": self.execution_result_id,
            "feature_id": self.feature_id,
            "product_id": self.product_id,
            "prerequisites_checked": [
                {
                    "name": p.name,
                    "description": p.description,
                    "satisfied": p.satisfied,
                    "failure_reason": p.failure_reason,
                    "details": p.details,
                }
                for p in self.prerequisites_checked
            ],
            "prerequisites_satisfied": self.prerequisites_satisfied,
            "prerequisites_failed": self.prerequisites_failed,
            "blocking_reasons": self.blocking_reasons,
            "trigger_allowed": self.trigger_allowed,
            "trigger_recommended": self.trigger_recommended,
            "policy_mode": self.policy_mode.value,
            "policy_decision": self.policy_decision,
            "checked_at": self.checked_at,
        }
    
    def is_triggerable(self) -> bool:
        """Check if acceptance can be triggered based on readiness."""
        return self.readiness == AcceptanceReadiness.READY and self.trigger_allowed
    
    def should_auto_trigger(self) -> bool:
        """Check if acceptance should be auto-triggered (ready + policy allows)."""
        return self.is_triggerable() and self.trigger_recommended


# Prerequisite definitions (Feature 070 section 6.2)
ACCEPTANCE_PREREQUISITES = {
    "execution_complete": {
        "description": "ExecutionResult exists with success status",
        "check_field": "status",
        "expected_value": "success",
    },
    "closeout_success": {
        "description": "Closeout completed successfully",
        "check_field": "closeout_terminal_state",
        "expected_value": "success",
    },
    "verification_pass": {
        "description": "Verification passed or not required",
        "check_field": "orchestration_terminal_state",
        "expected_values": ["success", "not_required", "exception_accepted", "skipped_by_policy"],
    },
    "no_blockers": {
        "description": "No blocked items present",
        "check_field": "blocked_items",
        "expected_value": [],  # Empty list
    },
    "no_pending_decisions": {
        "description": "No pending decisions needed",
        "check_field": "decisions_needed",
        "expected_value": [],  # Empty list
    },
    "feature_spec_has_criteria": {
        "description": "FeatureSpec has acceptance criteria defined",
        "check_field": "acceptance_criteria",
        "min_items": 1,
    },
}


def check_prerequisite_execution_complete(
    execution_result: dict[str, Any]
) -> PrerequisiteCheck:
    """Check execution_complete prerequisite."""
    status = execution_result.get("status", "")
    satisfied = status == "success"
    
    return PrerequisiteCheck(
        name="execution_complete",
        description="ExecutionResult exists with success status",
        satisfied=satisfied,
        failure_reason=None if satisfied else f"ExecutionResult.status is '{status}', not 'success'",
        details={"status": status},
    )


def check_prerequisite_closeout_success(
    execution_result: dict[str, Any]
) -> PrerequisiteCheck:
    """Check closeout_success prerequisite."""
    closeout_state = execution_result.get("closeout_state", "")
    closeout_terminal = execution_result.get("closeout_terminal_state", "")
    
    # Check if closeout reached terminal success state
    satisfied = closeout_terminal == "success"
    
    return PrerequisiteCheck(
        name="closeout_success",
        description="Closeout completed successfully",
        satisfied=satisfied,
        failure_reason=None if satisfied else f"closeout_terminal_state is '{closeout_terminal}', not 'success'",
        details={
            "closeout_state": closeout_state,
            "closeout_terminal_state": closeout_terminal,
        },
    )


def check_prerequisite_verification_pass(
    execution_result: dict[str, Any]
) -> PrerequisiteCheck:
    """Check verification_pass prerequisite."""
    orchestration_state = execution_result.get("orchestration_terminal_state", "not_required")
    browser_verification = execution_result.get("browser_verification", {})
    
    # Valid terminal states for acceptance
    valid_states = ["success", "not_required", "exception_accepted", "skipped_by_policy"]
    satisfied = orchestration_state in valid_states
    
    # Additional check: if browser verification ran, check passed count
    if satisfied and browser_verification.get("executed"):
        passed = browser_verification.get("passed", 0)
        failed = browser_verification.get("failed", 0)
        satisfied = failed == 0
    
    failure_reason = None
    if not satisfied:
        if orchestration_state not in valid_states:
            failure_reason = f"orchestration_terminal_state is '{orchestration_state}'"
        elif browser_verification.get("executed") and browser_verification.get("failed", 0) > 0:
            failure_reason = f"Browser verification failed: {browser_verification.get('failed', 0)} scenarios failed"
    
    return PrerequisiteCheck(
        name="verification_pass",
        description="Verification passed or not required",
        satisfied=satisfied,
        failure_reason=failure_reason,
        details={
            "orchestration_terminal_state": orchestration_state,
            "browser_verification_executed": browser_verification.get("executed", False),
            "browser_verification_passed": browser_verification.get("passed", 0),
            "browser_verification_failed": browser_verification.get("failed", 0),
        },
    )


def check_prerequisite_no_blockers(
    runstate: dict[str, Any]
) -> PrerequisiteCheck:
    """Check no_blockers prerequisite."""
    blocked_items = runstate.get("blocked_items", [])
    satisfied = len(blocked_items) == 0
    
    return PrerequisiteCheck(
        name="no_blockers",
        description="No blocked items present",
        satisfied=satisfied,
        failure_reason=None if satisfied else f"{len(blocked_items)} blocked items present",
        details={"blocked_items_count": len(blocked_items)},
    )


def check_prerequisite_no_pending_decisions(
    runstate: dict[str, Any]
) -> PrerequisiteCheck:
    """Check no_pending_decisions prerequisite."""
    decisions_needed = runstate.get("decisions_needed", [])
    satisfied = len(decisions_needed) == 0
    
    return PrerequisiteCheck(
        name="no_pending_decisions",
        description="No pending decisions needed",
        satisfied=satisfied,
        failure_reason=None if satisfied else f"{len(decisions_needed)} decisions pending",
        details={"decisions_needed_count": len(decisions_needed)},
    )


def check_prerequisite_feature_spec_has_criteria(
    feature_spec: dict[str, Any] | None
) -> PrerequisiteCheck:
    """Check feature_spec_has_criteria prerequisite."""
    if feature_spec is None:
        return PrerequisiteCheck(
            name="feature_spec_has_criteria",
            description="FeatureSpec has acceptance criteria defined",
            satisfied=False,
            failure_reason="No FeatureSpec found",
            details={},
        )
    
    acceptance_criteria = feature_spec.get("acceptance_criteria", [])
    satisfied = len(acceptance_criteria) >= 1
    
    return PrerequisiteCheck(
        name="feature_spec_has_criteria",
        description="FeatureSpec has acceptance criteria defined",
        satisfied=satisfied,
        failure_reason=None if satisfied else "FeatureSpec has no acceptance_criteria",
        details={"acceptance_criteria_count": len(acceptance_criteria)},
    )


def check_acceptance_readiness(
    project_path: Path,
    execution_result_id: str,
    policy_mode: AcceptanceTriggerPolicyMode = AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY,
) -> AcceptanceReadinessResult:
    """Check acceptance readiness for an execution result (Feature 070 section 7.2).
    
    Evaluates all prerequisites and applies policy to determine if acceptance
    should be triggered.
    
    Args:
        project_path: Path to the project
        execution_result_id: ID of the ExecutionResult to evaluate
        policy_mode: Policy mode for trigger decision
    
    Returns:
        AcceptanceReadinessResult with detailed readiness evaluation
    """
    store = StateStore(project_path)
    
    # Load ExecutionResult
    execution_result = store.load_execution_result(execution_result_id)
    runstate = store.load_runstate() or {}
    
    # Load FeatureSpec if available
    feature_id = runstate.get("feature_id", "")
    feature_spec = None
    if feature_id:
        feature_spec_path = get_feature_spec_path(project_path, feature_id)
        if feature_spec_path.exists():
            import yaml
            content = feature_spec_path.read_text(encoding="utf-8")
            yaml_match = re.search(r"```yaml\n(.*?)\n```", content, re.DOTALL)
            if yaml_match:
                feature_spec = yaml.safe_load(yaml_match.group(1))
            else:
                feature_spec = yaml.safe_load(content)
    
    # Run all prerequisite checks
    prerequisites: list[PrerequisiteCheck] = []
    
    if execution_result:
        prerequisites.append(check_prerequisite_execution_complete(execution_result))
        prerequisites.append(check_prerequisite_closeout_success(execution_result))
        prerequisites.append(check_prerequisite_verification_pass(execution_result))
    else:
        # No ExecutionResult found
        prerequisites.append(PrerequisiteCheck(
            name="execution_complete",
            description="ExecutionResult exists with success status",
            satisfied=False,
            failure_reason=f"No ExecutionResult found for {execution_result_id}",
            details={},
        ))
        prerequisites.append(PrerequisiteCheck(
            name="closeout_success",
            description="Closeout completed successfully",
            satisfied=False,
            failure_reason="No ExecutionResult to check",
            details={},
        ))
        prerequisites.append(PrerequisiteCheck(
            name="verification_pass",
            description="Verification passed or not required",
            satisfied=False,
            failure_reason="No ExecutionResult to check",
            details={},
        ))
    
    prerequisites.append(check_prerequisite_no_blockers(runstate))
    prerequisites.append(check_prerequisite_no_pending_decisions(runstate))
    prerequisites.append(check_prerequisite_feature_spec_has_criteria(feature_spec))
    
    # Classify satisfied vs failed
    satisfied_names = [p.name for p in prerequisites if p.satisfied]
    failed_names = [p.name for p in prerequisites if not p.satisfied]
    
    # Determine blocking reasons
    blocking_reasons = [p.failure_reason for p in prerequisites if p.failure_reason]
    
    # Determine readiness state
    readiness = AcceptanceReadiness.NOT_READY
    
    if all(p.satisfied for p in prerequisites):
        readiness = AcceptanceReadiness.READY
    elif any(p.name == "no_blockers" and not p.satisfied for p in prerequisites):
        readiness = AcceptanceReadiness.BLOCKED
    elif any(p.name == "feature_spec_has_criteria" and not p.satisfied for p in prerequisites):
        readiness = AcceptanceReadiness.NO_CRITERIA
    
    # Apply policy decision
    trigger_allowed = readiness == AcceptanceReadiness.READY
    trigger_recommended = False
    policy_decision = ""
    
    if policy_mode == AcceptanceTriggerPolicyMode.ALWAYS_TRIGGER:
        if readiness == AcceptanceReadiness.READY:
            trigger_recommended = True
            policy_decision = "Policy 'always_trigger' allows auto-trigger when ready"
        else:
            policy_decision = f"Policy 'always_trigger' cannot trigger due to {readiness.value}"
    
    elif policy_mode == AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY:
        # Additional check: is this a feature completion candidate?
        # For now, we assume any successful execution is a candidate
        if readiness == AcceptanceReadiness.READY:
            trigger_recommended = True
            policy_decision = "Policy 'feature_completion_only' allows trigger for completion candidate"
        else:
            policy_decision = f"Policy 'feature_completion_only' cannot trigger due to {readiness.value}"
    
    elif policy_mode == AcceptanceTriggerPolicyMode.MANUAL_ONLY:
        trigger_allowed = readiness == AcceptanceReadiness.READY
        trigger_recommended = False
        policy_decision = "Policy 'manual_only' prevents auto-trigger - operator must request"
        if readiness == AcceptanceReadiness.READY:
            readiness = AcceptanceReadiness.POLICY_SKIPPED
    
    return AcceptanceReadinessResult(
        readiness=readiness,
        execution_result_id=execution_result_id,
        feature_id=feature_id,
        product_id=runstate.get("project_id", ""),
        prerequisites_checked=prerequisites,
        prerequisites_satisfied=satisfied_names,
        prerequisites_failed=failed_names,
        blocking_reasons=blocking_reasons,
        trigger_allowed=trigger_allowed,
        trigger_recommended=trigger_recommended,
        policy_mode=policy_mode,
        policy_decision=policy_decision,
    )


def is_acceptance_triggerable(
    project_path: Path,
    execution_result_id: str,
) -> bool:
    """Quick check if acceptance can be triggered (convenience function)."""
    result = check_acceptance_readiness(project_path, execution_result_id)
    return result.is_triggerable()


def should_auto_trigger_acceptance(
    project_path: Path,
    execution_result_id: str,
    policy_mode: AcceptanceTriggerPolicyMode = AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY,
) -> bool:
    """Check if acceptance should be auto-triggered (convenience function)."""
    result = check_acceptance_readiness(project_path, execution_result_id, policy_mode)
    return result.should_auto_trigger()