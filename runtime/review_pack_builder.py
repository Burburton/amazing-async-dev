"""Review pack builder - generates DailyReviewPack from ExecutionResult and RunState.

Feature 015: Enhanced with structured issues_summary, decision inbox, and next_day_recommendation.
Feature 016: Integrated decision template matching for consistent decision structure.
Feature 019a: Integrated workflow_feedback section for workflow/system issues.
Feature 019c: Integrated promotions section for promoted feedback.
Feature 033: Enriched with doctor assessment, recovery guidance, and feedback handoff signals.
Feature 037: Integrated continuation decision and checkpoint semantics.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.decision_templates import enhance_decision_with_template
from runtime.workflow_feedback_store import create_workflow_feedback_for_review
from runtime.feedback_promotion_store import create_promotions_for_review
from runtime.continuation_evaluator import evaluate_continuation, get_continuation_summary


def build_daily_review_pack(
    execution_result: dict[str, Any],
    runstate: dict[str, Any],
    project_path: Path | None = None,
    workflow_feedbacks: list[dict[str, Any]] | None = None,
    promotions: list[dict[str, Any]] | None = None,
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
    
    if project_path:
        doctor_assessment = _build_doctor_assessment(project_path)
        if doctor_assessment:
            review_pack["doctor_assessment"] = doctor_assessment

    if workflow_feedbacks:
        review_pack["workflow_feedback"] = create_workflow_feedback_for_review(workflow_feedbacks)

    if promotions:
        review_pack["promotions"] = create_promotions_for_review(promotions)

    continuation_decision = _build_continuation_decision(execution_result, runstate)
    if continuation_decision:
        review_pack["continuation_decision"] = continuation_decision

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
        if isinstance(issue, dict):
            encountered.append({
                "description": issue.get("description", ""),
                "severity": issue.get("severity", "medium"),
                "timestamp": issue.get("timestamp", ""),
            })
        else:
            encountered.append({
                "description": str(issue),
                "severity": "medium",
                "timestamp": "",
            })
    
    resolved = []
    for issue in issues_resolved:
        if isinstance(issue, dict):
            resolved.append({
                "description": issue.get("description", ""),
                "resolution": issue.get("resolution", ""),
                "resolved_at": issue.get("resolved_at", ""),
            })
    
    unresolved = []
    for issue in issues_found:
        if isinstance(issue, dict):
            resolution = issue.get("resolution", "pending")
            if resolution == "pending" or resolution == "deferred":
                severity = issue.get("severity", "medium")
                blocking = resolution == "pending" and severity != "low"
                unresolved.append({
                    "description": issue.get("description", ""),
                    "severity": severity,
                    "blocking": blocking,
                    "estimated_impact": _estimate_impact(issue),
                })
        else:
            # String issues are always pending and blocking
            unresolved.append({
                "description": str(issue),
                "severity": "medium",
                "blocking": True,
                "estimated_impact": "May slow down execution",
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
    metrics = execution_result.get("metrics", {})
    duration = execution_result.get("duration", "")
    
    for i, decision in enumerate(decisions_required):
        decision_id = f"dec-{i+1:03d}"
        
        options = decision.get("options", [])
        enhanced_options = _analyze_options(options, decision)
        
        base_decision = {
            "decision_id": decision_id,
            "decision": decision.get("decision", ""),
            "decision_type": _infer_decision_type(decision),
            "options": enhanced_options,
            "recommendation": decision.get("recommendation", ""),
            "recommendation_reason": _infer_recommendation_reason(decision, metrics, duration),
            "recommendation_confidence": _infer_recommendation_confidence(decision, metrics),
            "impact": decision.get("context", ""),
            "blocking_tomorrow": _is_blocking_tomorrow(decision),
            "defer_impact": _infer_defer_impact(decision),
            "urgency": decision.get("urgency", "medium"),
            "decision_context": _generate_decision_context(decision, execution_result),
        }
        
        enhanced = enhance_decision_with_template(base_decision)
        
        if "template_id" not in enhanced:
            enhanced["is_template_based"] = False
        else:
            enhanced["is_template_based"] = True
        
        decisions_needed.append(enhanced)
    
    return decisions_needed


def _analyze_options(options: list, decision: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze each option and add effort, risk, and impact metadata."""
    if not options:
        return []
    
    decision_text = decision.get("decision", "").lower()
    enhanced = []
    
    for i, opt in enumerate(options):
        if isinstance(opt, str):
            label = opt
            opt_id = chr(65 + i) if i < 26 else str(i)
        elif isinstance(opt, dict):
            label = opt.get("label", "")
            opt_id = opt.get("id", chr(65 + i) if i < 26 else str(i))
        else:
            label = str(opt)
            opt_id = chr(65 + i) if i < 26 else str(i)
        
        effort, risk, time_impact, quality_impact = _estimate_option_attributes(label, decision_text)
        
        enhanced_opt = {
            "id": opt_id,
            "label": label,
            "effort": effort,
            "risk": risk,
            "time_impact": time_impact,
            "quality_impact": quality_impact,
        }
        
        if isinstance(opt, dict):
            enhanced_opt["description"] = opt.get("description", "")
        
        enhanced.append(enhanced_opt)
    
    return enhanced


