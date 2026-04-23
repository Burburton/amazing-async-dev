"""recovery command - Execution Recovery Console (Operator Surface).

Feature: Execution Recovery Console
Feature 066a: Wired recovery actions to async-dev flows (AC-003)
Architecture Reference: docs/infra/async-dev-platform-architecture-product-positioning.md (Section 12.1)
Spec: docs/infra/execution-recovery-console-spec-v1.md
"""

from pathlib import Path
from datetime import datetime
import subprocess
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.sqlite_state_store import SQLiteStateStore
from runtime.recovery_classifier import (
    classify_recovery,
    check_resume_eligibility,
    get_recovery_guidance,
    RecoveryClassification,
    ResumeEligibility,
)
from runtime.execution_observer import run_observer, ObservationResult
from runtime.recovery_data_adapter import RecoveryDataAdapter, get_recovery_item_for_project

app = typer.Typer(help="Execution Recovery Console - Operator surface for recovery operations")
console = Console()


def _invoke_asyncdev_command(command: str, project_id: str, extra_args: list[str] = None) -> int:
    """Invoke an asyncdev CLI command via subprocess and return exit code."""
    cli_path = Path(__file__).parent.parent / "asyncdev.py"
    args = [sys.executable, str(cli_path)] + command.split() + ["--project", project_id]
    if extra_args:
        args.extend(extra_args)
    
    console.print(f"\n[cyan]Invoking: {command} --project {project_id}[/cyan]")
    result = subprocess.run(args, capture_output=True, text=True)
    
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")
    
    return result.returncode


def _get_all_projects(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]


def _get_recoveries_for_project(project_path: Path) -> list[dict]:
    adapter = RecoveryDataAdapter(project_path)
    item = adapter.get_recovery_item()
    
    if item is None:
        return []
    
    return [{
        "project": item.product_id,
        "feature": item.feature_id,
        "execution_id": item.execution_id,
        "classification": item.status,
        "phase": item.phase,
        "reason": item.recovery_reason,
        "category": item.recovery_category,
        "recommended_action": item.suggested_action,
        "recommended_command": item.suggested_command,
        "updated_at": item.last_updated_at,
        "blocked_count": len(item.blocked_items),
        "decisions_count": len(item.decisions_needed),
        "observer_findings_count": len(item.observer_findings),
        "verification_status": item.verification_status,
        "closeout_status": item.closeout_status,
        "project_path": project_path,
    }]


