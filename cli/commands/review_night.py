"""review-night command - Generate nightly review pack."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.review_pack_builder import build_daily_review_pack
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Generate nightly review pack for human review")
console = Console()


@app.command()
def generate(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    execution_id: str = typer.Option(None, help="Execution ID to review"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Generate DailyReviewPack from ExecutionResult and RunState."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path

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

    review_path = store.reviews_path / f"{review_pack['date']}-review.md"

    print_success_panel(
        message=f"DailyReviewPack generated: {review_pack['date']}",
        title="Review-Night Complete",
        paths=[
            {"label": "DailyReviewPack", "path": str(review_path)},
        ],
        root=root,
    )

    console.print("\n[bold]Human Review Actions:[/bold]")
    console.print("  approve - Accept AI recommendation")
    console.print("  revise - Choose different option")
    console.print("  defer - Postpone decision, work on alternative")
    console.print("  redefine - Change question or scope")

    print_next_step(
        action="Review the DailyReviewPack and make decisions",
        command="asyncdev resume-next-day continue-loop --decision <choice>",
        artifact_path=review_path,
        root=root,
        hints=["Use --decision approve/revise/defer/redefine"],
    )


@app.command()
def show(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show latest DailyReviewPack."""
    project_path = path / project
    store = StateStore(project_path)
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