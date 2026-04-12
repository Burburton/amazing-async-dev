"""Execution policy engine for low-interruption workflow automation."""

from enum import Enum
from typing import Any

from runtime.pause_reason import PauseReason, PauseCategory


class PolicyMode(str, Enum):
    """Execution policy modes."""
    
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    LOW_INTERRUPTION = "low_interruption"


class ActionType(str, Enum):
    """Types of actions that may require pause."""
    
    GIT_PUSH = "git_push"
    GIT_COMMIT_TO_REMOTE = "git_commit_to_remote"
    ARCHIVE_IRREVERSIBLE = "archive_irreversible"
    BATCH_MULTI_FEATURE = "batch_multi_feature"
    EXTERNAL_API_MUTATION = "external_api_mutation"
    PROMOTION_EXTERNALIZATION = "promotion_externalization"
    GITHUB_ISSUE_CREATE = "github_issue_create"
    REMOTE_STATE_CHANGE = "remote_state_change"
    INTERNAL_ARTIFACT = "internal_artifact"
    INTERNAL_STATE_CHANGE = "internal_state_change"


RISKY_ACTION_TYPES = {
    ActionType.GIT_PUSH,
    ActionType.GIT_COMMIT_TO_REMOTE,
    ActionType.ARCHIVE_IRREVERSIBLE,
    ActionType.BATCH_MULTI_FEATURE,
    ActionType.EXTERNAL_API_MUTATION,
    ActionType.PROMOTION_EXTERNALIZATION,
    ActionType.GITHUB_ISSUE_CREATE,
    ActionType.REMOTE_STATE_CHANGE,
}

DEFAULT_POLICY_MODE = PolicyMode.CONSERVATIVE


def get_policy_mode(runstate: dict[str, Any]) -> PolicyMode:
    """Get current policy mode from RunState."""
    mode_str = runstate.get("policy_mode", DEFAULT_POLICY_MODE.value)
    try:
        return PolicyMode(mode_str)
    except ValueError:
        return DEFAULT_POLICY_MODE


def should_auto_continue(
    runstate: dict[str, Any],
    transition_type: str,
    execution_result: dict[str, Any] | None = None,
) -> bool:
    """Check if transition should auto-continue based on policy.
    
    Args:
        runstate: Current RunState
        transition_type: Type of transition (e.g., 'execution_success_to_review')
        execution_result: Optional execution result for context
        
    Returns:
        True if should auto-continue, False if should pause
    """
    policy_mode = get_policy_mode(runstate)
    
    # Check must-pause conditions first (always pause regardless of mode)
    pause_reason = check_must_pause_conditions(runstate)
    if pause_reason:
        return False
    
    # Check auto-continue rules based on mode
    auto_continue_rules = get_auto_continue_rules(policy_mode)
    
    if transition_type in auto_continue_rules:
        # Verify conditions are met
        conditions_met = check_auto_continue_conditions(
            runstate, transition_type, execution_result
        )
        return conditions_met
    
    # Check conditional pause rules
    conditional_pause = get_conditional_pause_rules(policy_mode)
    if transition_type in conditional_pause:
        # Conditional - may pause depending on context
        return False
    
    # Default: pause in conservative, auto-continue in low-interruption
    if policy_mode == PolicyMode.CONSERVATIVE:
        return False
    elif policy_mode == PolicyMode.LOW_INTERRUPTION:
        return True
    else:
        # Balanced - auto-continue safe transitions only
        return is_safe_transition(transition_type)


def check_must_pause_conditions(runstate: dict[str, Any]) -> PauseReason | None:
    """Check must-pause conditions (always pause regardless of mode).
    
    Returns PauseReason if must pause, None if can proceed.
    """
    # Check blocked_items
    blocked_items = runstate.get("blocked_items", [])
    if blocked_items:
        blocker = blocked_items[0]
        return PauseReason(
            category=PauseCategory.BLOCKER,
            summary=f"Blocked by: {blocker.get('item', 'unknown')}",
            why=f"Blocker reason: {blocker.get('reason', 'not specified')}",
            required_to_continue="Resolve blocker or use alternative task",
            suggested_next_action="asyncdev resume-next-day unblock --retry or --alternative <task>",
        )
    
    # Check decisions_needed (must pause in conservative/balanced)
    decisions_needed = runstate.get("decisions_needed", [])
    policy_mode = get_policy_mode(runstate)
    if decisions_needed and policy_mode != PolicyMode.LOW_INTERRUPTION:
        decision = decisions_needed[0]
        return PauseReason(
            category=PauseCategory.DECISION_REQUIRED,
            summary=f"Pending decision: {decision.get('decision', 'unknown')}",
            why=f"RunState contains {len(decisions_needed)} unresolved decisions",
            required_to_continue="Make decision (approve/revise/defer) or use --force",
            suggested_next_action="asyncdev resume-next-day continue-loop --decision approve",
        )
    
    # Check scope_change_flag
    if runstate.get("scope_change_flag", False):
        return PauseReason(
            category=PauseCategory.SCOPE_CHANGE,
            summary="Task scope has changed from original plan",
            why="scope_change_flag is set in RunState",
            required_to_continue="Acknowledge scope change or revert",
            suggested_next_action="Review scope change, use --acknowledge-scope or --revert",
        )
    
    # Check pending_risky_actions
    pending_risky = runstate.get("pending_risky_actions", [])
    for action in pending_risky:
        if action.get("requires_confirmation", True):
            action_type = action.get("action_type", "unknown")
            return PauseReason(
                category=PauseCategory.RISKY_ACTION,
                summary=f"Risky action pending: {action_type}",
                why=f"Action {action_type} requires explicit confirmation",
                required_to_continue=f"Confirm {action_type} to proceed",
                suggested_next_action=f"Use --confirm-{action_type.replace('_', '-')} to proceed",
            )
    
    return None


