"""Loop Journal Viewer - Artifact detection and reading module.

Day 1: Artifact Reader for dogfooding async-dev loop.
"""

from pathlib import Path
from typing import Any
import yaml
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JournalEntry:
    """Normalized journal entry from an async-dev artifact."""
    timestamp: str = ""
    day: str = ""
    artifact_type: str = ""  # review, resume, plan, run
    project: str = ""
    feature: str = ""
    title: str = ""
    summary: str = ""
    key_fields: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""


ARTIFACT_TYPES = {
    "review": {
        "patterns": ["reviews/*-review.md", "reviews/YYYY-MM-DD-review.md"],
        "artifact_name": "DailyReviewPack",
    },
    "plan": {
        "patterns": ["execution-packs/exec-*.md"],
        "artifact_name": "ExecutionPack",
    },
    "run": {
        "patterns": ["execution-results/exec-*.md"],
        "artifact_name": "ExecutionResult",
    },
    "runstate": {
        "patterns": ["runstate.md"],
        "artifact_name": "RunState",
    },
}


def detect_project_path(base_path: Path | None = None) -> Path:
    """Detect the async-dev project directory.
    
    Looks for:
    - projects/ directory with runstate.md
    - Current directory if it contains runstate.md
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Check if current dir has projects/
    projects_dir = base_path / "projects"
    if projects_dir.exists():
        # Find projects with runstate.md
        for project in projects_dir.iterdir():
            if project.is_dir() and (project / "runstate.md").exists():
                return project
    
    # Check if current dir is a project
    if (base_path / "runstate.md").exists():
        return base_path
    
    raise ValueError(f"No async-dev project found in {base_path}")


def find_artifacts(project_path: Path, artifact_type: str) -> list[Path]:
    """Find artifact files of a specific type in a project."""
    artifacts = []
    
    if artifact_type not in ARTIFACT_TYPES:
        return artifacts
    
    patterns = ARTIFACT_TYPES[artifact_type]["patterns"]
    
    for pattern in patterns:
        # Handle glob patterns
        if "*" in pattern:
            matches = list(project_path.glob(pattern))
            artifacts.extend(matches)
        else:
            path = project_path / pattern
            if path.exists():
                artifacts.append(path)
    
    return sorted(artifacts, key=lambda p: p.stem)


def extract_yaml_block(content: str) -> dict[str, Any] | None:
    """Extract YAML block from markdown content.
    
    Handles both ```yaml and --- delimiters.
    """
    # Try ```yaml block first
    if "```yaml" in content:
        start = content.find("```yaml")
        end = content.find("```", start + 7)
        if start != -1 and end != -1:
            yaml_content = content[start + 7:end].strip()
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                return None
    
    # Try --- delimited YAML
    if content.startswith("---"):
        parts = content.split("---")
        if len(parts) >= 2:
            yaml_content = parts[1].strip()
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                return None
    
    return None


def parse_review_pack(path: Path) -> JournalEntry:
    """Parse a DailyReviewPack into a JournalEntry."""
    content = path.read_text(encoding="utf-8")
    data = extract_yaml_block(content) or {}
    
    entry = JournalEntry(
        timestamp=data.get("date", ""),
        day=data.get("date", ""),
        artifact_type="review",
        project=data.get("project_id", ""),
        feature=data.get("feature_id", ""),
        title=f"Review Night - {data.get('date', path.stem)}",
        summary=data.get("today_goal", "Daily review pack"),
        key_fields={
            "completed_count": len(data.get("what_was_completed", [])),
            "blocked_count": len(data.get("blocked_items", [])),
            "decisions_count": len(data.get("decisions_needed", [])),
            "doctor_status": data.get("doctor_status", ""),
        },
        source_path=str(path),
    )
    
    return entry


def parse_execution_pack(path: Path) -> JournalEntry:
    """Parse an ExecutionPack into a JournalEntry."""
    content = path.read_text(encoding="utf-8")
    data = extract_yaml_block(content) or {}
    
    # Extract date from execution_id (exec-YYYYMMDD-###)
    exec_id = data.get("execution_id", "")
    date_str = ""
    if exec_id.startswith("exec-"):
        date_part = exec_id.split("-")[1]
        if len(date_part) == 8:
            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    
    entry = JournalEntry(
        timestamp=date_str,
        day=date_str,
        artifact_type="plan",
        project=data.get("project_id", ""),
        feature=data.get("feature_id", ""),
        title=f"Plan Day - {data.get('goal', 'Execution plan')[:50]}",
        summary=data.get("goal", "Daily execution pack"),
        key_fields={
            "planning_mode": data.get("planning_mode", ""),
            "safe_to_execute": data.get("safe_to_execute", True),
            "estimated_scope": data.get("estimated_scope", ""),
            "task_scope": data.get("task_scope", []),
        },
        source_path=str(path),
    )
    
    return entry