def _estimate_option_attributes(label: str, decision_text: str) -> tuple[str, str, str, str]:
    """Estimate effort, risk, time_impact, and quality_impact for an option."""
    label_lower = label.lower()
    
    effort = "medium"
    risk = "medium"
    time_impact = "medium"
    quality_impact = "neutral"
    
    if any(kw in label_lower for kw in ["simple", "basic", "minimal", "MVP", "fast", "quick", "temporary"]):
        effort = "low"
        risk = "low"
        time_impact = "low"
        quality_impact = "neutral"
    
    if any(kw in label_lower for kw in ["robust", "complete", "full", "proper", "enterprise"]):
        effort = "high"
        risk = "low"
        time_impact = "high"
        quality_impact = "positive"
    
    if any(kw in label_lower for kw in ["defer", "skip", "ignore", "postpone", "later"]):
        effort = "none"
        risk = "medium"
        time_impact = "none"
        quality_impact = "negative"
    
    if any(kw in label_lower for kw in ["experimental", "new", "cutting", "untested"]):
        effort = "medium"
        risk = "high"
        time_impact = "unknown"
        quality_impact = "unknown"
    
    if any(kw in label_lower for kw in ["multi", "several", "multiple", "all"]):
        effort = "high"
        time_impact = "high"
    
    if any(kw in label_lower for kw in ["single", "one", "only", "google-only"]):
        effort = "low"
        time_impact = "low"
    
    return effort, risk, time_impact, quality_impact


def _infer_recommendation_reason(decision: dict[str, Any], metrics: dict, duration: str) -> str:
    """Generate detailed recommendation reason based on context."""
    recommendation = decision.get("recommendation", "")
    decision_type = decision.get("decision_type", "technical")
    impact = decision.get("context", "")
    
    if not recommendation:
        return "Based on execution analysis"
    
    reason_parts = []
    
    if decision_type == "technical":
        if "simple" in recommendation.lower() or "basic" in recommendation.lower():
            reason_parts.append("Fastest path to MVP")
        elif "robust" in recommendation.lower() or "complete" in recommendation.lower():
            reason_parts.append("Long-term maintainability")
        elif "defer" in recommendation.lower():
            reason_parts.append("Preserve current momentum")
    
    if impact:
        reason_parts.append(f"Impact: {impact[:50]}")
    
    if duration:
        reason_parts.append(f"Execution took {duration}")
    
    files_read = metrics.get("files_read", 0)
    if files_read > 50:
        reason_parts.append("Deep context gathered - ready to decide")
    
    if not reason_parts:
        reason_parts.append("Recommended based on project patterns and constraints")
    
    return " | ".join(reason_parts)


