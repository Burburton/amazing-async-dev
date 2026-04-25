"""evidence command - Evidence Summary Console (Feature 079).

Operator surface for viewing rolled-up project/feature evidence.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.evidence_rollup import (
    build_project_evidence_summary,
    build_feature_evidence_summary,
    save_project_evidence_summary,
    save_feature_evidence_summary,
    LatestTruthResolver,
)
from runtime.state_store import StateStore

app = typer.Typer(help="Evidence Summary Console - Rolled-up project/feature evidence view")
console = Console()


@app.command()
def summary(
    project: str = typer.Option(..., "--project", help="Project ID"),
    feature: str = typer.Option(None, "--feature", help="Feature ID for feature-level summary"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    save: bool = typer.Option(False, "--save", help="Save summary to file"),
):
    """Show rolled-up evidence summary for project or feature."""
    
    project_path = path / project
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    if feature:
        summary_obj = build_feature_evidence_summary(project_path, feature)
        
        console.print(Panel(
            f"Feature: {summary_obj.feature_id}",
            title="Feature Evidence Summary",
            border_style="blue",
        ))
        
        table = Table(title="Evidence Overview", show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Execution Result", summary_obj.latest_execution_result_ref or "N/A")
        table.add_row("Execution Status", summary_obj.latest_execution_status or "N/A")
        table.add_row("Acceptance Result", summary_obj.latest_acceptance_result_ref or "N/A")
        table.add_row("Acceptance Status", summary_obj.acceptance_terminal_state or "N/A")
        table.add_row("Attempt Count", str(summary_obj.acceptance_attempt_count))
        table.add_row("Recovery Required", str(summary_obj.recovery_required))
        table.add_row("Recovery Classification", summary_obj.recovery_classification or "N/A")
        table.add_row("Completion Blocked", str(summary_obj.completion_blocked))
        table.add_row("Observer Findings", str(summary_obj.observer_findings_count))
        
        console.print(table)
        
        if summary_obj.needs_attention():
            console.print("\n[yellow]⚠ This feature needs attention[/yellow]")
            if summary_obj.completion_blocked_reason:
                console.print(f"  Reason: {summary_obj.completion_blocked_reason}")
        
        if save:
            output_path = save_feature_evidence_summary(project_path, summary_obj)
            console.print(f"\n[green]Saved to: {output_path}[/green]")
    
    else:
        summary_obj = build_project_evidence_summary(project_path)
        
        console.print(Panel(
            f"Project: {summary_obj.project_id}\nPhase: {summary_obj.current_phase}",
            title="Project Evidence Summary",
            border_style="blue",
        ))
        
        status_table = Table(title="Status Overview", show_header=False)
        status_table.add_column("Field", style="cyan")
        status_table.add_column("Value", style="green")
        
        status_table.add_row("Total Features", str(summary_obj.total_features))
        status_table.add_row("Healthy Features", str(summary_obj.healthy_features))
        status_table.add_row("Blocked Features", str(summary_obj.blocked_features))
        status_table.add_row("Recovery Pending", str(summary_obj.recovery_pending_features))
        status_table.add_row("Any Blocking", str(summary_obj.any_blocking))
        
        console.print(status_table)
        
        if summary_obj.features:
            features_table = Table(title="Features")
            features_table.add_column("Feature ID", style="cyan")
            features_table.add_column("Status", style="green")
            features_table.add_column("Acceptance", style="yellow")
            features_table.add_column("Blocked", style="red")
            
            for f in summary_obj.features:
                blocked_str = "Yes" if f.completion_blocked else "No"
                features_table.add_row(
                    f.feature_id,
                    f.latest_execution_status or "N/A",
                    f.acceptance_terminal_state or "N/A",
                    blocked_str,
                )
            
            console.print(features_table)
        
        if summary_obj.any_blocking:
            console.print(f"\n[red]Blocked: {summary_obj.blocking_summary}[/red]")
        
        console.print(f"\n[cyan]Next Action: {summary_obj.recommended_next_action}[/cyan]")
        
        if save:
            output_path = save_project_evidence_summary(project_path, summary_obj)
            console.print(f"[green]Saved to: {output_path}[/green]")


@app.command()
def latest(
    project: str = typer.Option(..., "--project", help="Project ID"),
    artifact_type: str = typer.Option("execution_result", "--type", help="Artifact type to resolve"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Resolve latest artifact of given type."""
    
    project_path = path / project
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    resolver = LatestTruthResolver(project_path)
    
    artifact_id, artifact_path = resolver.get_latest_artifact(artifact_type)
    
    if artifact_id:
        console.print(Panel(
            f"Type: {artifact_type}\nID: {artifact_id}\nPath: {artifact_path}",
            title="Latest Artifact",
            border_style="green",
        ))
    else:
        console.print(f"[yellow]No artifacts found for type: {artifact_type}[/yellow]")


@app.command()
def generate(
    project: str = typer.Option(..., "--project", help="Project ID"),
    feature: str = typer.Option(None, "--feature", help="Feature ID for feature-level summary"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Generate and save evidence summary file."""
    
    project_path = path / project
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    if feature:
        summary_obj = build_feature_evidence_summary(project_path, feature)
        output_path = save_feature_evidence_summary(project_path, summary_obj)
        console.print(f"[green]Feature evidence summary saved: {output_path}[/green]")
    else:
        summary_obj = build_project_evidence_summary(project_path)
        output_path = save_project_evidence_summary(project_path, summary_obj)
        console.print(f"[green]Project evidence summary saved: {output_path}[/green]")


@app.command()
def questions(
    project: str = typer.Option(..., "--project", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Answer canonical evidence questions per 079 Section 7.1."""
    
    project_path = path / project
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    resolver = LatestTruthResolver(project_path)
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    console.print(Panel("Evidence Questions", title="079 Section 7.1", border_style="blue"))
    
    questions_table = Table(title="Canonical Questions", show_header=False)
    questions_table.add_column("Question", style="cyan", width=40)
    questions_table.add_column("Answer", style="green", width=50)
    
    exec_id, _ = resolver.get_latest_execution_result()
    questions_table.add_row("Latest execution result?", exec_id or "N/A")
    
    accept_id, _ = resolver.get_latest_acceptance_result()
    questions_table.add_row("Latest acceptance result?", accept_id or "N/A")
    
    recovery_id, _ = resolver.get_latest_recovery_pack()
    questions_table.add_row("Latest recovery pack?", recovery_id or "N/A")
    
    recovery_required = runstate.get("acceptance_recovery_pending", False) if runstate else False
    questions_table.add_row("Active recovery condition?", str(recovery_required))
    
    completion_blocked = runstate.get("acceptance_terminal_state", "") == "rejected" if runstate else False
    questions_table.add_row("Completion blocked?", str(completion_blocked))
    
    feature_id = runstate.get("feature_id", "") if runstate else ""
    questions_table.add_row("Current feature?", feature_id or "N/A")
    
    console.print(questions_table)