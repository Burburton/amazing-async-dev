"""New-product command - Create a new product with ProductBrief."""

import typer
from rich.console import Console
from rich.panel import Panel
from datetime import datetime

app = typer.Typer(help="Create new product")
console = Console()


@app.command()
def create(
    product_id: str = typer.Option(..., help="Unique product identifier"),
    name: str = typer.Option(..., help="Product name"),
    problem: str = typer.Option("", help="Problem statement"),
    target_user: str = typer.Option("", help="Target user description"),
    path: str = typer.Option("projects", help="Root directory for projects"),
):
    """Create new product with ProductBrief.

    Creates:
    - projects/{product_id}/ directory
    - product-brief.yaml with provided info
    - runstate.md with initial planning phase

    Example:
        asyncdev new-product create --product-id my-app --name "My App"
        asyncdev new-product create --product-id demo-001 --name "Demo" --problem "Test"
    """
    from pathlib import Path
    from runtime.adapters.filesystem_adapter import FilesystemAdapter
    import yaml

    fs = FilesystemAdapter()
    root = Path(path)
    product_dir = root / product_id

    if product_dir.exists():
        console.print(f"[red]Product already exists: {product_dir}[/red]")
        console.print("Use different --product-id or delete existing")
        raise typer.Exit(1)

    console.print(Panel(f"Create Product: {name}", border_style="green"))

    # Create directories
    fs.ensure_dir(product_dir)
    fs.ensure_dir(product_dir / "execution-packs")
    fs.ensure_dir(product_dir / "execution-results")
    fs.ensure_dir(product_dir / "reviews")
    fs.ensure_dir(product_dir / "features")

    console.print(f"[green]Created:[/green] {product_dir}/")

    # Create product-brief.yaml
    product_brief = {
        "product_id": product_id,
        "name": name,
        "problem": problem or f"{name} - problem to be defined",
        "target_user": target_user or "Target user to be defined",
        "core_value": "Core value to be defined",
        "constraints": ["Single developer", "Day-sized loops"],
        "success_signal": "DailyReviewPack generated with valid evidence",
        "created_at": datetime.now().isoformat(),
    }

    brief_path = product_dir / "product-brief.yaml"
    with open(brief_path, "w", encoding="utf-8") as f:
        yaml.dump(product_brief, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Created:[/green] {brief_path}")

    # Create initial runstate
    runstate = {
        "product_id": product_id,
        "feature_id": "",
        "current_phase": "planning",
        "active_task": "",
        "task_queue": [],
        "completed_outputs": [],
        "open_questions": [],
        "blocked_items": [],
        "decisions_needed": [],
        "last_action": "Product created",
        "next_recommended_action": "Run 'asyncdev new-feature' to add feature",
        "updated_at": datetime.now().isoformat(),
    }

    runstate_path = product_dir / "runstate.md"
    yaml_content = yaml.dump(runstate, default_flow_style=False, sort_keys=False)
    markdown_content = f"# RunState\n\n```yaml\n{yaml_content}\n```\n"

    with open(runstate_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    console.print(f"[green]Created:[/green] {runstate_path}")

    console.print("\n[green]Product created successfully![/green]")
    console.print("Next: Run 'asyncdev new-feature' to add features")


@app.command()
def list(
    path: str = typer.Option("projects", help="Root directory for projects"),
):
    """List all products."""
    from pathlib import Path
    import yaml

    root = Path(path)

    console.print(Panel("Products", border_style="blue"))

    if not root.exists():
        console.print("[yellow]No projects directory[/yellow]")
        return

    products = [p for p in root.iterdir() if p.is_dir()]

    if not products:
        console.print("[dim]No products yet[/dim]")
        return

    for p in products:
        brief_path = p / "product-brief.yaml"
        if brief_path.exists():
            with open(brief_path, encoding="utf-8") as f:
                brief = yaml.safe_load(f)
            console.print(f"[bold]{p.name}[/bold]: {brief.get('name', 'N/A')}")
        else:
            console.print(f"[bold]{p.name}[/bold]: (no brief)")


if __name__ == "__main__":
    app()