"""Tests for status_report_builder module (Feature 044 + Feature 045)."""

import pytest

from runtime.status_report_builder import (
    build_status_report,
    build_progress_report,
    build_milestone_report,
    build_blocker_report,
    build_dogfood_report,
    format_report_for_email,
    format_report_subject,
    compress_report_for_one_screen,
    is_report_high_signal,
    classify_continuation_status,
    explain_why_recommendation,
    determine_recommendation_type,
    frame_recommendation,
    REPORT_TYPES,
    RECOMMENDATION_TYPES,
    CONTINUATION_STATUS,
)


class TestBuildStatusReport:
    def test_build_progress_report(self):
        report = build_status_report(
            report_type="progress",
            project_id="test-project",
            feature_id="044",
            summary="Progress update",
            what_changed=["Created module", "Added tests"],
            current_state="Testing",
            reply_required=False,
        )
        
        assert report["report_type"] == "progress"
        assert report["project_id"] == "test-project"
        assert report["summary"] == "Progress update"
        assert len(report["what_changed"]) == 2
        assert report["reply_required"] == False

    def test_build_milestone_report(self):
        report = build_status_report(
            report_type="milestone",
            project_id="test-project",
            feature_id="044",
            summary="Milestone complete",
            what_changed=["Deliverable 1", "Deliverable 2"],
            current_state="Milestone completed",
            reply_required=False,
        )
        
        assert report["report_type"] == "milestone"
        assert report["milestone_complete"] == True

    def test_build_blocker_report_auto_reply_required(self):
        report = build_status_report(
            report_type="blocker",
            project_id="test-project",
            feature_id="044",
            summary="Blocked by API",
            what_changed=[],
            current_state="blocked",
            reply_required=False,
        )
        
        assert report["report_type"] == "blocker"
        assert report["reply_required"] == True
        assert report["blocking"] == True

    def test_invalid_report_type_defaults_to_progress(self):
        report = build_status_report(
            report_type="invalid",
            project_id="test",
            feature_id="044",
            summary="Test",
            what_changed=[],
            current_state="active",
            reply_required=False,
        )
        
        assert report["report_type"] == "progress"

    def test_limits_what_changed_to_five_items(self):
        report = build_status_report(
            report_type="progress",
            project_id="test",
            feature_id="044",
            summary="Test",
            what_changed=["a", "b", "c", "d", "e", "f", "g"],
            current_state="active",
            reply_required=False,
        )
        
        assert len(report["what_changed"]) == 5


class TestBuildProgressReport:
    def test_build_progress_report_convenience(self):
        report = build_progress_report(
            project_id="test",
            feature_id="044",
            completed_items=["item1", "item2"],
            current_task="testing",
        )
        
        assert report["report_type"] == "progress"
        assert "Progress" in report["summary"]
        assert report["reply_required"] == False


class TestBuildMilestoneReport:
    def test_build_milestone_report_convenience(self):
        report = build_milestone_report(
            project_id="test",
            feature_id="044",
            milestone_name="Phase 1 complete",
            deliverables=["schema", "tests"],
        )
        
        assert report["report_type"] == "milestone"
        assert "Milestone" in report["summary"]


class TestBuildBlockerReport:
    def test_build_blocker_report_convenience(self):
        report = build_blocker_report(
            project_id="test",
            feature_id="044",
            blocker_reason="API timeout",
            options=["retry", "skip"],
        )
        
        assert report["report_type"] == "blocker"
        assert report["reply_required"] == True


class TestBuildDogfoodReport:
    def test_build_dogfood_report_convenience(self):
        report = build_dogfood_report(
            project_id="test",
            feature_id="044",
            test_scenarios=["scenario1", "scenario2"],
            results={"scenario1": "passed", "scenario2": "passed"},
        )
        
        assert report["report_type"] == "dogfood"
        assert report["metrics"]["scenarios_passed"] == 2
        assert report["metrics"]["scenarios_total"] == 2


class TestFormatReportForEmail:
    def test_format_includes_summary(self):
        report = {
            "summary": "Test summary",
            "what_changed": ["change1"],
            "current_state": "testing",
            "next_step": "Continue",
            "reply_required": False,
            "report_id": "sr-001",
        }
        
        body = format_report_for_email(report)
        
        assert "Test summary" in body
        assert "change1" in body
        assert "testing" in body
        assert "Continue" in body
        assert "No reply needed" in body

    def test_format_shows_reply_required(self):
        report = {
            "summary": "Test",
            "what_changed": [],
            "current_state": "blocked",
            "next_step": "Resolve",
            "reply_required": True,
        }
        
        body = format_report_for_email(report)
        
        assert "Reply Required" in body

    def test_format_includes_evidence_links(self):
        report = {
            "summary": "Test",
            "what_changed": [],
            "current_state": "active",
            "evidence_links": ["tests/test.py", "output.log"],
        }
        
        body = format_report_for_email(report)
        
        assert "Evidence:" in body
        assert "tests/test.py" in body


