"""Project-link loader for Feature 055 - CLI Project-Link Awareness."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class OwnershipMode(str, Enum):
    """Repository ownership mode."""
    SELF_HOSTED = "self_hosted"
    MANAGED_EXTERNAL = "managed_external"


@dataclass
class ProjectLinkContext:
    """Context for project-link aware operations."""
    product_id: str
    ownership_mode: OwnershipMode
    project_link_path: Path | None = None
    product_repo_path: Path | None = None
    orchestrator_repo_path: Path | None = None
    product_artifact_root: Path | None = None
    orchestration_artifact_root: Path | None = None
    current_phase: str = ""
    current_feature: str = ""
    email_channel_enabled: bool = False
    email_decision_inbox: str = ""
    email_sender: str = ""
    raw_config: dict[str, Any] = field(default_factory=dict)


def load_project_link(project_path: Path) -> ProjectLinkContext | None:
    """Load project-link.yaml from project directory.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        ProjectLinkContext if project-link exists, None otherwise
    """
    project_link_path = project_path / "project-link.yaml"
    
    if not project_link_path.exists():
        return None
    
    with open(project_link_path, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    return parse_project_link_config(config, project_link_path)


def parse_project_link_config(config: dict[str, Any], project_link_path: Path) -> ProjectLinkContext:
    """Parse project-link.yaml config into context.
    
    Args:
        config: Raw yaml config
        project_link_path: Path to project-link.yaml
        
    Returns:
        ProjectLinkContext
    """
    product_id = config.get("product_id", project_link_path.parent.name)
    
    mode_str = config.get("ownership_mode", "self_hosted")
    try:
        ownership_mode = OwnershipMode(mode_str)
    except ValueError:
        ownership_mode = OwnershipMode.SELF_HOSTED
    
    product_repo_raw = config.get("product_repo", {})
    orchestrator_repo_raw = config.get("orchestrator_repo", {})
    
    product_repo_path = None
    if isinstance(product_repo_raw, dict):
        path_str = product_repo_raw.get("path", "")
        if path_str:
            product_repo_path = Path(path_str)
    elif isinstance(product_repo_raw, str):
        product_repo_path = Path(product_repo_raw)
    
    orchestrator_repo_path = None
    if isinstance(orchestrator_repo_raw, dict):
        path_str = orchestrator_repo_raw.get("path", "")
        if path_str:
            orchestrator_repo_path = Path(path_str)
    elif isinstance(orchestrator_repo_raw, str):
        orchestrator_repo_path = Path(orchestrator_repo_raw)
    
    email_channel = config.get("email_channel", {})
    
    product_artifact_root = None
    if product_repo_path:
        product_artifact_root = product_repo_path
    
    orchestration_artifact_root = project_link_path.parent
    
    return ProjectLinkContext(
        product_id=product_id,
        ownership_mode=ownership_mode,
        project_link_path=project_link_path,
        product_repo_path=product_repo_path,
        orchestrator_repo_path=orchestrator_repo_path,
        product_artifact_root=product_artifact_root,
        orchestration_artifact_root=orchestration_artifact_root,
        current_phase=config.get("current_phase", ""),
        current_feature=config.get("current_feature", ""),
        email_channel_enabled=email_channel.get("enabled", False),
        email_decision_inbox=email_channel.get("decision_inbox", ""),
        email_sender=email_channel.get("sender", ""),
        raw_config=config,
    )


def detect_ownership_mode(project_path: Path) -> OwnershipMode:
    """Detect ownership mode from project directory.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        OwnershipMode (defaults to SELF_HOSTED if no project-link)
    """
    context = load_project_link(project_path)
    if context:
        return context.ownership_mode
    return OwnershipMode.SELF_HOSTED


def get_product_repo_path(project_path: Path) -> Path:
    """Get product repository path for artifact routing.
    
    Args:
        project_path: Path to project directory in async-dev
        
    Returns:
        Path to product repository
    """
    context = load_project_link(project_path)
    
    if context and context.ownership_mode == OwnershipMode.MANAGED_EXTERNAL:
        if context.product_repo_path:
            return context.product_repo_path
    
    return project_path


def get_orchestration_repo_path(project_path: Path) -> Path:
    """Get orchestration repository path for artifact routing.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Path to orchestration repository (async-dev)
    """
    context = load_project_link(project_path)
    
    if context and context.orchestrator_repo_path:
        return context.orchestrator_repo_path
    
    return project_path


def is_mode_b(project_path: Path) -> bool:
    """Check if project is in Mode B (managed_external).
    
    Args:
        project_path: Path to project directory
        
    Returns:
        True if managed_external mode
    """
    return detect_ownership_mode(project_path) == OwnershipMode.MANAGED_EXTERNAL


def validate_project_link(project_path: Path) -> tuple[bool, list[str]]:
    """Validate project-link.yaml structure.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Tuple of (is_valid, issues_list)
    """
    issues = []
    
    context = load_project_link(project_path)
    
    if not context:
        return True, []
    
    if not context.product_id:
        issues.append("Missing product_id")
    
    if context.ownership_mode == OwnershipMode.MANAGED_EXTERNAL:
        if not context.product_repo_path:
            issues.append("Mode B requires product_repo path")
        elif not context.product_repo_path.exists():
            issues.append(f"Product repo path not found: {context.product_repo_path}")
    
    return len(issues) == 0, issues


def get_project_link_summary(project_path: Path) -> dict[str, Any]:
    """Get summary of project-link for display.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Dict with summary info
    """
    context = load_project_link(project_path)
    
    if not context:
        return {
            "has_project_link": False,
            "ownership_mode": "self_hosted",
            "product_id": project_path.name,
        }
    
    return {
        "has_project_link": True,
        "ownership_mode": context.ownership_mode.value,
        "product_id": context.product_id,
        "product_repo_path": str(context.product_repo_path) if context.product_repo_path else None,
        "orchestrator_repo_path": str(context.orchestrator_repo_path) if context.orchestrator_repo_path else None,
        "current_phase": context.current_phase,
        "current_feature": context.current_feature,
        "email_enabled": context.email_channel_enabled,
    }