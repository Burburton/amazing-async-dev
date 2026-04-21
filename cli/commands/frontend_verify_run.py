"""frontend-verify-run command - Controlled frontend verification recipe (Feature 062).

Canonical entry point for frontend verification that enforces:
- Controlled dev server startup (not foreground-blocking)
- Port discovery via stdout parsing + fallback probe
- Readiness probe before browser verification
- Mandatory browser verification (not stopping at "server ready")
- Structured result persistence

This is the preferred path for external agents performing frontend verification work.
"""

from pathlib import Path
from datetime import datetime
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.frontend_verification_recipe import execute_frontend_verification_recipe
from runtime.frontend_recipe_state import FrontendRecipeStage
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Controlled frontend verification execution (Feature 062)")
console = Console()


@app.command()
def execute(
    project: str = typer.Option(None, "--project", help="Project ID"),
    execution_id: str = typer.Option(None, "--execution-id", help="Execution ID (auto-generated if None)"),
    server_timeout: int = typer.Option(30, "--server-timeout", help="Dev server startup timeout (seconds)"),
    readiness_timeout: int = typer.Option(60, "--readiness-timeout", help="Readiness probe timeout (seconds)"),
    browser_timeout: int = typer.Option(120, "--browser-timeout", help="Browser verification timeout (seconds)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    dry_run: bool = typer.Option(False, help="Show recipe plan without executing"),
):
    """Execute controlled frontend verification recipe.
    
    This command runs a deterministic frontend verification flow:
    1. Detect framework and start dev server in controlled mode
    2. Probe for server readiness (not stopping at "server ready")
    3. Run browser verification via Playwright
    4. Persist structured execution result
    
    External agents should use this instead of ad hoc shell commands like:
    - npm run dev (foreground-blocking)
    - manual port guessing
    - stopping after seeing "server ready"
    """
    root = Path.cwd() if path == Path("projects") else path
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            console.print(f"[yellow]Path checked: {project_path}[/yellow]")
            raise typer.Exit(1)
    else:
        project_path = Path.cwd()
    
    if not execution_id:
        execution_id = f"frontend-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    console.print(Panel(
        f"Project: {project_path.name}\n"
        f"Execution ID: {execution_id}\n"
        f"Server Timeout: {server_timeout}s\n"
        f"Readiness Timeout: {readiness_timeout}s\n"
        f"Browser Timeout: {browser_timeout}s",
        title="Frontend Verification Recipe",
        border_style="cyan"
    ))
    
    if dry_run:
        console.print("\n[yellow]Dry run - recipe plan:[/yellow]")
        console.print("  1. INITIALIZING - Detect frontend framework")
        console.print("  2. SERVER_STARTING - Start dev server in controlled mode")
        console.print("  3. READINESS_PROBING - Probe server readiness with timeout")
        console.print("  4. BROWSER_VERIFICATION - Run Playwright verification")
        console.print("  5. RESULT_PERSISTING - Write structured execution result")
        console.print("  6. COMPLETED_SUCCESS - Terminal outcome")
        console.print("\n[dim]Execution would proceed through these stages[/dim]")
        return
    
    console.print("\n[cyan]Executing frontend verification recipe...[/cyan]")
    
    result = execute_frontend_verification_recipe(
        project_path=project_path,
        execution_id=execution_id,
        server_start_timeout=server_timeout,
        readiness_probe_timeout=readiness_timeout,
        browser_verification_timeout=browser_timeout,
    )
    
    _display_result(result, project_path, root)