def parse_execution_result(path: Path) -> JournalEntry:
    """Parse an ExecutionResult into a JournalEntry."""
    content = path.read_text(encoding="utf-8")
    data = extract_yaml_block(content) or {}
    
    # Extract date from execution_id
    exec_id = data.get("execution_id", "")
    date_str = ""
    if exec_id.startswith("exec-"):
        date_part = exec_id.split("-")[1]
        if len(date_part) == 8:
            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    
    entry = JournalEntry(
        timestamp=date_str,
        day=date_str,
        artifact_type="run",
        project=data.get("project_id", ""),
        feature=data.get("feature_id", ""),
        title=f"Run Day - {data.get('status', 'unknown')}",
        summary=f"Execution: {data.get('status', 'unknown')}",
        key_fields={
            "status": data.get("status", ""),
            "completed_items": data.get("completed_items", []),
            "artifacts_count": len(data.get("artifacts_created", [])),
            "blocked_reasons": data.get("blocked_reasons", []),
        },
        source_path=str(path),
    )
    
    return entry


def parse_runstate(path: Path) -> JournalEntry:
    """Parse RunState into a JournalEntry."""
    content = path.read_text(encoding="utf-8")
    data = extract_yaml_block(content) or {}
    
    entry = JournalEntry(
        timestamp=data.get("updated_at", ""),
        day=data.get("updated_at", "")[:10] if data.get("updated_at") else "",
        artifact_type="runstate",
        project=data.get("project_id", ""),
        feature=data.get("feature_id", ""),
        title=f"RunState - {data.get('current_phase', 'unknown')}",
        summary=f"Phase: {data.get('current_phase', 'unknown')} - {data.get('active_task', '')}",
        key_fields={
            "current_phase": data.get("current_phase", ""),
            "active_task": data.get("active_task", ""),
            "task_queue": data.get("task_queue", []),
            "blocked_items": data.get("blocked_items", []),
        },
        source_path=str(path),
    )
    
    return entry


PARSERS = {
    "review": parse_review_pack,
    "plan": parse_execution_pack,
    "run": parse_execution_result,
    "runstate": parse_runstate,
}


def build_journal_timeline(project_path: Path) -> list[JournalEntry]:
    """Build a complete journal timeline from a project's artifacts."""
    entries = []
    
    for artifact_type in ["review", "plan", "run"]:
        artifacts = find_artifacts(project_path, artifact_type)
        parser = PARSERS.get(artifact_type)
        
        if parser:
            for artifact in artifacts:
                try:
                    entry = parser(artifact)
                    entries.append(entry)
                except Exception as e:
                    # Record failure as friction
                    entries.append(JournalEntry(
                        artifact_type=artifact_type,
                        title=f"Failed to parse {artifact.stem}",
                        summary=f"Error: {str(e)}",
                        source_path=str(artifact),
                    ))
    
    # Sort by timestamp/day
    entries.sort(key=lambda e: (e.day, e.artifact_type))
    
    return entries


def display_timeline(entries: list[JournalEntry]) -> None:
    """Display journal timeline to console."""
    print("\n" + "=" * 60)
    print("LOOP JOURNAL TIMELINE")
    print("=" * 60)
    
    for entry in entries:
        print(f"\n[{entry.artifact_type.upper()}] {entry.day}")
        print(f"  Title: {entry.title}")
        print(f"  Summary: {entry.summary}")
        if entry.key_fields:
            print("  Key Fields:")
            for k, v in entry.key_fields.items():
                if isinstance(v, list):
                    print(f"    - {k}: {len(v)} items")
                else:
                    print(f"    - {k}: {v}")
        print(f"  Source: {entry.source_path}")
    
    print("\n" + "=" * 60)


# CLI entry point
def main():
    """Run the loop journal viewer."""
    import sys
    
    project_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    if project_arg:
        project_path = Path(project_arg)
    else:
        try:
            project_path = detect_project_path()
        except ValueError as e:
            print(f"Error: {e}")
            print("Usage: python -m viewer <project_path>")
            sys.exit(1)
    
    print(f"Project: {project_path}")
    
    entries = build_journal_timeline(project_path)
    display_timeline(entries)
    
    print(f"\nTotal entries: {len(entries)}")


if __name__ == "__main__":
    main()