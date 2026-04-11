"""backfill command - Archive historical features retroactively."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.archive_pack_builder import (
    build_backfill_archive_pack,
    check_backfill_eligibility,
    save_archive_pack,
)
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Backfill historical features into archive system")
console = Console()


@app.command()
def create(
    project: str = typer.Option(..., help="Project ID"),
    feature: str = typer.Option(..., help="Feature ID to backfill"),
    title: str = typer.Option(None, help="Feature title (extracted from spec if not provided)"),
    status: str = typer.Option("completed", help="Final status: completed/partial/abandoned"),
    outputs: str = typer.Option(None, help="Delivered outputs (comma-separated)"),
    decisions: str = typer.Option(None, help="Key decisions made (comma-separated)"),
    lessons: str = typer.Option(None, help="Lessons learned (comma-separated)"),
    patterns: str = typer.Option(None, help="Reusable patterns (comma-separated)"),
    artifacts: str = typer.Option(None, help="Artifact links (comma-separated)"),
    notes: str = typer.Option(None, help="Historical notes"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Create backfilled archive record for historical feature.

    Generates simplified ArchivePack for features completed before
    the formal archive system existed. Clearly marked as backfilled.

    Example:
        asyncdev backfill create --project my-app --feature 001-auth
        asyncdev backfill create --project demo --feature 002-core --lessons "Small tasks work better"
    """
    root = Path.cwd() if path == Path("projects") else path
    project_path = path / project

    console.print(Panel(f"Backfill Archive: {feature}", title="Historical Archive", border_style="yellow"))

    eligibility = check_backfill_eligibility(feature, project, path)

    if not eligibility.get("eligible"):
        console.print("[red]Feature not eligible for backfill[/red]")
        for reason in eligibility.get("reasons", []):
            console.print(f"  - {reason}")
        raise typer.Exit(1)

    if eligibility.get("warnings"):
        console.print("[yellow]Warnings:[/yellow]")
        for warning in eligibility["warnings"]:
            console.print(f"  - {warning}")

    spec_path = eligibility.get("spec_path")
    if spec_path:
        console.print(f"[dim]Feature spec found: {get_relative_path(Path(spec_path), root)}[/dim]")

    delivered_outputs = _parse_list(outputs)
    decisions_made = _parse_list(decisions)
    artifact_links = _parse_list(artifacts)

    archive_pack = build_backfill_archive_pack(
        feature_id=feature,
        product_id=project,
        title=title,
        final_status=status,
        delivered_outputs=delivered_outputs,
        decisions_made=decisions_made,
        lessons_input=lessons,
        patterns_input=patterns,
        artifact_links=artifact_links,
        historical_notes=notes,
        feature_spec_path=Path(spec_path) if spec_path else None,
    )

    table = Table(title="Backfill Archive Preview")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("feature_id", archive_pack["feature_id"])
    table.add_row("product_id", archive_pack["product_id"])
    table.add_row("title", archive_pack["title"])
    table.add_row("final_status", archive_pack["final_status"])
    table.add_row("archived_via_backfill", str(archive_pack["archived_via_backfill"]))
    table.add_row("delivered_outputs", str(len(archive_pack["delivered_outputs"])))
    table.add_row("lessons_learned", str(len(archive_pack["lessons_learned"])))
    table.add_row("reusable_patterns", str(len(archive_pack["reusable_patterns"])))

    console.print(table)

    if archive_pack.get("known_gaps"):
        console.print("\n[yellow]Known Gaps:[/yellow]")
        for gap in archive_pack["known_gaps"]:
            console.print(f"  - {gap}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    archive_dir = project_path / "archive" / feature
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_path = archive_dir / "archive-pack.yaml"
    save_archive_pack(archive_pack, archive_path)

    print_success_panel(
        message=f"Feature {feature} backfilled into archive",
        title="Backfill Complete",
        paths=[
            {"label": "ArchivePack", "path": str(archive_path)},
        ],
        root=root,
    )

    console.print("[dim]Backfilled records are marked with archived_via_backfill: true[/dim]")

    print_next_step(
        action="Continue backfilling other historical features",
        command="asyncdev backfill create --project <id> --feature <id>",
        artifact_path=archive_path,
        root=root,
    )


@app.command()
def check(
    project: str = typer.Option(..., help="Project ID"),
    feature: str = typer.Option(..., help="Feature ID to check"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Check if a feature is eligible for backfill."""
    eligibility = check_backfill_eligibility(feature, project, path)

    console.print(Panel(f"Backfill Eligibility: {feature}", border_style="blue"))

    table = Table(show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("feature_id", eligibility["feature_id"])
    table.add_row("product_id", eligibility["product_id"])
    table.add_row("eligible", "✅ YES" if eligibility["eligible"] else "❌ NO")

    console.print(table)

    if eligibility.get("reasons"):
        console.print("\n[bold]Reasons:[/bold]")
        for reason in eligibility["reasons"]:
            console.print(f"  - {reason}")

    if eligibility.get("warnings"):
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in eligibility["warnings"]:
            console.print(f"  - {warning}")

    if eligibility.get("has_spec"):
        console.print(f"\n[green]Feature spec available: {eligibility['spec_path']}[/green]")

    if eligibility["eligible"]:
        console.print("\n[cyan]Run 'asyncdev backfill create' to archive this feature[/cyan]")


@app.command()
def list(
    project: str = typer.Option(..., help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List features that may need backfill."""
    project_path = path / project
    features_path = project_path / "features"
    archive_path = project_path / "archive"

    console.print(Panel(f"Backfill Candidates: {project}", border_style="blue"))

    if not features_path.exists():
        console.print("[yellow]No features directory[/yellow]")
        return

    features = [f for f in features_path.iterdir() if f.is_dir()]

    if not features:
        console.print("[dim]No features found[/dim]")
        return

    table = Table(title="Features Status")
    table.add_column("Feature ID", style="cyan")
    table.add_column("Archived", style="green")
    table.add_column("Needs Backfill", style="yellow")
    table.add_column("Has Spec", style="dim")

    for feature_dir in sorted(features):
        feature_id = feature_dir.name
        archived = archive_path / feature_id / "archive-pack.yaml"
        has_spec = feature_dir / "feature-spec.yaml"

        archived_status = "✅ Yes" if archived.exists() else "❌ No"
        needs_backfill = "⚠️ Yes" if not archived.exists() else "✅ Done"
        spec_status = "✅" if has_spec.exists() else "❌"

        table.add_row(feature_id, archived_status, needs_backfill, spec_status)

    console.print(table)

    needs = [f for f in features if not (archive_path / f.name / "archive-pack.yaml").exists()]
    if needs:
        console.print(f"\n[yellow]{len(needs)} features need backfill[/yellow]")
        console.print("[cyan]Run 'asyncdev backfill create --feature <id>' to archive[/cyan]")
    else:
        console.print("\n[green]All features archived[/green]")


def _parse_list(input_str: str | None) -> list[str]:
    if not input_str:
        return []
    return [item.strip() for item in input_str.split(",") if item.strip()]


if __name__ == "__main__":
    app()