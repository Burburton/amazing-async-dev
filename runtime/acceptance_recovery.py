"""Acceptance to Recovery Integration - Feature 072.

Converts failed or conditional acceptance into structured recovery/rework inputs.
Maps acceptance findings to recovery categories.

Integration with:
- Feature 069/071 (AcceptanceResult)
- Feature 067 (Observer recovery findings)
- Feature 019 (Execution policy)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.acceptance_runner import AcceptanceResult, AcceptanceTerminalState, RemediationGuidance, load_acceptance_result
from runtime.acceptance_pack_builder import load_acceptance_pack


class RecoveryCategory(str, Enum):
    """Categories for acceptance failure recovery."""
    
    EVIDENCE_MISSING = "evidence_missing"
    CRITERION_FAILED = "criterion_failed"
    CONDITIONAL_ACCEPTANCE = "conditional_acceptance"
    VALIDATION_ERROR = "validation_error"
    IMPLEMENTATION_GAP = "implementation_gap"
    ESCALATION_REQUIRED = "escalation_required"


class RecoveryPriority(str, Enum):
    """Priority levels for recovery items."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RecoveryItem:
    """Single recovery item derived from acceptance failure."""
    
    recovery_item_id: str
    category: RecoveryCategory
    priority: RecoveryPriority
    
    source_acceptance_result_id: str
    source_criterion_id: str
    
    issue_description: str
    suggested_action: str
    
    related_artifacts: list[str] = field(default_factory=list)
    estimated_effort: str = "medium"
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_item_id": self.recovery_item_id,
            "category": self.category.value,
            "priority": self.priority.value,
            "source_acceptance_result_id": self.source_acceptance_result_id,
            "source_criterion_id": self.source_criterion_id,
            "issue_description": self.issue_description,
            "suggested_action": self.suggested_action,
            "related_artifacts": self.related_artifacts,
            "estimated_effort": self.estimated_effort,
            "created_at": self.created_at,
            "status": self.status,
        }


@dataclass
class AcceptanceRecoveryPack:
    """Pack of recovery items derived from failed acceptance (Feature 072)."""
    
    acceptance_recovery_pack_id: str
    acceptance_result_id: str
    feature_id: str
    
    recovery_items: list[RecoveryItem] = field(default_factory=list)
    
    total_items: int = 0
    critical_count: int = 0
    high_count: int = 0
    
    recommended_next_action: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "acceptance_recovery_pack_id": self.acceptance_recovery_pack_id,
            "acceptance_result_id": self.acceptance_result_id,
            "feature_id": self.feature_id,
            "recovery_items": [r.to_dict() for r in self.recovery_items],
            "total_items": self.total_items,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "recommended_next_action": self.recommended_next_action,
            "created_at": self.created_at,
        }


def categorize_failure(remediation: RemediationGuidance) -> RecoveryCategory:
    """Map remediation guidance to recovery category."""
    issue_type = remediation.issue_type
    
    if issue_type == "evidence_missing":
        return RecoveryCategory.EVIDENCE_MISSING
    elif issue_type == "criterion_failed":
        return RecoveryCategory.CRITERION_FAILED
    elif issue_type == "conditional":
        return RecoveryCategory.CONDITIONAL_ACCEPTANCE
    elif issue_type == "validation_error":
        return RecoveryCategory.VALIDATION_ERROR
    elif issue_type == "implementation_gap":
        return RecoveryCategory.IMPLEMENTATION_GAP
    elif issue_type == "escalation":
        return RecoveryCategory.ESCALATION_REQUIRED
    
    return RecoveryCategory.CRITERION_FAILED


def determine_priority(remediation: RemediationGuidance) -> RecoveryPriority:
    """Determine recovery priority from remediation guidance."""
    priority_str = remediation.priority.lower()
    
    if priority_str == "critical":
        return RecoveryPriority.CRITICAL
    elif priority_str == "high":
        return RecoveryPriority.HIGH
    elif priority_str == "medium":
        return RecoveryPriority.MEDIUM
    elif priority_str == "low":
        return RecoveryPriority.LOW
    
    return RecoveryPriority.MEDIUM


