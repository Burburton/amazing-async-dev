"""Config CLI commands - safety checks and shell configuration."""

import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.gitignore_manager import (
    GitignoreManager,
    check_gitignore_safety,
    ensure_gitignore_safe,
)
from runtime.sensitive_file_detector import SafetyCheckResult
from runtime.shell_config import get_shell_config, ShellConfig, DEFAULT_CONFIG_PATH

app = typer.Typer(name="config", help="Config safety commands")
console = Console()


@app.command()
def safety_check(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Root path to check",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    manager = GitignoreManager(root_path=path)
    check_result = manager.check_sensitive_patterns()
    
    is_safe = len(check_result.tracked_sensitive_files) == 0 and check_result.sensitive_not_excluded == 0
    
    if is_safe:
        console.print(Panel(
            f"Gitignore: {check_result.gitignore_path or 'not found'}\n"
            f"Sensitive patterns excluded: {check_result.sensitive_excluded}\n"
            f"Tracked sensitive files: {len(check_result.tracked_sensitive_files)}",
            title="[OK] Config Safe",
            border_style="green"
        ))
        return
    
    console.print(Panel(
        f"Gitignore: {check_result.gitignore_path or 'not found'}\n"
        f"Sensitive patterns excluded: {check_result.sensitive_excluded}\n"
        f"Missing gitignore entries: {check_result.sensitive_not_excluded}\n"
        f"Tracked sensitive files: {len(check_result.tracked_sensitive_files)}",
        title="[WARN] Config Safety Issues",
        border_style="yellow"
    ))
    
    if check_result.tracked_sensitive_files:
        console.print("\n[bold red][DANGER] TRACKED SENSITIVE FILES:[/bold red]")
        for file in check_result.tracked_sensitive_files:
            console.print(f"  - {file}")
        console.print("\n[yellow]Manual remediation required:[/yellow]")
        console.print("  git rm --cached <file>")
        console.print("  git commit -m 'Remove exposed secrets'")
    
    if verbose:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in check_result.recommendations:
            console.print(f"  - {rec}")


@app.command()
def safety_fix(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Root path to fix",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
):
    manager = GitignoreManager(root_path=path)
    result = ensure_gitignore_safe(root_path=path, auto_fix=False)
    
    if result.safe:
        console.print(Panel(
            "All sensitive patterns already excluded",
            title="[OK] Already Safe",
            border_style="green"
        ))
        return
    
    if result.missing_gitignore_entries:
        console.print("[cyan]Missing gitignore entries:[/cyan]")
        for entry in result.missing_gitignore_entries:
            console.print(f"  - {entry}")
        
        if dry_run:
            console.print("[yellow]Dry run - not applying changes[/yellow]")
            return
        
        manager.add_entries(result.missing_gitignore_entries)
        console.print(Panel(
            f"Added {len(result.missing_gitignore_entries)} entries to .gitignore",
            title="[OK] Gitignore Updated",
            border_style="green"
        ))
    
    if result.tracked_sensitive_files:
        console.print("\n[bold red][DANGER] Cannot auto-fix tracked files:[/bold red]")
        for detected in result.tracked_sensitive_files:
            console.print(f"  - {detected.path}")
        console.print("\n[yellow]Manual remediation required:[/yellow]")
        console.print("  git rm --cached <file>")
        console.print("  git commit -m 'Remove exposed secrets'")


@app.command()
def patterns(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Root path to check",
    ),
    risk: str = typer.Option(
        "all",
        "--risk",
        "-r",
        help="Filter by risk level: all, high, medium",
    ),
):
    from runtime.sensitive_file_detector import SensitiveFileDetector, RiskLevel
    
    detector = SensitiveFileDetector(root_path=path)
    
    if risk == "high":
        patterns = detector.get_patterns_by_risk()[RiskLevel.HIGH]
    elif risk == "medium":
        patterns = detector.get_patterns_by_risk()[RiskLevel.MEDIUM]
    else:
        patterns = detector.patterns
    
    table = Table(title="Sensitive Patterns")
    table.add_column("Pattern", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Risk", style="yellow")
    table.add_column("Category", style="magenta")
    
    for p in patterns:
        table.add_row(
            p.pattern,
            p.pattern_type.value,
            p.risk_level.value,
            p.category,
        )
    
    console.print(table)


@app.command()
def status(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Root path to check",
    ),
):
    manager = GitignoreManager(root_path=path)
    summary = manager.get_safety_summary()
    
    status_color = "green" if summary["safe"] else "yellow"
    status_text = "[OK] SAFE" if summary["safe"] else "[WARN] ISSUES"
    
    console.print(Panel(
        f"Status: {status_text}\n"
        f"Gitignore exists: {summary['gitignore_exists']}\n"
        f"Total entries: {summary['total_entries']}\n"
        f"Sensitive excluded: {summary['sensitive_excluded']}\n"
        f"Sensitive not excluded: {summary['sensitive_not_excluded']}\n"
        f"Tracked sensitive: {summary['tracked_sensitive']}",
        title="Config Safety Status",
        border_style=status_color
    ))


