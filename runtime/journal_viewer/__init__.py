"""Journal Viewer V1.3 - Scoped views: project, feature, day."""

from runtime.journal_viewer.artifact_reader import (
    JournalEntry,
    build_journal_timeline,
    detect_project_path,
    find_artifacts,
    get_artifact_summary,
    CANONICAL_LOOP_ORDER,
    DAY_DETAIL_ORDER,
)
from runtime.journal_viewer.tui_viewer import (
    display_timeline_tui,
    display_day_detail,
    display_feature_timeline,
    display_project_summary,
    display_stats,
    interactive_viewer,
    filter_entries_strict,
    group_entries_by_feature,
    get_available_features,
)

__all__ = [
    "JournalEntry",
    "build_journal_timeline",
    "detect_project_path",
    "find_artifacts",
    "get_artifact_summary",
    "CANONICAL_LOOP_ORDER",
    "DAY_DETAIL_ORDER",
    "display_timeline_tui",
    "display_day_detail",
    "display_feature_timeline",
    "display_project_summary",
    "display_stats",
    "interactive_viewer",
    "filter_entries_strict",
    "group_entries_by_feature",
    "get_available_features",
]