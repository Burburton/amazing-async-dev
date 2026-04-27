"""Latest Pointer Files - Feature 067 hardening (C-006).

Provides canonical pointer files for latest artifacts, avoiding
repeated glob + mtime scanning.

Pointer files are small markdown files that point to the latest artifact:
- latest-execution-result.md
- latest-acceptance-result.md
- latest-observer-findings.md

This enables faster latest-truth resolution without filesystem scanning.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

POINTER_FILES = {
    "execution_result": "latest-execution-result.md",
    "execution_pack": "latest-execution-pack.md",
    "acceptance_result": "latest-acceptance-result.md",
    "acceptance_pack": "latest-acceptance-pack.md",
    "observer_findings": "latest-observer-findings.md",
    "acceptance_recovery_pack": "latest-acceptance-recovery-pack.md",
}


def create_latest_pointer(
    project_path: Path,
    pointer_type: str,
    target_id: str,
    target_path: Path,
) -> Path:
    """Create or update a latest pointer file.
    
    Args:
        project_path: Project directory path
        pointer_type: Type of artifact (execution_result, acceptance_result, etc.)
        target_id: ID of the target artifact
        target_path: Full path to target artifact
        
    Returns:
        Path to created pointer file
    """
    pointer_filename = POINTER_FILES.get(pointer_type)
    if not pointer_filename:
        raise ValueError(f"Unknown pointer type: {pointer_type}")
    
    pointer_path = project_path / pointer_filename
    
    relative_path = target_path.relative_to(project_path)
    
    content = f"""# Latest {pointer_type.replace('_', ' ').title()} Pointer

```yaml
pointer_type: {pointer_type}
target_id: {target_id}
target_path: {relative_path}
updated_at: {datetime.now().isoformat()}
```

**Target**: [{target_path.name}]({relative_path})
"""
    
    pointer_path.write_text(content, encoding="utf-8")
    return pointer_path


def read_latest_pointer(project_path: Path, pointer_type: str) -> tuple[str, Path | None]:
    """Read latest pointer file and resolve target.
    
    Args:
        project_path: Project directory path
        pointer_type: Type of artifact
        
    Returns:
        Tuple of (target_id, target_path) or ("", None) if not found
    """
    pointer_filename = POINTER_FILES.get(pointer_type)
    if not pointer_filename:
        return "", None
    
    pointer_path = project_path / pointer_filename
    
    if not pointer_path.exists():
        return "", None
    
    content = pointer_path.read_text(encoding="utf-8")
    
    target_id = ""
    target_path_str = ""
    
    for line in content.split("\n"):
        if line.startswith("target_id:"):
            target_id = line.split(":", 1)[1].strip()
        elif line.startswith("target_path:"):
            target_path_str = line.split(":", 1)[1].strip()
    
    if target_id and target_path_str:
        target_path = project_path / target_path_str
        if target_path.exists():
            return target_id, target_path
    
    return "", None


def update_pointer_after_execution_result(project_path: Path, execution_id: str) -> Path | None:
    """Update execution result pointer after saving new result.
    
    Args:
        project_path: Project directory path
        execution_id: Execution result ID
        
    Returns:
        Path to pointer file or None if target not found
    """
    from runtime.artifact_router import get_execution_result_path
    
    target_path = get_execution_result_path(project_path, execution_id)
    
    if not target_path.exists():
        return None
    
    return create_latest_pointer(
        project_path,
        "execution_result",
        execution_id,
        target_path,
    )


def update_pointer_after_execution_pack(project_path: Path, execution_id: str) -> Path | None:
    """Update execution pack pointer after saving new pack."""
    from runtime.artifact_router import get_execution_pack_path
    
    target_path = get_execution_pack_path(project_path, execution_id)
    
    if not target_path.exists():
        return None
    
    return create_latest_pointer(
        project_path,
        "execution_pack",
        execution_id,
        target_path,
    )


def update_pointer_after_acceptance_result(project_path: Path, result_id: str) -> Path | None:
    """Update acceptance result pointer after saving new result."""
    from runtime.artifact_router import get_acceptance_result_path
    
    target_path = get_acceptance_result_path(project_path, result_id)
    
    if not target_path.exists():
        return None
    
    return create_latest_pointer(
        project_path,
        "acceptance_result",
        result_id,
        target_path,
    )


def update_pointer_after_observer_findings(project_path: Path, observation_id: str) -> Path | None:
    """Update observer findings pointer after saving new findings."""
    from runtime.artifact_router import get_observer_findings_path
    
    target_path = get_observer_findings_path(project_path, observation_id)
    
    if not target_path.exists():
        return None
    
    return create_latest_pointer(
        project_path,
        "observer_findings",
        observation_id,
        target_path,
    )


def update_pointer_after_acceptance_recovery_pack(project_path: Path, pack_id: str) -> Path | None:
    """Update acceptance recovery pack pointer after saving new pack."""
    from runtime.artifact_router import get_acceptance_recovery_pack_path
    
    target_path = get_acceptance_recovery_pack_path(project_path, pack_id)
    
    if not target_path.exists():
        return None
    
    return create_latest_pointer(
        project_path,
        "acceptance_recovery_pack",
        pack_id,
        target_path,
    )


def get_all_pointers(project_path: Path) -> dict[str, tuple[str, Path | None]]:
    """Get all pointer states for a project.
    
    Args:
        project_path: Project directory path
        
    Returns:
        Dict mapping pointer_type to (target_id, target_path)
    """
    result = {}
    
    for pointer_type in POINTER_FILES:
        target_id, target_path = read_latest_pointer(project_path, pointer_type)
        result[pointer_type] = (target_id, target_path)
    
    return result


def pointer_exists(project_path: Path, pointer_type: str) -> bool:
    """Check if a pointer file exists.
    
    Args:
        project_path: Project directory path
        pointer_type: Type of artifact
        
    Returns:
        True if pointer exists
    """
    pointer_filename = POINTER_FILES.get(pointer_type)
    if not pointer_filename:
        return False
    
    return (project_path / pointer_filename).exists()


def delete_pointer(project_path: Path, pointer_type: str) -> bool:
    """Delete a pointer file.
    
    Args:
        project_path: Project directory path
        pointer_type: Type of artifact
        
    Returns:
        True if deleted, False if didn't exist
    """
    pointer_filename = POINTER_FILES.get(pointer_type)
    if not pointer_filename:
        return False
    
    pointer_path = project_path / pointer_filename
    
    if pointer_path.exists():
        pointer_path.unlink()
        return True
    
    return False