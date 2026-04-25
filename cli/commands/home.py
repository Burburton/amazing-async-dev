"""home command - Operator Home / Platform Overview.

Minimal unified operator entry point for async-dev.
Aggregates: active runs, recovery, acceptance, observer findings.

Per operator-home-platform-overview.md:
- Overview first, detail second
- Lightweight, not overbuilt
- Reuse existing platform truth
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.operator_home_adapter import build_operator_home_overview

app = typer.Typer(help="Operator Home - Unified platform overview")
console = Console()


@app.command()
def show(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show operator home overview - unified platform status."""
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        overview = build_operator_home_overview(project_path.parent)
    else:
        overview = build_operator_home_overview(path)
    
    console.print(Panel(
        f"Projects: {overview.total_projects} | Features: {overview.total_features}\n"
        f"Healthy: {overview.healthy_count} | Blocked: {overview.blocked_count} | Attention: {overview.attention_count}",
        title="Operator Home - Platform Overview",
        border_style="blue",
    ))
    
    if overview.is_calm():
        console.print("\n[green]Platform is calm - nothing requiring attention[/green]")
        console.print("[dim]Use 'asyncdev plan-day' to start new work[/dim]")
    else:
        if overview.has_critical():
            console.print("\n[red]Critical issues detected![/red]")
        
        if overview.attention_items:
            console.print("\n[bold yellow]Needs Attention[/bold yellow]")
            attention_table = Table(title="Attention Items", show_header=True)
            attention_table.add_column("Category", style="cyan", width=15)
            attention_table.add_column("Item", style="white", width=30)
            attention_table.add_column("Severity", style="red", width=10)
            attention_table.add_column("Action", style="green", width=35)
            
            for item in overview.attention_items[:5]:
                severity_style = {"critical": "red", "high": "yellow", "medium": "blue"}
                style = severity_style.get(item.severity, "white")
                attention_table.add_row(
                    item.category,
                    item.title,
                    f"[{style}]{item.severity}[/{style}]",
                    item.suggested_action[:35],
                )
            
            console.print(attention_table)
        
        if overview.blocked_items:
            console.print("\n[bold red]Blocked Items[/bold red]")
            blocked_table = Table(title="Blocked", show_header=True)
            blocked_table.add_column("Category", style="cyan")
            blocked_table.add_column("Title", style="white")
            blocked_table.add_column("Reason", style="yellow")
            blocked_table.add_column("Next Step", style="green")
            
            for item in overview.blocked_items[:5]:
                blocked_table.add_row(
                    item.category,
                    item.title,
                    item.reason[:40],
                    item.suggested_action[:40],
                )
            
            console.print(blocked_table)
        
        if overview.acceptance_queue:
            console.print("\n[bold cyan]Awaiting Acceptance[/bold cyan]")
            acceptance_table = Table(title="Acceptance Queue", show_header=True)
            acceptance_table.add_column("Project", style="cyan")
            acceptance_table.add_column("Feature", style="white")
            acceptance_table.add_column("Status", style="yellow")
            acceptance_table.add_column("Attempts", style="dim")
            acceptance_table.add_column("Blocked", style="red")
            
            for item in overview.acceptance_queue[:5]:
                blocked_str = "Yes" if item.completion_blocked else "No"
                acceptance_table.add_row(
                    item.project_id,
                    item.feature_id,
                    item.terminal_state or "pending",
                    str(item.attempt_count),
                    blocked_str,
                )
            
            console.print(acceptance_table)
        
        if overview.observer_highlights:
            console.print("\n[bold magenta]Observer Highlights[/bold magenta]")
            observer_table = Table(title="Observer Findings", show_header=True)
            observer_table.add_column("Type", style="cyan")
            observer_table.add_column("Severity", style="red")
            observer_table.add_column("Summary", style="white")
            observer_table.add_column("Project", style="dim")
            
            for item in overview.observer_highlights[:5]:
                severity_style = {"critical": "red", "high": "yellow"}
                style = severity_style.get(item.severity, "white")
                observer_table.add_row(
                    item.finding_type,
                    f"[{style}]{item.severity}[/{style}]",
                    item.summary,
                    item.project_id,
                )
            
            console.print(observer_table)
    
    if overview.active_runs:
        console.print("\n[bold]Active Runs[/bold]")
        runs_table = Table(title="Active Runs", show_header=True)
        runs_table.add_column("Project", style="cyan")
        runs_table.add_column("Feature", style="white")
        runs_table.add_column("Phase", style="yellow")
        runs_table.add_column("Health", style="green")
        runs_table.add_column("Updated", style="dim")
        
        for run in overview.active_runs:
            health_style = {"healthy": "green", "active": "blue", "blocked": "red"}
            style = health_style.get(run.health_summary, "white")
            runs_table.add_row(
                run.project_id,
                run.feature_id,
                run.phase,
                f"[{style}]{run.health_summary}[/{style}]",
                run.last_updated,
            )
        
        console.print(runs_table)
    
    console.print("\n[bold cyan]Quick Links[/bold cyan]")
    for link in overview.quick_links:
        console.print(f"  [cyan]{link.label}[/cyan]: {link.command}")
    
    console.print(f"\n[dim]Updated: {overview.updated_at[:19]}[/dim]")


@app.command()
def status(
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show quick platform status summary."""
    
    overview = build_operator_home_overview(path)
    
    if overview.is_calm():
        console.print("[green]Platform Status: CALM[/green]")
        console.print(f"  Projects: {overview.total_projects}, Healthy: {overview.healthy_count}")
    elif overview.has_critical():
        console.print("[red]Platform Status: CRITICAL[/red]")
        console.print(f"  Attention: {overview.attention_count}, Blocked: {overview.blocked_count}")
    elif overview.blocked_count > 0:
        console.print("[yellow]Platform Status: BLOCKED[/yellow]")
        console.print(f"  Blocked: {overview.blocked_count}, Attention: {overview.attention_count}")
    else:
        console.print("[blue]Platform Status: ACTIVE[/blue]")
        console.print(f"  Active: {len(overview.active_runs)}, Projects: {overview.total_projects}")
    
    console.print(f"\nNext: {overview.quick_links[0].command}")


@app.command()
def calm(
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check if platform is calm (no attention needed)."""
    
    overview = build_operator_home_overview(path)
    
    if overview.is_calm():
        console.print("[green]Yes - Platform is calm[/green]")
        console.print("[dim]No items requiring attention[/dim]")
    else:
        console.print("[yellow]No - Platform has attention items[/yellow]")
        console.print(f"  Attention: {overview.attention_count}")
        console.print(f"  Blocked: {overview.blocked_count}")
        console.print(f"\nRun: asyncdev home show")