"""Tests for report_quality_rubric module (Feature 046)."""

import pytest

from runtime.report_quality_rubric import (
    evaluate_bluf_compliance,
    evaluate_one_screen_fit,
    evaluate_format_consistency,
    evaluate_explicit_ask,
    evaluate_options_provided,
    evaluate_recommendation_stated,
    evaluate_deadline_included,
    evaluate_outcomes_not_activities,
    evaluate_quantified_claims,
    evaluate_blocker_risk_separated,
    evaluate_no_hedging_language,
    evaluate_changed_items_only,
    evaluate_no_vanity_metrics,
    evaluate_truncation_applied,
    evaluate_report_quality,
    format_evaluation_summary,
    get_quality_level_for_score,
    get_improvement_priorities,
    compare_format_to_best_practice,
    get_future_improvements,
    QUALITY_LEVELS,
    ANTI_PATTERN_SEVERITY,
)


class TestEvaluateBLUFCompliance:
    def test_empty_summary_returns_zero(self):
        score, reason = evaluate_bluf_compliance("")
        assert score == 0
        assert "Missing" in reason

    def test_decision_keyword_in_first_line_passes(self):
        score, reason = evaluate_bluf_compliance("Blocked: API integration requires approval")
        assert score >= 6
        assert "leads" in reason.lower()

    def test_vague_opening_reduced_score(self):
        score, reason = evaluate_bluf_compliance("Update on project status for today")
        assert score <= 5
        assert "vague" in reason.lower()

    def test_milestone_keyword_passes(self):
        score, reason = evaluate_bluf_compliance("Milestone complete: Feature 046 shipped")
        assert score >= 6


class TestEvaluateOneScreenFit:
    def test_few_items_fits_screen(self):
        report = {
            "what_changed": ["item1", "item2"],
            "risks_blockers": [],
            "summary": "Progress update",
        }
        score, reason = evaluate_one_screen_fit(report)
        assert score >= 4
        assert "one-screen" in reason.lower()

    def test_many_items_exceeds_limit(self):
        report = {
            "what_changed": ["a", "b", "c", "d", "e", "f", "g", "h"],
            "risks_blockers": ["risk1", "risk2", "risk3"],
            "summary": "Very long summary text that exceeds normal limits for one screen",
        }
        score, reason = evaluate_one_screen_fit(report)
        assert score <= 4


class TestEvaluateFormatConsistency:
    def test_all_required_fields_pass(self):
        report = {
            "summary": "Test",
            "what_changed": ["item"],
            "current_state": "active",
            "reply_required": False,
        }
        score, reason = evaluate_format_consistency(report)
        assert score == 6
        assert "consistent" in reason.lower()

    def test_missing_fields_reduced_score(self):
        report = {"summary": "Test", "what_changed": ["item"]}
        score, reason = evaluate_format_consistency(report)
        assert score <= 4


class TestEvaluateExplicitAsk:
    def test_reply_required_with_specific_ask(self):
        report = {
            "reply_required": True,
            "next_step": "Please approve the deployment",
        }
        score, reason = evaluate_explicit_ask(report)
        assert score >= 8

    def test_reply_required_vague_ask(self):
        report = {
            "reply_required": True,
            "next_step": "Please do something",  # No specific keyword
        }
        score, reason = evaluate_explicit_ask(report)
        assert score == 6  # Vague ask, not specific

    def test_no_reply_required_informational(self):
        report = {
            "reply_required": False,
            "recommendation_type": "informational",
            "next_step": "No action needed",
        }
        score, reason = evaluate_explicit_ask(report)
        assert score >= 8


class TestEvaluateOptionsProvided:
    def test_options_mentioned_for_blocker(self):
        report = {
            "report_type": "blocker",
            "risks_blockers": ["API timeout. Options: retry, skip, escalate"],
        }
        score, reason = evaluate_options_provided(report)
        assert score >= 6

    def test_no_options_for_blocker(self):
        report = {
            "report_type": "blocker",
            "risks_blockers": ["API timeout blocking progress"],
        }
        score, reason = evaluate_options_provided(report)
        assert score <= 5

    def test_progress_report_no_options_needed(self):
        report = {"report_type": "progress"}
        score, reason = evaluate_options_provided(report)
        assert score >= 6


