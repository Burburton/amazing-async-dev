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
    
    # Recovery playbook fields (Feature 030)
    likely_cause: str = ""
    what_to_check: list[str] = field(default_factory=list)
    recovery_steps: list[str] = field(default_factory=list)
    fallback_next_step: str = ""
    
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
    _apply_recovery_playbooks(diagnosis, snapshot)
    
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


def _apply_recovery_playbooks(diagnosis: DoctorDiagnosis, snapshot) -> None:
    """Apply recovery playbooks for problematic scenarios."""
    
    if diagnosis.pending_decisions > 0:
        diagnosis.likely_cause = "Workflow cannot safely continue until human decision is resolved."
        diagnosis.what_to_check = [
            "decision request details",
            "blocking phase context",
            "latest review artifacts"
        ]
        diagnosis.recovery_steps = [
            "Inspect pending decision request",
            "Confirm required human input",
            "Resolve decision or resume with explicit command"
        ]
        diagnosis.fallback_next_step = "Review latest nightly pack or unblock instructions"
        return
    
    if diagnosis.current_phase == "blocked":
        diagnosis.likely_cause = "Execution explicitly blocked by external dependency or condition."
        diagnosis.what_to_check = [
            "blocked_items in runstate",
            "external blocker details",
            "last checkpoint before block"
        ]
        diagnosis.recovery_steps = [
            "Inspect blocked items list",
            "Resolve external blocker",
            "Run unblock command"
        ]
        diagnosis.fallback_next_step = "Check execution results for blocker details"
        return
    
    if diagnosis.doctor_status == "ATTENTION_NEEDED" and diagnosis.verification_status == "not_run":
        diagnosis.likely_cause = "Initialization or integration state has not been validated."
        diagnosis.what_to_check = [
            "verification documentation",
            f"{diagnosis.initialization_mode} initialization mode",
            "required workspace artifacts"
        ]
        diagnosis.recovery_steps = [
            "Run verification check",
            "Inspect result summary",
            "Continue only if verification passes"
        ]
        diagnosis.fallback_next_step = "Inspect workspace snapshot and initialization inputs"
        return
    
    if diagnosis.doctor_status == "ATTENTION_NEEDED" and diagnosis.verification_status == "failed":
        diagnosis.likely_cause = "Contract mismatch, missing artifact, invalid initialization, or configuration drift."
        diagnosis.what_to_check = [
            "latest verification output",
            "starter-pack compatibility (if applicable)",
            "required workspace files"
        ]
        diagnosis.recovery_steps = [
            "Inspect verification failure details",
            "Correct mismatch or missing inputs",
            "Rerun verification"
        ]
        diagnosis.fallback_next_step = "Compare current workspace state with expected example or docs"
        return
    
    if diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT":
        diagnosis.likely_cause = "Execution is done but closure artifacts are incomplete."
        diagnosis.what_to_check = [
            "completion marker presence",
            "archive directory existence",
            "final review artifacts"
        ]
        diagnosis.recovery_steps = [
            "Confirm feature is actually complete",
            "Create archive or closeout artifact",
            "Verify workspace returns to healthy state"
        ]
        diagnosis.fallback_next_step = "Inspect review and completion command docs"
        return
    
    if diagnosis.doctor_status == "UNKNOWN":
        diagnosis.likely_cause = "Required state files or runtime signals are missing or cannot be interpreted."
        diagnosis.what_to_check = [
            "runstate.md existence and format",
            "workspace metadata",
            "expected artifact presence"
        ]
        diagnosis.recovery_steps = [
            "Inspect missing or incomplete state",
            "Restore or recreate minimum required state",
            "Rerun doctor and status checks"
        ]
        diagnosis.fallback_next_step = "Use examples/docs to compare expected structure"


def format_diagnosis_markdown(diagnosis: DoctorDiagnosis) -> str:
    """Format diagnosis as human-readable markdown."""
    lines = [
        f"# Workspace Health: {diagnosis.doctor_status}",
        "",
        f"**Initialization**: {diagnosis.initialization_mode}",
    ]
    
    if diagnosis.initialization_mode == "starter-pack" and diagnosis.provider_linkage.get("detected"):
        if diagnosis.provider_linkage.get("product_type"):
            lines.append(f"  Provider Context: {diagnosis.provider_linkage.get('product_type')}")
        hints = diagnosis.provider_linkage.get("workflow_hints", {})
        if hints.get("policy_mode"):
            lines.append(f"  Policy Mode: {hints.get('policy_mode')}")
    
    lines.extend([
        "",
        "## Execution State",
        f"- Product: {diagnosis.product_id or 'N/A'}",
        f"- Feature: {diagnosis.feature_id or 'N/A'}",
        f"- Phase: **{diagnosis.current_phase or 'N/A'}**",
        "",
        "## Signals",
        f"- Verification: {diagnosis.verification_status}",
        f"- Pending Decisions: {diagnosis.pending_decisions}",
        f"- Blocked Items: {diagnosis.blocked_items_count}",
        "",
        "## Recommended Action",
        f"{diagnosis.recommended_action}",
        "",
        "## Suggested Command",
        f"`{diagnosis.suggested_command}`",
        "",
        "## Why",
        f"{diagnosis.rationale}",
    ])
    
    if diagnosis.warnings:
        lines.extend(["", "## Warnings"])
        for warning in diagnosis.warnings:
            lines.append(f"- {warning}")
    
    if diagnosis.likely_cause:
        lines.extend([
            "",
            "## Recovery Hints",
            "",
            f"**Likely Cause**: {diagnosis.likely_cause}",
            "",
            "**What To Check**:",
        ])
        for item in diagnosis.what_to_check:
            lines.append(f"- {item}")
        
        lines.extend(["", "**Recovery Steps**:"])
        for i, step in enumerate(diagnosis.recovery_steps, 1):
            lines.append(f"{i}. {step}")
        
        if diagnosis.fallback_next_step:
            lines.extend([
                "",
                f"**If This Fails, Try Next**: {diagnosis.fallback_next_step}"
            ])
    
    lines.extend(["", f"[dim]Workspace: {diagnosis.workspace_path}[/dim]"])
    
    return "\n".join(lines)


def format_diagnosis_yaml(diagnosis: DoctorDiagnosis) -> str:
    """Format diagnosis as YAML for machine consumption."""
    data = {
        "doctor_status": diagnosis.doctor_status,
        "health_status": diagnosis.health_status,
        "initialization_mode": diagnosis.initialization_mode,
        "provider_linkage": diagnosis.provider_linkage,
        "execution_state": {
            "product_id": diagnosis.product_id,
            "feature_id": diagnosis.feature_id,
            "current_phase": diagnosis.current_phase,
        },
        "signals": {
            "verification_status": diagnosis.verification_status,
            "pending_decisions": diagnosis.pending_decisions,
            "blocked_items_count": diagnosis.blocked_items_count,
        },
        "recommended_action": diagnosis.recommended_action,
        "suggested_command": diagnosis.suggested_command,
        "rationale": diagnosis.rationale,
        "warnings": diagnosis.warnings,
        "workspace_path": diagnosis.workspace_path,
    }
    
    if diagnosis.likely_cause:
        data["likely_cause"] = diagnosis.likely_cause
        data["what_to_check"] = diagnosis.what_to_check
        data["recovery_steps"] = diagnosis.recovery_steps
        data["fallback_next_step"] = diagnosis.fallback_next_step
    
    return yaml.dump(data, default_flow_style=False, sort_keys=False)