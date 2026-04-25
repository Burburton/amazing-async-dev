"""Acceptance Pack Builder - Feature 071.

Builds AcceptancePack from ExecutionResult and FeatureSpec.
AcceptancePack is the input package for independent validator.

Integration with:
- Feature 069 (AcceptancePack schema)
- Feature 070 (AcceptanceReadiness)
- Feature 061 (ExecutionResult closeout)
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.state_store import StateStore
from runtime.validator_types import ValidatorType


@dataclass
class VerificationSummary:
    """Summary of verification layer results."""
    
    orchestration_terminal_state: str
    browser_verification_executed: bool = False
    browser_verification_passed: int = 0
    browser_verification_failed: int = 0
    closeout_terminal_state: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "orchestration_terminal_state": self.orchestration_terminal_state,
            "browser_verification_executed": self.browser_verification_executed,
            "browser_verification_passed": self.browser_verification_passed,
            "browser_verification_failed": self.browser_verification_failed,
            "closeout_terminal_state": self.closeout_terminal_state,
        }


@dataclass
class ImplementationSummary:
    """Summary of what was implemented."""
    
    completed_items: list[str] = field(default_factory=list)
    artifacts_created: list[dict[str, str]] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    key_changes: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "completed_items": self.completed_items,
            "artifacts_created": self.artifacts_created,
            "files_modified": self.files_modified,
            "key_changes": self.key_changes,
        }


@dataclass
class AcceptancePack:
    """AcceptancePack artifact (Feature 069/071).
    
    Input package for independent validator.
    Contains all context needed to validate against acceptance criteria.
    """
    
    acceptance_pack_id: str
    feature_id: str
    execution_result_id: str
    product_id: str
    
    acceptance_criteria: list[dict[str, Any]] = field(default_factory=list)
    implementation_summary: ImplementationSummary = field(default_factory=lambda: ImplementationSummary())
    evidence_artifacts: list[str] = field(default_factory=list)
    verification_summary: VerificationSummary = field(default_factory=lambda: VerificationSummary(orchestration_terminal_state="not_required"))
    
    trigger_reason: str = "execution_result_complete"
    triggered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    triggered_by: str = "observer_auto_trigger"
    
    intended_validator_type: ValidatorType = ValidatorType.AI_SESSION
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "acceptance_pack_id": self.acceptance_pack_id,
            "feature_id": self.feature_id,
            "execution_result_id": self.execution_result_id,
            "product_id": self.product_id,
            "acceptance_criteria": self.acceptance_criteria,
            "implementation_summary": self.implementation_summary.to_dict(),
            "evidence_artifacts": self.evidence_artifacts,
            "verification_summary": self.verification_summary.to_dict(),
            "trigger_reason": self.trigger_reason,
            "triggered_at": self.triggered_at,
            "triggered_by": self.triggered_by,
            "intended_validator_type": self.intended_validator_type.value,
        }
    
    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)


def generate_acceptance_pack_id(date_str: str | None = None) -> str:
    """Generate acceptance pack ID in format ap-YYYYMMDD-###."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    
    return f"ap-{date_str}-001"


def extract_verification_summary(execution_result: dict[str, Any]) -> VerificationSummary:
    """Extract verification summary from ExecutionResult."""
    orchestration_state = execution_result.get("orchestration_terminal_state", "not_required")
    browser_verification = execution_result.get("browser_verification", {})
    
    return VerificationSummary(
        orchestration_terminal_state=orchestration_state,
        browser_verification_executed=browser_verification.get("executed", False),
        browser_verification_passed=browser_verification.get("passed", 0),
        browser_verification_failed=browser_verification.get("failed", 0),
        closeout_terminal_state=execution_result.get("closeout_terminal_state", ""),
    )


def extract_implementation_summary(execution_result: dict[str, Any]) -> ImplementationSummary:
    """Extract implementation summary from ExecutionResult."""
    completed_items = execution_result.get("completed_items", [])
    artifacts_created = execution_result.get("artifacts_created", [])
    files_modified = execution_result.get("files_modified", [])
    
    key_changes = ""
    notes = execution_result.get("notes", "")
    if notes:
        key_changes = notes[:500] if len(notes) > 500 else notes
    
    return ImplementationSummary(
        completed_items=completed_items,
        artifacts_created=artifacts_created,
        files_modified=files_modified,
        key_changes=key_changes,
    )


