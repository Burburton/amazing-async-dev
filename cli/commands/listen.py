"""listen command - Continuous webhook polling for automatic decision continuation.

Feature 058: Webhook Auto-Polling & Decision Continuation.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
from datetime import datetime

app = typer.Typer(help="Listen for webhook decision replies")
console = Console()


@app.command()
def start(
    project: str = typer.Option(None, help="Project ID to monitor"),
    interval: int = typer.Option(
        60,
        "--interval", "-i",
        help="Polling interval in seconds (default: 60)"
    ),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Start continuous webhook polling daemon.

    Monitors Cloudflare Worker for pending email replies and
    automatically processes them when detected.

    Examples:
        asyncdev listen start
        asyncdev listen start --project my-product
        asyncdev listen start --interval 30
    """
    from runtime.state_store import StateStore
    from runtime.webhook_poller import listen_for_decisions, format_poll_result, PollingStatus

    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
    else:
        store = StateStore()
        project_path = store.project_path

    console.print(Panel(
        f"Project: {project_path.name}\n"
        f"Interval: {interval}s\n"
        f"Started: {datetime.now().isoformat()}",
        title="Webhook Polling Started",
        border_style="green"
    ))

    console.print("\n[cyan]Listening for decision replies...[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    try:
        listen_for_decisions(project_path, interval=interval, once=False)
    except KeyboardInterrupt:
        console.print("\n[yellow]Polling stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Polling error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def once(
    project: str = typer.Option(None, help="Project ID to check"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Run a single polling cycle.

    Checks webhook for pending decisions once and processes any found.

    Examples:
        asyncdev listen once
        asyncdev listen once --project my-product
        asyncdev listen once --json
    """
    from runtime.state_store import StateStore
    from runtime.webhook_poller import listen_for_decisions, format_poll_result, PollingStatus

    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
    else:
        store = StateStore()
        project_path = store.project_path

    result = listen_for_decisions(project_path, interval=60, once=True)

    if result is None:
        console.print("[red]No result returned[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print_json(data={
            "status": result.status.value,
            "decisions_found": result.decisions_found,
            "decisions_processed": result.decisions_processed,
            "decisions_skipped": result.decisions_skipped,
            "processed_ids": result.processed_ids,
            "errors": result.errors,
            "timestamp": result.timestamp,
        })
        return

    if result.status == PollingStatus.ERROR:
        console.print(Panel(
            "\n".join(result.errors),
            title="Polling Error",
            border_style="red"
        ))
        raise typer.Exit(1)

    if result.status == PollingStatus.NO_DECISIONS:
        console.print(Panel(
            "No pending decisions found",
            title="Poll Result",
            border_style="blue"
        ))
        return

    console.print(Panel(
        f"Found: {result.decisions_found}\n"
        f"Processed: {result.decisions_processed}\n"
        f"Skipped: {result.decisions_skipped}",
        title="Poll Result",
        border_style="green"
    ))

    if result.processed_ids:
        console.print("\n[cyan]Processed decisions:[/cyan]")
        for id in result.processed_ids:
            console.print(f"  [green]✓[/green] {id}")

    if result.errors:
        console.print("\n[yellow]Skipped:[/yellow]")
        for err in result.errors:
            console.print(f"  [yellow]•[/yellow] {err}")


@app.command()
def status(
    project: str = typer.Option(None, help="Project ID to check"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show polling configuration status.

    Examples:
        asyncdev listen status
        asyncdev listen status --project my-product
    """
    from runtime.state_store import StateStore
    from runtime.webhook_poller import get_polling_config, PollingConfig
    from runtime.resend_provider import load_resend_config

    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
    else:
        store = StateStore()
        project_path = store.project_path

    config = load_resend_config(project_path / ".runtime" / "resend-config.json")

    polling_config = get_polling_config(project_path)

    console.print(Panel("Webhook Polling Status", border_style="blue"))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim")
    table.add_column("Value")

    table.add_row("Enabled", str(polling_config.enabled))
    table.add_row("Interval", f"{polling_config.interval_seconds}s")
    table.add_row("Auto Resume", str(polling_config.auto_resume))
    table.add_row("Max Retries", str(polling_config.max_retries))
    table.add_row("Timeout", f"{polling_config.timeout_seconds}s")

    console.print(table)

    if config and config.get("webhook_url"):
        console.print(f"\n[cyan]Webhook URL:[/cyan] {config.get('webhook_url')}")
    else:
        console.print("\n[yellow]No webhook URL configured[/yellow]")
        console.print("[dim]Run 'asyncdev resend-auth setup' to configure[/dim]")


if __name__ == "__main__":
    app()