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
    
    _apply_rules(diagnosis, snapshot)
    
    return diagnosis


def _apply_rules(diagnosis: DoctorDiagnosis, snapshot) -> None:
    """Apply recommendation rules to classify health."""
    
    if not snapshot.product_id or snapshot.current_phase in ["unknown", "none", ""]:
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "Insufficient workspace metadata."
        return
    
    diagnosis.doctor_status = "HEALTHY"
    diagnosis.health_status = "healthy"
    diagnosis.recommended_action = "Check workspace state."
    diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
    diagnosis.rationale = "Workspace has sufficient metadata."