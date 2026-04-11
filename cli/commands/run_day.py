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
from runtime.execution_event_types import ExecutionEventType
from runtime.execution_logger import get_logger
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

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
    """Execute today's bounded task with selected engine."""
    logger = get_logger(store.project_path)
    
    runstate = store.load_runstate()
    feature_id = runstate.get("feature_id", "") if runstate else ""
    product_id = runstate.get("project_id", "") if runstate else ""

    logger.log_event(
        ExecutionEventType.RUN_DAY_STARTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "mode": mode},
    )
    
    available = get_available_modes()
    if not available.get(mode, False):
        console.print(f"[red]Mode '{mode}' is not available[/red]")
        console.print(f"Available modes: {list(available.keys())}")
        logger.close()
        raise typer.Exit(1)

    engine = get_engine(mode, project_path=store.project_path)
    console.print(Panel(
        f"Mode: {mode}\nEngine: {engine.get_mode_name()}",
        title="Run-Day",
        border_style="blue"
    ))

    if mode == "external":
        return _run_external_mode(execution_id, engine, trigger, dry_run, logger, feature_id, product_id)
    elif mode == "live":
        return _run_live_mode(execution_id, engine, dry_run, logger, feature_id, product_id)
    elif mode == "mock":
        return _run_mock_mode(execution_id, engine, dry_run, logger, feature_id, product_id)


def _run_external_mode(
    execution_id: str | None,
    engine,
    trigger: bool,
    dry_run: bool,
    logger,
    feature_id: str,
    product_id: str,
) -> None:
    """Execute in external tool mode."""
    root = Path.cwd()
    
    if execution_id is None:
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        if not packs:
            console.print("[red]No ExecutionPack found. Run 'asyncdev plan-day' first.[/red]")
            logger.close()
            raise typer.Exit(1)
        execution_id = packs[-1].stem

    execution_pack = store.load_execution_pack(execution_id)
    if execution_pack is None:
        console.print(f"[red]ExecutionPack not found: {execution_id}[/red]")
        logger.close()
        raise typer.Exit(1)

    engine.output_dir = store.execution_packs_path

    prep_result = engine.prepare(execution_pack)

    logger.log_event(
        ExecutionEventType.EXTERNAL_EXECUTION_TRIGGERED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "yaml_path": str(prep_result.get("yaml_path", ""))},
    )

    yaml_path = Path(prep_result.get("yaml_path", ""))
    md_path = Path(prep_result.get("md_path", ""))

    print_success_panel(
        message="ExecutionPack prepared for external execution",
        title="Run-Day Ready",
        paths=[
            {"label": "YAML Pack", "path": str(yaml_path)},
            {"label": "Markdown Pack", "path": str(md_path)},
        ],
        root=root,
    )

    console.print(f"\n[cyan]{prep_result['instructions']}[/cyan]")

    if trigger:
        _trigger_external_tool(prep_result['md_path'])
        logger.log_event(
            ExecutionEventType.RUN_DAY_DISPATCHED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"execution_id": execution_id, "triggered": True},
        )

    if dry_run:
        console.print("[yellow]Dry run - external mode does not modify state[/yellow]")
        logger.close()
        return

    print_next_step(
        action="Execute the ExecutionPack with external tool",
        command="asyncdev resume-next-day",
        artifact_path=md_path,
        root=root,
        hints=["After execution, run resume-next-day to continue"],
    )


def _run_live_mode(
    execution_id: str | None,
    engine,
    dry_run: bool,
    logger,
    feature_id: str,
    product_id: str,
) -> None:
    """Execute in live API mode."""
    root = Path.cwd()
    
    runstate = store.load_runstate()
    if runstate is None:
        console.print("[red]No RunState found. Run 'asyncdev plan-day' first.[/red]")
        logger.close()
        raise typer.Exit(1)

    if execution_id is None:
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        if not packs:
            console.print("[red]No ExecutionPack found. Run 'asyncdev plan-day' first.[/red]")
            logger.close()
            raise typer.Exit(1)
        execution_id = packs[-1].stem

    execution_pack = store.load_execution_pack(execution_id)
    if execution_pack is None:
        console.print(f"[red]ExecutionPack not found: {execution_id}[/red]")
        logger.close()
        raise typer.Exit(1)

    prep = engine.prepare(execution_pack)
    if prep.get("status") != "ready":
        console.print(f"[red]ExecutionPack invalid: missing {prep.get('missing_fields', [])}[/red]")
        logger.close()
        raise typer.Exit(1)

    console.print(f"\n[cyan]Executing via API (model: {prep.get('model', 'unknown')})...[/cyan]")

    result = engine.run(execution_pack)

    logger.log_event(
        ExecutionEventType.EXECUTION_RESULT_COLLECTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "status": result.get("status", "unknown")},
    )

    console.print("\n[green]ExecutionResult:[/green]")
    console.print(f"  Status: {result['status']}")
    console.print(f"  Completed: {result['completed_items']}")
    console.print(f"  Artifacts: {len(result['artifacts_created'])}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    store.save_execution_result(result)
    previous_phase = runstate.get("current_phase", "executing")
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)

    logger.log_transition(
        from_phase=previous_phase,
        to_phase="reviewing",
        feature_id=feature_id,
        product_id=product_id,
        reason="Live execution completed",
    )
    logger.log_event(
        ExecutionEventType.NORMAL_STOP,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"phase": "reviewing"},
    )
    engine.close()
    logger.close()

    result_path = store.execution_results_path / f"{execution_id}.md"

    print_success_panel(
        message=f"Live execution completed: {result['status']}",
        title="Run-Day Complete",
        paths=[
            {"label": "ExecutionResult", "path": str(result_path)},
            {"label": "RunState", "path": str(store.project_path / "runstate.md")},
        ],
        root=root,
    )

    print_next_step(
        action="Generate DailyReviewPack for human review",
        command="asyncdev review-night generate",
        artifact_path=result_path,
        root=root,
    )


def _run_mock_mode(
    execution_id: str | None,
    engine,
    dry_run: bool,
    logger,
    feature_id: str,
    product_id: str,
) -> None:
    """Execute in mock mode for testing."""
    root = Path.cwd()
    
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
        feature_id = "001-test"
        product_id = "demo-product-001"

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

    logger.log_event(
        ExecutionEventType.EXECUTION_RESULT_COLLECTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "status": result.get("status", "mock"), "mode": "mock"},
    )

    console.print("\n[green]Mock ExecutionResult:[/green]")
    console.print(f"  Status: {result['status']}")
    console.print(f"  Completed: {result['completed_items']}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    store.save_execution_result(result)
    previous_phase = runstate.get("current_phase", "executing")
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)

    logger.log_transition(
        from_phase=previous_phase,
        to_phase="reviewing",
        feature_id=feature_id,
        product_id=product_id,
        reason="Mock execution completed",
    )
    logger.log_event(
        ExecutionEventType.NORMAL_STOP,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"phase": "reviewing", "mode": "mock"},
    )
    logger.close()

    result_path = store.execution_results_path / f"{execution_id}.md"

    print_success_panel(
        message=f"Mock execution completed: {result['status']}",
        title="Run-Day Mock Complete",
        paths=[
            {"label": "ExecutionResult", "path": str(result_path)},
        ],
        root=root,
    )

    print_next_step(
        action="Generate DailyReviewPack for review",
        command="asyncdev review-night generate",
    )


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