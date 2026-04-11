"""run-day command - Execute today's task with selected engine mode.

Modes:
- external (default): Generate ExecutionPack for external tools
- live: Direct API execution via BailianLLMAdapter
- mock: Testing and demonstration
"""

from pathlib import Path
import subprocess
import typer
from rich.console import Console
from rich.panel import Panel

from runtime.state_store import StateStore
from runtime.engines.factory import get_engine, get_available_modes

app = typer.Typer(help="Run today's execution task")
console = Console()
store = StateStore()


@app.command()
def execute(
    execution_id: str = typer.Option(None, help="Execution ID to run"),
    mode: str = typer.Option(
        "external",
        help="Execution mode: external (default), live, mock"
    ),
    trigger: bool = typer.Option(
        False,
        help="Trigger external tool after preparing pack (external mode only)"
    ),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
):
    """Execute today's bounded task with selected engine.

    External Mode (--mode external, default):
    - Saves ExecutionPack in YAML + Markdown formats
    - Outputs instructions for triggering external tools
    - Use --trigger to auto-start OpenCode
    - Awaits external execution and result consumption

    Live Mode (--mode live):
    - Direct API call via BailianLLMAdapter
    - Returns ExecutionResult immediately
    - Requires DASHSCOPE_API_KEY environment variable

    Mock Mode (--mode mock):
    - Fake execution for testing workflow
    - Returns mock ExecutionResult
    """
    available = get_available_modes()
    if not available.get(mode, False):
        console.print(f"[red]Mode '{mode}' is not available[/red]")
        console.print(f"Available modes: {list(available.keys())}")
        raise typer.Exit(1)

    engine = get_engine(mode)
    console.print(Panel(
        f"Mode: {mode}\nEngine: {engine.get_mode_name()}",
        title="Run-Day",
        border_style="blue"
    ))

    if mode == "external":
        return _run_external_mode(execution_id, engine, trigger, dry_run)
    elif mode == "live":
        return _run_live_mode(execution_id, engine, dry_run)
    elif mode == "mock":
        return _run_mock_mode(execution_id, engine, dry_run)


def _run_external_mode(
    execution_id: str | None,
    engine,
    trigger: bool,
    dry_run: bool,
) -> None:
    """Execute in external tool mode.

    Saves ExecutionPack and optionally triggers external tool.
    """
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

    engine.output_dir = store.execution_packs_path

    prep_result = engine.prepare(execution_pack)

    console.print("\n[green]ExecutionPack prepared:[/green]")
    console.print(f"  YAML: {prep_result['yaml_path']}")
    console.print(f"  Markdown: {prep_result['md_path']}")

    console.print(f"\n[cyan]{prep_result['instructions']}[/cyan]")

    if trigger:
        _trigger_external_tool(prep_result['md_path'])

    if dry_run:
        console.print("[yellow]Dry run - external mode does not modify state[/yellow]")


def _run_live_mode(
    execution_id: str | None,
    engine,
    dry_run: bool,
) -> None:
    """Execute in live API mode."""
    runstate = store.load_runstate()
    if runstate is None:
        console.print("[red]No RunState found. Run 'asyncdev plan-day' first.[/red]")
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

    prep = engine.prepare(execution_pack)
    if prep.get("status") != "ready":
        console.print(f"[red]ExecutionPack invalid: missing {prep.get('missing_fields', [])}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[cyan]Executing via API (model: {prep.get('model', 'unknown')})...[/cyan]")

    result = engine.run(execution_pack)

    console.print("\n[green]ExecutionResult:[/green]")
    console.print(f"  Status: {result['status']}")
    console.print(f"  Completed: {result['completed_items']}")
    console.print(f"  Artifacts: {len(result['artifacts_created'])}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    store.save_execution_result(result)
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)

    console.print("\n[green]Live execution complete![/green]")
    console.print("Next: Run 'asyncdev review-night' to generate DailyReviewPack")


def _run_mock_mode(
    execution_id: str | None,
    engine,
    dry_run: bool,
) -> None:
    """Execute in mock mode for testing."""
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

    if execution_id is None:
        execution_id = "exec-test-001"

    test_pack = {
        "execution_id": execution_id,
        "feature_id": "001-test",
        "task_id": "test-task",
        "goal": "Test execution flow",
        "task_scope": ["test"],
        "deliverables": [{"item": "test-output", "path": "test.md", "type": "file"}],
        "verification_steps": ["Check output"],
        "stop_conditions": ["Complete"],
    }

    result = engine.run(test_pack)

    console.print("\n[green]Mock ExecutionResult:[/green]")
    console.print(f"  Status: {result['status']}")
    console.print(f"  Completed: {result['completed_items']}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    store.save_execution_result(result)
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)

    console.print("\n[green]Mock execution complete![/green]")
    console.print("Next: Run 'asyncdev review-night' to generate DailyReviewPack")


def _trigger_external_tool(pack_path: str) -> None:
    """Trigger OpenCode to execute the ExecutionPack.

    Uses subprocess to call opencode CLI.
    """
    console.print(f"\n[cyan]Triggering OpenCode...[/cyan]")

    try:
        result = subprocess.run(
            ["opencode", "--file", pack_path],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            console.print("[green]OpenCode triggered successfully[/green]")
            console.print("OpenCode will execute the ExecutionPack.")
            console.print("After completion, run: asyncdev resume-next-day")
        else:
            console.print(f"[red]OpenCode failed: {result.stderr}[/red]")
            console.print("Manual trigger: Open the ExecutionPack.md in your editor")

    except FileNotFoundError:
        console.print("[yellow]OpenCode CLI not found[/yellow]")
        console.print("Manual trigger: Open the ExecutionPack.md in your editor")
    except subprocess.TimeoutExpired:
        console.print("[yellow]OpenCode trigger timed out[/yellow]")
        console.print("Check if OpenCode is running")


@app.command()
def mock_quick():
    """Quick mock execution for testing the full flow."""
    execute(mode="mock", execution_id="exec-test-001", trigger=False, dry_run=False)


@app.command()
def modes():
    """Show available execution modes and their status."""
    available = get_available_modes()

    console.print(Panel("Execution Modes", border_style="green"))

    for mode, is_avail in available.items():
        status = "[green]available[/green]" if is_avail else "[red]not available[/red]"
        console.print(f"  {mode}: {status}")

    console.print("\n[cyan]Usage:[/cyan]")
    console.print("  asyncdev run-day --mode external  (default)")
    console.print("  asyncdev run-day --mode live")
    console.print("  asyncdev run-day --mode mock")
    console.print("  asyncdev run-day --mode external --trigger")


if __name__ == "__main__":
    app()