@app.command()
def list(
    project: str = typer.Option(None, "--project", help="Filter by project ID"),
    all: bool = typer.Option(False, "--all", help="Show all projects (default)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List all executions needing recovery.
    
    Shows executions across all projects that are in recovery-required state:
    - BLOCKED: Workflow blocked by external dependency
    - FAILED: Execution failed unexpectedly
    - AWAITING_DECISION: Waiting for human decision
    - UNSAFE_TO_RESUME: State inconsistent, needs inspection
    """
    console.print(Panel("Execution Recovery Console", title="recovery list", border_style="blue"))
    
    projects = _get_all_projects(path)
    
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(1)
        projects = [project_path]
    
    all_recoveries = []
    for project_path in projects:
        recoveries = _get_recoveries_for_project(project_path)
        all_recoveries.extend(recoveries)
    
    if not all_recoveries:
        console.print("[green]No executions needing recovery[/green]")
        console.print("[dim]All workflows are in healthy state[/dim]")
        return
    
    urgency_order = {
        "failed": 0,
        "blocked": 1,
        "awaiting_decision": 2,
        "unsafe_to_resume": 3,
    }
    
    all_recoveries.sort(key=lambda r: (
        urgency_order.get(r["classification"], 4),
        r["updated_at"] or "",
    ))
    
    table = Table(title="Executions Needing Recovery")
    table.add_column("Execution ID", style="cyan", width=25)
    table.add_column("Project", style="green", width=15)
    table.add_column("Classification", style="yellow", width=18)
    table.add_column("Reason", style="white", width=35)
    table.add_column("Suggested Action", style="magenta", width=25)
    table.add_column("Updated", style="dim", width=10)
    
    classification_style = {
        "failed": "red",
        "blocked": "orange1",
        "awaiting_decision": "yellow",
        "unsafe_to_resume": "magenta",
    }
    
    for r in all_recoveries:
        style = classification_style.get(r["classification"], "white")
        updated = r["updated_at"][:10] if r["updated_at"] else "N/A"
        reason_short = r["reason"][:35] if len(r["reason"]) > 35 else r["reason"]
        action_short = r["recommended_action"][:25] if len(r["recommended_action"]) > 25 else r["recommended_action"]
        
        table.add_row(
            r["execution_id"],
            r["project"],
            f"[{style}]{r['classification']}[/{style}]",
            reason_short,
            action_short,
            updated,
        )
    
    console.print(table)
    
    console.print(f"\n[bold]Summary:[/bold] {len(all_recoveries)} executions need recovery")
    
    counts = {}
    for r in all_recoveries:
        c = r["classification"]
        counts[c] = counts.get(c, 0) + 1
    
    console.print("\n[bold]By Type:[/bold]")
    for c, count in sorted(counts.items(), key=lambda x: urgency_order.get(x[0], 4)):
        style = classification_style.get(c, "white")
        console.print(f"  [{style}]{c}[/{style}]: {count}")
    
    console.print(f"\n[dim]Use 'asyncdev recovery show --execution <id>' for details[/dim]")
    console.print(f"[dim]Use 'asyncdev recovery resume --execution <id> --action <action>' to recover[/dim]")


@app.command()
def show(
    execution: str = typer.Option(..., "--execution", help="Execution ID to inspect"),
    observe: bool = typer.Option(False, "--observe", help="Run observer for additional findings"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed recovery information for an execution."""
    parts = execution.split("-")
    if len(parts) < 3 or parts[0] != "exec":
        console.print(f"[red]Invalid execution ID format: {execution}[/red]")
        console.print("[yellow]Expected format: exec-{project}-{feature}[/yellow]")
        raise typer.Exit(1)
    
    project_id = "-".join(parts[1:-1])
    feature_id = parts[-1]
    
    project_path = path / project_id
    if not project_path.exists():
        console.print(f"[red]Project not found: {project_id}[/red]")
        raise typer.Exit(1)
    
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print(f"[red]No RunState found for project: {project_id}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Recovery Details: {execution}", title="recovery show", border_style="blue"))
    
    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)
    guidance = get_recovery_guidance(runstate)
    
    classification_style = {
        RecoveryClassification.FAILED: "red",
        RecoveryClassification.BLOCKED: "orange1",
        RecoveryClassification.AWAITING_DECISION: "yellow",
        RecoveryClassification.UNSAFE_TO_RESUME: "magenta",
        RecoveryClassification.NORMAL_PAUSE: "green",
        RecoveryClassification.READY_TO_RESUME: "green",
    }
    
    style = classification_style.get(classification, "white")
    
    info_table = Table(title="Recovery Analysis", show_header=False)
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Execution ID", execution)
    info_table.add_row("Project", project_id)
    info_table.add_row("Feature", feature_id)
    info_table.add_row("Classification", f"[{style}]{classification.value}[/{style}]")
    info_table.add_row("Eligibility", eligibility.value)
    info_table.add_row("Current Phase", runstate.get("current_phase", "N/A"))
    info_table.add_row("Last Action", runstate.get("last_action", "N/A")[:50])
    info_table.add_row("Updated", runstate.get("updated_at", "N/A")[:19])
    
    console.print(info_table)
    
    console.print(Panel(guidance["explanation"], title="Diagnosis", border_style="yellow"))
    console.print(f"[bold cyan]Recommended Action:[/bold cyan] {guidance['recommended_action']}")
    
    if guidance.get("warnings"):
        console.print("\n[bold red]Warnings:[/bold red]")
        for w in guidance["warnings"]:
            console.print(f"  - {w}")
    
    console.print(f"\n[bold]Context:[/bold]")
    console.print(f"  Blocked items: {guidance['blocked_count']}")
    console.print(f"  Pending decisions: {guidance['decisions_count']}")
    
    sqlite_store = SQLiteStateStore(project_path)
    events = sqlite_store.get_recent_events(feature_id, limit=10)
    
    if events:
        console.print("\n[bold]Recent Events:[/bold]")
        events_table = Table()
        events_table.add_column("Event", style="cyan")
        events_table.add_column("Time", style="dim")
        
        for e in events[:5]:
            event_type = e.get("event_type", "unknown")
            event_time = e.get("occurred_at", "N/A")
            events_table.add_row(event_type, event_time[:19] if len(event_time) > 19 else event_time)
        
        console.print(events_table)
    
    sqlite_store.close()
    
    console.print("\n[bold]Linked Artifacts:[/bold]")
    
    runstate_path = project_path / "runstate.md"
    if runstate_path.exists():
        console.print(f"  RunState: {runstate_path}")
    
    execution_packs_dir = project_path / "execution-packs"
    if execution_packs_dir.exists():
        packs = sorted(execution_packs_dir.glob("*.md"))
        if packs:
            console.print(f"  ExecutionPacks: {len(packs)} files")
            console.print(f"    Latest: {packs[-1].name}")
    
    execution_results_dir = project_path / "execution-results"
    if execution_results_dir.exists():
        results = sorted(execution_results_dir.glob("*.md"))
        if results:
            console.print(f"  ExecutionResults: {len(results)} files")
            console.print(f"    Latest: {results[-1].name}")
    
    console.print("\n[bold]Available Recovery Actions:[/bold]")
    
    action_map = {
        RecoveryClassification.BLOCKED: [
            ("unblock", "Resolve blocker and continue"),
            ("abort", "Abort execution"),
        ],
        RecoveryClassification.FAILED: [
            ("retry", "Retry failed step"),
            ("escalate", "Escalate for human handling"),
            ("abort", "Abort execution"),
        ],
        RecoveryClassification.AWAITING_DECISION: [
            ("continue", "Apply pending decision and continue"),
            ("defer", "Defer and wait"),
            ("abort", "Abort execution"),
        ],
        RecoveryClassification.UNSAFE_TO_RESUME: [
            ("inspect", "Manual inspection required"),
            ("reset", "Reset to safe state"),
            ("abort", "Abort execution"),
        ],
    }
    
    available_actions = action_map.get(classification, [("abort", "Abort execution")])
    
    for action, desc in available_actions:
        console.print(f"  [cyan]{action}[/cyan]: {desc}")
    
    if observe:
        console.print("\n[bold]Observer Findings:[/bold]")
        
        obs_result = run_observer(project_path)
        
        if obs_result.findings:
            findings_table = Table()
            findings_table.add_column("Type", style="cyan")
            findings_table.add_column("Severity", style="yellow")
            findings_table.add_column("Reason")
            findings_table.add_column("Action")
            findings_table.add_column("Detected", style="dim")
            
            for f in obs_result.findings:
                sev_style = {
                    "critical": "red bold",
                    "high": "yellow",
                    "medium": "blue",
                }.get(f.severity.value, "")
                
                detected = f.detected_at[:19] if len(f.detected_at) > 19 else f.detected_at
                
                findings_table.add_row(
                    f.finding_type.value,
                    f"[{sev_style}]{f.severity.value}[/{sev_style}]",
                    f.reason[:40] if len(f.reason) > 40 else f.reason,
                    f.suggested_action[:35] if len(f.suggested_action) > 35 else f.suggested_action,
                    detected,
                )
            
            console.print(findings_table)
            
            recovery_sig = [f for f in obs_result.findings if f.recovery_significant]
            if recovery_sig:
                console.print(f"\n[bold red]Recovery-significant findings: {len(recovery_sig)}[/bold red]")
            
            if obs_result.findings:
                for f in obs_result.findings[:3]:
                    if f.related_artifacts:
                        console.print(f"[dim]Related artifacts for {f.finding_type.value}:[/dim]")
                        for artifact in f.related_artifacts[:2]:
                            console.print(f"  [dim]- {artifact}[/dim]")
            
            console.print(f"[dim]Summary: {obs_result.summary}[/dim]")
        else:
            console.print("[green]No observer findings[/green]")
    
    console.print(f"\n[dim]Run: asyncdev recovery resume --execution {execution} --action <action>[/dim]")


