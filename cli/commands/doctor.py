"""Workspace Doctor CLI command (Feature 029)."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.workspace_doctor import diagnose_workspace, format_diagnosis_markdown, format_diagnosis_yaml

app = typer.Typer(name="doctor", help="Diagnose workspace health and recommend next action")
console = Console()


def _resolve_project_path(project_id: Optional[str], projects_path: Path) -> Path:
    """Resolve project path from project ID or find active project."""
    if project_id:
        return projects_path / project_id
    
    if not projects_path.exists():
        return Path("nonexistent")
    
    project_dirs = sorted(
        projects_path.iterdir(),
        key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
        reverse=True
    )
    
    for project_dir in project_dirs:
        if project_dir.is_dir() and (project_dir / "runstate.md").exists():
            return project_dir
    
    return Path("nonexistent")


@app.command()
def show(
    project: str = typer.Option(None, "--project", "-p", help="Project ID to diagnose"),
    path: Path = typer.Option("projects", "--path", help="Projects root path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, yaml"),
):
    """Show workspace diagnosis with health classification and recommended next action.
    
    The diagnosis includes:
    - Overall health status (HEALTHY, ATTENTION_NEEDED, BLOCKED, etc.)
    - Current execution state
    - Signal summary (verification, decisions, blockers)
    - Recommended action with exact command
    - Rationale and warnings
    
    This command does NOT mutate workspace state.
    """
    project_path = _resolve_project_path(project, path)
    
    diagnosis = diagnose_workspace(project_path)
    
    if format == "yaml":
        output = format_diagnosis_yaml(diagnosis)
        console.print(output)
    else:
        output = format_diagnosis_markdown(diagnosis)
        console.print(output)
        
        if diagnosis.suggested_command:
            console.print(Panel(
                diagnosis.suggested_command,
                title="Suggested Command",
                border_style="green"
            ))