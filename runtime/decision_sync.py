"""Decision sync layer for Feature 043 - Decision Application & Continuation Resume.

Provides bidirectional sync between DecisionRequestStore and RunState.decisions_needed.

This module is the ONLY pathway for decision state updates to ensure consistency.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
)


def sync_decision_to_runstate(
    request: dict[str, Any],
    runstate: dict[str, Any],
) -> dict[str, Any]:
    """Sync a decision request to RunState.decisions_needed.
    
    Creates decision entry in decisions_needed, sets decision_request_pending,
    and optionally sets current_phase to blocked.
    
    Args:
        request: Decision request dict from DecisionRequestStore
        runstate: Current RunState dict
        
    Returns:
        Updated RunState dict
    """
    request_id = request.get("decision_request_id", "")
    question = request.get("question", "")
    options = request.get("options", [])
    recommendation = request.get("recommendation", "")
    decision_type = request.get("decision_type", "technical")
    pause_category = request.get("pause_reason_category", "decision_required")
    
    # Create decision entry for RunState.decisions_needed
    decision_entry = {
        "decision": question,
        "decision_id": request_id,
        "options": [opt.get("label", opt.get("id", "")) for opt in options],
        "recommendation": recommendation,
        "impact": request.get("defer_impact", ""),
        "decision_type": decision_type,
        "source": "email_request",
        "request_id": request_id,
    }
    
    # Initialize decisions_needed if not present
    if "decisions_needed" not in runstate:
        runstate["decisions_needed"] = []
    
    # Check if this request is already in decisions_needed
    existing_ids = [
        d.get("request_id", d.get("decision_id", ""))
        for d in runstate["decisions_needed"]
    ]
    
    if request_id not in existing_ids:
        runstate["decisions_needed"].append(decision_entry)
    
    # Set decision request tracking fields
    runstate["decision_request_pending"] = request_id
    runstate["decision_request_sent_at"] = request.get("sent_at", datetime.now().isoformat())
    
    # Set phase to blocked if pause category requires it
    current_phase = runstate.get("current_phase", "executing")
    if pause_category in ["decision_required", "blocker", "scope_change"]:
        runstate["current_phase"] = "blocked"
    
    # Update last_action
    runstate["last_action"] = f"Decision request synced: {request_id}"
    
    return runstate


def sync_reply_to_runstate(
    request_id: str,
    reply: dict[str, Any],
    runstate: dict[str, Any],
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Sync email reply resolution to RunState.
    
    Removes matching entry from decisions_needed, sets last_decision_resolution,
    and sets phase for continuation based on reply.
    
    Args:
        request_id: Decision request ID
        reply: Reply record dict from reply_parser
        runstate: Current RunState dict
        action: Optional action mapping from reply_action_mapper
        
    Returns:
        Updated RunState dict
    """
    reply_value = reply.get("reply_value", "")
    reply_command = reply.get("parsed_result", {}).get("command", "")
    reply_argument = reply.get("parsed_result", {}).get("argument", "")
    
    # Remove matching entry from decisions_needed
    decisions_needed = runstate.get("decisions_needed", [])
    filtered_decisions = [
        d for d in decisions_needed
        if d.get("request_id", d.get("decision_id", "")) != request_id
    ]
    runstate["decisions_needed"] = filtered_decisions
    
    # Set last_decision_resolution
    resolution_record = {
        "request_id": request_id,
        "reply_command": reply_value,
        "reply_type": reply_command,
        "selected_option": reply_argument if reply_command == "DECISION" else None,
        "resolved_at": reply.get("received_at", datetime.now().isoformat()),
        "applied_action": action.get("runstate_action", "") if action else "",
    }
    runstate["last_decision_resolution"] = resolution_record
    
    # Clear decision_request_pending if all decisions resolved
    if len(runstate["decisions_needed"]) == 0:
        runstate["decision_request_pending"] = None
    
    # Set phase for continuation based on action
    if action:
        continuation_phase = action.get("continuation_phase", "planning")
        runstate["current_phase"] = continuation_phase
        runstate["next_recommended_action"] = action.get("next_recommended", "")
    else:
        # Default continuation based on reply type
        if reply_command in ["DECISION", "APPROVE", "CONTINUE"]:
            runstate["current_phase"] = "planning"
        elif reply_command == "DEFER":
            runstate["current_phase"] = "planning"
        elif reply_command == "RETRY":
            runstate["current_phase"] = "executing"
    
    # Update last_action
    runstate["last_action"] = f"Decision resolved: {request_id} → {reply_value}"
    
    return runstate


