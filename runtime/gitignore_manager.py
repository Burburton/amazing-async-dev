"""Gitignore manager for Feature 057 - Config Safety Automation."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.sensitive_file_detector import (
    SensitiveFileDetector,
    SafetyCheckResult,
    RiskLevel,
)


@dataclass
class GitignoreCheckResult:
    """Result of gitignore check."""
    gitignore_exists: bool
    gitignore_path: Path | None
    current_entries: list[str]
    sensitive_excluded: int
    sensitive_not_excluded: int
    tracked_sensitive_files: list[str]
    recommendations: list[str]


class GitignoreManager:
    """Manages .gitignore file for sensitive pattern exclusion."""
    
    def __init__(self, root_path: Path | None = None):
        self.root_path = root_path or Path.cwd()
        self.gitignore_path = self.root_path / ".gitignore"
        self.detector = SensitiveFileDetector(root_path=self.root_path)
    
    def load_gitignore(self) -> list[str]:
        """Load current gitignore entries."""
        if not self.gitignore_path.exists():
            return []
        content = self.gitignore_path.read_text(encoding="utf-8")
        return [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.startswith("#")
        ]
    
    def save_gitignore(self, entries: list[str]) -> None:
        """Save gitignore entries."""
        existing = []
        if self.gitignore_path.exists():
            existing = self.gitignore_path.read_text(encoding="utf-8").splitlines()
        
        new_content_lines = []
        added_entries = []
        
        for entry in entries:
            if entry not in existing:
                added_entries.append(entry)
        
        if added_entries:
            new_content_lines.append("")
            new_content_lines.append("# Added by asyncdev config safety")
            new_content_lines.extend(added_entries)
        
        full_content = existing + new_content_lines
        self.gitignore_path.write_text(
            "\n".join(full_content) + "\n",
            encoding="utf-8"
        )
    
    def add_entries(self, entries: list[str]) -> list[str]:
        """Add entries to gitignore."""
        current = self.load_gitignore()
        new_entries = [e for e in entries if e not in current]
        if new_entries:
            self.save_gitignore(current + new_entries)
        return new_entries
    
    def is_excluded(self, file_path: str) -> bool:
        """Check if a file is excluded by gitignore."""
        entries = self.load_gitignore()
        return self.detector.check_pattern_excluded(file_path, entries)
    
    def get_tracked_files(self) -> list[str]:
        """Get files tracked by git."""
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.splitlines()
            return []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
    
    def check_sensitive_patterns(self) -> GitignoreCheckResult:
        """Check if sensitive patterns are excluded."""
        entries = self.load_gitignore()
        tracked = self.get_tracked_files()
        
        safety_result = self.detector.run_safety_check(entries, tracked)
        
        recommendations = []
        for pattern in safety_result.missing_gitignore_entries:
            recommendations.append(f"Add '{pattern}' to .gitignore")
        
        for detected in safety_result.tracked_sensitive_files:
            relative = str(detected.path.relative_to(self.root_path))
            recommendations.append(
                f"Remove '{relative}' from git tracking (git rm --cached)"
            )
        
        return GitignoreCheckResult(
            gitignore_exists=self.gitignore_path.exists(),
            gitignore_path=self.gitignore_path if self.gitignore_path.exists() else None,
            current_entries=entries,
            sensitive_excluded=safety_result.excluded_correctly,
            sensitive_not_excluded=len(safety_result.missing_gitignore_entries),
            tracked_sensitive_files=[
                str(d.path.relative_to(self.root_path))
                for d in safety_result.tracked_sensitive_files
            ],
            recommendations=recommendations,
        )
    
    def ensure_safe(self, auto_fix: bool = True) -> SafetyCheckResult:
        """Ensure all sensitive patterns are excluded."""
        entries = self.load_gitignore()
        tracked = self.get_tracked_files()
        
        result = self.detector.run_safety_check(entries, tracked)
        
        if auto_fix and result.missing_gitignore_entries:
            self.add_entries(result.missing_gitignore_entries)
        
        return result
    
    def get_safety_summary(self) -> dict[str, Any]:
        """Get summary for display."""
        check_result = self.check_sensitive_patterns()
        return {
            "gitignore_exists": check_result.gitignore_exists,
            "total_entries": len(check_result.current_entries),
            "sensitive_excluded": check_result.sensitive_excluded,
            "sensitive_not_excluded": check_result.sensitive_not_excluded,
            "tracked_sensitive": len(check_result.tracked_sensitive_files),
            "tracked_files": check_result.tracked_sensitive_files,
            "recommendations": check_result.recommendations,
            "safe": (
                check_result.sensitive_not_excluded == 0
                and len(check_result.tracked_sensitive_files) == 0
            ),
        }


def check_gitignore_safety(root_path: Path | None = None) -> GitignoreCheckResult:
    """Convenience function to check gitignore safety."""
    manager = GitignoreManager(root_path=root_path)
    return manager.check_sensitive_patterns()


def ensure_gitignore_safe(
    root_path: Path | None = None,
    auto_fix: bool = True,
) -> SafetyCheckResult:
    """Convenience function to ensure gitignore safety."""
    manager = GitignoreManager(root_path=root_path)
    return manager.ensure_safe(auto_fix=auto_fix)