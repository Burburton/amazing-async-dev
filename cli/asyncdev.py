"""Amazing Async Dev - Personal Async AI Development OS CLI."""

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from cli.commands import plan_day, run_day, review_night, resume_next_day
from cli.commands import init, new_product, new_feature
from cli.commands import complete_feature, archive_feature
from cli.commands import sqlite_status, inspect_stop, recovery, decision, session_start, verification, observer, acceptance
from cli.commands import backfill, archive, summary, feedback, policy, email_decision, snapshot, doctor, journal, gmail_auth, resend_auth, check_inbox, config, project_link, browser_test, frontend_verify_run
from cli.utils.output_formatter import print_next_step, print_phase_indicator
from cli.utils.path_formatter import get_relative_path

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

# Register historical backfill command
app.add_typer(backfill.app, name="backfill", help="Backfill historical features into archive")

app.add_typer(archive.app, name="archive", help="Query and inspect archived features")

app.add_typer(summary.app, name="summary", help="Management summary for nightly review")

app.add_typer(feedback.app, name="feedback", help="Record and inspect workflow feedback")

app.add_typer(policy.app, name="policy", help="Execution policy configuration (Feature 020)")

app.add_typer(email_decision.app, name="email-decision", help="Async decision channel (Feature 021)")

app.add_typer(snapshot.app, name="snapshot", help="Workspace snapshot - comprehensive state view (Feature 028)")

app.add_typer(doctor.app, name="doctor", help="Diagnose workspace health and recommend next action (Feature 029)")

app.add_typer(journal.app, name="journal", help="View async-dev loop artifact timeline (Feature 036 dogfooding)")
 
app.add_typer(gmail_auth.app, name="gmail-auth", help="Gmail OAuth2 authentication setup")

app.add_typer(resend_auth.app, name="resend-auth", help="Resend email provider setup")

app.add_typer(check_inbox.app, name="check-inbox", help="Check pending decisions from webhook")

app.add_typer(config.app, name="config", help="Config safety commands (Feature 057)")

app.add_typer(project_link.app, name="project-link", help="Project-link management (Feature 055)")

app.add_typer(browser_test.app, name="browser-test", help="Browser verification for frontend projects (Feature 056)")

app.add_typer(frontend_verify_run.app, name="frontend-verify-run", help="Controlled frontend verification recipe (Feature 062)")

app.add_typer(sqlite_status.app, name="sqlite", help="SQLite state store queries")

# Register recovery commands
app.add_typer(inspect_stop.app, name="inspect-stop", help="Inspect stop point and recovery options")
app.add_typer(recovery.app, name="recovery", help="Execution Recovery Console (operator surface)")
app.add_typer(decision.app, name="decision", help="Decision Inbox (operator surface - Phase 3)")
app.add_typer(session_start.app, name="session-start", help="Mandatory blocking state check (Feature 065)")
app.add_typer(verification.app, name="verification", help="Verification Console (operator surface - Priority 2)")
app.add_typer(observer.app, name="observe-runs", help="Execution Observer Foundation (Feature 067)")

app.add_typer(acceptance.app, name="acceptance", help="Acceptance Console - Operator surface for acceptance validation (Feature 077)")


