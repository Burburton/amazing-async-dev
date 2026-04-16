"""Status report builder for high-signal email reporting (Feature 044).
Feature 045: Enhanced recommendation framing with why reasoning and continuation status.
"""

from datetime import datetime
from pathlib import Path
from typing import Any


REPORT_TYPES = ["progress", "milestone", "blocker", "dogfood"]

RECOMMENDATION_TYPES = ["recommendation", "required_decision", "optional_future_work"]

CONTINUATION_STATUS = ["autonomous_possible", "needs_input", "blocked"]


def classify_continuation_status(
    risks_blockers: list[str] | None,
    reply_required: bool,
) -> str:
    """Classify whether system can continue autonomously.
    
    Args:
        risks_blockers: Current risks/blockers
        reply_required: Whether reply is needed
        
    Returns:
        Continuation status: autonomous_possible, needs_input, blocked
    """
    blocker_keywords = ["blocked", "blocker", "cannot proceed", "stuck", "halted", "error", "fail"]
    
    if risks_blockers:
        for risk in risks_blockers:
            for kw in blocker_keywords:
                if kw.lower() in risk.lower():
                    return "blocked"
    
    if reply_required:
        return "needs_input"
    
    return "autonomous_possible"


def explain_why_recommendation(
    next_step: str,
    current_state: str,
    risks_blockers: list[str] | None = None,
    recommendation_type: str = "recommendation",
) -> str:
    """Generate brief explanation for why this is recommended.
    
    Args:
        next_step: The recommended next step
        current_state: Current execution state
        risks_blockers: Current risks/blockers
        recommendation_type: Type of recommendation
        
    Returns:
        Brief explanation string (max 80 chars)
    """
    if recommendation_type == "required_decision":
        return "Cannot proceed without human input"
    
    if recommendation_type == "optional_future_work":
        return "Low priority, can defer"
    
    if risks_blockers:
        return f"Best path given {len(risks_blockers)} active risks"
    
    if "complete" in current_state.lower() or "done" in current_state.lower():
        return "Natural progression from completed work"
    
    if "testing" in current_state.lower():
        return "Continue verification before next phase"
    
    if "executing" in current_state.lower():
        return "On track, continue current path"
    
    return "Next logical step in workflow"


def determine_recommendation_type(
    reply_required: bool,
    continuation_status: str,
    next_step: str | None = None,
) -> str:
    """Determine the recommendation type classification.
    
    Args:
        reply_required: Whether reply is needed
        continuation_status: Whether autonomous continuation is possible
        next_step: The next step content
        
    Returns:
        Recommendation type: recommendation, required_decision, optional_future_work
    """
    if continuation_status == "blocked" or reply_required:
        return "required_decision"
    
    if next_step:
        optional_keywords = ["consider", "may", "could", "optional", "later", "future"]
        for kw in optional_keywords:
            if kw in next_step.lower():
                return "optional_future_work"
    
    return "recommendation"


def frame_recommendation(
    next_step: str,
    current_state: str,
    risks_blockers: list[str] | None = None,
    reply_required: bool = False,
) -> dict[str, str]:
    """Frame recommendation with type and why reasoning.
    
    Args:
        next_step: Recommended next step
        current_state: Current state
        risks_blockers: Risks/blockers
        reply_required: Reply needed
        
    Returns:
        Dict with recommendation_type, why, continuation_status
    """
    continuation = classify_continuation_status(risks_blockers, reply_required)
    rec_type = determine_recommendation_type(reply_required, continuation, next_step)
    why = explain_why_recommendation(next_step, current_state, risks_blockers, rec_type)
    
    return {
        "recommendation_type": rec_type,
        "why": why,
        "continuation_status": continuation,
    }


