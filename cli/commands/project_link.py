"""Project-link CLI commands for Feature 055."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.project_link_loader import (
    load_project_link,
    validate_project_link,
    get_project_link_summary,
    is_mode_b,
)
from runtime.artifact_router import get_routing_summary

app = typer.Typer(name="project-link", help="Project-link management commands")
console = Console()


@app.command()
def show(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
):
    project_path = path / project if project else path
    
    summary = get_project_link_summary(project_path)
    
    if not summary.get("has_project_link"):
        console.print(Panel(
            f"Project: {project or 'N/A'}\n"
            f"Mode: self_hosted (default)\n"
            f"All artifacts local: True",
            title="Project Link (None)",
            border_style="blue"
        ))
        console.print("\n[cyan]To create project-link for Mode B:[/cyan]")
        console.print("  Create projects/{product_id}/project-link.yaml")
        return
    
    mode_color = "green" if summary["ownership_mode"] == "self_hosted" else "yellow"
    
    console.print(Panel(
        f"Product ID: {summary['product_id']}\n"
        f"Mode: {summary['ownership_mode']}\n"
        f"Product Repo: {summary.get('product_repo_path', 'N/A')}\n"
        f"Orchestrator Repo: {summary.get('orchestrator_repo_path', 'N/A')}\n"
        f"Current Phase: {summary.get('current_phase', 'N/A')}\n"
        f"Email Enabled: {summary.get('email_enabled', False)}",
        title=f"Project Link ({project or 'current'})",
        border_style=mode_color
    ))
    
    if summary["ownership_mode"] == "managed_external":
        routing = get_routing_summary(project_path)
        console.print("\n[bold]Routing Rules:[/bold]")
        for artifact, location in routing.get("routing_rules", {}).items():
            console.print(f"  {artifact}: {location}")


@app.command()
def validate(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
):
    project_path = path / project if project else path
    
    is_valid, issues = validate_project_link(project_path)
    
    if is_valid:
        console.print(Panel(
            f"Project: {project or 'current'}\n"
            f"Status: Valid",
            title="[OK] Project Link Valid",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"Project: {project or 'current'}\n"
            f"Status: Invalid\n"
            f"Issues: {len(issues)}",
            title="[WARN] Project Link Issues",
            border_style="yellow"
        ))
        console.print("\n[bold]Issues:[/bold]")
        for issue in issues:
            console.print(f"  - {issue}")


@app.command()
def routing(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
):
    project_path = path / project if project else path
    
    routing_summary = get_routing_summary(project_path)
    
    console.print(Panel(
        f"Mode: {routing_summary['mode']}\n"
        f"Product Repo: {routing_summary['product_repo']}\n"
        f"Orchestration Repo: {routing_summary['orchestration_repo']}\n"
        f"Product-owned artifacts: {routing_summary.get('product_owned_count', 0)}\n"
        f"Orchestration-owned artifacts: {routing_summary.get('orchestration_owned_count', 0)}",
        title="Artifact Routing",
        border_style="blue"
    ))
    
    if routing_summary.get("routing_rules"):
        console.print("\n[bold]Routing Rules:[/bold]")
        rules_table = Table()
        rules_table.add_column("Artifact", style="cyan")
        rules_table.add_column("Location", style="green")
        
        for artifact, location in routing_summary["routing_rules"].items():
            rules_table.add_row(artifact, location)
        
        console.print(rules_table)


@app.command()
def mode(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
):
    project_path = path / project if project else path
    
    if is_mode_b(project_path):
        console.print("[yellow]Mode B (managed_external)[/yellow]")
        console.print("  Product artifacts go to product repo")
        console.print("  Orchestration artifacts stay in async-dev")
    else:
        console.print("[green]Mode A (self_hosted)[/green]")
        console.print("  All artifacts in single repo")