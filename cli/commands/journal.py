"""journal command - Loop Journal Viewer integration."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

console = Console()

app = typer.Typer(help="View async-dev loop artifact timeline")


@app.command()
def timeline(
    project: Optional[str] = typer.Option(None, help="Project ID to view"),
    feature: Optional[str] = typer.Option(None, help="Filter by feature ID"),
    type: Optional[str] = typer.Option(None, help="Filter by artifact type (review, plan, run)"),
    detailed: bool = typer.Option(False, help="Show detailed view"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
) -> None:
    """Display timeline of async-dev artifacts."""
    from runtime.journal_viewer.tui_viewer import display_timeline_tui
    
    if project:
        project_path = path / project
    else:
        project_path = Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    display_timeline_tui(
        project_path,
        feature_filter=feature,
        artifact_type_filter=type,
        detailed=detailed,
    )


@app.command()
def stats(
    project: Optional[str] = typer.Option(None, help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
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
    project: Optional[str] = typer.Option(None, help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
) -> None:
    """Display detailed view for a specific day."""
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
    project: Optional[str] = typer.Option(None, help="Project ID to view"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
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


if __name__ == "__main__":
    app()