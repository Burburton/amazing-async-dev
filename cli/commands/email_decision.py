"""email-decision command - Async human decision channel (Feature 021)."""

import os
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
    DecisionType,
    DeliveryChannel,
)
from runtime.email_sender import create_email_config, EmailSender
from runtime.resend_provider import apply_resend_config_from_file
from runtime.reply_parser import (
    parse_reply,
    validate_reply,
    create_reply_record,
    ValidationStatus,
    ReplyCommand,
)
from runtime.decision_sync import sync_decision_to_runstate, sync_reply_to_runstate
from runtime.reply_action_mapper import map_reply_to_action
from runtime.state_store import StateStore

app = typer.Typer(help="Async decision channel (Feature 021)")
console = Console()


@app.command()
def create(
    project: str = typer.Option(..., help="Product ID"),
    feature: str = typer.Option(..., help="Feature ID"),
    question: str = typer.Option(..., help="Decision question"),
    options: str = typer.Option(..., help="Options as A:Label,B:Label,C:Label"),
    recommendation: str = typer.Option("", help="Recommendation"),
    category: str = typer.Option("decision_required", help="Pause reason category"),
    decision_type: str = typer.Option("technical", help="Decision type"),
    defer_impact: str = typer.Option("", help="What happens if deferred"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    send: bool = typer.Option(True, help="Send after creating"),
):
    """Create a decision request.
    
    Example:
        asyncdev email-decision create --project my-app --feature 001 \
            --question "Use YAML or JSON?" --options "A:YAML,B:JSON" \
            --recommendation "A" --send
    """
    project_path = path / project
    
    store = DecisionRequestStore(project_path)
    
    parsed_options = []
    for opt in options.split(","):
        if ":" in opt:
            id_part, label_part = opt.split(":", 1)
            parsed_options.append({"id": id_part.strip(), "label": label_part.strip(), "description": ""})
        else:
            parsed_options.append({"id": opt.strip(), "label": opt.strip(), "description": ""})
    
    try:
        dt = DecisionType(decision_type)
    except ValueError:
        dt = DecisionType.TECHNICAL
    
    delivery_mode = os.getenv("ASYNCDEV_DELIVERY_MODE", "mock_file")
    if delivery_mode == "resend":
        delivery_channel = DeliveryChannel.RESEND
    elif delivery_mode == "console":
        delivery_channel = DeliveryChannel.CONSOLE
    else:
        delivery_channel = DeliveryChannel.MOCK_FILE
    
    request = store.create_request(
        product_id=project,
        feature_id=feature,
        pause_reason_category=category,
        decision_type=dt,
        question=question,
        options=parsed_options,
        recommendation=recommendation,
        defer_impact=defer_impact if defer_impact else None,
        delivery_channel=delivery_channel,
    )
    
    console.print(Panel(
        f"Request ID: {request['decision_request_id']}\n"
        f"Question: {question}\n"
        f"Options: {len(parsed_options)}",
        title="Decision Request Created",
        border_style="green"
    ))
    
    if send:
        apply_resend_config_from_file()
        config = create_email_config(project_path)
        sender = EmailSender(config)
        success, mock_path = sender.send_decision_request(request)
        
        if success:
            store.mark_sent(
                request["decision_request_id"],
                mock_path=mock_path,
            )
            if config.delivery_mode == "resend":
                console.print(f"[green]Email sent via Resend: Message ID {mock_path}[/green]")
            elif config.delivery_mode == "console":
                console.print("[yellow]Email output above (console mode)[/yellow]")
            else:
                console.print(f"[green]Email sent (mock): {mock_path}[/green]")
            
            state_store = StateStore(project_path)
            runstate = state_store.load_runstate() or {}
            runstate = sync_decision_to_runstate(request, runstate)
            state_store.save_runstate(runstate)
            console.print("[cyan]Synced to RunState.decisions_needed[/cyan]")
        else:
            console.print("[red]Failed to send[/red]")
    
    if not send:
        state_store = StateStore(project_path)
        runstate = state_store.load_runstate() or {}
        runstate = sync_decision_to_runstate(request, runstate)
        state_store.save_runstate(runstate)
        console.print("[cyan]Synced to RunState.decisions_needed[/cyan]")
        console.print("[yellow]Created but not sent. Use --send to send.[/yellow]")


@app.command()
def list(
    project: str = typer.Option(..., help="Product ID"),
    status: str = typer.Option(None, help="Filter by status"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List decision requests.
    
    Example:
        asyncdev email-decision list --project my-app
        asyncdev email-decision list --project my-app --status sent
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    filter_status = None
    if status:
        try:
            filter_status = DecisionRequestStatus(status)
        except ValueError:
            console.print(f"[red]Invalid status: {status}[/red]")
            raise typer.Exit(1)
    
    requests = store.list_requests(status=filter_status)
    
    if not requests:
        console.print("[yellow]No decision requests found[/yellow]")
        return
    
    table = Table(title="Decision Requests")
    table.add_column("ID", style="cyan")
    table.add_column("Question", style="white")
    table.add_column("Status", style="green")
    table.add_column("Sent At", style="blue")
    
    for req in requests:
        table.add_row(
            req.get("decision_request_id", ""),
            req.get("question", "")[:50],
            req.get("status", ""),
            req.get("sent_at", "")[:19],
        )
    
    console.print(table)
    
    stats = store.get_statistics()
    console.print(f"\n[dim]Statistics: {stats}[/dim]")


@app.command()
def show(
    project: str = typer.Option(..., help="Product ID"),
    request_id: str = typer.Option(..., "--id", help="Decision request ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show decision request details.
    
    Example:
        asyncdev email-decision show --project my-app --id dr-20260412-001
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    request = store.load_request(request_id)
    
    if not request:
        console.print(f"[red]Request not found: {request_id}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"ID: {request.get('decision_request_id')}\n"
        f"Product: {request.get('product_id')}\n"
        f"Feature: {request.get('feature_id')}\n"
        f"Category: {request.get('pause_reason_category')}\n"
        f"Type: {request.get('decision_type')}\n"
        f"Status: {request.get('status')}",
        title="Decision Request",
        border_style="blue"
    ))
    
    console.print(f"\n[bold]Question:[/bold] {request.get('question')}")
    
    options = request.get("options", [])
    console.print("\n[bold]Options:[/bold]")
    for opt in options:
        console.print(f"  [{opt.get('id')}] {opt.get('label')}")
    
    console.print(f"\n[bold]Recommendation:[/bold] {request.get('recommendation')}")
    console.print(f"[bold]Reply format:[/bold] {request.get('reply_format_hint')}")
    
    if request.get("resolution"):
        console.print(f"\n[bold]Resolution:[/bold] {request.get('resolution')}")
    
    if request.get("email_sent_mock_path"):
        console.print(f"\n[dim]Mock email: {request.get('email_sent_mock_path')}[/dim]")


@app.command()
def send(
    project: str = typer.Option(..., help="Product ID"),
    request_id: str = typer.Option(..., "--id", help="Decision request ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Send decision request email.
    
    Example:
        asyncdev email-decision send --project my-app --id dr-20260412-001
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    request = store.load_request(request_id)
    if not request:
        console.print(f"[red]Request not found: {request_id}[/red]")
        raise typer.Exit(1)
    
    if request.get("status") not in ["pending", "sent"]:
        console.print(f"[yellow]Request already {request.get('status')}[/yellow]")
        return
    
    apply_resend_config_from_file()
    if os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL"):
        os.environ["ASYNCDEV_DELIVERY_MODE"] = "resend"
    config = create_email_config(project_path)
    sender = EmailSender(config)
    
    success, mock_path = sender.send_decision_request(request)
    
    if success:
        store.mark_sent(request_id, mock_path=mock_path)
        if config.delivery_mode == "resend":
            console.print(f"[green]Email sent via Resend: Message ID {mock_path}[/green]")
        elif config.delivery_mode == "console":
            console.print("[yellow]Email output above (console mode)[/yellow]")
        else:
            console.print(f"[green]Email sent (mock): {mock_path}[/green]")
    else:
        console.print("[red]Failed to send email[/red]")
        raise typer.Exit(1)


@app.command()
def reply(
    project: str = typer.Option(..., help="Product ID"),
    request_id: str = typer.Option(..., "--id", help="Decision request ID"),
    command: str = typer.Option(..., help="Reply command (DECISION A, DEFER, RETRY, etc)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Process a reply to a decision request.
    
    Example:
        asyncdev email-decision reply --project my-app --id dr-20260412-001 --command "DECISION A"
        asyncdev email-decision reply --project my-app --id dr-001 --command "DEFER"
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    request = store.load_request(request_id)
    if not request:
        console.print(f"[red]Request not found: {request_id}[/red]")
        raise typer.Exit(1)
    
    if request.get("status") not in ["sent", "reply_received"]:
        console.print(f"[yellow]Request is {request.get('status')}, cannot process reply[/yellow]")
        return
    
    parsed = parse_reply(command)
    
    if not parsed.is_valid:
        console.print(f"[red]Invalid reply syntax: {command}[/red]")
        console.print(f"[yellow]Valid: DECISION A, DEFER, RETRY, CONTINUE[/yellow]")
        raise typer.Exit(1)
    
    is_valid, validation_status, error_msg = validate_reply(parsed, request)
    
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
    
    action = map_reply_to_action(parsed, request)
    
    state_store = StateStore(project_path)
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
    
    next_action = request.get("recommended_next_action_after_reply")
    if next_action:
        console.print(f"[dim]After reply: {next_action}[/dim]")


@app.command()
def check_replies(
    project: str = typer.Option(..., help="Product ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    inbox_path: Path = typer.Option(None, help="Inbox path (for mock mode)"),
):
    """Check for new replies (manual pull mode).
    
    Example:
        asyncdev email-decision check-replies --project my-app
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    sent_requests = store.list_requests(status=DecisionRequestStatus.SENT)
    
    if not sent_requests:
        console.print("[yellow]No pending requests[/yellow]")
        return
    
    console.print(f"[cyan]Checking for replies to {len(sent_requests)} pending requests...[/cyan]")
    
    if inbox_path:
        console.print(f"[dim]Inbox path: {inbox_path}[/dim]")
        console.print("[yellow]Mock inbox checking not yet implemented[/yellow]")
        console.print("[yellow]Use 'reply' command to manually process replies[/yellow]")
    else:
        console.print("[yellow]No inbox configured. Use --inbox-path for mock mode[/yellow]")
        console.print("[yellow]Use 'reply' command to manually process replies[/yellow]")
    
    for req in sent_requests:
        console.print(f"  Pending: {req.get('decision_request_id')} - {req.get('question', '')[:40]}")


@app.command()
def expire(
    project: str = typer.Option(..., help="Product ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check and mark expired requests.
    
    Example:
        asyncdev email-decision expire --project my-app
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    expired = store.check_expired()
    
    if not expired:
        console.print("[green]No expired requests[/green]")
        return
    
    console.print(f"[yellow]Marked {len(expired)} requests as expired[/yellow]")
    
    for req in expired:
        console.print(f"  {req.get('decision_request_id')}: {req.get('question', '')[:40]}")


@app.command()
def stats(
    project: str = typer.Option(..., help="Product ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show decision request statistics.
    
    Example:
        asyncdev email-decision stats --project my-app
    """
    project_path = path / project
    store = DecisionRequestStore(project_path)
    
    stats = store.get_statistics()
    
    table = Table(title="Decision Request Statistics")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="green")
    
    for status, count in stats.items():
        table.add_row(status, str(count))
    
    console.print(table)


@app.command()
def status_report(
    project: str = typer.Option(..., help="Product ID"),
    feature: str = typer.Option("", help="Feature ID"),
    type: str = typer.Option("progress", help="Report type (progress/milestone/blocker/dogfood)"),
    summary: str = typer.Option("", help="One-line summary"),
    changes: str = typer.Option("", help="Changes (comma-separated)"),
    state: str = typer.Option("active", help="Current state"),
    risks: str = typer.Option("", help="Risks/blockers (comma-separated)"),
    next: str = typer.Option("", help="Next step"),
    reply: bool = typer.Option(False, help="Whether reply is required"),
    send: bool = typer.Option(True, help="Send after creating"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Create and send a high-signal status report (Feature 044).
    
    Example:
        asyncdev email-decision status-report --project my-app --feature 001 \
            --type progress --summary "Progress: 3 items done" \
            --changes "item1,item2,item3" --state "testing"
    """
    from runtime.status_report_builder import build_status_report, format_report_for_email
    from runtime.email_sender import create_email_config, EmailSender
    
    project_path = path / project
    
    what_changed = [c.strip() for c in changes.split(",")] if changes else []
    risks_blockers = [r.strip() for r in risks.split(",")] if risks else None
    
    if type not in ["progress", "milestone", "blocker", "dogfood"]:
        type = "progress"
    
    if not summary:
        summary = f"{type.capitalize()} update for {project}/{feature}"
    
    report = build_status_report(
        report_type=type,
        project_id=project,
        feature_id=feature,
        summary=summary,
        what_changed=what_changed,
        current_state=state,
        risks_blockers=risks_blockers,
        next_step=next if next else None,
        reply_required=reply,
    )
    
    console.print(Panel(
        f"Report ID: {report['report_id']}\n"
        f"Type: {type}\n"
        f"Summary: {summary[:40]}...\n"
        f"Changes: {len(what_changed)} items\n"
        f"Reply required: {reply}",
        title="Status Report Created",
        border_style="green"
    ))
    
    if send:
        config = create_email_config(project_path)
        sender = EmailSender(config)
        success, mock_path = sender.send_status_report(report)
        
        if success:
            console.print(f"[green]Report sent (mock): {mock_path}[/green]")
        else:
            console.print("[red]Failed to send[/red]")
    
    if not send:
        console.print("\n[bold]Report Preview:[/bold]")
        console.print(format_report_for_email(report))


@app.command()
def escalation_check(
    project: str = typer.Option(..., help="Product ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    trigger: str = typer.Option(None, help="Trigger type to check"),
):
    """Check if email should be sent based on escalation policy (Feature 048).
    
    Example:
        asyncdev email-decision escalation-check --project my-app
        asyncdev email-decision escalation-check --project my-app --trigger escalation_blocker
    """
    from runtime.email_escalation_policy import (
        EmailTriggerType,
        should_send_email,
        get_appropriate_triggers_for_runstate,
        format_escalation_summary,
        classify_email_type,
        get_email_urgency,
    )
    from runtime.state_store import StateStore
    
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if not runstate:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)
    
    triggers = get_appropriate_triggers_for_runstate(runstate)
    
    if trigger:
        try:
            trigger_type = EmailTriggerType(trigger)
            triggers = [trigger_type]
        except ValueError:
            console.print(f"[red]Invalid trigger: {trigger}[/red]")
            console.print(f"[yellow]Valid triggers: {[t.value for t in EmailTriggerType]}[/yellow]")
            raise typer.Exit(1)
    
    if not triggers:
        console.print("[green]No escalation triggers detected[/green]")
        console.print("[dim]RunState has no blockers, decisions, or risky actions[/dim]")
        return
    
    console.print(f"[cyan]Found {len(triggers)} potential triggers[/cyan]")
    
    table = Table(title="Escalation Policy Check")
    table.add_column("Trigger", style="cyan")
    table.add_column("Should Send", style="green")
    table.add_column("Urgency", style="yellow")
    table.add_column("Email Type", style="magenta")
    table.add_column("Reason", style="white")
    
    for trigger_type in triggers:
        should, reason, explanation = should_send_email(runstate, trigger_type)
        urgency = get_email_urgency(trigger_type)
        email_type, email_desc = classify_email_type(trigger_type)
        
        table.add_row(
            trigger_type.value,
            str(should),
            urgency.value,
            email_type,
            explanation[:50] if explanation else "",
        )
    
    console.print(table)
    
    console.print("\n[bold]Policy Mode:[/bold] " + runstate.get("policy_mode", "balanced"))
    
    blockers = runstate.get("blocked_items", [])
    decisions = runstate.get("decisions_needed", [])
    risky = runstate.get("pending_risky_actions", [])
    
    console.print(f"[bold]Blocked Items:[/bold] {len(blockers)}")
    console.print(f"[bold]Decisions Needed:[/bold] {len(decisions)}")
    console.print(f"[bold]Risky Actions:[/bold] {len(risky)}")


@app.command()
def failures(
    project: str = typer.Option(..., help="Product ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    unresolved: bool = typer.Option(False, help="Show only unresolved failures"),
    request_id: str = typer.Option(None, help="Filter by request ID"),
):
    """List email channel failure records (Feature 049).
    
    Example:
        asyncdev email-decision failures --project my-app
        asyncdev email-decision failures --project my-app --unresolved
        asyncdev email-decision failures --project my-app --request-id dr-001
    """
    from runtime.email_failure_handler import FailureRecordStore
    
    project_path = path / project
    store = FailureRecordStore(project_path)
    
    failures = store.list_failures(
        request_id=request_id,
        unresolved_only=unresolved,
    )
    
    if not failures:
        console.print("[green]No failure records found[/green]")
        return
    
    table = Table(title="Email Channel Failures")
    table.add_column("Failure ID", style="cyan")
    table.add_column("Request", style="blue")
    table.add_column("Type", style="yellow")
    table.add_column("Resolved", style="green")
    table.add_column("Occurred", style="magenta")
    
    for failure in failures:
        table.add_row(
            failure.get("failure_id", ""),
            failure.get("request_id", ""),
            failure.get("failure_type", ""),
            str(failure.get("resolved", False)),
            failure.get("occurred_at", "")[:19],
        )
    
    console.print(table)
    
    unresolved_count = len([f for f in failures if not f.get("resolved")])
    console.print(f"\n[bold]Total:[/bold] {len(failures)} failures, {unresolved_count} unresolved")


@app.command()
def resolve_failure(
    project: str = typer.Option(..., help="Product ID"),
    failure_id: str = typer.Option(..., "--id", help="Failure ID"),
    action: str = typer.Option("pause_for_human", help="Recovery action"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Resolve a failure record (Feature 049).
    
    Example:
        asyncdev email-decision resolve-failure --project my-app --id fail-001 --action retry_send
    """
    from runtime.email_failure_handler import FailureRecordStore, RecoveryAction
    
    project_path = path / project
    store = FailureRecordStore(project_path)
    
    try:
        recovery = RecoveryAction(action)
    except ValueError:
        console.print(f"[red]Invalid action: {action}[/red]")
        console.print(f"[yellow]Valid actions: {[a.value for a in RecoveryAction]}[/yellow]")
        raise typer.Exit(1)
    
    resolved = store.resolve_failure(failure_id, recovery)
    
    if not resolved:
        console.print(f"[red]Failure not found: {failure_id}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"Failure ID: {failure_id}\n"
        f"Action: {action}\n"
        f"Resolved At: {resolved.get('resolved_at', '')}",
        title="Failure Resolved",
        border_style="green"
    ))


@app.command()
def check_timeout(
    project: str = typer.Option(..., help="Product ID"),
    request_id: str = typer.Option(None, "--id", help="Check specific request"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check for timeout conditions on pending requests (Feature 049).
    
    Example:
        asyncdev email-decision check-timeout --project my-app
        asyncdev email-decision check-timeout --project my-app --id dr-001
    """
    from runtime.email_failure_handler import (
        handle_timeout,
        get_timeout_policy,
        FailureRecordStore,
    )
    from runtime.decision_request_store import DecisionRequestStore, DecisionRequestStatus
    
    project_path = path / project
    req_store = DecisionRequestStore(project_path)
    fail_store = FailureRecordStore(project_path)
    
    pending = req_store.list_requests(status=DecisionRequestStatus.SENT)
    
    if request_id:
        pending = [r for r in pending if r.get("decision_request_id") == request_id]
    
    if not pending:
        console.print("[green]No pending requests to check[/green]")
        return
    
    console.print(f"[cyan]Checking {len(pending)} pending requests[/cyan]")
    
    table = Table(title="Timeout Check")
    table.add_column("Request ID", style="cyan")
    table.add_column("Sent At", style="blue")
    table.add_column("Hours Elapsed", style="yellow")
    table.add_column("Policy", style="magenta")
    table.add_column("Needs Timeout", style="green")
    
    timeout_count = 0
    
    for req in pending:
        sent_at = req.get("sent_at")
        if sent_at:
            sent_dt = datetime.fromisoformat(sent_at)
            hours_elapsed = (datetime.now() - sent_dt).total_seconds() / 3600
            
            category = req.get("pause_reason_category", "technical")
            policy_mode = req.get("policy_mode", "balanced")
            timeout_behavior = get_timeout_policy(policy_mode, category)
            
            needs_timeout = hours_elapsed >= 48
            
            if needs_timeout:
                timeout_count += 1
                fail_store.record_failure(
                    req.get("decision_request_id"),
                    "timeout_no_reply",
                    {"hours_elapsed": hours_elapsed},
                )
            
            table.add_row(
                req.get("decision_request_id", ""),
                sent_at[:19],
                f"{hours_elapsed:.1f}",
                timeout_behavior.value,
                str(needs_timeout),
            )
    
    console.print(table)
    
    if timeout_count > 0:
        console.print(f"\n[yellow]{timeout_count} requests need timeout handling[/yellow]")
    else:
        console.print(f"\n[green]All requests within timeout threshold[/green]")