def reconcile_decision_sources(
    project_path: Path,
) -> dict[str, Any]:
    """Reconcile DecisionRequestStore and RunState.
    
    Loads pending requests from DecisionRequestStore and RunState.decisions_needed,
    identifies discrepancies, and returns unified state.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Unified decision state dict with:
        - pending_email_decisions: list of pending email requests
        - resolved_email_decisions: list of resolved email requests
        - runstate_decisions: list of decisions in RunState
        - discrepancies: list of detected discrepancies
        - pending_count: total pending count
        - resolved_count: resolved count
    """
    store = DecisionRequestStore(project_path)
    
    # Load pending requests from DecisionRequestStore
    pending_requests = store.list_requests(status=DecisionRequestStatus.SENT)
    
    # Load resolved requests
    resolved_requests = store.list_requests(status=DecisionRequestStatus.RESOLVED)
    
    # Load RunState if available
    from runtime.state_store import StateStore
    state_store = StateStore(project_path)
    runstate = state_store.load_runstate()
    
    runstate_decisions = []
    if runstate:
        runstate_decisions = runstate.get("decisions_needed", [])
    
    # Identify discrepancies
    discrepancies = []
    
    # Check for email requests not in RunState
    email_request_ids = {r.get("decision_request_id") for r in pending_requests}
    runstate_request_ids = {
        d.get("request_id", d.get("decision_id", ""))
        for d in runstate_decisions
    }
    
    # Requests in email but not in RunState (need sync)
    missing_in_runstate = email_request_ids - runstate_request_ids
    for req_id in missing_in_runstate:
        discrepancies.append({
            "type": "email_request_not_in_runstate",
            "request_id": req_id,
            "message": f"Email request {req_id} not in RunState.decisions_needed",
        })
    
    # Requests in RunState but not in email store (orphaned)
    missing_in_email = runstate_request_ids - email_request_ids
    for req_id in missing_in_email:
        if req_id.startswith("dr-"):  # Only check email-format IDs
            discrepancies.append({
                "type": "orphaned_runstate_entry",
                "request_id": req_id,
                "message": f"RunState has entry for {req_id} but no matching email request",
            })
    
    # Build unified state
    unified_state = {
        "pending_email_decisions": pending_requests,
        "resolved_email_decisions": resolved_requests,
        "runstate_decisions": runstate_decisions,
        "discrepancies": discrepancies,
        "pending_count": len(pending_requests),
        "resolved_count": len(resolved_requests),
        "email_decision_resolved": len(resolved_requests) > 0,
        "has_discrepancies": len(discrepancies) > 0,
    }
    
    # Add latest resolved request if available
    if resolved_requests:
        latest = resolved_requests[-1]  # Most recent
        unified_state["resolved_request_id"] = latest.get("decision_request_id")
        unified_state["resolved_reply"] = {
            "reply_value": latest.get("resolution", ""),
            "parsed_result": {
                "command": latest.get("resolution", "").split()[0] if latest.get("resolution") else "",
                "argument": latest.get("resolution", "").split()[1] if len(latest.get("resolution", "").split()) > 1 else None,
            },
            "received_at": latest.get("resolved_at", ""),
        }
    
    return unified_state


def get_pending_decision_count(project_path: Path) -> int:
    """Get count of pending decisions from both sources.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Total count of pending decisions
    """
    unified = reconcile_decision_sources(project_path)
    return unified.get("pending_count", 0)


def get_decision_status_summary(project_path: Path) -> dict[str, Any]:
    """Get summary of decision status for display.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Summary dict for CLI display
    """
    unified = reconcile_decision_sources(project_path)
    
    summary = {
        "total_pending": unified["pending_count"],
        "total_resolved": unified["resolved_count"],
        "has_discrepancies": unified["has_discrepancies"],
        "pending_from_email": len(unified["pending_email_decisions"]),
        "pending_from_runstate": len(unified["runstate_decisions"]),
    }
    
    if unified["has_discrepancies"]:
        summary["discrepancy_details"] = unified["discrepancies"]
    
    if unified.get("resolved_request_id"):
        summary["latest_resolution"] = unified["resolved_request_id"]
    
    return summary


def apply_email_resolution_to_runstate(
    project_path: Path,
) -> dict[str, Any] | None:
    """Apply latest email resolution to RunState if not already applied.
    
    This is called by resume_next_day to sync resolved email decisions.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Updated RunState if resolution was applied, None otherwise
    """
    from runtime.state_store import StateStore
    from runtime.reply_action_mapper import map_reply_to_action, ParsedReply, ReplyCommand
    
    unified = reconcile_decision_sources(project_path)
    
    if not unified.get("email_decision_resolved"):
        return None
    
    # Check if resolution already applied
    state_store = StateStore(project_path)
    runstate = state_store.load_runstate()
    
    if not runstate:
        return None
    
    last_resolution = runstate.get("last_decision_resolution", {})
    resolved_id = unified.get("resolved_request_id")
    
    if last_resolution.get("request_id") == resolved_id:
        # Already applied
        return None
    
    # Get the request and reply details
    store = DecisionRequestStore(project_path)
    request = store.load_request(resolved_id)
    
    if not request:
        return None
    
    # Build ParsedReply from resolution
    reply_value = request.get("resolution", "")
    parts = reply_value.split()
    command_str = parts[0] if parts else ""
    argument = parts[1] if len(parts) > 1 else None
    
    try:
        command = ReplyCommand(command_str.upper())
    except ValueError:
        command = None
    
    parsed_reply = ParsedReply(
        command=command,
        argument=argument,
        is_valid=True,
        raw_text=reply_value,
    )
    
    # Map reply to action
    action = map_reply_to_action(parsed_reply, request)
    
    # Build reply record
    reply_record = {
        "reply_value": reply_value,
        "parsed_result": {
            "command": command_str,
            "argument": argument,
            "is_valid": True,
        },
        "received_at": request.get("resolved_at", datetime.now().isoformat()),
    }
    
    # Sync to RunState
    runstate = sync_reply_to_runstate(resolved_id, reply_record, runstate, action)
    
    # Save updated RunState
    state_store.save_runstate(runstate)
    
    return runstate