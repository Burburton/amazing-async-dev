"""Evidence Rollup - Feature 079.

Canonical evidence summary layer that rolls up project/feature artifacts
into a unified view for operators and platform components.

Per 079 Section 6:
- Consolidates execution, acceptance, observer, recovery evidence
- Provides latest-truth resolution
- Serves both human and machine consumers
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.state_store import StateStore
from runtime.recovery_classifier import classify_recovery, RecoveryClassification
from runtime.acceptance_runner import load_acceptance_result
from runtime.acceptance_pack_builder import load_acceptance_pack
from runtime.acceptance_recovery_adapter import AcceptanceRecoveryAdapter
from runtime.recovery_data_adapter import RecoveryDataAdapter


@dataclass
class FeatureEvidenceSummary:
    """Rolled-up evidence summary for a single feature (079 Section 7.3)."""
    
    feature_id: str
    feature_title: str = ""
    
    latest_execution_result_ref: str = ""
    latest_execution_status: str = ""
    latest_execution_pack_ref: str = ""
    
    latest_acceptance_result_ref: str = ""
    latest_acceptance_status: str = ""
    acceptance_terminal_state: str = ""
    acceptance_attempt_count: int = 0
    
    recovery_required: bool = False
    recovery_classification: str = ""
    latest_recovery_pack_ref: str = ""
    
    observer_findings_count: int = 0
    observer_high_severity_count: int = 0
    
    completion_blocked: bool = False
    completion_blocked_reason: str = ""
    
    evidence_directory: str = ""
    linked_artifacts: list[str] = field(default_factory=list)
    
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "feature_title": self.feature_title,
            "latest_execution_result_ref": self.latest_execution_result_ref,
            "latest_execution_status": self.latest_execution_status,
            "latest_execution_pack_ref": self.latest_execution_pack_ref,
            "latest_acceptance_result_ref": self.latest_acceptance_result_ref,
            "latest_acceptance_status": self.latest_acceptance_status,
            "acceptance_terminal_state": self.acceptance_terminal_state,
            "acceptance_attempt_count": self.acceptance_attempt_count,
            "recovery_required": self.recovery_required,
            "recovery_classification": self.recovery_classification,
            "latest_recovery_pack_ref": self.latest_recovery_pack_ref,
            "observer_findings_count": self.observer_findings_count,
            "observer_high_severity_count": self.observer_high_severity_count,
            "completion_blocked": self.completion_blocked,
            "completion_blocked_reason": self.completion_blocked_reason,
            "evidence_directory": self.evidence_directory,
            "linked_artifacts": self.linked_artifacts,
            "updated_at": self.updated_at,
        }
    
    def is_healthy(self) -> bool:
        return (
            not self.recovery_required
            and not self.completion_blocked
            and self.latest_execution_status in ["success", "partial"]
        )
    
    def needs_attention(self) -> bool:
        return self.recovery_required or self.completion_blocked or self.observer_high_severity_count > 0


@dataclass
class ProjectEvidenceSummary:
    """Rolled-up evidence summary for entire project (079 Section 7.2)."""
    
    project_id: str
    project_name: str = ""
    current_phase: str = ""
    
    features: list[FeatureEvidenceSummary] = field(default_factory=list)
    
    total_features: int = 0
    healthy_features: int = 0
    blocked_features: int = 0
    recovery_pending_features: int = 0
    
    latest_execution_result_ref: str = ""
    latest_acceptance_result_ref: str = ""
    latest_observer_run: str = ""
    
    any_blocking: bool = False
    blocking_summary: str = ""
    
    recommended_next_action: str = ""
    
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "current_phase": self.current_phase,
            "features": [f.to_dict() for f in self.features],
            "total_features": self.total_features,
            "healthy_features": self.healthy_features,
            "blocked_features": self.blocked_features,
            "recovery_pending_features": self.recovery_pending_features,
            "latest_execution_result_ref": self.latest_execution_result_ref,
            "latest_acceptance_result_ref": self.latest_acceptance_result_ref,
            "latest_observer_run": self.latest_observer_run,
            "any_blocking": self.any_blocking,
            "blocking_summary": self.blocking_summary,
            "recommended_next_action": self.recommended_next_action,
            "updated_at": self.updated_at,
        }


class LatestTruthResolver:
    """Canonical latest-truth resolution (079 Section 6.2).
    
    Consolidates the scattered resolution patterns from:
    - workspace_snapshot.py (mtime sorting)
    - recovery_data_adapter.py (glob + last index)
    - acceptance_runner.py (mtime + feature_id filter)
    - summary.py (list[-1])
    
    Enhanced with pointer file support (C-006):
    - Checks pointer files first for faster resolution
    - Falls back to glob + mtime if pointer missing
    """
    
    def __init__(self, project_path: Path, use_pointer: bool = True):
        self.project_path = project_path
        self.use_pointer = use_pointer
    
    def get_latest_execution_result(self) -> tuple[str, Path | None]:
        """Get latest execution result ID and path.
        
        Uses pointer file if available (C-006), falls back to glob + mtime.
        """
        if self.use_pointer:
            from runtime.latest_pointer_manager import read_latest_pointer
            target_id, target_path = read_latest_pointer(self.project_path, "execution_result")
            if target_id and target_path:
                return target_id, target_path
        
        results_dir = self.project_path / "execution-results"
        if not results_dir.exists():
            return "", None
        
        results = sorted(
            results_dir.glob("*.md"),
            key=lambda r: r.stat().st_mtime,
            reverse=True,
        )
        
        if not results:
            return "", None
        
        latest = results[0]
        return latest.stem, latest
    
    def get_latest_execution_pack(self) -> tuple[str, Path | None]:
        """Get latest execution pack ID and path.
        
        Uses pointer file if available (C-006), falls back to glob + mtime.
        """
        if self.use_pointer:
            from runtime.latest_pointer_manager import read_latest_pointer
            target_id, target_path = read_latest_pointer(self.project_path, "execution_pack")
            if target_id and target_path:
                return target_id, target_path
        
        packs_dir = self.project_path / "execution-packs"
        if not packs_dir.exists():
            return "", None
        
        packs = sorted(
            packs_dir.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        
        if not packs:
            return "", None
        
        latest = packs[0]
        return latest.stem, latest
    
    def get_latest_acceptance_result(self, feature_id: str | None = None) -> tuple[str, Path | None]:
        """Get latest acceptance result ID and path.
        
        Uses pointer file if available (C-006), falls back to glob + mtime.
        Note: Pointer doesn't filter by feature_id; fallback scan does.
        """
        if self.use_pointer and feature_id is None:
            from runtime.latest_pointer_manager import read_latest_pointer
            target_id, target_path = read_latest_pointer(self.project_path, "acceptance_result")
            if target_id and target_path:
                return target_id, target_path
        
        results_dir = self.project_path / "acceptance-results"
        if not results_dir.exists():
            return "", None
        
        results = sorted(
            results_dir.glob("*.md"),
            key=lambda r: r.stat().st_mtime,
            reverse=True,
        )
        
        for result_path in results:
            result_id = result_path.stem
            result = load_acceptance_result(self.project_path, result_id)
            if result:
                pack = load_acceptance_pack(self.project_path, result.acceptance_pack_id)
                if pack:
                    if feature_id is None or pack.feature_id == feature_id:
                        return result_id, result_path
        
        return "", None
    
    def get_latest_recovery_pack(self) -> tuple[str, Path | None]:
        """Get latest acceptance recovery pack ID and path.
        
        Uses pointer file if available (C-006), falls back to glob + mtime.
        """
        if self.use_pointer:
            from runtime.latest_pointer_manager import read_latest_pointer
            target_id, target_path = read_latest_pointer(self.project_path, "acceptance_recovery_pack")
            if target_id and target_path:
                return target_id, target_path
        
        packs_dir = self.project_path / "acceptance-recovery"
        if not packs_dir.exists():
            return "", None
        
        packs = sorted(
            packs_dir.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        
        if not packs:
            return "", None
        
        latest = packs[0]
        return latest.stem, latest
    
    def get_latest_observer_findings(self) -> tuple[str, Path | None]:
        """Get latest observer findings ID and path.
        
        Uses pointer file if available (C-006), falls back to glob + mtime.
        """
        if self.use_pointer:
            from runtime.latest_pointer_manager import read_latest_pointer
            target_id, target_path = read_latest_pointer(self.project_path, "observer_findings")
            if target_id and target_path:
                return target_id, target_path
        
        findings_dir = self.project_path / "observer-findings"
        if not findings_dir.exists():
            return "", None
        
        findings = sorted(
            findings_dir.glob("*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        
        if not findings:
            return "", None
        
        latest = findings[0]
        return latest.stem, latest
    
    def get_latest_artifact(self, artifact_type: str) -> tuple[str, Path | None]:
        """Generic latest artifact resolver by type.
        
        Uses pointer file if available (C-006), falls back to glob + mtime.
        """
        if self.use_pointer:
            from runtime.latest_pointer_manager import read_latest_pointer, POINTER_FILES
            
            if artifact_type in POINTER_FILES:
                target_id, target_path = read_latest_pointer(self.project_path, artifact_type)
                if target_id and target_path:
                    return target_id, target_path
        
        type_to_dir = {
            "execution_result": "execution-results",
            "execution_pack": "execution-packs",
            "acceptance_result": "acceptance-results",
            "acceptance_pack": "acceptance-packs",
            "acceptance_recovery_pack": "acceptance-recovery",
            "observer_findings": "observer-findings",
            "daily_review": "reviews",
        }
        
        dir_name = type_to_dir.get(artifact_type)
        if not dir_name:
            return "", None
        
        artifact_dir = self.project_path / dir_name
        if not artifact_dir.exists():
            return "", None
        
        artifacts = sorted(
            artifact_dir.glob("*.md"),
            key=lambda a: a.stat().st_mtime,
            reverse=True,
        )
        
        if not artifacts:
            return "", None
        
        latest = artifacts[0]
        return latest.stem, latest


def build_feature_evidence_summary(
    project_path: Path,
    feature_id: str,
    runstate: dict[str, Any] | None = None,
) -> FeatureEvidenceSummary:
    """Build evidence summary for a single feature."""
    
    resolver = LatestTruthResolver(project_path)
    store = StateStore(project_path)
    
    if runstate is None:
        runstate = store.load_runstate()
    
    summary = FeatureEvidenceSummary(feature_id=feature_id)
    
    exec_result_id, exec_result_path = resolver.get_latest_execution_result()
    summary.latest_execution_result_ref = exec_result_id
    
    if exec_result_path:
        result = store.load_execution_result(exec_result_id)
        if result:
            summary.latest_execution_status = result.get("status", "")
    
    exec_pack_id, _ = resolver.get_latest_execution_pack()
    summary.latest_execution_pack_ref = exec_pack_id
    
    accept_result_id, accept_result_path = resolver.get_latest_acceptance_result(feature_id)
    summary.latest_acceptance_result_ref = accept_result_id
    
    if accept_result_id:
        acceptance_result = load_acceptance_result(project_path, accept_result_id)
        if acceptance_result:
            summary.latest_acceptance_status = acceptance_result.terminal_state.value
            summary.acceptance_terminal_state = acceptance_result.terminal_state.value
    
    recovery_adapter = AcceptanceRecoveryAdapter(project_path)
    acceptance_recovery_summary = recovery_adapter.get_acceptance_recovery_summary(feature_id, runstate)
    
    if acceptance_recovery_summary:
        summary.acceptance_attempt_count = acceptance_recovery_summary.attempt_count
        summary.latest_recovery_pack_ref = acceptance_recovery_summary.acceptance_recovery_pack_id
    
    recovery_data_adapter = RecoveryDataAdapter(project_path)
    recovery_item = recovery_data_adapter.get_recovery_item()
    
    if recovery_item:
        summary.recovery_required = recovery_item.recovery_required
        summary.recovery_classification = recovery_item.status
        summary.observer_findings_count = len(recovery_item.observer_findings)
        summary.observer_high_severity_count = sum(
            1 for f in recovery_item.observer_findings if f.severity == "high"
        )
        summary.completion_blocked = acceptance_recovery_summary.is_blocking_completion if acceptance_recovery_summary else False
        summary.completion_blocked_reason = (
            "Acceptance rejected" if summary.acceptance_terminal_state == "rejected"
            else "Recovery required" if summary.recovery_required
            else ""
        )
    
    summary.evidence_directory = f"projects/{project_path.name}"
    summary.linked_artifacts = [
        f"execution-results/{exec_result_id}.md" if exec_result_id else "",
        f"acceptance-results/{accept_result_id}.md" if accept_result_id else "",
    ]
    summary.linked_artifacts = [a for a in summary.linked_artifacts if a]
    
    return summary


def build_project_evidence_summary(project_path: Path) -> ProjectEvidenceSummary:
    """Build evidence summary for entire project."""
    
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    project_id = project_path.name
    summary = ProjectEvidenceSummary(project_id=project_id)
    
    if runstate:
        summary.current_phase = runstate.get("current_phase", "")
        feature_id = runstate.get("feature_id", "")
        
        if feature_id:
            feature_summary = build_feature_evidence_summary(project_path, feature_id, runstate)
            summary.features = [feature_summary]
    
    resolver = LatestTruthResolver(project_path)
    
    latest_exec_id, _ = resolver.get_latest_execution_result()
    summary.latest_execution_result_ref = latest_exec_id
    
    latest_accept_id, _ = resolver.get_latest_acceptance_result()
    summary.latest_acceptance_result_ref = latest_accept_id
    
    summary.total_features = len(summary.features)
    summary.healthy_features = sum(1 for f in summary.features if f.is_healthy())
    summary.blocked_features = sum(1 for f in summary.features if f.completion_blocked)
    summary.recovery_pending_features = sum(1 for f in summary.features if f.recovery_required)
    
    summary.any_blocking = summary.blocked_features > 0 or summary.recovery_pending_features > 0
    
    if summary.any_blocking:
        blocked_reasons = []
        for f in summary.features:
            if f.completion_blocked:
                blocked_reasons.append(f"{f.feature_id}: {f.completion_blocked_reason}")
        summary.blocking_summary = "; ".join(blocked_reasons[:3])
    
    if summary.any_blocking:
        summary.recommended_next_action = "asyncdev recovery list"
    elif summary.healthy_features == summary.total_features and summary.total_features > 0:
        summary.recommended_next_action = "asyncdev complete-feature mark"
    else:
        summary.recommended_next_action = "asyncdev plan-day create"
    
    return summary


def save_feature_evidence_summary(project_path: Path, summary: FeatureEvidenceSummary) -> Path:
    """Save feature evidence summary to file."""
    from runtime.artifact_router import get_evidence_summary_path
    
    output_path = get_evidence_summary_path(project_path, summary.feature_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"# Feature Evidence Summary\n\n```yaml\n"
    for key, value in summary.to_dict().items():
        if isinstance(value, list):
            content += f"{key}:\n"
            for item in value:
                content += f"  - {item}\n"
        else:
            content += f"{key}: {value}\n"
    content += "```\n"
    
    output_path.write_text(content, encoding="utf-8")
    return output_path


def save_project_evidence_summary(project_path: Path, summary: ProjectEvidenceSummary) -> Path:
    """Save project evidence summary to file."""
    from runtime.artifact_router import get_evidence_summary_path
    
    output_path = get_evidence_summary_path(project_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"# Project Evidence Summary\n\n```yaml\n"
    for key, value in summary.to_dict().items():
        if key == "features":
            content += "features:\n"
            for f in value:
                content += f"  - feature_id: {f['feature_id']}\n"
                content += f"    status: {f['latest_execution_status']}\n"
                content += f"    acceptance: {f['acceptance_terminal_state']}\n"
                content += f"    blocked: {f['completion_blocked']}\n"
        elif isinstance(value, list):
            content += f"{key}:\n"
            for item in value:
                content += f"  - {item}\n"
        else:
            content += f"{key}: {value}\n"
    content += "```\n"
    
    output_path.write_text(content, encoding="utf-8")
    return output_path


def load_feature_evidence_summary(project_path: Path, feature_id: str) -> FeatureEvidenceSummary | None:
    """Load feature evidence summary from file."""
    from runtime.artifact_router import get_evidence_summary_path
    import yaml
    
    summary_path = get_evidence_summary_path(project_path, feature_id)
    if not summary_path.exists():
        return None
    
    content = summary_path.read_text(encoding="utf-8")
    yaml_start = content.find("```yaml")
    yaml_end = content.find("```", yaml_start + 7)
    
    if yaml_start == -1 or yaml_end == -1:
        return None
    
    yaml_content = content[yaml_start + 7:yaml_end]
    data = yaml.safe_load(yaml_content)
    
    return FeatureEvidenceSummary(**data)


def get_evidence_summary_for_project(project_path: Path) -> ProjectEvidenceSummary:
    """Get or build project evidence summary."""
    return build_project_evidence_summary(project_path)