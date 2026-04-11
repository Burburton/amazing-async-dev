"""Archive pack builder - generates ArchivePack from RunState."""

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