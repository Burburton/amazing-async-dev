import typer
from rich.console import Console
from rich.panel import Panel
from datetime import datetime
from pathlib import Path

from runtime.project_link_loader import load_project_link, is_mode_b, get_product_repo_path
from runtime.artifact_router import route_new_feature

app = typer.Typer(help="Create new feature")
console = Console()


@app.command()
def create(
    product_id: str = typer.Option(..., help="Product to add feature to"),
    feature_id: str = typer.Option(..., help="Unique feature identifier"),
    name: str = typer.Option(..., help="Feature name"),
    goal: str = typer.Option("", help="Feature goal"),
    path: str = typer.Option("projects", help="Root directory for projects"),
):
    from pathlib import Path
    from runtime.adapters.filesystem_adapter import FilesystemAdapter
    from runtime.state_store import StateStore
    import yaml

    fs = FilesystemAdapter()
    root = Path(path)
    product_dir = root / product_id

    if not product_dir.exists():
        console.print(f"[red]Product not found: {product_dir}[/red]")
        console.print("Run 'asyncdev new-product' first")
        raise typer.Exit(1)

    console.print(Panel(f"Create Feature: {name}", border_style="green"))

    context = load_project_link(product_dir)
    
    if context and context.ownership_mode.value == "managed_external":
        spec_path, feature_dir = route_new_feature(product_dir, feature_id)
        console.print(f"[cyan]Mode B: Routing FeatureSpec to product repo[/cyan]")
    else:
        feature_dir = product_dir / "docs" / "features" / feature_id
        spec_path = feature_dir / "feature-spec.md"

    if feature_dir.exists():
        console.print(f"[red]Feature already exists: {feature_dir}[/red]")
        raise typer.Exit(1)

    fs.ensure_dir(feature_dir)
    console.print(f"[green]Created:[/green] {feature_dir}/")

    feature_spec = {
        "feature_id": feature_id,
        "product_id": product_id,
        "name": name,
        "goal": goal or f"{name} - goal to be defined",
        "scope": ["Core functionality", "Essential features"],
        "out_of_scope": ["Advanced features", "Future iterations"],
        "acceptance_criteria": [
            "Feature works correctly",
            "Tests pass",
            "Documentation complete",
        ],
        "constraints": ["Day-sized execution", "Single developer"],
        "estimated_tasks": 3,
        "created_at": datetime.now().isoformat(),
    }

    spec_file = spec_path
    if spec_file.suffix == ".md":
        spec_content = f"# FeatureSpec - {name}\n\n```yaml\n{yaml.dump(feature_spec, default_flow_style=False, sort_keys=False)}```\n"
        spec_file.write_text(spec_content, encoding="utf-8")
    else:
        with open(spec_file, "w", encoding="utf-8") as f:
            yaml.dump(feature_spec, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Created:[/green] {spec_file}")

    store = StateStore(product_dir)
    runstate = store.load_runstate() or {}

    runstate["feature_id"] = feature_id
    runstate["active_task"] = f"{feature_id}-task-001"
    runstate["current_phase"] = "planning"
    runstate["last_action"] = f"Feature created: {name}"
    runstate["next_recommended_action"] = f"Run 'asyncdev plan-day' to plan {name}"
    runstate["updated_at"] = datetime.now().isoformat()

    store.save_runstate(runstate)

    console.print(f"[green]Updated:[/green] {product_dir}/runstate.md")

    console.print("\n[green]Feature created successfully![/green]")
    console.print(f"RunState phase: planning")
    console.print(f"FeatureSpec: {spec_file}")
    console.print(f"Next: asyncdev plan-day to create ExecutionPack")


@app.command()
def list(
    product_id: str = typer.Option(..., help="Product to list features for"),
    path: str = typer.Option("projects", help="Root directory for projects"),
):
    """List all features for a product."""
    from pathlib import Path
    import yaml

    root = Path(path)
    product_dir = root / product_id
    
    features_dir = product_dir / "docs" / "features"
    
    if not features_dir.exists():
        features_dir = product_dir / "features"

    console.print(Panel(f"Features: {product_id}", border_style="blue"))

    if not features_dir.exists():
        console.print("[dim]No features yet[/dim]")
        return

    features = [f for f in features_dir.iterdir() if f.is_dir()]

    if not features:
        console.print("[dim]No features yet[/dim]")
        return

    for f in features:
        spec_path = f / "feature-spec.md"
        if not spec_path.exists():
            spec_path = f / "feature-spec.yaml"
        
        if spec_path.exists():
            content = spec_path.read_text(encoding="utf-8")
            
            yaml_start = content.find("```yaml")
            yaml_end = content.find("```", yaml_start + 7) if yaml_start != -1 else -1
            
            if yaml_start != -1 and yaml_end != -1:
                spec = yaml.safe_load(content[yaml_start + 7:yaml_end])
            else:
                spec = yaml.safe_load(content)
            
            console.print(f"[bold]{f.name}[/bold]: {spec.get('name', 'N/A')}")
            console.print(f"  Goal: {spec.get('goal', 'N/A')[:50]}...")
        else:
            console.print(f"[bold]{f.name}[/bold]: (no spec)")


if __name__ == "__main__":
    app()