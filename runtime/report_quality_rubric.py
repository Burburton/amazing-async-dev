"""Report quality rubric for evaluating status reports against best-practice standards.
Feature 046: Reporting Best-Practice Research & Iteration Pack.

Based on research from McKinsey Pyramid Principle, Harvard Business Review,
AI Advisory Board, WhenNotesFly, and Nielsen Norman Group.
"""

from typing import Any


# Quality levels
QUALITY_LEVELS = {
    "excellent": {"min": 90, "max": 100, "description": "Fully compliant with best practices"},
    "good": {"min": 75, "max": 89, "description": "Mostly compliant, minor gaps"},
    "acceptable": {"min": 60, "max": 74, "description": "Meets minimum standards"},
    "needs_improvement": {"min": 40, "max": 59, "description": "Significant gaps, requires revision"},
    "poor": {"min": 0, "max": 39, "description": "Does not meet standards"},
}

# Anti-pattern severities
ANTI_PATTERN_SEVERITY = {
    "building_up_to_recommendation": "high",
    "over_including_methodology": "medium",
    "hedging_language": "medium",
    "passive_voice": "low",
    "implicit_ask": "high",
    "everything_is_fine": "high",
    "options_without_recommendation": "high",
    "long_narrative_paragraphs": "medium",
    "vanity_metrics": "medium",
    "blocker_risk_mixed": "medium",
}

# Hedging words to detect
HEDGING_WORDS = ["maybe", "might", "could", "perhaps", "possibly", "think", "guess", "probably"]

# Passive voice patterns
PASSIVE_PATTERNS = ["was decided", "was completed", "it was", "were done", "has been"]


def evaluate_bluf_compliance(summary: str) -> tuple[int, str]:
    """Evaluate BLUF (Bottom Line Up Front) compliance.
    
    Args:
        summary: Report summary line
        
    Returns:
        Tuple of (score, reason)
    """
    if not summary:
        return (0, "Missing summary")
    
    # Check for decision/ask keywords in first 50 chars
    first_part = summary[:50].lower()
    
    decision_keywords = [
        "blocked", "need", "require", "recommend", "decision",
        "approve", "complete", "milestone", "progress", "dogfood",
    ]
    
    has_decision_keyword = any(kw in first_part for kw in decision_keywords)
    
    if has_decision_keyword:
        return (8, "Summary leads with conclusion/status")
    
    # Vague opening
    vague_openings = ["update", "status", "report", "information"]
    if any(summary.lower().startswith(vo) for vo in vague_openings):
        return (4, "Summary starts with vague opening, consider BLUF format")
    
    return (6, "Summary present but could be more decisive")


