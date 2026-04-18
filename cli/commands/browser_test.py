"""browser-test command - Feature 056.

Run browser verification for frontend projects.

Usage:
    asyncdev browser-test --project <id>
    asyncdev browser-test --project <id> --url http://localhost:3000
    asyncdev browser-test --project <id> --scenarios "render,console-check"
    asyncdev browser-test --project <id> --timeout 120
"""

from pathlib import Path
from typing import Any
import typer
from rich.console import Console
from rich.table import Table

from runtime.verification_classifier import (
    get_verification_type,
    VerificationType,
    classify_verification_type_from_files,
)
from runtime.dev_server_manager import DevServerManager, DevServerFramework, detect_framework
from runtime.browser_verifier import (
    run_browser_verification,
    check_playwright_available,
    ExceptionReason,
    create_exception_result,
)
from runtime.state_store import StateStore

app = typer.Typer(help="Browser verification for frontend projects")
console = Console()


@app.command("run")
def run_browser_test(
    project: str = typer.Option(None, "--project", "-p", help="Project ID or path"),
    url: str = typer.Option(None, "--url", "-u", help="Dev server URL"),
    scenarios: str = typer.Option(None, "--scenarios", "-s", help="Scenarios to run (comma-separated)"),
    timeout: int = typer.Option(60, "--timeout", "-t", help="Timeout in seconds"),
    start_server: bool = typer.Option(True, "--start-server", help="Auto-start dev server"),
    no_start_server: bool = typer.Option(False, "--no-start-server", help="Skip dev server startup"),
):
    """Run browser verification for a frontend project."""
    project_path = Path(project) if project else Path.cwd()
    
    if not project_path.exists():
        console.print(f"[red]Project path not found: {project_path}[/red]")
        raise typer.Exit(1)
    
    framework = detect_framework(project_path)
    
    if framework == DevServerFramework.UNKNOWN:
        console.print(f"[yellow]Warning: Could not detect frontend framework[/yellow]")
        console.print(f"[yellow]Assuming generic dev server on port 3000[/yellow]")
    
    console.print(f"\n[bold cyan]Browser Verification[/bold cyan]")
    console.print(f"  Project: {project_path}")
    console.print(f"  Framework: {framework.value}")
    
    if not check_playwright_available():
        console.print(f"\n[red]Playwright not available[/red]")
        console.print(f"[yellow]Install: pip install playwright && playwright install[/yellow]")
        result = create_exception_result(
            ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
            "Playwright not installed",
        )
        _display_result(result)
        raise typer.Exit(1)
    
    target_scenarios = None
    if scenarios:
        target_scenarios = [s.strip() for s in scenarios.split(",")]
    
    target_url = url
    manager = None
    
    should_start_server = start_server and not no_start_server
    
    if should_start_server and not url:
        console.print(f"\n[bold]Starting dev server...[/bold]")
        manager = DevServerManager(project_path)
        
        server_result = manager.start(timeout=timeout)
        
        if not server_result.success:
            console.print(f"[red]Failed to start dev server: {server_result.status.error_message}[/red]")
            raise typer.Exit(1)
        
        target_url = manager.get_url()
        console.print(f"[green]Dev server running at {target_url}[/green]")
        console.print(f"[dim]Process ID: {server_result.status.process_id}[/dim]")
    
    if not target_url:
        console.print(f"[red]No URL specified and dev server not started[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold]Running browser verification...[/bold]")
    console.print(f"  URL: {target_url}")
    console.print(f"  Scenarios: {target_scenarios or 'default'}")
    console.print(f"  Timeout: {timeout}s")
    
    screenshot_dir = project_path / ".runtime" / "browser-screenshots"
    
    result = run_browser_verification(
        url=target_url,
        scenarios=target_scenarios,
        timeout=timeout,
        screenshot_dir=screenshot_dir,
    )
    
    _display_result(result)
    
    if manager is not None:
        manager.stop()
        console.print(f"\n[dim]Dev server stopped[/dim]")
    
    if result.failed > 0:
        raise typer.Exit(1)


