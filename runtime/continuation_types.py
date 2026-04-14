"""Continuation semantics types for Feature 037.

Defines execution states, checkpoint types, and continuation outcomes
for the Continuous Canonical Loop Continuation Semantics.

Core Principle: Successful progress is a continuation trigger unless
a defined stop condition overrides it.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionState(str, Enum):
    """Execution states for continuation semantics.
    
    These states are operational, not merely descriptive.
    They determine what happens after a checkpoint.
    """
    
    CHECKPOINT = "checkpoint"  # Milestone reached, evaluate continuation
    CONTINUE = "continue"      # Proceed to next canonical stage
    STOP = "stop"              # Terminal stop with explicit reason
    ESCALATE = "escalate"      # Human decision required before continuation
    BLOCKED = "blocked"        # External blocker prevents continuation
    AWAITING_INPUT = "awaiting_input"  # Waiting for external input


class CheckpointType(str, Enum):
    """Types of checkpoint events.
    
    Checkpoint events are milestones that should trigger
    continuation evaluation, not automatic termination.
    """
    
    ITERATION_COMPLETED = "iteration_completed"
    IMPLEMENTATION_DONE = "implementation_done"
    TESTS_PASSED = "tests_passed"
    AUDIT_GENERATED = "audit_generated"
    COMMIT_COMPLETED = "commit_completed"
    PUSH_COMPLETED = "push_completed"
    DOGFOOD_REPORT_GENERATED = "dogfood_report_generated"
    REVIEW_PACK_GENERATED = "review_pack_generated"
    FEATURE_MILESTONE = "feature_milestone"


class TerminalStopType(str, Enum):
    """Types of terminal stop events.
    
    Terminal stops require explicit reasons matching
    valid stop conditions. Phase boundary alone is NOT
    a sufficient stop reason.
    """
    
    ESCALATION_REQUIRED = "escalation_required"
    NO_MEANINGFUL_NEXT_STEP = "no_meaningful_next_step"
    EXTERNAL_BLOCKER = "external_blocker"
    INTEGRITY_SAFETY_PAUSE = "integrity_safety_pause"
    POLICY_BASED_STOP = "policy_based_stop"
    HUMAN_REQUESTED_STOP = "human_requested_stop"


class CanonicalStage(str, Enum):
    """Canonical next stages for continuation.
    
    After a checkpoint, the system may continue into
    one of these stages based on current artifacts
    and governance context.
    """
    
    DOGFOOD = "dogfood"
    FRICTION_CAPTURE = "friction_capture"
    AUDIT_CONSOLIDATION = "audit_consolidation"
    REPAIR_LOOP = "repair_loop"
    NEXT_SCOPE_DERIVATION = "next_scope_derivation"
    NEXT_ITERATION_PLANNING = "next_iteration_planning"
    EXECUTION_PACK_GENERATION = "execution_pack_generation"
    PRODUCT_EVOLUTION = "product_evolution"
    VERIFICATION = "verification"
    CLOSEOUT = "closeout"


@dataclass
class StopCondition:
    """Represents a stop condition with full context.
    
    Stop conditions are explicit and inspectable.
    They must match a valid TerminalStopType.
    """
    
    stop_type: TerminalStopType
    summary: str
    reason: str
    required_to_continue: str
    suggested_action: str
    details: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stop_type": self.stop_type.value,
            "summary": self.summary,
            "reason": self.reason,
            "required_to_continue": self.required_to_continue,
            "suggested_action": self.suggested_action,
            "details": self.details,
        }


@dataclass
class ContinuationDecision:
    """Decision result from ContinuationEvaluator.
    
    This is the output of evaluating whether to continue
    after a checkpoint. It provides clear, inspectable
    reasoning for the decision.
    """
    
    state: ExecutionState
    checkpoint_type: CheckpointType | None = None
    stop_condition: StopCondition | None = None
    next_stage: CanonicalStage | None = None
    continuation_allowed: bool = True
    escalation_required: bool = False
    reason: str = ""
    artifacts_for_next_stage: list[str] = field(default_factory=list)
    candidate_next_actions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "state": self.state.value,
            "checkpoint_type": self.checkpoint_type.value if self.checkpoint_type else None,
            "stop_condition": self.stop_condition.to_dict() if self.stop_condition else None,
            "next_stage": self.next_stage.value if self.next_stage else None,
            "continuation_allowed": self.continuation_allowed,
            "escalation_required": self.escalation_required,
            "reason": self.reason,
            "artifacts_for_next_stage": self.artifacts_for_next_stage,
            "candidate_next_actions": self.candidate_next_actions,
        }
    
    def is_checkpoint(self) -> bool:
        """Check if this is a checkpoint (non-terminal)."""
        return self.state == ExecutionState.CHECKPOINT
    
    def should_continue(self) -> bool:
        """Check if continuation should proceed."""
        return self.state in (ExecutionState.CONTINUE, ExecutionState.CHECKPOINT)
    
    def requires_escalation(self) -> bool:
        """Check if human escalation is required."""
        return self.state == ExecutionState.ESCALATE or self.escalation_required


@dataclass
class ContinuityArtifact:
    """Machine-readable continuity artifact for checkpoint boundaries.
    
    This artifact survives checkpoint boundaries and enables
    autonomous continuation and later audit.
    
    Stored in RunState as 'continuity_context' field.
    """
    
    latest_checkpoint: str = ""
    latest_checkpoint_type: CheckpointType | None = None
    continuation_allowed: bool = True
    next_intended_stage: CanonicalStage | None = None
    active_blockers: list[str] = field(default_factory=list)
    escalation_required: bool = False
    stop_reason: str = ""
    last_meaningful_outputs: list[str] = field(default_factory=list)
    candidate_next_actions: list[str] = field(default_factory=list)
    updated_at: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for RunState storage."""
        return {
            "latest_checkpoint": self.latest_checkpoint,
            "latest_checkpoint_type": self.latest_checkpoint_type.value if self.latest_checkpoint_type else None,
            "continuation_allowed": self.continuation_allowed,
            "next_intended_stage": self.next_intended_stage.value if self.next_intended_stage else None,
            "active_blockers": self.active_blockers,
            "escalation_required": self.escalation_required,
            "stop_reason": self.stop_reason,
            "last_meaningful_outputs": self.last_meaningful_outputs,
            "candidate_next_actions": self.candidate_next_actions,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContinuityArtifact":
        """Create from dictionary."""
        checkpoint_type = None
        if data.get("latest_checkpoint_type"):
            try:
                checkpoint_type = CheckpointType(data["latest_checkpoint_type"])
            except ValueError:
                pass
        
        next_stage = None
        if data.get("next_intended_stage"):
            try:
                next_stage = CanonicalStage(data["next_intended_stage"])
            except ValueError:
                pass
        
        return cls(
            latest_checkpoint=data.get("latest_checkpoint", ""),
            latest_checkpoint_type=checkpoint_type,
            continuation_allowed=data.get("continuation_allowed", True),
            next_intended_stage=next_stage,
            active_blockers=data.get("active_blockers", []),
            escalation_required=data.get("escalation_required", False),
            stop_reason=data.get("stop_reason", ""),
            last_meaningful_outputs=data.get("last_meaningful_outputs", []),
            candidate_next_actions=data.get("candidate_next_actions", []),
            updated_at=data.get("updated_at", ""),
        )


# Human escalation discipline rules
# Phase boundary alone is NOT a sufficient stop reason

INVALID_STOP_REASONS = [
    "iteration ended cleanly",
    "commit was pushed",
    "next step is in a new logical phase",
    "work could be described as a new session",
    "phase boundary reached",
    "this would be a new session",
]

def is_valid_stop_reason(reason: str) -> bool:
    """Check if a stop reason is valid.
    
    Invalid reasons are those that cite phase boundaries
    or session-style completion without genuine blockers.
    """
    reason_lower = reason.lower()
    for invalid in INVALID_STOP_REASONS:
        if invalid in reason_lower:
            return False
    return True


def checkpoint_from_status(execution_status: str) -> CheckpointType:
    """Derive checkpoint type from execution status."""
    status_map = {
        "success": CheckpointType.ITERATION_COMPLETED,
        "partial": CheckpointType.ITERATION_COMPLETED,
        "tests_passed": CheckpointType.TESTS_PASSED,
        "committed": CheckpointType.COMMIT_COMPLETED,
        "pushed": CheckpointType.PUSH_COMPLETED,
    }
    return status_map.get(execution_status, CheckpointType.ITERATION_COMPLETED)


# Type aliases for common usage
ContinuationOutcome = ContinuationDecision
CheckpointEvent = CheckpointType