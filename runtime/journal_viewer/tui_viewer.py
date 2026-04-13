"""TUI Timeline Display with rich."""

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
)


console = Console()


def filter_entries(
    entries: list[JournalEntry],
    feature: str | None = None,
    project: str | None = None,
    artifact_type: str | None = None,
) -> list[JournalEntry]:
    """Filter journal entries by feature, project, or artifact type."""
    filtered = entries
    
    if feature:
        filtered = [e for e in filtered if e.feature == feature]
    
    if project:
        filtered = [e for e in filtered if e.project == project]
    
    if artifact_type:
        filtered = [e for e in filtered if e.artifact_type == artifact_type]
    
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


def render_entry_detail(entry: JournalEntry) -> Panel:
    """Render detailed view of a journal entry."""
    content_lines = [
        f"[bold]Title:[/bold] {entry.title}",
        f"[bold]Summary:[/bold] {entry.summary}",
    ]
    
    if entry.key_fields:
        content_lines.append("[bold]Key Fields:[/bold]")
        for k, v in entry.key_fields.items():
            if isinstance(v, list):
                content_lines.append(f"  • {k}: {len(v)} items")
            else:
                content_lines.append(f"  • {k}: {v}")
    
    content_lines.append(f"[bold]Source:[/bold] {entry.source_path}")
    
    type_color = {
        "review": "green",
        "plan": "blue",
        "run": "yellow",
        "runstate": "cyan",
    }.get(entry.artifact_type, "white")
    
    return Panel(
        "\n".join(content_lines),
        title=f"[{type_color}]{entry.artifact_type.upper()}[/{type_color}] - {entry.day}",
        border_style=type_color,
    )


def render_timeline_table(entries: list[JournalEntry]) -> Table:
    """Render timeline as a Rich table."""
    table = Table(title="Loop Journal Timeline", show_header=True)
    
    table.add_column("Day", style="cyan")
    table.add_column("Type", style="bold")
    table.add_column("Title", style="white")
    table.add_column("Summary", style="dim")
    table.add_column("Source", style="dim")
    
    for entry in entries:
        type_color = {
            "review": "green",
            "plan": "blue",
            "run": "yellow",
            "runstate": "cyan",
        }.get(entry.artifact_type, "white")
        
        summary_preview = entry.summary[:50] + "..." if len(entry.summary) > 50 else entry.summary
        source_preview = Path(entry.source_path).name
        
        table.add_row(
            entry.day,
            f"[{type_color}]{entry.artifact_type.upper()}[/{type_color}]",
            entry.title[:40],
            summary_preview,
            source_preview,
        )
    
    return table


def render_day_summary(day: str, entries: list[JournalEntry]) -> Panel:
    """Render summary panel for a day."""
    type_counts = {}
    for e in entries:
        type_counts[e.artifact_type] = type_counts.get(e.artifact_type, 0) + 1
    
    summary_lines = [f"[bold]{day}[/bold]"]
    for t, count in sorted(type_counts.items()):
        summary_lines.append(f"  {t}: {count}")
    
    return Panel("\n".join(summary_lines), title="Day Summary", border_style="blue")


def display_timeline_tui(
    project_path: Path,
    feature_filter: str | None = None,
    project_filter: str | None = None,
    artifact_type_filter: str | None = None,
    detailed: bool = False,
) -> None:
    """Display timeline in TUI format."""
    console.print(f"\n[bold cyan]Loop Journal Viewer[/bold cyan]")
    console.print(f"[dim]Project: {project_path}[/dim]")
    
    entries = build_journal_timeline(project_path)
    
    if feature_filter or project_filter or artifact_type_filter:
        console.print(f"[dim]Filters: feature={feature_filter}, project={project_filter}, type={artifact_type_filter}[/dim]")
        entries = filter_entries(entries, feature_filter, project_filter, artifact_type_filter)
    
    console.print(f"\n[bold]Total entries: {len(entries)}[/bold]\n")
    
    if detailed:
        for entry in entries:
            console.print(render_entry_detail(entry))
    else:
        console.print(render_timeline_table(entries))
    
    grouped = group_entries_by_day(entries)
    console.print(f"\n[bold]Days covered: {len(grouped)}[/bold]")


def display_day_detail(project_path: Path, day: str) -> None:
    """Display detailed view for a specific day."""
    entries = build_journal_timeline(project_path)
    grouped = group_entries_by_day(entries)
    
    if day not in grouped:
        console.print(f"[red]Day not found: {day}[/red]")
        return
    
    day_entries = grouped[day]
    console.print(f"\n[bold cyan]Day: {day}[/bold cyan]")
    console.print(f"[dim]Entries: {len(day_entries)}[/dim]\n")
    
    for entry in day_entries:
        console.print(render_entry_detail(entry))


def display_stats(project_path: Path) -> None:
    """Display statistics about the project's artifacts."""
    console.print(f"\n[bold cyan]Artifact Statistics[/bold cyan]")
    console.print(f"[dim]Project: {project_path}[/dim]\n")
    
    stats_table = Table(title="Artifact Counts", show_header=True)
    stats_table.add_column("Type", style="bold")
    stats_table.add_column("Count", style="cyan")
    stats_table.add_column("Files", style="dim")
    
    for artifact_type in ["review", "plan", "run"]:
        artifacts = find_artifacts(project_path, artifact_type)
        stats_table.add_row(
            artifact_type.upper(),
            str(len(artifacts)),
            ", ".join([Path(a).name for a in artifacts[:3]]) + ("..." if len(artifacts) > 3 else ""),
        )
    
    console.print(stats_table)


def interactive_viewer(project_path: Path) -> None:
    """Interactive TUI viewer with commands."""
    console.print(Panel(
        "[bold]Loop Journal Viewer[/bold]\n\n"
        "Commands:\n"
        "  timeline - Show full timeline\n"
        "  day <date> - Show day detail\n"
        "  stats - Show artifact stats\n"
        "  filter --feature <id> - Filter by feature\n"
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
        
        if command == "quit" or command == "exit":
            console.print("[dim]Goodbye[/dim]")
            break
        elif command == "timeline":
            display_timeline_tui(project_path, detailed=False)
        elif command == "timeline --detailed":
            display_timeline_tui(project_path, detailed=True)
        elif command.startswith("day "):
            day = command.split(" ", 1)[1]
            display_day_detail(project_path, day)
        elif command == "stats":
            display_stats(project_path)
        elif command.startswith("filter --feature "):
            feature = command.split("--feature ", 1)[1]
            display_timeline_tui(project_path, feature_filter=feature)
        elif command.startswith("filter --type "):
            artifact_type = command.split("--type ", 1)[1]
            display_timeline_tui(project_path, artifact_type_filter=artifact_type)
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")


def main():
    """CLI entry point for TUI viewer."""
    import sys
    
    args = sys.argv[1:]
    
    if not args:
        try:
            project_path = detect_project_path()
            interactive_viewer(project_path)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("Usage: python viewer/tui_viewer.py <project_path>")
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