@app.command("classify")
def classify_verification(
    project: str = typer.Option(None, "--project", "-p", help="Project ID or path"),
    files: str = typer.Option(None, "--files", "-f", help="Files to analyze (comma-separated)"),
    description: str = typer.Option("", "--description", "-d", help="Feature description"),
):
    """Classify verification type for a project or file set."""
    project_path = Path(project) if project else Path.cwd()
    
    target_files = []
    if files:
        target_files = [f.strip() for f in files.split(",")]
    
    console.print(f"\n[bold cyan]Verification Classification[/bold cyan]")
    
    if target_files:
        result = classify_verification_type_from_files(target_files, description)
        console.print(f"\n[bold]Classification Result[/bold]")
        console.print(f"  Type: [green]{result.verification_type.value}[/green]")
        console.print(f"  Confidence: {result.confidence:.2f}")
        console.print(f"  Reasoning: {result.reasoning}")
        console.print(f"  Patterns detected: {', '.join(result.detected_patterns)}")
    else:
        vt = get_verification_type(files=None, feature_description=description)
        console.print(f"\n[bold]Classification Result[/bold]")
        console.print(f"  Type: [green]{vt.value}[/green]")


@app.command("check")
def check_environment():
    """Check browser verification environment status."""
    console.print(f"\n[bold cyan]Browser Verification Environment Check[/bold cyan]\n")
    
    playwright_available = check_playwright_available()
    
    status_table = Table(title="Environment Status")
    status_table.add_column("Component")
    status_table.add_column("Status")
    
    status_table.add_row(
        "Playwright",
        "[green]Available[/green]" if playwright_available else "[red]Not Installed[/red]"
    )
    
    console.print(status_table)
    
    if not playwright_available:
        console.print(f"\n[yellow]To install Playwright:[/yellow]")
        console.print(f"  pip install playwright")
        console.print(f"  playwright install chromium")


def _display_result(result: Any):
    """Display browser verification result."""
    console.print(f"\n[bold]Verification Result[/bold]")
    
    status_color = "green" if result.passed == result.passed + result.failed else "red"
    console.print(f"  Status: [{status_color}]{result.status.value}[/{status_color}]")
    console.print(f"  Passed: {result.passed}")
    console.print(f"  Failed: {result.failed}")
    console.print(f"  Duration: {result.duration_seconds:.2f}s")
    
    if result.scenarios_run:
        console.print(f"\n[bold]Scenarios[/bold]")
        scenario_table = Table()
        scenario_table.add_column("Scenario")
        scenario_table.add_column("Status")
        scenario_table.add_column("Duration")
        
        for sr in result.scenario_results:
            status = "[green]PASS[/green]" if sr.passed else "[red]FAIL[/red]"
            scenario_table.add_row(sr.name, status, f"{sr.duration_seconds:.2f}s")
        
        console.print(scenario_table)
    
    if result.console_errors:
        console.print(f"\n[bold]Console Errors[/bold] ({len(result.console_errors)} total)")
        error_table = Table()
        error_table.add_column("Level")
        error_table.add_column("Message")
        
        for error in result.console_errors[:5]:
            level_color = "red" if error.level == "error" else "yellow"
            error_table.add_row(
                f"[{level_color}]{error.level}[/{level_color}]",
                error.message[:50] + "..." if len(error.message) > 50 else error.message,
            )
        
        console.print(error_table)
    
    if result.screenshots:
        console.print(f"\n[bold]Screenshots[/bold]")
        for screenshot in result.screenshots:
            console.print(f"  {screenshot}")
    
    if result.exception_reason:
        console.print(f"\n[red]Exception: {result.exception_reason.value}[/red]")
        console.print(f"[yellow]Details: {result.exception_details}[/yellow]")