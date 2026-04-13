"""Artifact detection and reading module.

V1.1: Stabilized artifact ingestion with fallback handling.
"""

from pathlib import Path
from typing import Any
import yaml
from dataclasses import dataclass, field


@dataclass
class JournalEntry:
    """Normalized journal entry from an async-dev artifact.
    
    V1.1: Stable internal event shape for timeline view.
    """
    timestamp: str = ""
    day: str = ""
    artifact_type: str = ""
    project_id: str = ""
    feature_id: str = ""
    title: str = ""
    summary: str = ""
    key_fields: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""
    parse_status: str = "success"
    parse_warning: str = ""


ARTIFACT_TYPES = {
    "review": {
        "patterns": ["reviews/*-review.md", "reviews/YYYY-MM-DD-review.md"],
        "artifact_name": "DailyReviewPack",
        "label": "Review Night",
    },
    "plan": {
        "patterns": ["execution-packs/exec-*.md"],
        "artifact_name": "ExecutionPack",
        "label": "Plan Day",
    },
    "run": {
        "patterns": ["execution-results/exec-*.md"],
        "artifact_name": "ExecutionResult",
        "label": "Run Day",
    },
    "runstate": {
        "patterns": ["runstate.md"],
        "artifact_name": "RunState",
        "label": "RunState",
    },
}

CANONICAL_LOOP_ORDER = ["plan", "run", "review"]

DAY_DETAIL_ORDER = ["review", "plan", "run"]


def detect_project_path(base_path: Path | None = None) -> Path:
    """Detect async-dev project directory with fallback."""
    if base_path is None:
        base_path = Path.cwd()

    projects_dir = base_path / "projects"
    if projects_dir.exists():
        for project in projects_dir.iterdir():
            if project.is_dir() and (project / "runstate.md").exists():
                return project

    if (base_path / "runstate.md").exists():
        return base_path

    raise ValueError(f"No async-dev project found in {base_path}")


def find_artifacts(project_path: Path, artifact_type: str) -> list[Path]:
    """Find artifact files with graceful handling."""
    artifacts = []

    if artifact_type not in ARTIFACT_TYPES:
        return artifacts

    patterns = ARTIFACT_TYPES[artifact_type]["patterns"]

    for pattern in patterns:
        if "*" in pattern:
            try:
                matches = list(project_path.glob(pattern))
                artifacts.extend(matches)
            except Exception:
                pass
        else:
            path = project_path / pattern
            if path.exists():
                artifacts.append(path)

    return sorted(artifacts, key=lambda p: p.stem)


def extract_yaml_block(content: str) -> dict[str, Any] | None:
    """Extract YAML block with fallback for malformed content."""
    if "```yaml" in content:
        start = content.find("```yaml")
        end = content.find("```", start + 7)
        if start != -1 and end != -1:
            yaml_content = content[start + 7:end].strip()
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                return None

    if content.startswith("---"):
        parts = content.split("---")
        if len(parts) >= 2:
            yaml_content = parts[1].strip()
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                return None

    return None


def safe_extract_date_from_exec_id(exec_id: str) -> str:
    """Extract date from execution_id with fallback."""
    if not exec_id:
        return ""
    if exec_id.startswith("exec-"):
        parts = exec_id.split("-")
        if len(parts) >= 2:
            date_part = parts[1]
            if len(date_part) == 8 and date_part.isdigit():
                return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    return ""


def parse_review_pack(path: Path) -> JournalEntry:
    """Parse DailyReviewPack with fallback handling."""
    try:
        content = path.read_text(encoding="utf-8")
        data = extract_yaml_block(content) or {}

        date_val = data.get("date", "")
        if not date_val:
            date_val = path.stem.replace("-review", "")

        return JournalEntry(
            timestamp=date_val,
            day=date_val,
            artifact_type="review",
            project_id=data.get("project_id", "") or data.get("product_id", ""),
            feature_id=data.get("feature_id", ""),
            title=f"Review Night - {date_val}",
            summary=data.get("today_goal", "Daily review pack")[:100] if data.get("today_goal") else "Daily review pack",
            key_fields={
                "completed_count": len(data.get("what_was_completed", [])),
                "blocked_count": len(data.get("blocked_items", [])),
                "decisions_count": len(data.get("decisions_needed", [])),
                "doctor_status": data.get("doctor_assessment", {}).get("doctor_status", "") if isinstance(data.get("doctor_assessment"), dict) else "",
            },
            source_path=str(path),
            parse_status="success",
        )
    except Exception as e:
        return JournalEntry(
            artifact_type="review",
            title=f"Parse Error - {path.stem}",
            summary=f"Could not read artifact: {str(e)[:50]}",
            source_path=str(path),
            parse_status="error",
            parse_warning=str(e),
        )