@app.command()
def shell(
    bash_path: str = typer.Option(
        None,
        "--bash-path",
        "-b",
        help="Path to bash executable for Windows (e.g., 'C:/Program Files/Git/bin/bash.exe')",
    ),
    force_bash: bool = typer.Option(
        False,
        "--force-bash",
        "-f",
        help="Force bash on all platforms",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current shell configuration",
    ),
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
    ),
):
    if show:
        config = get_shell_config(path / DEFAULT_CONFIG_PATH)
        executable = config.get_executable()
        
        console.print(Panel(
            f"Platform: {sys.platform}\n"
            f"Shell type: {config.shell_type}\n"
            f"Force bash: {config.force_bash}\n"
            f"Bash executable: {executable or 'Not configured'}\n"
            f"Config file: {config.config_path}\n"
            f"Config exists: {config.config_path.exists()}",
            title="Shell Configuration",
            border_style="cyan"
        ))
        
        if sys.platform == "win32" and not executable:
            console.print("\n[yellow]Tip: Configure bash to use Git Bash instead of cmd.exe[/yellow]")
            console.print("  asyncdev config shell --bash-path 'C:/Program Files/Git/bin/bash.exe'")
        return
    
    if bash_path:
        config_dir = path / ".runtime"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "shell-config.yaml"
        
        config_data = {}
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        
        config_data["windows_bash_executable"] = bash_path
        if force_bash:
            config_data["force_bash"] = True
        
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        console.print(Panel(
            f"Bash path: {bash_path}\n"
            f"Force bash: {force_bash}\n"
            f"Config saved to: {config_file}",
            title="[OK] Shell Configuration Updated",
            border_style="green"
        ))
        
        console.print("\n[cyan]Environment variable alternative:[/cyan]")
        console.print(f"  export ASYNCDEV_BASH_EXECUTABLE='{bash_path}'")
        return
    
    if force_bash:
        config_dir = path / ".runtime"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "shell-config.yaml"
        
        config_data = {}
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        
        config_data["force_bash"] = True
        
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        console.print(Panel(
            f"Force bash: True\n"
            f"Config saved to: {config_file}",
            title="[OK] Shell Configuration Updated",
            border_style="green"
        ))
        return
    
    config = get_shell_config(path / DEFAULT_CONFIG_PATH)
    executable = config.get_executable()
    
    console.print(Panel(
        f"Platform: {sys.platform}\n"
        f"Current bash executable: {executable or 'Not configured (using default)'}\n"
        f"Config file: {config.config_path}",
        title="Shell Configuration",
        border_style="cyan"
    ))
    
    if sys.platform == "win32":
        console.print("\n[cyan]Options:[/cyan]")
        console.print("  --bash-path 'C:/Program Files/Git/bin/bash.exe'  Set Git Bash path")
        console.print("  --force-bash                                     Force bash on all platforms")
        console.print("  --show                                           Show detailed configuration")