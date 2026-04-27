"""Observer Finding Persistence - Feature 067 hardening.

Provides persistence layer for observer findings.

Observer findings were previously ephemeral - disappeared after each run.
This module ensures findings are persisted to disk for:
- Audit trail
- Historical query
- Recovery Console consumption without re-running observer
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.artifact_router import get_observer_findings_path, get_observer_findings_dir
from runtime.execution_observer import ObservationResult, ObserverFinding


def save_observation_result(result: ObservationResult, project_path: Path) -> Path:
    """Persist observation result to disk.
    
    Creates observer-findings/{observation_id}.md file with full result.
    Also updates latest pointer file (C-006).
    
    Args:
        result: ObservationResult from execution_observer
        project_path: Project directory path
        
    Returns:
        Path to saved file
    """
    findings_dir = get_observer_findings_dir(project_path)
    findings_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = get_observer_findings_path(project_path, result.observation_id)
    
    content = _format_observation_result(result)
    output_path.write_text(content, encoding="utf-8")
    
    from runtime.latest_pointer_manager import update_pointer_after_observer_findings
    update_pointer_after_observer_findings(project_path, result.observation_id)
    
    return output_path


def load_observation_result(project_path: Path, observation_id: str) -> ObservationResult | None:
    """Load observation result from disk.
    
    Args:
        project_path: Project directory path
        observation_id: Observation identifier
        
    Returns:
        ObservationResult if found, None otherwise
    """
    findings_path = get_observer_findings_path(project_path, observation_id)
    
    if not findings_path.exists():
        return None
    
    content = findings_path.read_text(encoding="utf-8")
    return _parse_observation_result(content)


def list_observation_results(project_path: Path) -> list[str]:
    """List all observation IDs for a project.
    
    Args:
        project_path: Project directory path
        
    Returns:
        List of observation IDs (sorted by timestamp descending)
    """
    findings_dir = get_observer_findings_dir(project_path)
    
    if not findings_dir.exists():
        return []
    
    observation_ids = []
    for f in findings_dir.glob("*.md"):
        observation_ids.append(f.stem)
    
    return sorted(observation_ids, reverse=True)


def get_latest_observation_result(project_path: Path) -> ObservationResult | None:
    """Get most recent observation result.
    
    Args:
        project_path: Project directory path
        
    Returns:
        Latest ObservationResult if any, None otherwise
    """
    observation_ids = list_observation_results(project_path)
    
    if not observation_ids:
        return None
    
    return load_observation_result(project_path, observation_ids[0])


def get_cumulative_findings(project_path: Path, limit: int = 10) -> list[ObserverFinding]:
    """Get cumulative findings from recent observations.
    
    Aggregates findings across multiple observation runs, useful for
    Recovery Console overview.
    
    Args:
        project_path: Project directory path
        limit: Maximum number of observations to consider
        
    Returns:
        List of ObserverFinding objects (most recent first)
    """
    observation_ids = list_observation_results(project_path)[:limit]
    
    all_findings: list[ObserverFinding] = []
    
    for obs_id in observation_ids:
        result = load_observation_result(project_path, obs_id)
        if result:
            all_findings.extend(result.findings)
    
    return all_findings


def _format_observation_result(result: ObservationResult) -> str:
    """Format observation result as markdown."""
    lines = [
        "# ObservationResult",
        "",
        "```yaml",
        f"observation_id: {result.observation_id}",
        f"project_id: {result.project_id}",
        f"started_at: {result.started_at}",
        f"finished_at: {result.finished_at}",
        f"findings_count: {len(result.findings)}",
        f"execution_state_analyzed: {result.execution_state_analyzed}",
        f"artifacts_checked: {result.artifacts_checked}",
        f"verification_state_checked: {result.verification_state_checked}",
        f"closeout_state_checked: {result.closeout_state_checked}",
        f"acceptance_readiness_checked: {result.acceptance_readiness_checked}",
        f"has_critical: {result.has_critical_findings()}",
        f"has_recovery_significant: {result.has_recovery_significant()}",
        f"summary: {result.summary}",
        "```",
        "",
    ]
    
    if result.findings:
        lines.append("## Findings")
        lines.append("")
        
        for finding in result.findings:
            lines.extend(_format_finding_section(finding))
    
    return "\n".join(lines)


def _format_finding_section(finding: ObserverFinding) -> list[str]:
    """Format single finding as markdown section."""
    lines = [
        f"### {finding.finding_id}",
        "",
        "```yaml",
        f"finding_type: {finding.finding_type.value}",
        f"severity: {finding.severity.value}",
        f"execution_id: {finding.execution_id}",
        f"project_id: {finding.project_id}",
        f"feature_id: {finding.feature_id}",
        f"reason: {finding.reason}",
        f"detected_at: {finding.detected_at}",
        f"suggested_action: {finding.suggested_action}",
        f"suggested_command: {finding.suggested_command}",
        f"recovery_significant: {finding.recovery_significant}",
        f"resolved: {finding.resolved}",
        "```",
        "",
    ]
    
    if finding.details:
        lines.append("**Details:**")
        lines.append("")
        lines.append("```yaml")
        for key, value in finding.details.items():
            lines.append(f"{key}: {value}")
        lines.append("```")
        lines.append("")
    
    if finding.related_artifacts:
        lines.append("**Related Artifacts:**")
        lines.append("")
        for artifact in finding.related_artifacts:
            lines.append(f"- {artifact}")
        lines.append("")
    
    return lines


def _parse_observation_result(content: str) -> ObservationResult:
    """Parse observation result from markdown content."""
    from runtime.execution_observer import (
        ObserverFindingType,
        FindingSeverity,
        ObserverFinding,
    )
    
    lines = content.split("\n")
    
    yaml_data: dict[str, Any] = {}
    in_yaml = False
    in_header_yaml = False
    
    findings: list[ObserverFinding] = []
    
    current_finding_yaml: dict[str, Any] = {}
    in_finding_yaml = False
    in_finding_section = False
    
    for i, line in enumerate(lines):
        if line == "```yaml":
            in_yaml = True
            if not in_finding_section:
                in_header_yaml = True
            elif not in_finding_yaml:
                in_finding_yaml = True
            continue
        
        if line == "```" and in_yaml:
            in_yaml = False
            
            if in_header_yaml:
                in_header_yaml = False
            
            if in_finding_yaml and current_finding_yaml:
                finding = ObserverFinding(
                    finding_id=current_finding_yaml.get("finding_id", ""),
                    finding_type=ObserverFindingType(current_finding_yaml.get("finding_type", "")),
                    severity=FindingSeverity(current_finding_yaml.get("severity", "info")),
                    execution_id=current_finding_yaml.get("execution_id") or None,
                    project_id=current_finding_yaml.get("project_id") or None,
                    feature_id=current_finding_yaml.get("feature_id") or None,
                    reason=current_finding_yaml.get("reason", ""),
                    detected_at=current_finding_yaml.get("detected_at", ""),
                    suggested_action=current_finding_yaml.get("suggested_action", ""),
                    suggested_command=current_finding_yaml.get("suggested_command", ""),
                    recovery_significant=str(current_finding_yaml.get("recovery_significant", "false")).lower() == "true",
                    resolved=str(current_finding_yaml.get("resolved", "false")).lower() == "true",
                )
                findings.append(finding)
                current_finding_yaml = {}
                in_finding_yaml = False
                in_finding_section = False
            continue
        
        if line.startswith("### find-"):
            in_finding_section = True
            current_finding_yaml = {}
            continue
        
        if line.startswith("## ") or line.startswith("# "):
            in_finding_section = False
            in_finding_yaml = False
            continue
        
        if in_yaml and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            if in_header_yaml:
                yaml_data[key] = value
            elif in_finding_yaml:
                current_finding_yaml[key] = value
    
    return ObservationResult(
        observation_id=yaml_data.get("observation_id", ""),
        project_id=yaml_data.get("project_id", ""),
        started_at=yaml_data.get("started_at", ""),
        finished_at=yaml_data.get("finished_at", ""),
        findings=findings,
        execution_state_analyzed=str(yaml_data.get("execution_state_analyzed", "false")).lower() == "true",
        artifacts_checked=str(yaml_data.get("artifacts_checked", "false")).lower() == "true",
        verification_state_checked=str(yaml_data.get("verification_state_checked", "false")).lower() == "true",
        closeout_state_checked=str(yaml_data.get("closeout_state_checked", "false")).lower() == "true",
        acceptance_readiness_checked=str(yaml_data.get("acceptance_readiness_checked", "false")).lower() == "true",
        summary=yaml_data.get("summary", ""),
    )