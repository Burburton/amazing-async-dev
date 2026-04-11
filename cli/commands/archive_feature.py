"""archive-feature command - Archive a completed feature."""

from datetime import datetime
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore
from runtime.archive_pack_builder import build_archive_pack
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Archive a completed feature with lessons and patterns")
console = Console()


@app.command()
def create(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID to archive"),
    status: str = typer.Option("completed", help="Final status: completed/partial/abandoned"),
    lessons: str = typer.Option(None, help="Lessons learned (comma-separated)"),
    patterns: str = typer.Option(None, help="Reusable patterns (comma-separated)"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Create ArchivePack for a completed feature.

    Generates archive artifact in dedicated archive directory:
    projects/{product_id}/archive/{feature_id}/archive-pack.yaml

    Example:
        asyncdev archive-feature create --project my-app --feature 001-auth
        asyncdev archive-feature create --project demo --feature 001-core --lessons "Small tasks work better"
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        raise typer.Exit(1)

    feature_id = feature or runstate.get("feature_id", "")
    if not feature_id:
        console.print("[red]No feature_id specified or found in RunState[/red]")
        raise typer.Exit(1)

    current_phase = runstate.get("current_phase", "planning")
    if current_phase != "completed":
        console.print(f"[yellow]Current phase: {current_phase}[/yellow]")
        console.print("Feature must be marked completed first.")
        console.print("Run 'asyncdev complete-feature mark' before archiving.")
        raise typer.Exit(1)

    console.print(Panel(f"Archive Feature: {feature_id}", title="archive-feature", border_style="green"))

    archive_pack = build_archive_pack(
        runstate=runstate,
        feature_id=feature_id,
        product_id=project,
        final_status=status,
        lessons_input=lessons,
        patterns_input=patterns,
    )

    table = Table(title="ArchivePack Preview")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("feature_id", archive_pack["feature_id"])
    table.add_row("product_id", archive_pack["product_id"])
    table.add_row("title", archive_pack["title"])
    table.add_row("final_status", archive_pack["final_status"])
    table.add_row("delivered_outputs", str(len(archive_pack["delivered_outputs"])))
    table.add_row("lessons_learned", str(len(archive_pack["lessons_learned"])))
    table.add_row("reusable_patterns", str(len(archive_pack["reusable_patterns"])))

    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        return

    archive_dir = project_path / "archive" / feature_id
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_path = archive_dir / "archive-pack.yaml"
    with open(archive_path, "w", encoding="utf-8") as f:
        yaml.dump(archive_pack, f, default_flow_style=False, sort_keys=False)

    runstate["current_phase"] = "archived"
    runstate["last_action"] = f"Feature archived: {feature_id}"
    runstate["next_recommended_action"] = "Feature archived. Start new feature or product."
    store.save_runstate(runstate)

    print_success_panel(
        message=f"Feature {feature_id} archived successfully",
        title="Archive Complete",
        paths=[
            {"label": "ArchivePack", "path": str(archive_path)},
        ],
        root=root,
    )

    console.print("[dim]Archived features are excluded from active execution selection.[/dim]")

    print_next_step(
        action="Start a new feature or product",
        command="asyncdev new-feature create",
        artifact_path=archive_path,
        root=root,
        hints=["Create a new feature for continued development"],
    )


@app.command()
def show(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option(None, help="Feature ID to show"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show archived feature details."""
    project_path = path / project

    if feature:
        archive_path = project_path / "archive" / feature / "archive-pack.yaml"
        if not archive_path.exists():
            console.print(f"[red]Archive not found: {feature}[/red]")
            raise typer.Exit(1)

        with open(archive_path, encoding="utf-8") as f:
            archive_pack = yaml.safe_load(f)

        console.print(Panel(f"Archive: {feature}", border_style="green"))

        console.print(f"[bold]Title:[/bold] {archive_pack.get('title', 'N/A')}")
        console.print(f"[bold]Status:[/bold] {archive_pack.get('final_status', 'N/A')}")
        console.print(f"[bold]Archived At:[/bold] {archive_pack.get('archived_at', 'N/A')}")

        console.print(f"\n[bold]Delivered Outputs ({len(archive_pack.get('delivered_outputs', []))}):[/bold]")
        for output in archive_pack.get("delivered_outputs", [])[:5]:
            console.print(f"  - {output.get('name', 'N/A')}")

        console.print(f"\n[bold]Lessons Learned ({len(archive_pack.get('lessons_learned', []))}):[/bold]")
        for lesson in archive_pack.get("lessons_learned", [])[:5]:
            console.print(f"  - {lesson.get('lesson', 'N/A')}")

        console.print(f"\n[bold]Reusable Patterns ({len(archive_pack.get('reusable_patterns', []))}):[/bold]")
        for pattern in archive_pack.get("reusable_patterns", [])[:5]:
            console.print(f"  - {pattern.get('pattern', 'N/A')}")

    else:
        archive_dir = project_path / "archive"
        if not archive_dir.exists():
            console.print("[yellow]No archived features[/yellow]")
            return

        features = [d for d in archive_dir.iterdir() if d.is_dir()]
        if not features:
            console.print("[yellow]No archived features[/yellow]")
            return

        console.print(Panel("Archived Features", border_style="blue"))

        for f in features:
            archive_path = f / "archive-pack.yaml"
            if archive_path.exists():
                with open(archive_path, encoding="utf-8") as fp:
                    pack = yaml.safe_load(fp)
                console.print(f"[bold]{f.name}[/bold]: {pack.get('title', 'N/A')}")
                console.print(f"  Status: {pack.get('final_status', 'N/A')}")
            else:
                console.print(f"[bold]{f.name}[/bold]: (no archive-pack)")


@app.command()
def list(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List all archived features for a product."""
    project_path = path / project
    archive_dir = project_path / "archive"

    console.print(Panel(f"Archived: {project}", border_style="blue"))

    if not archive_dir.exists():
        console.print("[dim]No archived features[/dim]")
        return

    features = [d for d in archive_dir.iterdir() if d.is_dir()]

    if not features:
        console.print("[dim]No archived features[/dim]")
        return

    table = Table(title="Archived Features")
    table.add_column("Feature ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Archived At", style="dim")

    for f in sorted(features):
        archive_path = f / "archive-pack.yaml"
        if archive_path.exists():
            with open(archive_path, encoding="utf-8") as fp:
                pack = yaml.safe_load(fp)
            table.add_row(
                f.name,
                pack.get("title", "N/A")[:30],
                pack.get("final_status", "N/A"),
                pack.get("archived_at", "N/A")[:10],
            )
        else:
            table.add_row(f.name, "(no pack)", "-", "-")

    console.print(table)


if __name__ == "__main__":
    app()