"""decision command - Decision Inbox (Operator Surface).

Phase 3 operator surface per platform architecture.
Spec: docs/infra/decision-inbox-spec-v1.md
"""

from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
)
from runtime.decision_sync import sync_reply_to_runstate, reconcile_decision_sources
from runtime.decision_waiting_session import (
    check_blocking_state,
    get_blocking_message,
    poll_and_wait,
)
from runtime.reply_parser import parse_reply, validate_reply, create_reply_record
from runtime.reply_action_mapper import map_reply_to_action
from runtime.state_store import StateStore
from runtime.webhook_poller import (
    PollingDaemon,
    PollingConfig,
    poll_pending_decisions,
    process_pending_decision,
)
from runtime.resend_provider import load_resend_config

app = typer.Typer(help="Decision Inbox - Operator surface for decision management")
console = Console()

DECISION_POLL_INTERVAL = 60
DECISION_POLL_TIMEOUT = 3600


def _get_all_projects(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]


def _get_decisions_for_project(project_path: Path, status_filter: DecisionRequestStatus | None = None) -> list[dict]:
    store = DecisionRequestStore(project_path)
    requests = store.list_requests(status=status_filter)
    
    blocking_status, blocking_request_id = check_blocking_state(project_path)
    
    for req in requests:
        req["blocking_status"] = "CLEAR"
        req["project_path"] = project_path
        req["project_id"] = project_path.name
        
        if req["decision_request_id"] == blocking_request_id:
            req["blocking_status"] = blocking_status
    
    return requests


