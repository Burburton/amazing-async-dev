"""check-inbox command - Poll pending decisions from Cloudflare Worker."""

import json
import urllib.request
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.resend_provider import (
    load_resend_config,
    apply_resend_config_from_file,
    RESEND_CONFIG_FILE,
)

app = typer.Typer(help="Check pending decisions from inbox")
console = Console()


@app.command()
def pending(
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Check pending decisions from Cloudflare Worker.
    
    Example:
        asyncdev check-inbox pending
        asyncdev check-inbox pending --json
    """
    path = config_path or RESEND_CONFIG_FILE
    
    config = load_resend_config(path)
    if not config:
        console.print("[red]No config found[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' first[/cyan]")
        raise typer.Exit(1)
    
    webhook_url = config.get("webhook_url", "")
    if not webhook_url:
        console.print("[red]No webhook URL configured[/red]")
        raise typer.Exit(1)
    
    pending_url = webhook_url.rstrip("/") + "/pending-decisions"
    
    try:
        req = urllib.request.Request(
            pending_url,
            headers={
                "User-Agent": "async-dev/1.0",
                "Accept": "application/json",
            },
            method="GET",
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        if json_output:
            console.print_json(data=result)
            return
        
        if not result.get("ok"):
            console.print(f"[red]Error: {result.get('error', 'Unknown')}[/red]")
            raise typer.Exit(1)
        
        decisions = result.get("decisions", [])
        count = result.get("count", 0)
        
        if count == 0:
            console.print(Panel(
                "No pending decisions\n\nReplies will appear here after you respond to decision emails.",
                title="Inbox Empty",
                border_style="blue"
            ))
            return
        
        console.print(Panel(
            f"Found {count} pending decision(s)",
            title="Pending Decisions",
            border_style="green"
        ))
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("From")
        table.add_column("Option", style="bold green")
        table.add_column("Comment")
        table.add_column("Received")
        
        for decision in decisions:
            table.add_row(
                decision.get("id", "N/A"),
                decision.get("from", "N/A"),
                decision.get("option", "N/A"),
                decision.get("comment", "")[:30] + "..." if len(decision.get("comment", "")) > 30 else decision.get("comment", ""),
                decision.get("receivedAt", "N/A")[:19] if decision.get("receivedAt") else "N/A",
            )
        
        console.print(table)
        
        console.print("\n[cyan]To process a decision:[/cyan]")
        console.print("  asyncdev check-inbox process --id <decision-id> --action approve")
        
    except urllib.error.URLError as e:
        console.print(f"[red]Failed to connect to webhook: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def process(
    decision_id: str = typer.Option(..., "--id", help="Decision ID to process"),
    action: str = typer.Option("approve", help="Action: approve, reject, defer"),
    comment: str = typer.Option("", "--comment", help="Additional comment"),
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
):
    """Process and clear a pending decision.
    
    Example:
        asyncdev check-inbox process --id dr-20260418-001 --action approve
        asyncdev check-inbox process --id dr-20260418-001 --action reject --comment "not ready"
    """
    path = config_path or RESEND_CONFIG_FILE
    
    config = load_resend_config(path)
    if not config:
        console.print("[red]No config found[/red]")
        raise typer.Exit(1)
    
    webhook_url = config.get("webhook_url", "")
    if not webhook_url:
        console.print("[red]No webhook URL configured[/red]")
        raise typer.Exit(1)
    
    clear_url = webhook_url.rstrip("/") + f"/pending-decisions/{decision_id}"
    
    try:
        req = urllib.request.Request(
            clear_url,
            headers={
                "User-Agent": "async-dev/1.0",
                "Accept": "application/json",
            },
            method="DELETE",
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        if not result.get("ok"):
            console.print(f"[red]Error: {result.get('error', 'Unknown')}[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(
            f"Decision ID: {decision_id}\n"
            f"Action: {action}\n"
            f"Comment: {comment or 'none'}\n"
            f"Status: cleared from inbox",
            title="Decision Processed",
            border_style="green"
        ))
        
        console.print("\n[cyan]Decision marked as processed in Worker KV[/cyan]")
        
    except urllib.error.URLError as e:
        console.print(f"[red]Failed to connect to webhook: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test(
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
):
    """Test webhook connection.
    
    Example:
        asyncdev check-inbox test
    """
    path = config_path or RESEND_CONFIG_FILE
    
    config = load_resend_config(path)
    if not config:
        console.print("[red]No config found[/red]")
        raise typer.Exit(1)
    
    webhook_url = config.get("webhook_url", "")
    if not webhook_url:
        console.print("[red]No webhook URL configured[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Testing webhook connection to: {webhook_url}[/cyan]")
    
    try:
        req = urllib.request.Request(
            webhook_url,
            headers={
                "User-Agent": "async-dev/1.0",
                "Accept": "application/json",
            },
            method="GET",
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        if result.get("ok"):
            console.print(Panel(
                f"URL: {webhook_url}\n"
                f"Service: {result.get('service', 'unknown')}\n"
                f"Version: {result.get('version', 'unknown')}\n"
                f"Endpoints: {json.dumps(result.get('endpoints', {}))}",
                title="Webhook Connection OK",
                border_style="green"
            ))
        else:
            console.print(f"[red]Webhook returned error[/red]")
            raise typer.Exit(1)
        
    except urllib.error.URLError as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        console.print("[yellow]Check:[/yellow]")
        console.print("  - Worker is deployed")
        console.print("  - KV namespace is bound")
        console.print("  - URL is correct in config")
        raise typer.Exit(1)