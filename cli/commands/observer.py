"""observer command - Execution Observer CLI (Feature 066).

Commands to run execution observation and view findings.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.execution_observer import (
    ExecutionObserver,
    ObserverFindingType,
    FindingSeverity,
    run_observer,
)

app = typer.Typer(help="Execution Observer - Monitor async-dev execution state")
console = Console()


@app.command()
def run(
    project: str = typer.Option(None, "--project", help="Project ID to observe"),
    all: bool = typer.Option(False, "--all", help="Observe all projects"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Run execution observation on project(s).
    
    Detects:
    - Stalled executions
    - Timeout issues
    - Missing artifacts
    - Verification failures
    - Closeout incomplete
    - Decision overdue
    """
    console.print(Panel("Execution Observer", title="observer run", border_style="cyan"))
    
    projects_to_observe = []
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects_to_observe = [project_path]
    elif all:
        projects_to_observe = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    else:
        if path.exists():
            projects_to_observe = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    if not projects_to_observe:
        console.print("[yellow]No projects found to observe[/yellow]")
        return
    
    total_findings = 0
    critical_count = 0
    high_count = 0
    
    for project_path in projects_to_observe:
        result = run_observer(project_path)
        
        console.print(f"\n[bold]{project_path.name}[/bold]")
        console.print(f"  Findings: {len(result.findings)}")
        
        if result.has_critical_findings():
            console.print(f"  [red]CRITICAL findings detected[/red]")
            critical_count += 1
        
        if result.findings:
            total_findings += len(result.findings)
            high_count += sum(1 for f in result.findings if f.severity == FindingSeverity.HIGH)
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Type", style="cyan")
            table.add_column("Severity", style="yellow")
            table.add_column("Reason")
            table.add_column("Action")
            
            for finding in result.findings:
                severity_style = {
                    FindingSeverity.CRITICAL: "red",
                    FindingSeverity.HIGH: "yellow",
                    FindingSeverity.MEDIUM: "blue",
                    FindingSeverity.LOW: "dim",
                    FindingSeverity.INFO: "dim",
                }.get(finding.severity, "")
                
                table.add_row(
                    finding.finding_type.value,
                    f"[{severity_style}]{finding.severity.value}[/{severity_style}]",
                    finding.reason[:50] + "..." if len(finding.reason) > 50 else finding.reason,
                    finding.suggested_action[:40] + "..." if len(finding.suggested_action) > 40 else finding.suggested_action,
                )
            
            console.print(table)
    
    console.print(f"\n[bold]Summary[/bold]")
    console.print(f"  Projects observed: {len(projects_to_observe)}")
    console.print(f"  Total findings: {total_findings}")
    console.print(f"  Projects with critical: {critical_count}")
    console.print(f"  Projects with high: {high_count}")
    
    if total_findings > 0:
        console.print(f"\n[yellow]Recommended: Use 'asyncdev recovery list' to see recovery actions[/yellow]")


@app.command()
def status(
    project: str = typer.Option(None, "--project", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show observer status for a project.
    
    Quick check without full observation run.
    """
    if project:
        project_path = path / project
    else:
        projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return
        project_path = projects[0]
    
    if not project_path.exists():
        console.print(f"[red]Project not found[/red]")
        raise typer.Exit(1)
    
    result = run_observer(project_path)
    
    console.print(Panel(
        f"Project: {project_path.name}\n"
        f"Findings: {len(result.findings)}\n"
        f"Critical: {result.has_critical_findings()}\n"
        f"Recovery Required: {result.has_recovery_required()}\n"
        f"Summary: {result.summary}",
        title="Observer Status",
        border_style="cyan"
    ))


@app.command()
def types():
    """List all observer finding types."""
    console.print(Panel("Observer Finding Types", title="observer types", border_style="cyan"))
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Finding Type")
    table.add_column("Description")
    
    type_descriptions = {
        ObserverFindingType.STALLED_EXECUTION: "No progress for threshold duration",
        ObserverFindingType.TIMEOUT_DETECTED: "Closeout or verification timeout",
        ObserverFindingType.MISSING_ARTIFACT: "Expected artifact not found",
        ObserverFindingType.VERIFICATION_FAILURE: "Verification failed or not executed",
        ObserverFindingType.CLOSEOUT_INCOMPLETE: "Closeout did not reach terminal state",
        ObserverFindingType.DECISION_OVERDUE: "Decision pending over threshold",
        ObserverFindingType.BLOCKED_STATE: "Execution blocked by external issue",
        ObserverFindingType.RECOVERY_REQUIRED: "Execution requires recovery action",
    }
    
    for finding_type, description in type_descriptions.items():
        table.add_row(finding_type.value, description)
    
    console.print(table)


@app.command()
def severities():
    """List all finding severity levels."""
    console.print(Panel("Finding Severities", title="observer severities", border_style="cyan"))
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Severity")
    table.add_column("Style")
    
    for severity in FindingSeverity:
        style = {
            FindingSeverity.CRITICAL: "red bold",
            FindingSeverity.HIGH: "yellow",
            FindingSeverity.MEDIUM: "blue",
            FindingSeverity.LOW: "dim",
            FindingSeverity.INFO: "dim",
        }.get(severity, "")
        
        table.add_row(f"[{style}]{severity.value}[/{style}]", style)
    
    console.print(table)