@app.command()
def list(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    all: bool = typer.Option(False, "--all", help="Show all projects"),
    status: str = typer.Option(None, "--status", help="Filter by status (pending, sent, resolved)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List pending decisions across projects.
    
    Shows decision requests with blocking state visibility.
    Blocking states: BLOCKED, WAITING_DECISION, CLEAR
    
    Examples:
        asyncdev decision list --all
        asyncdev decision list --project my-app
        asyncdev decision list --status sent
    """
    console.print(Panel("Decision Inbox", title="decision list", border_style="blue"))
    
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        console.print("[dim]Create a project: asyncdev new-product create[/dim]")
        return
    
    status_filter = None
    if status:
        try:
            status_filter = DecisionRequestStatus(status)
        except ValueError:
            console.print(f"[red]Invalid status: {status}[/red]")
            console.print(f"[yellow]Valid: pending, sent, reply_received, resolved, expired[/yellow]")
            raise typer.Exit(1)
    
    all_decisions = []
    for project_path in projects:
        decisions = _get_decisions_for_project(project_path, status_filter)
        all_decisions.extend(decisions)
    
    if not all_decisions:
        console.print("[green]No decision requests found[/green]")
        console.print("[dim]All workflows are decision-free[/dim]")
        return
    
    blocking_order = {"BLOCKED": 0, "WAITING_DECISION": 1, "CLEAR": 2}
    all_decisions.sort(key=lambda d: (
        blocking_order.get(d["blocking_status"], 3),
        d.get("sent_at", ""),
    ))
    
    table = Table(title="Pending Decisions")
    table.add_column("Request ID", style="cyan", width=18)
    table.add_column("Project", style="green", width=15)
    table.add_column("Question", style="white", width=35)
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Blocking", style="magenta", width=15)
    table.add_column("Sent", style="dim", width=10)
    
    blocking_style = {
        "BLOCKED": "red",
        "WAITING_DECISION": "orange1",
        "CLEAR": "green",
    }
    
    for d in all_decisions:
        style = blocking_style.get(d["blocking_status"], "white")
        blocking_display = f"[{style}]{d['blocking_status']}[/{style}]"
        question_short = d.get("question", "")[:35] if len(d.get("question", "")) > 35 else d.get("question", "")
        sent_short = d.get("sent_at", "")[:10] if d.get("sent_at") else "N/A"
        
        table.add_row(
            d["decision_request_id"],
            d["project_id"],
            question_short,
            d.get("status", ""),
            blocking_display,
            sent_short,
        )
    
    console.print(table)
    
    blocked_count = len([d for d in all_decisions if d["blocking_status"] == "BLOCKED"])
    waiting_count = len([d for d in all_decisions if d["blocking_status"] == "WAITING_DECISION"])
    
    console.print(f"\n[bold]Summary:[/bold] {len(all_decisions)} decision requests")
    if blocked_count > 0:
        console.print(f"  [red]BLOCKED: {blocked_count}[/red] (progress halted)")
    if waiting_count > 0:
        console.print(f"  [orange1]WAITING_DECISION: {waiting_count}[/orange1] (polling required)")
    
    for project_path in projects:
        blocking_status, request_id = check_blocking_state(project_path)
        if blocking_status in ["BLOCKED", "WAITING_DECISION"]:
            message = get_blocking_message(project_path)
            console.print(f"\n[bold]Blocking Alert ({project_path.name}):[/bold]")
            console.print(f"  {message}")
    
    console.print(f"\n[dim]Use 'asyncdev decision show --request <id>' for details[/dim]")
    console.print(f"[dim]Use 'asyncdev decision reply --request <id> --command \"DECISION A\"' to resolve[/dim]")
    console.print(f"[dim]Use 'asyncdev decision wait --request <id>' to poll for reply[/dim]")


@app.command()
def show(
    request_id: str = typer.Option(..., "--request", help="Decision request ID"),
    project: str = typer.Option(None, "--project", help="Project ID (optional, auto-detected)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed decision context with blocking state.
    
    Displays: request details, blocking state, options, recommendation, linked artifacts.
    
    Example:
        asyncdev decision show --request dr-20260422-001
    """
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    found_request = None
    found_project: Path | None = None
    
    for project_path in projects:
        store = DecisionRequestStore(project_path)
        request = store.load_request(request_id)
        if request:
            found_request = request
            found_project = project_path
            break
    
    if not found_request or not found_project:
        console.print(f"[red]Request not found: {request_id}[/red]")
        console.print("[dim]Search across all projects with --project omitted[/dim]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Decision Request: {request_id}", title="decision show", border_style="blue"))
    
    blocking_status, blocking_request_id = check_blocking_state(found_project)
    blocking_style = {"BLOCKED": "red", "WAITING_DECISION": "orange1", "CLEAR": "green"}
    style = blocking_style.get(blocking_status, "white")
    
    is_blocking = request_id == blocking_request_id
    
    info_table = Table(title="Decision Request", show_header=False)
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Request ID", request_id)
    info_table.add_row("Project", found_project.name)
    info_table.add_row("Feature", found_request.get("feature_id", "N/A"))
    info_table.add_row("Decision Type", found_request.get("decision_type", "N/A"))
    info_table.add_row("Pause Category", found_request.get("pause_reason_category", "N/A"))
    info_table.add_row("Status", found_request.get("status", "N/A"))
    info_table.add_row("Blocking State", f"[{style}]{blocking_status if is_blocking else 'CLEAR'}[/{style}]")
    info_table.add_row("Sent At", found_request.get("sent_at", "N/A")[:19])
    
    console.print(info_table)
    
    console.print(f"\n[bold]Question:[/bold] {found_request.get('question')}")
    
    options = found_request.get("options", [])
    console.print("\n[bold]Options:[/bold]")
    for opt in options:
        console.print(f"  [{opt.get('id')}] {opt.get('label')}")
        if opt.get("description"):
            console.print(f"      {opt.get('description')}")
    
    console.print(f"\n[bold]Recommendation:[/bold] {found_request.get('recommendation', 'N/A')}")
    console.print(f"[bold]Reply Format:[/bold] {found_request.get('reply_format_hint', 'N/A')}")
    
    if found_request.get("defer_impact"):
        console.print(f"\n[bold]Impact if Deferred:[/bold] {found_request.get('defer_impact')}")
    
    if is_blocking:
        message = get_blocking_message(found_project)
        console.print(f"\n[bold red]Blocking Alert:[/bold red]")
        console.print(f"  {message}")
    
    if found_request.get("resolution"):
        console.print(f"\n[bold]Resolution:[/bold] {found_request.get('resolution')}")
        console.print(f"[bold]Resolved At:[/bold] {found_request.get('resolved_at', 'N/A')[:19]}")
    
    console.print("\n[bold]Linked Artifacts:[/bold]")
    
    runstate_path = found_project / "runstate.md"
    if runstate_path.exists():
        console.print(f"  RunState: {runstate_path}")
    
    unified = reconcile_decision_sources(found_project)
    console.print(f"  Pending decisions: {unified['pending_count']}")
    console.print(f"  Resolved decisions: {unified['resolved_count']}")
    
    console.print("\n[bold]Available Actions:[/bold]")
    
    status_val = found_request.get("status", "")
    if status_val == "sent":
        console.print("  [cyan]reply[/cyan]: Reply to this decision")
        console.print("  [cyan]wait[/cyan]: Poll for asynchronous reply")
    elif status_val == "resolved":
        console.print("  [dim]Already resolved[/dim]")
    else:
        console.print(f"  [dim]Status: {status_val}[/dim]")
    
    console.print(f"\n[dim]Run: asyncdev decision reply --request {request_id} --command \"DECISION A\"[/dim]")
    console.print(f"[dim]Run: asyncdev decision wait --request {request_id}[/dim]")


@app.command()
def reply(
    request_id: str = typer.Option(..., "--request", help="Decision request ID"),
    command: str = typer.Option(..., "--command", help="Reply command (DECISION A, DEFER, RETRY, etc)"),
    project: str = typer.Option(None, "--project", help="Project ID (optional)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Process a reply to a decision request.
    
    Validates reply, updates DecisionRequestStore, syncs to RunState.
    
    Examples:
        asyncdev decision reply --request dr-20260422-001 --command "DECISION A"
        asyncdev decision reply --request dr-001 --command "DEFER"
        asyncdev decision reply --request dr-001 --command "RETRY"
    """
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    found_request = None
    found_project: Path | None = None
    store: DecisionRequestStore | None = None
    
    for project_path in projects:
        store = DecisionRequestStore(project_path)
        request = store.load_request(request_id)
        if request:
            found_request = request
            found_project = project_path
            break
    
    if not found_request or not found_project or not store:
        console.print(f"[red]Request not found: {request_id}[/red]")
        raise typer.Exit(1)
    
    if found_request.get("status") not in ["sent", "reply_received"]:
        console.print(f"[yellow]Request is {found_request.get('status')}, cannot process reply[/yellow]")
        return
    
    parsed = parse_reply(command)
    
    if not parsed.is_valid:
        console.print(f"[red]Invalid reply syntax: {command}[/red]")
        console.print(f"[yellow]Valid: DECISION A, DEFER, RETRY, CONTINUE[/yellow]")
        raise typer.Exit(1)
    
    is_valid, validation_status, error_msg = validate_reply(parsed, found_request)
    
    if not is_valid:
        console.print(f"[red]Validation failed: {validation_status.value}[/red]")
        if error_msg:
            console.print(f"[yellow]{error_msg}[/yellow]")
        raise typer.Exit(1)
    
    reply_record = create_reply_record(request_id, parsed, validation_status)
    
    store.update_request_status(
        request_id,
        DecisionRequestStatus.RESOLVED,
        resolution=reply_record["reply_value"],
        reply_raw_text=command,
    )
    
    action = map_reply_to_action(parsed, found_request)
    
    state_store = StateStore(found_project)
    runstate = state_store.load_runstate() or {}
    runstate = sync_reply_to_runstate(request_id, reply_record, runstate, action)
    state_store.save_runstate(runstate)
    
    console.print(Panel(
        f"Request: {request_id}\n"
        f"Reply: {command}\n"
        f"Status: resolved",
        title="Reply Processed",
        border_style="green"
    ))
    
    console.print(f"\n[green]Decision resolved: {command}[/green]")
    console.print(f"[cyan]Action: {action['runstate_action']}[/cyan]")
    console.print(f"[cyan]Next: {action['next_recommended']}[/cyan]")
    
    next_action = found_request.get("recommended_next_action_after_reply")
    if next_action:
        console.print(f"[dim]After reply: {next_action}[/dim]")
    
    blocking_status, _ = check_blocking_state(found_project)
    if blocking_status == "CLEAR":
        console.print(f"\n[green]All decisions resolved - no longer blocked[/green]")
    else:
        console.print(f"\n[yellow]Still blocked: {blocking_status}[/yellow]")
        console.print("[dim]Check for other pending decisions[/dim]")


@app.command()
def wait(
    request_id: str = typer.Option(..., "--request", help="Decision request ID"),
    project: str = typer.Option(None, "--project", help="Project ID (optional)"),
    interval: int = typer.Option(60, "--interval", help="Poll interval in seconds"),
    timeout: int = typer.Option(3600, "--timeout", help="Max wait time in seconds"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Poll for decision reply (blocking protocol integration).
    
    Blocks terminal until reply received or timeout.
    Auto-processes reply when found.
    
    Per Feature 064 blocking protocol:
    - Polls webhook for reply at specified interval
    - Updates RunState when reply found
    - Clears blocking state if all decisions resolved
    
    Examples:
        asyncdev decision wait --request dr-20260422-001
        asyncdev decision wait --request dr-001 --interval 30 --timeout 600
    """
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    found_request = None
    found_project: Path | None = None
    
    for project_path in projects:
        store = DecisionRequestStore(project_path)
        request = store.load_request(request_id)
        if request:
            found_request = request
            found_project = project_path
            break
    
    if not found_request or not found_project:
        console.print(f"[red]Request not found: {request_id}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"Request: {request_id}\n"
        f"Interval: {interval}s\n"
        f"Timeout: {timeout}s",
        title="Waiting for Decision Reply",
        border_style="yellow"
    ))
    
    if found_request.get("status") == "resolved":
        console.print(f"[green]Request already resolved: {found_request.get('resolution')}[/green]")
        return
    
    config = load_resend_config(found_project / ".runtime" / "resend-config.json")
    
    if not config:
        console.print("[red]No resend config found[/red]")
        console.print("[yellow]Run: asyncdev resend-auth setup[/yellow]")
        raise typer.Exit(1)
    
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        console.print("[red]No webhook URL configured[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Polling webhook: {webhook_url}[/cyan]")
    console.print(f"[dim]Waiting for reply...[/dim]")
    
    elapsed = 0
    poll_count = 0
    
    while elapsed < timeout:
        poll_count += 1
        console.print(f"[dim]Poll #{poll_count} ({elapsed}s elapsed)[/dim]")
        
        pending = poll_pending_decisions(webhook_url)
        
        if pending:
            for decision in pending:
                if decision.id == request_id:
                    console.print(f"\n[green]Reply found![/green]")
                    
                    success, message = process_pending_decision(found_project, decision)
                    
                    if success:
                        console.print(Panel(
                            f"Request: {request_id}\n"
                            f"Resolution: {message}",
                            title="Decision Resolved",
                            border_style="green"
                        ))
                        
                        blocking_status, _ = check_blocking_state(found_project)
                        if blocking_status == "CLEAR":
                            console.print(f"\n[green]All decisions resolved - unblocked[/green]")
                        else:
                            console.print(f"\n[yellow]Still blocked: {blocking_status}[/yellow]")
                        
                        return
                    else:
                        console.print(f"[yellow]Processing failed: {message}[/yellow]")
        
        import time
        time.sleep(interval)
        elapsed += interval
    
    console.print(f"\n[red]Timeout reached ({timeout}s)[/red]")
    console.print(f"[yellow]No reply received for request {request_id}[/yellow]")
    console.print(f"[dim]Manual reply: asyncdev decision reply --request {request_id} --command \"DECISION A\"[/dim]")


@app.command()
def history(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    all: bool = typer.Option(False, "--all", help="Show all projects"),
    limit: int = typer.Option(10, "--limit", help="Maximum results"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show resolved decision history.
    
    Displays resolved decision requests with resolution details.
    
    Examples:
        asyncdev decision history --all
        asyncdev decision history --project my-app --limit 20
    """
    console.print(Panel("Decision History", title="decision history", border_style="cyan"))
    
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return
    
    all_resolved = []
    
    for project_path in projects:
        store = DecisionRequestStore(project_path)
        resolved = store.list_requests(status=DecisionRequestStatus.RESOLVED)
        
        for req in resolved:
            req["project_id"] = project_path.name
        
        all_resolved.extend(resolved)
    
    if not all_resolved:
        console.print("[dim]No resolved decisions found[/dim]")
        return
    
    all_resolved.sort(key=lambda r: r.get("resolved_at", ""), reverse=True)
    all_resolved = all_resolved[:limit]
    
    table = Table(title="Resolved Decisions")
    table.add_column("Request ID", style="cyan", width=18)
    table.add_column("Project", style="green", width=15)
    table.add_column("Resolution", style="yellow", width=15)
    table.add_column("Resolved At", style="dim", width=19)
    
    for r in all_resolved:
        resolved_at = r.get("resolved_at", "N/A")
        if len(resolved_at) > 19:
            resolved_at = resolved_at[:19]
        
        table.add_row(
            r["decision_request_id"],
            r["project_id"],
            r.get("resolution", ""),
            resolved_at,
        )
    
    console.print(table)
    
    console.print(f"\n[bold]Total:[/bold] {len(all_resolved)} resolved decisions")
    
    if len(all_resolved) == limit:
        console.print(f"[dim]Limited to {limit} results. Use --limit for more.[/dim]")


if __name__ == "__main__":
    app()