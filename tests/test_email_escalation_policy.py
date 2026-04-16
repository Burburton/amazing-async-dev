"""Tests for email_escalation_policy module (Feature 048)."""

from datetime import datetime, timedelta

import pytest

from runtime.email_escalation_policy import (
    EmailTriggerType,
    EmailSuppressReason,
    EmailUrgency,
    should_send_email,
    get_rate_limit_hours,
    classify_email_type,
    get_email_urgency,
    check_timeout_condition,
    get_appropriate_triggers_for_runstate,
    format_escalation_summary,
    validate_email_frequency,
    DEFAULT_RATE_LIMIT_HOURS,
    DEFAULT_DIGEST_INTERVAL_HOURS,
    DEFAULT_TIMEOUT_WARNING_HOURS,
    TRIGGER_TO_URGENCY,
)


class TestEmailTriggerType:
    def test_all_trigger_types_defined(self):
        assert EmailTriggerType.ESCALATION_BLOCKER.value == "escalation_blocker"
        assert EmailTriggerType.ESCALATION_DECISION_REQUIRED.value == "escalation_decision_required"
        assert EmailTriggerType.RISKY_ACTION_APPROVAL.value == "risky_action_approvalval"
        assert EmailTriggerType.MILESTONE_REPORT.value == "milestone_report"

    def test_trigger_count(self):
        assert len(EmailTriggerType) >= 8


class TestEmailSuppressReason:
    def test_all_suppress_reasons_defined(self):
        assert EmailSuppressReason.RATE_LIMITED.value == "rate_limited"
        assert EmailSuppressReason.SIMILAR_PENDING.value == "similar_pending"
        assert EmailSuppressReason.INFORMATION_ONLY.value == "information_only"

    def test_suppress_reason_count(self):
        assert len(EmailSuppressReason) >= 7


class TestEmailUrgency:
    def test_urgency_levels_defined(self):
        assert EmailUrgency.HIGH.value == "high"
        assert EmailUrgency.MEDIUM.value == "medium"
        assert EmailUrgency.LOW.value == "low"
        assert EmailUrgency.INFORMATIONAL.value == "informational"


class TestShouldSendEmail:
    def test_high_urgency_always_sent(self):
        runstate = {"policy_mode": "low_interruption"}
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.ESCALATION_BLOCKER,
        )
        assert should == True
        assert reason is None
        assert "High urgency" in explanation

    def test_rate_limit_suppresses(self):
        runstate = {"policy_mode": "balanced"}
        last_sent = datetime.now() - timedelta(hours=2)
        
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.MILESTONE_REPORT,
            last_email_sent_at=last_sent,
        )
        assert should == False
        assert reason == EmailSuppressReason.RATE_LIMITED
        assert "rate limit" in explanation.lower()

    def test_similar_pending_suppresses(self):
        runstate = {"policy_mode": "balanced"}
        pending = [{"status": "sent", "pause_reason_category": "escalation"}]
        
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.ESCALATION_BLOCKER,
            pending_requests=pending,
        )
        assert should == False
        assert reason == EmailSuppressReason.SIMILAR_PENDING
        assert "Similar" in explanation

    def test_conservative_mode_sends_more(self):
        runstate = {"policy_mode": "conservative"}
        
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.PROGRESS_DIGEST,
        )
        assert should == True
        assert reason is None
        assert "Conservative" in explanation

    def test_low_interruption_skips_digest(self):
        runstate = {"policy_mode": "low_interruption", "digest_interval_hours": 24}
        
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.PROGRESS_DIGEST,
        )
        assert should == False
        assert reason in [EmailSuppressReason.LOW_INTERRUPTION_SKIP, EmailSuppressReason.INFORMATION_ONLY]

    def test_balanced_mode_medium_urgency_sent(self):
        runstate = {"policy_mode": "balanced"}
        
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.BLOCKER_REPORT,
        )
        assert should == True
        assert "Medium" in explanation or "Balanced" in explanation

    def test_balanced_mode_low_urgency_skipped(self):
        runstate = {"policy_mode": "balanced"}
        
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.PROGRESS_DIGEST,
        )
        assert should == False
        assert reason == EmailSuppressReason.LOW_INTERRUPTION_SKIP


