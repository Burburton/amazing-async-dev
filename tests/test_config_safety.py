"""Tests for Feature 057 - Config Safety Automation."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from runtime.sensitive_file_detector import (
    SensitiveFileDetector,
    SensitivePattern,
    DetectedFile,
    SafetyCheckResult,
    PatternType,
    RiskLevel,
    DEFAULT_SENSITIVE_PATTERNS,
    detect_sensitive_patterns,
    run_safety_check,
)
from runtime.gitignore_manager import (
    GitignoreManager,
    GitignoreCheckResult,
    check_gitignore_safety,
    ensure_gitignore_safe,
)


class TestSensitiveFileDetector:
    def test_detector_has_default_patterns(self):
        detector = SensitiveFileDetector()
        assert len(detector.patterns) > 0
        assert len(DEFAULT_SENSITIVE_PATTERNS) > 0
    
    def test_detector_includes_runtime_pattern(self):
        detector = SensitiveFileDetector()
        patterns = [p.pattern for p in detector.patterns]
        assert ".runtime/" in patterns
    
    def test_detector_includes_env_pattern(self):
        detector = SensitiveFileDetector()
        patterns = [p.pattern for p in detector.patterns]
        assert "*.env" in patterns
    
    def test_detector_includes_resend_config(self):
        detector = SensitiveFileDetector()
        patterns = [p.pattern for p in detector.patterns]
        assert "resend-config.json" in patterns
    
    def test_get_patterns_by_risk(self):
        detector = SensitiveFileDetector()
        risks = detector.get_patterns_by_risk()
        assert RiskLevel.HIGH in risks
        assert RiskLevel.MEDIUM in risks
        assert len(risks[RiskLevel.HIGH]) > len(risks[RiskLevel.MEDIUM])
    
    def test_get_patterns_by_category(self):
        detector = SensitiveFileDetector()
        categories = detector.get_patterns_by_category()
        assert "runtime_config" in categories
        assert "provider_config" in categories
    
    def test_check_pattern_excluded_direct_match(self):
        detector = SensitiveFileDetector()
        gitignore_entries = ["*.env", ".runtime/"]
        
        assert detector.check_pattern_excluded("*.env", gitignore_entries) is True
        assert detector.check_pattern_excluded(".runtime/", gitignore_entries) is True
    
    def test_check_pattern_excluded_no_match(self):
        detector = SensitiveFileDetector()
        gitignore_entries = ["*.py"]
        
        assert detector.check_pattern_excluded("*.env", gitignore_entries) is False
        assert detector.check_pattern_excluded(".runtime/", gitignore_entries) is False
    
    def test_check_pattern_excluded_directory_covers_nested(self):
        detector = SensitiveFileDetector()
        gitignore_entries = [".runtime/"]
        
        assert detector.check_pattern_excluded(".runtime/", gitignore_entries) is True
    
    def test_check_pattern_excluded_glob_match(self):
        detector = SensitiveFileDetector()
        gitignore_entries = ["*.env"]
        
        assert detector.check_pattern_excluded("*.env", gitignore_entries) is True
    
    def test_run_safety_check_safe(self):
        detector = SensitiveFileDetector()
        recommended = detector.get_recommended_gitignore_entries()
        gitignore_entries = recommended
        
        result = detector.run_safety_check(gitignore_entries, [])
        
        assert result.missing_gitignore_entries == []
        assert result.tracked_sensitive_files == []
    
    def test_run_safety_check_missing_entries(self):
        detector = SensitiveFileDetector()
        gitignore_entries = ["*.py"]
        
        result = detector.run_safety_check(gitignore_entries, [])
        
        assert ".runtime/" in result.missing_gitignore_entries
    
    def test_run_safety_check_tracked_sensitive(self):
        detector = SensitiveFileDetector(root_path=Path("/tmp"))
        
        result = detector.run_safety_check([], [])
        
        assert isinstance(result, SafetyCheckResult)
        assert isinstance(result.tracked_sensitive_files, list)


class TestGitignoreManager:
    def test_manager_initializes(self):
        manager = GitignoreManager()
        assert manager.gitignore_path.name == ".gitignore"
    
    def test_load_gitignore_empty(self, tmp_path):
        manager = GitignoreManager(root_path=tmp_path)
        entries = manager.load_gitignore()
        assert entries == []
    
    def test_load_gitignore_with_entries(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.py\n*.md\n# comment\n.runtime/\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        entries = manager.load_gitignore()
        
        assert "*.py" in entries
        assert "*.md" in entries
        assert ".runtime/" in entries
        assert "# comment" not in entries
    
    def test_is_excluded_true(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".runtime/\n*.env\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        
        assert manager.is_excluded(".runtime/") is True
        assert manager.is_excluded("*.env") is True
    
    def test_is_excluded_false(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.py\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        
        assert manager.is_excluded("*.env") is False
    
    def test_add_entries(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.py\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        new_entries = manager.add_entries([".runtime/", "*.env"])
        
        assert ".runtime/" in new_entries
        assert "*.env" in new_entries
        
        content = gitignore.read_text()
        assert ".runtime/" in content
        assert "*.env" in content
    
    def test_add_entries_no_duplicates(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.py\n.runtime/\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        new_entries = manager.add_entries([".runtime/", "*.env"])
        
        assert ".runtime/" not in new_entries
        assert "*.env" in new_entries
    
    def test_get_safety_summary_safe(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        
        detector = SensitiveFileDetector()
        recommended = detector.get_recommended_gitignore_entries()
        gitignore.write_text("\n".join(recommended) + "\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        
        with patch.object(manager, 'get_tracked_files', return_value=[]):
            summary = manager.get_safety_summary()
            
            assert summary["safe"] is True
            assert summary["sensitive_not_excluded"] == 0
    
    def test_get_safety_summary_issues(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.py\n")
        
        manager = GitignoreManager(root_path=tmp_path)
        
        with patch.object(manager, 'get_tracked_files', return_value=[]):
            summary = manager.get_safety_summary()
            
            assert summary["safe"] is False
            assert summary["sensitive_not_excluded"] > 0
    
    def test_ensure_safe_auto_fix(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("")
        
        manager = GitignoreManager(root_path=tmp_path)
        
        with patch.object(manager, 'get_tracked_files', return_value=[]):
            result = manager.ensure_safe(auto_fix=True)
            
            content = gitignore.read_text()
            assert ".runtime/" in content


class TestConvenienceFunctions:
    def test_detect_sensitive_patterns(self):
        with patch('runtime.sensitive_file_detector.SensitiveFileDetector') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.detect_sensitive_files.return_value = []
            
            result = detect_sensitive_patterns()
            assert result == []
    
    def test_run_safety_check(self):
        with patch('runtime.sensitive_file_detector.SensitiveFileDetector') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.run_safety_check.return_value = SafetyCheckResult(safe=True)
            
            result = run_safety_check(Path.cwd(), [], [])
            assert result.safe is True
    
    def test_check_gitignore_safety(self):
        with patch('runtime.gitignore_manager.GitignoreManager') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.check_sensitive_patterns.return_value = GitignoreCheckResult(
                gitignore_exists=True,
                gitignore_path=Path(".gitignore"),
                current_entries=[".runtime/"],
                sensitive_excluded=1,
                sensitive_not_excluded=0,
                tracked_sensitive_files=[],
                recommendations=[],
            )
            
            result = check_gitignore_safety()
            assert result.gitignore_exists is True
    
    def test_ensure_gitignore_safe(self):
        with patch('runtime.gitignore_manager.GitignoreManager') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.ensure_safe.return_value = SafetyCheckResult(safe=True)
            
            result = ensure_gitignore_safe()
            assert result.safe is True


class TestSensitivePatternDataclass:
    def test_pattern_creation(self):
        pattern = SensitivePattern(
            pattern=".runtime/",
            pattern_type=PatternType.DIRECTORY,
            risk_level=RiskLevel.HIGH,
            description="Runtime config",
            category="runtime_config",
        )
        
        assert pattern.pattern == ".runtime/"
        assert pattern.pattern_type == PatternType.DIRECTORY
        assert pattern.risk_level == RiskLevel.HIGH


class TestSafetyCheckResultDataclass:
    def test_result_creation(self):
        result = SafetyCheckResult(
            safe=True,
            detected_files=[],
            missing_gitignore_entries=[],
            tracked_sensitive_files=[],
            warnings=[],
            checked_patterns=10,
            excluded_correctly=10,
        )
        
        assert result.safe is True
        assert result.checked_patterns == 10