"""Execution lifecycle event types for structured logging."""

from enum import Enum


class ExecutionEventType(str, Enum):
    """Types of execution lifecycle events to log.
    
    These events provide inspectable history of workflow actions,
    supporting recovery diagnosis and operational debugging.
    """
    
    # Day loop lifecycle
    PLAN_DAY_STARTED = "plan-day-started"
    PLAN_DAY_COMPLETED = "plan-day-completed"
    RUN_DAY_STARTED = "run-day-started"
    RUN_DAY_DISPATCHED = "run-day-dispatched"
    EXECUTION_RESULT_COLLECTED = "execution-result-collected"
    REVIEW_NIGHT_STARTED = "review-night-started"
    REVIEW_NIGHT_GENERATED = "review-night-generated"
    RESUME_NEXT_DAY_STARTED = "resume-next-day-started"
    
    # External execution mode
    EXTERNAL_EXECUTION_TRIGGERED = "external-execution-triggered"
    EXTERNAL_EXECUTION_AWAITING = "external-execution-awaiting"
    
    # State transitions
    BLOCKED_ENTERED = "blocked-entered"
    BLOCKED_RESOLVED = "blocked-resolved"
    FAILED_ENTERED = "failed-entered"
    FAILED_HANDLED = "failed-handled"
    
    # Decision handling
    DECISION_ESCALATED = "decision-escalated"
    DECISION_APPROVED = "decision-approved"
    DECISION_REVISED = "decision-revised"
    DECISION_DEFERRED = "decision-deferred"
    
    # Feature lifecycle
    COMPLETE_FEATURE = "complete-feature"
    ARCHIVE_FEATURE = "archive-feature"
    NEW_FEATURE = "new-feature"
    NEW_PRODUCT = "new-product"
    
    # Recovery actions
    RESUME_ATTEMPTED = "resume-attempted"
    RESUME_VALIDATED = "resume-validated"
    RESUME_BLOCKED = "resume-blocked"
    RECOVERY_GUIDANCE_PROVIDED = "recovery-guidance-provided"
    
    # Stop points
    NORMAL_STOP = "normal-stop"
    INTERRUPTED_STOP = "interrupted-stop"
    ERROR_STOP = "error-stop"


# Event metadata templates
EVENT_METADATA: dict[ExecutionEventType, dict[str, str]] = {
    ExecutionEventType.PLAN_DAY_STARTED: {
        "category": "lifecycle",
        "description": "Day planning phase started",
        "recovery_hint": "Check ExecutionPack creation status",
    },
    ExecutionEventType.PLAN_DAY_COMPLETED: {
        "category": "lifecycle",
        "description": "ExecutionPack created successfully",
        "recovery_hint": "Ready for run-day",
    },
    ExecutionEventType.RUN_DAY_STARTED: {
        "category": "lifecycle",
        "description": "Execution phase started",
        "recovery_hint": "Check execution result status",
    },
    ExecutionEventType.BLOCKED_ENTERED: {
        "category": "state-transition",
        "description": "Workflow entered blocked state",
        "recovery_hint": "Use resume-next-day unblock to resolve",
    },
    ExecutionEventType.BLOCKED_RESOLVED: {
        "category": "state-transition",
        "description": "Blocker resolved",
        "recovery_hint": "Ready to continue execution",
    },
    ExecutionEventType.FAILED_ENTERED: {
        "category": "state-transition",
        "description": "Execution failed",
        "recovery_hint": "Use resume-next-day handle-failed",
    },
    ExecutionEventType.RESUME_ATTEMPTED: {
        "category": "recovery",
        "description": "Resume attempted",
        "recovery_hint": "Check validation result",
    },
    ExecutionEventType.NORMAL_STOP: {
        "category": "stop",
        "description": "Normal end-of-day stop",
        "recovery_hint": "Ready to resume next day",
    },
    ExecutionEventType.INTERRUPTED_STOP: {
        "category": "stop",
        "description": "Workflow interrupted unexpectedly",
        "recovery_hint": "Inspect state and decide recovery action",
    },
}


def get_event_description(event_type: ExecutionEventType) -> str:
    """Get human-readable description for event type."""
    meta = EVENT_METADATA.get(event_type)
    return meta.get("description", event_type.value) if meta else event_type.value


def get_recovery_hint(event_type: ExecutionEventType) -> str | None:
    """Get recovery hint for event type."""
    meta = EVENT_METADATA.get(event_type)
    return meta.get("recovery_hint") if meta else None