"""Review pack builder - generates DailyReviewPack from ExecutionResult and RunState."""

from datetime import datetime
from typing import Any


def build_daily_review_pack(
    execution_result: dict[str, Any], runstate: dict[str, Any]
) -> dict[str, Any]:
    """Build DailyReviewPack from ExecutionResult and RunState."""
    today = datetime.now().strftime("%Y-%m-%d")

    review_pack = {
        "date": today,
        "project_id": runstate.get("project_id", ""),
        "feature_id": runstate.get("feature_id", ""),
        "today_goal": _get_today_goal(execution_result),
        "what_was_completed": execution_result.get("completed_items", []),
        "evidence": _build_evidence(execution_result),
        "problems_found": _extract_problems(execution_result),
        "blocked_items": _convert_blocked_items(execution_result),
        "decisions_needed": _convert_decisions(execution_result),
        "recommended_options": _build_recommendations(execution_result),
        "tomorrow_plan": execution_result.get("recommended_next_step", ""),
    }

    optional_fields = {
        "risk_summary": _build_risk_summary(execution_result),
        "confidence_notes": _build_confidence_notes(execution_result),
        "open_followups": runstate.get("open_questions", []),
        "metrics_summary": _build_metrics_summary(execution_result),
    }

    for key, value in optional_fields.items():
        if value:
            review_pack[key] = value

    return review_pack


def _get_today_goal(execution_result: dict[str, Any]) -> str:
    """Extract today's goal from execution result."""
    execution_id = execution_result.get("execution_id", "")

    if execution_id:
        return f"Execution {execution_id} completed with status: {execution_result.get('status', 'unknown')}"

    return "Day execution completed"


def _build_evidence(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build evidence list from artifacts_created."""
    artifacts = execution_result.get("artifacts_created", [])
    evidence = []

    for artifact in artifacts:
        evidence.append({
            "item": artifact.get("name", ""),
            "path": artifact.get("path", ""),
            "verified": True,
        })

    return evidence


def _extract_problems(execution_result: dict[str, Any]) -> list[str]:
    """Extract problem descriptions from issues_found."""
    issues = execution_result.get("issues_found", [])
    problems = []

    for issue in issues:
        if isinstance(issue, dict):
            desc = issue.get("description", "")
            if desc:
                problems.append(desc)
        elif isinstance(issue, str):
            problems.append(issue)

    return problems


def _convert_blocked_items(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert blocked_reasons to blocked_items format."""
    blocked_reasons = execution_result.get("blocked_reasons", [])
    blocked_items = []

    for reason in blocked_reasons:
        blocked_items.append({
            "item": reason.get("reason", ""),
            "reason": reason.get("impact", ""),
            "status": "waiting",
        })

    return blocked_items


def _convert_decisions(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert decisions_required to decisions_needed format."""
    decisions_required = execution_result.get("decisions_required", [])
    decisions_needed = []

    for decision in decisions_required:
        decisions_needed.append({
            "decision": decision.get("decision", ""),
            "options": decision.get("options", []),
            "recommendation": decision.get("recommendation", ""),
            "impact": decision.get("context", ""),
            "urgency": decision.get("urgency", "medium"),
        })

    return decisions_needed


def _build_recommendations(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build recommended_options from decisions_required."""
    decisions_required = execution_result.get("decisions_required", [])
    recommendations = []

    for decision in decisions_required:
        rec = decision.get("recommendation", "")
        if rec:
            recommendations.append({
                "decision": decision.get("decision", ""),
                "recommended": rec,
                "reason": f"Based on execution analysis",
            })

    return recommendations


def _build_risk_summary(execution_result: dict[str, Any]) -> str:
    """Build risk summary from execution result."""
    status = execution_result.get("status", "success")

    if status == "blocked":
        return "Execution blocked - requires resolution before proceeding"
    elif status == "partial":
        return "Partial completion - some deliverables not finished"
    elif status == "failed":
        return "Execution failed - review error details"

    return "No significant risks. Execution completed successfully."


def _build_confidence_notes(execution_result: dict[str, Any]) -> str:
    """Build confidence notes from verification result."""
    verification = execution_result.get("verification_result", {})

    passed = verification.get("passed", 0)
    failed = verification.get("failed", 0)

    if failed > 0:
        return f"Low confidence. {failed} verification steps failed."
    elif passed > 0:
        return f"High confidence. {passed} verification steps passed."

    return "Medium confidence. No verification data available."


def _build_metrics_summary(execution_result: dict[str, Any]) -> dict[str, Any]:
    """Build metrics summary from execution result."""
    metrics = execution_result.get("metrics", {})

    return {
        "execution_time": execution_result.get("duration", "N/A"),
        "files_created": len(execution_result.get("artifacts_created", [])),
        "decisions_made": metrics.get("decisions_made", 0),
    }