"""Workspace Doctor CLI command (Feature 029)."""

import yaml
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.workspace_doctor import diagnose_workspace, format_diagnosis_markdown, format_diagnosis_yaml

app = typer.Typer(name="doctor", help="Diagnose workspace health and recommend next action")
console = Console()


def _resolve_project_path(project_id: Optional[str], projects_path: Path) -> Path:
    """Resolve project path from project ID or find active project."""
    if project_id:
        return projects_path / project_id
    
    if not projects_path.exists():
        return Path("nonexistent")
    
    project_dirs = sorted(
        projects_path.iterdir(),
        key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
        reverse=True
    )
    
    for project_dir in project_dirs:
        if project_dir.is_dir() and (project_dir / "runstate.md").exists():
            return project_dir
    
    return Path("nonexistent")


@app.command()
def show(
    project: str = typer.Option(None, "--project", "-p", help="Project ID to diagnose"),
    path: Path = typer.Option("projects", "--path", help="Projects root path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, yaml"),
):
    """Show workspace diagnosis with health classification and recommended next action.
    
    The diagnosis includes:
    - Overall health status (HEALTHY, ATTENTION_NEEDED, BLOCKED, etc.)
    - Current execution state
    - Signal summary (verification, decisions, blockers)
    - Recommended action with exact command
    - Rationale and warnings
    
    This command does NOT mutate workspace state.
    """
    project_path = _resolve_project_path(project, path)
    
    diagnosis = diagnose_workspace(project_path)
    
    if format == "yaml":
        output = format_diagnosis_yaml(diagnosis)
        console.print(output)
    else:
        output = format_diagnosis_markdown(diagnosis)
        console.print(output)
        
        if diagnosis.suggested_command:
            console.print(Panel(
                diagnosis.suggested_command,
                title="Suggested Command",
                border_style="green"
            ))


@app.command()
def fix(
    project: str = typer.Option(None, "--project", "-p", help="Project ID to fix"),
    path: Path = typer.Option("projects", "--path", help="Projects root path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be fixed without fixing"),
):
    """Attempt auto-remediation of common workspace issues.

    Fixes:
    - Invalid YAML in runstate.md (re-serialize to fix formatting)
    - Missing required directories (execution-packs, execution-results, etc.)
    - Invalid YAML in other project files

    This command will NOT fix:
    - Missing product-brief.yaml
    - Missing feature specs
    - Logic errors in execution flow
    """
    project_path = _resolve_project_path(project, path)

    if not project_path.exists():
        console.print(f"[red]Project not found: {project_path}[/red]")
        raise typer.Exit(1)

    fixes_applied = []
    fixes_skipped = []
    fixes_failed = []

    # 1. Fix runstate.yaml if invalid
    runstate_path = project_path / "runstate.md"
    if runstate_path.exists():
        try:
            content = runstate_path.read_text(encoding="utf-8")
            if "```yaml" in content:
                yaml_block = content.split("```yaml")[1].split("```")[0]
                data = yaml.safe_load(yaml_block)
                if dry_run:
                    fixes_skipped.append(f"runstate.yaml: would re-serialize YAML")
                else:
                    new_content = content
                    if "```yaml" in new_content:
                        lines = new_content.split("\n")
                        yaml_lines = []
                        in_yaml = False
                        for line in lines:
                            if line.strip() == "```yaml":
                                in_yaml = True
                                continue
                            elif in_yaml and line.strip() == "```":
                                in_yaml = False
                                continue
                            if in_yaml:
                                yaml_lines.append(line)
                        if yaml_lines:
                            new_yaml = yaml.dump(yaml.safe_load("\n".join(yaml_lines)), default_flow_style=False)
                            new_content = content.replace("```yaml\n" + "\n".join(yaml_lines) + "\n```", "```yaml\n" + new_yaml + "```")
                            if new_content != content:
                                runstate_path.write_text(new_content, encoding="utf-8")
                                fixes_applied.append("runstate.yaml: fixed YAML formatting")
        except yaml.YAMLError as e:
            fixes_failed.append(f"runstate.yaml: YAML error - {e}")
        except Exception as e:
            fixes_failed.append(f"runstate.yaml: error - {e}")

    # 2. Create missing required directories
    required_dirs = ["execution-packs", "execution-results", "reviews", "archive"]
    for dir_name in required_dirs:
        dir_path = project_path / dir_name
        if not dir_path.exists():
            if dry_run:
                fixes_skipped.append(f"{dir_name}/: would create directory")
            else:
                try:
                    dir_path.mkdir(exist_ok=True)
                    fixes_applied.append(f"{dir_name}/: created directory")
                except Exception as e:
                    fixes_failed.append(f"{dir_name}/: failed to create - {e}")

    # 3. Check other .yaml files for YAML errors
    for yaml_file in project_path.rglob("*.yaml"):
        if yaml_file.name == "product-brief.yaml":
            continue
        try:
            yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            fixes_failed.append(f"{yaml_file.name}: YAML error - {e}")
        except Exception as e:
            fixes_failed.append(f"{yaml_file.name}: error - {e}")

    # Report results
    console.print(Panel(
        f"Project: {project_path.name}\n"
        f"Mode: {'DRY RUN' if dry_run else 'LIVE'}",
        title="Doctor Fix Results",
        border_style="blue"
    ))

    if fixes_applied:
        table = Table(title="Fixes Applied", show_header=True)
        table.add_column("Action", style="green")
        for fix in fixes_applied:
            table.add_row(fix)
        console.print(table)

    if fixes_skipped:
        table = Table(title="Fixes Skipped (dry-run)", show_header=True)
        table.add_column("Action", style="yellow")
        for fix in fixes_skipped:
            table.add_row(fix)
        console.print(table)

    if fixes_failed:
        table = Table(title="Fixes Failed", show_header=True)
        table.add_column("Action", style="red")
        for fix in fixes_failed:
            table.add_row(fix)
        console.print(table)

    if not fixes_applied and not fixes_skipped and not fixes_failed:
        console.print("[green]No issues found - workspace is healthy[/green]")