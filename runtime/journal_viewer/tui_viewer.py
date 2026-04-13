"""TUI Timeline Display - V1.3 Scoped Views.

Primary experience for viewing async-dev loop artifacts.
"""

from pathlib import Path
from typing import Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from runtime.journal_viewer.artifact_reader import (
    JournalEntry,
    build_journal_timeline,
    detect_project_path,
    find_artifacts,
    get_artifact_summary,
    CANONICAL_LOOP_ORDER,
    DAY_DETAIL_ORDER,
)


console = Console()

ARTIFACT_LABELS = {
    "review": "Review Night",
    "plan": "Plan Day",
    "run": "Run Day",
    "runstate": "RunState",
}

ARTIFACT_COLORS = {
    "review": "green",
    "plan": "blue",
    "run": "yellow",
    "runstate": "cyan",
}


def filter_entries(
    entries: list[JournalEntry],
    feature: str | None = None,
    project: str | None = None,
    artifact_type: str | None = None,
) -> list[JournalEntry]:
    """Filter journal entries."""
    filtered = entries

    if feature:
        filtered = [e for e in filtered if e.feature_id == feature or not e.feature_id]

    if project:
        filtered = [e for e in filtered if e.project_id == project]

    if artifact_type:
        filtered = [e for e in filtered if e.artifact_type == artifact_type]

    return filtered


def filter_entries_strict(
    entries: list[JournalEntry],
    feature: str | None = None,
    project: str | None = None,
) -> list[JournalEntry]:
    """Filter entries with strict matching for scoped views."""
    filtered = entries

    if feature:
        filtered = [e for e in filtered if e.feature_id == feature]

    if project:
        filtered = [e for e in filtered if e.project_id == project]

    return filtered


def group_entries_by_day(entries: list[JournalEntry]) -> dict[str, list[JournalEntry]]:
    """Group journal entries by day."""
    grouped: dict[str, list[JournalEntry]] = {}

    for entry in entries:
        day = entry.day or "unknown"
        if day not in grouped:
            grouped[day] = []
        grouped[day].append(entry)

    return grouped


def group_entries_by_feature(entries: list[JournalEntry]) -> dict[str, list[JournalEntry]]:
    """Group journal entries by feature ID.

    V1.3: Used for feature-focused view. Entries without feature_id
    go into 'unassigned' group.
    """
    grouped: dict[str, list[JournalEntry]] = {}

    for entry in entries:
        feature = entry.feature_id or "unassigned"
        if feature not in grouped:
            grouped[feature] = []
        grouped[feature].append(entry)

    return grouped


def get_available_features(project_path: Path) -> list[str]:
    """Get list of feature IDs found in project artifacts.

    V1.3: Used to show available features for feature-focused view.
    """
    entries, _ = build_journal_timeline(project_path)
    features = set()
    for entry in entries:
        if entry.feature_id:
            features.add(entry.feature_id)
    return sorted(features)


def render_entry_detail(entry: JournalEntry) -> Panel:
    """Render detailed view of a journal entry."""
    content_lines = [
        f"[bold]Title:[/bold] {entry.title}",
        f"[bold]Summary:[/bold] {entry.summary}",
    ]

    if entry.project_id:
        content_lines.append(f"[bold]Project:[/bold] {entry.project_id}")
    if entry.feature_id:
        content_lines.append(f"[bold]Feature:[/bold] {entry.feature_id}")

    if entry.key_fields:
        content_lines.append("[bold]Key Fields:[/bold]")
        for k, v in entry.key_fields.items():
            if isinstance(v, list):
                content_lines.append(f"  • {k}: {len(v)} items")
            elif v:
                content_lines.append(f"  • {k}: {v}")

    content_lines.append(f"[bold]Source:[/bold] {entry.source_path}")

    type_color = ARTIFACT_COLORS.get(entry.artifact_type, "white")
    artifact_label = ARTIFACT_LABELS.get(entry.artifact_type, entry.artifact_type.upper())

    status_style = "" if entry.parse_status == "success" else "[red]"
    return Panel(
        "\n".join(content_lines),
        title=f"[{type_color}]{artifact_label}[/{type_color}] - {entry.day}",
        border_style=type_color if entry.parse_status == "success" else "red",
    )