def check_auto_continue_conditions(
    runstate: dict[str, Any],
    transition_type: str,
    execution_result: dict[str, Any] | None = None,
) -> bool:
    """Check if conditions for auto-continue are met."""
    conditions = get_transition_conditions(transition_type)
    
    for condition in conditions:
        if not evaluate_condition(runstate, condition, execution_result):
            return False
    
    return True


def get_auto_continue_rules(policy_mode: PolicyMode) -> set[str]:
    """Get auto-continue rules for policy mode."""
    if policy_mode == PolicyMode.CONSERVATIVE:
        return {"execution_success_to_review"}
    elif policy_mode == PolicyMode.BALANCED:
        return {
            "execution_success_to_review",
            "review_pack_generated",
            "safe_state_advance",
            "non_destructive_artifact_creation",
        }
    else:  # LOW_INTERRUPTION
        return {
            "execution_success_to_review",
            "review_pack_generated",
            "safe_state_advance",
            "non_destructive_artifact_creation",
            "next_safe_task_in_queue",
            "routine_cli_commands",
        }


def get_conditional_pause_rules(policy_mode: PolicyMode) -> set[str]:
    """Get conditional pause rules for policy mode."""
    if policy_mode == PolicyMode.CONSERVATIVE:
        return set()
    elif policy_mode == PolicyMode.BALANCED:
        return {
            "first_feature_in_product",
            "unfamiliar_pattern_detected",
        }
    else:  # LOW_INTERRUPTION
        return {
            "decisions_needed_not_empty",
            "scope_change_detected",
        }


def get_transition_conditions(transition_type: str) -> list[str]:
    """Get conditions required for auto-continue transition."""
    conditions_map = {
        "execution_success_to_review": [
            "no decisions_needed",
            "no blocked_items",
            "no scope_change_detected",
            "no pending risky actions",
        ],
        "review_pack_generated": [
            "review_pack validated",
        ],
        "safe_state_advance": [
            "no blockers",
            "no decisions",
            "next step is bounded and safe",
        ],
        "non_destructive_artifact_creation": [
            "artifact does not overwrite existing",
            "no external side effects",
        ],
    }
    return conditions_map.get(transition_type, [])


def evaluate_condition(
    runstate: dict[str, Any],
    condition: str,
    execution_result: dict[str, Any] | None = None,
) -> bool:
    """Evaluate a single condition string."""
    if condition == "no decisions_needed":
        return len(runstate.get("decisions_needed", [])) == 0
    elif condition == "no blocked_items":
        return len(runstate.get("blocked_items", [])) == 0
    elif condition == "no scope_change_detected":
        return not runstate.get("scope_change_flag", False)
    elif condition == "no pending risky actions":
        pending = runstate.get("pending_risky_actions", [])
        return len([a for a in pending if a.get("requires_confirmation")]) == 0
    elif condition == "review_pack validated":
        return execution_result is not None and execution_result.get("status") == "success"
    elif condition == "no blockers":
        return len(runstate.get("blocked_items", [])) == 0
    elif condition == "no decisions":
        return len(runstate.get("decisions_needed", [])) == 0
    elif condition == "next step is bounded and safe":
        next_action = runstate.get("next_recommended_action", "")
        return next_action and "risky" not in next_action.lower()
    elif condition == "artifact does not overwrite existing":
        return True  # Default safe assumption
    elif condition == "no external side effects":
        return True  # Default safe assumption
    else:
        return True


def is_safe_transition(transition_type: str) -> bool:
    """Check if transition is generally safe."""
    safe_transitions = {
        "execution_success_to_review",
        "review_pack_generated",
        "safe_state_advance",
        "non_destructive_artifact_creation",
    }
    return transition_type in safe_transitions


