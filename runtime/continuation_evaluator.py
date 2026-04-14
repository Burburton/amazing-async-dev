"""Continuation evaluator for Feature 037.

Evaluates current state after checkpoint and decides:
- continue automatically
- stop with explicit reason
- escalate with explicit reason

Core Principle: Successful progress is a continuation trigger
unless a defined stop condition overrides it.

FR-2: Default Continuation Policy
After each checkpoint, the system evaluates whether continuation
is allowed and expected. If there is a meaningful next canonical step,
no explicit stop condition is active, and no escalation condition
is triggered, then the system should continue by default.
"""

from datetime import datetime
from typing import Any

from runtime.continuation_types import (
    ExecutionState,
    CheckpointType,
    CanonicalStage,
    ContinuationDecision,
    ContinuityArtifact,
    StopCondition,
    TerminalStopType,
    checkpoint_from_status,
    is_valid_stop_reason,
)
from runtime.stop_conditions import (
    evaluate_all_stop_conditions,
    resolve_next_canonical_stage,
    has_meaningful_next_step,
)


def evaluate_continuation(
    runstate: dict[str, Any],
    execution_result: dict[str, Any],
    checkpoint_type: CheckpointType | None = None,
) -> ContinuationDecision:
    """Evaluate continuation after a checkpoint.
    
    This is the main entry point for continuation evaluation.
    
    Args:
        runstate: Current RunState
        execution_result: Execution result from run-day
        checkpoint_type: Type of checkpoint event
        
    Returns:
        ContinuationDecision with explicit reasoning
    """
    if checkpoint_type is None:
        status = execution_result.get("status", "success")
        checkpoint_type = checkpoint_from_status(status)
    
    stop_condition = evaluate_all_stop_conditions(runstate, execution_result)
    
    if stop_condition:
        return _build_stop_decision(checkpoint_type, stop_condition, execution_result)
    
    next_stage = resolve_next_canonical_stage(runstate, execution_result)
    
    if not next_stage and not has_meaningful_next_step(runstate, execution_result):
        return _build_no_next_step_decision(checkpoint_type, execution_result)
    
    return _build_continue_decision(
        checkpoint_type,
        next_stage,
        runstate,
        execution_result,
    )


def _build_stop_decision(
    checkpoint_type: CheckpointType,
    stop_condition: StopCondition,
    execution_result: dict[str, Any],
) -> ContinuationDecision:
    """Build decision for stop case."""
    state = ExecutionState.STOP
    if stop_condition.stop_type.value in ["escalation_required"]:
        state = ExecutionState.ESCALATE
    elif stop_condition.stop_type.value in ["external_blocker", "integrity_safety_pause"]:
        state = ExecutionState.BLOCKED
    
    return ContinuationDecision(
        state=state,
        checkpoint_type=checkpoint_type,
        stop_condition=stop_condition,
        continuation_allowed=False,
        escalation_required=state == ExecutionState.ESCALATE,
        reason=f"Stopped: {stop_condition.summary}",
        artifacts_for_next_stage=_get_artifacts_for_next_stage(execution_result),
        candidate_next_actions=[stop_condition.suggested_action],
    )


def _build_no_next_step_decision(
    checkpoint_type: CheckpointType,
    execution_result: dict[str, Any],
) -> ContinuationDecision:
    """Build decision when no meaningful next step exists."""
    return ContinuationDecision(
        state=ExecutionState.STOP,
        checkpoint_type=checkpoint_type,
        stop_condition=StopCondition(
            stop_type=TerminalStopType.NO_MEANINGFUL_NEXT_STEP,
            summary="No meaningful next step available",
            reason="All tasks completed, no further scope defined",
            required_to_continue="Add new tasks or complete feature",
            suggested_action="Review completed outputs and plan next phase",
        ),
        continuation_allowed=False,
        escalation_required=False,
        reason="Stopped: no meaningful next step",
        artifacts_for_next_stage=_get_artifacts_for_next_stage(execution_result),
        candidate_next_actions=["asyncdev complete-feature mark", "asyncdev plan-day create"],
    )


def _build_continue_decision(
    checkpoint_type: CheckpointType,
    next_stage: CanonicalStage | None,
    runstate: dict[str, Any],
    execution_result: dict[str, Any],
) -> ContinuationDecision:
    """Build decision for continue case."""
    next_action = execution_result.get("recommended_next_step", "")
    task_queue = runstate.get("task_queue", [])
    
    candidate_actions = []
    if task_queue:
        candidate_actions.append(f"Execute next task: {task_queue[0]}")
    if next_action:
        candidate_actions.append(next_action)
    if next_stage:
        candidate_actions.append(f"Enter {next_stage.value} stage")
    
    return ContinuationDecision(
        state=ExecutionState.CONTINUE,
        checkpoint_type=checkpoint_type,
        next_stage=next_stage,
        continuation_allowed=True,
        escalation_required=False,
        reason=f"Checkpoint reached: {checkpoint_type.value}. No stop conditions apply. Continuing to {next_stage.value if next_stage else 'next task'}.",
        artifacts_for_next_stage=_get_artifacts_for_next_stage(execution_result),
        candidate_next_actions=candidate_actions,
    )


def _get_artifacts_for_next_stage(execution_result: dict[str, Any]) -> list[str]:
    """Get list of artifacts for next stage consumption."""
    artifacts = execution_result.get("artifacts_created", [])
    return [a.get("path", "") for a in artifacts if a.get("path")]


