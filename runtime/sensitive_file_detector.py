"""Sensitive file detector for Feature 057 - Config Safety Automation.

Detects files matching sensitive patterns that should be excluded from git.
"""

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class RiskLevel(Enum):
    """Risk level for sensitive files."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PatternType(Enum):
    """Type of sensitive pattern."""
    DIRECTORY = "directory"
    FILE = "file"
    GLOB = "glob"


@dataclass
class SensitivePattern:
    """A sensitive file/directory pattern."""
    pattern: str
    pattern_type: PatternType
    risk_level: RiskLevel
    description: str
    category: str


@dataclass
class DetectedFile:
    """A detected sensitive file."""
    path: Path
    pattern: SensitivePattern
    exists: bool
    is_tracked_by_git: bool = False


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    safe: bool
    detected_files: list[DetectedFile] = field(default_factory=list)
    missing_gitignore_entries: list[str] = field(default_factory=list)
    tracked_sensitive_files: list[DetectedFile] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_patterns: int = 0
    excluded_correctly: int = 0


# Default sensitive patterns
DEFAULT_SENSITIVE_PATTERNS: list[SensitivePattern] = [
    # High-risk directories
    SensitivePattern(
        pattern=".runtime/",
        pattern_type=PatternType.DIRECTORY,
        risk_level=RiskLevel.HIGH,
        description="Runtime config directory (contains API keys)",
        category="runtime_config",
    ),
    SensitivePattern(
        pattern=".secrets/",
        pattern_type=PatternType.DIRECTORY,
        risk_level=RiskLevel.HIGH,
        description="Secrets directory",
        category="secret_directory",
    ),
    SensitivePattern(
        pattern="cloudflare/",
        pattern_type=PatternType.DIRECTORY,
        risk_level=RiskLevel.HIGH,
        description="Cloudflare worker credentials",
        category="worker_credentials",
    ),
    SensitivePattern(
        pattern=".credentials/",
        pattern_type=PatternType.DIRECTORY,
        risk_level=RiskLevel.HIGH,
        description="Credentials directory",
        category="credentials",
    ),
    
    # High-risk files
    SensitivePattern(
        pattern="*.env",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.HIGH,
        description="Environment secrets file",
        category="environment_secrets",
    ),
    SensitivePattern(
        pattern="*.env.local",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.HIGH,
        description="Local environment secrets file",
        category="environment_secrets",
    ),
    SensitivePattern(
        pattern="*-config.json",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.HIGH,
        description="Provider config file (contains tokens)",
        category="provider_config",
    ),
    SensitivePattern(
        pattern="resend-config.json",
        pattern_type=PatternType.FILE,
        risk_level=RiskLevel.HIGH,
        description="Resend API config",
        category="provider_config",
    ),
    SensitivePattern(
        pattern=".resend-config.json",
        pattern_type=PatternType.FILE,
        risk_level=RiskLevel.HIGH,
        description="Resend API config (hidden)",
        category="provider_config",
    ),
    
    # Medium-risk patterns
    SensitivePattern(
        pattern="*secret*",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.MEDIUM,
        description="File with 'secret' in name",
        category="named_secret",
    ),
    SensitivePattern(
        pattern="*token*",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.MEDIUM,
        description="File with 'token' in name",
        category="named_token",
    ),
    SensitivePattern(
        pattern="*credentials*",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.MEDIUM,
        description="File with 'credentials' in name",
        category="named_credentials",
    ),
    
    # Nested patterns
    SensitivePattern(
        pattern="**/secrets/**",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.HIGH,
        description="Any secrets directory at any depth",
        category="nested_secrets",
    ),
    SensitivePattern(
        pattern="**/.env*",
        pattern_type=PatternType.GLOB,
        risk_level=RiskLevel.HIGH,
        description="Any .env file at any depth",
        category="nested_env",
    ),
]


class SensitiveFileDetector:
    """Detects sensitive files matching defined patterns."""
    
    def __init__(
        self,
        patterns: list[SensitivePattern] | None = None,
        root_path: Path | None = None,
    ):
        self.patterns = patterns or DEFAULT_SENSITIVE_PATTERNS
        self.root_path = root_path or Path.cwd()
    
    def detect_sensitive_files(self) -> list[DetectedFile]:
        """Scan for files matching sensitive patterns.
        
        Returns:
            List of detected sensitive files
        """
        detected = []
        
        for pattern in self.patterns:
            matches = self._find_matching_files(pattern)
            for match in matches:
                detected.append(DetectedFile(
                    path=match,
                    pattern=pattern,
                    exists=True,
                ))
        
        # Also check for pattern matches that don't exist yet
        # (for directories that should be gitignored even if empty)
        for pattern in self.patterns:
            if pattern.pattern_type == PatternType.DIRECTORY:
                potential_path = self.root_path / pattern.pattern.rstrip("/")
                if not potential_path.exists():
                    detected.append(DetectedFile(
                        path=potential_path,
                        pattern=pattern,
                        exists=False,
                    ))
        
        return detected
    
    def _find_matching_files(self, pattern: SensitivePattern) -> list[Path]:
        """Find files matching a pattern.
        
        Args:
            pattern: Sensitive pattern to match
            
        Returns:
            List of matching file paths
        """
        matches = []
        
        if pattern.pattern_type == PatternType.FILE:
            # Exact file match
            file_path = self.root_path / pattern.pattern
            if file_path.exists():
                matches.append(file_path)
        
        elif pattern.pattern_type == PatternType.DIRECTORY:
            # Directory match
            dir_path = self.root_path / pattern.pattern.rstrip("/")
            if dir_path.exists() and dir_path.is_dir():
                matches.append(dir_path)
        
        elif pattern.pattern_type == PatternType.GLOB:
            # Glob pattern match
            for path in self.root_path.rglob("*"):
                if fnmatch.fnmatch(str(path.relative_to(self.root_path)), pattern.pattern):
                    matches.append(path)
        
        return matches
    
    def get_patterns_by_category(self) -> dict[str, list[SensitivePattern]]:
        """Group patterns by category.
        
        Returns:
            Dict mapping category to patterns
        """
        categories: dict[str, list[SensitivePattern]] = {}
        for pattern in self.patterns:
            if pattern.category not in categories:
                categories[pattern.category] = []
            categories[pattern.category].append(pattern)
        return categories
    
    def get_patterns_by_risk(self) -> dict[RiskLevel, list[SensitivePattern]]:
        """Group patterns by risk level.
        
        Returns:
            Dict mapping risk level to patterns
        """
        risks: dict[RiskLevel, list[SensitivePattern]] = {
            RiskLevel.HIGH: [],
            RiskLevel.MEDIUM: [],
            RiskLevel.LOW: [],
        }
        for pattern in self.patterns:
            risks[pattern.risk_level].append(pattern)
        return risks
    
    def check_pattern_excluded(
        self,
        pattern: str,
        gitignore_entries: list[str],
    ) -> bool:
        """Check if a pattern is excluded by gitignore.
        
        Args:
            pattern: Pattern to check
            gitignore_entries: List of gitignore entries
            
        Returns:
            True if pattern is excluded
        """
        # Normalize pattern
        normalized = pattern.rstrip("/")
        
        for entry in gitignore_entries:
            # Normalize entry
            entry_normalized = entry.strip().rstrip("/")
            
            # Direct match
            if entry_normalized == normalized:
                return True
            
            # Pattern covers entry (e.g., *.env covers .env.local)
            if fnmatch.fnmatch(normalized, entry_normalized):
                return True
            
            # Entry covers pattern (e.g., .runtime/ covers resend-config.json inside)
            if entry_normalized.endswith("/") and normalized.startswith(entry_normalized.rstrip("/")):
                return True
        
        return False
    
    def run_safety_check(
        self,
        gitignore_entries: list[str],
        tracked_files: list[str] | None = None,
    ) -> SafetyCheckResult:
        """Run a comprehensive safety check.
        
        Args:
            gitignore_entries: Current gitignore entries
            tracked_files: Files currently tracked by git
            
        Returns:
            SafetyCheckResult with findings
        """
        detected_files = self.detect_sensitive_files()
        tracked_sensitive = []
        missing_entries = []
        warnings = []
        
        tracked_files = tracked_files or []
        
        for detected in detected_files:
            # Check if pattern is excluded
            pattern_str = detected.pattern.pattern
            is_excluded = self.check_pattern_excluded(pattern_str, gitignore_entries)
            
            if is_excluded:
                continue
            
            # Pattern not in gitignore
            if detected.pattern.pattern_type == PatternType.DIRECTORY:
                # Add directory pattern
                missing_entries.append(detected.pattern.pattern)
            elif detected.exists:
                # Add file pattern if file exists
                missing_entries.append(detected.pattern.pattern)
            
            # Check if file is tracked by git
            relative_path = str(detected.path.relative_to(self.root_path))
            if detected.exists and relative_path in tracked_files:
                detected.is_tracked_by_git = True
                tracked_sensitive.append(detected)
                warnings.append(
                    f"🚨 {relative_path} is TRACKED BY GIT (danger!) - "
                    f"Pattern: {pattern_str}"
                )
        
        # Deduplicate missing entries
        missing_entries = list(set(missing_entries))
        
        # Count correctly excluded
        excluded_count = len(detected_files) - len(tracked_sensitive) - len([
            d for d in detected_files 
            if not self.check_pattern_excluded(d.pattern.pattern, gitignore_entries)
        ])
        
        return SafetyCheckResult(
            safe=len(tracked_sensitive) == 0 and len(missing_entries) == 0,
            detected_files=detected_files,
            missing_gitignore_entries=missing_entries,
            tracked_sensitive_files=tracked_sensitive,
            warnings=warnings,
            checked_patterns=len(self.patterns),
            excluded_correctly=excluded_count,
        )
    
    def get_recommended_gitignore_entries(self) -> list[str]:
        """Get recommended gitignore entries for all patterns.
        
        Returns:
            List of gitignore entries to add
        """
        entries = []
        
        # Add directory patterns
        for pattern in self.patterns:
            if pattern.pattern_type == PatternType.DIRECTORY:
                entries.append(pattern.pattern)
            elif pattern.pattern_type == PatternType.GLOB:
                # Add glob pattern
                entries.append(pattern.pattern)
            elif pattern.risk_level == RiskLevel.HIGH:
                # Add high-risk file patterns
                entries.append(pattern.pattern)
        
        # Deduplicate
        return list(set(entries))


def detect_sensitive_patterns(root_path: Path | None = None) -> list[DetectedFile]:
    """Convenience function to detect sensitive files.
    
    Args:
        root_path: Root path to scan
        
    Returns:
        List of detected sensitive files
    """
    detector = SensitiveFileDetector(root_path=root_path)
    return detector.detect_sensitive_files()


def run_safety_check(
    root_path: Path,
    gitignore_entries: list[str],
    tracked_files: list[str] | None = None,
) -> SafetyCheckResult:
    """Convenience function to run safety check.
    
    Args:
        root_path: Root path to check
        gitignore_entries: Current gitignore entries
        tracked_files: Files tracked by git
        
    Returns:
        SafetyCheckResult
    """
    detector = SensitiveFileDetector(root_path=root_path)
    return detector.run_safety_check(gitignore_entries, tracked_files)