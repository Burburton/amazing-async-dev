"""notification command - Notification management CLI (Feature 080)."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.notification_store import NotificationStore
from runtime.notification_event import (
    NotificationEventType,
    NotificationStatus,
    NotificationSeverity,
)
from cli.utils.output_formatter import print_next_step, print_success_panel

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
        console.print(f"\n[bold]Related Artifacts:[/bold]")
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


if __name__ == "__main__":
    app()