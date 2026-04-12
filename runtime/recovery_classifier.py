"""Recovery classification for workflow state."""

from enum import Enum
from typing import Any

from runtime.execution_policy import (
    check_must_pause_conditions,
    get_policy_mode,
    PolicyMode,
)


class RecoveryClassification(str, Enum):
    """Classification of workflow stop states for recovery decisions.
    
    These classifications determine what recovery actions are appropriate
    and whether automatic resume is safe.
    """
    
    NORMAL_PAUSE = "normal_pause"
    """Workflow stopped normally at end of day.
    
    Recovery: Ready to resume with resume-next-day.
    """
    
    BLOCKED = "blocked"
    """Workflow blocked by external dependency or issue.
    
    Recovery: Requires unblock after blocker resolution.
    """
    
    FAILED = "failed"
    """Execution failed unexpectedly.
    
    Recovery: Requires handle-failed, may need retry or alternative.
    """
    
    AWAITING_DECISION = "awaiting_decision"
    """Workflow paused for human decision.
    
    Recovery: Decision must be made before resume.
    """
    
    READY_TO_RESUME = "ready_to_resume"
    """Workflow is in safe state to resume.
    
    Recovery: Safe to continue with plan-day or run-day.
    """
    
    UNSAFE_TO_RESUME = "unsafe_to_resume"
    """Workflow state is inconsistent or corrupted.
    
    Recovery: Requires manual inspection before any action.
    """
    
    ALREADY_COMPLETED = "already_completed"
    """Feature already completed.
    
    Recovery: No resume needed, can archive.
    """
    
    ALREADY_ARCHIVED = "already_archived"
    """Feature already archived.
    
    Recovery: Cannot resume archived feature.
    """


class ResumeEligibility(str, Enum):
    """Result of resume eligibility check."""
    
    ELIGIBLE = "eligible"
    """Resume is safe and allowed."""
    
    NEEDS_DECISION = "needs_decision"
    """Resume blocked by pending decision."""
    
    NEEDS_UNBLOCK = "needs_unblock"
    """Resume blocked by blocker."""
    
    NEEDS_FAILURE_HANDLING = "needs_failure_handling"
    """Resume blocked by failed state."""
    
    INCONSISTENT_STATE = "inconsistent_state"
    """State is inconsistent, needs inspection."""
    
    NOT_RESUMABLE = "not_resumable"
    """Feature completed or archived, cannot resume."""


def classify_recovery(runstate: dict[str, Any]) -> RecoveryClassification:
    """Classify the recovery state of a workflow.
    
    Args:
        runstate: Current RunState dictionary
        
    Returns:
        RecoveryClassification indicating current recovery state
    """
    phase = runstate.get("current_phase", "planning")
    blocked_items = runstate.get("blocked_items", [])
    decisions_needed = runstate.get("decisions_needed", [])
    
    # Check archived/completed first (terminal states)
    if phase == "archived":
        return RecoveryClassification.ALREADY_ARCHIVED
    if phase == "completed":
        return RecoveryClassification.ALREADY_COMPLETED
    
    # Check blocked
    if phase == "blocked" or blocked_items:
        return RecoveryClassification.BLOCKED
    
    # Check awaiting decision
    if decisions_needed:
        return RecoveryClassification.AWAITING_DECISION
    
    # Check failed (implied by phase stuck in executing without progress)
    # This is a heuristic - if last_action mentions failure
    last_action = runstate.get("last_action", "")
    if "failed" in last_action.lower() or "error" in last_action.lower():
        return RecoveryClassification.FAILED
    
    # Check reviewing phase (normal pause after execution)
    if phase == "reviewing":
        return RecoveryClassification.NORMAL_PAUSE
    
    # Check planning phase (normal start of day)
    if phase == "planning":
        return RecoveryClassification.READY_TO_RESUME
    
    # Check executing phase (could be interrupted)
    if phase == "executing":
        # Check if there's an active execution
        active_task = runstate.get("active_task")
        if active_task:
            return RecoveryClassification.UNSAFE_TO_RESUME
        return RecoveryClassification.NORMAL_PAUSE
    
    # Default fallback
    return RecoveryClassification.UNSAFE_TO_RESUME


def check_resume_eligibility(runstate: dict[str, Any]) -> ResumeEligibility:
    """Check if workflow can be safely resumed.
    
    Args:
        runstate: Current RunState dictionary
        
    Returns:
        ResumeEligibility indicating resume eligibility
    """
    classification = classify_recovery(runstate)
    
    # Map classification to eligibility
    eligibility_map = {
        RecoveryClassification.READY_TO_RESUME: ResumeEligibility.ELIGIBLE,
        RecoveryClassification.NORMAL_PAUSE: ResumeEligibility.ELIGIBLE,
        RecoveryClassification.AWAITING_DECISION: ResumeEligibility.NEEDS_DECISION,
        RecoveryClassification.BLOCKED: ResumeEligibility.NEEDS_UNBLOCK,
        RecoveryClassification.FAILED: ResumeEligibility.NEEDS_FAILURE_HANDLING,
        RecoveryClassification.UNSAFE_TO_RESUME: ResumeEligibility.INCONSISTENT_STATE,
        RecoveryClassification.ALREADY_COMPLETED: ResumeEligibility.NOT_RESUMABLE,
        RecoveryClassification.ALREADY_ARCHIVED: ResumeEligibility.NOT_RESUMABLE,
    }
    
    return eligibility_map.get(classification, ResumeEligibility.INCONSISTENT_STATE)