class TestGetRateLimitHours:
    def test_high_urgency_short_limit(self):
        hours = get_rate_limit_hours("balanced", EmailTriggerType.ESCALATION_BLOCKER)
        assert hours == 1.0

    def test_conservative_lower_limit(self):
        hours = get_rate_limit_hours("conservative", EmailTriggerType.MILESTONE_REPORT)
        assert hours == 2.0

    def test_balanced_default_limit(self):
        hours = get_rate_limit_hours("balanced", EmailTriggerType.MILESTONE_REPORT)
        assert hours == DEFAULT_RATE_LIMIT_HOURS

    def test_low_interruption_high_limit(self):
        hours = get_rate_limit_hours("low_interruption", EmailTriggerType.PROGRESS_DIGEST)
        assert hours == DEFAULT_DIGEST_INTERVAL_HOURS


class TestClassifyEmailType:
    def test_blocker_is_decision_request(self):
        type, desc = classify_email_type(EmailTriggerType.ESCALATION_BLOCKER)
        assert type == "decision_request"
        assert "decision" in desc.lower() or "approval" in desc.lower()

    def test_risky_action_is_decision_request(self):
        type, desc = classify_email_type(EmailTriggerType.RISKY_ACTION_APPROVAL)
        assert type == "decision_request"

    def test_milestone_is_status_report(self):
        type, desc = classify_email_type(EmailTriggerType.MILESTONE_REPORT)
        assert type == "status_report"
        assert "Informational" in desc

    def test_reply_required_override(self):
        type, desc = classify_email_type(EmailTriggerType.MILESTONE_REPORT, reply_required=True)
        assert type == "decision_request"
        assert "reply" in desc.lower()


class TestGetEmailUrgency:
    def test_blocker_is_high(self):
        urgency = get_email_urgency(EmailTriggerType.ESCALATION_BLOCKER)
        assert urgency == EmailUrgency.HIGH

    def test_milestone_is_low(self):
        urgency = get_email_urgency(EmailTriggerType.MILESTONE_REPORT)
        assert urgency == EmailUrgency.LOW

    def test_blocker_report_is_medium(self):
        urgency = get_email_urgency(EmailTriggerType.BLOCKER_REPORT)
        assert urgency == EmailUrgency.MEDIUM


class TestCheckTimeoutCondition:
    def test_timeout_triggers_warning(self):
        sent_at = datetime.now() - timedelta(hours=50)
        needs_warning, hours, explanation = check_timeout_condition(sent_at, timeout_hours=48)
        assert needs_warning == True
        assert hours >= 48
        assert "exceeds" in explanation

    def test_within_threshold_no_warning(self):
        sent_at = datetime.now() - timedelta(hours=24)
        needs_warning, hours, explanation = check_timeout_condition(sent_at, timeout_hours=48)
        assert needs_warning == False
        assert hours < 48
        assert "within" in explanation

    def test_default_timeout_hours(self):
        assert DEFAULT_TIMEOUT_WARNING_HOURS == 48


class TestGetAppropriateTriggersForRunstate:
    def test_blocked_items_trigger_blocker(self):
        runstate = {"blocked_items": [{"item": "test"}], "policy_mode": "balanced"}
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert EmailTriggerType.ESCALATION_BLOCKER in triggers

    def test_critical_decision_trigger(self):
        runstate = {
            "decisions_needed": [{"decision": "test", "category": "critical"}],
            "policy_mode": "balanced",
        }
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert EmailTriggerType.ESCALATION_DECISION_REQUIRED in triggers

    def test_checkpoint_trigger(self):
        runstate = {
            "decisions_needed": [{"decision": "test", "category": "checkpoint"}],
            "policy_mode": "balanced",
        }
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert EmailTriggerType.HUMAN_CHECKPOINT in triggers

    def test_risky_action_trigger(self):
        runstate = {
            "pending_risky_actions": [{"action_type": "git_push", "requires_confirmation": True}],
            "policy_mode": "balanced",
        }
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert EmailTriggerType.RISKY_ACTION_APPROVAL in triggers

    def test_milestone_phase_trigger(self):
        runstate = {"current_phase": "milestone", "policy_mode": "balanced"}
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert EmailTriggerType.MILESTONE_REPORT in triggers

    def test_empty_runstate_no_triggers(self):
        runstate = {"policy_mode": "balanced"}
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert len(triggers) == 0


