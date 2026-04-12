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