class TestFormatReportSubject:
    def test_format_progress_subject(self):
        report = {
            "report_type": "progress",
            "project_id": "test-project",
            "report_id": "sr-001",
        }
        
        subject = format_report_subject(report)
        
        assert "Progress" in subject
        assert "test-project" in subject
        assert "sr-001" in subject

    def test_format_blocker_subject(self):
        report = {
            "report_type": "blocker",
            "project_id": "test",
            "report_id": "sr-002",
        }
        
        subject = format_report_subject(report)
        
        assert "BLOCKER" in subject


class TestCompressReportForOneScreen:
    def test_compress_limits_what_changed(self):
        report = {
            "summary": "Test summary",
            "what_changed": ["a", "b", "c", "d", "e"],
            "risks_blockers": [],
        }
        
        compressed = compress_report_for_one_screen(report)
        
        assert len(compressed["what_changed"]) == 3
        assert compressed.get("what_changed_truncated") == True

    def test_compress_limits_summary_length(self):
        report = {
            "summary": "This is a very long summary that exceeds the fifty character limit",
            "what_changed": [],
        }
        
        compressed = compress_report_for_one_screen(report)
        
        assert len(compressed["summary"]) <= 53
        assert "..." in compressed["summary"]

    def test_compress_limits_risks(self):
        report = {
            "summary": "Test",
            "what_changed": [],
            "risks_blockers": ["risk1", "risk2", "risk3", "risk4"],
        }
        
        compressed = compress_report_for_one_screen(report)
        
        assert len(compressed["risks_blockers"]) == 2


class TestIsReportHighSignal:
    def test_valid_report_is_high_signal(self):
        report = {
            "summary": "Test",
            "current_state": "active",
            "next_step": "Continue",
            "reply_required": False,
        }
        
        assert is_report_high_signal(report) == True

    def test_missing_reply_required_is_not_high_signal(self):
        report = {
            "summary": "Test",
            "current_state": "active",
            "next_step": "Continue",
        }
        
        assert is_report_high_signal(report) == False

    def test_missing_summary_is_not_high_signal(self):
        report = {
            "current_state": "active",
            "next_step": "Continue",
            "reply_required": False,
        }
        
        assert is_report_high_signal(report) == False


class TestReportTypes:
    def test_all_types_defined(self):
        assert "progress" in REPORT_TYPES
        assert "milestone" in REPORT_TYPES
        assert "blocker" in REPORT_TYPES
        assert "dogfood" in REPORT_TYPES


class TestClassifyContinuationStatus:
    def test_autonomous_when_no_risks_no_reply(self):
        status = classify_continuation_status([], False)
        assert status == "autonomous_possible"

    def test_needs_input_when_reply_required(self):
        status = classify_continuation_status([], True)
        assert status == "needs_input"

    def test_blocked_when_blocker_keyword_present(self):
        status = classify_continuation_status(["Blocked by API"], False)
        assert status == "blocked"

    def test_blocked_when_stuck_keyword_present(self):
        status = classify_continuation_status(["Stuck on dependency"], False)
        assert status == "blocked"


class TestExplainWhyRecommendation:
    def test_required_decision_explanation(self):
        why = explain_why_recommendation(
            next_step="Approve",
            current_state="waiting",
            recommendation_type="required_decision",
        )
        assert "human input" in why.lower()

    def test_optional_future_work_explanation(self):
        why = explain_why_recommendation(
            next_step="Consider refactoring",
            current_state="done",
            recommendation_type="optional_future_work",
        )
        assert "defer" in why.lower() or "low priority" in why.lower()

    def test_with_risks_explanation(self):
        why = explain_why_recommendation(
            next_step="Proceed",
            current_state="testing",
            risks_blockers=["API timeout"],
        )
        assert "risk" in why.lower()

    def test_completed_state_explanation(self):
        why = explain_why_recommendation(
            next_step="Next phase",
            current_state="milestone complete",
        )
        assert "completed" in why.lower() or "progression" in why.lower()