def get_recovery_guidance(runstate: dict[str, Any]) -> dict[str, Any]:
    """Generate recovery guidance for current workflow state.
    
    Args:
        runstate: Current RunState dictionary
        
    Returns:
        Dictionary with guidance information:
        - classification: RecoveryClassification
        - eligibility: ResumeEligibility
        - recommended_action: suggested CLI command
        - explanation: human-readable explanation
        - warnings: list of warnings if any
    """
    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)
    
    guidance_map = {
        RecoveryClassification.READY_TO_RESUME: {
            "recommended_action": "asyncdev plan-day create",
            "explanation": "Workflow is ready to start new execution cycle.",
            "warnings": [],
        },
        RecoveryClassification.NORMAL_PAUSE: {
            "recommended_action": "asyncdev resume-next-day continue-loop",
            "explanation": "Workflow paused normally. Ready to resume.",
            "warnings": [],
        },
        RecoveryClassification.AWAITING_DECISION: {
            "recommended_action": "asyncdev resume-next-day continue-loop --decision <choice>",
            "explanation": "Pending decisions must be resolved before continuing.",
            "warnings": ["Decisions pending, automatic resume blocked"],
        },
        RecoveryClassification.BLOCKED: {
            "recommended_action": "asyncdev resume-next-day unblock --reason '<resolution>'",
            "explanation": "Blockers must be resolved before continuing.",
            "warnings": ["Blocked items present, resume blocked"],
        },
        RecoveryClassification.FAILED: {
            "recommended_action": "asyncdev resume-next-day handle-failed --<option>",
            "explanation": "Execution failed. Choose retry, escalate, or abandon.",
            "warnings": ["Failed state requires manual intervention"],
        },
        RecoveryClassification.UNSAFE_TO_RESUME: {
            "recommended_action": "asyncdev inspect-stop --project <id>",
            "explanation": "Workflow state is inconsistent. Manual inspection required.",
            "warnings": ["State inconsistent, automatic resume unsafe"],
        },
        RecoveryClassification.ALREADY_COMPLETED: {
            "recommended_action": "asyncdev archive-feature create",
            "explanation": "Feature completed. Ready to archive.",
            "warnings": ["Feature completed, cannot resume execution"],
        },
        RecoveryClassification.ALREADY_ARCHIVED: {
            "recommended_action": "No action needed",
            "explanation": "Feature archived. Cannot resume.",
            "warnings": ["Feature archived, resume not possible"],
        },
    }
    
    guidance = guidance_map.get(classification, {
        "recommended_action": "asyncdev inspect-stop",
        "explanation": "Unknown state. Manual inspection required.",
        "warnings": ["Unknown state classification"],
    })
    
    return {
        "classification": classification.value,
        "eligibility": eligibility.value,
        "phase": runstate.get("current_phase"),
        "blocked_count": len(runstate.get("blocked_items", [])),
        "decisions_count": len(runstate.get("decisions_needed", [])),
        "policy_mode": get_policy_mode(runstate).value,
        "recommended_action": guidance["recommended_action"],
        "explanation": guidance["explanation"],
        "warnings": guidance["warnings"],
    }


def get_policy_pause_reason(runstate: dict[str, Any]) -> dict[str, Any] | None:
    """Get structured pause reason from policy checks.
    
    Args:
        runstate: Current RunState dictionary
        
    Returns:
        PauseReason dict if must pause, None if can proceed
    """
    pause_reason = check_must_pause_conditions(runstate)
    if pause_reason:
        return pause_reason.to_dict()
    return None


def can_auto_proceed(runstate: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
    """Check if workflow can auto-proceed based on policy.
    
    Args:
        runstate: Current RunState dictionary
        
    Returns:
        (can_proceed, pause_reason_dict_if_blocked)
    """
    pause_reason = check_must_pause_conditions(runstate)
    if pause_reason:
        return False, pause_reason.to_dict()
    
    policy_mode = get_policy_mode(runstate)
    
    if policy_mode == PolicyMode.CONSERVATIVE:
        return False, {
            "category": "policy_boundary",
            "summary": "Conservative policy requires manual confirmation",
            "why": f"Policy mode: {policy_mode.value}",
            "required_to_continue": "Proceed manually or change policy mode",
            "suggested_next_action": "asyncdev policy set --mode balanced",
        }
    
    return True, None