def render_timeline_table(entries: list[JournalEntry]) -> Table:
    """Render timeline as Rich table - canonical primary view."""
    table = Table(title="Canonical Loop Timeline", show_header=True)

    table.add_column("Day", style="cyan", width=12)
    table.add_column("Phase", style="bold", width=12)
    table.add_column("Title", style="white", width=40)
    table.add_column("Summary", style="dim", width=50)
    table.add_column("Source", style="dim", width=20)

    for entry in entries:
        type_color = ARTIFACT_COLORS.get(entry.artifact_type, "white")
        artifact_label = ARTIFACT_LABELS.get(entry.artifact_type, entry.artifact_type.upper())

        summary_preview = entry.summary[:50] + "..." if len(entry.summary) > 50 else entry.summary
        source_preview = Path(entry.source_path).name

        status_marker = "" if entry.parse_status == "success" else "[red]⚠[/red] "

        table.add_row(
            entry.day or "unknown",
            f"[{type_color}]{artifact_label}[/{type_color}]",
            status_marker + entry.title[:40],
            summary_preview,
            source_preview,
        )

    return table


def render_warnings(warnings: list[str]) -> None:
    """Display warnings for missing/partial artifacts."""
    if not warnings:
        return

    console.print("\n[yellow]Warnings:[/yellow]")
    for warning in warnings:
        console.print(f"  [yellow]•[/yellow] {warning}")


def display_timeline_tui(
    project_path: Path,
    feature_filter: str | None = None,
    project_filter: str | None = None,
    artifact_type_filter: str | None = None,
    detailed: bool = False,
    show_warnings: bool = True,
) -> None:
    """Display canonical timeline - primary view for V1.1."""
    console.print(f"\n[bold cyan]Loop Journal Viewer V1.1[/bold cyan]")
    console.print(f"[dim]Project: {project_path}[/dim]")

    entries, warnings = build_journal_timeline(project_path)

    if feature_filter or project_filter or artifact_type_filter:
        console.print(f"[dim]Filters: feature={feature_filter}, project={project_filter}, type={artifact_type_filter}[/dim]")
        entries = filter_entries(entries, feature_filter, project_filter, artifact_type_filter)

    summary = get_artifact_summary(project_path)
    console.print(f"\n[dim]Artifacts: review={summary.get('review', 0)}, plan={summary.get('plan', 0)}, run={summary.get('run', 0)}[/dim]")

    console.print(f"\n[bold]Timeline entries: {len(entries)}[/bold]\n")

    if detailed:
        for entry in entries:
            console.print(render_entry_detail(entry))
    else:
        console.print(render_timeline_table(entries))

    grouped = group_entries_by_day(entries)
    console.print(f"\n[bold]Days covered: {len(grouped)}[/bold]")

    if show_warnings and warnings:
        render_warnings(warnings)

    error_count = sum(1 for e in entries if e.parse_status == "error")
    if error_count:
        console.print(f"\n[red]Parse errors: {error_count}[/red]")


def display_day_detail(project_path: Path, day: str) -> None:
    """Display detailed view for a specific day in canonical loop order.

    V1.2: Organizes entries in review → plan → run order with graceful
    handling for missing artifact types.
    """
    entries, warnings = build_journal_timeline(project_path)
    grouped = group_entries_by_day(entries)

    if day not in grouped:
        console.print(f"[red]Day not found: {day}[/red]")
        available_days = sorted(grouped.keys())
        if available_days:
            console.print(f"[dim]Available days: {', '.join(available_days[:10])}[/dim]")
        else:
            console.print("[dim]No days available in this project[/dim]")
        return

    day_entries = grouped[day]
    console.print(f"\n[bold cyan]Day: {day}[/bold cyan]")
    console.print(f"[dim]Total entries: {len(day_entries)}[/dim]\n")

    entries_by_type: dict[str, list[JournalEntry]] = {}
    for entry in day_entries:
        artifact_type = entry.artifact_type
        if artifact_type not in entries_by_type:
            entries_by_type[artifact_type] = []
        entries_by_type[artifact_type].append(entry)

    displayed_count = 0
    for artifact_type in DAY_DETAIL_ORDER:
        type_color = ARTIFACT_COLORS.get(artifact_type, "white")
        artifact_label = ARTIFACT_LABELS.get(artifact_type, artifact_type.upper())

        if artifact_type in entries_by_type and entries_by_type[artifact_type]:
            console.print(f"[bold {type_color}]━━━ {artifact_label} ━━━[/bold {type_color}]")
            for entry in entries_by_type[artifact_type]:
                console.print(render_entry_detail(entry))
                displayed_count += 1
        else:
            console.print(f"[dim {type_color}]━━━ {artifact_label} ━━━[/dim {type_color}]")
            console.print(f"[dim]No {artifact_label} artifacts for this day[/dim]\n")

    other_types = [t for t in entries_by_type.keys() if t not in DAY_DETAIL_ORDER]
    for artifact_type in other_types:
        type_color = ARTIFACT_COLORS.get(artifact_type, "white")
        artifact_label = ARTIFACT_LABELS.get(artifact_type, artifact_type.upper())
        console.print(f"[bold {type_color}]━━━ {artifact_label} ━━━[/bold {type_color}]")
        for entry in entries_by_type[artifact_type]:
            console.print(render_entry_detail(entry))
            displayed_count += 1

    console.print(f"\n[dim]Displayed {displayed_count} entries for {day}[/dim]")


