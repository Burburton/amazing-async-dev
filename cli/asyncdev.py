"""Amazing Async Dev - Personal Async AI Development OS CLI."""

import typer
from rich.console import Console

from cli.commands import plan_day, run_day, review_night, resume_next_day
from cli.commands import init, new_product, new_feature
from cli.commands import complete_feature, archive_feature
from cli.commands import sqlite_status

app = typer.Typer(
    name="asyncdev",
    help="Personal Async AI Development OS - Day-sized async development loops",
    add_completion=False,
)

console = Console()

# Register initialization commands
app.add_typer(init.app, name="init", help="Initialize project structure")
app.add_typer(new_product.app, name="new-product", help="Create new product")
app.add_typer(new_feature.app, name="new-feature", help="Create new feature")

# Register day loop commands
app.add_typer(plan_day.app, name="plan-day", help="Plan today's bounded task")
app.add_typer(run_day.app, name="run-day", help="Run today's execution (manual or mock)")
app.add_typer(review_night.app, name="review-night", help="Generate nightly review pack")
app.add_typer(resume_next_day.app, name="resume-next-day", help="Resume from decisions")

# Register lifecycle completion commands
app.add_typer(complete_feature.app, name="complete-feature", help="Mark feature as completed")
app.add_typer(archive_feature.app, name="archive-feature", help="Archive completed feature")

# Register SQLite commands
app.add_typer(sqlite_status.app, name="sqlite", help="SQLite state store queries")


@app.command()
def status():
    """Show current RunState status."""
    from runtime.state_store import StateStore
    
    store = StateStore()
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[yellow]No active RunState found[/yellow]")
        console.print("Run 'asyncdev plan-day' to start a new day loop")
        return
    
    console.print("[bold]Current RunState[/bold]")
    console.print(f"  Project: {runstate.get('project_id', 'N/A')}")
    console.print(f"  Feature: {runstate.get('feature_id', 'N/A')}")
    console.print(f"  Phase: {runstate.get('current_phase', 'N/A')}")
    console.print(f"  Active Task: {runstate.get('active_task', 'N/A')}")
    console.print(f"  Queue: {len(runstate.get('task_queue', []))} pending")
    console.print(f"  Completed: {len(runstate.get('completed_outputs', []))} outputs")
    console.print(f"  Blocked: {len(runstate.get('blocked_items', []))} items")
    console.print(f"  Decisions: {len(runstate.get('decisions_needed', []))} pending")


@app.command()
def version():
    """Show version."""
    console.print("[bold]amazing-async-dev[/bold] v0.1.0")


if __name__ == "__main__":
    app()