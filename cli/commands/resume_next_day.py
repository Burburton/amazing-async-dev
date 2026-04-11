"""resume-next-day command - Continue from human decisions."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.state_store import StateStore, generate_execution_id

app = typer.Typer(help="Resume from human decisions, start next day loop")
console = Console()


@app.command()
def continue_loop(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    decision: str = typer.Option("approve", help="Human decision: approve/revise/defer/redefine"),
    revise_choice: str = typer.Option(None, help="Choice if decision=revise"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Process human decision and continue day loop."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    decisions_needed = runstate.get("decisions_needed", [])

    if not decisions_needed:
        console.print("[green]No pending decisions. Ready to continue.[/green]")
    else:
        console.print(f"[yellow]Processing decision: {decision}[/yellow]")

        if decision == "approve":
            runstate["decisions_needed"] = []
            console.print("[green]All decisions approved[/green]")

        elif decision == "revise":
            if not revise_choice:
                console.print("[red]Must specify --revise-choice for revise decision[/red]")
                raise typer.Exit(1)
            console.print(f"[green]Decision revised to: {revise_choice}[/green]")
            runstate["decisions_needed"] = []

        elif decision == "defer":
            console.print("[yellow]Decision deferred. Moving to alternative task.[/yellow]")

        elif decision == "redefine":
            console.print("[yellow]Decision redefined. Scope updated.[/yellow]")
            runstate["decisions_needed"] = []

    runstate["current_phase"] = "planning"
    runstate["last_action"] = f"Resumed with decision: {decision}"

    if runstate.get("task_queue"):
        next_task = runstate["task_queue"][0]
        runstate["next_recommended_action"] = f"Execute: {next_task}"
    else:
        runstate["next_recommended_action"] = "Add tasks to queue or complete feature"

    console.print(Panel(f"Resume Summary", title="resume-next-day", border_style="blue"))

    console.print(f"[bold]Current Phase:[/bold] {runstate['current_phase']}")
    console.print(f"[bold]Next Task:[/bold] {runstate.get('active_task', 'None')}")
    console.print(f"[bold]Queue:[/bold] {len(runstate.get('task_queue', []))} pending")
    console.print(f"[bold]Completed:[/bold] {len(runstate.get('completed_outputs', []))} outputs")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    store.save_runstate(runstate)

    console.print("\n[green]RunState updated. Ready for next day.[/green]")
    console.print("Next: Run 'asyncdev plan-day' to create new ExecutionPack")


@app.command()
def status(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show current RunState status for resume."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[yellow]No RunState found[/yellow]")
        return

    console.print(Panel("Current State", title="resume-status"))

    console.print(f"Phase: {runstate.get('current_phase')}")
    console.print(f"Project: {runstate.get('project_id')}")
    console.print(f"Feature: {runstate.get('feature_id')}")

    if runstate.get("decisions_needed"):
        console.print("\n[bold yellow]Pending Decisions:[/bold yellow]")
        for d in runstate["decisions_needed"]:
            console.print(f"  - {d.get('decision', 'unknown')}")
            console.print(f"    Options: {d.get('options', [])}")

    console.print(f"\n[bold]Completed Outputs:[/bold] {len(runstate.get('completed_outputs', []))}")
    console.print(f"[bold]Task Queue:[/bold] {len(runstate.get('task_queue', []))} pending")
    console.print(f"[bold]Next Recommended:[/bold] {runstate.get('next_recommended_action', 'N/A')}")


if __name__ == "__main__":
    app()


@app.command()
def unblock(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    reason: str = typer.Option(None, help="Resolution note for blocker"),
    retry: bool = typer.Option(False, help="Retry the same task"),
    alternative: str = typer.Option(None, help="Alternative task to try"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Resume from blocked state to executing.

    Usage:
        asyncdev resume-next-day unblock --reason "Dependency resolved"
        asyncdev resume-next-day unblock --retry
        asyncdev resume-next-day unblock --alternative "task-002-backup"
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    current_phase = runstate.get("current_phase")

    if current_phase != "blocked":
        console.print(f"[yellow]Current phase: {current_phase}[/yellow]")
        console.print("This command is only for blocked state.")
        console.print("Use 'asyncdev resume-next-day continue-loop' for other phases.")
        raise typer.Exit(1)

    blocked_items = runstate.get("blocked_items", [])

    console.print(Panel("Unblock State", title="resume-next-day unblock", border_style="green"))

    console.print(f"[bold]Blocked Items:[/bold] {len(blocked_items)}")
    if blocked_items:
        for item in blocked_items[:3]:
            console.print(f"  - {item.get('reason', 'unknown')}")

    resolution_note = reason or "Manual unblock"
    console.print(f"\n[cyan]Resolution:[/cyan] {resolution_note}")

    runstate["current_phase"] = "planning"
    runstate["blocked_items"] = []
    runstate["last_action"] = f"Unblocked: {resolution_note}"

    if retry:
        console.print("[green]Will retry same task[/green]")
        runstate["next_recommended_action"] = f"Retry: {runstate.get('active_task', 'unknown')}"
    elif alternative:
        console.print(f"[green]Will try alternative: {alternative}[/green]")
        runstate["active_task"] = alternative
        runstate["next_recommended_action"] = f"Execute: {alternative}"
    else:
        console.print("[yellow]Choose next action: --retry or --alternative[/yellow]")
        runstate["next_recommended_action"] = "Review blocker resolution, plan next task"

    store.save_runstate(runstate)

    console.print("\n[green]Blocker resolved. Ready to continue.[/green]")
    console.print("Next: Run 'asyncdev plan-day' to create new ExecutionPack")


@app.command()
def handle_failed(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    report: bool = typer.Option(False, help="Generate failure report"),
    escalate: bool = typer.Option(False, help="Escalate as decision needed"),
    abandon: bool = typer.Option(False, help="Abandon task and move to next"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Handle failed execution state.

    Failed state transitions to blocked for human intervention.

    Usage:
        asyncdev resume-next-day handle-failed --report
        asyncdev resume-next-day handle-failed --escalate
        asyncdev resume-next-day handle-failed --abandon
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    console.print(Panel("Handle Failed State", title="resume-next-day handle-failed", border_style="yellow"))

    console.print("[yellow]Failed execution detected[/yellow]")
    console.print("Converting to blocked state for human intervention...")

    if escalate:
        decision_item = {
            "decision": f"Task {runstate.get('active_task', 'unknown')} failed",
            "options": ["retry", "alternative approach", "abandon"],
            "recommendation": "Retry with adjusted parameters",
            "impact": "Feature progress blocked",
            "urgency": "high",
        }
        runstate["decisions_needed"] = [decision_item]
        runstate["current_phase"] = "reviewing"
        console.print("[cyan]Escalated to decision needed[/cyan]")

    elif abandon:
        runstate["blocked_items"] = []
        runstate["current_phase"] = "planning"
        if runstate.get("task_queue"):
            runstate["active_task"] = runstate["task_queue"][0]
            runstate["task_queue"] = runstate["task_queue"][1:]
        console.print("[green]Task abandoned. Moving to next[/green]")

    else:
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [{
            "reason": "Execution failed",
            "resolution": "Needs human intervention",
            "options": ["Retry", "Change approach", "Abandon"],
        }]
        console.print("[yellow]State set to blocked[/yellow]")
        console.print("Use 'asyncdev resume-next-day unblock' to resolve")

    runstate["last_action"] = f"Handled failed state: {escalate or abandon or 'blocked'}"

    store.save_runstate(runstate)

    console.print("\nNext action depends on choice:")
    if escalate:
        console.print("  Run 'asyncdev review-night' to see decision options")
    elif abandon:
        console.print("  Run 'asyncdev plan-day' to plan next task")
    else:
        console.print("  Run 'asyncdev resume-next-day unblock' to resolve blocker")