class TestEvaluateRecommendationStated:
    def test_required_decision_with_recommendation(self):
        report = {
            "recommendation_type": "required_decision",
            "next_step": "Approve Option B for faster delivery",
        }
        score, reason = evaluate_recommendation_stated(report)
        assert score >= 5

    def test_required_decision_missing_next_step(self):
        report = {
            "recommendation_type": "required_decision",
            "next_step": "",
        }
        score, reason = evaluate_recommendation_stated(report)
        assert score <= 4

    def test_recommendation_type_set(self):
        report = {"recommendation_type": "recommendation"}
        score, reason = evaluate_recommendation_stated(report)
        assert score >= 5


class TestEvaluateDeadlineIncluded:
    def test_deadline_in_blocker(self):
        report = {
            "report_type": "blocker",
            "summary": "Blocked: API integration. Decision needed by Friday",
        }
        score, reason = evaluate_deadline_included(report)
        assert score >= 4

    def test_progress_no_deadline_needed(self):
        report = {"report_type": "progress"}
        score, reason = evaluate_deadline_included(report)
        assert score >= 4

    def test_blocker_missing_deadline(self):
        report = {
            "report_type": "blocker",
            "summary": "Cannot proceed - API timeout",  # No "by" keyword
            "risks_blockers": ["Production access missing"],
            "recommendation_type": "required_decision",
        }
        score, reason = evaluate_deadline_included(report)
        assert score == 2


class TestEvaluateOutcomesNotActivities:
    def test_outcomes_focused_items(self):
        report = {
            "what_changed": [
                "Completed feature implementation",
                "Validated API integration",
                "Delivered milestone 1",
            ]
        }
        score, reason = evaluate_outcomes_not_activities(report)
        assert score >= 6
        assert "outcome" in reason.lower()

    def test_activity_focused_items(self):
        report = {
            "what_changed": [
                "Met with team",
                "Discussed approach",
                "Started development",
            ]
        }
        score, reason = evaluate_outcomes_not_activities(report)
        assert score <= 5

    def test_empty_what_changed(self):
        report = {"what_changed": []}
        score, reason = evaluate_outcomes_not_activities(report)
        assert score <= 5


class TestEvaluateQuantifiedClaims:
    def test_metrics_provided(self):
        report = {"metrics": {"tests_passed": 15, "files_created": 3}}
        score, reason = evaluate_quantified_claims(report)
        assert score >= 5

    def test_number_in_summary(self):
        report = {"summary": "3 features completed today"}
        score, reason = evaluate_quantified_claims(report)
        assert score >= 4

    def test_milestone_without_metrics(self):
        report = {"report_type": "milestone", "summary": "Milestone complete"}
        score, reason = evaluate_quantified_claims(report)
        assert score <= 4


class TestEvaluateBlockerRiskSeparated:
    def test_no_risks_returns_pass(self):
        report = {"risks_blockers": []}
        score, reason = evaluate_blocker_risk_separated(report)
        assert score >= 4

    def test_only_blockers_present(self):
        report = {
            "risks_blockers": ["Blocked by API timeout", "Cannot proceed without approval"]
        }
        score, reason = evaluate_blocker_risk_separated(report)
        assert score >= 4

    def test_blockers_and_risks_mixed(self):
        report = {
            "risks_blockers": ["Blocked by API", "Risk: might delay next phase"]
        }
        score, reason = evaluate_blocker_risk_separated(report)
        assert score <= 4


class TestEvaluateNoHedgingLanguage:
    def test_confident_framing(self):
        report = {
            "summary": "Completed feature implementation",
            "next_step": "Proceed to testing",
            "risks_blockers": [],
        }
        score, reason = evaluate_no_hedging_language(report)
        assert score >= 4
        assert "confident" in reason.lower()

    def test_hedging_detected(self):
        report = {
            "summary": "Maybe we should consider this approach",
            "next_step": "I think we can proceed",
        }
        score, reason = evaluate_no_hedging_language(report)
        assert score <= 4

    def test_passive_voice_detected(self):
        report = {"summary": "It was decided to proceed"}
        score, reason = evaluate_no_hedging_language(report)
        assert score <= 4


