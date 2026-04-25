"""acceptance command - Acceptance Console CLI (Feature 077).

Canonical acceptance CLI surface for operator-usable acceptance workflow:
- acceptance run: Trigger acceptance validation
- acceptance status: Inspect acceptance state
- acceptance history: View attempt history
- acceptance result: Show detailed result
- acceptance retry: Re-run acceptance after remediation

Integration with:
- Feature 069-076 (Acceptance subsystem)
- run-day (mainflow integration)
- resume-next-day (continuation integration)
"""

from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.acceptance_readiness import (
    check_acceptance_readiness,
    AcceptanceReadiness,
    AcceptanceTriggerPolicyMode,
)
from runtime.acceptance_pack_builder import (
    build_acceptance_pack,
    save_acceptance_pack,
    load_acceptance_pack,
)
from runtime.acceptance_runner import (
    run_acceptance_from_execution,
    load_acceptance_result,
    AcceptanceTerminalState,
)
from runtime.acceptance_recovery import (
    get_recovery_items_for_feature,
    load_acceptance_recovery_pack,
)
from runtime.reacceptance_loop import (
    get_or_create_attempt_history,
    save_attempt_history,
    load_attempt_history,
    get_acceptance_lineage,
    trigger_reacceptance,
    ReAcceptancePolicy,
    ReAcceptanceState,
)
from runtime.acceptance_console import (
    list_acceptance_results,
    show_acceptance_result,
    show_acceptance_history,
    show_recovery_status,
    get_acceptance_summary,
    format_acceptance_console_output,
)
from runtime.acceptance_gating import (
    check_completion_gate,
    validate_acceptance_for_completion,
    AcceptancePolicyMode,
)

app = typer.Typer(help="Acceptance Console - Operator surface for acceptance validation")
console = Console()


def _resolve_project_path(
    project: str | None,
    path: Path,
) -> Path:
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            console.print(f"[yellow]Path checked: {project_path}[/yellow]")
            raise typer.Exit(1)
        return project_path
    
    projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if not projects:
        console.print("[red]No projects found[/red]")
        raise typer.Exit(1)
    
    if len(projects) == 1:
        return projects[0]
    
    console.print("[yellow]Multiple projects found. Specify --project[/yellow]")
    for p in projects:
        console.print(f"  {p.name}")
    raise typer.Exit(1)


def _resolve_feature_id(project_path: Path) -> str:
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate:
        return runstate.get("feature_id", "")
    
    return ""