def generate_recovery_item_id(date_str: str | None = None, index: int = 1) -> str:
    """Generate recovery item ID."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    
    return f"ri-{date_str}-{index:03d}"


def convert_remediation_to_recovery_item(
    remediation: RemediationGuidance,
    acceptance_result_id: str,
    index: int = 1,
) -> RecoveryItem:
    """Convert RemediationGuidance to RecoveryItem."""
    category = categorize_failure(remediation)
    priority = determine_priority(remediation)
    
    return RecoveryItem(
        recovery_item_id=generate_recovery_item_id(index=index),
        category=category,
        priority=priority,
        source_acceptance_result_id=acceptance_result_id,
        source_criterion_id=remediation.criterion_id,
        issue_description=f"Criterion {remediation.criterion_id} requires rework: {remediation.issue_type}",
        suggested_action=remediation.suggested_fix,
        related_artifacts=remediation.related_artifacts,
        estimated_effort="medium",
    )


def create_acceptance_recovery_pack(
    project_path: Path,
    acceptance_result_id: str,
) -> AcceptanceRecoveryPack | None:
    """Create recovery pack from failed acceptance result (Feature 072)."""
    acceptance_result = load_acceptance_result(project_path, acceptance_result_id)
    
    if acceptance_result is None:
        return None
    
    if acceptance_result.is_valid_for_completion():
        return None
    
    acceptance_pack = load_acceptance_pack(project_path, acceptance_result.acceptance_pack_id)
    
    if acceptance_pack is None:
        return None
    
    recovery_items: list[RecoveryItem] = []
    
    for i, remediation in enumerate(acceptance_result.remediation_guidance, 1):
        recovery_item = convert_remediation_to_recovery_item(
            remediation,
            acceptance_result_id,
            i,
        )
        recovery_items.append(recovery_item)
    
    for criterion_id in acceptance_result.failed_criteria:
        existing = [r for r in recovery_items if r.source_criterion_id == criterion_id]
        if not existing:
            recovery_items.append(RecoveryItem(
                recovery_item_id=generate_recovery_item_id(index=len(recovery_items) + 1),
                category=RecoveryCategory.CRITERION_FAILED,
                priority=RecoveryPriority.HIGH,
                source_acceptance_result_id=acceptance_result_id,
                source_criterion_id=criterion_id,
                issue_description=f"Criterion {criterion_id} failed without specific remediation",
                suggested_action=f"Review and fix implementation for criterion {criterion_id}",
            ))
    
    if acceptance_result.terminal_state == AcceptanceTerminalState.ESCALATED:
        recovery_items.append(RecoveryItem(
            recovery_item_id=generate_recovery_item_id(index=len(recovery_items) + 1),
            category=RecoveryCategory.ESCALATION_REQUIRED,
            priority=RecoveryPriority.CRITICAL,
            source_acceptance_result_id=acceptance_result_id,
            source_criterion_id="escalation",
            issue_description="Acceptance requires human escalation",
            suggested_action="Review acceptance findings and make decision",
            estimated_effort="high",
        ))
    
    critical_count = sum(1 for r in recovery_items if r.priority == RecoveryPriority.CRITICAL)
    high_count = sum(1 for r in recovery_items if r.priority == RecoveryPriority.HIGH)
    
    recommended_next_action = determine_next_action(
        acceptance_result.terminal_state,
        recovery_items,
    )
    
    date_str = datetime.now().strftime("%Y%m%d")
    recovery_pack_id = f"arp-{date_str}-001"
    
    return AcceptanceRecoveryPack(
        acceptance_recovery_pack_id=recovery_pack_id,
        acceptance_result_id=acceptance_result_id,
        feature_id=acceptance_pack.feature_id,
        recovery_items=recovery_items,
        total_items=len(recovery_items),
        critical_count=critical_count,
        high_count=high_count,
        recommended_next_action=recommended_next_action,
    )


def determine_next_action(
    terminal_state: AcceptanceTerminalState,
    recovery_items: list[RecoveryItem],
) -> str:
    """Determine recommended next action."""
    if terminal_state == AcceptanceTerminalState.ESCALATED:
        return "Resolve escalation before proceeding with implementation"
    
    if terminal_state == AcceptanceTerminalState.MANUAL_REVIEW:
        return "Complete manual review and update acceptance state"
    
    critical_items = [r for r in recovery_items if r.priority == RecoveryPriority.CRITICAL]
    if critical_items:
        return f"Address {len(critical_items)} critical recovery items before re-acceptance"
    
    high_items = [r for r in recovery_items if r.priority == RecoveryPriority.HIGH]
    if high_items:
        return f"Fix {len(high_items)} high-priority items and request re-acceptance"
    
    return "Address recovery items and trigger re-acceptance"


def attach_recovery_to_runstate(
    project_path: Path,
    recovery_pack: AcceptanceRecoveryPack,
) -> None:
    """Attach recovery items to RunState blocked_items."""
    from runtime.state_store import StateStore
    
    store = StateStore(project_path)
    runstate = store.load_runstate() or {}
    
    blocked_items = runstate.get("blocked_items", [])
    
    for item in recovery_pack.recovery_items:
        blocked_items.append({
            "type": "acceptance_recovery",
            "recovery_item_id": item.recovery_item_id,
            "category": item.category.value,
            "priority": item.priority.value,
            "source_acceptance_result_id": item.source_acceptance_result_id,
        })
    
    runstate["blocked_items"] = blocked_items
    runstate["acceptance_recovery_pending"] = True
    runstate["acceptance_recovery_pack_id"] = recovery_pack.acceptance_recovery_pack_id
    
    store.save_runstate(runstate)


def get_recovery_items_for_feature(
    project_path: Path,
    feature_id: str,
) -> list[RecoveryItem]:
    """Get all pending recovery items for a feature."""
    recovery_dir = project_path / "acceptance-recovery"
    
    if not recovery_dir.exists():
        return []
    
    items: list[RecoveryItem] = []
    
    for pack_file in recovery_dir.glob("*.md"):
        pack = load_acceptance_recovery_pack(project_path, pack_file.stem)
        if pack and pack.feature_id == feature_id:
            for item in pack.recovery_items:
                if item.status == "pending":
                    items.append(item)
    
    return items


def save_acceptance_recovery_pack(
    project_path: Path,
    recovery_pack: AcceptanceRecoveryPack,
) -> Path:
    """Save AcceptanceRecoveryPack to file."""
    import yaml
    
    recovery_dir = project_path / "acceptance-recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    
    pack_path = recovery_dir / f"{recovery_pack.acceptance_recovery_pack_id}.md"
    
    yaml_content = yaml.dump(recovery_pack.to_dict(), default_flow_style=False, sort_keys=False)
    markdown_content = f"""# AcceptanceRecoveryPack

