"""Archive query module - loading and filtering archive packs.

Feature 014: Archive Query / History Inspection

This module provides the data layer for querying archived features:
- Load archive packs from YAML files (primary source)
- Use SQLite for fast metadata filtering (secondary)
- Support filters: product, recent, has-patterns, has-lessons
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def load_archive_pack(archive_path: Path) -> dict[str, Any] | None:
    """Load ArchivePack from YAML file.
    
    Args:
        archive_path: Path to archive-pack.yaml
        
    Returns:
        ArchivePack dict or None if not found
    """
    if not archive_path.exists():
        return None
    
    with open(archive_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def discover_all_archives(projects_path: Path) -> list[dict[str, Any]]:
    """Discover all archive packs across all products.
    
    Scans the projects directory for archive directories and loads
    all archive-pack.yaml files.
    
    Args:
        projects_path: Root projects directory
        
    Returns:
        List of archive pack dicts with metadata
    """
    archives = []
    
    if not projects_path.exists():
        return archives
    
    for product_dir in projects_path.iterdir():
        if not product_dir.is_dir():
            continue
        if product_dir.name.startswith("."):
            continue
        
        archive_dir = product_dir / "archive"
        if not archive_dir.exists():
            continue
        
        for feature_dir in archive_dir.iterdir():
            if not feature_dir.is_dir():
                continue
            
            archive_path = feature_dir / "archive-pack.yaml"
            pack = load_archive_pack(archive_path)
            
            if pack:
                archives.append({
                    "feature_id": pack.get("feature_id", feature_dir.name),
                    "product_id": pack.get("product_id", product_dir.name),
                    "title": pack.get("title", feature_dir.name),
                    "final_status": pack.get("final_status", "unknown"),
                    "archived_at": pack.get("archived_at", ""),
                    "has_patterns": len(pack.get("reusable_patterns", [])) > 0,
                    "has_lessons": len(pack.get("lessons_learned", [])) > 0,
                    "patterns_count": len(pack.get("reusable_patterns", [])),
                    "lessons_count": len(pack.get("lessons_learned", [])),
                    "archive_path": str(archive_path),
                    "pack": pack,
                })
    
    return archives


def filter_archives(
    archives: list[dict[str, Any]],
    product: str | None = None,
    recent: bool = False,
    has_patterns: bool = False,
    has_lessons: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Filter archive list based on criteria.
    
    Args:
        archives: List of archive metadata dicts
        product: Filter by product ID
        recent: Sort by archived_at descending
        has_patterns: Only archives with reusable patterns
        has_lessons: Only archives with lessons learned
        limit: Maximum number of results
        
    Returns:
        Filtered list of archive metadata dicts
    """
    result = archives
    
    if product:
        result = [a for a in result if a.get("product_id") == product]
    
    if has_patterns:
        result = [a for a in result if a.get("has_patterns", False)]
    
    if has_lessons:
        result = [a for a in result if a.get("has_lessons", False)]
    
    if recent:
        result = sorted(
            result,
            key=lambda a: a.get("archived_at", ""),
            reverse=True,
        )
    
    if limit and limit > 0:
        result = result[:limit]
    
    return result


def get_archive_detail(
    projects_path: Path,
    feature_id: str,
    product_id: str | None = None,
) -> dict[str, Any] | None:
    """Get detailed archive pack for a specific feature.
    
    Args:
        projects_path: Root projects directory
        feature_id: Feature ID to inspect
        product_id: Product ID (optional, helps locate faster)
        
    Returns:
        Full archive pack dict with detail metadata, or None
    """
    if product_id:
        archive_path = projects_path / product_id / "archive" / feature_id / "archive-pack.yaml"
        pack = load_archive_pack(archive_path)
        if pack:
            return enrich_archive_detail(pack, archive_path)
    
    archives = discover_all_archives(projects_path)
    for archive in archives:
        if archive.get("feature_id") == feature_id:
            return enrich_archive_detail(archive.get("pack", {}), Path(archive.get("archive_path", "")))
    
    return None


def enrich_archive_detail(pack: dict[str, Any], archive_path: Path) -> dict[str, Any]:
    """Enrich archive pack with additional detail metadata.
    
    Args:
        pack: ArchivePack dict
        archive_path: Path to archive-pack.yaml
        
    Returns:
        Enriched archive detail dict
    """
    return {
        "feature_id": pack.get("feature_id", ""),
        "product_id": pack.get("product_id", ""),
        "title": pack.get("title", ""),
        "final_status": pack.get("final_status", "unknown"),
        "archived_at": pack.get("archived_at", ""),
        "delivered_outputs": pack.get("delivered_outputs", []),
        "acceptance_result": pack.get("acceptance_result", {}),
        "unresolved_followups": pack.get("unresolved_followups", []),
        "decisions_made": pack.get("decisions_made", []),
        "lessons_learned": pack.get("lessons_learned", []),
        "reusable_patterns": pack.get("reusable_patterns", []),
        "artifact_links": pack.get("artifact_links", []),
        "has_patterns": len(pack.get("reusable_patterns", [])) > 0,
        "has_lessons": len(pack.get("lessons_learned", [])) > 0,
        "patterns_count": len(pack.get("reusable_patterns", [])),
        "lessons_count": len(pack.get("lessons_learned", [])),
        "archive_path": str(archive_path),
        "historical_notes": pack.get("historical_notes", ""),
        "backfilled": pack.get("archived_via_backfill", False),
    }


def get_lessons_summary(archive_detail: dict[str, Any]) -> list[dict[str, str]]:
    """Extract lessons learned from archive detail.
    
    Args:
        archive_detail: Enriched archive detail dict
        
    Returns:
        List of lesson dicts with 'lesson' and 'context' keys
    """
    return archive_detail.get("lessons_learned", [])


def get_patterns_summary(archive_detail: dict[str, Any]) -> list[dict[str, str]]:
    """Extract reusable patterns from archive detail.
    
    Args:
        archive_detail: Enriched archive detail dict
        
    Returns:
        List of pattern dicts with 'pattern' and 'applicability' keys
    """
    return archive_detail.get("reusable_patterns", [])


def list_archives_with_patterns(projects_path: Path) -> list[dict[str, Any]]:
    """List all archives that have reusable patterns.
    
    Args:
        projects_path: Root projects directory
        
    Returns:
        List of archive metadata dicts with patterns
    """
    archives = discover_all_archives(projects_path)
    return filter_archives(archives, has_patterns=True)


def list_archives_with_lessons(projects_path: Path) -> list[dict[str, Any]]:
    """List all archives that have lessons learned.
    
    Args:
        projects_path: Root projects directory
        
    Returns:
        List of archive metadata dicts with lessons
    """
    archives = discover_all_archives(projects_path)
    return filter_archives(archives, has_lessons=True)


def get_recent_archives(projects_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    """Get most recently archived features.
    
    Args:
        projects_path: Root projects directory
        limit: Maximum number to return
        
    Returns:
        List of archive metadata dicts sorted by archived_at desc
    """
    archives = discover_all_archives(projects_path)
    return filter_archives(archives, recent=True, limit=limit)