class TestFormatEscalationSummary:
    def test_format_includes_trigger_type(self):
        summary = format_escalation_summary(
            EmailTriggerType.ESCALATION_BLOCKER,
            True,
            None,
            "Test explanation",
        )
        assert EmailTriggerType.ESCALATION_BLOCKER.value in summary
        assert "Decision" in summary
        assert "Test explanation" in summary

    def test_format_shows_suppress_reason(self):
        summary = format_escalation_summary(
            EmailTriggerType.MILESTONE_REPORT,
            False,
            EmailSuppressReason.RATE_LIMITED,
            "Rate limited",
        )
        assert "rate_limited" in summary
        assert "Suppressed" in summary

    def test_format_shows_urgency(self):
        summary = format_escalation_summary(
            EmailTriggerType.ESCALATION_BLOCKER,
            True,
            None,
            "Test",
        )
        assert "high" in summary.lower()


class TestValidateEmailFrequency:
    def test_within_daily_limit(self):
        within, explanation = validate_email_frequency(3, max_emails_per_day=10)
        assert within == True
        assert "3/10" in explanation

    def test_exceeds_daily_limit(self):
        within, explanation = validate_email_frequency(10, max_emails_per_day=10)
        assert within == False
        assert "limit" in explanation.lower()

    def test_conservative_higher_limit(self):
        within, explanation = validate_email_frequency(12, max_emails_per_day=10, policy_mode="conservative")
        assert within == True
        assert "conservative" not in explanation.lower()

    def test_low_interruption_lower_limit(self):
        within, explanation = validate_email_frequency(6, max_emails_per_day=10, policy_mode="low_interruption")
        assert within == False


class TestTriggerToUrgencyMapping:
    def test_all_triggers_have_urgency(self):
        for trigger in EmailTriggerType:
            urgency = TRIGGER_TO_URGENCY.get(trigger)
            assert urgency is not None or trigger == EmailTriggerType.TIMEOUT_WARNING

    def test_escalation_triggers_are_high(self):
        assert TRIGGER_TO_URGENCY[EmailTriggerType.ESCALATION_BLOCKER] == EmailUrgency.HIGH
        assert TRIGGER_TO_URGENCY[EmailTriggerType.ESCALATION_DECISION_REQUIRED] == EmailUrgency.HIGH

    def test_report_triggers_are_low(self):
        assert TRIGGER_TO_URGENCY[EmailTriggerType.MILESTONE_REPORT] == EmailUrgency.LOW
        assert TRIGGER_TO_URGENCY[EmailTriggerType.PROGRESS_DIGEST] == EmailUrgency.LOW


class TestEndToEndEscalationPolicy:
    def test_full_policy_flow_blocker(self):
        runstate = {"policy_mode": "balanced", "blocked_items": [{"item": "test"}]}
        
        triggers = get_appropriate_triggers_for_runstate(runstate)
        assert EmailTriggerType.ESCALATION_BLOCKER in triggers
        
        should, reason, explanation = should_send_email(runstate, EmailTriggerType.ESCALATION_BLOCKER)
        assert should == True
        
        type, desc = classify_email_type(EmailTriggerType.ESCALATION_BLOCKER)
        assert type == "decision_request"

    def test_full_policy_flow_milestone_digest_suppressed(self):
        runstate = {"policy_mode": "low_interruption"}
        last_sent = datetime.now() - timedelta(hours=6)
        
        triggers = get_appropriate_triggers_for_runstate(runstate)
        should, reason, explanation = should_send_email(
            runstate,
            EmailTriggerType.PROGRESS_DIGEST,
            last_email_sent_at=last_sent,
        )
        assert should == False
        assert reason in [EmailSuppressReason.LOW_INTERRUPTION_SKIP, EmailSuppressReason.RATE_LIMITED]

    def test_frequency_limit_applies(self):
        runstate = {"policy_mode": "balanced"}
        
        within, explanation = validate_email_frequency(9, max_emails_per_day=10)
        assert within == True
        
        within, explanation = validate_email_frequency(11, max_emails_per_day=10)
        assert within == False