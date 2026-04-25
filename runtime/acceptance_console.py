"""Acceptance Console - Feature 074.

Operator surface for acceptance state and findings.
CLI commands for visibility and traceability.

Integration with:
- Feature 071 (AcceptanceRunner)
- Feature 073 (ReAcceptanceLoop)
- Feature 067 (Observer)
- Recovery Console (Feature 066a)
"""

from pathlib import Path
from typing import Any

from runtime.acceptance_runner import (
    load_acceptance_result,
    AcceptanceTerminalState,
)
from runtime.acceptance_pack_builder import load_acceptance_pack
from runtime.acceptance_recovery import (
    load_acceptance_recovery_pack,
    get_recovery_items_for_feature,
)
from runtime.reacceptance_loop import (
    load_attempt_history,
    get_acceptance_lineage,
    ReAcceptanceState,
)


def list_acceptance_results(
    project_path: Path,
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    """List acceptance results with optional status filter."""
    results_dir = project_path / "acceptance-results"
    
    if not results_dir.exists():
        return []
    
    results: list[dict[str, Any]] = []
    
    for result_file in results_dir.glob("*.md"):
        result = load_acceptance_result(project_path, result_file.stem)
        
        if result is None:
            continue
        
        if status_filter:
            if result.terminal_state.value != status_filter:
                continue
        
        pack = load_acceptance_pack(project_path, result.acceptance_pack_id)
        
        results.append({
            "acceptance_result_id": result.acceptance_result_id,
            "terminal_state": result.terminal_state.value,
            "feature_id": pack.feature_id if pack else "unknown",
            "attempt_number": result.attempt_number,
            "accepted_count": len(result.accepted_criteria),
            "failed_count": len(result.failed_criteria),
            "validated_at": result.validated_at,
        })
    
    return sorted(results, key=lambda r: r.get("validated_at", ""), reverse=True)


def show_acceptance_result(
    project_path: Path,
    acceptance_result_id: str,
) -> dict[str, Any] | None:
    """Show detailed acceptance result."""
    result = load_acceptance_result(project_path, acceptance_result_id)
    
    if result is None:
        return None
    
    pack = load_acceptance_pack(project_path, result.acceptance_pack_id)
    
    if pack is None:
        return None
    
    findings_summary = []
    for finding in result.findings:
        findings_summary.append({
            "criterion_id": finding.criterion_id,
            "criterion_text": finding.criterion_text,
            "result": finding.result,
            "evidence_found": finding.evidence_found,
            "notes": finding.notes,
        })
    
    remediation_summary = []
    for remediation in result.remediation_guidance:
        remediation_summary.append({
            "criterion_id": remediation.criterion_id,
            "issue_type": remediation.issue_type,
            "suggested_fix": remediation.suggested_fix,
            "priority": remediation.priority,
        })
    
    return {
        "acceptance_result_id": result.acceptance_result_id,
        "acceptance_pack_id": result.acceptance_pack_id,
        "feature_id": pack.feature_id,
        "execution_result_id": pack.execution_result_id,
        "terminal_state": result.terminal_state.value,
        "attempt_number": result.attempt_number,
        "validator_type": result.validator_identity.validator_type.value,
        "validator_id": result.validator_identity.validator_id,
        "findings": findings_summary,
        "accepted_criteria": result.accepted_criteria,
        "failed_criteria": result.failed_criteria,
        "conditional_criteria": result.conditional_criteria,
        "remediation_guidance": remediation_summary,
        "overall_summary": result.overall_summary,
        "confidence_score": result.confidence_score,
        "validated_at": result.validated_at,
    }


def show_acceptance_history(
    project_path: Path,
    feature_id: str,
) -> dict[str, Any]:
    """Show acceptance attempt history for a feature."""
    lineage = get_acceptance_lineage(project_path, feature_id)
    
    if not lineage:
        return {
            "feature_id": feature_id,
            "total_executions": 0,
            "attempts": [],
            "message": "No acceptance history found",
        }
    
    attempts_summary = []
    for entry in lineage:
        attempts_summary.append({
            "execution_result_id": entry.get("execution_result_id"),
            "total_attempts": entry.get("total_attempts"),
            "final_state": entry.get("final_state"),
            "accepted": entry.get("accepted"),
        })
    
    total_attempts = sum(e.get("total_attempts", 0) for e in lineage)
    accepted_executions = sum(1 for e in lineage if e.get("accepted"))
    
    return {
        "feature_id": feature_id,
        "total_executions": len(lineage),
        "total_attempts": total_attempts,
        "accepted_executions": accepted_executions,
        "attempts": attempts_summary,
    }


def show_recovery_status(
    project_path: Path,
    feature_id: str,
) -> dict[str, Any]:
    """Show recovery status from failed acceptance."""
    recovery_items = get_recovery_items_for_feature(project_path, feature_id)
    
    if not recovery_items:
        return {
            "feature_id": feature_id,
            "pending_items": 0,
            "message": "No pending recovery items",
        }
    
    items_summary = []
    critical_count = 0
    high_count = 0
    
    for item in recovery_items:
        items_summary.append({
            "recovery_item_id": item.recovery_item_id,
            "category": item.category.value if hasattr(item.category, 'value') else item.category,
            "priority": item.priority.value if hasattr(item.priority, 'value') else item.priority,
            "criterion_id": item.source_criterion_id,
            "issue_description": item.issue_description,
            "suggested_action": item.suggested_action,
        })
        
        priority_value = item.priority.value if hasattr(item.priority, 'value') else item.priority
        if priority_value == "critical":
            critical_count += 1
        elif priority_value == "high":
            high_count += 1
    
    return {
        "feature_id": feature_id,
        "pending_items": len(recovery_items),
        "critical_count": critical_count,
        "high_count": high_count,
        "items": items_summary,
        "next_action": f"Address {critical_count} critical and {high_count} high-priority items",
    }


def get_acceptance_summary(
    project_path: Path,
    feature_id: str,
) -> dict[str, Any]:
    """Get overall acceptance summary for a feature."""
    results = list_acceptance_results(project_path)
    
    feature_results = [r for r in results if r.get("feature_id") == feature_id]
    
    if not feature_results:
        return {
            "feature_id": feature_id,
            "status": "no_acceptance",
            "message": "No acceptance validation performed yet",
        }
    
    latest = feature_results[0]
    
    history = show_acceptance_history(project_path, feature_id)
    recovery = show_recovery_status(project_path, feature_id)
    
    status = "pending"
    next_action = ""
    
    if latest.get("terminal_state") == "accepted":
        status = "accepted"
        next_action = "Feature ready for completion"
    elif latest.get("terminal_state") == "conditional":
        status = "conditional"
        next_action = "Review conditional findings before completion"
    elif latest.get("terminal_state") == "rejected":
        status = "rejected"
        next_action = recovery.get("next_action", "Address recovery items")
    elif latest.get("terminal_state") == "manual_review":
        status = "manual_review"
        next_action = "Complete manual review and update state"
    elif latest.get("terminal_state") == "escalated":
        status = "escalated"
        next_action = "Resolve escalation before proceeding"
    
    return {
        "feature_id": feature_id,
        "status": status,
        "latest_result_id": latest.get("acceptance_result_id"),
        "latest_terminal_state": latest.get("terminal_state"),
        "attempt_number": latest.get("attempt_number"),
        "total_attempts": history.get("total_attempts", 0),
        "accepted_criteria": latest.get("accepted_count", 0),
        "failed_criteria": latest.get("failed_count", 0),
        "pending_recovery_items": recovery.get("pending_items", 0),
        "next_action": next_action,
    }


def format_acceptance_console_output(
    summary: dict[str, Any],
    include_details: bool = False,
) -> str:
    """Format acceptance summary for console output."""
    lines = []
    
    lines.append("=" * 60)
    lines.append("ACCEPTANCE CONSOLE")
    lines.append("=" * 60)
    lines.append("")
    
    lines.append(f"Feature: {summary.get('feature_id', 'unknown')}")
    lines.append(f"Status: {summary.get('status', 'unknown')}")
    lines.append("")
    
    if summary.get("latest_result_id"):
        lines.append(f"Latest Result: {summary.get('latest_result_id')}")
        lines.append(f"Terminal State: {summary.get('latest_terminal_state')}")
        lines.append(f"Attempt: #{summary.get('attempt_number', 1)}")
        lines.append("")
    
    lines.append(f"Total Attempts: {summary.get('total_attempts', 0)}")
    lines.append(f"Accepted Criteria: {summary.get('accepted_criteria', 0)}")
    lines.append(f"Failed Criteria: {summary.get('failed_criteria', 0)}")
    lines.append("")
    
    if summary.get("pending_recovery_items", 0) > 0:
        lines.append(f"Pending Recovery Items: {summary.get('pending_recovery_items')}")
    
    lines.append("")
    lines.append("Next Action:")
    lines.append(f"  {summary.get('next_action', 'No action specified')}")
    
    if include_details:
        lines.append("")
        lines.append("-" * 60)
        lines.append("Details:")
        lines.append("-" * 60)
        
        if summary.get("findings"):
            lines.append("")
            lines.append("Findings:")
            for f in summary.get("findings", []):
                lines.append(f"  [{f.get('result')}] {f.get('criterion_id')}: {f.get('criterion_text', '')[:50]}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)