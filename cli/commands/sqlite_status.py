"""SQLite status commands for inspecting persisted state and events."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.sqlite_state_store import SQLiteStateStore

app = typer.Typer(help="SQLite state store queries")
console = Console()


@app.command()
def history(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID"),
    limit: int = typer.Option(20, help="Number of events to show"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show recent events from SQLite."""
    project_path = path / project
    store = SQLiteStateStore(project_path)

    feature_id = feature
    if not feature_id:
        runstate = store.load_runstate()
        if runstate:
            feature_id = runstate.get("feature_id", "")

    if not feature_id:
        console.print("[yellow]No feature_id found[/yellow]")
        return

    events = store.get_recent_events(feature_id, limit)

    if not events:
        console.print(f"[dim]No events recorded for {feature_id}[/dim]")
        return

    table = Table(title=f"Recent Events: {feature_id}")
    table.add_column("Event Type", style="cyan")
    table.add_column("Time", style="dim")
    table.add_column("Data", style="green")

    for event in events:
        table.add_row(
            event.get("event_type", "N/A"),
            event.get("occurred_at", "N/A")[:19],
            str(event.get("event_data", {}))[:50],
        )

    console.print(table)


@app.command()
def transitions(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show lifecycle transitions from SQLite."""
    project_path = path / project
    store = SQLiteStateStore(project_path)

    feature_id = feature
    if not feature_id:
        runstate = store.load_runstate()
        if runstate:
            feature_id = runstate.get("feature_id", "")

    if not feature_id:
        console.print("[yellow]No feature_id found[/yellow]")
        return

    transitions = store.get_transitions(feature_id)

    if not transitions:
        console.print(f"[dim]No transitions recorded for {feature_id}[/dim]")
        return

    table = Table(title=f"Lifecycle Transitions: {feature_id}")
    table.add_column("From", style="yellow")
    table.add_column("To", style="green")
    table.add_column("Time", style="dim")
    table.add_column("Reason", style="cyan")

    for t in transitions:
        table.add_row(
            t.get("from_phase", "N/A"),
            t.get("to_phase", "N/A"),
            t.get("transitioned_at", "N/A")[:19],
            t.get("reason", "")[:30],
        )

    console.print(table)


@app.command()
def recovery(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show recovery information from SQLite."""
    project_path = path / project
    store = SQLiteStateStore(project_path)

    feature_id = feature
    if not feature_id:
        runstate = store.load_runstate()
        if runstate:
            feature_id = runstate.get("feature_id", "")

    if not feature_id:
        console.print("[yellow]No feature_id found[/yellow]")
        return

    info = store.get_recovery_info(feature_id)

    console.print(Panel(f"Recovery Info: {feature_id}", border_style="blue"))

    snapshot = info.get("latest_snapshot")
    if snapshot:
        console.print("[bold]Latest Snapshot:[/bold]")
        console.print(f"  Phase: {snapshot.get('phase', 'N/A')}")
        console.print(f"  Active Task: {snapshot.get('active_task', 'N/A')}")
        console.print(f"  Time: {snapshot.get('snapshot_at', 'N/A')[:19]}")
    else:
        console.print("[dim]No snapshot recorded[/dim]")

    console.print(f"\n[bold]Can Resume:[/bold] {info.get('can_resume', False)}")

    events_count = len(info.get("recent_events", []))
    console.print(f"[bold]Recent Events:[/bold] {events_count}")

    transitions_count = len(info.get("transitions", []))
    console.print(f"[bold]Transitions:[/bold] {transitions_count}")


@app.command()
def features(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List all features from SQLite."""
    project_path = path / project
    store = SQLiteStateStore(project_path)

    features = store.list_features(project)

    if not features:
        console.print("[dim]No features in SQLite[/dim]")
        console.print("Features are registered when using new-feature command")
        return

    table = Table(title=f"Features: {project}")
    table.add_column("Feature ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Phase", style="yellow")
    table.add_column("Updated", style="dim")

    for f in features:
        table.add_row(
            f.get("feature_id", "N/A"),
            f.get("name", "N/A")[:30],
            f.get("current_phase", "N/A"),
            f.get("updated_at", "N/A")[:19],
        )

    console.print(table)


@app.command()
def snapshot(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show latest RunState snapshot from SQLite."""
    project_path = path / project
    store = SQLiteStateStore(project_path)

    feature_id = feature
    if not feature_id:
        runstate = store.load_runstate()
        if runstate:
            feature_id = runstate.get("feature_id", "")

    if not feature_id:
        console.print("[yellow]No feature_id found[/yellow]")
        return

    snapshot = store.get_latest_snapshot(feature_id)

    if not snapshot:
        console.print(f"[dim]No snapshot for {feature_id}[/dim]")
        return

    console.print(Panel(f"Snapshot: {feature_id}", border_style="green"))

    console.print(f"[bold]Phase:[/bold] {snapshot.get('phase', 'N/A')}")
    console.print(f"[bold]Active Task:[/bold] {snapshot.get('active_task', 'N/A')}")
    console.print(f"[bold]Snapshot Time:[/bold] {snapshot.get('snapshot_at', 'N/A')}")

    task_queue = snapshot.get("task_queue", [])
    console.print(f"\n[bold]Task Queue:[/bold] {len(task_queue)} items")
    for task in task_queue[:5]:
        console.print(f"  - {task}")

    completed = snapshot.get("completed_outputs", [])
    console.print(f"[bold]Completed:[/bold] {len(completed)} outputs")
    for item in completed[:5]:
        console.print(f"  - {item}")

    blocked = snapshot.get("blocked_items", [])
    console.print(f"[bold]Blocked:[/bold] {len(blocked)} items")
    for item in blocked[:3]:
        console.print(f"  - {item}")


if __name__ == "__main__":
    app()