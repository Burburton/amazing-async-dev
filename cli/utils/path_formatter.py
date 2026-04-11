"""Path formatting utilities for CLI output.

Provides relative path display with root hint for better UX.
Operator can see where file is without hunting for full path.
"""

from pathlib import Path
from rich.console import Console

console = Console()


def get_relative_path(absolute_path: Path, root: Path) -> str:
    """Get relative path from root, or absolute if not relative.
    
    Args:
        absolute_path: Full path to file/directory
        root: Root directory to compute relative path from
        
    Returns:
        Relative path string, or absolute if not under root
    """
    try:
        return str(absolute_path.relative_to(root))
    except ValueError:
        # Path is not under root, return absolute
        return str(absolute_path)


def format_path(path: Path, root: Path | None = None, show_root_hint: bool = True) -> str:
    """Format path for display with optional root hint.
    
    Args:
        path: Path to format
        root: Root directory (defaults to cwd)
        show_root_hint: Whether to show root hint
        
    Returns:
        Formatted path string with optional root hint
    """
    if root is None:
        root = Path.cwd()
    
    relative = get_relative_path(path, root)
    
    if show_root_hint and relative != str(path):
        # Show relative path with root hint
        return f"{relative} (root: {root})"
    else:
        # Show absolute path
        return str(path)


def print_path_with_root(
    path: Path,
    root: Path | None = None,
    label: str = "Path",
    style: str = "cyan",
) -> None:
    """Print path with root hint in formatted output.
    
    Args:
        path: Path to print
        root: Root directory
        label: Label prefix (e.g., "Created:", "Output:")
        style: Rich style for path
    """
    if root is None:
        root = Path.cwd()
    
    relative = get_relative_path(path, root)
    
    if relative != str(path):
        console.print(f"[bold]{label}[/bold] [{style}]{relative}[/{style}]")
        console.print(f"[dim]  (root: {root})[/dim]")
    else:
        console.print(f"[bold]{label}[/bold] [{style}]{path}[/{style}]")


def print_paths_table(
    paths: list[dict],
    root: Path | None = None,
    title: str = "Artifacts",
) -> None:
    """Print multiple paths in a table format.
    
    Args:
        paths: List of dicts with 'label' and 'path' keys
        root: Root directory
        title: Table title
    """
    from rich.table import Table
    
    if root is None:
        root = Path.cwd()
    
    table = Table(title=title)
    table.add_column("Type", style="cyan")
    table.add_column("Path", style="green")
    
    for item in paths:
        label = item.get("label", "File")
        path = Path(item.get("path", ""))
        relative = get_relative_path(path, root)
        table.add_row(label, relative)
    
    console.print(table)
    console.print(f"[dim]root: {root}[/dim]")