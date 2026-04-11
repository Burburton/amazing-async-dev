"""Init command - Initialize amazing-async-dev project structure."""

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Initialize project structure")
console = Console()


@app.command()
def create(
    path: str = typer.Option("projects", help="Root directory for projects"),
    force: bool = typer.Option(False, help="Overwrite existing structure"),
):
    """Initialize empty project structure.

    Creates:
    - projects/ root directory
    - No demo content (ready for new-product)

    Example:
        asyncdev init create
        asyncdev init create --path ./my-projects
    """
    from pathlib import Path
    from runtime.adapters.filesystem_adapter import FilesystemAdapter

    fs = FilesystemAdapter()
    root = Path(path)

    if root.exists() and not force:
        console.print(f"[yellow]Directory exists: {root}[/yellow]")
        console.print("Use --force to overwrite, or choose different --path")
        raise typer.Exit(1)

    console.print(Panel("Initialize Project Structure", border_style="green"))

    # Create root
    fs.ensure_dir(root)
    console.print(f"[green]Created:[/green] {root}/")

    # Create placeholder structure
    console.print("\n[cyan]Structure ready for:[/cyan]")
    console.print("  1. asyncdev new-product --product-id <id> --name <name>")
    console.print("  2. asyncdev new-feature --product-id <id> --feature-id <id>")

    console.print("\n[green]Initialization complete![/green]")
    console.print(f"Projects will be created under: {root}/{{product_id}}/")


@app.command()
def status():
    """Show current project structure status."""
    from pathlib import Path

    root = Path("projects")

    console.print(Panel("Project Structure Status", border_style="blue"))

    if not root.exists():
        console.print("[yellow]No projects directory found[/yellow]")
        console.print("Run 'asyncdev init create' to initialize")
        return

    # List existing projects
    projects = [p for p in root.iterdir() if p.is_dir()]
    console.print(f"[bold]Root:[/bold] {root}")
    console.print(f"[bold]Projects:[/bold] {len(projects)}")

    if projects:
        for p in projects[:5]:
            console.print(f"  - {p.name}")
    else:
        console.print("[dim]No projects yet[/dim]")
        console.print("Run 'asyncdev new-product' to create one")


if __name__ == "__main__":
    app()