def is_risky_action(action_type: ActionType) -> bool:
    """Check if action type is risky."""
    return action_type in RISKY_ACTION_TYPES


def register_risky_action(
    runstate: dict[str, Any],
    action_type: ActionType,
    target: str | None = None,
    requires_confirmation: bool = True,
) -> dict[str, Any]:
    """Register a pending risky action in RunState.
    
    Args:
        runstate: Current RunState (will be modified)
        action_type: Type of risky action
        target: Optional target of the action
        requires_confirmation: Whether confirmation is required
        
    Returns:
        Updated runstate
    """
    pending_risky = runstate.get("pending_risky_actions", [])
    pending_risky.append({
        "action_type": action_type.value,
        "target": target,
        "requires_confirmation": requires_confirmation,
    })
    runstate["pending_risky_actions"] = pending_risky
    return runstate


def clear_risky_action(runstate: dict[str, Any], action_type: ActionType) -> dict[str, Any]:
    """Clear a pending risky action after confirmation.
    
    Args:
        runstate: Current RunState (will be modified)
        action_type: Type of action to clear
        
    Returns:
        Updated runstate
    """
    pending_risky = runstate.get("pending_risky_actions", [])
    filtered = [a for a in pending_risky if a.get("action_type") != action_type.value]
    runstate["pending_risky_actions"] = filtered
    return runstate


def set_scope_change_flag(runstate: dict[str, Any], flag: bool) -> dict[str, Any]:
    """Set scope change flag in RunState.
    
    Args:
        runstate: Current RunState (will be modified)
        flag: Value to set
        
    Returns:
        Updated runstate
    """
    runstate["scope_change_flag"] = flag
    return runstate


def set_policy_mode(runstate: dict[str, Any], mode: PolicyMode) -> dict[str, Any]:
    """Set policy mode in RunState.
    
    Args:
        runstate: Current RunState (will be modified)
        mode: Policy mode to set
        
    Returns:
        Updated runstate
    """
    runstate["policy_mode"] = mode.value
    return runstate


def get_pause_reason_for_action(action_type: ActionType, target: str | None = None) -> PauseReason:
    """Generate pause reason for a risky action."""
    action_descriptions = {
        ActionType.GIT_PUSH: "Git push to remote repository",
        ActionType.GIT_COMMIT_TO_REMOTE: "Git commit to remote",
        ActionType.ARCHIVE_IRREVERSIBLE: "Irreversible archive operation",
        ActionType.BATCH_MULTI_FEATURE: "Batch operation affecting multiple features",
        ActionType.EXTERNAL_API_MUTATION: "External API call with side effects",
        ActionType.PROMOTION_EXTERNALIZATION: "Promotion to external issue tracker",
        ActionType.GITHUB_ISSUE_CREATE: "Create GitHub issue",
        ActionType.REMOTE_STATE_CHANGE: "Remote state mutation",
    }
    
    desc = action_descriptions.get(action_type, action_type.value)
    target_str = f" (target: {target})" if target else ""
    
    return PauseReason(
        category=PauseCategory.RISKY_ACTION,
        summary=f"{desc}{target_str}",
        why=f"Action {action_type.value} requires explicit confirmation",
        required_to_continue=f"Confirm {action_type.value} to proceed",
        suggested_next_action=f"Use --confirm-{action_type.value.replace('_', '-')} to proceed",
    )


def can_auto_proceed_after_execution(
    runstate: dict[str, Any],
    execution_result: dict[str, Any],
) -> tuple[bool, PauseReason | None]:
    """Check if system can auto-proceed after execution result.
    
    Args:
        runstate: Current RunState
        execution_result: Execution result from run-day
        
    Returns:
        (can_proceed, pause_reason_if_blocked)
    """
    # Execution must be successful
    if execution_result.get("status") != "success":
        return False, PauseReason(
            category=PauseCategory.POLICY_BOUNDARY,
            summary="Execution did not complete successfully",
            why=f"Execution status: {execution_result.get('status', 'unknown')}",
            required_to_continue="Review execution result and retry or handle failure",
            suggested_next_action="asyncdev resume-next-day handle-failed --retry or --abandon",
        )
    
    # Check if auto-continue is allowed
    can_auto = should_auto_continue(
        runstate,
        "execution_success_to_review",
        execution_result,
    )
    
    if can_auto:
        return True, None
    
    # Get the reason for pause
    pause_reason = check_must_pause_conditions(runstate)
    if pause_reason:
        return False, pause_reason
    
    # Policy boundary pause
    return False, PauseReason(
        category=PauseCategory.POLICY_BOUNDARY,
        summary="Current policy mode requires pause after execution",
        why=f"Policy mode: {get_policy_mode(runstate).value}",
        required_to_continue="Proceed manually or change policy mode",
        suggested_next_action="asyncdev review-night generate or asyncdev policy set --mode balanced",
    )