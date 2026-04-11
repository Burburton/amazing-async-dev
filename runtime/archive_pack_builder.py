"""Archive pack builder - generates ArchivePack from RunState or historical backfill."""

from datetime import datetime
from pathlib import Path
from typing import Any


def build_archive_pack(
    runstate: dict[str, Any],
    feature_id: str,
    product_id: str,
    final_status: str = "completed",
    lessons_input: str | None = None,
    patterns_input: str | None = None,
) -> dict[str, Any]:
    """Build ArchivePack from RunState and inputs.

    Args:
        runstate: Current RunState dict
        feature_id: Feature being archived
        product_id: Product ID
        final_status: completed/partial/abandoned
        lessons_input: Comma-separated lessons (optional)
        patterns_input: Comma-separated patterns (optional)

    Returns:
        ArchivePack dict ready for YAML serialization
    """
    completed_outputs = runstate.get("completed_outputs", [])
    decisions_needed = runstate.get("decisions_needed", [])
    blocked_items = runstate.get("blocked_items", [])

    delivered_outputs = []
    for output in completed_outputs:
        if isinstance(output, str):
            delivered_outputs.append({
                "name": output,
                "path": output,
                "type": _guess_output_type(output),
            })
        elif isinstance(output, dict):
            delivered_outputs.append(output)

    decisions_made = []
    for d in decisions_needed:
        decisions_made.append({
            "decision": d.get("decision", "unknown"),
            "rationale": d.get("recommendation", ""),
            "impact": d.get("impact", ""),
        })

    lessons_learned = _parse_lessons(lessons_input)
    if not lessons_learned:
        lessons_learned = [{
            "lesson": "No explicit lessons recorded",
            "context": "Consider documenting what worked well",
        }]

    reusable_patterns = _parse_patterns(patterns_input)
    if not reusable_patterns:
        reusable_patterns = [{
            "pattern": "Schema + Template + Example structure",
            "applicability": "Object definitions",
        }]

    unresolved_followups = []
    for b in blocked_items:
        unresolved_followups.append({
            "item": b.get("item", b.get("reason", "unknown")),
            "priority": "high",
            "reason": b.get("reason", "blocked"),
        })

    acceptance_result = {
        "satisfied": [o.get("name", o) for o in delivered_outputs[:3]],
        "unsatisfied": [f["item"] for f in unresolved_followups],
        "overall": "mostly-satisfied" if delivered_outputs else "partial",
    }

    archive_pack = {
        "feature_id": feature_id,
        "product_id": product_id,
        "title": _get_feature_title(runstate, feature_id),
        "final_status": final_status,
        "delivered_outputs": delivered_outputs,
        "acceptance_result": acceptance_result,
        "unresolved_followups": unresolved_followups,
        "decisions_made": decisions_made,
        "lessons_learned": lessons_learned,
        "reusable_patterns": reusable_patterns,
        "archived_at": datetime.now().isoformat(),
    }

    if runstate.get("completion_override"):
        archive_pack["completion_override"] = runstate["completion_override"]

    return archive_pack


def _guess_output_type(path: str) -> str:
    if ".schema.yaml" in path:
        return "schema"
    elif ".template.md" in path:
        return "template"
    elif ".spec.yaml" in path:
        return "spec"
    elif ".py" in path:
        return "code"
    elif ".md" in path:
        return "documentation"
    return "file"


def _parse_lessons(input_str: str | None) -> list[dict[str, str]]:
    if not input_str:
        return []

    lessons = []
    for item in input_str.split(","):
        item = item.strip()
        if item:
            lessons.append({
                "lesson": item,
                "context": "User-provided during archiving",
            })
    return lessons


def _parse_patterns(input_str: str | None) -> list[dict[str, str]]:
    if not input_str:
        return []

    patterns = []
    for item in input_str.split(","):
        item = item.strip()
        if item:
            patterns.append({
                "pattern": item,
                "applicability": "User-provided during archiving",
            })
    return patterns


def _get_feature_title(runstate: dict[str, Any], feature_id: str) -> str:
    feature_dir = Path(runstate.get("project_path", "projects/demo-product")) / "features" / feature_id
    spec_path = feature_dir / "feature-spec.yaml"

    if spec_path.exists():
        import yaml
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
            return spec.get("name", spec.get("title", feature_id))

    return feature_id


