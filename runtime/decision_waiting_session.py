"""Decision waiting session check - Feature 064.

Ensures blocking state is honored at session start and during TODO continuation.
"""

from pathlib import Path
from typing import Any

from runtime.state_store import StateStore
from runtime.webhook_poller import PollingDaemon
from runtime.resend_provider import load_resend_config


DECISION_POLL_INTERVAL = 60
DECISION_POLL_TIMEOUT = 3600


def check_blocking_state(project_path: Path) -> tuple[str, str | None]:
    """Check if RunState is in blocking state.
    
    Returns:
        (status, request_id) where status is:
        - "BLOCKED": current_phase is blocked
        - "WAITING_DECISION": decision_request_pending exists
        - "CLEAR": no blocking condition
    """
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if not runstate:
        return "CLEAR", None
    
    if runstate.get("current_phase") == "blocked":
        request_id = runstate.get("decision_request_pending")
        return "BLOCKED", request_id
    
    if runstate.get("decision_request_pending"):
        request_id = runstate.get("decision_request_pending")
        return "WAITING_DECISION", request_id
    
    return "CLEAR", None


def should_block_todo_continuation(project_path: Path) -> bool:
    """Check if TODO continuation should be blocked.
    
    This is called when system receives TODO CONTINUATION directive.
    Returns True if the directive should be ignored due to blocking state.
    """
    status, request_id = check_blocking_state(project_path)
    return status in ["BLOCKED", "WAITING_DECISION"]


def get_blocking_message(project_path: Path) -> str:
    """Get human-readable blocking message.
    
    Returns message explaining why progress is blocked.
    """
    status, request_id = check_blocking_state(project_path)
    
    if status == "CLEAR":
        return "No blocking condition - proceed with tasks"
    
    if status == "BLOCKED":
        return f"RunState is blocked. Cannot proceed. Waiting for decision reply to {request_id}"
    
    if status == "WAITING_DECISION":
        return f"Decision pending: {request_id}. Poll inbox before proceeding."
    
    return "Unknown blocking state"


def poll_and_wait(project_path: Path, request_id: str, timeout: int = DECISION_POLL_TIMEOUT) -> bool:
    """Poll for decision reply until resolved or timeout.
    
    Args:
        project_path: Project path
        request_id: Decision request ID to wait for
        timeout: Maximum wait time in seconds
        
    Returns:
        True if reply received and processed, False if timeout
    """
    config = load_resend_config(project_path / ".runtime" / "resend-config.json")
    
    if not config:
        return False
    
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        return False
    
    daemon = PollingDaemon(
        project_path=project_path,
        webhook_url=webhook_url,
        interval=DECISION_POLL_INTERVAL,
    )
    
    elapsed = 0
    while elapsed < timeout:
        pending = daemon.poll_pending_decisions_once()
        
        if pending:
            for decision in pending:
                if decision.get("id") == request_id:
                    daemon.process_pending_decision(decision)
                    return True
        
        elapsed += DECISION_POLL_INTERVAL
    
    return False


def session_startup_check(project_path: Path) -> dict[str, Any]:
    """Run blocking check at session start.
    
    This should be called BEFORE any TODO tasks are executed.
    
    Returns:
        Dict with status and action recommendation
    """
    status, request_id = check_blocking_state(project_path)
    
    result = {
        "status": status,
        "request_id": request_id,
        "should_poll": False,
        "message": "",
        "action": "",
    }
    
    if status == "CLEAR":
        result["message"] = "Ready to proceed"
        result["action"] = "continue"
        return result
    
    if status in ["BLOCKED", "WAITING_DECISION"]:
        result["should_poll"] = True
        result["message"] = get_blocking_message(project_path)
        result["action"] = "poll_and_wait"
        
    return result