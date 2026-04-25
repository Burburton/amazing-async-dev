"""Operator Home Adapter - Minimal Platform Overview.

Aggregates existing platform summaries into unified operator entry point.
Per operator-home-platform-overview.md Section 15:
- Active runs summary
- Attention queue
- Acceptance queue
- Observer highlight list
- Blocked-item summary
- Quick-link generation

This is a MINIMAL implementation (Bucket D - narrow operator UX fix).
Uses existing adapters, does not create new truth sources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.evidence_rollup import ProjectEvidenceSummary, LatestTruthResolver
from runtime.recovery_data_adapter import RecoveryDataAdapter, RecoveryItem
from runtime.acceptance_recovery_adapter import AcceptanceRecoveryAdapter, AcceptanceRecoverySummary
from runtime.execution_observer import run_observer, ObserverFinding
from runtime.state_store import StateStore


@dataclass
class ActiveRunItem:
    """Single active run summary for home display."""
    project_id: str
    feature_id: str
    status: str
    phase: str
    last_updated: str
    health_summary: str
    detail_path: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "feature_id": self.feature_id,
            "status": self.status,
            "phase": self.phase,
            "last_updated": self.last_updated,
            "health_summary": self.health_summary,
            "detail_path": self.detail_path,
        }


@dataclass
class AttentionItem:
    """Single attention-worthy item for home display."""
    category: str
    title: str
    severity: str
    reason: str
    suggested_action: str
    destination: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "title": self.title,
            "severity": self.severity,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
            "destination": self.destination,
        }


@dataclass
class AcceptanceQueueItem:
    """Single acceptance-relevant item for home display."""
    project_id: str
    feature_id: str
    acceptance_status: str
    terminal_state: str
    completion_blocked: bool
    attempt_count: int
    destination: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "feature_id": self.feature_id,
            "acceptance_status": self.acceptance_status,
            "terminal_state": self.terminal_state,
            "completion_blocked": self.completion_blocked,
            "attempt_count": self.attempt_count,
            "destination": self.destination,
        }


@dataclass
class ObserverHighlight:
    """Single observer finding highlight for home display."""
    finding_type: str
    severity: str
    summary: str
    recommended_action: str
    project_id: str
    destination: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "severity": self.severity,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "project_id": self.project_id,
            "destination": self.destination,
        }


@dataclass
class QuickLink:
    """Navigation link for home display."""
    label: str
    command: str
    description: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "description": self.description,
        }


@dataclass
class OperatorHomeOverview:
    """Complete operator home overview data model.
    
    Per operator-home-platform-overview.md Section 9:
    - active_runs_summary
    - attention_items
    - awaiting_acceptance_items
    - observer_highlights
    - blocked_items
    - quick_links
    """
    
    active_runs: list[ActiveRunItem] = field(default_factory=list)
    attention_items: list[AttentionItem] = field(default_factory=list)
    acceptance_queue: list[AcceptanceQueueItem] = field(default_factory=list)
    observer_highlights: list[ObserverHighlight] = field(default_factory=list)
    blocked_items: list[AttentionItem] = field(default_factory=list)
    quick_links: list[QuickLink] = field(default_factory=list)
    
    total_projects: int = 0
    total_features: int = 0
    healthy_count: int = 0
    blocked_count: int = 0
    attention_count: int = 0
    
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "active_runs": [r.to_dict() for r in self.active_runs],
            "attention_items": [a.to_dict() for a in self.attention_items],
            "acceptance_queue": [a.to_dict() for a in self.acceptance_queue],
            "observer_highlights": [o.to_dict() for o in self.observer_highlights],
            "blocked_items": [b.to_dict() for b in self.blocked_items],
            "quick_links": [l.to_dict() for l in self.quick_links],
            "total_projects": self.total_projects,
            "total_features": self.total_features,
            "healthy_count": self.healthy_count,
            "blocked_count": self.blocked_count,
            "attention_count": self.attention_count,
            "updated_at": self.updated_at,
        }
    
    def is_calm(self) -> bool:
        """Check if platform is in calm state (nothing requiring attention)."""
        return (
            len(self.attention_items) == 0
            and len(self.blocked_items) == 0
            and self.blocked_count == 0
        )
    
    def has_critical(self) -> bool:
        """Check if any critical severity items exist."""
        return any(
            item.severity == "critical"
            for item in self.attention_items + self.observer_highlights
        )


def build_operator_home_overview(projects_path: Path) -> OperatorHomeOverview:
    """Build complete operator home overview from all projects.
    
    Aggregates from:
    - StateStore (active runs)
    - RecoveryDataAdapter (recovery-needed)
    - AcceptanceRecoveryAdapter (acceptance-blocked)
    - execution_observer (observer findings)
    - ProjectEvidenceSummary (evidence rollup)
    """
    
    overview = OperatorHomeOverview()
    
    if not projects_path.exists():
        return overview
    
    project_dirs = [
        p for p in projects_path.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ]
    
    overview.total_projects = len(project_dirs)
    
    all_attention_items = []
    all_acceptance_items = []
    all_observer_highlights = []
    all_blocked_items = []
    
    for project_path in project_dirs:
        project_id = project_path.name
        
        store = StateStore(project_path)
        runstate = store.load_runstate()
        
        if runstate:
            feature_id = runstate.get("feature_id", "")
            phase = runstate.get("current_phase", "")
            updated_at = runstate.get("updated_at", "")
            
            if feature_id and phase not in ["completed", "archived"]:
                health = "healthy" if phase in ["planning", "reviewing"] else "active"
                if runstate.get("acceptance_recovery_pending"):
                    health = "blocked"
                elif runstate.get("blocked_items"):
                    health = "blocked"
                
                active_run = ActiveRunItem(
                    project_id=project_id,
                    feature_id=feature_id,
                    status="active",
                    phase=phase,
                    last_updated=updated_at[:19] if updated_at else "",
                    health_summary=health,
                    detail_path=f"asyncdev evidence summary --project {project_id}",
                )
                overview.active_runs.append(active_run)
                overview.total_features += 1
                
                if health == "healthy":
                    overview.healthy_count += 1
                elif health == "blocked":
                    overview.blocked_count += 1
        
        recovery_adapter = RecoveryDataAdapter(project_path)
        recovery_item = recovery_adapter.get_recovery_item_with_observer()
        
        if recovery_item:
            if recovery_item.recovery_required:
                attention_item = AttentionItem(
                    category="recovery",
                    title=f"{project_id}: {recovery_item.feature_id}",
                    severity="high",
                    reason=recovery_item.recovery_reason[:50],
                    suggested_action=recovery_item.suggested_command or "asyncdev recovery list",
                    destination=f"asyncdev recovery show --execution {recovery_item.execution_id}",
                )
                all_attention_items.append(attention_item)
            
            for finding in recovery_item.observer_findings:
                if finding.severity in ["high", "critical"]:
                    highlight = ObserverHighlight(
                        finding_type=finding.finding_type,
                        severity=finding.severity,
                        summary=finding.reason[:60],
                        recommended_action=finding.suggested_action,
                        project_id=project_id,
                        destination=f"asyncdev observe-runs run --project {project_id}",
                    )
                    all_observer_highlights.append(highlight)
        
        if runstate and runstate.get("feature_id"):
            acceptance_adapter = AcceptanceRecoveryAdapter(project_path)
            acceptance_summary = acceptance_adapter.get_acceptance_recovery_summary(
                runstate.get("feature_id"),
                runstate,
            )
            
            if acceptance_summary:
                if acceptance_summary.is_blocking_completion or acceptance_summary.needs_reacceptance:
                    accept_item = AcceptanceQueueItem(
                        project_id=project_id,
                        feature_id=runstate.get("feature_id"),
                        acceptance_status=acceptance_summary.latest_status,
                        terminal_state=acceptance_summary.latest_terminal_state,
                        completion_blocked=acceptance_summary.is_blocking_completion,
                        attempt_count=acceptance_summary.attempt_count,
                        destination=f"asyncdev acceptance status --project {project_id}",
                    )
                    all_acceptance_items.append(accept_item)
                    
                    if acceptance_summary.is_blocking_completion:
                        blocked_item = AttentionItem(
                            category="acceptance_blocked",
                            title=f"{project_id}: acceptance blocked",
                            severity="high",
                            reason=f"Terminal state: {acceptance_summary.latest_terminal_state}",
                            suggested_action="asyncdev acceptance recovery --project " + project_id,
                            destination=f"asyncdev acceptance result --project {project_id}",
                        )
                        all_blocked_items.append(blocked_item)
    
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_attention_items.sort(key=lambda x: severity_order.get(x.severity, 99))
    all_observer_highlights.sort(key=lambda x: severity_order.get(x.severity, 99))
    all_blocked_items.sort(key=lambda x: severity_order.get(x.severity, 99))
    
    overview.attention_items = all_attention_items[:10]
    overview.acceptance_queue = all_acceptance_items[:10]
    overview.observer_highlights = all_observer_highlights[:5]
    overview.blocked_items = all_blocked_items[:10]
    
    overview.attention_count = len(all_attention_items)
    
    overview.quick_links = [
        QuickLink(
            label="Recovery Console",
            command="asyncdev recovery list",
            description="View executions needing recovery",
        ),
        QuickLink(
            label="Acceptance Status",
            command="asyncdev acceptance status --project {id}",
            description="Check acceptance validation state",
        ),
        QuickLink(
            label="Evidence Summary",
            command="asyncdev evidence summary --project {id}",
            description="View rolled-up project evidence",
        ),
        QuickLink(
            label="Observer Findings",
            command="asyncdev observe-runs run --project {id}",
            description="Run execution observation",
        ),
        QuickLink(
            label="Platform Questions",
            command="asyncdev evidence questions --project {id}",
            description="Answer canonical evidence questions",
        ),
    ]
    
    return overview


def get_operator_home_for_project(project_path: Path) -> OperatorHomeOverview:
    """Get operator home overview for single project."""
    projects_path = project_path.parent
    return build_operator_home_overview(projects_path)