def _display_result(result, project_path: Path, root: Path) -> None:
    """Display recipe execution result."""
    stage_color = {
        FrontendRecipeStage.COMPLETED_SUCCESS: "green",
        FrontendRecipeStage.COMPLETED_FAILURE: "red",
        FrontendRecipeStage.COMPLETED_TIMEOUT: "yellow",
    }
    
    color = stage_color.get(result.stage, "blue")
    
    console.print(f"\n[bold]Recipe Stage:[/bold] [{color}]{result.stage.value}[/{color}]")
    console.print(f"[bold]Framework:[/bold] {result.framework}")
    console.print(f"[bold]Duration:[/bold] {result.total_duration_seconds:.1f}s")
    
    if result.server_startup:
        console.print(f"\n[cyan]Server Startup:[/cyan]")
        console.print(f"  Command: {' '.join(result.server_startup.command)}")
        console.print(f"  Detected Port: {result.server_startup.detected_port or 'N/A'}")
        console.print(f"  Detected URL: {result.server_startup.detected_url or 'N/A'}")
        console.print(f"  Process ID: {result.server_startup.process_id or 'N/A'}")
        console.print(f"  Startup Duration: {result.server_startup.startup_duration_seconds:.1f}s")
    
    if result.readiness_probe:
        console.print(f"\n[cyan]Readiness Probe:[/cyan]")
        console.print(f"  Target URL: {result.readiness_probe.target_url}")
        console.print(f"  Probe Attempts: {result.readiness_probe.probe_attempts}")
        console.print(f"  Successful: {'Yes' if result.readiness_probe.successful_probe else 'No'}")
        console.print(f"  HTTP Status: {result.readiness_probe.http_status_code or 'N/A'}")
    
    console.print(f"\n[cyan]Browser Verification:[/cyan]")
    console.print(f"  Executed: {'Yes' if result.browser_verification_executed else 'No'}")
    
    if result.browser_verification_result:
        console.print(f"  Status: {result.browser_verification_result.get('status', 'N/A')}")
        console.print(f"  Passed: {result.browser_verification_result.get('passed', 0)}")
        console.print(f"  Failed: {result.browser_verification_result.get('failed', 0)}")
    
    if result.failure_reason:
        console.print(f"\n[bold red]Failure Reason:[/bold red] {result.failure_reason.value}")
        if result.error_message:
            console.print(f"[red]Error: {result.error_message}[/red]")
    
    if result.result_persisted:
        console.print(f"\n[green]Result persisted: {result.result_artifact_path}[/green]")
    
    console.print()
    
    if result.stage == FrontendRecipeStage.COMPLETED_SUCCESS:
        print_success_panel(
            message="Frontend verification completed successfully",
            title="Recipe Complete",
            paths=[
                {"label": "ExecutionResult", "path": result.result_artifact_path or ""},
            ],
            root=root,
        )
        print_next_step(
            action="Review verification results",
            command="asyncdev resume-next-day",
            artifact_path=Path(result.result_artifact_path or ""),
            root=root,
        )
    else:
        console.print(f"\n[red]Recipe failed at stage: {result.stage.value}[/red]")
        print_next_step(
            action="Diagnose failure and retry",
            command="asyncdev doctor",
            hints=["Check execution result for error details"],
            root=root,
        )


@app.command()
def stages():
    """Show recipe stage definitions."""
    console.print(Panel("Recipe Stage Definitions", title="Feature 062", border_style="cyan"))
    
    table = Table(title="Execution Stages")
    table.add_column("Stage", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Transition", style="green")
    
    stages = [
        ("INITIALIZING", "Execution", "→ SERVER_STARTING"),
        ("SERVER_STARTING", "Execution", "→ READINESS_PROBING"),
        ("READINESS_PROBING", "Execution", "→ BROWSER_VERIFICATION"),
        ("BROWSER_VERIFICATION", "Execution", "→ RESULT_PERSISTING"),
        ("RESULT_PERSISTING", "Execution", "→ COMPLETED_SUCCESS"),
        ("COMPLETED_SUCCESS", "Terminal", "✓ Success"),
        ("COMPLETED_FAILURE", "Terminal", "✗ Failure"),
        ("COMPLETED_TIMEOUT", "Terminal", "⏱ Timeout"),
    ]
    
    for stage, type_, transition in stages:
        table.add_row(stage, type_, transition)
    
    console.print(table)
    
    console.print("\n[dim]Recipe guarantees: No stopping at 'server ready', mandatory browser verification[/dim]")


if __name__ == "__main__":
    app()