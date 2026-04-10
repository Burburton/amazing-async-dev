"""run-day command - Execute today's task (manual or mock mode)."""

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.state_store import StateStore
from runtime.adapters.llm_adapter import get_adapter

app = typer.Typer(help="Run today's execution task")
console = Console()
store = StateStore()


@app.command()
def execute(
    execution_id: str = typer.Option(None, help="Execution ID to run"),
    mock: bool = typer.Option(False, help="Use mock execution instead of manual"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
):
    """Execute today's bounded task.

    Default mode: MANUAL EXECUTION
    - Generates ExecutionPack if needed
    - Outputs instructions for human to trigger AI
    - AI runs autonomously within scope
    - User calls resume-next-day after AI completes

    Mock mode: MOCK EXECUTION (--mock)
    - Uses MockLLMAdapter
    - Generates fake ExecutionResult
    - Completes full flow for testing
    """
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found. Run 'asyncdev plan-day' first.[/red]")
        raise typer.Exit(1)

    if runstate.get("current_phase") != "executing":
        console.print(f"[yellow]Current phase: {runstate.get('current_phase')}[/yellow]")
        console.print("Run 'asyncdev plan-day' to start execution phase.")
        raise typer.Exit(1)

    if execution_id is None:
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        if not packs:
            console.print("[red]No ExecutionPack found. Run 'asyncdev plan-day' first.[/red]")
            raise typer.Exit(1)
        execution_id = packs[-1].stem

    execution_pack = store.load_execution_pack(execution_id)

    if execution_pack is None:
        console.print(f"[red]ExecutionPack not found: {execution_id}[/red]")
        raise typer.Exit(1)

    console.print(Panel(f"Execution ID: {execution_id}", title="Run-Day", border_style="blue"))

    if mock:
        console.print("[bold cyan]MOCK MODE[/bold cyan] - Using MockLLMAdapter")
        adapter = get_adapter(mock=True)
        result = adapter.execute(execution_pack)

        console.print("\n[green]Mock ExecutionResult:[/green]")
        console.print(f"  Status: {result['status']}")
        console.print(f"  Completed: {result['completed_items']}")
        console.print(f"  Artifacts: {len(result['artifacts_created'])}")

        if dry_run:
            console.print("[yellow]Dry run - not saving[/yellow]")
            return

        store.save_execution_result(result)
        runstate["current_phase"] = "reviewing"
        store.save_runstate(runstate)

        console.print("\n[green]Mock execution complete![/green]")
        console.print("Next: Run 'asyncdev review-night' to generate DailyReviewPack")
        return

    console.print("[bold yellow]MANUAL EXECUTION MODE[/bold yellow]")
    console.print("\nThe ExecutionPack is ready. You need to:")
    console.print("\n[bold]Step 1:[/bold] Trigger AI to read and execute")
    console.print(f"  AI should read: execution-packs/{execution_id}.md")
    console.print(f"  AI must stay within: {execution_pack.get('task_scope', [])}")
    console.print(f"  AI must complete: {execution_pack.get('deliverables', [])}")
    console.print(f"  AI must stop at: {execution_pack.get('stop_conditions', [])}")

    console.print("\n[bold]Step 2:[/bold] After AI completes, create ExecutionResult")
    console.print("  Save to: execution-results/{execution_id}.md")
    console.print("  Required fields: status, completed_items, artifacts_created, verification_result")

    console.print("\n[bold]Step 3:[/bold] Continue the loop")
    console.print("  Run: asyncdev resume-next-day")

    console.print(f"\n[dim]ExecutionPack location: {store.execution_packs_path / execution_id}.md[/dim]")


@app.command()
def mock_quick():
    """Quick mock execution for testing the full flow."""
    console.print("[bold cyan]Quick Mock Test[/bold cyan]")

    runstate = store.load_runstate()
    if runstate is None:
        console.print("[yellow]Creating minimal RunState for test[/yellow]")
        runstate = {
            "project_id": "demo-product-001",
            "feature_id": "001-test",
            "current_phase": "executing",
            "active_task": "test-task",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Test setup",
            "next_recommended_action": "Run mock",
            "updated_at": "",
        }
        store.save_runstate(runstate)

    adapter = get_adapter(mock=True)
    test_pack = {
        "execution_id": "exec-test-001",
        "feature_id": "001-test",
        "task_id": "test-task",
        "goal": "Test execution flow",
        "task_scope": ["test"],
        "deliverables": [{"item": "test-output", "path": "test.md", "type": "file"}],
        "verification_steps": ["Check output"],
        "stop_conditions": ["Complete"],
    }

    result = adapter.execute(test_pack)
    store.save_execution_result(result)

    console.print("[green]Mock execution complete![/green]")
    console.print(f"Result saved: execution-results/exec-test-001.md")
    console.print("Next: asyncdev review-night")


if __name__ == "__main__":
    app()