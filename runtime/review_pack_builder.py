"""Review pack builder - generates DailyReviewPack from ExecutionResult and RunState.

Feature 015: Enhanced with structured issues_summary, decision inbox, and next_day_recommendation.
Feature 016: Integrated decision template matching for consistent decision structure.
"""

from datetime import datetime
from typing import Any

from runtime.decision_templates import enhance_decision_with_template


def build_daily_review_pack(
    execution_result: dict[str, Any], runstate: dict[str, Any]
) -> dict[str, Any]:
    """Build DailyReviewPack from ExecutionResult and RunState."""
    today = datetime.now().strftime("%Y-%m-%d")

    review_pack = {
        "date": today,
        "project_id": runstate.get("project_id", ""),
        "feature_id": runstate.get("feature_id", ""),
        "today_goal": _get_today_goal(execution_result, runstate),
        "what_was_completed": _build_completed_items(execution_result),
        "evidence": _build_evidence(execution_result),
        "issues_summary": _build_issues_summary(execution_result),
        "problems_found": _build_problems_found(execution_result),
        "blocked_items": _convert_blocked_items(execution_result),
        "decisions_needed": _convert_decisions(execution_result),
        "recommended_options": _build_recommendations(execution_result),
        "next_day_recommendation": _build_next_day_recommendation(execution_result, runstate),
        "tomorrow_plan": _build_tomorrow_plan(execution_result),
    }

    optional_fields = {
        "risk_summary": _build_risk_summary(execution_result),
        "risk_watch_items": _build_risk_watch_items(execution_result, runstate),
        "confidence_notes": _build_confidence_notes(execution_result),
        "open_followups": runstate.get("open_questions", []),
        "metrics_summary": _build_metrics_summary(execution_result),
        "historical_context": _build_historical_context(runstate),
    }

    for key, value in optional_fields.items():
        if value:
            review_pack[key] = value

    return review_pack


def _get_today_goal(execution_result: dict[str, Any], runstate: dict[str, Any]) -> str:
    """Extract today's original goal from execution result or runstate."""
    execution_id = execution_result.get("execution_id", "")
    status = execution_result.get("status", "unknown")
    
    active_task = runstate.get("active_task", "")
    if active_task:
        return f"Goal: {active_task} (status: {status})"
    
    if execution_id:
        return f"Execution {execution_id} completed with status: {status}"

    return f"Day execution completed with status: {status}"


