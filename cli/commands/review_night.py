"""review-night command - Generate nightly review pack."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.review_pack_builder import build_daily_review_pack

app = typer.Typer(help="Generate nightly review pack for human review")
console = Console()
store = StateStore()


@app.command()
def generate(
    execution_id: str = typer.Option(None, help="Execution ID to review"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
):
    """Generate DailyReviewPack from ExecutionResult and RunState."""
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    if execution_id is None:
        results = list(store.execution_results_path.glob("exec-*.md"))
        if not results:
            console.print("[red]No ExecutionResult found. Run 'asyncdev run-day' first.[/red]")
            raise typer.Exit(1)
        execution_id = results[-1].stem

    execution_result = store.load_execution_result(execution_id)

    if execution_result is None:
        console.print(f"[red]ExecutionResult not found: {execution_id}[/red]")
        raise typer.Exit(1)

    review_pack = build_daily_review_pack(execution_result, runstate)

    console.print(Panel(f"DailyReviewPack Preview", title="review-night", border_style="green"))

    table = Table(title="Review Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("date", review_pack["date"])
    table.add_row("project_id", review_pack["project_id"])
    table.add_row("feature_id", review_pack["feature_id"])
    table.add_row("today_goal", review_pack["today_goal"])
    table.add_row("completed", str(len(review_pack["what_was_completed"])))
    table.add_row("problems", str(len(review_pack["problems_found"])))
    table.add_row("blocked", str(len(review_pack["blocked_items"])))
    table.add_row("decisions", str(len(review_pack["decisions_needed"])))

    console.print(table)

    if review_pack["decisions_needed"]:
        console.print("\n[bold yellow]Decisions Needed:[/bold yellow]")
        for i, d in enumerate(review_pack["decisions_needed"], 1):
            console.print(f"  {i}. {d['decision']}")
            console.print(f"     Options: {d['options']}")
            console.print(f"     Recommendation: {d['recommendation']}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    store.save_daily_review_pack(review_pack)
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)

    console.print(f"\n[green]DailyReviewPack saved: reviews/{review_pack['date']}-review.md[/green]")
    console.print("\n[bold]Human Review Actions:[/bold]")
    console.print("  approve - Accept AI recommendation")
    console.print("  revise - Choose different option")
    console.print("  defer - Postpone decision, work on alternative")
    console.print("  redefine - Change question or scope")
    console.print("\nAfter review, run: asyncdev resume-next-day")


@app.command()
def show():
    """Show latest DailyReviewPack."""
    reviews = list(store.reviews_path.glob("*-review.md"))

    if not reviews:
        console.print("[yellow]No DailyReviewPack found[/yellow]")
        return

    latest = reviews[-1]
    review_pack = store.load_daily_review_pack(latest.stem.replace("-review", ""))

    if review_pack is None:
        console.print(f"[red]Could not load: {latest}[/red]")
        return

    console.print(Panel(f"DailyReviewPack: {review_pack['date']}", border_style="green"))

    console.print(f"\n[bold]Today's Goal:[/bold] {review_pack['today_goal']}")
    console.print(f"\n[bold]Completed:[/bold]")
    for item in review_pack["what_was_completed"]:
        console.print(f"  - {item}")

    if review_pack["decisions_needed"]:
        console.print(f"\n[bold yellow]Decisions Needed:[/bold yellow]")
        for d in review_pack["decisions_needed"]:
            console.print(f"  {d['decision']}: {d['options']}")
            console.print(f"    Recommended: {d['recommendation']}")

    console.print(f"\n[bold]Tomorrow's Plan:[/bold] {review_pack['tomorrow_plan']}")


if __name__ == "__main__":
    app()