def update_continuity_artifact(
    runstate: dict[str, Any],
    decision: ContinuationDecision,
    execution_result: dict[str, Any],
) -> ContinuityArtifact:
    """Update continuity artifact in RunState.
    
    FR-5: Program State Continuity Artifact
    Maintains machine-readable continuity artifact that survives
    checkpoint boundaries.
    """
    existing = runstate.get("continuity_context", {})
    
    if existing:
        continuity = ContinuityArtifact.from_dict(existing)
    else:
        continuity = ContinuityArtifact()
    
    continuity.latest_checkpoint = execution_result.get("execution_id", "")
    continuity.latest_checkpoint_type = decision.checkpoint_type
    continuity.continuation_allowed = decision.continuation_allowed
    continuity.next_intended_stage = decision.next_stage
    continuity.active_blockers = runstate.get("blocked_items", [])
    continuity.escalation_required = decision.escalation_required
    continuity.stop_reason = decision.reason if decision.state == ExecutionState.STOP else ""
    continuity.last_meaningful_outputs = decision.artifacts_for_next_stage
    continuity.candidate_next_actions = decision.candidate_next_actions
    continuity.updated_at = datetime.now().isoformat()
    
    return continuity


def should_auto_proceed_to_next_stage(
    runstate: dict[str, Any],
    execution_result: dict[str, Any],
) -> tuple[bool, str]:
    """Check if system should auto-proceed to next canonical stage.
    
    Simplified check for immediate continuation decision.
    Returns (should_proceed, reason).
    """
    decision = evaluate_continuation(runstate, execution_result)
    
    if decision.should_continue():
        return True, decision.reason
    
    return False, decision.reason


def get_continuation_summary(decision: ContinuationDecision) -> str:
    """Generate human-readable continuation summary."""
    if decision.state == ExecutionState.CONTINUE:
        next_stage = decision.next_stage.value if decision.next_stage else "next task"
        return f"Checkpoint reached. Continuing to {next_stage}. No stop conditions apply."
    
    if decision.state == ExecutionState.ESCALATE:
        return f"Checkpoint reached. Escalation required: {decision.stop_condition.summary if decision.stop_condition else 'decision pending'}"
    
    if decision.state == ExecutionState.BLOCKED:
        return f"Checkpoint reached. Blocked: {decision.stop_condition.summary if decision.stop_condition else 'external blocker'}"
    
    if decision.state == ExecutionState.STOP:
        return f"Checkpoint reached. Stopping: {decision.stop_condition.summary if decision.stop_condition else 'no next step'}"
    
    return f"Checkpoint reached. State: {decision.state.value}"


def validate_stop_reason(reason: str) -> tuple[bool, str]:
    """Validate that a stop reason is legitimate.
    
    FR-8: Human Escalation Discipline
    Phase boundary alone is NOT a sufficient stop reason.
    """
    if not is_valid_stop_reason(reason):
        return False, f"Invalid stop reason: '{reason}'. Phase boundary is not sufficient."
    
    return True, "Valid stop reason"


def get_next_action_for_stage(stage: CanonicalStage) -> str:
    """Get suggested CLI action for a canonical stage."""
    stage_actions = {
        CanonicalStage.DOGFOOD: "Run dogfood testing on current implementation",
        CanonicalStage.FRICTION_CAPTURE: "Capture friction observations and feedback",
        CanonicalStage.AUDIT_CONSOLIDATION: "Consolidate audit findings",
        CanonicalStage.REPAIR_LOOP: "Address pending issues and repairs",
        CanonicalStage.NEXT_SCOPE_DERIVATION: "Derive scope for next iteration",
        CanonicalStage.NEXT_ITERATION_PLANNING: "Plan next iteration",
        CanonicalStage.EXECUTION_PACK_GENERATION: "asyncdev plan-day create",
        CanonicalStage.PRODUCT_EVOLUTION: "Continue product development",
        CanonicalStage.VERIFICATION: "Verify current implementation",
        CanonicalStage.CLOSEOUT: "asyncdev complete-feature mark",
    }
    
    return stage_actions.get(stage, "Continue with next step")


def apply_continuation_decision_to_runstate(
    runstate: dict[str, Any],
    decision: ContinuationDecision,
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    """Apply continuation decision to RunState.
    
    Updates RunState fields based on continuation decision.
    """
    continuity = update_continuity_artifact(runstate, decision, execution_result)
    runstate["continuity_context"] = continuity.to_dict()
    
    runstate["next_recommended_action"] = get_continuation_summary(decision)
    
    if decision.candidate_next_actions:
        runstate["continuation_candidate_actions"] = decision.candidate_next_actions
    
    if decision.next_stage:
        runstate["next_intended_stage"] = decision.next_stage.value
    
    if decision.state == ExecutionState.CONTINUE:
        runstate["current_phase"] = "planning"
        runstate["continuation_allowed"] = True
    elif decision.state == ExecutionState.ESCALATE:
        runstate["current_phase"] = "reviewing"
        runstate["continuation_allowed"] = False
    elif decision.state == ExecutionState.BLOCKED:
        runstate["current_phase"] = "blocked"
        runstate["continuation_allowed"] = False
    elif decision.state == ExecutionState.STOP:
        if decision.stop_condition and decision.stop_condition.stop_type.value == "no_meaningful_next_step":
            runstate["current_phase"] = "completed"
        else:
            runstate["current_phase"] = "reviewing"
        runstate["continuation_allowed"] = False
    
    runstate["last_action"] = f"Continuation evaluated: {decision.state.value}"
    runstate["updated_at"] = datetime.now().isoformat()
    
    return runstate