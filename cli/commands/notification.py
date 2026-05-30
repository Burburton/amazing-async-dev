"""notification command - Notification management CLI (Feature 080)."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.notification_event import (
    NotificationEventType,
    NotificationStatus,
)
from runtime.notification_store import NotificationStore

app = typer.Typer(help="Notification management for async-dev platform")
console = Console()


@app.command()
def list(
    project: str = typer.Option(..., help="Project ID"),
    status: str = typer.Option(None, help="Filter by status (pending/sent/delivered/failed/skipped)"),
    event_type: str = typer.Option(None, help="Filter by event type"),
    unresolved: bool = typer.Option(False, help="Show only unresolved notifications"),
    limit: int = typer.Option(20, help="Maximum results"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List notifications for a project.

    Examples:
        asyncdev notification list --project my-app
        asyncdev notification list --project my-app --status pending
        asyncdev notification list --project my-app --unresolved
    """
    project_path = path / project
    store = NotificationStore(project_path)

    filter_status = None
    if status:
        try:
            filter_status = NotificationStatus(status)
        except ValueError:
            console.print(f"[red]Invalid status: {status}[/red]")
            console.print(f"[yellow]Valid: {[s.value for s in NotificationStatus]}[/yellow]")
            raise typer.Exit(1)

    filter_type = None
    if event_type:
        try:
            filter_type = NotificationEventType(event_type)
        except ValueError:
            console.print(f"[red]Invalid event type: {event_type}[/red]")
            console.print(f"[yellow]Valid: {[t.value for t in NotificationEventType]}[/yellow]")
            raise typer.Exit(1)

    notifications = store.list_notifications(
        status=filter_status,
        event_type=filter_type,
        unresolved_only=unresolved,
    )[:limit]

    if not notifications:
        console.print("[yellow]No notifications found[/yellow]")
        return

    table = Table(title="Notifications")
    table.add_column("Event ID", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Severity", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Sent", style="yellow")
    table.add_column("Created", style="white")

    for notif in notifications:
        table.add_row(
            notif.event_id,
            notif.event_type.value,
            notif.severity.value,
            notif.delivery_status.value,
            str(notif.email_sent),
            notif.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)

    stats = store.get_statistics()
    console.print(f"\n[dim]Statistics: {stats}[/dim]")