@app.command()
def status(
    all: bool = typer.Option(False, "--all", help="Show all products and features"),
    all_features: bool = typer.Option(False, "--all-features", help="Show all features in a project"),
    feature: str = typer.Option(None, "--feature", help="Show specific feature details"),
    project: str = typer.Option(None, "--project", help="Project ID (required for --feature or --all-features)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show current RunState status.
    
    Levels:
    - Default: Current RunState
    - --all: All products and features summary
    - --project <id> --all-features: All features in a specific project
    - --feature <id>: Specific feature details
    """
    root = Path.cwd() if path == Path("projects") else path
    
    if all:
        _show_all_status(path, root)
    elif all_features:
        _show_all_features_status(project, path, root)
    elif feature:
        _show_feature_status(feature, project, path, root)
    else:
        _show_current_status(path, root)


def _show_all_features_status(project: str | None, path: Path, root: Path) -> None:
    """Show all features in a specific project."""
    if not project:
        console.print("[red]--project required when using --all-features[/red]")
        console.print("[yellow]Example: asyncdev status --all-features --project my-app[/yellow]")
        raise typer.Exit(1)
    
    project_path = path / project
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold cyan]All Features in: {project}[/bold cyan]\n")
    
    from runtime.state_store import StateStore
    from runtime.sqlite_state_store import SQLiteStateStore
    
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    sqlite_store = SQLiteStateStore(project_path)
    features = sqlite_store.list_features(project)
    
    features_dir = project_path / "features"
    archive_dir = project_path / "archive"
    
    phase_style = {
        "planning": "blue",
        "executing": "yellow",
        "reviewing": "cyan",
        "blocked": "red",
        "completed": "green",
        "archived": "dim",
    }
    
    if features:
        table = Table(title="Features (SQLite)")
        table.add_column("Feature ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Phase", style="yellow")
        table.add_column("Active Task", style="dim")
    else:
        table = Table(title="Features (File-based)")
        table.add_column("Feature ID", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("In RunState", style="green")
        table.add_column("Archived", style="dim")
    
    if features:
        for f in features:
            feature_id = f.get("feature_id", "")
            name = f.get("name", feature_id)
            phase = f.get("phase", "unknown")
            active_task = f.get("active_task", "")[:30] if f.get("active_task") else ""
            
            style = phase_style.get(phase, "white")
            
            table.add_row(
                feature_id,
                name[:30],
                f"[{style}]{phase}[/{style}]",
                active_task,
            )
    elif features_dir.exists():
        feature_dirs = [f for f in features_dir.iterdir() if f.is_dir()]
        
        for feature_dir in sorted(feature_dirs):
            feature_id = feature_dir.name
            
            in_runstate = "Y" if runstate and runstate.get("feature_id") == feature_id else "N"
            archived = "Y" if archive_dir.exists() and (archive_dir / feature_id).exists() else "N"
            
            status_text = "archived" if archived == "Y" else ("active" if in_runstate == "Y" else "defined")
            style = phase_style.get(status_text, "white")
            
            table.add_row(feature_id, f"[{style}]{status_text}[/{style}]", in_runstate, archived)
    
    console.print(table)
    
    phase_summary = {"planning": 0, "executing": 0, "reviewing": 0, "blocked": 0, "completed": 0, "archived": 0}
    if features:
        for f in features:
            phase = f.get("phase", "unknown")
            if phase in phase_summary:
                phase_summary[phase] += 1
    elif features_dir.exists():
        for feature_dir in features_dir.iterdir():
            if archive_dir.exists() and (archive_dir / feature_dir.name).exists():
                phase_summary["archived"] += 1
            elif runstate and runstate.get("feature_id") == feature_dir.name:
                phase = runstate.get("current_phase", "planning")
                if phase in phase_summary:
                    phase_summary[phase] += 1
            else:
                phase_summary["defined"] = phase_summary.get("defined", 0) + 1
    
    console.print(f"\n[bold]Phase Distribution:[/bold]")
    for phase, count in phase_summary.items():
        if count > 0:
            console.print(f"  {phase}: {count}")
    
    sqlite_store.close()
    
    console.print(f"\n[dim]Project: {project}[/dim]")
    console.print(f"[dim]root: {root}[/dim]")
    
    print_next_step(
        action="Inspect specific feature",
        command="asyncdev status --feature <id> --project " + project,
    )


def _show_current_status(path: Path, root: Path) -> None:
    from runtime.state_store import StateStore
    
    store = StateStore(path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[yellow]No active RunState found[/yellow]")
        print_next_step(
            action="Initialize a project or load existing RunState",
            command="asyncdev init create",
            hints=["Run asyncdev new-product to create a product"],
        )
        return
    
    phase = runstate.get("current_phase", "planning")
    print_phase_indicator(phase)
    
    table = Table(title="Current RunState", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Project", runstate.get("project_id", "N/A"))
    table.add_row("Feature", runstate.get("feature_id", "N/A"))
    table.add_row("Phase", phase)
    table.add_row("Active Task", runstate.get("active_task", "N/A") or "[dim]none[/dim]")
    table.add_row("Queue", f"{len(runstate.get('task_queue', []))} pending")
    table.add_row("Completed", f"{len(runstate.get('completed_outputs', []))} outputs")
    table.add_row("Blocked", f"{len(runstate.get('blocked_items', []))} items")
    table.add_row("Decisions", f"{len(runstate.get('decisions_needed', []))} pending")
    
    console.print(table)
    
    if store.project_path:
        runstate_path = store.project_path / "runstate.md"
        relative = get_relative_path(runstate_path, root)
        console.print(f"\n[dim]RunState file: {relative}[/dim]")
        console.print(f"[dim]root: {root}[/dim]")
    
    next_action = runstate.get("next_recommended_action", "")
    if next_action:
        console.print()
        print_next_step(
            action=next_action,
            command="asyncdev plan-day",
        )


def _show_all_status(path: Path, root: Path) -> None:
    console.print("[bold]All Products and Features[/bold]\n")
    
    if not path.exists():
        console.print("[yellow]No projects directory[/yellow]")
        console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
        return
    
    products = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    if not products:
        console.print("[dim]No products yet[/dim]")
        console.print(f"[dim]root: {root}[/dim]")
        return
    
    for product_dir in sorted(products):
        brief_path = product_dir / "product-brief.yaml"
        runstate_path = product_dir / "runstate.md"
        
        product_name = product_dir.name
        if brief_path.exists():
            with open(brief_path, encoding="utf-8") as f:
                brief = yaml.safe_load(f)
            product_name = brief.get("name", product_dir.name)
        
        console.print(f"\n[bold cyan]{product_dir.name}[/bold cyan]: {product_name}")
        
        if runstate_path.exists():
            from runtime.state_store import StateStore
            store = StateStore(product_dir)
            runstate = store.load_runstate()
            
            if runstate:
                phase = runstate.get("current_phase", "N/A")
                feature_id = runstate.get("feature_id", "")
                
                phase_style = {
                    "planning": "blue",
                    "executing": "yellow",
                    "reviewing": "cyan",
                    "blocked": "red",
                    "completed": "green",
                    "archived": "dim",
                }
                style = phase_style.get(phase, "white")
                
                console.print(f"  [{style}]Phase: {phase}[/{style}]")
                console.print(f"  Feature: {feature_id or '[dim]none[/dim]'}")
                console.print(f"  Blocked: {len(runstate.get('blocked_items', []))}")
                console.print(f"  Decisions: {len(runstate.get('decisions_needed', []))}")
        else:
            console.print("  [dim]No RunState[/dim]")
        
        features_dir = product_dir / "features"
        if features_dir.exists():
            features = [f for f in features_dir.iterdir() if f.is_dir()]
            if features:
                console.print(f"  Features: {len(features)} defined")
        
        archive_dir = product_dir / "archive"
        if archive_dir.exists():
            archived = [f for f in archive_dir.iterdir() if f.is_dir()]
            if archived:
                console.print(f"  Archived: {len(archived)}")
    
    console.print(f"\n[dim]root: {root}[/dim]")


def _show_feature_status(feature_id: str, project: str | None, path: Path, root: Path) -> None:
    if not project:
        console.print("[red]--project required when using --feature[/red]")
        console.print("[yellow]Example: asyncdev status --feature 001-auth --project my-app[/yellow]")
        raise typer.Exit(1)
    
    project_path = path / project
    
    if not project_path.exists():
        console.print(f"[red]Project not found: {project}[/red]")
        raise typer.Exit(1)
    
    from runtime.state_store import StateStore
    from runtime.sqlite_state_store import SQLiteStateStore
    
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    console.print(f"[bold]Feature: {feature_id}[/bold] (project: {project})\n")
    
    table = Table(title="Feature Status")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    if runstate and runstate.get("feature_id") == feature_id:
        phase = runstate.get("current_phase", "N/A")
        print_phase_indicator(phase)
        
        table.add_row("Phase", phase)
        table.add_row("Active Task", runstate.get("active_task", "N/A"))
        table.add_row("Queue", f"{len(runstate.get('task_queue', []))} pending")
        table.add_row("Completed Outputs", f"{len(runstate.get('completed_outputs', []))}")
        table.add_row("Blocked Items", str(len(runstate.get('blocked_items', []))))
        table.add_row("Pending Decisions", str(len(runstate.get('decisions_needed', []))))
        table.add_row("Last Action", runstate.get("last_action", "N/A")[:40])
        table.add_row("Updated", runstate.get("updated_at", "N/A")[:19])
    else:
        table.add_row("Phase", "[dim]Not active[/dim]")
        table.add_row("Status", "Feature exists but not in current RunState")
    
    console.print(table)
    
    sqlite_store = SQLiteStateStore(project_path)
    events = sqlite_store.get_recent_events(feature_id, limit=10)
    
    if events:
        console.print("\n[bold]Recent Events:[/bold]")
        events_table = Table()
        events_table.add_column("Event", style="cyan")
        events_table.add_column("Time", style="dim")
        
        for e in events[:5]:
            event_type = e.get("event_type", "unknown")
            event_time = e.get("occurred_at", "N/A")
            events_table.add_row(event_type, event_time[:19] if len(event_time) > 19 else event_time)
        
        console.print(events_table)
    
    sqlite_store.close()
    
    runstate_path = project_path / "runstate.md"
    relative = get_relative_path(runstate_path, root)
    console.print(f"\n[dim]RunState: {relative}[/dim]")
    console.print(f"[dim]root: {root}[/dim]")
    
    if runstate and runstate.get("feature_id") == feature_id:
        print_next_step(
            action=runstate.get("next_recommended_action", "Continue execution"),
            command="asyncdev plan-day",
        )


@app.command()
def version():
    """Show version."""
    console.print("[bold]amazing-async-dev[/bold] v0.1.0")


if __name__ == "__main__":
    app()