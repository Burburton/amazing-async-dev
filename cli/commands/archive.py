"""Archive query command - list and inspect archived features.

Feature 014: Archive Query / History Inspection

Commands:
    asyncdev archive list          - List all archived features (global)
    asyncdev archive list --recent - Sort by most recent
    asyncdev archive list --product <id> - Filter by product
    asyncdev archive list --has-patterns - Only with reusable patterns
    asyncdev archive list --has-lessons - Only with lessons learned
    asyncdev archive show --feature <id> [--product <id>] - Show details
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.archive_query import (
    discover_all_archives,
    filter_archives,
    get_archive_detail,
    get_lessons_summary,
    get_patterns_summary,
)
from cli.utils.output_formatter import print_next_step, print_phase_indicator
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Query and inspect archived features")
console = Console()


@app.command()
def list(
    product: str = typer.Option(None, "--product", "-p", help="Filter by product ID"),
    recent: bool = typer.Option(False, "--recent", "-r", help="Sort by most recent"),
    has_patterns: bool = typer.Option(False, "--has-patterns", help="Only with reusable patterns"),
    has_lessons: bool = typer.Option(False, "--has-lessons", help="Only with lessons learned"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List archived features across all products or filtered.

    Default: List all archived features globally.
    Use filters to narrow results.

    Examples:
        asyncdev archive list
        asyncdev archive list --recent --limit 10
        asyncdev archive list --product demo-product
        asyncdev archive list --has-patterns
        asyncdev archive list --has-lessons --recent
    """
    root = Path.cwd() if path == Path("projects") else path
    
    archives = discover_all_archives(path)
    
    filtered = filter_archives(
        archives,
        product=product,
        recent=recent,
        has_patterns=has_patterns,
        has_lessons=has_lessons,
        limit=limit,
    )
    
    if not filtered:
        console.print("[dim]No archived features found[/dim]")
        if product:
            console.print(f"[dim]Product: {product}[/dim]")
        console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
        return
    
    title = "Archived Features"
    if product:
        title = f"Archived: {product}"
    if has_patterns:
        title += " (with patterns)"
    if has_lessons:
        title += " (with lessons)"
    
    console.print(Panel(title, border_style="blue"))
    
    table = Table(show_header=True)
    table.add_column("Feature ID", style="cyan", width=20)
    table.add_column("Product", style="dim", width=15)
    table.add_column("Title", style="green", width=30)
    table.add_column("Status", style="yellow", width=10)
    table.add_column("Archived", style="dim", width=10)
    table.add_column("Patterns", style="blue", width=8)
    table.add_column("Lessons", style="magenta", width=8)
    
    for archive in filtered:
        archived_at = archive.get("archived_at", "")
        if archived_at:
            archived_at = archived_at[:10]
        
        table.add_row(
            archive.get("feature_id", ""),
            archive.get("product_id", ""),
            archive.get("title", "")[:30],
            archive.get("final_status", ""),
            archived_at,
            str(archive.get("patterns_count", 0)),
            str(archive.get("lessons_count", 0)),
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(filtered)} archives[/dim]")
    console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
    
    if not product and not recent:
        print_next_step(
            action="Inspect specific archive",
            command="asyncdev archive show --feature <id>",
            hints=["Use --recent for most recent archives"],
        )


@app.command()
def show(
    feature: str = typer.Option(..., "--feature", "-f", help="Feature ID to inspect"),
    product: str = typer.Option(None, "--product", "-p", help="Product ID (optional)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed archive pack for a feature.

    Displays full archive details including:
    - Feature identity and status
    - Delivered outputs
    - Lessons learned
    - Reusable patterns
    - Decisions made
    - Artifact links

    Examples:
        asyncdev archive show --feature 001-auth
        asyncdev archive show --feature 001-auth --product my-app
    """
    root = Path.cwd() if path == Path("projects") else path
    
    detail = get_archive_detail(path, feature, product)
    
    if not detail:
        console.print(f"[red]Archive not found: {feature}[/red]")
        if product:
            console.print(f"[dim]Product: {product}[/dim]")
        console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
        raise typer.Exit(1)
    
    console.print(Panel(f"Archive: {feature}", border_style="green"))
    
    console.print(f"[bold]Title:[/bold] {detail.get('title', 'N/A')}")
    console.print(f"[bold]Product:[/bold] {detail.get('product_id', 'N/A')}")
    console.print(f"[bold]Status:[/bold] {detail.get('final_status', 'N/A')}")
    console.print(f"[bold]Archived At:[/bold] {detail.get('archived_at', 'N/A')[:19]}")
    
    if detail.get("backfilled"):
        console.print("[dim](Backfilled from historical record)[/dim]")
    
    delivered = detail.get("delivered_outputs", [])
    if delivered:
        console.print(f"\n[bold]Delivered Outputs ({len(delivered)}):[/bold]")
        for output in delivered[:10]:
            name = output.get("name", str(output))[:40]
            console.print(f"  - {name}")
    
    lessons = get_lessons_summary(detail)
    if lessons:
        console.print(f"\n[bold]Lessons Learned ({len(lessons)}):[/bold]")
        for lesson in lessons[:10]:
            lesson_text = lesson.get("lesson", str(lesson))[:50]
            context = lesson.get("context", "")
            console.print(f"  - {lesson_text}")
            if context:
                console.print(f"    [dim]{context[:40]}[/dim]")
    
    patterns = get_patterns_summary(detail)
    if patterns:
        console.print(f"\n[bold]Reusable Patterns ({len(patterns)}):[/bold]")
        for pattern in patterns[:10]:
            pattern_text = pattern.get("pattern", str(pattern))[:50]
            applicability = pattern.get("applicability", "")
            console.print(f"  - {pattern_text}")
            if applicability:
                console.print(f"    [dim]{applicability[:40]}[/dim]")
    
    decisions = detail.get("decisions_made", [])
    if decisions:
        console.print(f"\n[bold]Decisions Made ({len(decisions)}):[/bold]")
        for decision in decisions[:5]:
            decision_text = decision.get("decision", str(decision))[:40]
            console.print(f"  - {decision_text}")
    
    followups = detail.get("unresolved_followups", [])
    if followups:
        console.print(f"\n[yellow]Unresolved Follow-ups ({len(followups)}):[/yellow]")
        for followup in followups[:5]:
            item = followup.get("item", str(followup))[:40]
            console.print(f"  - {item}")
    
    archive_path = Path(detail.get("archive_path", ""))
    relative = get_relative_path(archive_path, root)
    console.print(f"\n[dim]Archive Pack: {relative}[/dim]")
    console.print(f"[dim]root: {root}[/dim]")
    
    print_next_step(
        action="Query related archives",
        command="asyncdev archive list --product " + detail.get("product_id", ""),
        hints=["Use --has-patterns to find similar patterns"],
    )


if __name__ == "__main__":
    app()