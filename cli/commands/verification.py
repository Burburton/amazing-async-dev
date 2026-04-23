"""verification command - Verification Console (Operator Surface).

Priority 2 operator surface per platform architecture.
Spec: docs/infra/verification-console-spec-v1.md
"""

from pathlib import Path
from datetime import datetime
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.verification_classifier import (
    VerificationType,
    classify_verification_type_from_files,
    ClassificationResult,
)
from runtime.verification_gate import (
    requires_browser_verification,
    validate_browser_verification,
    get_completion_gate_status,
)
from runtime.state_store import StateStore

app = typer.Typer(help="Verification Console - Operator surface for verification visibility")
console = Console()


def _get_all_projects(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]


def _get_execution_results(project_path: Path) -> list[dict[str, Any]]:
    results_dir = project_path / "execution-results"
    if not results_dir.exists():
        return []
    
    results = []
    for result_file in results_dir.glob("*.md"):
        store = StateStore(project_path)
        result = store.load_execution_result(result_file.stem)
        if result:
            result["execution_id"] = result_file.stem
            result["project_id"] = project_path.name
            result["project_path"] = project_path
            results.append(result)
    
    return sorted(results, key=lambda r: r.get("updated_at", "") or r.get("started_at", ""), reverse=True)


def _extract_verification_info(execution_result: dict[str, Any]) -> dict[str, Any]:
    verification_result = execution_result.get("verification_result", {})
    browser_verification = execution_result.get("browser_verification", {})
    frontend_recipe = execution_result.get("frontend_recipe", {})
    
    verification_type = execution_result.get("verification_type", "unknown")
    
    browser_required = requires_browser_verification(verification_type)
    
    browser_executed = browser_verification.get("executed", False)
    browser_passed = browser_verification.get("passed", 0)
    browser_failed = browser_verification.get("failed", 0)
    exception_reason = browser_verification.get("exception_reason")
    
    gate_status = get_completion_gate_status(verification_type, execution_result)
    
    if verification_result:
        passed = verification_result.get("passed", browser_passed)
        failed = verification_result.get("failed", browser_failed)
        skipped = verification_result.get("skipped", 0)
    else:
        passed = browser_passed
        failed = browser_failed
        skipped = 0
    
    status = "unknown"
    if browser_required:
        if browser_executed:
            if failed == 0 and passed > 0:
                status = "success"
            elif failed > 0:
                status = "failed"
            else:
                status = "no_scenarios"
        elif exception_reason:
            status = "exception"
        else:
            status = "pending"
    else:
        if execution_result.get("status") == "success":
            status = "success"
        elif execution_result.get("status") == "failed":
            status = "failed"
        else:
            status = "pending"
    
    return {
        "execution_id": execution_result.get("execution_id", ""),
        "project_id": execution_result.get("project_id", ""),
        "verification_type": verification_type,
        "browser_required": browser_required,
        "browser_executed": browser_executed,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "exception_reason": exception_reason,
        "gate_status": gate_status,
        "status": status,
        "frontend_recipe_stage": frontend_recipe.get("stage", ""),
        "updated_at": execution_result.get("updated_at", ""),
    }