@app.command()
def run(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    execution_id: str = typer.Option(None, "--execution", "-e", help="Execution ID"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID"),
    policy_mode: str = typer.Option("feature_completion_only", "--policy", help="Policy mode: always_trigger, feature_completion_only, manual_only"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without running"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Run acceptance validation for a feature execution (AC-002).
    
    Steps:
    1. Resolve target (feature/execution)
    2. Check acceptance readiness
    3. Build AcceptancePack if ready
    4. Invoke AcceptanceRunner
    5. Persist AcceptanceResult
    """
    project_path = _resolve_project_path(project, path)
    
    feature_id = feature or _resolve_feature_id(project_path)
    if not feature_id:
        console.print("[red]No feature ID found. Specify --feature[/red]")
        raise typer.Exit(1)
    
    execution_results_dir = project_path / "execution-results"
    if not execution_results_dir.exists():
        console.print("[red]No execution-results directory[/red]")
        console.print("[yellow]Run run-day first to generate ExecutionResult[/yellow]")
        raise typer.Exit(1)
    
    results = list(execution_results_dir.glob("*.md"))
    if not results:
        console.print("[red]No ExecutionResult found[/red]")
        raise typer.Exit(1)
    
    if execution_id:
        target_result = execution_results_dir / f"{execution_id}.md"
        if not target_result.exists():
            console.print(f"[red]ExecutionResult not found: {execution_id}[/red]")
            raise typer.Exit(1)
    else:
        target_result = sorted(results, key=lambda r: r.stat().st_mtime, reverse=True)[0]
        execution_id = target_result.stem
    
    console.print(Panel(
        f"Project: {project_path.name}\nFeature: {feature_id}\nExecution: {execution_id}\nPolicy: {policy_mode}",
        title="Acceptance Run",
        border_style="blue"
    ))
    
    mode_map = {
        "always_trigger": AcceptanceTriggerPolicyMode.ALWAYS_TRIGGER,
        "feature_completion_only": AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY,
        "manual_only": AcceptanceTriggerPolicyMode.MANUAL_ONLY,
    }
    policy = mode_map.get(policy_mode, AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY)
    
    readiness_result = check_acceptance_readiness(
        project_path,
        execution_id,
        policy,
    )
    
    if readiness_result.readiness != AcceptanceReadiness.READY:
        console.print(f"\n[yellow]Acceptance not ready: {readiness_result.readiness.value}[/yellow]")
        
        for prereq in readiness_result.prerequisites_checked:
            status_icon = "[green]✓[/green]" if prereq.satisfied else "[red]✗[/red]"
            console.print(f"  {status_icon} {prereq.name}: {prereq.description}")
            if prereq.failure_reason:
                console.print(f"    [red]{prereq.failure_reason}[/red]")
        
        console.print(f"\n[cyan]Next action: Resolve blockers before acceptance[/cyan]")
        raise typer.Exit(1)
    
    console.print("\n[green]All prerequisites satisfied[/green]")
    
    if dry_run:
        pack = build_acceptance_pack(project_path, execution_id)
        if pack:
            console.print(f"\n[cyan]AcceptancePack would be created: {pack.acceptance_pack_id}[/cyan]")
            console.print(f"  Feature: {pack.feature_id}")
            console.print(f"  Criteria: {len(pack.acceptance_criteria)}")
            console.print(f"  Evidence: {len(pack.evidence_artifacts)}")
        raise typer.Exit(0)
    
    console.print("\n[bold cyan]Running acceptance validation...[/bold cyan]")
    
    result = run_acceptance_from_execution(project_path, execution_id)
    
    if result is None:
        console.print("[red]Acceptance failed to run[/red]")
        raise typer.Exit(1)
    
    history = get_or_create_attempt_history(project_path, feature_id, execution_id)
    history.add_attempt(result)
    save_attempt_history(project_path, history)
    
    console.print(f"\n[bold]Acceptance Result: {result.terminal_state.value}[/bold]")
    console.print(f"  Result ID: {result.acceptance_result_id}")
    console.print(f"  Attempt: #{result.attempt_number}")
    console.print(f"  Accepted: {len(result.accepted_criteria)}")
    console.print(f"  Failed: {len(result.failed_criteria)}")
    console.print(f"  Conditional: {len(result.conditional_criteria)}")
    
    if result.terminal_state == AcceptanceTerminalState.ACCEPTED:
        console.print("\n[green]Feature ready for completion[/green]")
    elif result.terminal_state == AcceptanceTerminalState.CONDITIONAL:
        console.print("\n[yellow]Accepted with conditions - review before completion[/yellow]")
    elif result.terminal_state == AcceptanceTerminalState.REJECTED:
        console.print("\n[red]Acceptance rejected - recovery items created[/red]")
        console.print("[cyan]Run 'asyncdev acceptance recovery' to see items[/cyan]")
    elif result.terminal_state == AcceptanceTerminalState.MANUAL_REVIEW:
        console.print("\n[yellow]Manual review required[/yellow]")
    elif result.terminal_state == AcceptanceTerminalState.ESCALATED:
        console.print("\n[red]Escalation required[/red]")


@app.command()
def status(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Inspect acceptance status for a feature (AC-003).
    
    Shows:
    - Acceptance readiness
    - Latest attempt status
    - Pass/fail/conditional state
    - Linked result artifact
    - Whether completion is blocked
    """
    project_path = _resolve_project_path(project, path)
    
    feature_id = feature or _resolve_feature_id(project_path)
    if not feature_id:
        console.print("[red]No feature ID found. Specify --feature[/red]")
        raise typer.Exit(1)
    
    summary = get_acceptance_summary(project_path, feature_id)
    
    console.print(format_acceptance_console_output(summary, include_details=True))


@app.command("history")
def show_history(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Inspect prior acceptance attempts (AC-004).
    
    Shows:
    - How many attempts occurred
    - When they happened
    - Outcome of each attempt
    - Whether current result is latest/final
    """
    project_path = _resolve_project_path(project, path)
    
    feature_id = feature or _resolve_feature_id(project_path)
    if not feature_id:
        console.print("[red]No feature ID found. Specify --feature[/red]")
        raise typer.Exit(1)
    
    history_data = show_acceptance_history(project_path, feature_id)
    
    console.print(Panel(
        f"Feature: {feature_id}\nTotal Executions: {history_data.get('total_executions', 0)}\nTotal Attempts: {history_data.get('total_attempts', 0)}",
        title="Acceptance History",
        border_style="blue"
    ))
    
    attempts = history_data.get("attempts", [])
    
    if not attempts:
        console.print("\n[yellow]No acceptance history found[/yellow]")
        raise typer.Exit(0)
    
    table = Table(title="Acceptance Attempts")
    table.add_column("Execution", style="cyan")
    table.add_column("Attempts", style="magenta")
    table.add_column("Final State", style="green")
    table.add_column("Accepted", style="bold")
    
    for entry in attempts:
        table.add_row(
            entry.get("execution_result_id", ""),
            str(entry.get("total_attempts", 0)),
            entry.get("final_state", ""),
            "[green]Yes[/green]" if entry.get("accepted") else "[red]No[/red]",
        )
    
    console.print(table)


@app.command()
def result(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    result_id: str = typer.Option(None, "--id", help="Acceptance result ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed acceptance result (AC-004).
    
    Shows:
    - All findings per criterion
    - Accepted/failed/conditional criteria lists
    - Remediation guidance if rejected
    - Validator identity
    """
    project_path = _resolve_project_path(project, path)
    
    if not result_id:
        feature_id = _resolve_feature_id(project_path)
        summary = get_acceptance_summary(project_path, feature_id)
        result_id = summary.get("latest_result_id") or ""
        
        if not result_id:
            console.print("[red]No acceptance result found[/red]")
            console.print("[yellow]Specify --id or run acceptance first[/yellow]")
            raise typer.Exit(1)
    
    details = show_acceptance_result(project_path, result_id)
    
    if details is None:
        console.print(f"[red]Acceptance result not found: {result_id}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"Result ID: {details.get('acceptance_result_id')}\nTerminal State: {details.get('terminal_state')}\nFeature: {details.get('feature_id')}\nExecution: {details.get('execution_result_id')}\nAttempt: #{details.get('attempt_number')}\nValidator: {details.get('validator_type')} ({details.get('validator_id')})",
        title="Acceptance Result",
        border_style="blue"
    ))
    
    findings = details.get("findings", [])
    if findings:
        console.print("\n[bold]Findings:[/bold]")
        
        for finding in findings:
            result_icon = "[green]✓[/green]" if finding.get("result") == "passed" else "[red]✗[/red]" if finding.get("result") == "failed" else "[yellow]?[/yellow]"
            console.print(f"  {result_icon} {finding.get('criterion_id')}: {finding.get('criterion_text', '')[:50]}")
            if finding.get("notes"):
                console.print(f"    {finding.get('notes')}")
    
    remediation = details.get("remediation_guidance", [])
    if remediation:
        console.print("\n[bold red]Remediation Guidance:[/bold red]")
        
        for item in remediation:
            console.print(f"  [{item.get('priority')}] {item.get('criterion_id')}: {item.get('issue_type')}")
            console.print(f"    {item.get('suggested_fix')}")
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  {details.get('overall_summary')}")
    console.print(f"  Confidence: {details.get('confidence_score'):.1%}")


@app.command()
def retry(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID"),
    execution_id: str = typer.Option(None, "--execution", "-e", help="Execution ID"),
    policy: str = typer.Option("auto_retry", "--policy", help="Retry policy: auto_retry, manual_trigger, escalate_after_failures"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Re-run acceptance after remediation (AC-005).
    
    Creates new acceptance attempt when:
    - Previous acceptance rejected/conditional
    - Recovery items addressed
    - Retry policy allows
    """
    project_path = _resolve_project_path(project, path)
    
    feature_id = feature or _resolve_feature_id(project_path)
    if not feature_id:
        console.print("[red]No feature ID found. Specify --feature[/red]")
        raise typer.Exit(1)
    
    execution_results_dir = project_path / "execution-results"
    if not execution_results_dir.exists():
        console.print("[red]No execution-results directory[/red]")
        raise typer.Exit(1)
    
    results = list(execution_results_dir.glob("*.md"))
    if not results:
        console.print("[red]No ExecutionResult found[/red]")
        raise typer.Exit(1)
    
    if not execution_id:
        execution_id = sorted(results, key=lambda r: r.stat().st_mtime, reverse=True)[0].stem
    
    console.print(Panel(
        f"Project: {project_path.name}\nFeature: {feature_id}\nExecution: {execution_id}\nPolicy: {policy}",
        title="Acceptance Retry",
        border_style="blue"
    ))
    
    policy_map = {
        "auto_retry": ReAcceptancePolicy.AUTO_RETRY,
        "manual_trigger": ReAcceptancePolicy.MANUAL_TRIGGER,
        "escalate_after_failures": ReAcceptancePolicy.ESCALATE_AFTER_FAILURES,
    }
    retry_policy = policy_map.get(policy, ReAcceptancePolicy.AUTO_RETRY)
    
    history = get_or_create_attempt_history(project_path, feature_id, execution_id)
    
    console.print(f"\n[cyan]Current attempt count: {history.total_attempts}[/cyan]")
    console.print(f"  Accepted: {history.accepted_attempts}")
    console.print(f"  Rejected: {history.rejected_attempts}")
    console.print(f"  Max attempts: {history.max_attempts}")
    
    if not history.can_retry():
        console.print(f"\n[red]Cannot retry: max attempts ({history.max_attempts}) reached[/red]")
        raise typer.Exit(1)
    
    if history.is_terminal():
        console.print(f"\n[yellow]History already terminal: {history.current_state.value}[/yellow]")
        raise typer.Exit(1)
    
    console.print("\n[bold cyan]Triggering re-acceptance...[/bold cyan]")
    
    result = trigger_reacceptance(
        project_path,
        execution_id,
        feature_id,
        retry_policy,
    )
    
    if result is None:
        console.print("[red]Re-acceptance could not be triggered[/red]")
        console.print("[yellow]Check if recovery items are pending[/yellow]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold]Re-acceptance Result: {result.terminal_state.value}[/bold]")
    console.print(f"  Result ID: {result.acceptance_result_id}")
    console.print(f"  Attempt: #{result.attempt_number}")


@app.command()
def recovery(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show recovery status from failed acceptance (AC-004).
    
    Shows pending recovery items that need resolution before re-acceptance.
    """
    project_path = _resolve_project_path(project, path)
    
    feature_id = feature or _resolve_feature_id(project_path)
    if not feature_id:
        console.print("[red]No feature ID found. Specify --feature[/red]")
        raise typer.Exit(1)
    
    recovery_data = show_recovery_status(project_path, feature_id)
    
    console.print(Panel(
        f"Feature: {feature_id}\nPending Items: {recovery_data.get('pending_items', 0)}\nCritical: {recovery_data.get('critical_count', 0)}\nHigh: {recovery_data.get('high_count', 0)}",
        title="Acceptance Recovery",
        border_style="blue"
    ))
    
    items = recovery_data.get("items", [])
    
    if not items:
        console.print("\n[green]No pending recovery items[/green]")
        raise typer.Exit(0)
    
    console.print("\n[bold]Recovery Items:[/bold]")
    
    for item in items:
        priority_icon = "[red]![/red]" if item.get("priority") in ["critical", "high"] else "[yellow]○[/yellow]"
        console.print(f"  {priority_icon} [{item.get('priority')}] {item.get('criterion_id')}: {item.get('category')}")
        console.print(f"    {item.get('issue_description')}")
        console.print(f"    [cyan]Action: {item.get('suggested_action')}[/cyan]")
    
    console.print(f"\n[cyan]{recovery_data.get('next_action', '')}[/cyan]")


@app.command()
def gate(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID"),
    policy: str = typer.Option("strict", "--policy", help="Completion policy: strict, relaxed, optional, bypass_allowed"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check completion gate status (AC-008).
    
    Shows whether feature can be marked complete based on acceptance state.
    """
    project_path = _resolve_project_path(project, path)
    
    feature_id = feature or _resolve_feature_id(project_path)
    if not feature_id:
        console.print("[red]No feature ID found. Specify --feature[/red]")
        raise typer.Exit(1)
    
    policy_map = {
        "strict": AcceptancePolicyMode.STRICT,
        "relaxed": AcceptancePolicyMode.RELAXED,
        "optional": AcceptancePolicyMode.OPTIONAL,
        "bypass_allowed": AcceptancePolicyMode.BYPASS_ALLOWED,
    }
    gate_policy = policy_map.get(policy, AcceptancePolicyMode.STRICT)
    
    gate_check = check_completion_gate(project_path, feature_id, gate_policy)
    
    console.print(Panel(
        f"Feature: {feature_id}\nGate Result: {gate_check.result.value}\nAllowed: {gate_check.is_allowed()}",
        title="Completion Gate",
        border_style="green" if gate_check.is_allowed() else "red"
    ))
    
    if gate_check.blocking_reason:
        console.print(f"\n[red]Blocking Reason:[/red]")
        console.print(f"  {gate_check.blocking_reason}")
    
    if gate_check.is_allowed():
        console.print("\n[green]Feature ready for completion[/green]")
        console.print("[cyan]Run 'asyncdev complete-feature mark' to complete[/cyan]")
    else:
        console.print("\n[yellow]Resolve blockers before completion[/yellow]")
        
        requirements = []
        if gate_check.result.value == "blocked_acceptance_required":
            requirements.append("Run acceptance validation")
        elif gate_check.result.value == "blocked_acceptance_failed":
            requirements.append("Address recovery items")
        elif gate_check.result.value == "blocked_acceptance_pending":
            requirements.append("Complete manual review")
        elif gate_check.result.value == "blocked_recovery_items":
            requirements.append("Resolve pending recovery items")
        
        if requirements:
            console.print("\n[bold]Required Actions:[/bold]")
            for req in requirements:
                console.print(f"  • {req}")