def parse_execution_pack(path: Path) -> JournalEntry:
    """Parse ExecutionPack with fallback handling."""
    try:
        content = path.read_text(encoding="utf-8")
        data = extract_yaml_block(content) or {}

        exec_id = data.get("execution_id", "")
        date_str = safe_extract_date_from_exec_id(exec_id)

        goal = data.get("goal", "")
        if goal:
            goal = goal[:80]

        return JournalEntry(
            timestamp=date_str,
            day=date_str,
            artifact_type="plan",
            project_id=data.get("project_id", "") or data.get("product_id", ""),
            feature_id=data.get("feature_id", ""),
            title=f"Plan Day - {goal[:50] if goal else 'Execution plan'}",
            summary=goal or "Daily execution pack",
            key_fields={
                "planning_mode": data.get("planning_mode", ""),
                "safe_to_execute": data.get("safe_to_execute", True),
                "estimated_scope": data.get("estimated_scope", ""),
                "prior_doctor_status": data.get("prior_doctor_status", ""),
            },
            source_path=str(path),
            parse_status="success",
        )
    except Exception as e:
        return JournalEntry(
            artifact_type="plan",
            title=f"Parse Error - {path.stem}",
            summary=f"Could not read artifact: {str(e)[:50]}",
            source_path=str(path),
            parse_status="error",
            parse_warning=str(e),
        )


def parse_execution_result(path: Path) -> JournalEntry:
    """Parse ExecutionResult with fallback handling."""
    try:
        content = path.read_text(encoding="utf-8")
        data = extract_yaml_block(content) or {}

        exec_id = data.get("execution_id", "")
        date_str = safe_extract_date_from_exec_id(exec_id)

        status = data.get("status", "unknown")

        return JournalEntry(
            timestamp=date_str,
            day=date_str,
            artifact_type="run",
            project_id=data.get("project_id", "") or data.get("product_id", ""),
            feature_id=data.get("feature_id", ""),
            title=f"Run Day - {status}",
            summary=f"Execution: {status}",
            key_fields={
                "status": status,
                "completed_count": len(data.get("completed_items", [])),
                "artifacts_count": len(data.get("artifacts_created", [])),
                "blocked_count": len(data.get("blocked_reasons", [])),
            },
            source_path=str(path),
            parse_status="success",
        )
    except Exception as e:
        return JournalEntry(
            artifact_type="run",
            title=f"Parse Error - {path.stem}",
            summary=f"Could not read artifact: {str(e)[:50]}",
            source_path=str(path),
            parse_status="error",
            parse_warning=str(e),
        )


def parse_runstate(path: Path) -> JournalEntry:
    """Parse RunState with fallback handling."""
    try:
        content = path.read_text(encoding="utf-8")
        data = extract_yaml_block(content) or {}

        updated_at = data.get("updated_at", "")
        day_val = updated_at[:10] if updated_at else ""

        return JournalEntry(
            timestamp=updated_at,
            day=day_val,
            artifact_type="runstate",
            project_id=data.get("project_id", "") or data.get("product_id", ""),
            feature_id=data.get("feature_id", ""),
            title=f"RunState - {data.get('current_phase', 'unknown')}",
            summary=f"Phase: {data.get('current_phase', 'unknown')}",
            key_fields={
                "current_phase": data.get("current_phase", ""),
                "active_task": data.get("active_task", "")[:50] if data.get("active_task") else "",
            },
            source_path=str(path),
            parse_status="success",
        )
    except Exception as e:
        return JournalEntry(
            artifact_type="runstate",
            title=f"Parse Error - runstate.md",
            summary=f"Could not read artifact: {str(e)[:50]}",
            source_path=str(path),
            parse_status="error",
            parse_warning=str(e),
        )


PARSERS = {
    "review": parse_review_pack,
    "plan": parse_execution_pack,
    "run": parse_execution_result,
    "runstate": parse_runstate,
}


def build_journal_timeline(project_path: Path) -> tuple[list[JournalEntry], list[str]]:
    """Build journal timeline with warnings for missing/partial artifacts.
    
    Returns:
        tuple: (entries, warnings)
    """
    entries = []
    warnings = []

    if not project_path.exists():
        warnings.append(f"Project path does not exist: {project_path}")
        return entries, warnings

    for artifact_type in CANONICAL_LOOP_ORDER:
        artifacts = find_artifacts(project_path, artifact_type)
        parser = PARSERS.get(artifact_type)

        if not artifacts:
            warnings.append(f"No {artifact_type} artifacts found")

        if parser:
            for artifact in artifacts:
                entry = parser(artifact)
                entries.append(entry)
                if entry.parse_status == "error":
                    warnings.append(f"Failed to parse {artifact.name}: {entry.parse_warning}")
                elif not entry.project_id:
                    warnings.append(f"{artifact.name}: missing project_id")
                elif not entry.feature_id:
                    pass

    entries.sort(key=lambda e: (e.day or "zzz", CANONICAL_LOOP_ORDER.index(e.artifact_type) if e.artifact_type in CANONICAL_LOOP_ORDER else 99))

    return entries, warnings


def get_artifact_summary(project_path: Path) -> dict[str, int]:
    """Get count of each artifact type."""
    summary = {}
    for artifact_type in CANONICAL_LOOP_ORDER:
        artifacts = find_artifacts(project_path, artifact_type)
        summary[artifact_type] = len(artifacts)
    return summary