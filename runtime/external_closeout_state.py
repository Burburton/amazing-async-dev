"""External Execution Closeout State Model - Feature 061.

Defines the structured state model for external execution closeout lifecycle.
Separates external execution lifecycle, verification lifecycle, and terminal closeout outcome.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CloseoutState(str, Enum):
    """Closeout lifecycle states for external execution (Feature 061 section 6.4).
    
    States clearly separate:
    - external execution lifecycle (triggered -> pending -> result_detected)
    - verification lifecycle (required -> running -> completed)
    - terminal closeout outcome (success, failure, timeout, recovery_required)
    """
    # External execution lifecycle
    EXTERNAL_EXECUTION_TRIGGERED = "external_execution_triggered"
    EXTERNAL_EXECUTION_PENDING = "external_execution_pending"
    EXTERNAL_EXECUTION_RESULT_DETECTED = "external_execution_result_detected"
    
    # Verification lifecycle
    POST_EXTERNAL_VERIFICATION_REQUIRED = "post_external_verification_required"
    POST_EXTERNAL_VERIFICATION_RUNNING = "post_external_verification_running"
    POST_EXTERNAL_VERIFICATION_COMPLETED = "post_external_verification_completed"
    
    # Stall detection
    EXTERNAL_EXECUTION_STALLED = "external_execution_stalled"
    
    # Terminal states
    CLOSEOUT_TIMEOUT = "closeout_timeout"
    CLOSEOUT_COMPLETED_SUCCESS = "closeout_completed_success"
    CLOSEOUT_COMPLETED_FAILURE = "closeout_completed_failure"
    CLOSEOUT_RECOVERY_REQUIRED = "closeout_recovery_required"
    
    @classmethod
    def terminal_states(cls) -> list[CloseoutState]:
        """Return states that are valid terminal states for closeout."""
        return [
            cls.CLOSEOUT_COMPLETED_SUCCESS,
            cls.CLOSEOUT_COMPLETED_FAILURE,
            cls.CLOSEOUT_TIMEOUT,
            cls.CLOSEOUT_RECOVERY_REQUIRED,
        ]
    
    @classmethod
    def success_terminal_states(cls) -> list[CloseoutState]:
        """Return terminal states that indicate successful completion."""
        return [cls.CLOSEOUT_COMPLETED_SUCCESS]
    
    def is_terminal(self) -> bool:
        """Check if this state is terminal."""
        return self in CloseoutState.terminal_states()
    
    def is_success(self) -> bool:
        """Check if this terminal state indicates success."""
        return self in CloseoutState.success_terminal_states()


class CloseoutTerminalClassification(str, Enum):
    """Final classification of external closeout outcome.
    
    Used for ExecutionResult.status and success progression gating.
    """
    SUCCESS = "success"
    FAILURE = "failure"
    VERIFICATION_FAILURE = "verification_failure"
    CLOSEOUT_TIMEOUT = "closeout_timeout"
    STALLED = "stalled"
    RECOVERY_REQUIRED = "recovery_required"
    
    def allows_success_progression(self) -> bool:
        """Check if this classification allows execution success progression."""
        return self == CloseoutTerminalClassification.SUCCESS


@dataclass
class CloseoutResult:
    """Result of external execution closeout orchestration.
    
    Captures the complete closeout lifecycle from trigger to terminal state,
    suitable for ExecutionResult closeout fields.
    """
    closeout_state: CloseoutState
    terminal_classification: CloseoutTerminalClassification | None = None
    execution_result_detected: bool = False
    execution_result_valid: bool = False
    verification_required: bool = False
    verification_completed: bool = False
    verification_terminal_state: str | None = None
    poll_attempts: int = 0
    elapsed_seconds: float = 0.0
    timeout_seconds: int = 120
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str | None = None
    recovery_required: bool = False
    recovery_reason: str | None = None
    stall_detected: bool = False
    closeout_error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for ExecutionResult closeout fields."""
        return {
            "closeout_state": self.closeout_state.value,
            "closeout_terminal_state": self.terminal_classification.value if self.terminal_classification else None,
            "execution_result_detected": self.execution_result_detected,
            "execution_result_valid": self.execution_result_valid,
            "verification_required": self.verification_required,
            "verification_completed": self.verification_completed,
            "verification_terminal_state": self.verification_terminal_state,
            "poll_attempts": self.poll_attempts,
            "elapsed_seconds": self.elapsed_seconds,
            "timeout_seconds": self.timeout_seconds,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "recovery_required": self.recovery_required,
            "recovery_reason": self.recovery_reason,
            "stall_detected": self.stall_detected,
            "closeout_error": self.closeout_error,
        }
    
    def is_complete(self) -> bool:
        """Check if closeout reached a valid terminal state."""
        return self.closeout_state.is_terminal()
    
    def allows_success_progression(self) -> bool:
        """Check if closeout allows execution success progression."""
        if not self.is_complete():
            return False
        return self.terminal_classification is not None and self.terminal_classification.allows_success_progression()
    
    def get_gate_status(self) -> str:
        """Get completion gate status: 'allowed' or 'blocked'."""
        return "allowed" if self.allows_success_progression() else "blocked"


# Default timeout constants
DEFAULT_CLOSEOUT_TIMEOUT_SECONDS = 120
DEFAULT_POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 12  # 120 seconds / 10 seconds