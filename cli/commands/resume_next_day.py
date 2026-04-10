"""resume-next-day command - Continue from human decisions."""

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.state_store import StateStore, generate_execution_id

app = typer.Typer(help="Resume from human decisions, start next day loop")
console = Console()
store = StateStore()


@app.command()
def continue_loop(
    decision: str = typer.Option("approve", help="Human decision: approve/revise/defer/redefine"),
    revise_choice: str = typer.Option(None, help="Choice if decision=revise"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
):
    """Process human decision and continue day loop."""
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
def status():
    """Show current RunState status for resume."""
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