def _infer_recommendation_confidence(decision: dict, metrics: dict) -> str:
    """Infer confidence level for the recommendation."""
    confidence = "medium"
    
    decision_type = decision.get("decision_type", "")
    has_context = bool(decision.get("context"))
    has_options = bool(decision.get("options"))
    
    if decision_type in ["scope", "priority"]:
        confidence = "high"
    elif has_context and has_options:
        confidence = "high"
    
    issues = len(decision.get("issues_found", []))
    if issues > 3:
        confidence = "low"
    
    return confidence


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


def _generate_decision_context(decision: dict[str, Any], execution_result: dict[str, Any]) -> str:
    """Generate context for why this decision is needed now."""
    context_parts = []
    
    completed_items = execution_result.get("completed_items", [])
    if completed_items:
        context_parts.append(f"After completing {len(completed_items)} items")
    
    issues = execution_result.get("issues_found", [])
    if issues:
        context_parts.append(f"encountered {len(issues)} issue(s)")
    
    status = execution_result.get("status", "")
    if status:
        context_parts.append(f"execution status: {status}")
    
    blocked = execution_result.get("blocked_reasons", [])
    if blocked:
        context_parts.append(f"blocked by: {blocked[0]}")
    
    if not context_parts:
        return "Decision needed to proceed with implementation"
    
    return " | ".join(context_parts)


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
                "reason": _infer_recommendation_reason(decision, {}, ""),
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
        if isinstance(issue, dict):
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


def _build_doctor_assessment(project_path: Path) -> dict[str, Any] | None:
    """Build doctor assessment section from diagnose_workspace."""
    from runtime.workspace_doctor import diagnose_workspace
    
    diagnosis = diagnose_workspace(project_path)
    
    assessment: dict[str, Any] = {
        "doctor_status": diagnosis.doctor_status,
        "health_status": diagnosis.health_status,
        "initialization_mode": diagnosis.initialization_mode,
        "current_phase": diagnosis.current_phase,
        "verification_status": diagnosis.verification_status,
        "pending_decisions": diagnosis.pending_decisions,
        "blocked_items_count": diagnosis.blocked_items_count,
        "recommended_action": diagnosis.recommended_action,
        "suggested_command": diagnosis.suggested_command,
    }
    
    if diagnosis.likely_cause:
        assessment["recovery_summary"] = {
            "likely_cause": diagnosis.likely_cause,
            "what_to_check": diagnosis.what_to_check,
            "recovery_steps": diagnosis.recovery_steps,
            "fallback_next_step": diagnosis.fallback_next_step,
        }
    
    if diagnosis.feedback_suggestion:
        feedback_handoff: dict[str, Any] = {
            "suggestion": diagnosis.feedback_suggestion,
            "reason": diagnosis.feedback_reason,
            "suggested_command": diagnosis.suggested_feedback_command,
        }
        
        if diagnosis.feedback_draft_summary:
            feedback_handoff["draft_summary"] = diagnosis.feedback_draft_summary
            feedback_handoff["draft_fields"] = diagnosis.feedback_draft_fields
        
        assessment["feedback_handoff"] = feedback_handoff
    
    if diagnosis.warnings:
        assessment["warnings"] = diagnosis.warnings
    
    if diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT":
        assessment["closeout_reminder"] = {
            "status": "Feature complete, pending archive/closeout",
            "action": "Archive or start new feature",
        }
    
    return assessment


def _build_continuation_decision(
    execution_result: dict[str, Any],
    runstate: dict[str, Any],
) -> dict[str, Any] | None:
    """Build continuation decision section from evaluation.
    
    Feature 037: Continuation semantics integration.
    """
    decision = evaluate_continuation(runstate, execution_result)
    
    return {
        "state": decision.state.value,
        "checkpoint_type": decision.checkpoint_type.value if decision.checkpoint_type else None,
        "continuation_allowed": decision.continuation_allowed,
        "next_stage": decision.next_stage.value if decision.next_stage else None,
        "reason": decision.reason,
        "escalation_required": decision.escalation_required,
        "stop_condition": decision.stop_condition.to_dict() if decision.stop_condition else None,
        "candidate_actions": decision.candidate_next_actions,
        "summary": get_continuation_summary(decision),
    }