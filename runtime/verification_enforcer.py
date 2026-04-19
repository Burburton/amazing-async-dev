"""Verification Enforcer - Feature 059.

Enforces completion of browser verification workflows,
preventing AI agents from stopping at "server started"
without completing actual verification.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.verification_session import (
    VerificationSessionManager,
    VerificationSessionStatus,
    format_reminder,
)


def create_verification_session(project_path: Path, project_id: str) -> dict[str, Any]:
    """Create verification session when dev server starts.

    Args:
        project_path: Project directory
        project_id: Project identifier

    Returns:
        Session info dict
    """
    manager = VerificationSessionManager(project_path)
    session = manager.create_session(project_id)

    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "timeout_seconds": session.timeout_seconds,
        "started_at": session.started_at.isoformat(),
    }


def register_dev_server(project_path: Path, url: str, port: int, pid: int) -> None:
    """Register dev server startup in verification session.

    Args:
        project_path: Project directory
        url: Dev server URL
        port: Dev server port
        pid: Process ID
    """
    manager = VerificationSessionManager(project_path)
    manager.start_dev_server(url, port, pid)


def begin_verification(project_path: Path) -> None:
    """Mark verification attempt as started."""
    manager = VerificationSessionManager(project_path)
    manager.start_verification()


def complete_verification(project_path: Path, result: dict[str, Any]) -> None:
    """Mark verification as complete with result."""
    manager = VerificationSessionManager(project_path)
    manager.complete_verification(result)


def check_verification_status(project_path: Path) -> dict[str, Any]:
    """Check verification session status.

    Returns enforcement info:
    - pending: Verification must continue
    - complete: Verification done
    - timeout: Timeout exceeded, must record exception
    """
    manager = VerificationSessionManager(project_path)

    if manager.check_timeout():
        timeout_result = manager.enforce_timeout()
        return {
            "status": "timeout",
            "must_action": "record_exception",
            "timeout_result": timeout_result,
        }

    session_status = manager.get_session_status()

    if not session_status.get("active"):
        return {"status": "no_session"}

    if session_status.get("verification_complete"):
        return {"status": "complete"}

    reminder = manager.get_reminder()

    return {
        "status": "pending",
        "must_action": "continue_verification",
        "session_status": session_status,
        "reminder": format_reminder(reminder) if reminder else None,
    }


def enforce_completion(project_path: Path) -> dict[str, Any]:
    """Enforce verification completion.

    Called by system hook when AI agent stops without completing verification.

    Returns:
        Enforcement result with must_action
    """
    manager = VerificationSessionManager(project_path)

    if not manager.active_session:
        return {"status": "no_session", "enforced": False}

    if manager.active_session.verification_complete:
        return {"status": "complete", "enforced": False}

    if manager.check_timeout():
        timeout_result = manager.enforce_timeout()
        return {
            "status": "timeout",
            "enforced": True,
            "action_taken": "recorded_timeout_exception",
            "result": timeout_result,
        }

    reminder = manager.get_reminder()

    return {
        "status": "pending",
        "enforced": True,
        "action_taken": "reminder_sent",
        "reminder": format_reminder(reminder) if reminder else None,
        "must_continue": True,
    }


def get_browser_verification_for_execution_result(project_path: Path) -> dict[str, Any]:
    """Get browser_verification field for ExecutionResult.

    Ensures ExecutionResult has correct browser_verification data
    based on session status.

    Returns:
        browser_verification dict for ExecutionResult
    """
    manager = VerificationSessionManager(project_path)

    if not manager.active_session:
        return {
            "executed": False,
            "exception_reason": "no_verification_session",
            "exception_details": "No verification session was created",
        }

    session = manager.active_session

    if session.verification_complete and session.result:
        return session.result

    if session.status == VerificationSessionStatus.TIMEOUT:
        return {
            "executed": False,
            "exception_reason": session.exception_reason,
            "exception_details": session.exception_details,
        }

    if session.status == VerificationSessionStatus.EXCEPTION:
        return {
            "executed": False,
            "exception_reason": session.exception_reason,
            "exception_details": session.exception_details,
        }

    elapsed = manager.get_elapsed_seconds()
    remaining = manager.get_remaining_seconds()

    return {
        "executed": False,
        "exception_reason": "verification_pending",
        "exception_details": (
            f"Verification session pending. "
            f"Elapsed: {elapsed:.0f}s, Remaining: {remaining:.0f}s. "
            f"Dev server: {session.dev_server_url or 'not started'}"
        ),
        "session_id": session.session_id,
        "must_complete": True,
    }


def can_mark_execution_success(project_path: Path) -> tuple[bool, str]:
    """Check if ExecutionResult can be marked as success.

    ExecutionResult cannot be marked success while verification is pending.

    Returns:
        Tuple of (can_mark, reason)
    """
    manager = VerificationSessionManager(project_path)

    if not manager.active_session:
        return True, "No verification session"

    if manager.active_session.verification_complete:
        return True, "Verification complete"

    if manager.check_timeout():
        return True, "Timeout - exception recorded"

    elapsed = manager.get_elapsed_seconds()
    remaining = manager.get_remaining_seconds()

    return False, (
        f"Verification pending - cannot mark success. "
        f"Elapsed: {elapsed:.0f}s, Remaining: {remaining:.0f}s. "
        f"Complete verification first or record exception."
    )