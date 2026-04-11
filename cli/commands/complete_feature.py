"""complete-feature command - Mark a feature as completed."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Mark feature as completed and prepare for archiving")
console = Console()


@app.command()
def mark(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID to complete"),
    status: str = typer.Option("completed", help="Final status: completed/partial/abandoned"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Mark a feature as completed.

    Validates completion eligibility:
    - No pending blockers
    - No pending decisions
    - Records completion metadata

    Example:
        asyncdev complete-feature mark --project my-app --feature 001-auth
        asyncdev complete-feature mark --project demo --feature 001-core --status partial
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    feature_id = feature or runstate.get("feature_id", "")
    if not feature_id:
        console.print("[red]No feature_id specified or found in RunState[/red]")
        raise typer.Exit(1)

    console.print(Panel(f"Complete Feature: {feature_id}", title="complete-feature", border_style="green"))

    table = Table(title="Completion Eligibility Check")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")

    blocked_items = runstate.get("blocked_items", [])
    decisions_needed = runstate.get("decisions_needed", [])
    current_phase = runstate.get("current_phase", "planning")

    blocked_ok = len(blocked_items) == 0
    decisions_ok = len(decisions_needed) == 0
    phase_ok = current_phase in ["planning", "reviewing", "executing"]

    table.add_row("No pending blockers", "✅" if blocked_ok else f"❌ {len(blocked_items)} blockers")
    table.add_row("No pending decisions", "✅" if decisions_ok else f"❌ {len(decisions_needed)} decisions")
    table.add_row("Phase eligible", "✅" if phase_ok else f"❌ phase={current_phase}")

    console.print(table)

    if not blocked_ok:
        console.print("[yellow]Warning: Feature has pending blockers[/yellow]")
        console.print("Resolve blockers before completing, or use --force")

    if not decisions_ok:
        console.print("[yellow]Warning: Feature has pending decisions[/yellow]")
        console.print("Make decisions before completing, or use --force")

    if not phase_ok and current_phase == "archived":
        console.print("[red]Feature is already archived[/red]")
        raise typer.Exit(1)

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    runstate["current_phase"] = "completed"
    runstate["last_action"] = f"Feature marked as {status}: {feature_id}"
    runstate["next_recommended_action"] = "Run 'asyncdev archive-feature' to archive this feature"

    if status != "completed":
        runstate["completion_status"] = status

    store.save_runstate(runstate)

    runstate_path = store.project_path / "runstate.md"

    print_success_panel(
        message=f"Feature {feature_id} marked as {status}",
        title="Complete-Feature Done",
        paths=[
            {"label": "RunState", "path": str(runstate_path)},
        ],
        root=root,
    )

    print_next_step(
        action="Archive the completed feature",
        command="asyncdev archive-feature create",
        artifact_path=runstate_path,
        root=root,
    )


@app.command()
def status(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show completion eligibility status for current feature."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[yellow]No RunState found[/yellow]")
        return

    console.print(Panel("Completion Status", title="complete-feature status", border_style="blue"))

    feature_id = runstate.get("feature_id", "N/A")
    current_phase = runstate.get("current_phase", "N/A")
    blocked_items = runstate.get("blocked_items", [])
    decisions_needed = runstate.get("decisions_needed", [])
    completed_outputs = runstate.get("completed_outputs", [])

    console.print(f"[bold]Feature:[/bold] {feature_id}")
    console.print(f"[bold]Phase:[/bold] {current_phase}")
    console.print(f"[bold]Completed Outputs:[/bold] {len(completed_outputs)}")
    console.print(f"[bold]Blocked Items:[/bold] {len(blocked_items)}")
    console.print(f"[bold]Pending Decisions:[/bold] {len(decisions_needed)}")

    eligible = len(blocked_items) == 0 and len(decisions_needed) == 0 and current_phase != "archived"

    if eligible:
        console.print("\n[green]✅ Feature is eligible for completion[/green]")
    else:
        console.print("\n[yellow]❌ Feature has unresolved items[/yellow]")
        if blocked_items:
            console.print(f"  Blockers: {len(blocked_items)}")
        if decisions_needed:
            console.print(f"  Decisions: {len(decisions_needed)}")


@app.command()
def force(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID to complete"),
    status: str = typer.Option("completed", help="Final status"),
    reason: str = typer.Option("Manual override", help="Reason for force completion"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Force complete a feature even with unresolved items.

    Use with caution - bypasses eligibility checks.
    Records the override reason for audit.
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    feature_id = feature or runstate.get("feature_id", "")
    if not feature_id:
        console.print("[red]No feature_id[/red]")
        raise typer.Exit(1)

    console.print(Panel(f"Force Complete: {feature_id}", border_style="yellow"))
    console.print(f"[yellow]Reason: {reason}[/yellow]")

    runstate["current_phase"] = "completed"
    runstate["completion_status"] = status
    runstate["completion_override"] = {
        "reason": reason,
        "forced_at": True,
    }
    runstate["last_action"] = f"Force completed: {feature_id} ({reason})"
    runstate["next_recommended_action"] = "Run 'asyncdev archive-feature'"

    store.save_runstate(runstate)

    console.print(f"\n[green]Feature {feature_id} force completed[/green]")
    console.print("[yellow]Note: Unresolved items preserved in RunState[/yellow]")


if __name__ == "__main__":
    app()