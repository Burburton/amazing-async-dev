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
)

app = typer.Typer(help="Resend email provider configuration")
console = Console()


@app.command()
def setup(
    api_key: str = typer.Option(None, help="Resend API key"),
    from_email: str = typer.Option(None, help="Verified sender email"),
    sandbox: bool = typer.Option(False, help="Enable sandbox mode"),
):
    """Configure Resend email provider.
    
    Example:
        asyncdev resend-auth setup
        asyncdev resend-auth setup --api-key re_xxx --from-email noreply@domain.com
    """
    if api_key:
        os.environ["RESEND_API_KEY"] = api_key
    if from_email:
        os.environ["RESEND_FROM_EMAIL"] = from_email
    if sandbox:
        os.environ["RESEND_SANDBOX_MODE"] = "true"
    
    config = ResendConfig()
    
    if config.is_configured():
        console.print(Panel(
            f"API Key: {config.api_key[:10]}...\n"
            f"From Email: {config.from_email}\n"
            f"Sandbox Mode: {config.sandbox_mode}",
            title="Resend Configuration",
            border_style="green"
        ))
        
        console.print("\n[bold]Configuration saved to environment variables[/bold]")
        console.print("\n[cyan]To persist, add to your shell profile:[/cyan]")
        console.print(f"  export RESEND_API_KEY={config.api_key}")
        console.print(f"  export RESEND_FROM_EMAIL={config.from_email}")
        if sandbox:
            console.print(f"  export RESEND_SANDBOX_MODE=true")
        console.print(f"  export ASYNCDEV_DELIVERY_MODE=resend")
    else:
        console.print("[red]Missing required configuration[/red]")
        console.print("\n[yellow]Required environment variables:[/yellow]")
        console.print("  RESEND_API_KEY=re_xxxxxxxxxxxxx")
        console.print("  RESEND_FROM_EMAIL=noreply@yourdomain.com")
        console.print("\n[cyan]Run 'asyncdev resend-auth guide' for setup instructions[/cyan]")
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
def status():
    """Check Resend configuration status.
    
    Example:
        asyncdev resend-auth status
    """
    config = ResendConfig()
    
    console.print(Panel(
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
    else:
        console.print("[red]Not configured[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' to configure[/cyan]")


@app.command()
def test():
    """Test Resend connection by sending a test email.
    
    Example:
        asyncdev resend-auth test
    """
    config = ResendConfig()
    
    if not config.is_configured():
        console.print("[red]Resend not configured[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' first[/cyan]")
        raise typer.Exit(1)
    
    console.print("[cyan]Sending test email via Resend...[/cyan]")
    
    provider = ResendProvider(config)
    success, explanation = provider.test_connection()
    
    if success:
        console.print(Panel(
            f"{explanation}\n\nTest email sent to: {RESEND_TEST_ADDRESS}",
            title="Resend Test Success",
            border_style="green"
        ))
        
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
def enable():
    """Enable Resend as the email delivery mode.
    
    Example:
        asyncdev resend-auth enable
    """
    config = ResendConfig()
    
    if not config.is_configured():
        console.print("[red]Resend not configured[/red]")
        console.print("[cyan]Run 'asyncdev resend-auth setup' first[/cyan]")
        raise typer.Exit(1)
    
    os.environ["ASYNCDEV_DELIVERY_MODE"] = "resend"
    
    console.print(Panel(
        f"Delivery mode set to: resend\n"
        f"From Email: {config.from_email}\n"
        f"Sandbox: {config.sandbox_mode}",
        title="Resend Enabled",
        border_style="green"
    ))
    
    console.print("\n[cyan]To persist, add to your shell profile:[/cyan]")
    console.print("  export ASYNCDEV_DELIVERY_MODE=resend")