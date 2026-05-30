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
        project = None
    
    console.print(Panel(
        f"Projects: {overview.total_projects} | Features: {overview.total_features}\n"
        f"Healthy: {overview.healthy_count} | Blocked: {overview.blocked_count} | Attention: {overview.attention_count}",
        title="Operator Home - Platform Overview",
        border_style="blue",
    ))
    
    if overview.blocking_state and overview.blocking_state.total_blocking_count > 0:
        blocking_items = []
        
        for sb in overview.blocking_state.session_blocking:
            status_color = "red" if sb.status == "BLOCKED" else "yellow"
            blocking_items.append(
                f"[{status_color}]{sb.status}[/{status_color}]: {sb.project_id} - {sb.message}"
            )
            blocking_items.append(f"  → asyncdev decision show --request {sb.request_id}")
        
        if blocking_items:
            console.print(Panel(
                "\n".join(blocking_items),
                title="🔴 Blocking State Detected",
                border_style="red",
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
        command = link.command
        if project:
            command = command.replace("{id}", project)
        console.print(f"  [cyan]{link.label}[/cyan]: {command}")
    
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


@app.command()
def blocking(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show all blocking states across surfaces.
    
    Unified view of:
    - Session blocking (pending decisions)
    - Acceptance escalations
    - Verification exceptions
    
    Example:
        asyncdev home blocking
        asyncdev home blocking --project my-app
    """
    from runtime.unified_blocking import get_unified_blocking_state
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        blocking_state = get_unified_blocking_state(project_path.parent)
    else:
        blocking_state = get_unified_blocking_state(path)
    
    if blocking_state.is_calm():
        console.print("[green]No blocking states detected[/green]")
        console.print("[dim]Platform is clear to proceed[/dim]")
        return
    
    console.print(Panel(
        f"Total blocking items: {blocking_state.total_blocking_count}\n"
        f"Summary: {blocking_state.blocking_summary}",
        title="Blocking State Overview",
        border_style="red",
    ))
    
    if blocking_state.session_blocking:
        console.print("\n[bold red]Session Blocking (Decisions)[/bold red]")
        session_table = Table(title="Session Blocking", show_header=True)
        session_table.add_column("Project", style="cyan", width=15)
        session_table.add_column("Status", style="red", width=15)
        session_table.add_column("Request ID", style="yellow", width=18)
        session_table.add_column("Message", style="white", width=40)
        session_table.add_column("Action", style="green", width=35)
        
        for sb in blocking_state.session_blocking:
            status_style = "red" if sb.status == "BLOCKED" else "yellow"
            action = f"asyncdev decision show --request {sb.request_id}" if sb.request_id else "N/A"
            session_table.add_row(
                sb.project_id,
                f"[{status_style}]{sb.status}[/{status_style}]",
                sb.request_id or "N/A",
                sb.message[:40],
                action,
            )
        
        console.print(session_table)
    
    if blocking_state.acceptance_escalations:
        console.print("\n[bold yellow]Acceptance Escalations[/bold yellow]")
        accept_table = Table(title="Acceptance Escalations", show_header=True)
        accept_table.add_column("Project", style="cyan")
        accept_table.add_column("Feature", style="white")
        accept_table.add_column("Reason", style="yellow")
        accept_table.add_column("Terminal State", style="red")
        
        for ae in blocking_state.acceptance_escalations:
            accept_table.add_row(
                ae.project_id,
                ae.feature_id,
                ae.escalation_reason[:40],
                ae.terminal_state,
            )
        
        console.print(accept_table)
    
    if blocking_state.verification_exceptions:
        console.print("\n[bold orange1]Verification Exceptions[/bold orange1]")
        verify_table = Table(title="Verification Exceptions", show_header=True)
        verify_table.add_column("Project", style="cyan")
        verify_table.add_column("Execution", style="white")
        verify_table.add_column("Exception", style="yellow")
        
        for ve in blocking_state.verification_exceptions:
            verify_table.add_row(
                ve.project_id,
                ve.execution_id,
                ve.exception_reason,
            )
        
        console.print(verify_table)
    
    console.print(f"\n[dim]Updated: {blocking_state.updated_at[:19]}[/dim]")


@app.command()
def recovery(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show recovery summary with drill-down to Recovery Console.
    
    Shows all executions needing recovery across projects.
    Links to Recovery Console for detailed actions.
    
    Example:
        asyncdev home recovery
        asyncdev home recovery --project my-app
    """
    import subprocess
    import sys
    from pathlib import Path as P
    
    if project:
        cmd = ["recovery", "list", "--project", project]
    else:
        cmd = ["recovery", "list", "--all"]
    
    cli_path = P(__file__).parent.parent / "asyncdev.py"
    result = subprocess.run(
        [sys.executable, str(cli_path)] + cmd,
        capture_output=True,
        text=True,
    )
    
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")
    
    console.print("\n[bold cyan]Drill-down:[/bold cyan]")
    console.print("  [green]asyncdev recovery list --all[/green] - Full Recovery Console")
    console.print("  [green]asyncdev recovery show --execution <id>[/green] - Specific execution detail")


@app.command()
def decision(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    status: str = typer.Option(None, "--status", help="Filter by status (pending, sent, resolved)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show decision inbox summary with drill-down.
    
    Shows pending decisions across projects.
    Links to Decision Inbox for reply actions.
    
    Example:
        asyncdev home decision
        asyncdev home decision --project my-app --status pending
    """
    import subprocess
    import sys
    from pathlib import Path as P
    
    cmd = ["decision", "list"]
    if project:
        cmd.extend(["--project", project])
    if status:
        cmd.extend(["--status", status])
    
    cli_path = P(__file__).parent.parent / "asyncdev.py"
    result = subprocess.run(
        [sys.executable, str(cli_path)] + cmd,
        capture_output=True,
        text=True,
    )
    
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")
    
    console.print("\n[bold cyan]Drill-down:[/bold cyan]")
    console.print("  [green]asyncdev decision list --all[/green] - Full Decision Inbox")
    console.print("  [green]asyncdev decision show --request <id>[/green] - Specific decision detail")
    console.print("  [green]asyncdev decision reply --request <id> --command \"DECISION A\"[/green] - Reply")


@app.command()
def navigate(
    surface: str = typer.Argument(..., help="Surface to navigate to (recovery, decision, acceptance, observer, verification, evidence)"),
    id: str = typer.Option(None, "--id", help="Specific ID for the surface (execution ID, request ID, etc.)"),
    project: str = typer.Option(None, "--project", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Direct navigation to specific surface detail.
    
    Routes directly to the appropriate surface command.
    
    Surfaces:
        recovery     - Recovery Console
        decision     - Decision Inbox
        acceptance   - Acceptance Console
        observer    - Execution Observer
        verification - Verification Console
        evidence    - Evidence Console
    
    Examples:
        asyncdev home navigate recovery --id exec-001
        asyncdev home navigate decision --id dr-20260530-001
        asyncdev home navigate acceptance --project my-app
    """
    import subprocess
    import sys
    from pathlib import Path as P
    
    surface_commands = {
        "recovery": ["recovery", "list"],
        "decision": ["decision", "list"],
        "acceptance": ["acceptance", "status"],
        "observer": ["observe-runs", "run"],
        "verification": ["verification", "list"],
        "evidence": ["evidence", "summary"],
    }
    
    if surface not in surface_commands:
        console.print(f"[red]Unknown surface: {surface}[/red]")
        console.print(f"[yellow]Valid surfaces: {', '.join(surface_commands.keys())}[/yellow]")
        raise typer.Exit(1)
    
    cmd = surface_commands[surface]
    
    if id and surface == "recovery":
        cmd = ["recovery", "show", "--execution", id]
    elif id and surface == "decision":
        cmd = ["decision", "show", "--request", id]
    elif id and surface == "acceptance":
        cmd = ["acceptance", "result", "--result-id", id]
    elif project:
        cmd.extend(["--project", project])
    
    cli_path = P(__file__).parent.parent / "asyncdev.py"
    result = subprocess.run(
        [sys.executable, str(cli_path)] + cmd,
        capture_output=True,
        text=True,
    )
    
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")

    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def recovery_dashboard(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show unified recovery dashboard across all recovery aspects.
    
    Aggregates:
    - Execution Recovery (from Recovery Console)
    - Acceptance Recovery (from Acceptance Console)
    - Observer Recovery Signals (from Execution Observer)
    
    Example:
        asyncdev home recovery-dashboard
        asyncdev home recovery-dashboard --project my-app
    """
    from runtime.recovery_data_adapter import RecoveryDataAdapter, get_recovery_item_for_project
    from runtime.execution_observer import run_observer
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        project_dirs = [project_path]
    else:
        project_dirs = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    all_recovery_items = []
    all_observer_signals = []
    
    for project_path in project_dirs:
        adapter = RecoveryDataAdapter(project_path)
        item = adapter.get_recovery_item_with_observer()
        
        if item:
            all_recovery_items.append(item)
            
            for finding in item.observer_findings:
                if finding.recovery_significant:
                    all_observer_signals.append({
                        "project": project_path.name,
                        "finding": finding,
                    })
    
    if not all_recovery_items and not all_observer_signals:
        console.print("[green]No recovery items detected[/green]")
        console.print("[dim]Platform is recovery-free[/dim]")
        return
    
    console.print(Panel(
        f"Recovery Items: {len(all_recovery_items)} | Observer Signals: {len(all_observer_signals)}",
        title="Unified Recovery Dashboard",
        border_style="yellow",
    ))
    
    if all_recovery_items:
        console.print("\n[bold]Execution Recovery[/bold]")
        exec_table = Table(title="Execution Recovery", show_header=True)
        exec_table.add_column("Project", style="cyan", width=15)
        exec_table.add_column("Execution", style="white", width=20)
        exec_table.add_column("Category", style="yellow", width=15)
        exec_table.add_column("Reason", style="white", width=30)
        exec_table.add_column("Action", style="green", width=25)
        
        for item in all_recovery_items[:10]:
            category_style = {
                "blocked": "yellow",
                "failed": "red",
                "decision_blocked": "orange1",
                "manual_investigation": "red",
            }.get(item.recovery_category, "white")
            
            exec_table.add_row(
                item.product_id,
                item.execution_id[:20],
                f"[{category_style}]{item.recovery_category}[/{category_style}]",
                item.recovery_reason[:30] if item.recovery_reason else "N/A",
                item.suggested_command[:25] if item.suggested_command else "N/A",
            )
        
        console.print(exec_table)
    
    if all_observer_signals:
        console.print("\n[bold magenta]Observer Recovery Signals[/bold magenta]")
        obs_table = Table(title="Observer Signals", show_header=True)
        obs_table.add_column("Project", style="cyan", width=15)
        obs_table.add_column("Finding", style="white", width=20)
        obs_table.add_column("Severity", style="red", width=10)
        obs_table.add_column("Reason", style="yellow", width=35)
        
        for sig in all_observer_signals[:10]:
            finding = sig["finding"]
            severity_style = "red" if finding.severity == "critical" else "yellow"
            obs_table.add_row(
                sig["project"],
                finding.finding_type,
                f"[{severity_style}]{finding.severity}[/{severity_style}]",
                finding.reason[:35],
            )
        
        console.print(obs_table)
    
    console.print("\n[bold cyan]Quick Actions[/bold cyan]")
    console.print("  [green]asyncdev recovery list --all[/green] - Full Recovery Console")
    console.print("  [green]asyncdev observer run --all[/green] - Run Observer")
    console.print("  [green]asyncdev acceptance status[/green] - Acceptance Status")


@app.command()
def attention(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive selection mode"),
):
    """Show all attention items with optional interactive drill-down.
    
    Lists items from:
    - Attention Items (recovery, blocked)
    - Acceptance Queue
    - Observer Highlights
    - Blocked Items
    
    Use --interactive/-i for numbered selection drill-down.
    
    Example:
        asyncdev home attention
        asyncdev home attention --project my-app
        asyncdev home attention -i
    """
    import subprocess
    import sys
    from pathlib import Path as P
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        overview = build_operator_home_overview(project_path.parent)
    else:
        overview = build_operator_home_overview(path)
    
    all_items = []
    
    for item in overview.attention_items:
        all_items.append({
            "type": "attention",
            "category": item.category,
            "title": item.title,
            "severity": item.severity,
            "reason": item.reason,
            "destination": item.destination,
            "suggested_action": item.suggested_action,
        })
    
    for item in overview.blocked_items:
        all_items.append({
            "type": "blocked",
            "category": item.category,
            "title": item.title,
            "severity": item.severity,
            "reason": item.reason,
            "destination": item.destination,
            "suggested_action": item.suggested_action,
        })
    
    for item in overview.acceptance_queue:
        all_items.append({
            "type": "acceptance",
            "category": "acceptance",
            "title": f"{item.project_id}: {item.feature_id}",
            "severity": "high" if item.completion_blocked else "medium",
            "reason": f"Status: {item.terminal_state or 'pending'}",
            "destination": f"asyncdev acceptance status --project {item.project_id}",
            "suggested_action": f"asyncdev acceptance result --project {item.project_id}",
        })
    
    for item in overview.observer_highlights:
        all_items.append({
            "type": "observer",
            "category": "observer",
            "title": f"{item.project_id}: {item.finding_type}",
            "severity": item.severity,
            "reason": item.summary,
            "destination": f"asyncdev observe-runs run --project {item.project_id}",
            "suggested_action": item.recommended_action,
        })
    
    if not all_items:
        console.print("[green]No attention items[/green]")
        console.print("[dim]Platform is calm[/dim]")
        return
    
    console.print(Panel(
        f"Total attention items: {len(all_items)}",
        title="Attention Items",
        border_style="yellow",
    ))
    
    console.print("\n[bold]All Attention Items[/bold]")
    items_table = Table(title="Attention Items", show_header=True)
    items_table.add_column("#", style="cyan", width=4)
    items_table.add_column("Type", style="magenta", width=12)
    items_table.add_column("Category", style="cyan", width=15)
    items_table.add_column("Title", style="white", width=30)
    items_table.add_column("Severity", style="red", width=10)
    items_table.add_column("Destination", style="green", width=35)
    
    for idx, item in enumerate(all_items, 1):
        severity_style = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
        }.get(item["severity"], "white")
        
        items_table.add_row(
            str(idx),
            item["type"],
            item["category"],
            item["title"][:30],
            f"[{severity_style}]{item['severity']}[/{severity_style}]",
            item["destination"][:35],
        )
    
    console.print(items_table)
    
    if interactive:
        console.print("\n[bold cyan]Select item number to drill-down (or Enter to exit):[/bold cyan]")
        try:
            choice = input("Selection: ").strip()
            if choice and choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(all_items):
                    selected = all_items[idx - 1]
                    console.print(f"\n[cyan]Drilling into: {selected['title']}[/cyan]")
                    console.print(f"[dim]Command: {selected['destination']}[/dim]")
                    
                    parts = selected["destination"].split()
                    cli_path = P(__file__).parent.parent / "asyncdev.py"
                    result = subprocess.run(
                        [sys.executable, str(cli_path)] + parts,
                        capture_output=True,
                        text=True,
                    )
                    if result.stdout:
                        console.print(result.stdout)
                    if result.stderr:
                        console.print(f"[red]{result.stderr}[/red]")
                else:
                    console.print("[yellow]Invalid selection[/yellow]")
            else:
                console.print("[dim]No selection, exiting[/dim]")
        except EOFError:
            console.print("[dim]Interactive mode not available[/dim]")
    else:
        console.print("\n[bold cyan]Drill-down Commands:[/bold cyan]")
        console.print("  [green]asyncdev home attention -i[/green] - Interactive mode")
        for idx, item in enumerate(all_items[:5], 1):
            console.print(f"  [{idx}] {item['destination']}")