def display_feature_timeline(project_path: Path, feature_id: str) -> None:
    """Display feature-focused timeline showing evolution across days.

    V1.3: Shows the evolution of one feature across multiple days with
    graceful handling for partial metadata and unassigned entries.
    """
    entries, warnings = build_journal_timeline(project_path)

    feature_entries = filter_entries_strict(entries, feature=feature_id)

    if not feature_entries:
        console.print(f"[red]Feature not found: {feature_id}[/red]")
        available_features = get_available_features(project_path)
        if available_features:
            console.print(f"[dim]Available features: {', '.join(available_features[:10])}[/dim]")
        else:
            console.print("[dim]No feature metadata found in project artifacts[/dim]")
            console.print("[dim]Tip: Feature IDs are extracted from artifact YAML blocks[/dim]")
        return

    console.print(f"\n[bold cyan]Feature Timeline: {feature_id}[/bold cyan]")
    console.print(f"[dim]Project: {project_path}[/dim]")
    console.print(f"[dim]Total entries: {len(feature_entries)}[/dim]\n")

    grouped_by_day = group_entries_by_day(feature_entries)
    sorted_days = sorted(grouped_by_day.keys())

    for day in sorted_days:
        day_entries = grouped_by_day[day]
        console.print(f"\n[bold blue]━━━ {day} ({len(day_entries)} entries) ━━━[/bold blue]")

        entries_by_type: dict[str, list[JournalEntry]] = {}
        for entry in day_entries:
            artifact_type = entry.artifact_type
            if artifact_type not in entries_by_type:
                entries_by_type[artifact_type] = []
            entries_by_type[artifact_type].append(entry)

        for artifact_type in DAY_DETAIL_ORDER:
            if artifact_type in entries_by_type and entries_by_type[artifact_type]:
                type_color = ARTIFACT_COLORS.get(artifact_type, "white")
                artifact_label = ARTIFACT_LABELS.get(artifact_type, artifact_type.upper())
                console.print(f"[{type_color}]  {artifact_label}[/{type_color}]")
                for entry in entries_by_type[artifact_type]:
                    console.print(f"    [dim]{entry.title[:50]}[/dim]")

    console.print(f"\n[bold]Days covered: {len(sorted_days)}[/bold]")
    console.print(f"[dim]Feature evolution from {sorted_days[0]} to {sorted_days[-1]}[/dim]")


