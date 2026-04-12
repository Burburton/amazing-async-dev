"""Starter Pack Consumer - Parse and validate starter packs from advisor."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ConsumptionResult:
    """Result of starter pack consumption."""
    
    success: bool
    error: Optional[str] = None
    product_brief_fields: Dict[str, Any] = field(default_factory=dict)
    runstate_hints: Dict[str, Any] = field(default_factory=dict)
    advisory_context: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


SUPPORTED_CONTRACT_VERSIONS = ["1.0"]
MIN_ASYNCDEV_VERSION = "v0.19.0"


def consume_starter_pack(starter_pack_path: str) -> ConsumptionResult:
    """
    Parse and validate starter pack for async-dev consumption.
    
    Args:
        starter_pack_path: Path to starter-pack.yaml
        
    Returns:
        ConsumptionResult with mapped fields and validation status
    """
    path = Path(starter_pack_path)
    
    if not path.exists():
        return ConsumptionResult(
            success=False,
            error=f"Starter pack not found: {starter_pack_path}",
        )
    
    try:
        with open(path, encoding="utf-8") as f:
            pack = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return ConsumptionResult(
            success=False,
            error=f"Invalid YAML: {e}",
        )
    
    if not pack:
        return ConsumptionResult(
            success=False,
            error="Empty starter pack",
        )
    
    integration = pack.get("integration_metadata", {})
    compatibility = pack.get("asyncdev_compatibility", {})
    
    contract_version = integration.get("contract_version", "")
    if contract_version not in SUPPORTED_CONTRACT_VERSIONS:
        return ConsumptionResult(
            success=False,
            error=f"Unsupported contract version: {contract_version}. Supported: {SUPPORTED_CONTRACT_VERSIONS}",
        )
    
    if not compatibility.get("compatible", True):
        return ConsumptionResult(
            success=False,
            error="Starter pack marked as incompatible",
        )
    
    min_version = compatibility.get("minimum_version", MIN_ASYNCDEV_VERSION)
    if min_version > MIN_ASYNCDEV_VERSION:
        warnings = [f"Starter pack recommends async-dev {min_version}+ (current: {MIN_ASYNCDEV_VERSION})"]
    else:
        warnings = []
    
    incompatible_fields = compatibility.get("incompatible_fields", [])
    if incompatible_fields:
        warnings.append(f"Some fields not supported: {incompatible_fields}")
    
    profile = pack.get("project_profile", {})
    workflow_mode = pack.get("workflow_mode", {})
    workflow_defaults = pack.get("workflow_defaults", {})
    
    product_brief_fields = {
        "problem_prefix": profile.get("summary", ""),
        "product_type": profile.get("product_type", ""),
        "stage": profile.get("stage", ""),
        "team_mode": profile.get("team_mode", ""),
        "required_skills": pack.get("required_skills", []),
    }
    
    runstate_hints = {
        "policy_mode_hint": workflow_defaults.get("policy_mode_hint", "balanced"),
        "execution_mode": workflow_mode.get("execution", "external-tool-first"),
        "review_mode": workflow_mode.get("review", "lightweight-summary"),
        "planning_mode": workflow_mode.get("planning", "simple-plan-day"),
        "archive_mode": workflow_mode.get("archive", "minimal-archive"),
        "decision_handling": workflow_defaults.get("decision_handling", "pause_for_human"),
    }
    
    advisory_context = {
        "optional_skills": pack.get("optional_skills", []),
        "deferred_skills": pack.get("deferred_skills", []),
        "rationale": pack.get("rationale", []),
        "notes": pack.get("notes", ""),
        "ergonomics": workflow_mode.get("ergonomics", "minimal-cli"),
        "compatibility_notes": compatibility.get("compatibility_notes", []),
    }
    
    return ConsumptionResult(
        success=True,
        product_brief_fields=product_brief_fields,
        runstate_hints=runstate_hints,
        advisory_context=advisory_context,
        warnings=warnings,
    )


def format_product_brief_with_starter_pack(
    base_brief: Dict[str, Any],
    consumption: ConsumptionResult,
) -> Dict[str, Any]:
    """
    Merge starter pack fields into product-brief.yaml.
    
    Args:
        base_brief: Base product brief dict
        consumption: ConsumptionResult from starter pack
        
    Returns:
        Enhanced product brief dict
    """
    if not consumption.success:
        return base_brief
    
    fields = consumption.product_brief_fields
    
    problem = base_brief.get("problem", "")
    summary = fields.get("problem_prefix", "")
    if summary:
        problem = f"[{summary}] {problem}"
    
    notes_parts = []
    if fields.get("product_type"):
        notes_parts.append(f"Product type: {fields['product_type']}")
    if fields.get("stage"):
        notes_parts.append(f"Stage: {fields['stage']}")
    if fields.get("team_mode"):
        notes_parts.append(f"Team mode: {fields['team_mode']}")
    if fields.get("required_skills"):
        notes_parts.append(f"Required skills: {', '.join(fields['required_skills'])}")
    
    brief = base_brief.copy()
    brief["problem"] = problem
    if notes_parts:
        brief["starter_pack_context"] = notes_parts
    
    return brief


def format_runstate_with_starter_pack(
    base_runstate: Dict[str, Any],
    consumption: ConsumptionResult,
) -> Dict[str, Any]:
    """
    Merge starter pack hints into runstate.
    
    Args:
        base_runstate: Base runstate dict
        consumption: ConsumptionResult from starter pack
        
    Returns:
        Enhanced runstate dict
    """
    if not consumption.success:
        return base_runstate
    
    hints = consumption.runstate_hints
    
    runstate = base_runstate.copy()
    runstate["workflow_hints"] = {
        "policy_mode": hints.get("policy_mode_hint", "balanced"),
        "execution": hints.get("execution_mode"),
        "review": hints.get("review_mode"),
        "planning": hints.get("planning_mode"),
        "archive": hints.get("archive_mode"),
        "decision_handling": hints.get("decision_handling"),
    }
    
    return runstate