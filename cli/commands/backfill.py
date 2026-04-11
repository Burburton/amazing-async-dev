"""backfill command - Archive historical features retroactively.

Feature 013: Historical Archive Backfill
Feature 018: Limited Batch Operations (batch backfill)

Commands:
    asyncdev backfill create --project <id> --feature <id> - Single backfill
    asyncdev backfill batch --project <id> --all           - Batch backfill all eligible
    asyncdev backfill check --project <id> --feature <id>  - Check eligibility
    asyncdev backfill list --project <id>                  - List candidates
"""

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


@app.command()
def batch(
    project: str = typer.Option(..., "--project", "-p", help="Project ID"),
    all: bool = typer.Option(False, "--all", "-a", help="Backfill all eligible features"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without saving"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum features to backfill"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Batch backfill multiple eligible historical features.

    Feature 018: Limited Batch Operations

    Scans project for features needing backfill and processes them
    in one controlled batch operation. Requires --all flag for safety.

    Safety features:
    - Dry run mode shows what would be backfilled
    - Requires explicit --all flag
    - Shows summary before processing
    - Reports each backfill result

    Examples:
        asyncdev backfill batch --project demo --dry-run
        asyncdev backfill batch --project demo --all
        asyncdev backfill batch --project demo --all --limit 5
    """
    root = Path.cwd() if path == Path("projects") else path
    project_path = path / project

    if not all and not dry_run:
        console.print("[red]--all flag required for batch backfill[/red]")
        console.print("[yellow]Use --dry-run to preview first, or --all to proceed[/yellow]")
        raise typer.Exit(1)

    console.print(Panel(f"Batch Backfill: {project}", title="Feature 018", border_style="yellow"))

    features_path = project_path / "features"
    archive_path = project_path / "archive"

    if not features_path.exists():
        console.print("[yellow]No features directory[/yellow]")
        return

    feature_dirs = [f for f in features_path.iterdir() if f.is_dir()]
    eligible_features = []

    for feature_dir in feature_dirs:
        feature_id = feature_dir.name
        eligibility = check_backfill_eligibility(feature_id, project, path)

        if eligibility.get("eligible"):
            eligible_features.append({
                "feature_id": feature_id,
                "spec_path": eligibility.get("spec_path"),
                "has_spec": eligibility.get("has_spec", False),
            })

    if not eligible_features:
        console.print("[green]No features need backfill[/green]")
        console.print("[dim]All features already archived[/dim]")
        return

    if limit > 0:
        eligible_features = eligible_features[:limit]

    console.print(f"[bold]Found {len(eligible_features)} eligible features[/bold]\n")

    preview_table = Table(title="Batch Preview")
    preview_table.add_column("Feature ID", style="cyan")
    preview_table.add_column("Has Spec", style="green")
    preview_table.add_column("Spec Path", style="dim")

    for ef in eligible_features:
        spec_path_short = ""
        if ef.get("spec_path"):
            spec_path_short = get_relative_path(Path(ef["spec_path"]), root)[:40]
        preview_table.add_row(
            ef["feature_id"],
            "✅" if ef.get("has_spec") else "❌",
            spec_path_short,
        )

    console.print(preview_table)

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        console.print("[cyan]Run with --all to proceed[/cyan]")
        return

    console.print(f"\n[bold yellow]Processing {len(eligible_features)} features...[/bold yellow]")

    results_table = Table(title="Batch Results")
    results_table.add_column("Feature ID", style="cyan")
    results_table.add_column("Status", style="green")
    results_table.add_column("Archive Path", style="dim")

    success_count = 0
    failed_count = 0

    for ef in eligible_features:
        feature_id = ef["feature_id"]
        spec_path = Path(ef["spec_path"]) if ef.get("spec_path") else None

        try:
            archive_pack = build_backfill_archive_pack(
                feature_id=feature_id,
                product_id=project,
                title=None,
                final_status="completed",
                delivered_outputs=None,
                decisions_made=None,
                lessons_input=None,
                patterns_input=None,
                artifact_links=None,
                historical_notes=None,
                feature_spec_path=spec_path,
            )

            archive_dir = project_path / "archive" / feature_id
            archive_dir.mkdir(parents=True, exist_ok=True)

            archive_file_path = archive_dir / "archive-pack.yaml"
            save_archive_pack(archive_pack, archive_file_path)

            relative_archive = get_relative_path(archive_file_path, root)
            results_table.add_row(feature_id, "✅ Success", relative_archive[:40])
            success_count += 1

        except Exception as e:
            results_table.add_row(feature_id, f"❌ Failed: {str(e)[:30]}", "")
            failed_count += 1

    console.print(results_table)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]Success: {success_count}[/green]")
    console.print(f"  [red]Failed: {failed_count}[/red]")

    if success_count > 0:
        print_success_panel(
            message=f"Backfilled {success_count} features",
            title="Batch Backfill Complete",
            paths=[{"label": "Archive Directory", "path": str(project_path / "archive")}],
            root=root,
        )

    print_next_step(
        action="Review archived features",
        command="asyncdev archive list --product " + project,
    )


def _parse_list(input_str: str | None) -> list[str]:
    if not input_str:
        return []
    return [item.strip() for item in input_str.split(",") if item.strip()]


if __name__ == "__main__":
    app()