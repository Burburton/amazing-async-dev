"""inspect-stop command - Stop-point visibility and recovery diagnosis."""

from pathlib import Path

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
)
from runtime.execution_event_types import ExecutionEventType, get_event_description

app = typer.Typer(help="Inspect workflow stop point and recovery options")
console = Console()


@app.command()
def show(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID (optional, uses current if not specified)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show stop-point details and recovery options."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    feature_id = feature or runstate.get("feature_id", "")
    product_id = runstate.get("project_id", "")

    console.print(Panel("Stop-Point Inspection", title="inspect-stop", border_style="blue"))

    runstate_table = Table(title="RunState Summary")
    runstate_table.add_column("Field", style="cyan")
    runstate_table.add_column("Value", style="green")
    runstate_table.add_row("Phase", runstate.get("current_phase", "N/A"))
    runstate_table.add_row("Feature", feature_id)
    runstate_table.add_row("Active Task", runstate.get("active_task", "N/A"))
    runstate_table.add_row("Last Action", runstate.get("last_action", "N/A"))
    runstate_table.add_row("Updated", runstate.get("updated_at", "N/A"))
    console.print(runstate_table)

    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)
    guidance = get_recovery_guidance(runstate)

    recovery_table = Table(title="Recovery Analysis")
    recovery_table.add_column("Field", style="cyan")
    recovery_table.add_column("Value", style="green")
    recovery_table.add_row("Classification", classification.value)
    recovery_table.add_row("Eligibility", eligibility.value)
    console.print(recovery_table)

    console.print(Panel(guidance["explanation"], title="Diagnosis", border_style="yellow"))
    console.print(f"[bold]Recommended Action:[/bold] {guidance['recommended_action']}")

    if guidance.get("warnings"):
        console.print("\n[bold red]Warnings:[/bold red]")
        for w in guidance["warnings"]:
            console.print(f"  - {w}")

    sqlite_store = SQLiteStateStore(project_path)
    events = sqlite_store.get_recent_events(feature_id, limit=5)

    if events:
        console.print("\n[bold]Recent Events:[/bold]")
        events_table = Table()
        events_table.add_column("Event", style="cyan")
        events_table.add_column("Time", style="green")
        for e in events:
            event_type = e.get("event_type", "unknown")
            event_time = e.get("occurred_at", "N/A")
            events_table.add_row(event_type, event_time[:19] if len(event_time) > 19 else event_time)
        console.print(events_table)
    else:
        console.print("\n[yellow]No recent events in SQLite[/yellow]")

    transitions = sqlite_store.get_transitions(feature_id)
    if transitions:
        console.print("\n[bold]Phase Transitions:[/bold]")
        transitions_table = Table()
        transitions_table.add_column("From", style="cyan")
        transitions_table.add_column("To", style="green")
        transitions_table.add_column("Reason", style="yellow")
        for t in transitions[:5]:
            transitions_table.add_row(
                t.get("from_phase", "N/A"),
                t.get("to_phase", "N/A"),
                t.get("reason", "N/A")[:30] if t.get("reason") else "N/A"
            )
        console.print(transitions_table)

    sqlite_store.close()

    console.print("\n[bold]Guidance:[/bold]")
    if eligibility.value == "eligible":
        console.print("[green]Workflow is ready to resume[/green]")
        console.print("  Run: asyncdev plan-day create")
    elif eligibility.value == "needs_decision":
        console.print("[yellow]Pending decisions must be resolved[/yellow]")
        console.print("  Run: asyncdev resume-next-day continue-loop --decision <choice>")
    elif eligibility.value == "needs_unblock":
        console.print("[red]Blockers must be resolved[/red]")
        console.print("  Run: asyncdev resume-next-day unblock --reason '<resolution>'")
    elif eligibility.value == "needs_failure_handling":
        console.print("[red]Failed state requires intervention[/red]")
        console.print("  Run: asyncdev resume-next-day handle-failed --<option>")
    else:
        console.print("[red]State is inconsistent or terminal[/red]")
        console.print("  Manual inspection recommended")


@app.command()
def history(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID"),
    limit: int = typer.Option(20, help="Number of events to show"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed execution history."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    feature_id = feature or (runstate.get("feature_id", "") if runstate else "")

    if not feature_id:
        console.print("[red]No feature ID found[/red]")
        raise typer.Exit(1)

    sqlite_store = SQLiteStateStore(project_path)
    events = sqlite_store.get_recent_events(feature_id, limit=limit)

    console.print(Panel(f"Execution History ({limit} events)", title="inspect-stop history", border_style="blue"))

    if not events:
        console.print("[yellow]No events found[/yellow]")
        sqlite_store.close()
        return

    table = Table()
    table.add_column("#", style="dim")
    table.add_column("Event Type", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Time", style="yellow")

    for i, e in enumerate(events, 1):
        event_type = e.get("event_type", "unknown")
        try:
            et = ExecutionEventType(event_type)
            desc = get_event_description(et)
        except ValueError:
            desc = event_type
        event_time = e.get("occurred_at", "N/A")
        table.add_row(
            str(i),
            event_type,
            desc[:40] if len(desc) > 40 else desc,
            event_time[:19] if len(event_time) > 19 else event_time
        )

    console.print(table)
    sqlite_store.close()


@app.command()
def guidance(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show recovery guidance for current state."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    guidance = get_recovery_guidance(runstate)
    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)

    console.print(Panel("Recovery Guidance", title="inspect-stop guidance", border_style="green"))

    console.print(f"[bold]Classification:[/bold] {classification.value}")
    console.print(f"[bold]Eligibility:[/bold] {eligibility.value}")
    console.print(f"[bold]Explanation:[/bold] {guidance['explanation']}")

    console.print(f"\n[bold cyan]Recommended Action:[/bold cyan]")
    console.print(f"  {guidance['recommended_action']}")

    if guidance.get("warnings"):
        console.print(f"\n[bold red]Warnings:[/bold red]")
        for w in guidance["warnings"]:
            console.print(f"  - {w}")

    console.print(f"\n[bold]Context:[/bold]")
    console.print(f"  Blocked items: {guidance['blocked_count']}")
    console.print(f"  Pending decisions: {guidance['decisions_count']}")
    console.print(f"  Current phase: {guidance['phase']}")


if __name__ == "__main__":
    app()