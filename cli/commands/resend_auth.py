"""resend-auth command - Resend email provider setup CLI (Feature 053)."""

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.resend_provider import (
    ResendConfig,
    ResendProvider,
    format_resend_setup_instructions,
    RESEND_TEST_ADDRESS,
    RESEND_TEST_ADDRESSES,
    RESEND_CONFIG_FILE,
    save_resend_config,
    load_resend_config,
    interactive_resend_setup,
    apply_resend_config_from_file,
)

app = typer.Typer(help="Resend email provider configuration")
console = Console()


@app.command()
def setup(
    api_key: str = typer.Option(None, help="Resend API key"),
    from_email: str = typer.Option(None, help="Verified sender email"),
    to_email: str = typer.Option(None, help="Your email for receiving decision emails"),
    sandbox: bool = typer.Option(False, help="Enable sandbox mode"),
    open_browser: bool = typer.Option(True, help="Open Resend dashboard in browser"),
    force: bool = typer.Option(False, help="Overwrite existing config"),
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
):
    """Configure Resend email provider interactively.
    
    Example:
        asyncdev resend-auth setup
        asyncdev resend-auth setup --api-key re_xxx --from-email noreply@domain.com --to-email your@email.com
        asyncdev resend-auth setup --no-open-browser
        asyncdev resend-auth setup --force
    """
    path = config_path or RESEND_CONFIG_FILE
    
    existing = load_resend_config(path)
    if existing and not force:
        console.print(Panel(
            f"Config exists at: {path}\n"
            f"API Key: {existing.get('api_key', '')[:10]}...\n"
            f"From Email: {existing.get('from_email')}\n"
            f"To Email: {existing.get('to_address', 'not set')}\n"
            f"Sandbox: {existing.get('sandbox_mode', False)}",
            title="Existing Config Found",
            border_style="yellow"
        ))
        console.print("\n[yellow]Use --force to overwrite[/yellow]")
        raise typer.Exit(0)
    
    if api_key and from_email:
        final_to_email = to_email or from_email
        
        result = save_resend_config(
            api_key=api_key,
            from_email=from_email,
            to_address=final_to_email,
            sandbox_mode=sandbox,
            config_path=path,
        )
        
        if result["status"] == "success":
            os.environ["RESEND_API_KEY"] = api_key
            os.environ["RESEND_FROM_EMAIL"] = from_email
            os.environ["ASYNCDEV_TO_ADDRESS"] = final_to_email
            if sandbox:
                os.environ["RESEND_SANDBOX_MODE"] = "true"
            
            console.print(Panel(
                f"Config saved: {path}\n"
                f"API Key: {api_key[:10]}...\n"
                f"From Email: {from_email}\n"
                f"To Email: {final_to_email}\n"
                f"Sandbox Mode: {sandbox}",
                title="Resend Configuration Saved",
                border_style="green"
            ))
            
            console.print("\n[bold]Environment variables set[/bold]")
            console.print("[cyan]Run 'asyncdev resend-auth test' to verify[/cyan]")
        else:
            console.print(f"[red]Failed: {result.get('error')}[/red]")
            raise typer.Exit(1)
        
        return
    
    result = interactive_resend_setup(
        api_key=api_key,
        from_email=from_email,
        to_address=to_email,
        open_browser=open_browser,
        config_path=path,
    )
    
    if result["status"] == "success":
        console.print(Panel(
            f"Config saved: {result['path']}\n"
            f"API Key: {result['api_key']}\n"
            f"From Email: {result['from_email']}\n"
            f"To Email: {result['to_address']}\n"
            f"Sandbox Mode: {result['sandbox_mode']}",
            title="Resend Configuration Complete",
            border_style="green"
        ))
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. [cyan]export ASYNCDEV_DELIVERY_MODE=resend[/cyan]")
        console.print("  2. [cyan]asyncdev resend-auth enable[/cyan]")
        console.print("  3. [cyan]asyncdev resend-auth test[/cyan]")
    elif result["status"] == "already_configured":
        console.print(Panel(
            f"Config exists at: {result['path']}\n"
            f"Use --force to overwrite",
            title="Config Already Exists",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            f"Error: {result.get('error', 'Unknown')}",
            title="Setup Failed",
            border_style="red"
        ))
        console.print("\n[cyan]Run 'asyncdev resend-auth guide' for help[/cyan]")
        raise typer.Exit(1)


@app.command()
def guide():
    """Display Resend setup guide.
    
    Example:
        asyncdev resend-auth guide
    """
    guide_text = format_resend_setup_instructions()
    console.print(guide_text)


@app.command()
def status(
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
):
    """Check Resend configuration status.
    
    Example:
        asyncdev resend-auth status
        asyncdev resend-auth status --config-path custom/path.json
    """
    path = config_path or RESEND_CONFIG_FILE
    
    # Try to load from config file first
    file_config = load_resend_config(path)
    
    # Apply file config to environment if exists
    if file_config:
        apply_resend_config_from_file(path)
    
    # Get current config (from env or file)
    config = ResendConfig()
    
    console.print(Panel(
        f"Config File: {path}\n"
        f"File Exists: {file_config is not None}\n"
        f"API Key: {config.api_key[:10] + '...' if config.api_key else 'NOT SET'}\n"
        f"From Email: {config.from_email or 'NOT SET'}\n"
        f"Webhook Secret: {'SET' if config.webhook_secret else 'NOT SET'}\n"
        f"Sandbox Mode: {config.sandbox_mode}\n"
        f"Is Configured: {config.is_configured()}",
        title="Resend Status",
        border_style="blue"
    ))
    
    if config.is_configured():
        console.print("[green]Ready to send emails[/green]")
        console.print(f"[cyan]Delivery mode: {os.getenv('ASYNCDEV_DELIVERY_MODE', 'mock_file')}[/cyan]")
        console.print(f"[cyan]Config source: {path if file_config else 'environment'}[/cyan]")
    else:
        console.print("[red]Not configured[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' to configure[/cyan]")


