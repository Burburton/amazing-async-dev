"""Auto email trigger for Feature 054 - Automatic decision email sending."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.execution_policy import PolicyMode, get_policy_mode
from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
    DecisionType,
    DeliveryChannel,
)
from runtime.email_sender import create_email_config, EmailSender
from runtime.decision_sync import sync_decision_to_runstate
from runtime.state_store import StateStore


class TriggerSource(str, Enum):
    """Source of the auto-trigger."""
    RUN_DAY_AUTO = "run_day_auto"
    PLAN_DAY_AUTO = "plan_day_auto"
    EXTERNAL_TOOL_AUTO = "external_tool_auto"
    MANUAL_CLI = "manual_cli"


@dataclass
class TriggerResult:
    """Result of an auto-trigger attempt."""
    triggered: bool
    request_id: str | None = None
    trigger_source: TriggerSource = TriggerSource.RUN_DAY_AUTO
    policy_mode_at_trigger: PolicyMode = PolicyMode.BALANCED
    skipped_reason: str | None = None
    error_message: str | None = None
    triggered_at: str = field(default_factory=lambda: datetime.now().isoformat())


PAUSE_CATEGORIES_AUTO_SEND = {
    "decision_required",
    "blocker",
    "scope_change",
    "architecture",
    "external_dependency",
}

PAUSE_CATEGORIES_SKIP_IN_BALANCED = {
    "technical",
    "minor",
}


def should_auto_trigger(
    runstate: dict[str, Any],
    pause_category: str | None = None,
) -> tuple[bool, str | None]:
    """Determine if auto-trigger should happen based on policy mode.
    
    Args:
        runstate: Current RunState
        pause_category: Category of the pause reason
        
    Returns:
        Tuple of (should_trigger, skip_reason)
    """
    policy_mode = get_policy_mode(runstate)
    
    pending_request_id = runstate.get("decision_request_pending")
    if pending_request_id:
        return False, "Decision request already pending: " + pending_request_id
    
    decisions_needed = runstate.get("decisions_needed", [])
    if not decisions_needed:
        return False, "No decisions_needed in RunState"
    
    if policy_mode == PolicyMode.CONSERVATIVE:
        return True, None
    
    if policy_mode == PolicyMode.LOW_INTERRUPTION:
        return True, None
    
    if policy_mode == PolicyMode.BALANCED:
        if pause_category and pause_category in PAUSE_CATEGORIES_SKIP_IN_BALANCED:
            return False, f"Balanced mode skips '{pause_category}' category"
        return True, None
    
    return True, None


def create_auto_decision_request(
    project_path: Path,
    decision_entry: dict[str, Any],
    trigger_source: TriggerSource = TriggerSource.RUN_DAY_AUTO,
    policy_mode: PolicyMode = PolicyMode.BALANCED,
) -> dict[str, Any] | None:
    """Create a decision request from a decisions_needed entry.
    
    Args:
        project_path: Project path
        decision_entry: Entry from RunState.decisions_needed
        trigger_source: Source of trigger
        policy_mode: Policy mode at trigger time
        
    Returns:
        Created decision request dict or None on failure
    """
    import os
    
    store = DecisionRequestStore(project_path)
    
    product_id = decision_entry.get("product_id", project_path.name)
    feature_id = decision_entry.get("feature_id", decision_entry.get("decision_id", "unknown"))
    question = decision_entry.get("decision", "Decision required")
    options_raw = decision_entry.get("options", [])
    
    parsed_options = []
    for i, opt in enumerate(options_raw):
        if isinstance(opt, str):
            parsed_options.append({
                "id": chr(65 + i),
                "label": opt,
                "description": ""
            })
        elif isinstance(opt, dict):
            parsed_options.append(opt)
    
    recommendation = decision_entry.get("recommendation", "")
    if recommendation and len(parsed_options) > 0:
        recommendation_id = recommendation[0] if isinstance(recommendation, str) else "A"
    else:
        recommendation_id = "A" if parsed_options else ""
    
    delivery_mode = os.getenv("ASYNCDEV_DELIVERY_MODE", "mock_file")
    if delivery_mode == "resend":
        delivery_channel = DeliveryChannel.RESEND
    elif delivery_mode == "console":
        delivery_channel = DeliveryChannel.CONSOLE
    else:
        delivery_channel = DeliveryChannel.MOCK_FILE
    
    pause_category = decision_entry.get("pause_reason_category", "decision_required")
    try:
        dt = DecisionType(decision_entry.get("decision_type", "technical"))
    except ValueError:
        dt = DecisionType.TECHNICAL
    
    request = store.create_request(
        product_id=product_id,
        feature_id=feature_id,
        pause_reason_category=pause_category,
        decision_type=dt,
        question=question,
        options=parsed_options,
        recommendation=recommendation_id,
        delivery_channel=delivery_channel,
    )
    
    request["trigger_source"] = trigger_source.value
    request["policy_mode_at_trigger"] = policy_mode.value
    request["auto_triggered"] = True
    
    store.save_request(request)
    
    return request


def send_auto_decision_email(
    project_path: Path,
    request: dict[str, Any],
) -> tuple[bool, str | None]:
    """Send email for auto-created decision request.
    
    Args:
        project_path: Project path
        request: Decision request dict
        
    Returns:
        Tuple of (success, message_id_or_error)
    """
    from runtime.resend_provider import apply_resend_config_from_file
    
    apply_resend_config_from_file()
    config = create_email_config(project_path)
    sender = EmailSender(config)
    
    success, message_id = sender.send_decision_request(request)
    
    if success:
        store = DecisionRequestStore(project_path)
        store.mark_sent(request["decision_request_id"], mock_path=message_id)
        return True, message_id
    
    return False, "Failed to send email"


def auto_trigger_decision_email(
    project_path: Path,
    runstate: dict[str, Any],
    trigger_source: TriggerSource = TriggerSource.RUN_DAY_AUTO,
) -> TriggerResult:
    """Auto-trigger decision email based on RunState.
    
    Args:
        project_path: Project path
        runstate: Current RunState
        trigger_source: Source of trigger
        
    Returns:
        TriggerResult with outcome
    """
    policy_mode = get_policy_mode(runstate)
    
    decisions_needed = runstate.get("decisions_needed", [])
    if not decisions_needed:
        return TriggerResult(
            triggered=False,
            trigger_source=trigger_source,
            policy_mode_at_trigger=policy_mode,
            skipped_reason="No decisions_needed in RunState",
        )
    
    pending_request_id = runstate.get("decision_request_pending")
    if pending_request_id:
        return TriggerResult(
            triggered=False,
            trigger_source=trigger_source,
            policy_mode_at_trigger=policy_mode,
            skipped_reason="Decision request already pending: " + pending_request_id,
        )
    
    first_decision = decisions_needed[0]
    pause_category = first_decision.get("pause_reason_category", "decision_required")
    
    should_trigger, skip_reason = should_auto_trigger(runstate, pause_category)
    
    if not should_trigger:
        return TriggerResult(
            triggered=False,
            trigger_source=trigger_source,
            policy_mode_at_trigger=policy_mode,
            skipped_reason=skip_reason,
        )
    
    request = create_auto_decision_request(
        project_path,
        first_decision,
        trigger_source=trigger_source,
        policy_mode=policy_mode,
    )
    
    if not request:
        return TriggerResult(
            triggered=False,
            trigger_source=trigger_source,
            policy_mode_at_trigger=policy_mode,
            error_message="Failed to create decision request",
        )
    
    success, message_id = send_auto_decision_email(project_path, request)
    
    if not success:
        return TriggerResult(
            triggered=False,
            request_id=request["decision_request_id"],
            trigger_source=trigger_source,
            policy_mode_at_trigger=policy_mode,
            error_message=message_id or "Failed to send email",
        )
    
    state_store = StateStore(project_path)
    runstate = sync_decision_to_runstate(request, runstate)
    state_store.save_runstate(runstate)
    
    return TriggerResult(
        triggered=True,
        request_id=request["decision_request_id"],
        trigger_source=trigger_source,
        policy_mode_at_trigger=policy_mode,
    )


def check_and_trigger(
    project_path: Path,
    trigger_source: TriggerSource = TriggerSource.RUN_DAY_AUTO,
) -> TriggerResult:
    """Check RunState and trigger if needed.
    
    Convenience function that loads RunState and triggers.
    
    Args:
        project_path: Project path
        trigger_source: Source of trigger
        
    Returns:
        TriggerResult with outcome
    """
    state_store = StateStore(project_path)
    runstate = state_store.load_runstate()
    
    if not runstate:
        return TriggerResult(
            triggered=False,
            trigger_source=trigger_source,
            skipped_reason="No RunState found",
        )
    
    return auto_trigger_decision_email(project_path, runstate, trigger_source)