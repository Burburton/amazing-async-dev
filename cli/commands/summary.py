"""Summary command - management view for nightly review.

Feature 015: Daily Management Summary / Decision Inbox

Commands:
    asyncdev summary              - Show today's management summary
    asyncdev summary --decisions  - Focus on decision inbox
    asyncdev summary --issues     - Focus on issues summary
    asyncdev summary --next       - Focus on next day recommendation
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.review_pack_builder import build_daily_review_pack
from cli.utils.output_formatter import print_next_step
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Management summary for nightly review")
console = Console()


@app.command()
def today(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show today's management summary.

    Aggregates today's execution outcomes into a clear management view:
    - What was accomplished
    - What issues occurred (resolved vs unresolved)
    - What decisions are needed
    - What should tomorrow do

    Examples:
        asyncdev summary today
        asyncdev summary today --project demo-product
    """
    root = Path.cwd() if path == Path("projects") else path
    
    if not project:
        project = _find_active_project(path)
    
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    
    if runstate is None:
        console.print("[yellow]No active project found[/yellow]")
        console.print("[dim]Run 'asyncdev status --all' to see all projects[/dim]")
        raise typer.Exit(1)
    
    results = list(store.execution_results_path.glob("exec-*.md"))
    if not results:
        console.print("[yellow]No ExecutionResult found for today[/yellow]")
        console.print("[dim]Run 'asyncdev run-day' first[/dim]")
        raise typer.Exit(1)
    
    latest_result = results[-1]
    execution_id = latest_result.stem
    execution_result = store.load_execution_result(execution_id)
    
    if execution_result is None:
        console.print(f"[red]Could not load: {execution_id}[/red]")
        raise typer.Exit(1)
    
    review_pack = build_daily_review_pack(execution_result, runstate)
    
    _display_management_summary(review_pack, root)


