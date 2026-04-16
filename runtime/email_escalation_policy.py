"""Email escalation policy for governing when to send emails (Feature 048).

Ensures email channel is used only at the right moments with proper escalation discipline.
Integrates with existing execution_policy system.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class EmailTriggerType(str, Enum):
    """Types of triggers that warrant email."""
    
    ESCALATION_BLOCKER = "escalation_blocker"
    ESCALATION_DECISION_REQUIRED = "escalation_decision_required"
    HUMAN_CHECKPOINT = "human_checkpoint"
    RISKY_ACTION_APPROVAL = "risky_action_approvalval"
    MILESTONE_REPORT = "milestone_report"
    BLOCKER_REPORT = "blocker_report"
    PROGRESS_DIGEST = "progress_digest"
    TIMEOUT_WARNING = "timeout_warning"
    INFORMATION_ONLY = "information_only"


class EmailSuppressReason(str, Enum):
    """Reasons to suppress email sending."""
    
    RATE_LIMITED = "rate_limited"
    SIMILAR_PENDING = "similar_pending"
    INFORMATION_ONLY = "information_only"
    LOW_INTERRUPTION_SKIP = "low_interruption_skip"
    AUTO_RESOLVABLE = "auto_resolvable"
    DUPLICATE_CONTENT = "duplicate_content"
    QUIET_MODE = "quiet_mode"


class EmailUrgency(str, Enum):
    """Email urgency levels."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


DEFAULT_RATE_LIMIT_HOURS = 4
DEFAULT_DIGEST_INTERVAL_HOURS = 24
DEFAULT_TIMEOUT_WARNING_HOURS = 48


TRIGGER_TO_URGENCY = {
    EmailTriggerType.ESCALATION_BLOCKER: EmailUrgency.HIGH,
    EmailTriggerType.ESCALATION_DECISION_REQUIRED: EmailUrgency.HIGH,
    EmailTriggerType.RISKY_ACTION_APPROVAL: EmailUrgency.HIGH,
    EmailTriggerType.HUMAN_CHECKPOINT: EmailUrgency.MEDIUM,
    EmailTriggerType.BLOCKER_REPORT: EmailUrgency.MEDIUM,
    EmailTriggerType.MILESTONE_REPORT: EmailUrgency.LOW,
    EmailTriggerType.PROGRESS_DIGEST: EmailUrgency.LOW,
    EmailTriggerType.TIMEOUT_WARNING: EmailUrgency.MEDIUM,
    EmailTriggerType.INFORMATION_ONLY: EmailUrgency.INFORMATIONAL,
}


