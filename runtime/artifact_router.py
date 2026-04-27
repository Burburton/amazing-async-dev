"""Artifact router for Feature 055 - CLI Project-Link Awareness."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.project_link_loader import (
    ProjectLinkContext,
    OwnershipMode,
    load_project_link,
    get_product_repo_path,
    get_orchestration_repo_path,
    is_mode_b,
)


class ArtifactType(str, Enum):
    """Types of artifacts that need routing."""
    PRODUCT_BRIEF = "product_brief"
    FEATURE_SPEC = "feature_spec"
    FEATURE_COMPLETION_REPORT = "feature_completion_report"
    DOGFOOD_REPORT = "dogfood_report"
    FRICION_LOG = "friction_log"
    PHASE_SUMMARY = "phase_summary"
    NORTH_STAR = "north_star"
    PRODUCT_MEMORY = "product_memory"
    
    EXECUTION_PACK = "execution_pack"
    EXECUTION_RESULT = "execution_result"
    RUNSTATE = "runstate"
    VERIFICATION_RECORD = "verification_record"
    CONTINUATION_STATE = "continuation_state"
    PROJECT_LINK = "project_link"
    DECISION_REQUEST = "decision_request"
    
    DAILY_REVIEW_PACK = "daily_review_pack"
    
    ACCEPTANCE_PACK = "acceptance_pack"
    ACCEPTANCE_RESULT = "acceptance_result"
    ACCEPTANCE_RECOVERY_PACK = "acceptance_recovery_pack"
    ACCEPTANCE_HISTORY = "acceptance_history"
    OBSERVER_FINDINGS = "observer_findings"
    
    EVIDENCE_SUMMARY = "evidence_summary"


PRODUCT_OWNED_ARTIFACTS = {
    ArtifactType.PRODUCT_BRIEF,
    ArtifactType.FEATURE_SPEC,
    ArtifactType.FEATURE_COMPLETION_REPORT,
    ArtifactType.DOGFOOD_REPORT,
    ArtifactType.FRICION_LOG,
    ArtifactType.PHASE_SUMMARY,
    ArtifactType.NORTH_STAR,
    ArtifactType.PRODUCT_MEMORY,
}

ORCHESTRATION_OWNED_ARTIFACTS = {
    ArtifactType.EXECUTION_PACK,
    ArtifactType.EXECUTION_RESULT,
    ArtifactType.RUNSTATE,
    ArtifactType.VERIFICATION_RECORD,
    ArtifactType.CONTINUATION_STATE,
    ArtifactType.PROJECT_LINK,
    ArtifactType.DECISION_REQUEST,
    ArtifactType.DAILY_REVIEW_PACK,
    ArtifactType.ACCEPTANCE_PACK,
    ArtifactType.ACCEPTANCE_RESULT,
    ArtifactType.ACCEPTANCE_RECOVERY_PACK,
    ArtifactType.ACCEPTANCE_HISTORY,
    ArtifactType.OBSERVER_FINDINGS,
    ArtifactType.EVIDENCE_SUMMARY,
}


@dataclass
class RoutingResult:
    """Result of artifact routing decision."""
    artifact_type: ArtifactType
    target_path: Path
    ownership: str
    is_product_owned: bool
    warnings: list[str]


def is_product_owned(artifact_type: ArtifactType) -> bool:
    """Check if artifact type is owned by product.
    
    Args:
        artifact_type: Type of artifact
        
    Returns:
        True if product-owned
    """
    return artifact_type in PRODUCT_OWNED_ARTIFACTS


def is_orchestration_owned(artifact_type: ArtifactType) -> bool:
    """Check if artifact type is owned by orchestrator.
    
    Args:
        artifact_type: Type of artifact
        
    Returns:
        True if orchestration-owned
    """
    return artifact_type in ORCHESTRATION_OWNED_ARTIFACTS


def route_artifact(
    artifact_type: ArtifactType,
    project_path: Path,
    relative_path: str | None = None,
) -> RoutingResult:
    """Route artifact to correct repository based on ownership.
    
    Args:
        artifact_type: Type of artifact
        project_path: Project directory path in async-dev
        relative_path: Optional relative path within artifact root
        
    Returns:
        RoutingResult with target path and ownership info
    """
    warnings = []
    context = load_project_link(project_path)
    
    if is_product_owned(artifact_type):
        if context and context.ownership_mode == OwnershipMode.MANAGED_EXTERNAL:
            target_repo = get_product_repo_path(project_path)
            ownership = "product"
        else:
            target_repo = project_path
            ownership = "product (self_hosted)"
    elif is_orchestration_owned(artifact_type):
        target_repo = get_orchestration_repo_path(project_path)
        ownership = "orchestration"
    else:
        target_repo = project_path
        ownership = "unknown"
        warnings.append(f"Unknown artifact type: {artifact_type}")
    
    target_path = target_repo
    if relative_path:
        target_path = target_repo / relative_path
    
    return RoutingResult(
        artifact_type=artifact_type,
        target_path=target_path,
        ownership=ownership,
        is_product_owned=is_product_owned(artifact_type),
        warnings=warnings,
    )


def get_feature_spec_path(project_path: Path, feature_id: str) -> Path:
    """Get path for FeatureSpec based on ownership mode.
    
    Args:
        project_path: Project directory path
        feature_id: Feature identifier
        
    Returns:
        Path to feature-spec location
    """
    result = route_artifact(
        ArtifactType.FEATURE_SPEC,
        project_path,
        f"docs/features/{feature_id}/feature-spec.md",
    )
    return result.target_path


def get_execution_pack_path(project_path: Path, execution_id: str) -> Path:
    """Get path for ExecutionPack (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        execution_id: Execution identifier
        
    Returns:
        Path to execution-pack location
    """
    result = route_artifact(
        ArtifactType.EXECUTION_PACK,
        project_path,
        f"execution-packs/{execution_id}.md",
    )
    return result.target_path


def get_execution_result_path(project_path: Path, execution_id: str) -> Path:
    """Get path for ExecutionResult (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        execution_id: Execution identifier
        
    Returns:
        Path to execution-result location
    """
    result = route_artifact(
        ArtifactType.EXECUTION_RESULT,
        project_path,
        f"execution-results/{execution_id}.md",
    )
    return result.target_path


def get_runstate_path(project_path: Path) -> Path:
    """Get path for RunState (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        
    Returns:
        Path to runstate.md location
    """
    result = route_artifact(ArtifactType.RUNSTATE, project_path, "runstate.md")
    return result.target_path


def get_acceptance_pack_path(project_path: Path, pack_id: str) -> Path:
    """Get path for AcceptancePack (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        pack_id: Acceptance pack identifier
        
    Returns:
        Path to acceptance-pack location
    """
    result = route_artifact(
        ArtifactType.ACCEPTANCE_PACK,
        project_path,
        f"acceptance-packs/{pack_id}.md",
    )
    return result.target_path


def get_acceptance_result_path(project_path: Path, result_id: str) -> Path:
    """Get path for AcceptanceResult (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        result_id: Acceptance result identifier
        
    Returns:
        Path to acceptance-result location
    """
    result = route_artifact(
        ArtifactType.ACCEPTANCE_RESULT,
        project_path,
        f"acceptance-results/{result_id}.md",
    )
    return result.target_path


def get_acceptance_recovery_pack_path(project_path: Path, pack_id: str) -> Path:
    """Get path for AcceptanceRecoveryPack (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        pack_id: Acceptance recovery pack identifier
        
    Returns:
        Path to acceptance-recovery-pack location
    """
    result = route_artifact(
        ArtifactType.ACCEPTANCE_RECOVERY_PACK,
        project_path,
        f"acceptance-recovery/{pack_id}.md",
    )
    return result.target_path


def get_evidence_summary_path(project_path: Path, feature_id: str | None = None) -> Path:
    """Get path for EvidenceSummary (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        feature_id: Optional feature ID for feature-level summary
        
    Returns:
        Path to evidence-summary location
    """
    if feature_id:
        result = route_artifact(
            ArtifactType.EVIDENCE_SUMMARY,
            project_path,
            f"evidence-summaries/{feature_id}-evidence-summary.md",
        )
    else:
        result = route_artifact(
            ArtifactType.EVIDENCE_SUMMARY,
            project_path,
            "evidence-summary.md",
        )
    return result.target_path


def get_observer_findings_path(project_path: Path, observation_id: str) -> Path:
    """Get path for ObserverFindings (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        observation_id: Observation identifier (e.g., obs-20260427120000)
        
    Returns:
        Path to observer-findings location
    """
    result = route_artifact(
        ArtifactType.OBSERVER_FINDINGS,
        project_path,
        f"observer-findings/{observation_id}.md",
    )
    return result.target_path


def get_observer_findings_dir(project_path: Path) -> Path:
    """Get directory for all observer findings (always in orchestration repo).
    
    Args:
        project_path: Project directory path
        
    Returns:
        Path to observer-findings directory
    """
    result = route_artifact(
        ArtifactType.OBSERVER_FINDINGS,
        project_path,
        "observer-findings",
    )
    return result.target_path


def route_new_feature(
    project_path: Path,
    feature_id: str,
) -> tuple[Path, Path]:
    """Route paths for new feature creation.
    
    Args:
        project_path: Project directory path
        feature_id: Feature identifier
        
    Returns:
        Tuple of (feature_spec_path, feature_dir_path)
    """
    spec_result = route_artifact(
        ArtifactType.FEATURE_SPEC,
        project_path,
        f"docs/features/{feature_id}/feature-spec.md",
    )
    
    feature_dir = spec_result.target_path.parent
    
    return spec_result.target_path, feature_dir


def check_artifact_placement(
    project_path: Path,
    artifact_type: ArtifactType,
    actual_path: Path,
) -> tuple[bool, str]:
    """Check if artifact is placed in correct location.
    
    Args:
        project_path: Project directory path
        artifact_type: Type of artifact
        actual_path: Where artifact was actually placed
        
    Returns:
        Tuple of (is_correct, message)
    """
    expected = route_artifact(artifact_type, project_path)
    
    if actual_path == expected.target_path:
        return True, "Artifact placed correctly"
    
    if expected.is_product_owned:
        if is_mode_b(project_path):
            if str(actual_path).startswith(str(get_product_repo_path(project_path))):
                return True, "Artifact in product repo (acceptable)"
    
    return False, f"Expected {expected.target_path}, found {actual_path}"


def get_routing_summary(project_path: Path) -> dict[str, Any]:
    """Get routing summary for display.
    
    Args:
        project_path: Project directory path
        
    Returns:
        Dict with routing info
    """
    context = load_project_link(project_path)
    
    if not context:
        return {
            "mode": "self_hosted",
            "all_artifacts_local": True,
            "product_repo": str(project_path),
            "orchestration_repo": str(project_path),
        }
    
    return {
        "mode": context.ownership_mode.value,
        "product_owned_count": len(PRODUCT_OWNED_ARTIFACTS),
        "orchestration_owned_count": len(ORCHESTRATION_OWNED_ARTIFACTS),
        "product_repo": str(get_product_repo_path(project_path)),
        "orchestration_repo": str(get_orchestration_repo_path(project_path)),
        "routing_rules": {
            "FeatureSpec": "Product repo (Mode B)",
            "ExecutionPack": "Orchestration repo",
            "ExecutionResult": "Orchestration repo",
            "RunState": "Orchestration repo",
        },
    }