@app.command()
def decisions(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show decision inbox.

    Focuses on decisions needing human judgment:
    - Decision questions
    - Options available
    - AI recommendations
    - Blocking status
    - Impact of deferring

    Examples:
        asyncdev summary decisions
        asyncdev summary decisions --project demo-product
    """
    root = Path.cwd() if path == Path("projects") else path
    
    if not project:
        project = _find_active_project(path)
    
    review_pack = _load_latest_review_pack(path, project)
    
    if review_pack is None:
        console.print("[yellow]No DailyReviewPack found[/yellow]")
        console.print("[dim]Run 'asyncdev review-night generate' first[/dim]")
        raise typer.Exit(1)
    
    _display_decision_inbox(review_pack, root)


@app.command()
def issues(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show issues summary.

    Focuses on issues encountered:
    - All issues encountered today
    - Issues resolved during execution
    - Issues still unresolved
    - Blocking vs non-blocking distinction

    Examples:
        asyncdev summary issues
        asyncdev summary issues --project demo-product
    """
    root = Path.cwd() if path == Path("projects") else path
    
    if not project:
        project = _find_active_project(path)
    
    review_pack = _load_latest_review_pack(path, project)
    
    if review_pack is None:
        console.print("[yellow]No DailyReviewPack found[/yellow]")
        raise typer.Exit(1)
    
    _display_issues_summary(review_pack, root)


@app.command()
def next_day(
    project: str = typer.Option(None, "--project", "-p", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show next day recommendation.

    Focuses on tomorrow's action:
    - Recommended next action
    - Preconditions required
    - Safe to execute status
    - Blocking decisions
    - Estimated scope

    Examples:
        asyncdev summary next-day
        asyncdev summary next-day --project demo-product
    """
    root = Path.cwd() if path == Path("projects") else path
    
    if not project:
        project = _find_active_project(path)
    
    review_pack = _load_latest_review_pack(path, project)
    
    if review_pack is None:
        console.print("[yellow]No DailyReviewPack found[/yellow]")
        raise typer.Exit(1)
    
    _display_next_day_recommendation(review_pack, root)


def _find_active_project(path: Path) -> str:
    """Find the most recently active project."""
    if not path.exists():
        return ""
    
    projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    
    if not projects:
        return ""
    
    for project_dir in sorted(projects, reverse=True):
        runstate_path = project_dir / "runstate.md"
        if runstate_path.exists():
            return project_dir.name
    
    return projects[0].name if projects else ""


def _load_latest_review_pack(path: Path, project: str) -> dict | None:
    """Load the latest DailyReviewPack for project."""
    project_path = path / project
    store = StateStore(project_path)
    
    reviews = list(store.reviews_path.glob("*-review.md"))
    if not reviews:
        return None
    
    latest = reviews[-1]
    return store.load_daily_review_pack(latest.stem.replace("-review", ""))


def _display_management_summary(review_pack: dict, root: Path) -> None:
    """Display full management summary."""
    console.print(Panel(
        f"[bold]{review_pack['date']}[/bold] | {review_pack['project_id']} | {review_pack['feature_id']}",
        title="Daily Management Summary",
        border_style="blue",
    ))
    
    console.print(f"\n[bold cyan]Today's Goal:[/bold cyan]")
    console.print(f"  {review_pack['today_goal']}")
    
    console.print(f"\n[bold green]Completed ({len(review_pack['what_was_completed'])}):[/bold green]")
    for item in review_pack['what_was_completed'][:5]:
        desc = item.get('description', item.get('item', str(item)))[:50]
        console.print(f"  - {desc}")
    
    issues_summary = review_pack.get('issues_summary', {})
    encountered = issues_summary.get('encountered', [])
    resolved = issues_summary.get('resolved', [])
    unresolved = issues_summary.get('unresolved', [])
    
    console.print(f"\n[bold yellow]Issues:[/bold yellow]")
    console.print(f"  Encountered: {len(encountered)}")
    console.print(f"  Resolved: {len(resolved)}")
    console.print(f"  Unresolved: {len(unresolved)}")
    
    decisions = review_pack.get('decisions_needed', [])
    template_count = sum(1 for d in decisions if d.get('is_template_based'))
    adhoc_count = len(decisions) - template_count
    
    console.print(f"\n[bold magenta]Decisions Needed: {len(decisions)}[/bold magenta]")
    if template_count > 0:
        console.print(f"  [dim]{template_count} template-based, {adhoc_count} ad hoc[/dim]")
    
    for d in decisions[:3]:
        decision_id = d.get('decision_id', '')
        template_id = d.get('template_id', '')
        decision_text = d.get('decision', '')[:40]
        
        label = f"[{decision_id}]"
        if template_id:
            label += f" [{template_id}]"
        
        console.print(f"  {label} {decision_text}")
        if d.get('blocking_tomorrow'):
            console.print(f"    [red]BLOCKING[/red]")
    
    next_rec = review_pack.get('next_day_recommendation', {})
    console.print(f"\n[bold blue]Tomorrow:[/bold blue]")
    console.print(f"  {next_rec.get('action', 'N/A')[:50]}")
    if next_rec.get('safe_to_execute'):
        console.print(f"  [green]Safe to execute[/green]")
    else:
        console.print(f"  [yellow]Requires: {', '.join(next_rec.get('preconditions', []))}[/yellow]")
    
    if review_pack.get('risk_watch_items'):
        console.print(f"\n[bold orange]Risk Watch:[/bold orange]")
        for risk in review_pack['risk_watch_items'][:2]:
            console.print(f"  - {risk.get('item', '')[:40]}")
    
    console.print(f"\n[dim]confidence: {review_pack.get('confidence_notes', 'N/A')}[/dim]")
    
    print_next_step(
        action="Review decisions in detail",
        command="asyncdev summary decisions",
    )


def _display_decision_inbox(review_pack: dict, root: Path) -> None:
    """Display decision inbox."""
    console.print(Panel("Decision Inbox", border_style="magenta"))
    
    decisions = review_pack.get('decisions_needed', [])
    
    if not decisions:
        console.print("[green]No decisions needed[/green]")
        console.print("[dim]All clear - proceed with tomorrow's plan[/dim]")
        return
    
    for i, d in enumerate(decisions, 1):
        decision_id = d.get('decision_id', '')
        template_id = d.get('template_id', '')
        is_template = d.get('is_template_based', False)
        
        console.print(f"\n[bold]Decision {i}: {decision_id}[/bold]")
        
        if template_id:
            console.print(f"  [magenta]Template:[/magenta] {template_id}")
        elif is_template:
            console.print(f"  [dim](ad hoc decision)[/dim]")
        
        console.print(f"  [cyan]Question:[/cyan] {d.get('decision', '')}")
        console.print(f"  [cyan]Type:[/cyan] {d.get('decision_type', 'technical')}")
        
        if d.get('template_name'):
            console.print(f"  [dim]Template: {d.get('template_name')}[/dim]")
        
        console.print(f"  [green]Options:[/green]")
        for opt in d.get('options', []):
            marker = "→" if opt == d.get('recommendation') else " "
            console.print(f"    {marker} {opt}")
        
        if d.get('recommendation'):
            console.print(f"  [green]Recommendation:[/green] {d.get('recommendation')}")
            if d.get('recommendation_reason'):
                console.print(f"    [dim]{d.get('recommendation_reason')}[/dim]")
        
        console.print(f"  [yellow]Impact:[/yellow] {d.get('impact', 'N/A')}")
        
        if d.get('blocking_tomorrow'):
            console.print(f"  [red]BLOCKING TOMORROW[/red]")
        
        if d.get('defer_impact'):
            console.print(f"  [dim]Defer impact: {d.get('defer_impact')}[/dim]")
    
    console.print(f"\n[bold]Human Actions:[/bold]")
    console.print("  approve  - Accept AI recommendation")
    console.print("  revise   - Choose different option")
    console.print("  defer    - Postpone, work on alternative")
    console.print("  redefine - Change question or scope")
    
    print_next_step(
        action="Process decisions",
        command="asyncdev resume-next-day continue-loop --decision <choice>",
    )


def _display_issues_summary(review_pack: dict, root: Path) -> None:
    """Display issues summary."""
    console.print(Panel("Issues Summary", border_style="yellow"))
    
    issues_summary = review_pack.get('issues_summary', {})
    
    encountered = issues_summary.get('encountered', [])
    if encountered:
        console.print(f"\n[bold]Encountered ({len(encountered)}):[/bold]")
        for issue in encountered[:5]:
            severity = issue.get('severity', 'medium')
            color = "red" if severity == "high" else "yellow" if severity == "medium" else "dim"
            console.print(f"  [{color}]({severity}) {issue.get('description', '')[:50]}[/{color}]")
    
    resolved = issues_summary.get('resolved', [])
    if resolved:
        console.print(f"\n[bold green]Resolved ({len(resolved)}):[/bold green]")
        for issue in resolved[:5]:
            console.print(f"  - {issue.get('description', '')[:40]}")
            console.print(f"    [dim]Resolution: {issue.get('resolution', '')[:30]}[/dim]")
    
    unresolved = issues_summary.get('unresolved', [])
    if unresolved:
        console.print(f"\n[bold red]Unresolved ({len(unresolved)}):[/bold red]")
        for issue in unresolved[:5]:
            blocking = issue.get('blocking', False)
            marker = "[BLOCKING]" if blocking else ""
            console.print(f"  - {issue.get('description', '')[:40]} {marker}")
            console.print(f"    [dim]Impact: {issue.get('estimated_impact', '')[:30]}[/dim]")
    
    if not encountered and not unresolved:
        console.print("[green]No issues encountered[/green]")
    
    console.print(f"\n[dim]Total: {len(encountered)} encountered, {len(resolved)} resolved, {len(unresolved)} pending[/dim]")


def _display_next_day_recommendation(review_pack: dict, root: Path) -> None:
    """Display next day recommendation."""
    console.print(Panel("Next Day Recommendation", border_style="blue"))
    
    next_rec = review_pack.get('next_day_recommendation', {})
    
    console.print(f"\n[bold cyan]Action:[/bold cyan]")
    console.print(f"  {next_rec.get('action', 'N/A')}")
    
    console.print(f"\n[bold]Scope:[/bold] {next_rec.get('estimated_scope', 'half-day')}")
    
    if next_rec.get('safe_to_execute'):
        console.print(f"\n[green]Safe to execute: YES[/green]")
        console.print("[dim]No blocking decisions or blockers[/dim]")
    else:
        console.print(f"\n[red]Safe to execute: NO[/red]")
        console.print("[yellow]Requires resolution before proceeding[/yellow]")
    
    preconditions = next_rec.get('preconditions', [])
    if preconditions:
        console.print(f"\n[bold yellow]Preconditions:[/bold yellow]")
        for pre in preconditions:
            console.print(f"  - {pre}")
    
    blocking = next_rec.get('blocking_decisions', [])
    if blocking:
        console.print(f"\n[bold red]Blocking Decisions:[/bold red]")
        for dec_id in blocking:
            console.print(f"  - {dec_id}")
    
    if next_rec.get('safe_to_execute'):
        print_next_step(
            action="Proceed with tomorrow's plan",
            command="asyncdev plan-day create",
        )
    else:
        print_next_step(
            action="Resolve blockers first",
            command="asyncdev summary decisions",
        )


if __name__ == "__main__":
    app()


@app.command("all-projects")
def all_projects(
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show summary across all projects.

    Feature 018: Limited Batch Operations

    Aggregates status across all projects for a portfolio view:
    - Project count and active features
    - Phase distribution across all projects
    - Blocked items count
    - Pending decisions count
    - Archive summary

    Examples:
        asyncdev summary all-projects
    """
    root = Path.cwd() if path == Path("projects") else path

    console.print(Panel("All Projects Summary", title="Feature 018", border_style="blue"))

    if not path.exists():
        console.print("[yellow]No projects directory[/yellow]")
        console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
        return

    projects = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]

    if not projects:
        console.print("[dim]No projects found[/dim]")
        console.print(f"[dim]root: {root}[/dim]")
        return

    table = Table(title="Projects Overview")
    table.add_column("Project", style="cyan")
    table.add_column("Phase", style="yellow")
    table.add_column("Features", style="green")
    table.add_column("Blocked", style="red")
    table.add_column("Decisions", style="magenta")
    table.add_column("Archived", style="dim")

    total_projects = 0
    total_blocked = 0
    total_decisions = 0
    total_archived = 0
    phase_counts = {}

    for project_dir in sorted(projects):
        runstate_path = project_dir / "runstate.md"

        if runstate_path.exists():
            store = StateStore(project_dir)
            runstate = store.load_runstate()

            if runstate:
                total_projects += 1
                phase = runstate.get("current_phase", "planning")
                blocked = len(runstate.get("blocked_items", []))
                decisions = len(runstate.get("decisions_needed", []))

                phase_counts[phase] = phase_counts.get(phase, 0) + 1
                total_blocked += blocked
                total_decisions += decisions

                phase_style = {
                    "planning": "blue",
                    "executing": "yellow",
                    "reviewing": "cyan",
                    "blocked": "red",
                    "completed": "green",
                    "archived": "dim",
                }
                style = phase_style.get(phase, "white")

                features_dir = project_dir / "features"
                features_count = len([f for f in features_dir.iterdir() if f.is_dir()]) if features_dir.exists() else 0

                archive_dir = project_dir / "archive"
                archived_count = len([f for f in archive_dir.iterdir() if f.is_dir()]) if archive_dir.exists() else 0
                total_archived += archived_count

                table.add_row(
                    project_dir.name,
                    f"[{style}]{phase}[/{style}]",
                    str(features_count),
                    str(blocked) if blocked > 0 else "0",
                    str(decisions) if decisions > 0 else "0",
                    str(archived_count),
                )

    console.print(table)

    console.print(f"\n[bold]Aggregated Metrics:[/bold]")
    console.print(f"  Projects tracked: {total_projects}")
    console.print(f"  Total blocked items: {total_blocked}")
    console.print(f"  Total pending decisions: {total_decisions}")
    console.print(f"  Total archived features: {total_archived}")

    if phase_counts:
        console.print(f"\n[bold]Phase Distribution:[/bold]")
        for phase, count in sorted(phase_counts.items()):
            console.print(f"  {phase}: {count}")

    if total_blocked > 0:
        console.print(f"\n[yellow]⚠️ {total_blocked} blocked items across projects[/yellow]")

    if total_decisions > 0:
        console.print(f"\n[magenta]📋 {total_decisions} decisions pending[/magenta]")

    console.print(f"\n[dim]root: {root}[/dim]")

    print_next_step(
        action="Inspect specific project",
        command="asyncdev status --project <id> --all-features",
    )