@app.command()
def list(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    all: bool = typer.Option(False, "--all", help="Show all projects"),
    status: str = typer.Option(None, "--status", help="Filter by status (pending, success, failed, exception)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List verification states across executions.
    
    Shows verification type, browser requirement, execution status.
    
    Examples:
        asyncdev verification list --all
        asyncdev verification list --project my-app
        asyncdev verification list --status pending
    """
    console.print(Panel("Verification Console", title="verification list", border_style="cyan"))
    
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return
    
    all_verifications = []
    for project_path in projects:
        results = _get_execution_results(project_path)
        for result in results:
            info = _extract_verification_info(result)
            if status and info["status"] != status:
                continue
            all_verifications.append(info)
    
    if not all_verifications:
        console.print("[green]No execution results found[/green]")
        return
    
    table = Table(title="Verification States")
    table.add_column("Execution ID", style="cyan", width=20)
    table.add_column("Project", style="green", width=15)
    table.add_column("Type", style="yellow", width=20)
    table.add_column("Browser Req", style="magenta", width=12)
    table.add_column("Status", style="blue", width=12)
    table.add_column("Gate", style="dim", width=10)
    table.add_column("Passed/Failed", style="white", width=12)
    
    status_style = {
        "success": "green",
        "failed": "red",
        "pending": "yellow",
        "exception": "orange1",
        "no_scenarios": "dim",
    }
    
    for v in all_verifications:
        style = status_style.get(v["status"], "white")
        browser_req = "Yes" if v["browser_required"] else "No"
        passed_failed = f"{v['passed']}/{v['failed']}" if v["browser_executed"] else "-"
        
        table.add_row(
            v["execution_id"][:20],
            v["project_id"],
            v["verification_type"],
            browser_req,
            f"[{style}]{v['status']}[/{style}]",
            v["gate_status"],
            passed_failed,
        )
    
    console.print(table)
    
    pending_count = len([v for v in all_verifications if v["status"] == "pending"])
    failed_count = len([v for v in all_verifications if v["status"] == "failed"])
    success_count = len([v for v in all_verifications if v["status"] == "success"])
    
    console.print(f"\n[bold]Summary:[/bold] {len(all_verifications)} executions")
    console.print(f"  [green]Success: {success_count}[/green]")
    console.print(f"  [yellow]Pending: {pending_count}[/yellow]")
    console.print(f"  [red]Failed: {failed_count}[/red]")
    
    if failed_count > 0:
        console.print(f"\n[bold]Failed Verifications:[/bold]")
        for v in all_verifications:
            if v["status"] == "failed":
                console.print(f"  [red]{v['execution_id']}[/red]: {v['failed']} scenarios failed")
                console.print(f"    [dim]Run: asyncdev verification retry --execution {v['execution_id']}[/dim]")
    
    console.print(f"\n[dim]Use 'asyncdev verification show --execution <id>' for details[/dim]")


@app.command()
def show(
    execution_id: str = typer.Option(..., "--execution", help="Execution ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed verification context.
    
    Displays classification, gate status, browser results, linked artifacts.
    
    Example:
        asyncdev verification show --execution exec-20260423-001
    """
    projects = _get_all_projects(path)
    
    found_result = None
    found_project = None
    
    for project_path in projects:
        store = StateStore(project_path)
        result = store.load_execution_result(execution_id)
        if result:
            found_result = result
            found_project = project_path
            break
    
    if not found_result or not found_project:
        console.print(f"[red]Execution not found: {execution_id}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Verification Details: {execution_id}", title="verification show", border_style="cyan"))
    
    info = _extract_verification_info(found_result)
    
    info_table = Table(title="Verification Classification", show_header=False)
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Execution ID", execution_id)
    info_table.add_row("Project", found_project.name)
    info_table.add_row("Verification Type", info["verification_type"])
    info_table.add_row("Browser Required", "Yes" if info["browser_required"] else "No")
    info_table.add_row("Completion Gate", info["gate_status"])
    info_table.add_row("Status", info["status"])
    
    console.print(info_table)
    
    browser_verification = found_result.get("browser_verification", {})
    
    if info["browser_required"]:
        console.print(f"\n[bold]Browser Verification:[/bold]")
        
        if info["browser_executed"]:
            console.print(f"  Executed: Yes")
            console.print(f"  Passed: {info['passed']}")
            console.print(f"  Failed: {info['failed']}")
            console.print(f"  Skipped: {info['skipped']}")
            
            if info["failed"] > 0:
                console.print(f"\n[yellow]Failed scenarios need review[/yellow]")
        else:
            console.print(f"  Executed: No")
            if info["exception_reason"]:
                console.print(f"  Exception Reason: {info['exception_reason']}")
            else:
                console.print(f"  [yellow]Browser verification not executed[/yellow]")
        
        scenarios_run = browser_verification.get("scenarios_run", [])
        if scenarios_run:
            console.print(f"\n[bold]Scenarios Run:[/bold]")
            for scenario in scenarios_run[:10]:
                console.print(f"  - {scenario}")
    
    frontend_recipe = found_result.get("frontend_recipe", {})
    if frontend_recipe:
        console.print(f"\n[bold]Frontend Recipe Stages:[/bold]")
        console.print(f"  Stage: {frontend_recipe.get('stage', 'N/A')}")
        console.print(f"  Framework: {frontend_recipe.get('framework', 'N/A')}")
        console.print(f"  Success: {frontend_recipe.get('success', 'N/A')}")
        
        if frontend_recipe.get("error_message"):
            console.print(f"  [red]Error: {frontend_recipe.get('error_message')}[/red]")
    
    console.print(f"\n[bold]Linked Artifacts:[/bold]")
    
    result_path = found_project / "execution-results" / f"{execution_id}.md"
    if result_path.exists():
        console.print(f"  ExecutionResult: {result_path}")
    
    screenshots_dir = found_project / "screenshots" / execution_id
    if screenshots_dir.exists():
        screenshots = list(screenshots_dir.glob("*.png"))
        if screenshots:
            console.print(f"  Screenshots: {len(screenshots)} files")
    
    console.print(f"\n[bold]Available Actions:[/bold]")
    
    if info["status"] == "failed":
        console.print(f"  [cyan]retry[/cyan]: Re-run frontend verification")
        console.print(f"  [dim]Run: asyncdev verification retry --execution {execution_id}[/dim]")
    elif info["status"] == "pending" and info["browser_required"]:
        console.print(f"  [cyan]run[/cyan]: Execute frontend verification recipe")
    else:
        console.print(f"  [dim]Verification completed[/dim]")


@app.command()
def classify(
    files: str = typer.Option(..., "--files", help="Files to classify (comma-separated)"),
    description: str = typer.Option("", "--description", help="Task description"),
):
    """Classify verification type for files/task.
    
    Returns VerificationType classification with reasoning.
    
    Example:
        asyncdev verification classify --files "src/components/Button.tsx,src/api/auth.py"
    """
    console.print(Panel("Verification Classification", title="verification classify", border_style="cyan"))
    
    file_list = [f.strip() for f in files.split(",")]
    
    result = classify_verification_type_from_files(file_list, description)
    
    console.print(f"\n[bold]Result:[/bold]")
    
    result_table = Table(show_header=False)
    result_table.add_column("Field", style="cyan")
    result_table.add_column("Value", style="green")
    
    result_table.add_row("Verification Type", result.verification_type.value)
    result_table.add_row("Confidence", f"{result.confidence:.2f}")
    result_table.add_row("Files Analyzed", str(result.files_analyzed))
    result_table.add_row("Reasoning", result.reasoning)
    
    console.print(result_table)
    
    if result.detected_patterns:
        console.print(f"\n[bold]Detected Patterns:[/bold]")
        for pattern in result.detected_patterns:
            console.print(f"  - {pattern}")
    
    browser_required = requires_browser_verification(result.verification_type.value)
    console.print(f"\n[bold]Browser Verification Required:[/bold] {browser_required}")


@app.command()
def gate(
    execution: str = typer.Option(..., "--execution", help="Execution ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check completion gate status.
    
    Returns 'allowed' or 'blocked' with reason.
    
    Example:
        asyncdev verification gate --execution exec-20260423-001
    """
    projects = _get_all_projects(path)
    
    found_result = None
    
    for project_path in projects:
        store = StateStore(project_path)
        result = store.load_execution_result(execution)
        if result:
            found_result = result
            break
    
    if not found_result:
        console.print(f"[red]Execution not found: {execution}[/red]")
        raise typer.Exit(1)
    
    verification_type = found_result.get("verification_type", "backend_only")
    gate_status = get_completion_gate_status(verification_type, found_result)
    
    console.print(Panel(f"Verification Gate: {execution}", title="verification gate", border_style="cyan"))
    
    if gate_status == "allowed":
        console.print(f"\n[bold green]Gate Status: ALLOWED[/bold green]")
        console.print(f"[dim]Execution may proceed to completion[/dim]")
    else:
        console.print(f"\n[bold red]Gate Status: BLOCKED[/bold red]")
        console.print(f"[dim]Browser verification required but not completed[/dim]")
        
        browser_verification = found_result.get("browser_verification", {})
        if browser_verification.get("exception_reason"):
            console.print(f"\n[yellow]Exception recorded: {browser_verification.get('exception_reason')}[/yellow]")
        else:
            console.print(f"\n[yellow]No browser verification executed[/yellow]")
            console.print(f"[dim]Run: asyncdev verification retry --execution {execution}[/dim]")
    
    console.print(f"\n[bold]Verification Type:[/bold] {verification_type}")
    console.print(f"[bold]Browser Required:[/bold] {requires_browser_verification(verification_type)}")


@app.command()
def retry(
    execution: str = typer.Option(..., "--execution", help="Execution ID to retry"),
    timeout: int = typer.Option(120, "--timeout", help="Browser verification timeout"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Retry failed frontend verification.
    
    Re-executes FrontendVerificationRecipe for failed executions.
    
    Example:
        asyncdev verification retry --execution exec-20260423-001 --timeout 180
    """
    projects = _get_all_projects(path)
    
    found_result = None
    found_project = None
    
    for project_path in projects:
        store = StateStore(project_path)
        result = store.load_execution_result(execution)
        if result:
            found_result = result
            found_project = project_path
            break
    
    if not found_result or not found_project:
        console.print(f"[red]Execution not found: {execution}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Retrying Verification: {execution}", title="verification retry", border_style="yellow"))
    
    verification_type = found_result.get("verification_type", "backend_only")
    
    if not requires_browser_verification(verification_type):
        console.print(f"[yellow]Browser verification not required for type: {verification_type}[/yellow]")
        return
    
    from runtime.frontend_verification_recipe import execute_frontend_verification_recipe
    
    console.print(f"[cyan]Executing frontend verification recipe...[/cyan]")
    console.print(f"[dim]Timeout: {timeout}s[/dim]")
    
    result = execute_frontend_verification_recipe(
        project_path=found_project,
        execution_id=execution,
        browser_verification_timeout=timeout,
    )
    
    if result.success:
        console.print(Panel(
            f"Execution: {execution}\n"
            f"Stage: {result.stage.value}\n"
            f"Passed: {result.browser_verification_result.get('passed', 0)}\n"
            f"Failed: {result.browser_verification_result.get('failed', 0)}",
            title="Verification Retry Success",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"Execution: {execution}\n"
            f"Stage: {result.stage.value}\n"
            f"Failure: {result.failure_reason.value}\n"
            f"Error: {result.error_message}",
            title="Verification Retry Failed",
            border_style="red"
        ))
        
        console.print(f"\n[bold]Failure Details:[/bold]")
        console.print(f"  Reason: {result.failure_reason.value}")
        console.print(f"  Message: {result.error_message}")
        
        if result.server_startup:
            console.print(f"\n[bold]Server Startup:[/bold]")
            console.print(f"  Detected Port: {result.server_startup.detected_port}")
            console.print(f"  Process ID: {result.server_startup.process_id}")


if __name__ == "__main__":
    app()