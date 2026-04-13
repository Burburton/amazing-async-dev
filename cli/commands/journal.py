"""journal command - Loop Journal Viewer V1.3.

Primary entry point: asyncdev journal timeline
Day detail view: asyncdev journal day <date>
Feature view: asyncdev journal feature <feature-id>
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

console = Console()

app = typer.Typer(
    name="journal",
    help="View async-dev loop artifacts: timeline, day, feature (V1.3), stats",
    no_args_is_help=True,
)


@app.command()
def timeline(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID to view"),
    feature: Optional[str] = typer.Option(None, "--feature", "-f", help="Filter by feature ID"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by artifact type (review, plan, run)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed view"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
    warnings: bool = typer.Option(True, "--warnings/--no-warnings", help="Show parsing warnings"),
) -> None:
    """Display canonical timeline of async-dev artifacts.
    
    This is the PRIMARY view for Loop Journal Viewer V1.1.
    Shows the sequence: Plan Day → Run Day → Review Night
    """
    from runtime.journal_viewer.tui_viewer import display_timeline_tui
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        console.print("[dim]Use --project <id> to specify a project[/dim]")
        console.print("[dim]Or run from within a project directory[/dim]")
        raise typer.Exit(1)
    
    display_timeline_tui(
        project_path,
        feature_filter=feature,
        artifact_type_filter=type,
        detailed=detailed,
        show_warnings=warnings,
    )


@app.command()
def stats(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
) -> None:
    """Display artifact statistics for a project."""
    from runtime.journal_viewer.tui_viewer import display_stats
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    display_stats(project_path)


@app.command()
def day(
    date: str = typer.Argument(..., help="Day to view (YYYY-MM-DD format)"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
) -> None:
    """Display day detail view: artifacts in canonical order (Review → Plan → Run).

    V1.2: Shows each phase header with graceful handling for missing artifacts.
    """
    from runtime.journal_viewer.tui_viewer import display_day_detail
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    display_day_detail(project_path, date)


@app.command()
def interactive(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
) -> None:
    """Launch interactive viewer mode."""
    from runtime.journal_viewer.tui_viewer import interactive_viewer
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    interactive_viewer(project_path)


@app.command()
def feature(
    feature_id: str = typer.Argument(..., help="Feature ID to inspect"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
) -> None:
    """Display feature-focused timeline: evolution across days.

    V1.3: Shows how one feature moved through review/plan/run phases.
    Gracefully handles partial or missing feature metadata.
    """
    from runtime.journal_viewer.tui_viewer import display_feature_timeline
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    display_feature_timeline(project_path, feature_id)


@app.command("project-summary")
def project_summary(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
) -> None:
    """Display project-level summary with feature breakdown.

    V1.3: Shows artifact counts and feature grouping overview.
    """
    from runtime.journal_viewer.tui_viewer import display_project_summary
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    display_project_summary(project_path)


if __name__ == "__main__":
    app()