class TestEvaluateChangedItemsOnly:
    def test_changed_items_high_signal(self):
        report = {"what_changed": ["Shipped Feature 046", "Resolved blocker"]}
        score, reason = evaluate_changed_items_only(report)
        assert score >= 6

    def test_noise_patterns_detected(self):
        report = {"what_changed": ["Everything is on track", "All good"]}
        score, reason = evaluate_changed_items_only(report)
        assert score <= 5

    def test_empty_what_changed(self):
        report = {"what_changed": []}
        score, reason = evaluate_changed_items_only(report)
        assert score <= 5


class TestEvaluateNoVanityMetrics:
    def test_no_metrics_no_vanity(self):
        report = {"metrics": {}}
        score, reason = evaluate_no_vanity_metrics(report)
        assert score >= 5

    def test_actionable_metrics(self):
        report = {"metrics": {"tests_passed": 15, "resolved": 3}}
        score, reason = evaluate_no_vanity_metrics(report)
        assert score >= 5

    def test_vanity_metrics_detected(self):
        report = {"metrics": {"total_files": 100, "lines_of_code": 5000}}
        score, reason = evaluate_no_vanity_metrics(report)
        assert score <= 5


class TestEvaluateTruncationApplied:
    def test_truncated_marker_present(self):
        report = {"what_changed": ["a", "b", "c"], "what_changed_truncated": True}
        score, reason = evaluate_truncation_applied(report)
        assert score >= 5

    def test_few_items_no_truncation_needed(self):
        report = {"what_changed": ["a", "b"]}
        score, reason = evaluate_truncation_applied(report)
        assert score >= 5

    def test_evidence_links_provided(self):
        report = {
            "what_changed": ["a", "b", "c", "d"],
            "evidence_links": ["tests/test.py"],
        }
        score, reason = evaluate_truncation_applied(report)
        assert score >= 4


class TestEvaluateReportQuality:
    def test_full_evaluation_returns_all_fields(self):
        report = {
            "report_id": "sr-001",
            "report_type": "progress",
            "summary": "Progress: 3 items completed",
            "what_changed": ["Completed feature", "Delivered milestone"],
            "current_state": "executing",
            "next_step": "Continue testing",
            "reply_required": False,
            "recommendation_type": "recommendation",
            "metrics": {"tests_passed": 10},
        }
        result = evaluate_report_quality(report)
        
        assert "total_score" in result
        assert "quality_level" in result
        assert "category_scores" in result
        assert "gaps" in result
        assert result["total_score"] >= 0

    def test_high_quality_report(self):
        report = {
            "report_id": "sr-002",
            "report_type": "blocker",
            "summary": "Blocked: API timeout. Decision needed by Friday",
            "what_changed": [],
            "current_state": "blocked",
            "risks_blockers": ["API timeout. Options: retry(A: faster), skip(B: risky), escalate"],
            "next_step": "Recommend Option A - retry with exponential backoff",
            "reply_required": True,
            "recommendation_type": "required_decision",
        }
        result = evaluate_report_quality(report)
        
        assert result["total_score"] >= 40

    def test_poor_quality_report(self):
        report = {
            "report_id": "sr-003",
            "report_type": "progress",
            "summary": "Update on things",  # Vague, no BLUF
            "what_changed": ["Met with team", "Discussed stuff"],  # Activities
            "current_state": "maybe progressing",  # Hedging
            "next_step": "I think we should maybe continue",  # Heavy hedging
            "risks_blockers": ["Maybe blocked", "Risk: something might happen"],  # Mixed + hedging
            "reply_required": False,
            "recommendation_type": "recommendation",
        }
        result = evaluate_report_quality(report)
        
        assert result["total_score"] <= 85
        assert len(result["gaps"]) >= 3
        assert "hedging_language" in result["anti_patterns_detected"]