class TestDetermineRecommendationType:
    def test_required_decision_when_blocked(self):
        rec_type = determine_recommendation_type(
            reply_required=False,
            continuation_status="blocked",
        )
        assert rec_type == "required_decision"

    def test_required_decision_when_reply_required(self):
        rec_type = determine_recommendation_type(
            reply_required=True,
            continuation_status="needs_input",
        )
        assert rec_type == "required_decision"

    def test_optional_when_consider_keyword(self):
        rec_type = determine_recommendation_type(
            reply_required=False,
            continuation_status="autonomous_possible",
            next_step="Consider adding tests",
        )
        assert rec_type == "optional_future_work"

    def test_recommendation_default(self):
        rec_type = determine_recommendation_type(
            reply_required=False,
            continuation_status="autonomous_possible",
            next_step="Continue execution",
        )
        assert rec_type == "recommendation"


class TestFrameRecommendation:
    def test_frame_returns_all_fields(self):
        frame = frame_recommendation(
            next_step="Continue",
            current_state="active",
            risks_blockers=None,
            reply_required=False,
        )
        
        assert "recommendation_type" in frame
        assert "why" in frame
        assert "continuation_status" in frame

    def test_frame_for_blocked_state(self):
        frame = frame_recommendation(
            next_step="Resolve blocker",
            current_state="blocked",
            risks_blockers=["API blocker"],
            reply_required=True,
        )
        
        assert frame["recommendation_type"] == "required_decision"
        assert frame["continuation_status"] == "blocked"

    def test_frame_for_autonomous_state(self):
        frame = frame_recommendation(
            next_step="Continue testing",
            current_state="executing",
            risks_blockers=None,
            reply_required=False,
        )
        
        assert frame["recommendation_type"] == "recommendation"
        assert frame["continuation_status"] == "autonomous_possible"


class TestBuildStatusReportWithFraming:
    def test_report_includes_recommendation_type(self):
        report = build_status_report(
            report_type="progress",
            project_id="test",
            feature_id="045",
            summary="Progress",
            what_changed=["item1"],
            current_state="executing",
            reply_required=False,
        )
        
        assert "recommendation_type" in report
        assert report["recommendation_type"] == "recommendation"

    def test_report_includes_why(self):
        report = build_status_report(
            report_type="progress",
            project_id="test",
            feature_id="045",
            summary="Progress",
            what_changed=["item1"],
            current_state="testing",
            reply_required=False,
        )
        
        assert "recommendation_why" in report
        assert len(report["recommendation_why"]) > 0

    def test_report_includes_continuation_status(self):
        report = build_status_report(
            report_type="blocker",
            project_id="test",
            feature_id="045",
            summary="Blocked",
            what_changed=[],
            current_state="blocked",
            reply_required=True,
        )
        
        assert "continuation_status" in report
        assert report["continuation_status"] == "blocked"


class TestFormatReportWithFraming:
    def test_format_shows_recommendation_type(self):
        report = {
            "summary": "Test",
            "what_changed": [],
            "current_state": "active",
            "next_step": "Continue",
            "recommendation_type": "recommendation",
            "recommendation_why": "On track",
            "continuation_status": "autonomous_possible",
            "reply_required": False,
        }
        
        body = format_report_for_email(report)
        
        assert "Recommended" in body
        assert "Why:" in body or "why" in body.lower()

    def test_format_shows_required_decision(self):
        report = {
            "summary": "Blocked",
            "what_changed": [],
            "current_state": "blocked",
            "next_step": "Resolve",
            "recommendation_type": "required_decision",
            "continuation_status": "blocked",
            "reply_required": True,
        }
        
        body = format_report_for_email(report)
        
        assert "Decision Required" in body

    def test_format_shows_continuation_status(self):
        report = {
            "summary": "Test",
            "what_changed": [],
            "current_state": "active",
            "next_step": "Continue",
            "continuation_status": "autonomous_possible",
            "reply_required": False,
        }
        
        body = format_report_for_email(report)
        
        assert "autonomous" in body.lower() or "continue" in body.lower()


class TestRecommendationAndContinuationConstants:
    def test_all_recommendation_types_defined(self):
        assert "recommendation" in RECOMMENDATION_TYPES
        assert "required_decision" in RECOMMENDATION_TYPES
        assert "optional_future_work" in RECOMMENDATION_TYPES

    def test_all_continuation_statuses_defined(self):
        assert "autonomous_possible" in CONTINUATION_STATUS
        assert "needs_input" in CONTINUATION_STATUS
        assert "blocked" in CONTINUATION_STATUS