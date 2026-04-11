"""plan-day command - Generate ExecutionPack for today's bounded task."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from runtime.state_store import StateStore, generate_execution_id
from runtime.execution_event_types import ExecutionEventType
from runtime.execution_logger import get_logger

app = typer.Typer(help="Plan today's bounded execution task")
console = Console()


@app.command()
def create(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option("001-core-object-system", help="Feature ID"),
    task: str = typer.Option(None, help="Specific task description"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Create ExecutionPack for today's bounded task."""
    project_path = path / project
    store = StateStore(project_path)
    logger = get_logger(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[yellow]No existing RunState found. Creating new one.[/yellow]")
        runstate = {
            "project_id": project,
            "feature_id": feature,
            "current_phase": "planning",
            "active_task": "",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Initialized RunState",
            "next_recommended_action": "Create first ExecutionPack",
            "updated_at": "",
        }

    feature_id = runstate.get("feature_id", feature)
    product_id = runstate.get("project_id", project)
    previous_phase = runstate.get("current_phase", "planning")

    logger.log_event(
        ExecutionEventType.PLAN_DAY_STARTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"project": project, "feature": feature, "task": task},
    )

    if task:
        runstate["active_task"] = task
        runstate["task_queue"] = [task]
    else:
        if not runstate.get("task_queue"):
            console.print("[red]No tasks in queue. Specify --task or update RunState.[/red]")
            raise typer.Exit(1)
        runstate["active_task"] = runstate["task_queue"][0]

    execution_id = generate_execution_id(project_path)
    execution_pack = {
        "execution_id": execution_id,
        "feature_id": runstate["feature_id"],
        "task_id": runstate["active_task"],
        "goal": f"Execute: {runstate['active_task']}",
        "task_scope": [runstate["active_task"]],
        "must_read": [],
        "constraints": ["Stay within task_scope"],
        "deliverables": [{"item": runstate["active_task"], "path": "", "type": "file"}],
        "verification_steps": ["Verify deliverable exists"],
        "stop_conditions": ["Deliverable completed", "Blocker encountered"],
    }

    table = Table(title="ExecutionPack Preview")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("execution_id", execution_id)
    table.add_row("feature_id", execution_pack["feature_id"])
    table.add_row("task_id", execution_pack["task_id"])
    table.add_row("goal", execution_pack["goal"])

    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    runstate["current_phase"] = "executing"
    store.save_runstate(runstate)
    store.save_execution_pack(execution_pack)

    logger.log_event(
        ExecutionEventType.PLAN_DAY_COMPLETED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "task": runstate["active_task"]},
    )
    logger.log_transition(
        from_phase=previous_phase,
        to_phase="executing",
        feature_id=feature_id,
        product_id=product_id,
        reason="Plan-day completed",
    )
    logger.close()

    console.print(f"[green]ExecutionPack created: {execution_id}[/green]")
    console.print("[bold]Next step:[/bold] Run 'asyncdev run-day' to execute (manual or mock)")

    console.print("\n[bold]Manual Execution Mode:[/bold]")
    console.print("1. AI reads ExecutionPack from execution-packs/{execution_id}.md")
    console.print("2. AI executes within task_scope")
    console.print("3. AI produces ExecutionResult")
    console.print("4. Run 'asyncdev resume-next-day' to continue")


@app.command()
def show(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show current RunState and pending tasks."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[yellow]No RunState found[/yellow]")
        return

    table = Table(title="Current RunState")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("project_id", runstate.get("project_id", "N/A"))
    table.add_row("feature_id", runstate.get("feature_id", "N/A"))
    table.add_row("current_phase", runstate.get("current_phase", "N/A"))
    table.add_row("active_task", runstate.get("active_task", "N/A"))
    table.add_row("task_queue", str(runstate.get("task_queue", [])))
    table.add_row("completed_outputs", str(len(runstate.get("completed_outputs", []))))
    table.add_row("blocked_items", str(len(runstate.get("blocked_items", []))))
    table.add_row("decisions_needed", str(len(runstate.get("decisions_needed", []))))

    console.print(table)


if __name__ == "__main__":
    app()