def display_project_summary(project_path: Path) -> None:
    """Display project-level summary with feature breakdown.

    V1.3: Shows overview of project artifacts with feature grouping.
    """
    entries, warnings = build_journal_timeline(project_path)

    console.print(f"\n[bold cyan]Project Summary: {project_path.name}[/bold cyan]")
    console.print(f"[dim]Path: {project_path}[/dim]\n")

    summary = get_artifact_summary(project_path)

    summary_table = Table(title="Artifact Counts by Type", show_header=True)
    summary_table.add_column("Type", style="bold")
    summary_table.add_column("Count", style="green")

    for artifact_type in CANONICAL_LOOP_ORDER:
        count = summary.get(artifact_type, 0)
        color = ARTIFACT_COLORS.get(artifact_type, "white")
        label = ARTIFACT_LABELS.get(artifact_type, artifact_type)
        summary_table.add_row(
            f"[{color}]{label}[/{color}]",
            str(count),
        )

    console.print(summary_table)

    grouped_by_feature = group_entries_by_feature(entries)
    features = [f for f in grouped_by_feature.keys() if f != "unassigned"]

    if features:
        console.print(f"\n[bold]Features found: {len(features)}[/bold]")
        feature_table = Table(title="Features", show_header=True)
        feature_table.add_column("Feature ID", style="cyan")
        feature_table.add_column("Entries", style="green")
        feature_table.add_column("Days", style="dim")

        for feature in sorted(features):
            feature_entries = grouped_by_feature[feature]
            days = set(e.day for e in feature_entries if e.day)
            feature_table.add_row(
                feature,
                str(len(feature_entries)),
                str(len(days)),
            )

        console.print(feature_table)
    else:
        console.print("\n[yellow]No feature metadata found[/yellow]")
        console.print("[dim]Feature IDs are extracted from artifact YAML blocks[/dim]")

    unassigned_count = len(grouped_by_feature.get("unassigned", []))
    if unassigned_count:
        console.print(f"\n[dim]{unassigned_count} entries without feature metadata[/dim]")


def display_stats(project_path: Path) -> None:
    """Display artifact statistics."""
    console.print(f"\n[bold cyan]Artifact Statistics[/bold cyan]")
    console.print(f"[dim]Project: {project_path}[/dim]\n")

    summary = get_artifact_summary(project_path)

    stats_table = Table(title="Artifact Counts", show_header=True)
    stats_table.add_column("Type", style="bold")
    stats_table.add_column("Label", style="cyan")
    stats_table.add_column("Count", style="green")

    for artifact_type in CANONICAL_LOOP_ORDER:
        count = summary.get(artifact_type, 0)
        label = ARTIFACT_LABELS.get(artifact_type, artifact_type)
        color = ARTIFACT_COLORS.get(artifact_type, "white")
        stats_table.add_row(
            f"[{color}]{artifact_type}[/{color}]",
            label,
            str(count),
        )

    console.print(stats_table)

    artifacts = find_artifacts(project_path, "review")
    if not artifacts:
        console.print("\n[yellow]No review artifacts found[/yellow]")
        console.print("[dim]Run 'asyncdev review-night generate' to create review packs[/dim]")


def interactive_viewer(project_path: Path) -> None:
    """Interactive viewer with canonical timeline as primary."""
    console.print(Panel(
        "[bold]Loop Journal Viewer V1.1[/bold]\n\n"
        "[bold]Primary Command:[/bold]\n"
        "  timeline - Show canonical timeline\n\n"
        "Other Commands:\n"
        "  day <date> - Show day detail\n"
        "  stats - Show artifact counts\n"
        "  filter --type <type> - Filter by artifact type\n"
        "  quit - Exit viewer",
        title="Help",
        border_style="blue",
    ))

    while True:
        try:
            command = console.input("\n[bold green]> [/bold green]").strip()
        except EOFError:
            break

        if command in ("quit", "exit", "q"):
            console.print("[dim]Goodbye[/dim]")
            break
        elif command in ("timeline", "t", ""):
            display_timeline_tui(project_path, detailed=False)
        elif command in ("timeline --detailed", "td"):
            display_timeline_tui(project_path, detailed=True)
        elif command.startswith("day "):
            day_arg = command.split(" ", 1)[1]
            display_day_detail(project_path, day_arg)
        elif command in ("stats", "s"):
            display_stats(project_path)
        elif command.startswith("filter --type "):
            artifact_type = command.split("--type ", 1)[1]
            display_timeline_tui(project_path, artifact_type_filter=artifact_type)
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("[dim]Type 'timeline' or press Enter for canonical timeline[/dim]")


def main():
    """CLI entry point."""
    import sys

    args = sys.argv[1:]

    if not args:
        try:
            project_path = detect_project_path()
            interactive_viewer(project_path)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("Usage: python -m runtime.journal_viewer <project_path>")
            sys.exit(1)
    else:
        project_path = Path(args[0])

        if "--timeline" in args:
            detailed = "--detailed" in args
            display_timeline_tui(project_path, detailed=detailed)
        elif "--stats" in args:
            display_stats(project_path)
        elif "--day" in args:
            day_idx = args.index("--day") + 1
            if day_idx < len(args):
                display_day_detail(project_path, args[day_idx])
        else:
            interactive_viewer(project_path)


if __name__ == "__main__":
    main()