"""session-start command - Mandatory session initialization (Feature 065).

Ensures blocking state is checked before any work begins.
This command MUST be run at session start per AGENTS.md Section 2.
"""

from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore, has_blocking_alert, generate_blocking_alert
from runtime.decision_waiting_session import (
    check_blocking_state,
    get_blocking_message,
    session_startup_check,
)
from runtime.webhook_poller import poll_pending_decisions

app = typer.Typer(help="Session start - Mandatory blocking state check")
console = Console()


@app.command()
def check(
    project: str = typer.Option(None, "--project", help="Project ID to check"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check blocking state at session start.
    
    MANDATORY per AGENTS.md Section 2:
    - Run this BEFORE any TODO tasks
    - If BLOCKED/WAITING_DECISION: poll for replies or stop
    - Only proceed if status is CLEAR
    
    Example:
        asyncdev session-start check --project my-app
        asyncdev session-start check (checks all projects)
    """
    console.print(Panel("Session Start Check", title="session-start", border_style="cyan"))
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    else:
        projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        console.print("[dim]Run: asyncdev new-product create[/dim]")
        return
    
    blocked_projects = []
    clear_projects = []
    
    for project_path in projects:
        status, request_id = check_blocking_state(project_path)
        
        if status in ["BLOCKED", "WAITING_DECISION"]:
            blocked_projects.append({
                "project": project_path.name,
                "status": status,
                "request_id": request_id,
                "path": project_path,
            })
        else:
            clear_projects.append(project_path.name)
    
    if blocked_projects:
        console.print(f"\n[bold red]BLOCKING ALERT: {len(blocked_projects)} projects blocked[/bold red]")
        
        table = Table(title="Blocked Projects")
        table.add_column("Project", style="red", width=20)
        table.add_column("Status", style="yellow", width=15)
        table.add_column("Request ID", style="cyan", width=20)
        table.add_column("Action", style="magenta", width=30)
        
        for bp in blocked_projects:
            action = f"asyncdev decision wait --request {bp['request_id']}"
            table.add_row(
                bp["project"],
                bp["status"],
                bp["request_id"],
                action,
            )
        
        console.print(table)
        
        for bp in blocked_projects:
            message = get_blocking_message(bp["path"])
            console.print(f"\n[bold]Blocking ({bp['project']}):[/bold]")
            console.print(f"  {message}")
        
        console.print(f"\n[bold red]MANDATORY: Stop all execution. Resolve decisions first.[/bold red]")
        console.print(f"[dim]Run: asyncdev decision wait --request <id>[/dim]")
        console.print(f"[dim]Or: asyncdev decision reply --request <id> --command \"DECISION X\"[/dim]")
        
        raise typer.Exit(2)
    
    console.print(f"\n[bold green]Status: CLEAR[/bold green]")
    console.print(f"[dim]Checked {len(clear_projects)} projects[/dim]")
    
    if clear_projects:
        console.print(f"\n[bold]Clear Projects:[/bold]")
        for name in clear_projects[:10]:
            console.print(f"  [green]{name}[/green]")
        
        if len(clear_projects) > 10:
            console.print(f"  [dim]... and {len(clear_projects) - 10} more[/dim]")
    
    console.print(f"\n[dim]Proceed with execution[/dim]")


@app.command()
def poll(
    project: str = typer.Option(..., "--project", help="Project ID"),
    timeout: int = typer.Option(60, "--timeout", help="Timeout in seconds (default: 60 for quick check)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Quick poll for pending decision replies.
    
    Checks webhook once for replies. Useful for session start
    to see if any replies arrived since last session.
    
    Example:
        asyncdev session-start poll --project my-app
    """
    project_path = path / project
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Polling for Decision Replies: {project}", title="session-start poll", border_style="yellow"))
    
    from runtime.resend_provider import load_resend_config
    
    config = load_resend_config(project_path / ".runtime" / "resend-config.json")
    
    if not config:
        console.print("[red]No resend config found[/red]")
        console.print("[yellow]Run: asyncdev resend-auth setup[/yellow]")
        raise typer.Exit(1)
    
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        console.print("[red]No webhook URL configured[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Checking webhook: {webhook_url}[/cyan]")
    
    pending = poll_pending_decisions(webhook_url, timeout=10)
    
    if not pending:
        console.print("[green]No pending replies found[/green]")
        
        status, request_id = check_blocking_state(project_path)
        if status in ["BLOCKED", "WAITING_DECISION"]:
            console.print(f"\n[yellow]Still blocked: {request_id}[/yellow]")
            console.print("[dim]Human reply not yet received[/dim]")
        
        return
    
    console.print(f"[green]Found {len(pending)} pending replies[/green]")
    
    table = Table(title="Pending Replies")
    table.add_column("Request ID", style="cyan", width=20)
    table.add_column("From", style="green", width=25)
    table.add_column("Option", style="yellow", width=10)
    table.add_column("Received", style="dim", width=20)
    
    for decision in pending:
        table.add_row(
            decision.id,
            decision.from_email,
            decision.option,
            decision.received_at[:19] if decision.received_at else "N/A",
        )
    
    console.print(table)
    
    console.print(f"\n[dim]Process: asyncdev decision reply --request <id> --command \"DECISION X\"[/dim]")


@app.command()
def status(
    project: str = typer.Option(None, "--project", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show session start status summary.
    
    Quick summary of blocking state across projects.
    
    Example:
        asyncdev session-start status
    """
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    else:
        projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return
    
    console.print(Panel("Session Start Status", title="session-start status", border_style="cyan"))
    
    blocked_count = 0
    waiting_count = 0
    clear_count = 0
    
    for project_path in projects:
        status, _ = check_blocking_state(project_path)
        
        if status == "BLOCKED":
            blocked_count += 1
        elif status == "WAITING_DECISION":
            waiting_count += 1
        else:
            clear_count += 1
    
    summary_table = Table(title="Blocking State Summary", show_header=False)
    summary_table.add_column("State", style="cyan", width=20)
    summary_table.add_column("Count", style="green", width=10)
    summary_table.add_column("Action", style="magenta", width=30)
    
    summary_table.add_row("BLOCKED", str(blocked_count), "[red]Stop - poll for replies[/red]" if blocked_count else "[dim]None[/dim]")
    summary_table.add_row("WAITING_DECISION", str(waiting_count), "[yellow]Poll inbox[/yellow]" if waiting_count else "[dim]None[/dim]")
    summary_table.add_row("CLEAR", str(clear_count), "[green]Ready to proceed[/green]" if clear_count else "[dim]None[/dim]")
    
    console.print(summary_table)
    
    if blocked_count > 0 or waiting_count > 0:
        console.print(f"\n[bold red]BLOCKING ACTIVE[/bold red]")
        console.print(f"[dim]Run: asyncdev session-start check for details[/dim]")
    else:
        console.print(f"\n[bold green]ALL CLEAR[/bold green]")
        console.print(f"[dim]Proceed with execution[/dim]")


if __name__ == "__main__":
    app()