@app.command()
def show(
    project: str = typer.Option(..., help="Project ID"),
    event_id: str = typer.Option(..., "--id", help="Notification event ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show notification details.

    Example:
        asyncdev notification show --project my-app --id notif-20260425-001
    """
    project_path = path / project
    store = NotificationStore(project_path)

    notification = store.load_notification(event_id)

    if not notification:
        console.print(f"[red]Notification not found: {event_id}[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        f"Event ID: {notification.event_id}\n"
        f"Type: {notification.event_type.value}\n"
        f"Severity: {notification.severity.value}\n"
        f"Status: {notification.delivery_status.value}\n"
        f"Dedupe Key: {notification.dedupe_key}",
        title="Notification",
        border_style="blue"
    ))

    console.print(f"\n[bold]Product/Feature:[/bold] {notification.product_id} / {notification.feature_id}")

    if notification.run_id:
        console.print(f"[bold]Run ID:[/bold] {notification.run_id}")

    if notification.request_id:
        console.print(f"[bold]Request ID:[/bold] {notification.request_id}")

    console.print(f"\n[bold]Reason:[/bold] {notification.reason}")

    if notification.message:
        console.print(f"\n[bold]Message:[/bold] {notification.message}")

    if notification.email_sent:
        console.print(f"\n[bold green]Email Sent:[/bold green] {notification.email_sent_at}")
        if notification.resend_message_id:
            console.print(f"[bold]Message ID:[/bold] {notification.resend_message_id}")

    if notification.error_message:
        console.print(f"\n[bold red]Error:[/bold red] {notification.error_message}")

    if notification.related_artifacts:
        console.print("\n[bold]Related Artifacts:[/bold]")
        for artifact in notification.related_artifacts:
            console.print(f"  - {artifact}")

    console.print(f"\n[dim]Created: {notification.created_at}[/dim]")
    if notification.expires_at:
        console.print(f"[dim]Expires: {notification.expires_at}[/dim]")


@app.command()
def pending(
    project: str = typer.Option(..., help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show pending notifications awaiting send.

    Example:
        asyncdev notification pending --project my-app
    """
    project_path = path / project
    store = NotificationStore(project_path)

    notifications = store.get_pending_notifications()

    if not notifications:
        console.print("[green]No pending notifications[/green]")
        return

    console.print(f"[yellow]{len(notifications)} pending notifications:[/yellow]")

    for notif in notifications:
        console.print(f"\n  Event: {notif.event_id}")
        console.print(f"  Type: {notif.event_type.value}")
        console.print(f"  Reason: {notif.reason}")
        console.print(f"  Created: {notif.created_at}")


@app.command()
def stats(
    project: str = typer.Option(..., help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show notification statistics.

    Example:
        asyncdev notification stats --project my-app
    """
    project_path = path / project
    store = NotificationStore(project_path)

    stats = store.get_statistics()

    table = Table(title="Notification Statistics")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="green")

    for status, count in stats.items():
        table.add_row(status, str(count))

    console.print(table)

    total = sum(stats.values())
    console.print(f"\n[bold]Total notifications: {total}[/bold]")

    unresolved = stats.get("pending", 0) + stats.get("retry_needed", 0)
    if unresolved > 0:
        console.print(f"[yellow]Unresolved: {unresolved}[/yellow]")


@app.command()
def retry(
    project: str = typer.Option(..., help="Project ID"),
    event_id: str = typer.Option(None, "--id", help="Specific notification to retry"),
    all_failed: bool = typer.Option(False, help="Retry all failed notifications"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Retry failed notifications.

    Examples:
        asyncdev notification retry --project my-app --id notif-001
        asyncdev notification retry --project my-app --all-failed
    """
    project_path = path / project
    store = NotificationStore(project_path)

    if event_id:
        notification = store.load_notification(event_id)
        if not notification:
            console.print(f"[red]Notification not found: {event_id}[/red]")
            raise typer.Exit(1)

        if notification.delivery_status not in [
            NotificationStatus.FAILED,
            NotificationStatus.RETRY_NEEDED,
        ]:
            console.print(f"[yellow]Notification is not failed: {notification.delivery_status.value}[/yellow]")
            return

        console.print(f"[cyan]Retrying notification: {event_id}[/cyan]")
        console.print("[yellow]Manual retry requires re-triggering via email-decision command[/yellow]")
        console.print("[dim]Use: asyncdev email-decision send --project {project} --id {request_id}[/dim]")
        return

    if all_failed:
        failed = store.list_notifications(status=NotificationStatus.RETRY_NEEDED)

        if not failed:
            console.print("[green]No notifications needing retry[/green]")
            return

        console.print(f"[yellow]{len(failed)} notifications need retry[/yellow]")
        for notif in failed:
            console.print(f"  {notif.event_id}: {notif.event_type.value}")

        console.print("\n[yellow]Manual retry required for each[/yellow]")
        return

    console.print("[yellow]Specify --id or --all-failed[/yellow]")


@app.command()
def clear_expired(
    project: str = typer.Option(..., help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Clear expired dedupe keys from index.

    Example:
        asyncdev notification clear-expired --project my-app
    """
    project_path = path / project
    store = NotificationStore(project_path)

    cleared = store.clear_expired_dedupe_keys()

    console.print(f"[green]Cleared {cleared} expired dedupe entries[/green]")


@app.command()
def day_end_status(
    project: str = typer.Option(..., help="Project ID"),
    date: str = typer.Option(None, help="Check specific date (YYYY-MM-DD)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check if day-end email was sent for a date.

    Example:
        asyncdev notification day-end-status --project my-app --date 2026-04-25
    """
    from datetime import datetime

    project_path = path / project
    store = NotificationStore(project_path)

    check_date = date or datetime.now().strftime("%Y-%m-%d")

    dedupe_key = f"day_end_summary_ready:review:{check_date}"
    existing = store.load_notification_by_dedupe_key(dedupe_key)

    if existing:
        console.print(Panel(
            f"Date: {check_date}\n"
            f"Event ID: {existing.event_id}\n"
            f"Status: {existing.delivery_status.value}\n"
            f"Sent: {existing.email_sent}\n"
            f"Sent At: {existing.email_sent_at or 'N/A'}",
            title="Day-End Email Status",
            border_style="green"
        ))
    else:
        console.print(f"[yellow]No day-end notification for {check_date}[/yellow]")
        console.print("[dim]Run 'asyncdev review-night generate' to trigger[/dim]")


@app.command()
def test(
    project: str = typer.Option(..., help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Test notification configuration and connectivity.

    Verifies:
    - Project notification store is accessible
    - Email channel is configured (via env vars)
    - Notification queue is functional

    Example:
        asyncdev notification test --project my-app
    """
    project_path = path / project

    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)

    store = NotificationStore(project_path)
    issues = []
    warnings = []

    try:
        store.list_notifications()
        console.print("[green]Notification store: OK[/green]")
    except Exception as e:
        issues.append(f"Notification store error: {e}")

    import os
    email_configured = all([
        os.getenv("GMAIL_CLIENT_ID"),
        os.getenv("GMAIL_CLIENT_SECRET"),
        os.getenv("GMAIL_REFRESH_TOKEN"),
    ])

    if email_configured:
        console.print("[green]Email channel: configured[/green]")
    else:
        warnings.append("Email channel: not configured (GMAIL_* env vars missing)")

    if warnings:
        for w in warnings:
            console.print(f"[yellow]{w}[/yellow]")

    if issues:
        for i in issues:
            console.print(f"[red]{i}[/red]")
        raise typer.Exit(1)

    if not warnings and not issues:
        console.print("[green]All notification systems operational[/green]")


@app.command()
def preview(
    email_type: str = typer.Argument(..., help="Email type: decision, day-end, execution-failed, verification-failed"),
    project: str = typer.Option(..., "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Preview email content without sending.

    Example:
        asyncdev notification preview decision --project my-app
        asyncdev notification preview day-end --project my-app
    """
    from rich.syntax import Syntax

    from runtime.email_sender import render_html_email

    project_path = path / project

    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)

    if email_type == "decision":
        context = {
            "subject": "Decision Needed: Continue or Change Approach?",
            "product_id": project,
            "feature_id": "feature-001",
            "request_id": "preview-001",
            "question": "Should we continue with the current implementation or change approach?",
            "options": [
                {"id": "A", "label": "Continue", "description": "Keep current implementation"},
                {"id": "B", "label": "Change", "description": "Switch to alternative approach"},
                {"id": "DEFER", "label": "Defer", "description": "Decide later"},
            ],
            "recommendation": "Continue - progress is good",
            "defer_impact": "Can proceed while waiting for decision",
            "reply_hint": "DECISION A, B, or DEFER",
            "next_action": "Continue implementation",
            "sent_at": "2026-05-24T12:00:00",
            "reply_base_url": "https://async-dev.example.com/reply",
        }
        template_name = "decision-request.html"

    elif email_type == "day-end":
        context = {
            "date": "2026-05-24",
            "product_id": project,
            "feature_id": "feature-001",
            "today_goal": "Complete Phase 1 implementation",
            "completed": ["Built email templates", "Added HTML rendering", "Created execution failed alerts"],
            "blocked": [],
            "decisions": [
                {
                    "question": "Should we add HTML email templates?",
                    "options": [
                        {"id": "A", "label": "Yes"},
                        {"id": "B", "label": "No"},
                    ],
                    "recommendation": "Yes - better UX",
                }
            ],
            "tomorrow_plan": "Continue with Phase 2",
            "doctor_status": "HEALTHY",
            "recommended_action": "Proceed with current plan",
            "artifact_links": [
                {"name": "Execution Result", "url": "https://async-dev.example.com/execution/exec-001"},
                {"name": "Review Pack", "url": "https://async-dev.example.com/review/rev-001"},
            ],
            "request_id": "preview-001",
            "reply_base_url": "https://async-dev.example.com/reply",
        }
        template_name = "day-end-summary.html"

    elif email_type == "execution-failed":
        context = {
            "project_id": project,
            "feature_id": "feature-001",
            "execution_id": "exec-001",
            "error_summary": "Connection timeout after 30 seconds",
            "what_was_attempted": "Fetching data from external API",
            "duration": "45 minutes",
            "impact": "Execution cannot complete without API data",
            "failed_at": "2026-05-24T12:00:00",
            "retry_url": "https://async-dev.example.com/retry/exec-001",
            "view_details_url": "https://async-dev.example.com/execution/exec-001",
        }
        template_name = "execution-failed.html"

    elif email_type == "verification-failed":
        context = {
            "project_id": project,
            "feature_id": "feature-001",
            "verification_id": "ver-001",
            "failure_reason": "Element not found: #login-button",
            "what_was_verified": "Login flow",
            "scenarios_run": 5,
            "scenarios_passed": 3,
            "screenshot_urls": ["https://example.com/screenshot1.png"],
            "failed_at": "2026-05-24T12:00:00",
            "retry_url": "https://async-dev.example.com/verify/retry/ver-001",
            "view_details_url": "https://async-dev.example.com/verify/ver-001",
        }
        template_name = "verification-failed.html"

    else:
        console.print(f"[red]Unknown email type: {email_type}[/red]")
        console.print("[yellow]Available types: decision, day-end, execution-failed, verification-failed[/yellow]")
        raise typer.Exit(1)

    html_content = render_html_email(template_name, context)

    if html_content:
        console.print(Panel(
            f"Email Type: {email_type}\nTemplate: {template_name}",
            title="Email Preview",
            border_style="blue"
        ))
        console.print("\n[dim]--- HTML Content (first 2000 chars) ---[/dim]\n")
        syntax = Syntax(html_content[:2000], "html", theme="monokai")
        console.print(syntax)
        if len(html_content) > 2000:
            console.print(f"\n[dim]... ({len(html_content) - 2000} more characters)[/dim]")
    else:
        console.print("[yellow]Template not found or rendering failed[/yellow]")
        console.print(f"[dim]Tried to render: {template_name}[/dim]")


@app.command()
def templates_list(
):
    """List available email templates.

    Example:
        asyncdev notification templates-list
    """
    from pathlib import Path

    templates_path = Path(__file__).parent.parent.parent / "templates" / "email"

    console.print(Panel(
        "Available Email Templates",
        title="Email Templates",
        border_style="blue"
    ))

    if not templates_path.exists():
        console.print("[yellow]Templates directory not found[/yellow]")
        raise typer.Exit(1)

    import builtins
    template_files = builtins.list(templates_path.glob("*.html"))
    template_files = [t for t in template_files if not t.name.startswith("_")]

    if not template_files:
        console.print("[yellow]No templates found[/yellow]")
    else:
        table = Table(title="Templates", show_header=True)
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="green")

        descriptions = {
            "decision-request.html": "Decision request with options",
            "day-end-summary.html": "Daily review summary",
            "execution-failed.html": "Execution failure alert",
            "verification-failed.html": "Verification failure alert",
        }

        for tmpl in sorted(template_files):
            desc = descriptions.get(tmpl.name, tmpl.name)
            table.add_row(tmpl.name, desc)

        console.print(table)


@app.command()
def preferences_show(
    project: str = typer.Option(..., help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show email notification preferences for a project.

    Example:
        asyncdev notification preferences-show --project my-app
    """
    from runtime.notification_store import EmailPreferences

    project_path = path / project
    prefs = EmailPreferences(project_path)
    data = prefs.load()

    table = Table(title=f"Email Preferences: {project}")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in data.items():
        table.add_row(key, str(value))

    console.print(table)


@app.command()
def preferences_set(
    project: str = typer.Option(..., help="Project ID"),
    key: str = typer.Option(..., help="Preference key"),
    value: str = typer.Option(..., help="New value"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Set an email notification preference.

    Available keys:
        decision_requests: Enable decision request emails (true/false)
        day_end_summary: Enable day-end summary emails (true/false)
        execution_failed: Enable execution failed emails (true/false)
        verification_failed: Enable verification failed emails (true/false)
        severity_threshold: Minimum severity to notify (critical/high/medium/low/info)
        reply_base_url: URL for email reply actions

    Examples:
        asyncdev notification preferences-set --project my-app --key decision_requests --value false
        asyncdev notification preferences-set --project my-app --key severity_threshold --value high
    """
    from runtime.notification_store import EmailPreferences

    project_path = path / project
    prefs = EmailPreferences(project_path)

    if key == "severity_threshold":
        valid = ["critical", "high", "medium", "low", "info"]
        if value not in valid:
            console.print(f"[red]Invalid severity: {value}[/red]")
            console.print(f"[yellow]Valid: {valid}[/yellow]")
            raise typer.Exit(1)
        prefs.set(key, value)
    elif key in ["decision_requests", "day_end_summary", "execution_failed", "verification_failed"]:
        parsed = value.lower() in ("true", "1", "yes", "on")
        prefs.set(key, parsed)
    elif key == "reply_base_url":
        prefs.set(key, value)
    else:
        console.print(f"[red]Unknown preference: {key}[/red]")
        console.print("[yellow]Valid keys: decision_requests, day_end_summary, execution_failed, verification_failed, severity_threshold, reply_base_url[/yellow]")
        raise typer.Exit(1)

    console.print(f"[green]Updated {key} = {value}[/green]")


if __name__ == "__main__":
    app()
