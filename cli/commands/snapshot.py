"""Workspace snapshot CLI command (Feature 028)."""

from pathlib import Path

import typer
from rich.console import Console

from cli.utils.output_formatter import print_next_step
from runtime.workspace_snapshot import generate_workspace_snapshot, format_snapshot_markdown

app = typer.Typer(help="Workspace snapshot - comprehensive state view")
console = Console()


@app.command()
def show(
    project: str = typer.Option(None, "--project", "-p", help="Project ID to snapshot"),
    path: Path = typer.Option(Path("projects"), "--path", help="Projects root path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, yaml"),
):
    """Show workspace snapshot with initialization mode, execution state, and signals.
    
    The snapshot includes:
    - Initialization mode (direct or starter-pack)
    - Current product, feature, and phase
    - Verification and review signals
    - Pending decision count
    - Recommended next step
    """
    if project:
        project_path = path / project
    else:
        project_path = _find_active_project(path)
    
    if not project_path or not project_path.exists():
        console.print("[yellow]No active project found[/yellow]")
        console.print("[dim]Specify --project or ensure RunState exists[/dim]")
        print_next_step(
            action="Create a product first",
            command="asyncdev new-product create --product-id <id> --name '<name>'",
        )
        raise typer.Exit(1)
    
    snapshot = generate_workspace_snapshot(project_path)
    
    if format == "yaml":
        _print_yaml_snapshot(snapshot)
    else:
        _print_markdown_snapshot(snapshot)


def _find_active_project(path: Path) -> Path | None:
    """Find project with most recent runstate."""
    if not path.exists():
        return None
    
    projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    if not projects:
        return None
    
    for project_dir in sorted(projects, reverse=True):
        runstate_path = project_dir / "runstate.md"
        if runstate_path.exists():
            return project_dir
    
    return projects[0] if projects else None


def _print_markdown_snapshot(snapshot) -> None:
    """Print snapshot in markdown format."""
    output = format_snapshot_markdown(snapshot)
    
    mode_style = {
        "direct": "green",
        "starter-pack": "cyan",
        "unknown": "yellow",
    }
    
    console.print()
    console.print("[bold]Workspace Snapshot[/bold]\n")
    
    mode = snapshot.initialization_mode
    console.print(f"Initialization: [{mode_style.get(mode, 'white')}]{mode}[/{mode_style.get(mode, 'white')}]")
    
    if mode == "starter-pack" and snapshot.provider_linkage.get("detected"):
        console.print(f"  Provider Context: {snapshot.provider_linkage.get('product_type', 'unknown')}")
        if snapshot.provider_linkage.get("workflow_hints"):
            hints = snapshot.provider_linkage["workflow_hints"]
            console.print(f"  Policy Mode: {hints.get('policy_mode', 'unknown')}")
    
    console.print()
    console.print("[bold]Execution State[/bold]")
    console.print(f"  Product: {snapshot.product_id or '[dim]N/A[/dim]'}")
    console.print(f"  Feature: {snapshot.feature_id or '[dim]N/A[/dim]'}")
    
    phase_style = {
        "planning": "blue",
        "executing": "yellow",
        "reviewing": "cyan",
        "blocked": "red",
        "completed": "green",
    }
    phase = snapshot.current_phase
    console.print(f"  Phase: [{phase_style.get(phase, 'white')}]{phase}[/{phase_style.get(phase, 'white')}]")
    console.print(f"  Last Checkpoint: {snapshot.last_checkpoint or '[dim]N/A[/dim]'}")
    
    console.print()
    console.print("[bold]Signals[/bold]")
    
    verify_style = {"success": "green", "failed": "red", "not_run": "yellow"}
    console.print(f"  Verification: [{verify_style.get(snapshot.verification_status, 'white')}]{snapshot.verification_status}[/{verify_style.get(snapshot.verification_status, 'white')}]")
    if snapshot.verification_artifact:
        console.print(f"    Latest: [dim]{snapshot.verification_artifact}[/dim]")
    
    review_style = {"present": "green", "missing": "yellow"}
    console.print(f"  Review: [{review_style.get(snapshot.review_status, 'white')}]{snapshot.review_status}[/{review_style.get(snapshot.review_status, 'white')}]")
    if snapshot.review_artifact:
        console.print(f"    Latest: [dim]{snapshot.review_artifact}[/dim]")
    
    decision_color = "red" if snapshot.pending_decisions > 0 else "green"
    console.print(f"  Pending Decisions: [{decision_color}]{snapshot.pending_decisions}[/{decision_color}]")
    
    console.print()
    console.print("[bold]Recommended Next Step[/bold]")
    console.print(f"  {snapshot.recommended_next_step}")
    
    console.print()
    console.print(f"[dim]Workspace: {snapshot.workspace_path}[/dim]")
    
    if snapshot.product_id:
        print_next_step(
            action="View detailed status",
            command=f"asyncdev status --project {snapshot.product_id}",
        )


def _print_yaml_snapshot(snapshot) -> None:
    """Print snapshot in YAML format."""
    import yaml
    
    data = {
        "initialization_mode": snapshot.initialization_mode,
        "provider_linkage": snapshot.provider_linkage,
        "execution_state": {
            "product_id": snapshot.product_id,
            "product_name": snapshot.product_name,
            "feature_id": snapshot.feature_id,
            "current_phase": snapshot.current_phase,
            "last_checkpoint": snapshot.last_checkpoint,
        },
        "signals": {
            "verification": {
                "status": snapshot.verification_status,
                "artifact": snapshot.verification_artifact,
            },
            "review": {
                "status": snapshot.review_status,
                "artifact": snapshot.review_artifact,
            },
            "pending_decisions": snapshot.pending_decisions,
        },
        "recommended_next_step": snapshot.recommended_next_step,
        "workspace_path": snapshot.workspace_path,
    }
    
    console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))