class TestFormatEvaluationSummary:
    def test_summary_includes_score(self):
        result = {
            "report_id": "sr-001",
            "total_score": 75,
            "quality_level": "good",
            "category_scores": {
                "structure": {"score": 20, "max": 25},
            },
            "gaps": [],
            "recommendations": [],
            "anti_patterns_detected": [],
        }
        summary = format_evaluation_summary(result)
        
        assert "75/100" in summary
        assert "good" in summary


class TestGetQualityLevelForScore:
    def test_excellent_score(self):
        level = get_quality_level_for_score(95)
        assert level == "excellent"

    def test_good_score(self):
        level = get_quality_level_for_score(80)
        assert level == "good"

    def test_acceptable_score(self):
        level = get_quality_level_for_score(65)
        assert level == "acceptable"

    def test_needs_improvement_score(self):
        level = get_quality_level_for_score(50)
        assert level == "needs_improvement"

    def test_poor_score(self):
        level = get_quality_level_for_score(30)
        assert level == "poor"


class TestGetImprovementPriorities:
    def test_returns_top_priorities(self):
        result = {
            "gaps": [
                {"criterion": "bluf_compliance", "score": 3, "reason": "Vague"},
                {"criterion": "explicit_ask", "score": 4, "reason": "Implicit"},
                {"criterion": "quantified_claims", "score": 5, "reason": "No numbers"},
            ]
        }
        priorities = get_improvement_priorities(result)
        
        assert len(priorities) <= 5
        assert priorities[0]["priority"] in ["high", "medium"]

    def test_empty_gaps_returns_empty(self):
        result = {"gaps": []}
        priorities = get_improvement_priorities(result)
        
        assert len(priorities) == 0


class TestCompareFormatToBestPractice:
    def test_returns_alignment_analysis(self):
        report = {
            "summary": "Test",
            "what_changed": [],
            "current_state": "active",
            "next_step": "Continue",
            "reply_required": False,
            "recommendation_type": "recommendation",
            "metrics": {},
        }
        comparison = compare_format_to_best_practice(report)
        
        assert "current_format" in comparison
        assert "best_practice_targets" in comparison
        assert "alignment" in comparison
        assert "gaps" in comparison

    def test_identifies_missing_options(self):
        report = {"report_type": "blocker"}
        comparison = compare_format_to_best_practice(report)
        
        assert comparison["alignment"]["options_structure"] == "missing"

    def test_identifies_missing_deadline(self):
        report = {"report_type": "blocker"}
        comparison = compare_format_to_best_practice(report)
        
        assert comparison["alignment"]["deadline_included"] == "missing"


class TestGetFutureImprovements:
    def test_returns_improvement_list(self):
        improvements = get_future_improvements()
        
        assert len(improvements) >= 5
        assert improvements[0]["id"].startswith("046-")

    def test_high_priority_improvements_first(self):
        improvements = get_future_improvements()
        high_priority = [i for i in improvements if i["priority"] == "high"]
        
        assert len(high_priority) >= 3

    def test_all_have_required_fields(self):
        improvements = get_future_improvements()
        
        for imp in improvements:
            assert "id" in imp
            assert "description" in imp
            assert "priority" in imp
            assert "category" in imp


class TestQualityLevels:
    def test_all_levels_defined(self):
        assert "excellent" in QUALITY_LEVELS
        assert "good" in QUALITY_LEVELS
        assert "acceptable" in QUALITY_LEVELS
        assert "needs_improvement" in QUALITY_LEVELS
        assert "poor" in QUALITY_LEVELS

    def test_levels_have_bounds(self):
        for level, bounds in QUALITY_LEVELS.items():
            assert "min" in bounds
            assert "max" in bounds
            assert bounds["min"] <= bounds["max"]


class TestAntiPatternSeverity:
    def test_severities_defined(self):
        assert "building_up_to_recommendation" in ANTI_PATTERN_SEVERITY
        assert "hedging_language" in ANTI_PATTERN_SEVERITY
        assert "options_without_recommendation" in ANTI_PATTERN_SEVERITY

    def test_severities_are_valid(self):
        for ap, severity in ANTI_PATTERN_SEVERITY.items():
            assert severity in ["high", "medium", "low"]