def build_status_report(
    report_type: str,
    project_id: str,
    feature_id: str,
    summary: str,
    what_changed: list[str],
    current_state: str,
    risks_blockers: list[str] | None = None,
    next_step: str | None = None,
    reply_required: bool = False,
    evidence_links: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a high-signal status report.
    
    Args:
        report_type: Type of report (progress, milestone, blocker, dogfood)
        project_id: Project identifier
        feature_id: Feature identifier
        summary: One-line summary
        what_changed: List of changes made
        current_state: Current state description
        risks_blockers: List of current risks/blockers
        next_step: Recommended next step
        reply_required: Whether reply is needed
        evidence_links: Links to evidence artifacts
        metrics: Optional metrics
        
    Returns:
        Status report dict
    """
    if report_type not in REPORT_TYPES:
        report_type = "progress"
    
    now = datetime.now().isoformat()
    report_id = f"sr-{datetime.now().strftime('%Y%m%d')}-{hash(summary) % 1000:03d}"
    
    report = {
        "report_id": report_id,
        "report_type": report_type,
        "project_id": project_id,
        "feature_id": feature_id,
        "summary": summary,
        "what_changed": what_changed[:5] if what_changed else [],
        "current_state": current_state,
        "risks_blockers": risks_blockers or [],
        "next_step": next_step or "Continue execution",
        "reply_required": reply_required,
        "evidence_links": evidence_links or [],
        "metrics": metrics or {},
        "created_at": now,
    }
    
    if report_type == "milestone":
        report["milestone_name"] = summary
        report["milestone_complete"] = True
    
    if report_type == "blocker":
        report["blocking"] = True
        report["reply_required"] = True
    
    if report_type == "dogfood":
        report["dogfood_results"] = True
    
    frame = frame_recommendation(
        next_step or "Continue execution",
        current_state,
        risks_blockers,
        reply_required,
    )
    report["recommendation_type"] = frame["recommendation_type"]
    report["recommendation_why"] = frame["why"]
    report["continuation_status"] = frame["continuation_status"]
    
    if report_type == "blocker":
        report["continuation_status"] = "blocked"
        report["recommendation_type"] = "required_decision"
    
    return report


def build_progress_report(
    project_id: str,
    feature_id: str,
    completed_items: list[str],
    current_task: str,
    issues: list[str] | None = None,
) -> dict[str, Any]:
    """Build a progress update report.
    
    Args:
        project_id: Project identifier
        feature_id: Feature identifier
        completed_items: List of items completed
        current_task: Current active task
        issues: Any issues encountered
        
    Returns:
        Progress report dict
    """
    summary = f"Progress: {len(completed_items)} items completed, working on {current_task[:30]}"
    
    return build_status_report(
        report_type="progress",
        project_id=project_id,
        feature_id=feature_id,
        summary=summary,
        what_changed=completed_items,
        current_state=f"Executing: {current_task}",
        risks_blockers=issues,
        next_step="Continue current task",
        reply_required=False,
    )


def build_milestone_report(
    project_id: str,
    feature_id: str,
    milestone_name: str,
    deliverables: list[str],
    test_results: str | None = None,
) -> dict[str, Any]:
    """Build a milestone closure report.
    
    Args:
        project_id: Project identifier
        feature_id: Feature identifier
        milestone_name: Milestone name
        deliverables: List of deliverables
        test_results: Test result summary
        
    Returns:
        Milestone report dict
    """
    summary = f"Milestone complete: {milestone_name[:40]}"
    
    metrics = {}
    if test_results:
        metrics["tests"] = test_results
    
    return build_status_report(
        report_type="milestone",
        project_id=project_id,
        feature_id=feature_id,
        summary=summary,
        what_changed=deliverables,
        current_state="Milestone completed",
        risks_blockers=None,
        next_step="Proceed to next milestone",
        reply_required=False,
        metrics=metrics,
    )


def build_blocker_report(
    project_id: str,
    feature_id: str,
    blocker_reason: str,
    options: list[str] | None = None,
    recommendation: str | None = None,
) -> dict[str, Any]:
    """Build a blocker notification report.
    
    Args:
        project_id: Project identifier
        feature_id: Feature identifier
        blocker_reason: Reason for blocker
        options: Available options
        recommendation: Recommended resolution
        
    Returns:
        Blocker report dict
    """
    summary = f"Blocked: {blocker_reason[:40]}"
    
    risks = [blocker_reason]
    if options:
        risks.append(f"Options: {', '.join(options[:3])}")
    
    return build_status_report(
        report_type="blocker",
        project_id=project_id,
        feature_id=feature_id,
        summary=summary,
        what_changed=[],
        current_state="blocked",
        risks_blockers=risks,
        next_step=recommendation or "Resolve blocker",
        reply_required=True,
    )


def build_dogfood_report(
    project_id: str,
    feature_id: str,
    test_scenarios: list[str],
    results: dict[str, str],
    issues_found: list[str] | None = None,
) -> dict[str, Any]:
    """Build a dogfood test results report.
    
    Args:
        project_id: Project identifier
        feature_id: Feature identifier
        test_scenarios: Test scenarios run
        results: Scenario results
        issues_found: Issues discovered
        
    Returns:
        Dogfood report dict
    """
    passed = sum(1 for r in results.values() if r == "passed")
    total = len(results)
    
    summary = f"Dogfood: {passed}/{total} scenarios passed"
    
    what_changed = test_scenarios[:5]
    risks = issues_found or []
    
    return build_status_report(
        report_type="dogfood",
        project_id=project_id,
        feature_id=feature_id,
        summary=summary,
        what_changed=what_changed,
        current_state="Dogfood testing complete",
        risks_blockers=risks,
        next_step="Review results and proceed",
        reply_required=len(risks) > 0,
        metrics={"scenarios_passed": passed, "scenarios_total": total},
    )


def format_report_for_email(report: dict[str, Any]) -> str:
    """Format status report for email body.
    
    Creates a compact, one-screen summary format.
    
    Args:
        report: Status report dict
        
    Returns:
        Email body text
    """
    lines = []
    
    lines.append(f"## {report.get('summary', 'Status Update')}")
    lines.append("")
    
    lines.append("**What Changed:**")
    for item in report.get("what_changed", []):
        lines.append(f"  • {item}")
    if not report.get("what_changed"):
        lines.append("  (nothing new)")
    lines.append("")
    
    lines.append(f"**Current State:** {report.get('current_state', 'active')}")
    lines.append("")
    
    risks = report.get("risks_blockers", [])
    if risks:
        lines.append("**Risks / Blockers:**")
        for risk in risks:
            lines.append(f"  • {risk}")
        lines.append("")
    
    lines.append(f"**Next Step:** {report.get('next_step', 'Continue')}")
    
    rec_type = report.get("recommendation_type", "recommendation")
    why = report.get("recommendation_why", "")
    
    type_labels = {
        "recommendation": "→ Recommended",
        "required_decision": "⚠ Decision Required",
        "optional_future_work": "○ Optional",
    }
    
    type_label = type_labels.get(rec_type, "→ Recommended")
    lines.append(f"**{type_label}**")
    
    if why:
        lines.append(f"  Why: {why}")
    lines.append("")
    
    continuation = report.get("continuation_status", "autonomous_possible")
    cont_labels = {
        "autonomous_possible": "✓ Can continue autonomously",
        "needs_input": "⏸ Needs input before continuing",
        "blocked": "✗ Blocked until resolved",
    }
    
    cont_label = cont_labels.get(continuation, "✓ Can continue")
    lines.append(f"**Status:** {cont_label}")
    lines.append("")
    
    reply_req = report.get("reply_required", False)
    if reply_req:
        lines.append("**⚠ Reply Required**")
    else:
        lines.append("*No reply needed - informational*")
    lines.append("")
    
    evidence = report.get("evidence_links", [])
    if evidence:
        lines.append("**Evidence:**")
        for link in evidence:
            lines.append(f"  • {link}")
    
    lines.append("")
    lines.append("---")
    lines.append(f"Report: {report.get('report_id', 'unknown')}")
    lines.append(f"Project: {report.get('project_id', '')} / {report.get('feature_id', '')}")
    lines.append(f"Type: {report.get('report_type', 'progress')}")
    lines.append(f"Time: {report.get('created_at', '')}")
    
    return "\n".join(lines)


def format_report_subject(report: dict[str, Any], prefix: str = "[async-dev]") -> str:
    """Format email subject for status report.
    
    Args:
        report: Status report dict
        prefix: Subject prefix
        
    Returns:
        Email subject string
    """
    report_type = report.get("report_type", "progress")
    project_id = report.get("project_id", "")
    report_id = report.get("report_id", "")
    
    type_labels = {
        "progress": "Progress",
        "milestone": "Milestone",
        "blocker": "BLOCKER",
        "dogfood": "Dogfood",
    }
    
    type_label = type_labels.get(report_type, "Status")
    
    return f"{prefix} {type_label}: {project_id} [{report_id}]"


def compress_report_for_one_screen(report: dict[str, Any]) -> dict[str, Any]:
    """Compress report to fit one-screen constraint.
    
    Limits what_changed to 3 items, summary to 50 chars.
    
    Args:
        report: Status report dict
        
    Returns:
        Compressed report dict
    """
    compressed = report.copy()
    
    if len(compressed.get("what_changed", [])) > 3:
        compressed["what_changed"] = compressed["what_changed"][:3]
        compressed["what_changed_truncated"] = True
    
    if len(compressed.get("summary", "")) > 50:
        compressed["summary"] = compressed["summary"][:50] + "..."
    
    if len(compressed.get("risks_blockers", [])) > 2:
        compressed["risks_blockers"] = compressed["risks_blockers"][:2]
        compressed["risks_truncated"] = True
    
    return compressed


def is_report_high_signal(report: dict[str, Any]) -> bool:
    """Check if report meets high-signal criteria.
    
    Args:
        report: Status report dict
        
    Returns:
        True if report is high-signal
    """
    has_summary = bool(report.get("summary"))
    has_state = bool(report.get("current_state"))
    has_next_step = bool(report.get("next_step"))
    reply_explicit = "reply_required" in report
    
    return has_summary and has_state and has_next_step and reply_explicit