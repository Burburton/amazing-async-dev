"""Reply action mapper for Feature 043.

Maps reply commands to RunState continuation actions.
"""

from typing import Any

from runtime.reply_parser import ParsedReply, ReplyCommand


REPLY_ACTION_MAP: dict[ReplyCommand, dict[str, str]] = {
    ReplyCommand.DECISION: {
        "runstate_action": "select_option",
        "continuation_phase": "planning",
        "next_recommended": "Proceed with selected option",
        "instruction": "Continue execution with chosen path",
    },
    ReplyCommand.APPROVE: {
        "runstate_action": "approve_risky_action",
        "continuation_phase": "executing",
        "next_recommended": "Execute approved action",
        "instruction": "Proceed with risky action after approval",
    },
    ReplyCommand.DEFER: {
        "runstate_action": "defer_decision",
        "continuation_phase": "planning",
        "next_recommended": "Find alternative approach",
        "instruction": "Work on alternative path while decision deferred",
    },
    ReplyCommand.RETRY: {
        "runstate_action": "mark_retry_needed",
        "continuation_phase": "executing",
        "next_recommended": "Retry current step",
        "instruction": "Retry the failed or blocked step",
    },
    ReplyCommand.CONTINUE: {
        "runstate_action": "clear_blocker",
        "continuation_phase": "executing",
        "next_recommended": "Continue execution",
        "instruction": "Proceed without changes",
    },
}


def map_reply_to_action(
    parsed: ParsedReply,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Map parsed reply to RunState action.
    
    Args:
        parsed: Parsed reply from reply_parser
        request: Decision request being replied to
        
    Returns:
        Action dict with:
        - runstate_action: action to apply
        - continuation_phase: phase to set
        - next_recommended: next recommended action
        - instruction: execution instruction
        - selected_option_label: label if DECISION with option
    """
    if not parsed.command:
        return {
            "runstate_action": "unknown",
            "continuation_phase": "planning",
            "next_recommended": "Review reply and determine action manually",
            "instruction": "Manual intervention needed",
        }
    
    base_action = REPLY_ACTION_MAP.get(parsed.command, {})
    
    action = {
        "runstate_action": base_action.get("runstate_action", ""),
        "continuation_phase": base_action.get("continuation_phase", "planning"),
        "next_recommended": base_action.get("next_recommended", ""),
        "instruction": base_action.get("instruction", ""),
        "reply_command": parsed.command.value,
        "reply_argument": parsed.argument,
    }
    
    if parsed.command == ReplyCommand.DECISION and parsed.argument:
        options = request.get("options", [])
        selected_label = ""
        for opt in options:
            if opt.get("id") == parsed.argument:
                selected_label = opt.get("label", "")
                break
        
        action["selected_option_id"] = parsed.argument
        action["selected_option_label"] = selected_label
        action["next_recommended"] = f"Proceed with option {parsed.argument}: {selected_label}"
        action["instruction"] = f"Execute path corresponding to option {parsed.argument}"
    
    if parsed.command == ReplyCommand.APPROVE and parsed.argument:
        action["approved_action_type"] = parsed.argument
        action["next_recommended"] = f"Execute approved {parsed.argument}"
    
    return action


def get_continuation_phase_for_reply(reply_command: ReplyCommand) -> str:
    """Get continuation phase for a reply command.
    
    Args:
        reply_command: Reply command enum
        
    Returns:
        Phase to set for continuation
    """
    action = REPLY_ACTION_MAP.get(reply_command, {})
    return action.get("continuation_phase", "planning")


def get_next_recommended_for_reply(
    reply_command: ReplyCommand,
    argument: str | None = None,
) -> str:
    """Get next recommended action for a reply command.
    
    Args:
        reply_command: Reply command enum
        argument: Optional argument (for DECISION/APPROVE)
        
    Returns:
        Next recommended action string
    """
    action = REPLY_ACTION_MAP.get(reply_command, {})
    base_recommended = action.get("next_recommended", "")
    
    if reply_command == ReplyCommand.DECISION and argument:
        return f"Proceed with option {argument}"
    
    if reply_command == ReplyCommand.APPROVE and argument:
        return f"Execute approved {argument}"
    
    return base_recommended