"""New-product command - Create a new product with ProductBrief.

Feature 039: Added --ownership-mode and --repo-url for managed external products.
"""

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
    starter_pack: str = typer.Option("", help="Path to starter-pack.yaml from advisor"),
    ownership_mode: str = typer.Option(
        "self_hosted",
        help="Repository ownership mode: self_hosted (Mode A) or managed_external (Mode B)"
    ),
    repo_url: str = typer.Option("", help="Remote repository URL (for managed_external mode)"),
    repo_name: str = typer.Option("", help="Repository name (defaults to product_id)"),
    enable_email: bool = typer.Option(
        False,
        "--enable-email",
        help="Enable email decision channel for this product"
    ),
    email_sender: str = typer.Option(
        "",
        help="Email sender address (e.g., noreply@yourdomain.com)"
    ),
    email_inbox: str = typer.Option(
        "",
        help="Email inbox for decision replies (e.g., decisions@yourdomain.com)"
    ),
):
    """Create new product with ProductBrief.

    Creates:
    - projects/{product_id}/ directory
    - product-brief.yaml with provided info
    - runstate.md with initial planning phase
    - project-link.yaml (for managed_external mode)
    - Email channel config (if --enable-email)

    Examples:
        asyncdev new-product create --product-id my-app --name "My App"
        asyncdev new-product create --product-id demo-001 --name "Demo" --problem "Test"
        asyncdev new-product create --product-id ai-tool --name "AI Tool" --starter-pack starter-pack.yaml
        asyncdev new-product create --product-id visual-map --name "Visual Map" --ownership-mode managed_external --repo-url https://github.com/user/visual-map
        asyncdev new-product create --product-id my-app --name "My App" --enable-email --email-sender noreply@example.com
    """
    from pathlib import Path
    from runtime.adapters.filesystem_adapter import FilesystemAdapter
    from cli.starter_pack_consumer import consume_starter_pack, format_product_brief_with_starter_pack, format_runstate_with_starter_pack
    import yaml

    fs = FilesystemAdapter()
    root = Path(path)
    product_dir = root / product_id

    if ownership_mode not in ["self_hosted", "managed_external"]:
        console.print(f"[red]Invalid ownership_mode: {ownership_mode}[/red]")
        console.print("Valid options: self_hosted, managed_external")
        raise typer.Exit(1)

    if ownership_mode == "managed_external" and not repo_url:
        console.print("[yellow]managed_external mode requires --repo-url[/yellow]")
        console.print("Example: --repo-url https://github.com/user/product-repo")

    if product_dir.exists():
        console.print(f"[red]Product already exists: {product_dir}[/red]")
        console.print("Use different --product-id or delete existing")
        raise typer.Exit(1)

    console.print(Panel(f"Create Product: {name}", border_style="green"))

    if ownership_mode == "managed_external":
        console.print(f"[blue]Ownership mode:[/blue] managed_external (Mode B)")
        console.print(f"[blue]Product repo:[/blue] {repo_url}")
    else:
        console.print(f"[blue]Ownership mode:[/blue] self_hosted (Mode A)")

    consumption = None
    if starter_pack:
        console.print(f"[blue]Consuming starter pack:[/blue] {starter_pack}")
        consumption = consume_starter_pack(starter_pack)
        
        if not consumption.success:
            console.print(f"[red]Starter pack error:[/red] {consumption.error}")
            raise typer.Exit(1)
        
        if consumption.warnings:
            for warning in consumption.warnings:
                console.print(f"[yellow]Warning:[/yellow] {warning}")

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

    if consumption and consumption.success:
        product_brief = format_product_brief_with_starter_pack(product_brief, consumption)

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

    if consumption and consumption.success:
        runstate = format_runstate_with_starter_pack(runstate, consumption)

    runstate_path = product_dir / "runstate.md"
    yaml_content = yaml.dump(runstate, default_flow_style=False, sort_keys=False)
    markdown_content = f"# RunState\n\n```yaml\n{yaml_content}\n```\n"

    with open(runstate_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    console.print(f"[green]Created:[/green] {runstate_path}")

    # Create project-link.yaml
    project_link_data = {
        "product_id": product_id,
        "ownership_mode": ownership_mode,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    if ownership_mode == "managed_external":
        project_link_data["repo_name"] = repo_name or product_id
        project_link_data["repo_url"] = repo_url
    
    if enable_email:
        project_link_data["email_channel"] = {
            "enabled": True,
            "sender": email_sender or "noreply@async-dev.local",
            "decision_inbox": email_inbox or f"decisions-{product_id}@async-dev.local",
        }
        console.print(f"[blue]Email channel enabled:[/blue] {email_sender or 'noreply@async-dev.local'}")
    
    if ownership_mode == "managed_external" or enable_email:
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w", encoding="utf-8") as f:
            yaml.dump(project_link_data, f, default_flow_style=False, sort_keys=False)
        
        console.print(f"[green]Created:[/green] {link_path}")
        
        if ownership_mode == "managed_external":
            console.print("\n[blue]Governance note:[/blue]")
            console.print("[dim]Product truth should live in the product repo.[/dim]")
            console.print("[dim]Orchestration truth stays in async-dev.[/dim]")

    if consumption and consumption.success:
        console.print("\n[blue]Starter pack applied:[/blue]")
        if consumption.advisory_context.get("rationale"):
            console.print("[dim]Recommendation rationale available in product-brief[/dim]")
        if consumption.runstate_hints.get("policy_mode_hint"):
            console.print(f"[dim]Policy mode hint: {consumption.runstate_hints['policy_mode_hint']}[/dim]")

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