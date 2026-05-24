"""Artifact link builder for Feature 081.

Provides utilities for building links to async-dev artifacts.
"""

from pathlib import Path
from typing import Any


def build_artifact_link(
    artifact_type: str,
    artifact_id: str,
    base_url: str = "https://async-dev.example.com",
) -> str:
    """Build a link to an artifact.

    Args:
        artifact_type: Type of artifact (execution_result, review_pack, acceptance_result, runstate)
        artifact_id: ID of the artifact
        base_url: Base URL for links

    Returns:
        URL to the artifact
    """
    routes = {
        "execution_result": f"{base_url}/execution/{artifact_id}",
        "execution-result": f"{base_url}/execution/{artifact_id}",
        "review_pack": f"{base_url}/review/{artifact_id}",
        "review-pack": f"{base_url}/review/{artifact_id}",
        "review": f"{base_url}/review/{artifact_id}",
        "acceptance_result": f"{base_url}/acceptance/{artifact_id}",
        "acceptance-result": f"{base_url}/acceptance/{artifact_id}",
        "acceptance": f"{base_url}/acceptance/{artifact_id}",
        "runstate": f"{base_url}/project/{artifact_id}/runstate",
        "run_state": f"{base_url}/project/{artifact_id}/runstate",
        "execution_pack": f"{base_url}/pack/{artifact_id}",
        "execution-pack": f"{base_url}/pack/{artifact_id}",
        "pack": f"{base_url}/pack/{artifact_id}",
    }

    return routes.get(artifact_type, f"{base_url}/{artifact_type}/{artifact_id}")


def build_artifact_links(
    artifacts: list[dict[str, Any]],
    base_url: str = "https://async-dev.example.com",
) -> list[dict[str, str]]:
    """Build links for multiple artifacts.

    Args:
        artifacts: List of artifact dicts with 'type' and 'id' or 'path'
        base_url: Base URL for links

    Returns:
        List of dicts with 'name' and 'url' keys
    """
    links = []
    for artifact in artifacts:
        artifact_type = artifact.get("type", "file")
        artifact_id = artifact.get("id", artifact.get("path", "unknown"))

        url = build_artifact_link(artifact_type, artifact_id, base_url)
        name = artifact.get("name", artifact.get("path", artifact_id))

        links.append({"name": name, "url": url})

    return links


def get_default_artifact_links(
    project_id: str,
    execution_id: str | None = None,
) -> list[dict[str, str]]:
    """Get default artifact links for a project/execution.

    Args:
        project_id: Project ID
        execution_id: Optional execution ID

    Returns:
        List of common artifact links
    """
    base_url = "https://async-dev.example.com"
    links = [
        {"name": "RunState", "url": f"{base_url}/project/{project_id}/runstate"},
    ]

    if execution_id:
        links.append({
            "name": f"Execution {execution_id}",
            "url": f"{base_url}/execution/{execution_id}",
        })

    links.append({
        "name": "Project Home",
        "url": f"{base_url}/project/{project_id}",
    })

    return links
