"""Git adapter for repository operations."""

from pathlib import Path
from typing import Any


class GitAdapter:
    """Adapter for git operations."""

    def __init__(self, repo_path: Path | None = None):
        self.repo_path = repo_path or Path.cwd()

    def is_git_repo(self) -> bool:
        """Check if directory is a git repository."""
        return (self.repo_path / ".git").exists()

    def get_current_branch(self) -> str:
        """Get current branch name."""
        import subprocess

        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def commit(self, message: str) -> bool:
        """Create a commit."""
        import subprocess

        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def add_file(self, path: Path) -> bool:
        """Add file to staging."""
        import subprocess

        result = subprocess.run(
            ["git", "add", str(path)],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def get_status(self) -> dict[str, Any]:
        """Get git status."""
        import subprocess

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        status = {"modified": [], "added": [], "deleted": [], "untracked": []}

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            code = line[:2]
            file_path = line[3:].strip()

            if code.startswith("M"):
                status["modified"].append(file_path)
            elif code.startswith("A"):
                status["added"].append(file_path)
            elif code.startswith("D"):
                status["deleted"].append(file_path)
            elif code == "??" or code.startswith("?"):
                status["untracked"].append(file_path)

        return status

    def get_last_commit_hash(self) -> str:
        """Get last commit hash."""
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()[:7]