"""Email failure handling for operational robustness (Feature 049).

Handles send failures, timeouts, invalid replies, duplicates, and partial states.
Ensures the email channel behaves safely under failure conditions.
"""

from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
import json


class FailureType(str, Enum):
    """Types of failures in email channel."""
    
    SEND_FAILED = "send_failed"
    SEND_RETRY_EXCEEDED = "send_retry_exceeded"
    TIMEOUT_NO_REPLY = "timeout_no_reply"
    INVALID_REPLY_SYNTAX = "invalid_reply_syntax"
    INVALID_REPLY_OPTION = "invalid_reply_option"
    DUPLICATE_REPLY = "duplicate_reply"
    EXPIRED_REQUEST = "expired_request"
    PARTIAL_STATE = "partial_state"
    RECOVERY_NEEDED = "recovery_needed"


class TimeoutBehavior(str, Enum):
    """Behavior when request times out without reply."""
    
    WAIT = "wait"
    DEFER = "defer"
    DEFAULT_OPTION = "default_option"
    ESCALATE = "escalate"
    MARK_UNRESOLVED = "mark_unresolved"


class RecoveryAction(str, Enum):
    """Actions for recovery from failure states."""
    
    RETRY_SEND = "retry_send"
    USE_DEFAULT_PATH = "use_default_path"
    REQUEST_NEW_DECISION = "request_new_decision"
    MARK_BLOCKED = "mark_blocked"
    CONTINUE_AUTONOMOUSLY = "continue_autonomously"
    PAUSE_FOR_HUMAN = "pause_for_human"


DEFAULT_TIMEOUT_HOURS = 48
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_INTERVAL_HOURS = 1


