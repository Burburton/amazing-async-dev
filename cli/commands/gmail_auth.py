"""gmail-auth command - Gmail OAuth2 token generation CLI."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.gmail_oauth2_token_generator import (
    generate_authorization_url,
    exchange_code_for_tokens,
    create_token_file,
    interactive_token_generation,
    validate_oauth2_credentials,
    format_setup_guide,
)

app = typer.Typer(help="Gmail OAuth2 authentication setup")
console = Console()


@app.command()
def setup(
    client_id: str = typer.Option(None, help="Google OAuth2 client ID"),
    client_secret: str = typer.Option(None, help="Google OAuth2 client secret"),
    email: str = typer.Option(None, help="Your Gmail address"),
    token_path: Path = typer.Option(
        Path(".runtime/gmail-oauth2-token.json"),
        help="Path to save token file",
    ),
):
    """Interactive Gmail OAuth2 token setup.
    
    This command will guide you through obtaining OAuth2 tokens
    for Gmail SMTP authentication.
    
    Example:
        asyncdev gmail-auth setup
        asyncdev gmail-auth setup --client-id xxx --client-secret xxx --email you@gmail.com
    """
    result = interactive_token_generation(
        client_id=client_id,
        client_secret=client_secret,
        email=email,
        token_path=token_path,
    )
    
    if result["status"] == "success":
        console.print(Panel(
            f"Token saved: {result['token_path']}\n"
            f"Email: {result.get('email')}\n"
            f"Has refresh token: {result.get('has_refresh_token')}",
            title="OAuth2 Setup Complete",
            border_style="green"
        ))
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. [cyan]export ASYNCDEV_USE_OAUTH2=true[/cyan]")
        console.print("  2. [cyan]export ASYNCDEV_DELIVERY_MODE=smtp[/cyan]")
        console.print("  3. Test email sending")
    else:
        console.print(Panel(
            f"Error: {result.get('error', 'Unknown')}",
            title="OAuth2 Setup Failed",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command()
def guide():
    """Display detailed Gmail OAuth2 setup guide.
    
    Example:
        asyncdev gmail-auth guide
    """
    guide_text = format_setup_guide()
    console.print(guide_text)


@app.command()
def validate(
    client_id: str = typer.Option(..., help="Google OAuth2 client ID"),
    client_secret: str = typer.Option(..., help="Google OAuth2 client secret"),
):
    """Validate OAuth2 credentials format.
    
    Example:
        asyncdev gmail-auth validate --client-id xxx --client-secret xxx
    """
    is_valid, explanation = validate_oauth2_credentials(client_id, client_secret)
    
    if is_valid:
        console.print(f"[green]Valid: {explanation}[/green]")
    else:
        console.print(f"[red]Invalid: {explanation}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    token_path: Path = typer.Option(
        Path(".runtime/gmail-oauth2-token.json"),
        help="Path to token file",
    ),
):
    """Check current OAuth2 token status.
    
    Example:
        asyncdev gmail-auth status
        asyncdev gmail-auth status --token-path custom/path.json
    """
    from runtime.gmail_oauth2 import GmailOAuth2Config
    
    config = GmailOAuth2Config(token_path)
    
    if not token_path.exists():
        console.print("[yellow]No token file found[/yellow]")
        console.print(f"[dim]Expected path: {token_path}[/dim]")
        console.print("\n[cyan]Run 'asyncdev gmail-auth setup' to generate tokens[/cyan]")
        return
    
    token_data = config.load()
    
    console.print(Panel(
        f"Email: {token_data.get('email', 'N/A')}\n"
        f"Has access token: {bool(token_data.get('access_token'))}\n"
        f"Has refresh token: {bool(token_data.get('refresh_token'))}\n"
        f"Token expiry: {token_data.get('token_expiry', 'N/A')}\n"
        f"Is expired: {config.is_configured() and not config.get_access_token()}",
        title="OAuth2 Token Status",
        border_style="blue"
    ))
    
    if config.is_configured():
        console.print("[green]Token is valid and ready to use[/green]")
    else:
        console.print("[yellow]Token needs refresh or regeneration[/yellow]")
        console.print("[cyan]Run 'asyncdev gmail-auth setup' to regenerate[/cyan]")


@app.command()
def refresh(
    token_path: Path = typer.Option(
        Path(".runtime/gmail-oauth2-token.json"),
        help="Path to token file",
    ),
):
    """Refresh OAuth2 access token using refresh token.
    
    Example:
        asyncdev gmail-auth refresh
    """
    from runtime.gmail_oauth2 import GmailOAuth2Config
    
    config = GmailOAuth2Config(token_path)
    
    if not token_path.exists():
        console.print("[red]No token file found[/red]")
        raise typer.Exit(1)
    
    if config.refresh():
        console.print(Panel(
            f"Token refreshed successfully\n"
            f"New expiry: {config.load().get('token_expiry')}",
            title="OAuth2 Token Refreshed",
            border_style="green"
        ))
    else:
        console.print("[red]Failed to refresh token[/red]")
        console.print("[yellow]Possible reasons:[/yellow]")
        console.print("  - No refresh token stored")
        console.print("  - No client_id/client_secret stored")
        console.print("  - Refresh token revoked")
        console.print("\n[cyan]Run 'asyncdev gmail-auth setup' to regenerate[/cyan]")
        raise typer.Exit(1)


@app.command()
def test_send(
    to_email: str = typer.Option(..., help="Recipient email address"),
    token_path: Path = typer.Option(
        Path(".runtime/gmail-oauth2-token.json"),
        help="Path to token file",
    ),
):
    """Send test email using OAuth2.
    
    Example:
        asyncdev gmail-auth test-send --to-email recipient@example.com
    """
    from runtime.email_sender import EmailConfig, EmailSender
    
    config = EmailConfig()
    config.use_oauth2 = True
    config.oauth2_token_path = token_path
    config.delivery_mode = "smtp"
    config.to_address = to_email
    
    sender = EmailSender(config)
    
    test_request = {
        "decision_request_id": "test-oauth2",
        "product_id": "test",
        "feature_id": "oauth2-test",
        "question": "OAuth2 test email - if you see this, OAuth2 is working!",
        "options": [{"id": "A", "label": "Success", "description": "It works!"}],
        "recommendation": "A",
        "sent_at": "test",
    }
    
    success, _ = sender.send_decision_request(test_request)
    
    if success:
        console.print(Panel(
            f"Test email sent to: {to_email}\n"
            f"Check your inbox!",
            title="OAuth2 Test Success",
            border_style="green"
        ))
    else:
        console.print("[red]Failed to send test email[/red]")
        console.print("[yellow]Check:[/yellow]")
        console.print("  - Token is valid (run 'asyncdev gmail-auth status')")
        console.print("  - Gmail API is enabled in Google Cloud Console")
        console.print("  - You added yourself as test user in OAuth consent screen")
        raise typer.Exit(1)