@app.command()
def test(
    to: str = typer.Option(
        None,
        "--to",
        help="Recipient email address (default: delivered@resend.dev)",
    ),
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
):
    """Test Resend connection by sending a test email.
    
    Example:
        asyncdev resend-auth test
        asyncdev resend-auth test --to your@email.com
        asyncdev resend-auth test --config-path custom/path.json
    """
    path = config_path or RESEND_CONFIG_FILE
    
    if load_resend_config(path):
        apply_resend_config_from_file(path)
    
    config = ResendConfig()
    
    if not config.is_configured():
        console.print("[red]Resend not configured[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' first[/cyan]")
        raise typer.Exit(1)
    
    recipient = to or RESEND_TEST_ADDRESS
    
    if to:
        console.print(f"[cyan]Sending test email to {to} via Resend...[/cyan]")
    else:
        console.print("[cyan]Sending test email to Resend test address...[/cyan]")
    
    provider = ResendProvider(config)
    success, explanation = provider.test_connection(to=to)
    
    if success:
        console.print(Panel(
            f"{explanation}",
            title="Resend Test Success",
            border_style="green"
        ))
        
        if not to:
            console.print(f"[dim]Test address used: {RESEND_TEST_ADDRESS}[/dim]")
            console.print("[dim]Use --to your@email.com to send a real test email[/dim]")
        
        if config.sandbox_mode:
            console.print("[yellow]Sandbox mode enabled - email went to test address[/yellow]")
    else:
        console.print(Panel(
            f"Failed: {explanation}",
            title="Resend Test Failed",
            border_style="red"
        ))
        console.print("\n[yellow]Possible issues:[/yellow]")
        console.print("  - Invalid API key")
        console.print("  - Sender email not verified in Resend dashboard")
        console.print("  - Network connectivity issues")
        console.print("\n[cyan]Run 'asyncdev resend-auth guide' for troubleshooting[/cyan]")
        raise typer.Exit(1)


@app.command()
def test_addresses():
    """List available test email addresses for Resend.
    
    Example:
        asyncdev resend-auth test-addresses
    """
    console.print("[bold]Resend Test Email Addresses[/bold]\n")
    
    for name, address in RESEND_TEST_ADDRESSES.items():
        console.print(f"  [{name}] {address}")
    
    console.print("\n[dim]These addresses simulate different email events without real delivery.[/dim]")
    console.print("[dim]Use them for safe testing during development.[/dim]")


@app.command()
def webhook_info():
    """Display webhook setup instructions for inbound replies.
    
    Example:
        asyncdev resend-auth webhook-info
    """
    console.print("""
[bold]Resend Webhook Setup[/bold]

1. Go to https://resend.com/webhooks

2. Create a new webhook:
   - Endpoint URL: https://your-server.com/webhooks/resend
   - Events to subscribe:
     [bold]email.received[/bold] - inbound replies
     [bold]email.sent[/bold] - outbound confirmation
     [bold]email.delivered[/bold] - delivery tracking
     [bold]email.bounced[/bold] - bounce handling

3. Copy the webhook signing secret:
   export RESEND_WEBHOOK_SECRET=whsec_xxxxx

4. Implement webhook handler:
   - Verify signature using RESEND_WEBHOOK_SECRET
   - Parse email.received events
   - Extract X-Decision-Request-Id header
   - Link to original decision request

[dim]See runtime/resend_provider.py for webhook handler implementation[/dim]
""")


@app.command()
def enable(
    config_path: Path = typer.Option(
        None,
        help="Path to config file (default: .runtime/resend-config.json)",
    ),
):
    """Enable Resend as the email delivery mode.
    
    Example:
        asyncdev resend-auth enable
        asyncdev resend-auth enable --config-path custom/path.json
    """
    path = config_path or RESEND_CONFIG_FILE
    
    if load_resend_config(path):
        apply_resend_config_from_file(path)
    
    config = ResendConfig()
    
    if not config.is_configured():
        console.print("[red]Resend not configured[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' first[/cyan]")
        raise typer.Exit(1)
    
    os.environ["ASYNCDEV_DELIVERY_MODE"] = "resend"
    
    console.print(Panel(
        f"Delivery mode set to: resend\n"
        f"From Email: {config.from_email}\n"
        f"Sandbox: {config.sandbox_mode}\n"
        f"Config source: {path if load_resend_config(path) else 'environment'}",
        title="Resend Enabled",
        border_style="green"
    ))
    
    console.print("\n[cyan]To persist delivery mode, add to your shell profile:[/cyan]")
    console.print("  export ASYNCDEV_DELIVERY_MODE=resend")