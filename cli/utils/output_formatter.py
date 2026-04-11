"""Output formatting utilities for CLI UX improvements.

Rich Panel formatting for next-step guidance and status summaries.
Makes operator's next action obvious and reduces cognitive load.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_next_step(
    action: str,
    command: str,
    artifact_path: Path | None = None,
    root: Path | None = None,
    hints: list[str] | None = None,
) -> None:
    from cli.utils.path_formatter import get_relative_path
    
    content_lines = [f"[bold cyan]{action}[/bold cyan]"]
    content_lines.append(f"\n[green]Command:[/green] {command}")
    
    if artifact_path:
        if root is None:
            root = Path.cwd()
        relative = get_relative_path(artifact_path, root)
        content_lines.append(f"[yellow]Artifact:[/yellow] {relative}")
    
    if hints:
        content_lines.append("\n[dim]Hints:[/dim]")
        for hint in hints:
            content_lines.append(f"  • {hint}")
    
    panel = Panel(
        "\n".join(content_lines),
        title="[bold]Next Step[/bold]",
        border_style="blue",
        expand=False,
    )
    
    console.print()
    console.print(panel)


def print_success_panel(
    message: str,
    title: str = "Success",
    paths: list[dict] | None = None,
    root: Path | None = None,
) -> None:
    from cli.utils.path_formatter import get_relative_path
    
    if root is None:
        root = Path.cwd()
    
    content_lines = [f"[green]{message}[/green]"]
    
    if paths:
        content_lines.append("\n[bold]Created:[/bold]")
        for item in paths:
            label = item.get("label", "")
            path = Path(item.get("path", ""))
            relative = get_relative_path(path, root)
            content_lines.append(f"  [{label}] {relative}")
    
    panel = Panel(
        "\n".join(content_lines),
        title=f"[bold green]{title}[/bold green]",
        border_style="green",
        expand=False,
    )
    
    console.print()
    console.print(panel)
    if paths and root:
        console.print(f"[dim]root: {root}[/dim]")


def print_status_summary(
    status_data: dict,
    title: str = "Status",
    show_recommendation: bool = True,
) -> None:
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in status_data.items():
        if key == "recommendation":
            continue
        table.add_row(key, str(value))
    
    console.print(Panel(table, title=f"[bold]{title}[/bold]", border_style="blue"))
    
    if show_recommendation and status_data.get("recommendation"):
        console.print()
        print_next_step(
            action=status_data.get("recommendation", ""),
            command=status_data.get("next_command", ""),
        )


def print_error_panel(
    message: str,
    title: str = "Error",
    suggestion: str | None = None,
) -> None:
    content = f"[red]{message}[/red]"
    
    if suggestion:
        content += f"\n\n[yellow]Suggestion:[/yellow] {suggestion}"
    
    panel = Panel(
        content,
        title=f"[bold red]{title}[/bold red]",
        border_style="red",
        expand=False,
    )
    
    console.print()
    console.print(panel)


def print_phase_indicator(phase: str, emoji: bool = True) -> None:
    phase_emoji = {
        "planning": "📋",
        "executing": "⚡",
        "reviewing": "🔍",
        "blocked": "🚫",
        "completed": "✅",
        "archived": "📦",
    }
    
    phase_style = {
        "planning": "blue",
        "executing": "yellow",
        "reviewing": "cyan",
        "blocked": "red",
        "completed": "green",
        "archived": "dim",
    }
    
    style = phase_style.get(phase, "white")
    indicator = phase_emoji.get(phase, "") if emoji else ""
    
    console.print(f"\n[{style}]Phase: {indicator} {phase}[/{style}]")