def build_acceptance_pack(
    project_path: Path,
    execution_result_id: str,
    trigger_reason: str = "execution_result_complete",
) -> AcceptancePack | None:
    """Build AcceptancePack from ExecutionResult and FeatureSpec (Feature 071 AC-001).
    
    Args:
        project_path: Path to project
        execution_result_id: ID of ExecutionResult to validate
        trigger_reason: Reason for triggering acceptance
    
    Returns:
        AcceptancePack if successful, None if prerequisites not met
    """
    store = StateStore(project_path)
    
    execution_result = store.load_execution_result(execution_result_id)
    if execution_result is None:
        return None
    
    runstate = store.load_runstate() or {}
    feature_id = runstate.get("feature_id", "")
    product_id = runstate.get("project_id", project_path.name)
    
    feature_spec_path = project_path / "features" / feature_id / "feature-spec.yaml"
    feature_spec = None
    if feature_spec_path.exists():
        with open(feature_spec_path, encoding="utf-8") as f:
            feature_spec = yaml.safe_load(f)
    
    if feature_spec is None:
        return None
    
    acceptance_criteria = feature_spec.get("acceptance_criteria", [])
    if not acceptance_criteria:
        return None
    
    verification_summary = extract_verification_summary(execution_result)
    implementation_summary = extract_implementation_summary(execution_result)
    
    evidence_artifacts = []
    for artifact in execution_result.get("artifacts_created", []):
        if isinstance(artifact, dict):
            path = artifact.get("path", "")
            if path:
                evidence_artifacts.append(path)
        elif isinstance(artifact, str):
            evidence_artifacts.append(artifact)
    
    acceptance_pack_id = generate_acceptance_pack_id()
    
    return AcceptancePack(
        acceptance_pack_id=acceptance_pack_id,
        feature_id=feature_id,
        execution_result_id=execution_result_id,
        product_id=product_id,
        acceptance_criteria=acceptance_criteria,
        implementation_summary=implementation_summary,
        evidence_artifacts=evidence_artifacts,
        verification_summary=verification_summary,
        trigger_reason=trigger_reason,
        triggered_at=datetime.now().isoformat(),
        triggered_by="observer_auto_trigger",
        intended_validator_type=ValidatorType.AI_SESSION,
    )


def save_acceptance_pack(project_path: Path, acceptance_pack: AcceptancePack) -> Path:
    """Save AcceptancePack to markdown file."""
    acceptance_packs_dir = project_path / "acceptance-packs"
    acceptance_packs_dir.mkdir(parents=True, exist_ok=True)
    
    pack_path = acceptance_packs_dir / f"{acceptance_pack.acceptance_pack_id}.md"
    
    yaml_content = acceptance_pack.to_yaml()
    markdown_content = f"""# AcceptancePack

```yaml
{yaml_content}
```
"""
    
    pack_path.write_text(markdown_content, encoding="utf-8")
    return pack_path


def load_acceptance_pack(project_path: Path, acceptance_pack_id: str) -> AcceptancePack | None:
    """Load AcceptancePack from markdown file."""
    pack_path = project_path / "acceptance-packs" / f"{acceptance_pack_id}.md"
    
    if not pack_path.exists():
        return None
    
    content = pack_path.read_text(encoding="utf-8")
    
    lines = content.split("\n")
    yaml_start = None
    yaml_end = None
    
    for i, line in enumerate(lines):
        if line.strip() == "```yaml":
            yaml_start = i + 1
        elif yaml_start is not None and line.strip() == "```":
            yaml_end = i
            break
    
    if yaml_start is not None and yaml_end is not None:
        yaml_block = "\n".join(lines[yaml_start:yaml_end])
        data = yaml.safe_load(yaml_block)
        
        return AcceptancePack(
            acceptance_pack_id=data.get("acceptance_pack_id", ""),
            feature_id=data.get("feature_id", ""),
            execution_result_id=data.get("execution_result_id", ""),
            product_id=data.get("product_id", ""),
            acceptance_criteria=data.get("acceptance_criteria", []),
            implementation_summary=ImplementationSummary(**data.get("implementation_summary", {})),
            evidence_artifacts=data.get("evidence_artifacts", []),
            verification_summary=VerificationSummary(**data.get("verification_summary", {})),
            trigger_reason=data.get("trigger_reason", ""),
            triggered_at=data.get("triggered_at", ""),
            triggered_by=data.get("triggered_by", ""),
            intended_validator_type=ValidatorType(data.get("intended_validator_type", "ai_session")),
        )
    
    return None