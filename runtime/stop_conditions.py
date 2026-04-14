"""Stop condition framework for Feature 037.

Defines explicit stop conditions that must be satisfied before
the system can legitimately stop after a checkpoint.

If none of these conditions apply, the system should not stop by default.

Stop conditions are:
- Explicit (must match a defined type)
- Inspectable (can be reviewed)
- Policy-driven (respect governance)
"""

from typing import Any

from runtime.continuation_types import (
    TerminalStopType,
    StopCondition,
    CanonicalStage,
)


def check_escalation_required(runstate: dict[str, Any], execution_result: dict[str, Any]) -> StopCondition | None:
    """Check if major decision requires human approval.
    
    FR-4.1: Escalation Required
    - Major product metaphor, scope, architecture, or dependency decision
    - Requires human approval before continuation
    """
    decisions_needed = runstate.get("decisions_needed", [])
    decisions_required = execution_result.get("decisions_required", [])
    
    all_decisions = decisions_needed + decisions_required
    
    for decision in all_decisions:
        if isinstance(decision, dict):
            urgency = decision.get("urgency", "medium")
            decision_text = decision.get("decision", "").lower()
            
            high_urgency_keywords = [
                "architecture", "metaphor", "scope expansion",
                "dependency", "critical", "major", "breaking",
            ]
            
            is_major = urgency == "high" or any(
                kw in decision_text for kw in high_urgency_keywords
            )
            
            if is_major:
                return StopCondition(
                    stop_type=TerminalStopType.ESCALATION_REQUIRED,
                    summary=f"Major decision pending: {decision.get('decision', 'unknown')}",
                    reason=f"Decision requires human approval before continuation",
                    required_to_continue="Make decision (approve/revise/defer/redefine)",
                    suggested_action="asyncdev resume-next-day continue-loop --decision <choice>",
                    details={"decision": decision},
                )
    
    return None


def check_no_meaningful_next_step(runstate: dict[str, Any], execution_result: dict[str, Any]) -> StopCondition | None:
    """Check if there is no coherent next action.
    
    FR-4.2: No Meaningful Next Step
    - Current artifacts do not support a coherent next action
    - Task queue is empty and no recommended action exists
    """
    task_queue = runstate.get("task_queue", [])
    next_action = execution_result.get("recommended_next_step", "")
    runstate_next = runstate.get("next_recommended_action", "")
    
    has_queue = len(task_queue) > 0
    has_next_action = next_action and len(next_action) > 10
    has_runstate_next = runstate_next and len(runstate_next) > 10
    
    if not has_queue and not has_next_action and not has_runstate_next:
        completed_outputs = runstate.get("completed_outputs", [])
        feature_id = runstate.get("feature_id", "")
        
        if len(completed_outputs) > 0:
            return StopCondition(
                stop_type=TerminalStopType.NO_MEANINGFUL_NEXT_STEP,
                summary="No meaningful next action available",
                reason=f"All tasks completed, no further scope defined for feature {feature_id}",
                required_to_continue="Add new tasks, complete feature, or start new feature",
                suggested_action="asyncdev complete-feature mark or asyncdev plan-day create with new task",
                details={
                    "completed_count": len(completed_outputs),
                    "feature_id": feature_id,
                },
            )
    
    return None


def check_external_blocker(runstate: dict[str, Any], execution_result: dict[str, Any] = None) -> StopCondition | None:
    """Check if external dependency blocks progress.
    
    FR-4.3: External Blocker
    - Required resource, repo, credential, dependency, or environment is missing
    """
    blocked_items = runstate.get("blocked_items", [])
    
    external_keywords = [
        "credential", "api key", "token", "environment",
        "repository", "dependency", "network", "service",
        "external", "remote", "authentication", "permission",
    ]
    
    for blocker in blocked_items:
        if isinstance(blocker, dict):
            reason = blocker.get("reason", "").lower()
            item = blocker.get("item", "").lower()
            
            is_external = any(
                kw in reason or kw in item for kw in external_keywords
            )
            
            if is_external:
                return StopCondition(
                    stop_type=TerminalStopType.EXTERNAL_BLOCKER,
                    summary=f"External blocker: {blocker.get('item', 'unknown')}",
                    reason=f"External dependency unavailable: {blocker.get('reason', 'not specified')}",
                    required_to_continue="Resolve external dependency or use alternative",
                    suggested_action="Resolve blocker manually, then asyncdev resume-next-day unblock",
                    details={"blocker": blocker},
                )
    
    return None


def check_integrity_safety_pause(runstate: dict[str, Any], execution_result: dict[str, Any]) -> StopCondition | None:
    """Check if continuation risks compounding errors.
    
    FR-4.4: Integrity / Safety Pause
    - Continuing risks compounding significant errors or invalid state
    """
    issues_found = execution_result.get("issues_found", [])
    status = execution_result.get("status", "success")
    
    high_severity_keywords = [
        "corruption", "invalid", "broken", "unsafe",
        "security", "vulnerability", "critical", "data loss",
    ]
    
    if status == "failed":
        return StopCondition(
            stop_type=TerminalStopType.INTEGRITY_SAFETY_PAUSE,
            summary="Execution failed - integrity risk",
            reason="Continuation after failed execution may compound errors",
            required_to_continue="Review failure, fix root cause, or abandon task",
            suggested_action="asyncdev resume-next-day handle-failed --report",
            details={"status": status, "issues_count": len(issues_found)},
        )
    
    for issue in issues_found:
        if isinstance(issue, dict):
            severity = issue.get("severity", "medium")
            description = issue.get("description", "").lower()
            
            is_critical = severity == "high" or any(
                kw in description for kw in high_severity_keywords
            )
            
            if is_critical and issue.get("resolution", "pending") == "pending":
                return StopCondition(
                    stop_type=TerminalStopType.INTEGRITY_SAFETY_PAUSE,
                    summary=f"Critical unresolved issue: {issue.get('description', 'unknown')}",
                    reason="Continuation risks compounding critical error",
                    required_to_continue="Resolve critical issue before continuation",
                    suggested_action="Fix issue or escalate for human intervention",
                    details={"issue": issue},
                )
    
    return None