def should_send_email(
    runstate: dict[str, Any],
    trigger_type: EmailTriggerType,
    last_email_sent_at: datetime | None = None,
    pending_requests: list[dict[str, Any]] | None = None,
    policy_mode: str | None = None,
) -> tuple[bool, EmailSuppressReason | None, str]:
    """Check if email should be sent based on escalation policy.
    
    Args:
        runstate: Current RunState
        trigger_type: Type of trigger
        last_email_sent_at: When last email was sent
        pending_requests: Currently pending decision requests
        policy_mode: Policy mode (conservative/balanced/low_interruption)
        
    Returns:
        (should_send, suppress_reason_if_not, explanation)
    """
    policy_mode = policy_mode or runstate.get("policy_mode", "balanced")
    
    if last_email_sent_at:
        hours_since = (datetime.now() - last_email_sent_at).total_seconds() / 3600
        rate_limit = get_rate_limit_hours(policy_mode, trigger_type)
        
        if hours_since < rate_limit:
            return (
                False,
                EmailSuppressReason.RATE_LIMITED,
                f"Last email sent {hours_since:.1f} hours ago, rate limit is {rate_limit} hours",
            )
    
    if pending_requests:
        for req in pending_requests:
            if req.get("status") == "sent":
                req_type = req.get("pause_reason_category", "")
                trigger_category = trigger_type.value.split("_")[0]
                
                if trigger_category in req_type and trigger_type != EmailTriggerType.MILESTONE_REPORT:
                    return (
                        False,
                        EmailSuppressReason.SIMILAR_PENDING,
                        f"Similar request already pending: {req.get('decision_request_id')}",
                    )
    
    if trigger_type == EmailTriggerType.PROGRESS_DIGEST:
        if policy_mode == "conservative":
            return (
                True,
                None,
                "Conservative mode: all digests sent",
            )
        elif policy_mode == "low_interruption":
            digest_interval = runstate.get("digest_interval_hours", DEFAULT_DIGEST_INTERVAL_HOURS)
            if last_email_sent_at:
                hours_since = (datetime.now() - last_email_sent_at).total_seconds() / 3600
                if hours_since < digest_interval:
                    return (
                        False,
                        EmailSuppressReason.LOW_INTERRUPTION_SKIP,
                        f"Low interruption mode: digest interval {digest_interval} hours",
                    )
    
    if trigger_type == EmailTriggerType.INFORMATION_ONLY:
        if policy_mode == "low_interruption":
            return (
                False,
                EmailSuppressReason.INFORMATION_ONLY,
                "Low interruption mode: skipping informational emails",
            )
    
    urgency = TRIGGER_TO_URGENCY.get(trigger_type, EmailUrgency.LOW)
    
    if urgency == EmailUrgency.HIGH:
        return (True, None, f"High urgency trigger: {trigger_type.value}")
    
    if policy_mode == "conservative":
        return (True, None, f"Conservative mode: sending for {trigger_type.value}")
    elif policy_mode == "balanced":
        if urgency in [EmailUrgency.HIGH, EmailUrgency.MEDIUM]:
            return (True, None, f"Balanced mode: sending for {urgency.value} urgency")
        else:
            return (
                False,
                EmailSuppressReason.LOW_INTERRUPTION_SKIP,
                f"Balanced mode: skipping low urgency {trigger_type.value}",
            )
    else:
        if urgency == EmailUrgency.HIGH:
            return (True, None, f"Low interruption mode: only high urgency sent")
        return (
            False,
            EmailSuppressReason.LOW_INTERRUPTION_SKIP,
            f"Low interruption mode: skipping {trigger_type.value}",
        )


def get_rate_limit_hours(policy_mode: str, trigger_type: EmailTriggerType) -> float:
    """Get rate limit hours based on policy mode and trigger type.
    
    Args:
        policy_mode: Policy mode
        trigger_type: Trigger type
        
    Returns:
        Minimum hours between similar emails
    """
    urgency = TRIGGER_TO_URGENCY.get(trigger_type, EmailUrgency.LOW)
    
    if urgency == EmailUrgency.HIGH:
        return 1.0
    
    if policy_mode == "conservative":
        return 2.0
    elif policy_mode == "balanced":
        return DEFAULT_RATE_LIMIT_HOURS
    else:
        if urgency == EmailUrgency.MEDIUM:
            return DEFAULT_RATE_LIMIT_HOURS
        return DEFAULT_DIGEST_INTERVAL_HOURS


def classify_email_type(
    trigger_type: EmailTriggerType,
    reply_required: bool = False,
) -> tuple[str, str]:
    """Classify email as decision request vs status report.
    
    Args:
        trigger_type: Trigger type
        reply_required: Whether reply is required
        
    Returns:
        (email_type, description)
    """
    if trigger_type in [
        EmailTriggerType.ESCALATION_BLOCKER,
        EmailTriggerType.ESCALATION_DECISION_REQUIRED,
        EmailTriggerType.RISKY_ACTION_APPROVAL,
        EmailTriggerType.HUMAN_CHECKPOINT,
    ]:
        return ("decision_request", "Requires human decision/approval")
    
    if reply_required:
        return ("decision_request", "Explicit reply requested")
    
    return ("status_report", "Informational only, no reply required")


def get_email_urgency(trigger_type: EmailTriggerType) -> EmailUrgency:
    """Get urgency level for trigger type."""
    return TRIGGER_TO_URGENCY.get(trigger_type, EmailUrgency.LOW)


