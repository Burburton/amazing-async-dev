"""Workspace Snapshot - comprehensive workspace state view (Feature 028)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WorkspaceSnapshot:
    """Complete workspace state snapshot."""
    
    initialization_mode: str = "unknown"
    provider_linkage: dict[str, Any] = field(default_factory=dict)
    
    product_id: str = ""
    product_name: str = ""
    feature_id: str = ""
    current_phase: str = ""
    last_checkpoint: str = ""
    
    verification_status: str = "not_run"
    verification_artifact: str = ""
    
    review_status: str = "missing"
    review_artifact: str = ""
    
    pending_decisions: int = 0
    
    recommended_next_step: str = ""
    
    workspace_path: str = ""


def generate_workspace_snapshot(project_path: Path) -> WorkspaceSnapshot:
    """Generate a comprehensive workspace snapshot.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        WorkspaceSnapshot with all gathered state
    """
    snapshot = WorkspaceSnapshot()
    snapshot.workspace_path = str(project_path)
    
    if not project_path.exists():
        return snapshot
    
    _gather_initialization_mode(project_path, snapshot)
    _gather_execution_state(project_path, snapshot)
    _gather_verification_signal(project_path, snapshot)
    _gather_review_signal(project_path, snapshot)
    _gather_decision_signal(project_path, snapshot)
    _determine_next_step(snapshot)
    
    return snapshot


def _gather_initialization_mode(project_path: Path, snapshot: WorkspaceSnapshot) -> None:
    """Determine initialization mode from product-brief."""
    brief_path = project_path / "product-brief.yaml"
    
    if not brief_path.exists():
        snapshot.initialization_mode = "unknown"
        return
    
    with open(brief_path, encoding="utf-8") as f:
        brief = yaml.safe_load(f)
    
    if brief.get("starter_pack_context"):
        snapshot.initialization_mode = "starter-pack"
        snapshot.provider_linkage["detected"] = True
        
        context = brief.get("starter_pack_context", [])
        for item in context:
            if isinstance(item, str):
                if "Product type:" in item:
                    snapshot.provider_linkage["product_type"] = item.split(":")[1].strip()
                elif "Stage:" in item:
                    snapshot.provider_linkage["stage"] = item.split(":")[1].strip()
    else:
        snapshot.initialization_mode = "direct"
        snapshot.provider_linkage["detected"] = False
    
    snapshot.product_id = brief.get("product_id", "")
    snapshot.product_name = brief.get("name", "")


def _gather_execution_state(project_path: Path, snapshot: WorkspaceSnapshot) -> None:
    """Gather current execution state from runstate."""
    runstate_path = project_path / "runstate.md"
    
    if not runstate_path.exists():
        snapshot.current_phase = "none"
        return
    
    with open(runstate_path, encoding="utf-8") as f:
        content = f.read()
    
    yaml_block_start = content.find("```yaml")
    yaml_block_end = content.find("```", yaml_block_start + 7)
    
    if yaml_block_start == -1 or yaml_block_end == -1:
        snapshot.current_phase = "unknown"
        return
    
    yaml_content = content[yaml_block_start + 7:yaml_block_end].strip()
    runstate = yaml.safe_load(yaml_content)
    
    if runstate:
        snapshot.feature_id = runstate.get("feature_id", "")
        snapshot.current_phase = runstate.get("current_phase", "")
        snapshot.last_checkpoint = runstate.get("last_action", "")
        
        workflow_hints = runstate.get("workflow_hints", {})
        if workflow_hints:
            snapshot.provider_linkage["workflow_hints"] = workflow_hints


def _gather_verification_signal(project_path: Path, snapshot: WorkspaceSnapshot) -> None:
    """Check for verification artifacts."""
    results_dir = project_path / "execution-results"
    
    if not results_dir.exists():
        snapshot.verification_status = "not_run"
        return
    
    result_files = sorted(results_dir.glob("*.md"), reverse=True)
    
    if not result_files:
        snapshot.verification_status = "not_run"
        return
    
    latest_result = result_files[0]
    snapshot.verification_artifact = str(latest_result.relative_to(project_path))
    
    with open(latest_result, encoding="utf-8") as f:
        content = f.read()
    
    yaml_block_start = content.find("```yaml")
    yaml_block_end = content.find("```", yaml_block_start + 7)
    
    if yaml_block_start != -1 and yaml_block_end != -1:
        yaml_content = content[yaml_block_start + 7:yaml_block_end].strip()
        result_data = yaml.safe_load(yaml_content)
        
        if result_data:
            status = result_data.get("status", "unknown")
            snapshot.verification_status = status


def _gather_review_signal(project_path: Path, snapshot: WorkspaceSnapshot) -> None:
    """Check for review artifacts."""
    reviews_dir = project_path / "reviews"
    
    if not reviews_dir.exists():
        snapshot.review_status = "missing"
        return
    
    review_files = sorted(reviews_dir.glob("*.md"), reverse=True)
    
    if not review_files:
        snapshot.review_status = "missing"
        return
    
    latest_review = review_files[0]
    snapshot.review_artifact = str(latest_review.relative_to(project_path))
    snapshot.review_status = "present"


def _gather_decision_signal(project_path: Path, snapshot: WorkspaceSnapshot) -> None:
    """Check for pending async decisions."""
    runstate_path = project_path / "runstate.md"
    
    if not runstate_path.exists():
        return
    
    with open(runstate_path, encoding="utf-8") as f:
        content = f.read()
    
    yaml_block_start = content.find("```yaml")
    yaml_block_end = content.find("```", yaml_block_start + 7)
    
    if yaml_block_start == -1 or yaml_block_end == -1:
        return
    
    yaml_content = content[yaml_block_start + 7:yaml_block_end].strip()
    runstate = yaml.safe_load(yaml_content)
    
    if runstate:
        decisions = runstate.get("decisions_needed", [])
        snapshot.pending_decisions = len(decisions) if decisions else 0


def _determine_next_step(snapshot: WorkspaceSnapshot) -> None:
    """Determine recommended next action."""
    if snapshot.current_phase == "blocked":
        snapshot.recommended_next_step = "Resolve blockers before resuming execution."
    elif snapshot.pending_decisions > 0:
        snapshot.recommended_next_step = "Respond to pending decisions before resuming."
    elif snapshot.current_phase == "reviewing":
        snapshot.recommended_next_step = "Review latest artifacts and make decisions."
    elif snapshot.current_phase == "planning":
        snapshot.recommended_next_step = "Plan a bounded task for execution."
    elif snapshot.current_phase == "executing":
        snapshot.recommended_next_step = "Continue execution or wait for completion."
    elif snapshot.current_phase == "completed":
        snapshot.recommended_next_step = "Archive completed feature or start new feature."
    elif snapshot.verification_status == "not_run":
        snapshot.recommended_next_step = "Run verification to confirm setup."
    else:
        snapshot.recommended_next_step = "Check workspace state and continue workflow."


def format_snapshot_markdown(snapshot: WorkspaceSnapshot) -> str:
    """Format snapshot as human-readable markdown."""
    lines = [
        "# Workspace Snapshot",
        "",
        "## Initialization",
        f"- Mode: **{snapshot.initialization_mode}**",
    ]
    
    if snapshot.initialization_mode == "starter-pack" and snapshot.provider_linkage.get("detected"):
        lines.append(f"- Provider Context: {snapshot.provider_linkage.get('product_type', 'unknown')}")
        if snapshot.provider_linkage.get("workflow_hints"):
            hints = snapshot.provider_linkage["workflow_hints"]
            lines.append(f"- Policy Mode: {hints.get('policy_mode', 'unknown')}")
    
    lines.extend([
        "",
        "## Execution State",
        f"- Product: {snapshot.product_id or 'N/A'}",
        f"- Feature: {snapshot.feature_id or 'N/A'}",
        f"- Phase: **{snapshot.current_phase or 'N/A'}**",
        f"- Last Checkpoint: {snapshot.last_checkpoint or 'N/A'}",
        "",
        "## Signals",
        f"- Verification: {snapshot.verification_status}",
    ])
    
    if snapshot.verification_artifact:
        lines.append(f"  - Latest: {snapshot.verification_artifact}")
    
    lines.append(f"- Review: {snapshot.review_status}")
    
    if snapshot.review_artifact:
        lines.append(f"  - Latest: {snapshot.review_artifact}")
    
    lines.append(f"- Pending Decisions: {snapshot.pending_decisions}")
    
    lines.extend([
        "",
        "## Recommended Next Step",
        f"- {snapshot.recommended_next_step}",
        "",
        f"[dim]Workspace: {snapshot.workspace_path}[/dim]",
    ])
    
    return "\n".join(lines)