class FailureRecordStore:
    """Store for tracking failure records."""
    
    DEFAULT_FAILURES_PATH = ".runtime/email-failures"
    
    def __init__(self, runtime_path: Path) -> None:
        self.runtime_path = runtime_path
        self.failures_path = runtime_path / self.DEFAULT_FAILURES_PATH
        self.failures_path.mkdir(parents=True, exist_ok=True)
    
    def record_failure(
        self,
        request_id: str,
        failure_type: FailureType,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a failure event.
        
        Args:
            request_id: Decision request ID
            failure_type: Type of failure
            details: Additional details
            
        Returns:
            Failure record
        """
        failure_id = f"fail-{datetime.now().strftime('%Y%m%d%H%M%S')}-{request_id}"
        now = datetime.now().isoformat()
        
        record = {
            "failure_id": failure_id,
            "request_id": request_id,
            "failure_type": failure_type.value,
            "occurred_at": now,
            "details": details or {},
            "resolved": False,
            "resolved_at": None,
            "resolution_action": None,
        }
        
        file_path = self.failures_path / f"{failure_id}.json"
        with open(file_path, "w") as f:
            json.dump(record, f, indent=2)
        
        return record
    
    def load_failure(self, failure_id: str) -> dict[str, Any] | None:
        """Load failure record by ID."""
        file_path = self.failures_path / f"{failure_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return json.load(f)
    
    def list_failures(
        self,
        request_id: str | None = None,
        unresolved_only: bool = False,
    ) -> list[dict[str, Any]]:
        """List failure records."""
        failures = []
        for file_path in self.failures_path.glob("fail-*.json"):
            with open(file_path) as f:
                record = json.load(f)
                if request_id and record.get("request_id") != request_id:
                    continue
                if unresolved_only and record.get("resolved"):
                    continue
                failures.append(record)
        return sorted(failures, key=lambda r: r.get("occurred_at", ""))
    
    def resolve_failure(
        self,
        failure_id: str,
        resolution_action: RecoveryAction,
    ) -> dict[str, Any] | None:
        """Mark failure as resolved."""
        record = self.load_failure(failure_id)
        if not record:
            return None
        
        record["resolved"] = True
        record["resolved_at"] = datetime.now().isoformat()
        record["resolution_action"] = resolution_action.value
        
        file_path = self.failures_path / f"{failure_id}.json"
        with open(file_path, "w") as f:
            json.dump(record, f, indent=2)
        
        return record


def handle_send_failure(
    request: dict[str, Any],
    error_message: str,
    retry_count: int = 0,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> tuple[FailureType, RecoveryAction, str]:
    """Handle email send failure.
    
    Args:
        request: Decision request that failed to send
        error_message: Error from send attempt
        retry_count: Current retry count
        max_retries: Maximum retries allowed
        
    Returns:
        (failure_type, recovery_action, explanation)
    """
    if retry_count < max_retries:
        return (
            FailureType.SEND_FAILED,
            RecoveryAction.RETRY_SEND,
            f"Send failed (attempt {retry_count + 1}/{max_retries}): {error_message}",
        )
    
    return (
        FailureType.SEND_RETRY_EXCEEDED,
        RecoveryAction.PAUSE_FOR_HUMAN,
        f"Send failed after {max_retries} attempts. Manual intervention required.",
    )


def handle_timeout(
    request: dict[str, Any],
    timeout_behavior: TimeoutBehavior = TimeoutBehavior.MARK_UNRESOLVED,
    default_option: str | None = None,
) -> tuple[FailureType, RecoveryAction, str, dict[str, Any]]:
    """Handle request timeout without reply.
    
    Args:
        request: Decision request that timed out
        timeout_behavior: Configured behavior for timeout
        default_option: Option to use if DEFAULT_OPTION behavior
        
    Returns:
        (failure_type, recovery_action, explanation, resolution_details)
    """
    sent_at = request.get("sent_at")
    hours_elapsed = 0
    if sent_at:
        sent_dt = datetime.fromisoformat(sent_at)
        hours_elapsed = (datetime.now() - sent_dt).total_seconds() / 3600
    
    resolution_details = {
        "hours_elapsed": hours_elapsed,
        "timeout_behavior": timeout_behavior.value,
        "resolved_at": datetime.now().isoformat(),
    }
    
    if timeout_behavior == TimeoutBehavior.WAIT:
        return (
            FailureType.TIMEOUT_NO_REPLY,
            RecoveryAction.PAUSE_FOR_HUMAN,
            f"Waiting for reply after {hours_elapsed:.1f} hours",
            resolution_details,
        )
    
    elif timeout_behavior == TimeoutBehavior.DEFER:
        resolution_details["resolution"] = "DEFER"
        resolution_details["resolution_value"] = "timeout_defer"
        return (
            FailureType.TIMEOUT_NO_REPLY,
            RecoveryAction.USE_DEFAULT_PATH,
            f"Timeout after {hours_elapsed:.1f} hours, deferring decision",
            resolution_details,
        )
    
    elif timeout_behavior == TimeoutBehavior.DEFAULT_OPTION:
        if default_option:
            resolution_details["resolution"] = f"DECISION {default_option}"
            resolution_details["resolution_value"] = default_option
            return (
                FailureType.TIMEOUT_NO_REPLY,
                RecoveryAction.USE_DEFAULT_PATH,
                f"Timeout after {hours_elapsed:.1f} hours, using default option {default_option}",
                resolution_details,
            )
        else:
            return (
                FailureType.TIMEOUT_NO_REPLY,
                RecoveryAction.MARK_BLOCKED,
                f"Timeout after {hours_elapsed:.1f} hours, no default option configured",
                resolution_details,
            )
    
    elif timeout_behavior == TimeoutBehavior.ESCALATE:
        return (
            FailureType.TIMEOUT_NO_REPLY,
            RecoveryAction.REQUEST_NEW_DECISION,
            f"Timeout after {hours_elapsed:.1f} hours, escalating with new request",
            resolution_details,
        )
    
    else:
        return (
            FailureType.TIMEOUT_NO_REPLY,
            RecoveryAction.MARK_BLOCKED,
            f"Timeout after {hours_elapsed:.1f} hours, marking as unresolved",
            resolution_details,
        )


def handle_invalid_reply(
    request: dict[str, Any],
    reply_text: str,
    validation_error: str,
    guidance: str | None = None,
) -> tuple[FailureType, RecoveryAction, str]:
    """Handle invalid reply received.
    
    Args:
        request: Decision request
        reply_text: Invalid reply text
        validation_error: Validation error message
        guidance: Guidance for correct reply
        
    Returns:
        (failure_type, recovery_action, explanation)
    """
    failure_type = FailureType.INVALID_REPLY_SYNTAX
    
    if "invalid option" in validation_error.lower():
        failure_type = FailureType.INVALID_REPLY_OPTION
    
    if "expired" in validation_error.lower():
        failure_type = FailureType.EXPIRED_REQUEST
    
    if guidance:
        explanation = f"Invalid reply '{reply_text}': {validation_error}. Guidance: {guidance}"
    else:
        options = request.get("options", [])
        option_ids = [opt.get("id") for opt in options]
        valid_commands = f"DECISION {option_ids[0]}, DEFER, RETRY"
        explanation = f"Invalid reply '{reply_text}': {validation_error}. Valid commands: {valid_commands}"
    
    return (
        failure_type,
        RecoveryAction.PAUSE_FOR_HUMAN,
        explanation,
    )


def detect_duplicate_reply(
    request: dict[str, Any],
    reply_text: str,
    previous_replies: list[dict[str, Any]] | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """Detect if reply is duplicate of previous.
    
    Args:
        request: Decision request
        reply_text: New reply text
        previous_replies: Previous reply records
        
    Returns:
        (is_duplicate, previous_reply_if_found)
    """
    if request.get("status") == "resolved":
        return (
            True,
            {
                "resolution": request.get("resolution"),
                "resolved_at": request.get("resolved_at"),
            },
        )
    
    if previous_replies:
        normalized_new = reply_text.strip().upper()
        for prev in previous_replies:
            prev_text = prev.get("reply_raw_text", "")
            normalized_prev = prev_text.strip().upper()
            if normalized_new == normalized_prev:
                return (True, prev)
    
    return (False, None)


def check_partial_state(
    request: dict[str, Any],
    expected_fields: list[str] | None = None,
) -> tuple[bool, list[str], str]:
    """Check if request has partial/incomplete state.
    
    Args:
        request: Decision request
        expected_fields: Fields that should be present
        
    Returns:
        (is_partial, missing_fields, explanation)
    """
    default_expected = [
        "decision_request_id",
        "product_id",
        "feature_id",
        "question",
        "options",
        "status",
    ]
    
    expected = expected_fields or default_expected
    missing = []
    
    for field in expected:
        if field not in request or request[field] is None:
            missing.append(field)
    
    is_partial = len(missing) > 0
    
    if is_partial:
        explanation = f"Partial state: missing fields {missing}"
    else:
        explanation = "Complete state: all expected fields present"
    
    return (is_partial, missing, explanation)


def get_recovery_recommendation(
    failure_type: FailureType,
    request: dict[str, Any],
    policy_mode: str = "balanced",
) -> tuple[RecoveryAction, str]:
    """Get recommended recovery action for failure type.
    
    Args:
        failure_type: Type of failure
        request: Decision request
        policy_mode: Current policy mode
        
    Returns:
        (recommended_action, explanation)
    """
    if failure_type == FailureType.SEND_FAILED:
        if policy_mode == "low_interruption":
            return (
                RecoveryAction.CONTINUE_AUTONOMOUSLY,
                "Low interruption mode: continuing autonomously despite send failure",
            )
        return (
            RecoveryAction.RETRY_SEND,
            "Standard recovery: retry send with interval",
        )
    
    if failure_type == FailureType.SEND_RETRY_EXCEEDED:
        return (
            RecoveryAction.PAUSE_FOR_HUMAN,
            "Send retries exhausted, requires human intervention",
        )
    
    if failure_type == FailureType.TIMEOUT_NO_REPLY:
        if policy_mode == "conservative":
            return (
                RecoveryAction.PAUSE_FOR_HUMAN,
                "Conservative mode: pausing for human decision",
            )
        elif policy_mode == "low_interruption":
            default_option = request.get("recommendation")
            if default_option:
                return (
                    RecoveryAction.USE_DEFAULT_PATH,
                    f"Low interruption mode: using recommendation {default_option}",
                )
            return (
                RecoveryAction.CONTINUE_AUTONOMOUSLY,
                "Low interruption mode: continuing autonomously",
            )
        return (
            RecoveryAction.MARK_BLOCKED,
            "Balanced mode: marking as blocked, awaiting resolution",
        )
    
    if failure_type in [FailureType.INVALID_REPLY_SYNTAX, FailureType.INVALID_REPLY_OPTION]:
        return (
            RecoveryAction.PAUSE_FOR_HUMAN,
            "Invalid reply requires human correction",
        )
    
    if failure_type == FailureType.DUPLICATE_REPLY:
        return (
            RecoveryAction.CONTINUE_AUTONOMOUSLY,
            "Duplicate reply, already resolved",
        )
    
    if failure_type == FailureType.EXPIRED_REQUEST:
        if policy_mode == "low_interruption":
            return (
                RecoveryAction.REQUEST_NEW_DECISION,
                "Request expired, creating new decision request",
            )
        return (
            RecoveryAction.PAUSE_FOR_HUMAN,
            "Request expired, human review needed",
        )
    
    if failure_type == FailureType.PARTIAL_STATE:
        return (
            RecoveryAction.MARK_BLOCKED,
            "Partial state detected, marking as blocked",
        )
    
    return (
        RecoveryAction.PAUSE_FOR_HUMAN,
        "Unknown failure type, pausing for human review",
    )


def format_failure_summary(
    failure_type: FailureType,
    recovery_action: RecoveryAction,
    explanation: str,
    resolved: bool = False,
) -> str:
    """Format failure as human-readable summary.
    
    Args:
        failure_type: Type of failure
        recovery_action: Action taken
        explanation: Explanation
        resolved: Whether resolved
        
    Returns:
        Human-readable summary
    """
    lines = []
    
    lines.append(f"## Failure: {failure_type.value}")
    lines.append("")
    lines.append(f"**Status:** {'Resolved' if resolved else 'Unresolved'}")
    lines.append(f"**Recovery Action:** {recovery_action.value}")
    lines.append("")
    lines.append(f"**Explanation:** {explanation}")
    
    return "\n".join(lines)


def get_timeout_policy(
    policy_mode: str,
    request_category: str,
) -> TimeoutBehavior:
    """Get timeout behavior based on policy mode and request category.
    
    Args:
        policy_mode: Current policy mode
        request_category: Category of decision request
        
    Returns:
        Timeout behavior for this context
    """
    if request_category in ["critical", "approval", "architecture"]:
        return TimeoutBehavior.ESCALATE
    
    if policy_mode == "conservative":
        return TimeoutBehavior.WAIT
    
    if policy_mode == "low_interruption":
        if request_category in ["routine", "technical"]:
            return TimeoutBehavior.DEFAULT_OPTION
        return TimeoutBehavior.DEFER
    
    return TimeoutBehavior.MARK_UNRESOLVED


def validate_state_consistency(
    request: dict[str, Any],
    runstate: dict[str, Any],
) -> tuple[bool, list[str], str]:
    """Validate consistency between request state and RunState.
    
    Args:
        request: Decision request
        runstate: Current RunState
        
    Returns:
        (is_consistent, inconsistencies, explanation)
    """
    inconsistencies = []
    
    request_id = request.get("decision_request_id")
    pending_requests = runstate.get("decision_request_pending")
    
    if request_id and pending_requests:
        if request_id != pending_requests:
            inconsistencies.append(f"Request ID mismatch: request={request_id}, runstate={pending_requests}")
    
    request_status = request.get("status")
    decisions_needed = runstate.get("decisions_needed", [])
    
    if request_status == "resolved" and len(decisions_needed) > 0:
        matching = any(d.get("request_id") == request_id for d in decisions_needed)
        if matching:
            inconsistencies.append("Request resolved but still in decisions_needed")
    
    if request_status in ["sent", "pending"] and len(decisions_needed) == 0:
        inconsistencies.append("Request pending but not in decisions_needed")
    
    is_consistent = len(inconsistencies) == 0
    
    if is_consistent:
        explanation = "State consistent: request and RunState aligned"
    else:
        explanation = f"State inconsistent: {inconsistencies}"
    
    return (is_consistent, inconsistencies, explanation)