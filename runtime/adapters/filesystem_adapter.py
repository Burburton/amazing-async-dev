"""Filesystem adapter for file operations."""

from pathlib import Path
from typing import Any


class FilesystemAdapter:
    """Adapter for filesystem operations."""

    def read_file(self, path: Path) -> str:
        """Read file content."""
        return Path(path).read_text(encoding="utf-8")

    def write_file(self, path: Path, content: str) -> None:
        """Write content to file."""
        Path(path).write_text(content, encoding="utf-8")

    def ensure_dir(self, path: Path) -> None:
        """Ensure directory exists."""
        Path(path).mkdir(parents=True, exist_ok=True)

    def file_exists(self, path: Path) -> bool:
        """Check if file exists."""
        return Path(path).exists()

    def list_files(self, path: Path, pattern: str = "*") -> list[Path]:
        """List files matching pattern."""
        return list(Path(path).glob(pattern))

    def delete_file(self, path: Path) -> None:
        """Delete file."""
        Path(path).unlink(missing_ok=True)

    def read_yaml(self, path: Path) -> dict[str, Any]:
        """Read YAML file."""
        import yaml

        content = self.read_file(path)
        return yaml.safe_load(content)

    def write_yaml(self, path: Path, data: dict[str, Any]) -> None:
        """Write YAML file."""
        import yaml

        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        self.write_file(path, content)