def load_archive_pack(archive_path: Path) -> dict[str, Any] | None:
    """Load ArchivePack from YAML file."""
    if not archive_path.exists():
        return None

    import yaml
    with open(archive_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_archive_pack(archive_pack: dict[str, Any], archive_path: Path) -> None:
    """Save ArchivePack to YAML file."""
    import yaml

    archive_path.parent.mkdir(parents=True, exist_ok=True)

    with open(archive_path, "w", encoding="utf-8") as f:
        yaml.dump(archive_pack, f, default_flow_style=False, sort_keys=False)


def build_backfill_archive_pack(
    feature_id: str,
    product_id: str,
    title: str | None = None,
    final_status: str = "completed",
    delivered_outputs: list[str] | None = None,
    decisions_made: list[str] | None = None,
    lessons_input: str | None = None,
    patterns_input: str | None = None,
    artifact_links: list[str] | None = None,
    historical_notes: str | None = None,
    feature_spec_path: Path | None = None,
) -> dict[str, Any]:
    """Build ArchivePack for historical feature backfill.
    
    Creates a simplified archive record for features completed before
    the formal archive system existed. Clearly marked as backfilled.
    
    Args:
        feature_id: Feature being backfilled
        product_id: Product ID
        title: Feature title (extracted from spec if not provided)
        final_status: completed/partial/abandoned
        delivered_outputs: List of delivered output names
        decisions_made: List of key decisions made
        lessons_input: Comma-separated lessons learned
        patterns_input: Comma-separated reusable patterns
        artifact_links: List of important artifact paths
        historical_notes: Notes about historical context
        feature_spec_path: Path to feature-spec.yaml for extraction
        
    Returns:
        ArchivePack dict with backfill metadata
    """
    if title is None:
        title = _extract_title_from_spec(feature_id, product_id, feature_spec_path)
    
    outputs = []
    for output in (delivered_outputs or []):
        outputs.append({
            "name": output,
            "path": output,
            "type": _guess_output_type(output),
        })
    
    decisions = []
    for decision in (decisions_made or []):
        decisions.append({
            "decision": decision,
            "rationale": "Historical record",
            "impact": "Documented during backfill",
        })
    
    lessons = _parse_lessons(lessons_input)
    if not lessons:
        lessons = [{
            "lesson": "No explicit lessons recorded",
            "context": "Historical feature - lessons may need manual addition",
        }]
    
    patterns = _parse_patterns(patterns_input)
    if not patterns:
        patterns = [{
            "pattern": "Standard implementation approach",
            "applicability": "Historical feature context",
        }]
    
    links = []
    for link in (artifact_links or []):
        links.append({
            "artifact": link,
            "type": _guess_output_type(link),
            "note": "Historical reference",
        })
    
    archive_pack = {
        "feature_id": feature_id,
        "product_id": product_id,
        "title": title or feature_id,
        "final_status": final_status,
        "delivered_outputs": outputs,
        "decisions_made": decisions,
        "lessons_learned": lessons,
        "reusable_patterns": patterns,
        "artifact_links": links,
        "archived_at": datetime.now().isoformat(),
        "archived_via_backfill": True,
        "backfilled_at": datetime.now().isoformat(),
        "backfill_source": "manual-backfill-command",
    }
    
    if historical_notes:
        archive_pack["historical_notes"] = historical_notes
    
    archive_pack["known_gaps"] = [
        "Original execution logs not available",
        "Intermediate runtime artifacts may be missing",
        "Decision traceability limited to backfill input",
    ]
    
    archive_pack["backfill_confidence"] = "medium"
    
    return archive_pack


def _extract_title_from_spec(
    feature_id: str,
    product_id: str,
    spec_path: Path | None = None,
) -> str:
    import yaml
    
    if spec_path is None:
        spec_path = Path("projects") / product_id / "features" / feature_id / "feature-spec.yaml"
    
    if spec_path.exists():
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
            return spec.get("name", spec.get("title", feature_id))
    
    return feature_id


def check_backfill_eligibility(
    feature_id: str,
    product_id: str,
    projects_path: Path = Path("projects"),
) -> dict[str, Any]:
    """Check if a feature is eligible for archive backfill.
    
    Args:
        feature_id: Feature to check
        product_id: Product ID
        projects_path: Root projects directory
        
    Returns:
        Dict with eligibility status and reasoning
    """
    project_path = projects_path / product_id
    feature_dir = project_path / "features" / feature_id
    archive_path = project_path / "archive" / feature_id / "archive-pack.yaml"
    runstate_path = project_path / "runstate.md"
    
    result = {
        "feature_id": feature_id,
        "product_id": product_id,
        "eligible": False,
        "reasons": [],
        "warnings": [],
    }
    
    if archive_path.exists():
        result["reasons"].append("Already archived - no need to backfill")
        result["warnings"].append("Archive pack already exists at: " + str(archive_path))
        return result
    
    if not feature_dir.exists():
        result["reasons"].append("Feature directory does not exist")
        result["warnings"].append("No feature found at: " + str(feature_dir))
        return result
    
    spec_path = feature_dir / "feature-spec.yaml"
    if spec_path.exists():
        result["has_spec"] = True
        result["spec_path"] = str(spec_path)
    else:
        result["has_spec"] = False
        result["warnings"].append("No feature-spec.yaml found")
    
    if runstate_path.exists():
        import yaml
        with open(runstate_path, encoding="utf-8") as f:
            content = f.read()
            yaml_start = content.find("```yaml")
            yaml_end = content.find("```", yaml_start + 7)
            if yaml_start >= 0 and yaml_end >= 0:
                yaml_content = content[yaml_start + 7:yaml_end]
                runstate = yaml.safe_load(yaml_content)
                
                current_feature = runstate.get("feature_id", "")
                current_phase = runstate.get("current_phase", "")
                
                if current_feature == feature_id and current_phase == "archived":
                    result["already_archived_in_runstate"] = True
                    result["warnings"].append("Feature marked archived in RunState but no archive-pack found")
                elif current_feature == feature_id:
                    result["current_phase"] = current_phase
                    result["warnings"].append(f"Feature in RunState at phase: {current_phase}")
    
    result["eligible"] = True
    result["reasons"].append("Feature exists and not yet archived")
    
    return result