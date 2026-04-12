"""Workspace Doctor - health diagnosis and next-action recommendations (Feature 029)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DoctorDiagnosis:
    """Workspace diagnosis result."""
    
    doctor_status: str = "UNKNOWN"
    health_status: str = "unknown"
    
    initialization_mode: str = "unknown"
    provider_linkage: dict[str, Any] = field(default_factory=dict)
    
    product_id: str = ""
    feature_id: str = ""
    current_phase: str = ""
    
    verification_status: str = "not_run"
    pending_decisions: int = 0
    blocked_items_count: int = 0
    
    recommended_action: str = ""
    suggested_command: str = ""
    rationale: str = ""
    warnings: list[str] = field(default_factory=list)
    
    workspace_path: str = ""


def diagnose_workspace(project_path: Path) -> DoctorDiagnosis:
    """Generate workspace diagnosis with health classification."""
    diagnosis = DoctorDiagnosis()
    diagnosis.workspace_path = str(project_path)
    
    if not project_path.exists():
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "Project directory does not exist."
        return diagnosis
    
    from runtime.workspace_snapshot import generate_workspace_snapshot
    
    snapshot = generate_workspace_snapshot(project_path)
    
    diagnosis.initialization_mode = snapshot.initialization_mode
    diagnosis.provider_linkage = snapshot.provider_linkage
    diagnosis.product_id = snapshot.product_id
    diagnosis.feature_id = snapshot.feature_id
    diagnosis.current_phase = snapshot.current_phase
    diagnosis.verification_status = snapshot.verification_status
    diagnosis.pending_decisions = snapshot.pending_decisions
    
    runstate = _load_runstate(project_path)
    blocked_items = runstate.get("blocked_items", [])
    diagnosis.blocked_items_count = len(blocked_items) if blocked_items else 0
    
    _apply_rules(diagnosis, snapshot)
    
    return diagnosis


def _load_runstate(project_path: Path) -> dict:
    """Load runstate data from runstate.md."""
    runstate_path = project_path / "runstate.md"
    
    if not runstate_path.exists():
        return {}
    
    with open(runstate_path, encoding="utf-8") as f:
        content = f.read()
    
    yaml_block_start = content.find("```yaml")
    yaml_block_end = content.find("```", yaml_block_start + 7)
    
    if yaml_block_start == -1 or yaml_block_end == -1:
        return {}
    
    yaml_content = content[yaml_block_start + 7:yaml_block_end].strip()
    return yaml.safe_load(yaml_content) or {}


def _apply_rules(diagnosis: DoctorDiagnosis, snapshot) -> None:
    """Apply recommendation rules in priority order."""
    
    if not snapshot.product_id or snapshot.current_phase in ["unknown", "none", ""]:
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "Insufficient workspace metadata."
        return
    
    if snapshot.pending_decisions > 0:
        diagnosis.doctor_status = "BLOCKED"
        diagnosis.health_status = "blocked"
        diagnosis.recommended_action = "Respond to pending decisions before resuming."
        diagnosis.suggested_command = f"asyncdev resume-next-day continue-loop --project {snapshot.product_id}"
        diagnosis.rationale = f"Human decision required ({snapshot.pending_decisions} pending)."
        diagnosis.warnings = ["Do not continue until decisions are resolved."]
        return
    
    if snapshot.current_phase == "blocked":
        diagnosis.doctor_status = "BLOCKED"
        diagnosis.health_status = "blocked"
        diagnosis.recommended_action = "Resolve blockers before resuming execution."
        diagnosis.suggested_command = f"asyncdev resume-next-day unblock --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is explicitly blocked."
        diagnosis.warnings = ["Do not continue until blockers are resolved."]
        return
    
    if snapshot.verification_status == "failed":
        diagnosis.doctor_status = "ATTENTION_NEEDED"
        diagnosis.health_status = "warning"
        diagnosis.recommended_action = "Re-check initialization or re-run verification."
        
        if snapshot.initialization_mode == "starter-pack":
            diagnosis.suggested_command = "Check starter-pack.yaml for contract_version and asyncdev_compatibility"
            diagnosis.rationale = "Starter-pack initialization verification failed. Check provider/input compatibility."
            diagnosis.warnings = ["Do not proceed until verification succeeds."]
        else:
            diagnosis.suggested_command = f"asyncdev new-product create --project {snapshot.product_id} --name 'Retry'"
            diagnosis.rationale = "Direct mode initialization verification failed. Check manual setup."
            diagnosis.warnings = ["Do not proceed until verification succeeds."]
        return
    
    if snapshot.current_phase == "completed":
        diagnosis.doctor_status = "COMPLETED_PENDING_CLOSEOUT"
        diagnosis.health_status = "healthy"
        diagnosis.recommended_action = "Archive completed feature."
        diagnosis.suggested_command = f"asyncdev archive-feature create --project {snapshot.product_id} --feature {snapshot.feature_id}"
        diagnosis.rationale = "Feature work complete but not archived."
        return
    
    if snapshot.current_phase == "archived":
        diagnosis.doctor_status = "COMPLETED_PENDING_CLOSEOUT"
        diagnosis.health_status = "healthy"
        diagnosis.recommended_action = "Start a new feature."
        diagnosis.suggested_command = f"asyncdev new-feature create --project {snapshot.product_id} --feature feature-new --name 'New Feature'"
        diagnosis.rationale = "Previous feature archived. Ready to start new work."
        return
    
    if not snapshot.feature_id:
        diagnosis.doctor_status = "ATTENTION_NEEDED"
        diagnosis.health_status = "warning"
        diagnosis.recommended_action = "Create or select a feature."
        diagnosis.suggested_command = f"asyncdev new-feature create --project {snapshot.product_id} --feature feature-001 --name 'First Feature'"
        diagnosis.rationale = "Product exists but no active feature selected."
        return
    
    diagnosis.doctor_status = "HEALTHY"
    diagnosis.health_status = "healthy"
    
    if snapshot.current_phase == "planning":
        diagnosis.recommended_action = "Plan a bounded task for execution."
        diagnosis.suggested_command = f"asyncdev plan-day create --project {snapshot.product_id} --feature {snapshot.feature_id} --task 'Your task'"
        diagnosis.rationale = "Workspace is in planning phase. Create an ExecutionPack."
    elif snapshot.current_phase == "executing":
        diagnosis.recommended_action = "Continue execution or wait for completion."
        diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
        diagnosis.rationale = "Feature is executing, no blockers."
    elif snapshot.current_phase == "reviewing":
        diagnosis.recommended_action = "Review latest artifacts and make decisions."
        diagnosis.suggested_command = f"asyncdev review-night show --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is in reviewing phase."
    else:
        diagnosis.recommended_action = "Check workspace state."
        diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is healthy."