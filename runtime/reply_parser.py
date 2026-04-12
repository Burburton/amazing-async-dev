"""Reply parser for decision email replies (Feature 021).

Strict grammar parser for command-style replies.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ReplyCommand(str, Enum):
    """Supported reply commands."""
    
    DECISION = "DECISION"
    APPROVE = "APPROVE"
    DEFER = "DEFER"
    RETRY = "RETRY"
    CONTINUE = "CONTINUE"


class ValidationStatus(str, Enum):
    """Result of reply validation."""
    
    VALID = "valid"
    INVALID_SYNTAX = "invalid_syntax"
    INVALID_OPTION = "invalid_option"
    INVALID_REQUEST_ID = "invalid_request_id"
    DUPLICATE_REPLY = "duplicate_reply"
    EXPIRED_REQUEST = "expired_request"


@dataclass
class ParsedReply:
    """Parsed reply result."""
    
    command: ReplyCommand | None
    argument: str | None
    is_valid: bool
    raw_text: str


REPLY_GRAMMAR = {
    ReplyCommand.DECISION: re.compile(r"^DECISION\s+([A-Z])$", re.IGNORECASE),
    ReplyCommand.APPROVE: re.compile(r"^APPROVE\s+(\w+)$", re.IGNORECASE),
    ReplyCommand.DEFER: re.compile(r"^DEFER$", re.IGNORECASE),
    ReplyCommand.RETRY: re.compile(r"^RETRY$", re.IGNORECASE),
    ReplyCommand.CONTINUE: re.compile(r"^CONTINUE$", re.IGNORECASE),
}


def parse_reply(reply_text: str) -> ParsedReply:
    """Parse reply text into structured result.
    
    Args:
        reply_text: Raw reply text
        
    Returns:
        ParsedReply with command, argument, validity
    """
    normalized = reply_text.strip().upper()
    
    for command, pattern in REPLY_GRAMMAR.items():
        match = pattern.match(normalized)
        if match:
            argument = match.group(1) if match.groups() else None
            return ParsedReply(
                command=command,
                argument=argument,
                is_valid=True,
                raw_text=reply_text,
            )
    
    return ParsedReply(
        command=None,
        argument=None,
        is_valid=False,
        raw_text=reply_text,
    )


def validate_reply(
    parsed: ParsedReply,
    request: dict[str, Any],
) -> tuple[bool, ValidationStatus, str | None]:
    """Validate parsed reply against decision request.
    
    Args:
        parsed: Parsed reply
        request: Decision request to validate against
        
    Returns:
        (is_valid, validation_status, error_message)
    """
    if not parsed.is_valid:
        return False, ValidationStatus.INVALID_SYNTAX, f"Invalid syntax: {parsed.raw_text}"
    
    request_id = request.get("decision_request_id", "")
    status = request.get("status", "")
    
    if status == "resolved":
        return False, ValidationStatus.DUPLICATE_REPLY, f"Request {request_id} already resolved"
    
    if status == "expired":
        return False, ValidationStatus.EXPIRED_REQUEST, f"Request {request_id} is expired"
    
    if parsed.command == ReplyCommand.DECISION:
        valid_options = [opt.get("id", "") for opt in request.get("options", [])]
        if parsed.argument not in valid_options:
            return False, ValidationStatus.INVALID_OPTION, f"Invalid option '{parsed.argument}', valid: {valid_options}"
    
    if parsed.command == ReplyCommand.APPROVE:
        pending_risky = request.get("pending_risky_actions", [])
        risky_types = [a.get("action_type", "") for a in pending_risky]
        if parsed.argument not in risky_types:
            return False, ValidationStatus.INVALID_OPTION, f"Invalid action type '{parsed.argument}'"
    
    return True, ValidationStatus.VALID, None


def create_reply_record(
    request_id: str,
    parsed: ParsedReply,
    validation_status: ValidationStatus,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Create a reply record for storage.
    
    Args:
        request_id: Decision request ID
        parsed: Parsed reply
        validation_status: Validation result
        error_message: Error if invalid
        
    Returns:
        Reply record dict
    """
    reply_value = ""
    if parsed.command:
        reply_value = parsed.command.value
        if parsed.argument:
            reply_value += f" {parsed.argument}"
    
    return {
        "decision_request_id": request_id,
        "reply_value": reply_value,
        "reply_raw_text": parsed.raw_text,
        "received_at": datetime.now().isoformat(),
        "parsed_result": {
            "command": parsed.command.value if parsed.command else None,
            "argument": parsed.argument,
            "is_valid": parsed.is_valid,
        },
        "validation_status": validation_status.value,
        "error_message": error_message,
    }


def get_reply_action(parsed: ParsedReply, request: dict[str, Any]) -> str:
    """Determine action to take based on valid reply.
    
    Args:
        parsed: Valid parsed reply
        request: Decision request
        
    Returns:
        Action description
    """
    if parsed.command == ReplyCommand.DECISION:
        option_id = parsed.argument
        options = request.get("options", [])
        for opt in options:
            if opt.get("id") == option_id:
                return f"Selected option: {opt.get('label', option_id)}"
        return f"Selected option: {option_id}"
    
    elif parsed.command == ReplyCommand.APPROVE:
        return f"Approved action: {parsed.argument}"
    
    elif parsed.command == ReplyCommand.DEFER:
        return "Decision deferred, proceed with alternative"
    
    elif parsed.command == ReplyCommand.RETRY:
        return "Retry requested"
    
    elif parsed.command == ReplyCommand.CONTINUE:
        return "Continue without change"
    
    return "Unknown action"


def extract_request_id_from_email(reply_text: str) -> str | None:
    """Extract request ID from email reply if present.
    
    Looks for patterns like:
    - In-Reply-To: dr-20260412-001
    - Subject: Re: [async-dev] Decision needed... dr-20260412-001
    """
    patterns = [
        r"dr-[0-9]{8}-[0-9]{3}",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, reply_text)
        if match:
            return match.group(0)
    
    return None


def find_command_in_reply(reply_text: str) -> str | None:
    """Find command line in multi-line reply.
    
    Looks for lines starting with DECISION, APPROVE, DEFER, RETRY, CONTINUE.
    """
    lines = reply_text.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        for command in ReplyCommand:
            if line.upper().startswith(command.value):
                return line
    
    return None