@app.command()
def resume(
    execution: str = typer.Argument(..., help="Execution ID (exec-{project}-{feature})"),
    action: str = typer.Argument(..., help="Recovery action (unblock, abort, continue, retry, reset, defer, inspect, escalate)"),
    reason: str = typer.Option(None, "--reason", help="Reason for recovery action"),
    execute: bool = typer.Option(False, "--execute", help="Execute the suggested asyncdev command after recovery"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Execute a recovery action to resume execution.
    
    With --execute flag, automatically invokes the suggested asyncdev command.
    Without --execute, updates state and prints suggested command for operator review.
    """
    parts = execution.split("-")
    if len(parts) < 3 or parts[0] != "exec":
        console.print(f"[red]Invalid execution ID format: {execution}[/red]")
        raise typer.Exit(1)
    
    project_id = "-".join(parts[1:-1])
    feature_id = parts[-1]
    
    project_path = path / project_id
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print(f"[red]No RunState found[/red]")
        raise typer.Exit(1)
    
    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)
    
    console.print(Panel(f"Executing Recovery: {action}", title="recovery resume", border_style="green"))
    
    valid_action_map = {
        RecoveryClassification.BLOCKED: ["unblock", "abort"],
        RecoveryClassification.FAILED: ["retry", "escalate", "abort"],
        RecoveryClassification.AWAITING_DECISION: ["continue", "defer", "abort"],
        RecoveryClassification.UNSAFE_TO_RESUME: ["inspect", "reset", "abort"],
        RecoveryClassification.NORMAL_PAUSE: ["continue"],
        RecoveryClassification.READY_TO_RESUME: ["continue"],
    }
    
    valid_actions = valid_action_map.get(classification, [])
    
    if action not in valid_actions:
        console.print(f"[red]Action '{action}' not valid for classification '{classification.value}'[/red]")
        console.print(f"[yellow]Valid actions: {', '.join(valid_actions)}[/yellow]")
        raise typer.Exit(1)
    
    if action == "abort":
        console.print("[yellow]Aborting execution...[/yellow]")
        runstate["current_phase"] = "completed"
        runstate["last_action"] = f"recovery_abort: {reason or 'Operator aborted'}"
        runstate["updated_at"] = datetime.now().isoformat()
        store.save_runstate(runstate)
        console.print("[green]Execution aborted[/green]")
        console.print("[dim]RunState updated to 'completed' phase[/dim]")
    
    elif action == "unblock":
        console.print("[yellow]Unblocking execution...[/yellow]")
        runstate["blocked_items"] = []
        runstate["current_phase"] = "planning"
        runstate["last_action"] = f"recovery_unblock: {reason or 'Operator unblocked'}"
        runstate["updated_at"] = datetime.now().isoformat()
        store.save_runstate(runstate)
        console.print("[green]Blockers cleared[/green]")
        console.print("[dim]RunState updated to 'planning' phase[/dim]")
        console.print("[dim]Next: asyncdev plan-day create[/dim]")
    
    elif action == "continue":
        console.print("[yellow]Continuing execution...[/yellow]")
        runstate["current_phase"] = "planning"
        runstate["last_action"] = f"recovery_continue: {reason or 'Operator approved continue'}"
        runstate["updated_at"] = datetime.now().isoformat()
        store.save_runstate(runstate)
        console.print("[green]Execution ready to continue[/green]")
        console.print("[dim]RunState updated to 'planning' phase[/dim]")
        console.print("[dim]Next: asyncdev plan-day create[/dim]")
    
    elif action == "retry":
        console.print("[yellow]Marking for retry...[/yellow]")
        runstate["current_phase"] = "planning"
        runstate["last_action"] = f"recovery_retry: {reason or 'Operator approved retry'}"
        runstate["updated_at"] = datetime.now().isoformat()
        store.save_runstate(runstate)
        console.print("[green]Ready for retry[/green]")
        console.print("[dim]RunState updated to 'planning' phase[/dim]")
        console.print("[dim]Next: asyncdev run-day[/dim]")
    
    elif action == "defer":
        console.print("[yellow]Deferring execution...[/yellow]")
        runstate["last_action"] = f"recovery_defer: {reason or 'Operator deferred'}"
        runstate["updated_at"] = datetime.now().isoformat()
        store.save_runstate(runstate)
        console.print("[green]Execution deferred[/green]")
        console.print("[dim]RunState unchanged, decisions preserved[/dim]")
    
    elif action == "inspect":
        console.print("[yellow]Marking for manual inspection...[/yellow]")
        console.print("[bold]Manual inspection required[/bold]")
        console.print(f"[dim]Run: asyncdev inspect-stop --project {project_id}[/dim]")
    
    elif action == "reset":
        console.print("[yellow]Resetting to safe state...[/yellow]")
        runstate["current_phase"] = "planning"
        runstate["blocked_items"] = []
        runstate["decisions_needed"] = []
        runstate["active_task"] = None
        runstate["last_action"] = f"recovery_reset: {reason or 'Operator reset state'}"
        runstate["updated_at"] = datetime.now().isoformat()
        store.save_runstate(runstate)
        console.print("[green]State reset[/green]")
        console.print("[dim]RunState reset to clean 'planning' phase[/dim]")
        console.print("[dim]Next: asyncdev plan-day create[/dim]")
    
    elif action == "escalate":
        console.print("[yellow]Escalating to human...[/yellow]")
        console.print("[bold]This requires manual intervention[/bold]")
        console.print(f"[dim]Review the execution and decide: {execution}[/dim]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)
    
    sqlite_store = SQLiteStateStore(project_path)
    sqlite_store.log_event(
        "recovery-action",
        feature_id=feature_id,
        product_id=project_id,
        event_data={
            "action": action,
            "reason": reason,
            "classification": classification.value,
        },
    )
    sqlite_store.close()
    
    console.print(f"\n[dim]Recovery logged to SQLite[/dim]")
    
    if execute and action in ("unblock", "continue", "retry", "reset"):
        next_command = {
            "unblock": "plan-day create",
            "continue": "plan-day create",
            "retry": "run-day --mode external",
            "reset": "plan-day create",
        }
        cmd = next_command.get(action)
        if cmd:
            exit_code = _invoke_asyncdev_command(cmd, project_id)
            if exit_code != 0:
                console.print(f"[red]Command failed with exit code {exit_code}[/red]")
                raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()