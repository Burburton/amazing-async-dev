"""policy command - Execution policy configuration (Feature 020)."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.execution_policy import (
    PolicyMode,
    get_policy_mode,
    set_policy_mode,
    DEFAULT_POLICY_MODE,
)
from runtime.pause_reason import format_pause_reasons_table

app = typer.Typer(help="Execution policy configuration")
console = Console()


@app.command()
def show(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show current execution policy mode and rules.
    
    Example:
        asyncdev policy show
        asyncdev policy show --project my-app
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[yellow]No RunState found. Using default policy: conservative[/yellow]")
        current_mode = DEFAULT_POLICY_MODE
    else:
        current_mode = get_policy_mode(runstate)
    
    mode_table = Table(title="Policy Mode")
    mode_table.add_column("Setting", style="cyan")
    mode_table.add_column("Value", style="green")
    
    mode_table.add_row("Current Mode", current_mode.value)
    mode_table.add_row("Default Mode", DEFAULT_POLICY_MODE.value)
    mode_table.add_row("Scope Change Flag", str(runstate.get("scope_change_flag", False) if runstate else False))
    mode_table.add_row("Pending Risky Actions", str(len(runstate.get("pending_risky_actions", []) if runstate else [])))
    
    console.print(mode_table)
    
    rules_table = Table(title="Policy Rules")
    rules_table.add_column("Category", style="cyan")
    rules_table.add_column("Auto-Continue", style="green")
    rules_table.add_row("Execution success → Review", "✓" if current_mode != PolicyMode.CONSERVATIVE else "manual")
    rules_table.add_row("Review pack → Safe state", "✓" if current_mode in [PolicyMode.BALANCED, PolicyMode.LOW_INTERRUPTION] else "manual")
    rules_table.add_row("Non-destructive artifact", "✓" if current_mode in [PolicyMode.BALANCED, PolicyMode.LOW_INTERRUPTION] else "manual")
    rules_table.add_row("Risky actions", "always pause")
    rules_table.add_row("Blockers", "always pause")
    rules_table.add_row("Decisions needed", "pause" if current_mode != PolicyMode.LOW_INTERRUPTION else "may auto-resolve")
    rules_table.add_row("Scope change", "pause" if current_mode != PolicyMode.LOW_INTERRUPTION else "review")
    
    console.print(rules_table)


@app.command()
def set(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    mode: str = typer.Option(
        DEFAULT_POLICY_MODE.value,
        help="Policy mode: conservative, balanced, low_interruption"
    ),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
):
    """Set execution policy mode.
    
    Modes:
    - conservative: Ask for confirmation on most transitions
    - balanced: Auto-continue safe transitions, pause for decisions/risky
    - low_interruption: Minimize interruptions, only pause for blockers/risky
    
    Example:
        asyncdev policy set --mode balanced
        asyncdev policy set --project my-app --mode low_interruption
    """
    try:
        policy_mode = PolicyMode(mode)
    except ValueError:
        console.print(f"[red]Invalid mode: {mode}[/red]")
        console.print(f"Valid modes: {list(PolicyMode.__members__.keys())}")
        raise typer.Exit(1)
    
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[red]No RunState found. Create project first.[/red]")
        raise typer.Exit(1)
    
    old_mode = get_policy_mode(runstate)
    
    console.print(Panel(
        f"Policy Mode Change\nOld: {old_mode.value}\nNew: {policy_mode.value}",
        title="policy set",
        border_style="blue"
    ))
    
    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return
    
    runstate = set_policy_mode(runstate, policy_mode)
    store.save_runstate(runstate)
    
    console.print(f"[green]Policy mode set to: {policy_mode.value}[/green]")
    
    if policy_mode == PolicyMode.LOW_INTERRUPTION:
        console.print("[yellow]Warning: low_interruption mode will auto-continue more transitions[/yellow]")
        console.print("[yellow]Risky actions and blockers will still pause[/yellow]")
    elif policy_mode == PolicyMode.BALANCED:
        console.print("[cyan]Balanced mode: safe transitions auto-continue, decisions/risky actions pause[/cyan]")


@app.command()
def scope_flag(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    set_flag: bool = typer.Option(None, help="Set scope change flag (true/false)"),
    clear: bool = typer.Option(False, help="Clear scope change flag"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Manage scope change flag.
    
    Scope change flag indicates task scope has changed from original plan.
    When set, workflow will pause for review.
    
    Example:
        asyncdev policy scope-flag --set-flag true
        asyncdev policy scope-flag --clear
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)
    
    current_flag = runstate.get("scope_change_flag", False)
    
    if clear:
        runstate["scope_change_flag"] = False
        store.save_runstate(runstate)
        console.print("[green]Scope change flag cleared[/green]")
    elif set_flag is not None:
        runstate["scope_change_flag"] = set_flag
        store.save_runstate(runstate)
        console.print(f"[green]Scope change flag set to: {set_flag}[/green]")
        if set_flag:
            console.print("[yellow]Warning: Workflow will pause for scope change review[/yellow]")
    else:
        console.print(f"Current scope_change_flag: {current_flag}")


@app.command()
def risky_actions(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    list_actions: bool = typer.Option(False, help="List pending risky actions"),
    clear_all: bool = typer.Option(False, help="Clear all pending risky actions"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Manage pending risky actions.
    
    Risky actions require explicit confirmation before proceeding.
    
    Example:
        asyncdev policy risky-actions --list
        asyncdev policy risky-actions --clear-all
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)
    
    pending = runstate.get("pending_risky_actions", [])
    
    if clear_all:
        runstate["pending_risky_actions"] = []
        store.save_runstate(runstate)
        console.print(f"[green]Cleared {len(pending)} pending risky actions[/green]")
        return
    
    if list_actions or not pending:
        if not pending:
            console.print("[green]No pending risky actions[/green]")
            return
        
        table = Table(title="Pending Risky Actions")
        table.add_column("Action Type", style="cyan")
        table.add_column("Target", style="yellow")
        table.add_column("Requires Confirmation", style="magenta")
        
        for action in pending:
            table.add_row(
                action.get("action_type", "unknown"),
                action.get("target", "N/A") or "N/A",
                str(action.get("requires_confirmation", True)),
            )
        
        console.print(table)


@app.command()
def modes():
    """List available policy modes with descriptions."""
    
    table = Table(title="Available Policy Modes")
    table.add_column("Mode", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Auto-Continue", style="green")
    
    table.add_row(
        "conservative",
        "Ask for confirmation on most transitions",
        "execution_success only"
    )
    table.add_row(
        "balanced",
        "Auto-continue safe, pause for decisions/risky",
        "safe transitions"
    )
    table.add_row(
        "low_interruption",
        "Minimize interruptions, pause only blockers/risky",
        "most transitions"
    )
    
    console.print(table)
    
    console.print("\n[bold]Default mode: conservative[/bold]")
    console.print("\n[yellow]All modes still pause for:[/yellow]")
    console.print("  - Git push / remote mutations")
    console.print("  - Irreversible archive operations")
    console.print("  - Batch multi-feature operations")
    console.print("  - External API side effects")
    console.print("  - Promotion externalization")