def evaluate_one_screen_fit(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate one-screen constraint compliance.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    what_changed = report.get("what_changed", [])
    risks = report.get("risks_blockers", [])
    summary_len = len(report.get("summary", ""))
    
    # Count items
    total_items = len(what_changed) + len(risks)
    
    if total_items <= 5 and summary_len <= 100:
        return (6, "Fits one-screen: ≤5 items, summary ≤100 chars")
    
    if total_items <= 8 and summary_len <= 150:
        return (4, "Close to one-screen limit, consider compression")
    
    return (2, "Exceeds one-screen limit, apply compression")


def evaluate_format_consistency(report: dict[str, Any]) -> tuple[int, str]:
    required_fields = ["summary", "what_changed", "current_state", "reply_required"]
    present = sum(1 for f in required_fields if f in report)
    
    if present == len(required_fields):
        return (6, "All required fields present, consistent format")
    
    if present >= 3:
        return (4, f"{present}/4 required fields present")
    
    return (2, "Missing required fields, inconsistent format")


def evaluate_explicit_headers(email_body: str | None = None) -> tuple[int, str]:
    """Evaluate section headers presence.
    
    Args:
        email_body: Formatted email body (optional)
        
    Returns:
        Tuple of (score, reason)
    """
    if not email_body:
        return (5, "Headers assumed in format function")
    
    header_patterns = ["**What Changed**", "**Current State**", "**Next Step**", "**Risks"]
    present = sum(1 for h in header_patterns if h in email_body)
    
    if present >= 3:
        return (5, f"{present} section headers present")
    
    return (3, f"Only {present} headers, consider adding more")


def evaluate_explicit_ask(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate explicit ask presence.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    reply_required = report.get("reply_required", False)
    next_step = report.get("next_step", "")
    
    if reply_required:
        # Check for specific ask keywords
        ask_keywords = ["approve", "decide", "choose", "confirm", "review", "provide"]
        has_specific_ask = any(kw in next_step.lower() for kw in ask_keywords)
        
        if has_specific_ask:
            return (10, "Explicit ask with specific action")
        
        return (6, "Reply required but ask could be more specific")
    
    # No reply required - check if informational is clear
    if "no reply" in next_step.lower() or "informational" in report.get("recommendation_type", "").lower():
        return (10, "Clear informational, no ask needed")
    
    return (8, "No reply required, informational intent clear")


def evaluate_options_provided(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate options structure for blockers.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    report_type = report.get("report_type", "progress")
    
    # Options only required for blocker and required_decision
    if report_type not in ["blocker", "progress"]:
        if report.get("recommendation_type") != "required_decision":
            return (8, "Options not required for this report type")
    
    # Check for options in risks_blockers or explicit field
    risks = report.get("risks_blockers", [])
    
    # Look for "Options:" pattern
    for risk in risks:
        if "options:" in risk.lower() or "option:" in risk.lower():
            return (8, "Options mentioned in blocker description")
    
    # Missing options for blocker
    if report_type == "blocker":
        return (4, "Blocker report missing explicit options")
    
    return (6, "Consider adding options for decision clarity")


def evaluate_recommendation_stated(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate recommendation presence.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    recommendation_type = report.get("recommendation_type", "recommendation")
    next_step = report.get("next_step", "")
    
    if recommendation_type == "required_decision":
        # Must have clear recommendation even when asking
        if next_step and len(next_step) > 10:
            return (7, "Recommendation stated in next_step")
        return (3, "Required decision missing clear recommendation")
    
    if recommendation_type == "recommendation":
        return (7, "Recommendation type set correctly")
    
    if recommendation_type == "optional_future_work":
        return (5, "Optional work correctly classified")
    
    return (4, "Recommendation type unclear")


def evaluate_deadline_included(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate decision deadline presence.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    report_type = report.get("report_type", "progress")
    recommendation_type = report.get("recommendation_type", "recommendation")
    
    # Deadline required for blocker and required_decision
    if report_type != "blocker" and recommendation_type != "required_decision":
        return (5, "Deadline not required for this report type")
    
    # Check for deadline patterns
    summary = report.get("summary", "")
    risks = report.get("risks_blockers", [])
    
    deadline_patterns = ["by", "before", "deadline", "due", "deadline:", "by:"]
    all_text = summary + " " + " ".join(risks)
    
    has_deadline = any(p in all_text.lower() for p in deadline_patterns)
    
    if has_deadline:
        return (5, "Deadline mentioned in report")
    
    return (2, "Blocker/decision missing deadline")


def evaluate_outcomes_not_activities(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate outcomes over activities.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    what_changed = report.get("what_changed", [])
    
    if not what_changed:
        return (4, "No progress items listed")
    
    # Activity keywords (bad)
    activity_keywords = ["met", "discussed", "started", "worked on", "began", "continued"]
    
    # Outcome keywords (good)
    outcome_keywords = ["completed", "finished", "delivered", "validated", "tested", "approved", "shipped", "resolved"]
    
    outcome_count = 0
    activity_count = 0
    
    for item in what_changed:
        item_lower = item.lower()
        if any(ok in item_lower for ok in outcome_keywords):
            outcome_count += 1
        elif any(ak in item_lower for ak in activity_keywords):
            activity_count += 1
    
    if outcome_count >= len(what_changed) * 0.7:
        return (8, f"{outcome_count}/{len(what_changed)} items are outcomes")
    
    if activity_count > outcome_count:
        return (4, f"{activity_count} activity items, {outcome_count} outcomes - focus on outcomes")
    
    return (6, "Mixed outcomes and activities")


def evaluate_quantified_claims(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate quantification of claims.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    metrics = report.get("metrics", {})
    summary = report.get("summary", "")
    
    # Check for numbers in summary
    has_number = any(c.isdigit() for c in summary)
    
    if metrics and len(metrics) > 0:
        return (7, f"Metrics provided: {list(metrics.keys())}")
    
    if has_number:
        return (5, "Number present in summary")
    
    report_type = report.get("report_type", "progress")
    if report_type in ["milestone", "blocker"]:
        return (3, f"{report_type} report should include quantification")
    
    return (5, "Quantification optional for this type")


def evaluate_blocker_risk_separated(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate blocker/risk separation.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    risks_blockers = report.get("risks_blockers", [])
    
    if not risks_blockers:
        return (5, "No risks/blockers to separate")
    
    # Check for explicit separation
    blocker_keywords = ["blocked", "blocker", "cannot", "stuck", "halted"]
    risk_keywords = ["risk", "may", "could", "potential", "concern"]
    
    blockers = []
    risks = []
    
    for item in risks_blockers:
        item_lower = item.lower()
        if any(bk in item_lower for bk in blocker_keywords):
            blockers.append(item)
        elif any(rk in item_lower for rk in risk_keywords):
            risks.append(item)
    
    if blockers and risks:
        # Mixed - not separated
        return (3, f"Blockers ({len(blockers)}) and risks ({len(risks)}) mixed")
    
    if blockers:
        return (5, "Only blockers present (no risks)")
    
    if risks:
        return (5, "Only risks present (no blockers)")
    
    return (4, "Items unclear as blocker or risk")


def evaluate_no_hedging_language(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate confident framing without hedging.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    summary = report.get("summary", "")
    next_step = report.get("next_step", "")
    risks = report.get("risks_blockers", [])
    
    all_text = summary + " " + next_step + " " + " ".join(risks)
    all_lower = all_text.lower()
    
    hedging_found = [w for w in HEDGING_WORDS if w in all_lower]
    
    if hedging_found:
        return (3, f"Hedging words found: {hedging_found}")
    
    # Check passive voice
    passive_found = [p for p in PASSIVE_PATTERNS if p in all_lower]
    
    if passive_found:
        return (4, f"Passive patterns found: {passive_found}")
    
    return (5, "Confident framing, no hedging")


def evaluate_changed_items_only(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate signal-to-noise: changed items only.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    what_changed = report.get("what_changed", [])
    
    if not what_changed:
        return (4, "Empty what_changed - consider adding changes")
    
    # Check for noise patterns
    noise_patterns = ["everything is", "all good", "no issues", "on track", "status: normal"]
    
    for item in what_changed:
        if any(np in item.lower() for np in noise_patterns):
            return (4, "Contains noise patterns like 'everything is fine'")
    
    return (8, f"{len(what_changed)} changed items, high signal")


def evaluate_no_vanity_metrics(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate no vanity metrics.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    metrics = report.get("metrics", {})
    
    if not metrics:
        return (6, "No metrics - no vanity metrics")
    
    # Vanity metric patterns
    vanity_keys = ["total", "count", "number", "size", "lines", "files"]
    
    actionable_keys = ["passed", "failed", "completed", "resolved", "duration"]
    
    vanity_count = sum(1 for k in metrics.keys() if any(vk in k.lower() for vk in vanity_keys))
    actionable_count = sum(1 for k in metrics.keys() if any(ak in k.lower() for ak in actionable_keys))
    
    if actionable_count > vanity_count:
        return (6, "Metrics are actionable")
    
    if vanity_count > 0:
        return (4, f"{vanity_count} vanity metrics without context")
    
    return (5, "Metrics present")


def evaluate_truncation_applied(report: dict[str, Any]) -> tuple[int, str]:
    """Evaluate truncation for signal-to-noise.
    
    Args:
        report: Status report dict
        
    Returns:
        Tuple of (score, reason)
    """
    what_changed = report.get("what_changed", [])
    evidence = report.get("evidence_links", [])
    
    # Check if truncation markers exist
    truncated = report.get("what_changed_truncated", False)
    
    if truncated:
        return (6, "Truncation marker present")
    
    if len(what_changed) <= 3:
        return (6, "Minimal items, no truncation needed")
    
    if evidence and len(evidence) > 0:
        return (5, "Evidence links provided for details")
    
    return (4, "Consider truncation or evidence links for long lists")


def evaluate_report_quality(report: dict[str, Any]) -> dict[str, Any]:
    """Evaluate status report against best-practice rubric.
    
    Args:
        report: Status report dict
        
    Returns:
        Evaluation result with scores, categories, and recommendations
    """
    results = {
        "report_id": report.get("report_id", "unknown"),
        "report_type": report.get("report_type", "progress"),
        "total_score": 0,
        "max_score": 100,
        "quality_level": "",
        "category_scores": {},
        "criteria_details": [],
        "gaps": [],
        "recommendations": [],
        "anti_patterns_detected": [],
    }
    
    # Category 1: Structure (25 pts)
    structure_scores = []
    
    bluf_score, bluf_reason = evaluate_bluf_compliance(report.get("summary", ""))
    structure_scores.append(("bluf_compliance", bluf_score, bluf_reason))
    
    screen_score, screen_reason = evaluate_one_screen_fit(report)
    structure_scores.append(("one_screen_fit", screen_score, screen_reason))
    
    format_score, format_reason = evaluate_format_consistency(report)
    structure_scores.append(("format_consistency", format_score, format_reason))
    
    header_score, header_reason = evaluate_explicit_headers()
    structure_scores.append(("explicit_headers", header_score, header_reason))
    
    structure_total = sum(s[1] for s in structure_scores)
    results["category_scores"]["structure"] = {
        "score": structure_total,
        "max": 25,
        "details": structure_scores,
    }
    
    # Category 2: Decision-Readiness (30 pts)
    decision_scores = []
    
    ask_score, ask_reason = evaluate_explicit_ask(report)
    decision_scores.append(("explicit_ask", ask_score, ask_reason))
    
    options_score, options_reason = evaluate_options_provided(report)
    decision_scores.append(("options_provided", options_score, options_reason))
    
    rec_score, rec_reason = evaluate_recommendation_stated(report)
    decision_scores.append(("recommendation_stated", rec_score, rec_reason))
    
    deadline_score, deadline_reason = evaluate_deadline_included(report)
    decision_scores.append(("deadline_included", deadline_score, deadline_reason))
    
    decision_total = sum(s[1] for s in decision_scores)
    results["category_scores"]["decision_readiness"] = {
        "score": decision_total,
        "max": 30,
        "details": decision_scores,
    }
    
    # Category 3: Content Quality (25 pts)
    content_scores = []
    
    outcomes_score, outcomes_reason = evaluate_outcomes_not_activities(report)
    content_scores.append(("outcomes_not_activities", outcomes_score, outcomes_reason))
    
    quant_score, quant_reason = evaluate_quantified_claims(report)
    content_scores.append(("quantified_claims", quant_score, quant_reason))
    
    sep_score, sep_reason = evaluate_blocker_risk_separated(report)
    content_scores.append(("blocker_risk_separated", sep_score, sep_reason))
    
    hedge_score, hedge_reason = evaluate_no_hedging_language(report)
    content_scores.append(("no_hedging_language", hedge_score, hedge_reason))
    
    content_total = sum(s[1] for s in content_scores)
    results["category_scores"]["content_quality"] = {
        "score": content_total,
        "max": 25,
        "details": content_scores,
    }
    
    # Category 4: Signal-to-Noise (20 pts)
    signal_scores = []
    
    changed_score, changed_reason = evaluate_changed_items_only(report)
    signal_scores.append(("changed_items_only", changed_score, changed_reason))
    
    vanity_score, vanity_reason = evaluate_no_vanity_metrics(report)
    signal_scores.append(("no_vanity_metrics", vanity_score, vanity_reason))
    
    trunc_score, trunc_reason = evaluate_truncation_applied(report)
    signal_scores.append(("truncation_applied", trunc_score, trunc_reason))
    
    signal_total = sum(s[1] for s in signal_scores)
    results["category_scores"]["signal_to_noise"] = {
        "score": signal_total,
        "max": 20,
        "details": signal_scores,
    }
    
    # Calculate total
    total = structure_total + decision_total + content_total + signal_total
    results["total_score"] = total
    
    # Determine quality level
    for level, bounds in QUALITY_LEVELS.items():
        if total >= bounds["min"] and total <= bounds["max"]:
            results["quality_level"] = level
            break
    
    # Collect all criteria details
    for cat_name, cat_data in results["category_scores"].items():
        for name, score, reason in cat_data["details"]:
            results["criteria_details"].append({
                "category": cat_name,
                "criterion": name,
                "score": score,
                "reason": reason,
            })
    
    # Identify gaps (score < 5)
    for detail in results["criteria_details"]:
        if detail["score"] < 5:
            results["gaps"].append({
                "criterion": detail["criterion"],
                "score": detail["score"],
                "reason": detail["reason"],
            })
    
    # Generate recommendations
    if total < 75:
        results["recommendations"].append("Review BLUF format - lead with conclusion/decision")
        results["recommendations"].append("Ensure explicit ask with deadline for blockers")
    
    if results["category_scores"]["decision_readiness"]["score"] < 20:
        results["recommendations"].append("Add options structure with pros/cons for decisions")
        results["recommendations"].append("Include decision deadline for blocker reports")
    
    if results["category_scores"]["content_quality"]["score"] < 18:
        results["recommendations"].append("Focus on outcomes, not activities")
        results["recommendations"].append("Add quantification for milestone/blocker reports")
    
    # Detect anti-patterns
    if bluf_score < 5:
        results["anti_patterns_detected"].append("building_up_to_recommendation")
    
    if hedge_score < 5:
        results["anti_patterns_detected"].append("hedging_language")
    
    if options_score < 5 and report.get("report_type") == "blocker":
        results["anti_patterns_detected"].append("options_without_recommendation")
    
    if sep_score < 5:
        results["anti_patterns_detected"].append("blocker_risk_mixed")
    
    return results


def format_evaluation_summary(eval_result: dict[str, Any]) -> str:
    """Format evaluation result as human-readable summary.
    
    Args:
        eval_result: Evaluation result dict
        
    Returns:
        Formatted summary string
    """
    lines = []
    
    lines.append(f"## Report Quality Evaluation: {eval_result['report_id']}")
    lines.append("")
    
    lines.append(f"**Total Score:** {eval_result['total_score']}/100")
    lines.append(f"**Quality Level:** {eval_result['quality_level']}")
    lines.append("")
    
    lines.append("### Category Scores")
    for cat, data in eval_result["category_scores"].items():
        pct = data["score"] / data["max"] * 100
        lines.append(f"- {cat}: {data['score']}/{data['max']} ({pct:.0f}%)")
    lines.append("")
    
    if eval_result["gaps"]:
        lines.append("### Gaps Identified")
        for gap in eval_result["gaps"]:
            lines.append(f"- {gap['criterion']}: {gap['score']} pts - {gap['reason']}")
        lines.append("")
    
    if eval_result["recommendations"]:
        lines.append("### Recommendations")
        for rec in eval_result["recommendations"]:
            lines.append(f"- {rec}")
        lines.append("")
    
    if eval_result["anti_patterns_detected"]:
        lines.append("### Anti-Patterns Detected")
        for ap in eval_result["anti_patterns_detected"]:
            severity = ANTI_PATTERN_SEVERITY.get(ap, "unknown")
            lines.append(f"- {ap} (severity: {severity})")
    
    return "\n".join(lines)


def get_quality_level_for_score(score: int) -> str:
    """Get quality level name for a score.
    
    Args:
        score: Total score
        
    Returns:
        Quality level name
    """
    for level, bounds in QUALITY_LEVELS.items():
        if score >= bounds["min"] and score <= bounds["max"]:
            return level
    return "poor"


def get_improvement_priorities(eval_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Get prioritized improvement actions based on gaps.
    
    Args:
        eval_result: Evaluation result dict
        
    Returns:
        List of improvement actions with priority
    """
    improvements = []
    
    # High priority gaps
    high_priority_criteria = [
        "bluf_compliance", "explicit_ask", "recommendation_stated",
        "options_provided", "deadline_included",
    ]
    
    for gap in eval_result.get("gaps", []):
        criterion = gap["criterion"]
        priority = "high" if criterion in high_priority_criteria else "medium"
        
        improvements.append({
            "criterion": criterion,
            "current_score": gap["score"],
            "target_score": 8,
            "priority": priority,
            "action": f"Improve {criterion} - {gap['reason']}",
        })
    
    # Sort by priority and score
    improvements.sort(key=lambda x: (-1 if x["priority"] == "high" else 0, -x["current_score"]))
    
    return improvements[:5]  # Top 5 priorities


def compare_format_to_best_practice(report: dict[str, Any]) -> dict[str, Any]:
    """Compare current format against best-practice targets.
    
    Args:
        report: Status report dict
        
    Returns:
        Comparison analysis with gaps and recommendations
    """
    comparison = {
        "current_format": {
            "has_summary": bool(report.get("summary")),
            "has_what_changed": bool(report.get("what_changed")),
            "has_current_state": bool(report.get("current_state")),
            "has_next_step": bool(report.get("next_step")),
            "has_reply_required": "reply_required" in report,
            "has_recommendation_type": "recommendation_type" in report,
            "has_continuation_status": "continuation_status" in report,
            "has_metrics": bool(report.get("metrics")),
            "has_evidence_links": bool(report.get("evidence_links")),
        },
        "best_practice_targets": {
            "bluf_first_line": "Summary must lead with conclusion",
            "one_screen": "≤400 words or ≤10 bullets",
            "explicit_ask": "States what specifically needed",
            "options_structure": "2-3 options with pros/cons for blockers",
            "recommendation_stated": "Clear recommendation, not just options",
            "deadline_included": "Decision needed by [date]",
            "outcomes_not_activities": "Progress = outcomes, not logs",
            "quantified_claims": "Numbers with qualitative statements",
            "blocker_risk_separated": "Blockers vs risks in separate sections",
            "no_hedging": "Active voice, confident framing",
        },
        "alignment": {},
        "gaps": [],
    }
    
    # Check alignment
    bp_targets = comparison["best_practice_targets"]
    current = comparison["current_format"]
    
    # BLUF alignment
    if current["has_summary"]:
        comparison["alignment"]["bluf_first_line"] = "partial"
        # Need to check actual content
    else:
        comparison["alignment"]["bluf_first_line"] = "missing"
        comparison["gaps"].append("Missing summary - BLUF principle not satisfied")
    
    # One-screen alignment (check in actual evaluation)
    comparison["alignment"]["one_screen"] = "check_required"
    
    # Explicit ask alignment
    if current["has_reply_required"] and current["has_next_step"]:
        comparison["alignment"]["explicit_ask"] = "partial"
        comparison["gaps"].append("reply_required is binary - consider explicit ask format")
    else:
        comparison["alignment"]["explicit_ask"] = "missing"
    
    # Options structure - not in current format
    comparison["alignment"]["options_structure"] = "missing"
    comparison["gaps"].append("No options field - blockers need options + pros/cons")
    
    # Recommendation stated
    if current["has_recommendation_type"]:
        comparison["alignment"]["recommendation_stated"] = "aligned"
    else:
        comparison["alignment"]["recommendation_stated"] = "missing"
    
    # Deadline - not in current format
    comparison["alignment"]["deadline_included"] = "missing"
    comparison["gaps"].append("No decision_deadline field - blockers need deadline")
    
    # Outcomes vs activities - check in actual evaluation
    comparison["alignment"]["outcomes_not_activities"] = "check_required"
    
    # Quantified claims
    if current["has_metrics"]:
        comparison["alignment"]["quantified_claims"] = "partial"
        comparison["gaps"].append("Metrics optional - should be mandatory for milestone/blocker")
    else:
        comparison["alignment"]["quantified_claims"] = "missing"
    
    # Blocker/risk separated - single field in current
    comparison["alignment"]["blocker_risk_separated"] = "missing"
    comparison["gaps"].append("risks_blockers combined - should separate blockers vs risks")
    
    # No hedging - check in actual evaluation
    comparison["alignment"]["no_hedging"] = "check_required"
    
    return comparison


def get_future_improvements() -> list[dict[str, Any]]:
    """Get list of future improvements for reporting format.
    
    Returns:
        List of improvement items with id, description, priority, category
    """
    return [
        {
            "id": "046-01",
            "description": "Add options structure with pros/cons format to status report",
            "priority": "high",
            "category": "decision_readiness",
            "impact": "Improves decision quality, prevents options without recommendation",
        },
        {
            "id": "046-02",
            "description": "Separate blockers (present) from risks (future) in report template",
            "priority": "high",
            "category": "content_quality",
            "impact": "Clearer urgency distinction, better prioritization",
        },
        {
            "id": "046-03",
            "description": "Add decision_deadline field for required_decision type",
            "priority": "high",
            "category": "decision_readiness",
            "impact": "Explicit deadline improves decision turnaround",
        },
        {
            "id": "046-04",
            "description": "Strengthen quantification enforcement for milestone/blocker reports",
            "priority": "medium",
            "category": "content_quality",
            "impact": "Better decision data, reduced ambiguity",
        },
        {
            "id": "046-05",
            "description": "Add SCQA framework support for complex decision requests",
            "priority": "low",
            "category": "structure",
            "impact": "Better framing for multi-stakeholder decisions",
        },
        {
            "id": "046-06",
            "description": "Add executive summary template for multi-feature projects",
            "priority": "low",
            "category": "structure",
            "impact": "Portfolio-level reporting capability",
        },
    ]