def check_policy_based_stop(runstate: dict[str, Any], execution_result: dict[str, Any]) -> StopCondition | None:
    """Check if governing document mandates stop.
    
    FR-4.5: Policy-Based Stop
    - A governing document explicitly mandates stop after a given milestone
    """
    policy_mode = runstate.get("policy_mode", "balanced")
    
    if policy_mode == "conservative":
        return StopCondition(
            stop_type=TerminalStopType.POLICY_BASED_STOP,
            summary="Conservative policy mode requires human checkpoint",
            reason="Policy mode 'conservative' requires explicit continuation approval",
            required_to_continue="Approve continuation or change policy mode",
            suggested_action="asyncdev resume-next-day continue-loop --decision approve or asyncdev policy set --mode balanced",
            details={"policy_mode": policy_mode},
        )
    
    scope_change_flag = runstate.get("scope_change_flag", False)
    if scope_change_flag:
        return StopCondition(
            stop_type=TerminalStopType.POLICY_BASED_STOP,
            summary="Scope change detected - policy requires pause",
            reason="scope_change_flag is set - scope drift requires acknowledgment",
            required_to_continue="Acknowledge scope change or revert to original scope",
            suggested_action="Review scope change, use --acknowledge-scope or --revert",
            details={"scope_change_flag": scope_change_flag},
        )
    
    pending_risky = runstate.get("pending_risky_actions", [])
    for action in pending_risky:
        if action.get("requires_confirmation", True):
            return StopCondition(
                stop_type=TerminalStopType.POLICY_BASED_STOP,
                summary=f"Risky action pending: {action.get('action_type', 'unknown')}",
                reason="Risky action requires explicit confirmation per policy",
                required_to_continue=f"Confirm {action.get('action_type', 'action')} to proceed",
                suggested_action=f"Use --confirm-{action.get('action_type', 'action').replace('_', '-')} to proceed",
                details={"action": action},
            )
    
    return None


def evaluate_all_stop_conditions(
    runstate: dict[str, Any],
    execution_result: dict[str, Any],
) -> StopCondition | None:
    """Evaluate all stop conditions in priority order.
    
    Returns the first matching stop condition, or None if no stop applies.
    
    Priority order:
    1. Integrity/Safety (highest - must stop)
    2. External Blocker
    3. Escalation Required
    4. Policy-Based Stop
    5. No Meaningful Next Step (lowest - can stop but may not need to)
    """
    checks = [
        check_integrity_safety_pause,
        check_external_blocker,
        check_escalation_required,
        check_policy_based_stop,
        check_no_meaningful_next_step,
    ]
    
    for check in checks:
        condition = check(runstate, execution_result)
        if condition:
            return condition
    
    return None


def resolve_next_canonical_stage(
    runstate: dict[str, Any],
    execution_result: dict[str, Any],
) -> CanonicalStage | None:
    """Resolve the next canonical stage from current artifacts.
    
    FR-3: Canonical Next-Step Resolution
    
    Possible next stages:
    - dogfood current iteration
    - collect friction and observations
    - consolidate audit findings
    - repair known issues
    - derive next iteration scope
    - generate next execution artifacts
    - continue product evolution
    """
    status = execution_result.get("status", "success")
    
    if status == "blocked":
        return CanonicalStage.REPAIR_LOOP
    
    completed_outputs = runstate.get("completed_outputs", [])
    issues_found = execution_result.get("issues_found", [])
    unresolved_issues = [
        i for i in issues_found
        if isinstance(i, dict) and i.get("resolution", "pending") == "pending"
    ]
    
    if len(unresolved_issues) > 0:
        return CanonicalStage.REPAIR_LOOP
    
    task_queue = runstate.get("task_queue", [])
    if len(task_queue) > 0:
        return CanonicalStage.EXECUTION_PACK_GENERATION
    
    next_action = execution_result.get("recommended_next_step", "").lower()
    
    stage_keywords = {
        CanonicalStage.DOGFOOD: ["dogfood", "test in", "validate on", "try on"],
        CanonicalStage.FRICTION_CAPTURE: ["friction", "capture", "feedback", "observe"],
        CanonicalStage.AUDIT_CONSOLIDATION: ["audit", "consolidate", "review"],
        CanonicalStage.NEXT_SCOPE_DERIVATION: ["derive", "next scope", "next iteration", "v2", "next version"],
        CanonicalStage.NEXT_ITERATION_PLANNING: ["plan next", "prepare next", "next iteration"],
        CanonicalStage.CLOSEOUT: ["closeout", "archive", "complete", "finish"],
    }
    
    for stage, keywords in stage_keywords.items():
        if any(kw in next_action for kw in keywords):
            return stage
    
    if len(completed_outputs) > 0 and status == "success":
        return CanonicalStage.EXECUTION_PACK_GENERATION
    
    return None


def has_meaningful_next_step(runstate: dict[str, Any], execution_result: dict[str, Any]) -> bool:
    """Check if there is a meaningful next step available."""
    next_stage = resolve_next_canonical_stage(runstate, execution_result)
    
    if next_stage:
        return True
    
    task_queue = runstate.get("task_queue", [])
    if len(task_queue) > 0:
        return True
    
    next_action = execution_result.get("recommended_next_step", "")
    if next_action and len(next_action) > 10:
        return True
    
    return False