def check_timeout_condition(
    request_sent_at: datetime,
    timeout_hours: float = DEFAULT_TIMEOUT_WARNING_HOURS,
) -> tuple[bool, float, str]:
    """Check if timeout warning should be sent.
    
    Args:
        request_sent_at: When the request was sent
        timeout_hours: Timeout threshold
        
    Returns:
        (needs_warning, hours_elapsed, explanation)
    """
    hours_elapsed = (datetime.now() - request_sent_at).total_seconds() / 3600
    
    if hours_elapsed >= timeout_hours:
        return (
            True,
            hours_elapsed,
            f"Request pending for {hours_elapsed:.1f} hours, exceeds {timeout_hours} threshold",
        )
    
    return (False, hours_elapsed, f"Request pending for {hours_elapsed:.1f} hours, within threshold")


def get_appropriate_triggers_for_runstate(
    runstate: dict[str, Any],
    policy_mode: str | None = None,
) -> list[EmailTriggerType]:
    """Get appropriate email triggers for current RunState.
    
    Args:
        runstate: Current RunState
        policy_mode: Policy mode
        
    Returns:
        List of appropriate trigger types
    """
    triggers = []
    policy_mode = policy_mode or runstate.get("policy_mode", "balanced")
    
    blocked_items = runstate.get("blocked_items", [])
    if blocked_items:
        triggers.append(EmailTriggerType.ESCALATION_BLOCKER)
    
    decisions_needed = runstate.get("decisions_needed", [])
    if decisions_needed:
        decision = decisions_needed[0]
        category = decision.get("category", "")
        
        if category in ["critical", "approval", "architecture"]:
            triggers.append(EmailTriggerType.ESCALATION_DECISION_REQUIRED)
        elif category in ["checkpoint", "review"]:
            triggers.append(EmailTriggerType.HUMAN_CHECKPOINT)
    
    pending_risky = runstate.get("pending_risky_actions", [])
    for action in pending_risky:
        if action.get("requires_confirmation"):
            triggers.append(EmailTriggerType.RISKY_ACTION_APPROVAL)
    
    current_phase = runstate.get("current_phase", "")
    if current_phase == "milestone":
        triggers.append(EmailTriggerType.MILESTONE_REPORT)
    
    return triggers


def format_escalation_summary(
    trigger_type: EmailTriggerType,
    should_send: bool,
    suppress_reason: EmailSuppressReason | None,
    explanation: str,
) -> str:
    """Format escalation decision as human-readable summary.
    
    Args:
        trigger_type: Trigger type
        should_send: Whether email should be sent
        suppress_reason: Reason if suppressed
        explanation: Explanation
        
    Returns:
        Human-readable summary
    """
    lines = []
    
    lines.append(f"## Email Escalation: {trigger_type.value}")
    lines.append("")
    lines.append(f"**Decision:** {should_send}")
    
    if suppress_reason:
        lines.append(f"**Suppressed:** {suppress_reason.value}")
    
    lines.append(f"**Urgency:** {TRIGGER_TO_URGENCY.get(trigger_type, EmailUrgency.LOW).value}")
    lines.append("")
    lines.append(f"**Explanation:** {explanation}")
    
    return "\n".join(lines)


def validate_email_frequency(
    emails_today: int,
    max_emails_per_day: int = 10,
    policy_mode: str = "balanced",
) -> tuple[bool, str]:
    """Validate if email frequency is within acceptable bounds.
    
    Args:
        emails_today: Number of emails sent today
        max_emails_per_day: Maximum allowed per day
        policy_mode: Policy mode
        
    Returns:
        (within_bounds, explanation)
    """
    if policy_mode == "conservative":
        max_emails_per_day = 15
    elif policy_mode == "low_interruption":
        max_emails_per_day = 5
    
    if emails_today >= max_emails_per_day:
        return (
            False,
            f"Daily limit reached: {emails_today}/{max_emails_per_day} emails",
        )
    
    return (True, f"Within daily limit: {emails_today}/{max_emails_per_day}")