```yaml
{yaml_content}
```
"""
    
    pack_path.write_text(markdown_content, encoding="utf-8")
    return pack_path


def load_acceptance_recovery_pack(
    project_path: Path,
    recovery_pack_id: str,
) -> AcceptanceRecoveryPack | None:
    """Load AcceptanceRecoveryPack from file."""
    import yaml
    
    pack_path = project_path / "acceptance-recovery" / f"{recovery_pack_id}.md"
    
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
        
        recovery_items = [
            RecoveryItem(**r) for r in data.get("recovery_items", [])
        ]
        
        return AcceptanceRecoveryPack(
            acceptance_recovery_pack_id=data.get("acceptance_recovery_pack_id", ""),
            acceptance_result_id=data.get("acceptance_result_id", ""),
            feature_id=data.get("feature_id", ""),
            recovery_items=recovery_items,
            total_items=data.get("total_items", 0),
            critical_count=data.get("critical_count", 0),
            high_count=data.get("high_count", 0),
            recommended_next_action=data.get("recommended_next_action", ""),
            created_at=data.get("created_at", ""),
        )
    
    return None


def process_failed_acceptance(
    project_path: Path,
    acceptance_result_id: str,
) -> AcceptanceRecoveryPack | None:
    """Process failed acceptance and create recovery flow (Feature 072 full)."""
    recovery_pack = create_acceptance_recovery_pack(project_path, acceptance_result_id)
    
    if recovery_pack is None:
        return None
    
    save_acceptance_recovery_pack(project_path, recovery_pack)
    attach_recovery_to_runstate(project_path, recovery_pack)
    
    return recovery_pack