"""Tests for reply_action_mapper module (Feature 043)."""

import pytest

from runtime.reply_action_mapper import (
    REPLY_ACTION_MAP,
    map_reply_to_action,
    get_continuation_phase_for_reply,
    get_next_recommended_for_reply,
)
from runtime.reply_parser import ReplyCommand, ParsedReply


class TestReplyActionMap:
    def test_map_has_all_commands(self):
        assert ReplyCommand.DECISION in REPLY_ACTION_MAP
        assert ReplyCommand.APPROVE in REPLY_ACTION_MAP
        assert ReplyCommand.DEFER in REPLY_ACTION_MAP
        assert ReplyCommand.RETRY in REPLY_ACTION_MAP
        assert ReplyCommand.CONTINUE in REPLY_ACTION_MAP

    def test_decision_command_has_select_option_action(self):
        action = REPLY_ACTION_MAP[ReplyCommand.DECISION]
        assert action["runstate_action"] == "select_option"
        assert action["continuation_phase"] == "planning"

    def test_approve_command_has_approve_risky_action(self):
        action = REPLY_ACTION_MAP[ReplyCommand.APPROVE]
        assert action["runstate_action"] == "approve_risky_action"
        assert action["continuation_phase"] == "executing"

    def test_continue_command_has_clear_blocker_action(self):
        action = REPLY_ACTION_MAP[ReplyCommand.CONTINUE]
        assert action["runstate_action"] == "clear_blocker"
        assert action["continuation_phase"] == "executing"


class TestMapReplyToAction:
    def test_map_decision_reply(self):
        parsed = ParsedReply(
            command=ReplyCommand.DECISION,
            argument="A",
            is_valid=True,
            raw_text="DECISION A",
        )
        request = {
            "options": [{"id": "A", "label": "Use YAML"}],
        }
        
        result = map_reply_to_action(parsed, request)
        
        assert result["runstate_action"] == "select_option"
        assert result["selected_option_id"] == "A"
        assert result["selected_option_label"] == "Use YAML"

    def test_map_approve_reply(self):
        parsed = ParsedReply(
            command=ReplyCommand.APPROVE,
            argument="PUSH",
            is_valid=True,
            raw_text="APPROVE PUSH",
        )
        request = {}
        
        result = map_reply_to_action(parsed, request)
        
        assert result["runstate_action"] == "approve_risky_action"
        assert result["approved_action_type"] == "PUSH"

    def test_map_defer_reply(self):
        parsed = ParsedReply(
            command=ReplyCommand.DEFER,
            argument=None,
            is_valid=True,
            raw_text="DEFER",
        )
        request = {}
        
        result = map_reply_to_action(parsed, request)
        
        assert result["runstate_action"] == "defer_decision"
        assert result["continuation_phase"] == "planning"

    def test_map_retry_reply(self):
        parsed = ParsedReply(
            command=ReplyCommand.RETRY,
            argument=None,
            is_valid=True,
            raw_text="RETRY",
        )
        request = {}
        
        result = map_reply_to_action(parsed, request)
        
        assert result["runstate_action"] == "mark_retry_needed"
        assert result["continuation_phase"] == "executing"

    def test_map_unknown_reply(self):
        parsed = ParsedReply(
            command=None,
            argument=None,
            is_valid=False,
            raw_text="UNKNOWN",
        )
        request = {}
        
        result = map_reply_to_action(parsed, request)
        
        assert result["runstate_action"] == "unknown"


class TestGetContinuationPhaseForReply:
    def test_decision_returns_planning(self):
        phase = get_continuation_phase_for_reply(ReplyCommand.DECISION)
        assert phase == "planning"

    def test_continue_returns_executing(self):
        phase = get_continuation_phase_for_reply(ReplyCommand.CONTINUE)
        assert phase == "executing"

    def test_approve_returns_executing(self):
        phase = get_continuation_phase_for_reply(ReplyCommand.APPROVE)
        assert phase == "executing"


class TestGetNextRecommendedForReply:
    def test_decision_with_argument(self):
        result = get_next_recommended_for_reply(ReplyCommand.DECISION, "A")
        assert "A" in result

    def test_approve_with_argument(self):
        result = get_next_recommended_for_reply(ReplyCommand.APPROVE, "PUSH")
        assert "PUSH" in result

    def test_defer_without_argument(self):
        result = get_next_recommended_for_reply(ReplyCommand.DEFER)
        assert result == "Find alternative approach"