def _build_completed_items(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build structured completed items with descriptions."""
    completed = execution_result.get("completed_items", [])
    items = []
    
    for item in completed:
        if isinstance(item, dict):
            items.append(item)
        elif isinstance(item, str):
            items.append({
                "item": item,
                "description": _infer_description(item),
            })
    
    return items


def _infer_description(item_name: str) -> str:
    """Infer a brief description from item name."""
    if ".py" in item_name:
        if "test" in item_name:
            return "Test coverage for feature"
        elif "cli" in item_name or "command" in item_name:
            return "CLI command implementation"
        elif "runtime" in item_name:
            return "Runtime logic module"
        elif "schema" in item_name:
            return "Schema definition"
        elif "template" in item_name:
            return "Template file"
    elif ".md" in item_name:
        return "Documentation file"
    elif ".yaml" in item_name or ".yml" in item_name:
        return "Configuration or schema file"
    
    return "Delivered output"


def _build_evidence(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build evidence list from artifacts_created."""
    artifacts = execution_result.get("artifacts_created", [])
    evidence = []
    
    for artifact in artifacts:
        evidence.append({
            "item": artifact.get("name", ""),
            "path": artifact.get("path", ""),
            "verified": True,
            "verification_note": _get_verification_note(artifact, execution_result),
        })
    
    return evidence


def _get_verification_note(artifact: dict[str, Any], execution_result: dict[str, Any]) -> str:
    """Generate verification note for artifact."""
    verification = execution_result.get("verification_result", {})
    passed = verification.get("passed", 0)
    
    if passed > 0:
        return f"{passed} verification steps passed"
    
    return "Artifact created"


def _build_issues_summary(execution_result: dict[str, Any]) -> dict[str, Any]:
    """Build structured issues summary with resolved/unresolved distinction."""
    issues_found = execution_result.get("issues_found", [])
    issues_resolved = execution_result.get("issues_resolved", [])
    
    encountered = []
    for issue in issues_found:
        encountered.append({
            "description": issue.get("description", str(issue)),
            "severity": issue.get("severity", "medium"),
            "timestamp": issue.get("timestamp", ""),
        })
    
    resolved = []
    for issue in issues_resolved:
        resolved.append({
            "description": issue.get("description", ""),
            "resolution": issue.get("resolution", ""),
            "resolved_at": issue.get("resolved_at", ""),
        })
    
    unresolved = []
    for issue in issues_found:
        resolution = issue.get("resolution", "pending")
        if resolution == "pending" or resolution == "deferred":
            severity = issue.get("severity", "medium")
            blocking = resolution == "pending" and severity != "low"
            unresolved.append({
                "description": issue.get("description", str(issue)),
                "severity": severity,
                "blocking": blocking,
                "estimated_impact": _estimate_impact(issue),
            })
    
    return {
        "encountered": encountered,
        "resolved": resolved,
        "unresolved": unresolved,
    }


def _build_problems_found(execution_result: dict[str, Any]) -> list[str]:
    """Build backward-compatible problems_found list from issues."""
    issues_found = execution_result.get("issues_found", [])
    problems = []
    
    for issue in issues_found:
        if isinstance(issue, dict):
            desc = issue.get("description", "")
            if desc:
                problems.append(desc)
        elif isinstance(issue, str):
            problems.append(issue)
    
    return problems


def _build_tomorrow_plan(execution_result: dict[str, Any]) -> str:
    """Build backward-compatible tomorrow_plan string."""
    return execution_result.get("recommended_next_step", "")


def _estimate_impact(issue: dict[str, Any]) -> str:
    """Estimate impact of unresolved issue."""
    severity = issue.get("severity", "medium")
    if severity == "high":
        return "Blocking progress on current task"
    elif severity == "medium":
        return "May slow down execution"
    
    return "Minor impact, can proceed"


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
    """Convert decisions_required to enhanced decision inbox format with template matching."""
    decisions_required = execution_result.get("decisions_required", [])
    decisions_needed = []
    
    for i, decision in enumerate(decisions_required):
        decision_id = f"dec-{i+1:03d}"
        
        base_decision = {
            "decision_id": decision_id,
            "decision": decision.get("decision", ""),
            "decision_type": _infer_decision_type(decision),
            "options": decision.get("options", []),
            "recommendation": decision.get("recommendation", ""),
            "recommendation_reason": _infer_recommendation_reason(decision),
            "impact": decision.get("context", ""),
            "blocking_tomorrow": _is_blocking_tomorrow(decision),
            "defer_impact": _infer_defer_impact(decision),
            "urgency": decision.get("urgency", "medium"),
        }
        
        enhanced = enhance_decision_with_template(base_decision)
        
        if "template_id" not in enhanced:
            enhanced["is_template_based"] = False
        else:
            enhanced["is_template_based"] = True
        
        decisions_needed.append(enhanced)
    
    return decisions_needed


def _infer_decision_type(decision: dict[str, Any]) -> str:
    """Infer decision type from decision content."""
    decision_text = decision.get("decision", "").lower()
    context = decision.get("context", "").lower()
    
    if any(kw in decision_text for kw in ["api", "library", "technology", "stack", "format", "tool"]):
        return "technical"
    elif any(kw in decision_text for kw in ["scope", "include", "exclude", "limit"]):
        return "scope"
    elif any(kw in decision_text for kw in ["priority", "order", "first", "next"]):
        return "priority"
    
    if any(kw in context for kw in ["architecture", "implementation", "design"]):
        return "design"
    
    return "technical"


def _infer_recommendation_reason(decision: dict[str, Any]) -> str:
    """Generate recommendation reason."""
    recommendation = decision.get("recommendation", "")
    if not recommendation:
        return "Based on execution analysis"
    
    return f"Recommended based on project patterns and constraints"


def _is_blocking_tomorrow(decision: dict[str, Any]) -> bool:
    """Determine if decision blocks tomorrow's progress."""
    urgency = decision.get("urgency", "medium")
    context = decision.get("context", "")
    
    if urgency == "high":
        return True
    
    if any(kw in context.lower() for kw in ["blocking", "cannot proceed", "required"]):
        return True
    
    return False


def _infer_defer_impact(decision: dict[str, Any]) -> str:
    """Generate defer impact description."""
    if _is_blocking_tomorrow(decision):
        return "Blocking - cannot proceed without decision"
    
    return "Can proceed with alternative approach while deferred"


def _build_recommendations(execution_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build recommended_options from decisions_required."""
    decisions_required = execution_result.get("decisions_required", [])
    recommendations = []
    
    for i, decision in enumerate(decisions_required):
        rec = decision.get("recommendation", "")
        if rec:
            recommendations.append({
                "decision_id": f"dec-{i+1:03d}",
                "decision": decision.get("decision", ""),
                "recommended": rec,
                "reason": _infer_recommendation_reason(decision),
            })
    
    return recommendations


def _build_next_day_recommendation(execution_result: dict[str, Any], runstate: dict[str, Any]) -> dict[str, Any]:
    """Build structured next_day_recommendation."""
    next_step = execution_result.get("recommended_next_step", "")
    decisions = execution_result.get("decisions_required", [])
    
    blocking_decisions = []
    for i, d in enumerate(decisions):
        if _is_blocking_tomorrow(d):
            blocking_decisions.append(f"dec-{i+1:03d}")
    
    safe_to_execute = len(blocking_decisions) == 0 and execution_result.get("status") != "blocked"
    
    preconditions = []
    if runstate.get("blocked_items"):
        preconditions.append("Resolve blocked items")
    if blocking_decisions:
        preconditions.append(f"Make decisions: {', '.join(blocking_decisions)}")
    
    return {
        "action": next_step,
        "preconditions": preconditions,
        "safe_to_execute": safe_to_execute,
        "blocking_decisions": blocking_decisions,
        "estimated_scope": _estimate_scope(next_step, execution_result),
    }


def _estimate_scope(next_step: str, execution_result: dict[str, Any]) -> str:
    """Estimate effort for next action."""
    metrics = execution_result.get("metrics", {})
    files_written = metrics.get("files_written", 0)
    
    if files_written >= 5:
        return "full-day"
    elif files_written >= 2:
        return "half-day"
    elif "test" in next_step.lower() or "fix" in next_step.lower():
        return "quick"
    
    return "half-day"


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


def _build_risk_watch_items(execution_result: dict[str, Any], runstate: dict[str, Any]) -> list[dict[str, Any]]:
    """Build risk watch items - items that may become risky."""
    risks = []
    
    issues = execution_result.get("issues_found", [])
    for issue in issues:
        if issue.get("resolution") == "deferred":
            risks.append({
                "item": issue.get("description", ""),
                "risk_type": "quality",
                "current_status": "Deferred",
                "escalation_trigger": "Issue persists or severity increases",
            })
    
    if runstate.get("decisions_needed") and len(runstate.get("decisions_needed", [])) > 1:
        risks.append({
            "item": "Multiple pending decisions",
            "risk_type": "timeline",
            "current_status": f"{len(runstate.get('decisions_needed', []))} decisions pending",
            "escalation_trigger": "Decisions not made by next day",
        })
    
    return risks


def _build_confidence_notes(execution_result: dict[str, Any]) -> str:
    """Build confidence notes from verification result."""
    verification = execution_result.get("verification_result", {})
    
    passed = verification.get("passed", 0)
    failed = verification.get("failed", 0)
    
    if failed > 0:
        return f"Low confidence. {failed} verification steps failed."
    elif passed > 0:
        return f"High confidence. {passed} verification steps passed."
    
    status = execution_result.get("status", "success")
    if status == "success":
        return "High confidence. Execution completed successfully."
    elif status == "partial":
        return "Medium confidence. Partial completion with some deliverables unfinished."
    
    return "Medium confidence. No verification data available."


def _build_metrics_summary(execution_result: dict[str, Any]) -> dict[str, Any]:
    """Build metrics summary from execution result."""
    metrics = execution_result.get("metrics", {})
    artifacts = execution_result.get("artifacts_created", [])
    
    tests_added = 0
    for artifact in artifacts:
        name = artifact.get("name", "")
        if "test" in name:
            tests_added += 1
    
    return {
        "execution_time": execution_result.get("duration", "N/A"),
        "files_created": len(artifacts),
        "tests_added": tests_added,
        "decisions_made": metrics.get("decisions_made", 0),
    }


def _build_historical_context(runstate: dict[str, Any]) -> dict[str, Any] | None:
    """Build historical context from runstate if available."""
    related_archives = runstate.get("related_archives", [])
    lessons_applied = runstate.get("lessons_applied", [])
    
    if not related_archives and not lessons_applied:
        return None
    
    return {
        "related_archives": related_archives,
        "lessons_applied": lessons_applied,
    }