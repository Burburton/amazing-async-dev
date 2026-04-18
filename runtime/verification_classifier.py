"""Verification Type Classifier - Feature 056.

Enhanced classification based on file patterns, task context, and feature spec.

Classification rules from spec:
- src/components/*.tsx → frontend_interactive
- src/pages/*.tsx → frontend_interactive
- src/styles/*.css → frontend_visual_behavior
- docs/*.md only → backend_only
- src/api/*.py only → backend_only
- tests/*.py only → backend_only
- Mix of frontend + backend → mixed_app_workflow
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class VerificationType(str, Enum):
    """Verification type classification."""
    BACKEND_ONLY = "backend_only"
    FRONTEND_NONINTERACTIVE = "frontend_noninteractive"
    FRONTEND_INTERACTIVE = "frontend_interactive"
    FRONTEND_VISUAL_BEHAVIOR = "frontend_visual_behavior"
    MIXED_APP_WORKFLOW = "mixed_app_workflow"


FRONTEND_COMPONENT_PATTERNS = [
    "src/components/",
    "components/",
    "app/components/",
    "lib/components/",
]

FRONTEND_PAGE_PATTERNS = [
    "src/pages/",
    "pages/",
    "app/",
    "routes/",
    "src/app/",
]

FRONTEND_STYLE_PATTERNS = [
    "src/styles/",
    "styles/",
    "css/",
    "*.css",
    "*.scss",
    "*.less",
]

FRONTEND_EXTENSIONS = [
    ".tsx",
    ".jsx",
    ".vue",
    ".svelte",
    ".html",
    ".css",
    ".scss",
    ".less",
]

BACKEND_PATTERNS = [
    "src/api/",
    "api/",
    "backend/",
    "server/",
    "lib/api/",
    "routes/api/",
]

BACKEND_EXTENSIONS = [
    ".py",
    ".go",
    ".rs",
    ".java",
    ".ts",
]

DOC_PATTERNS = [
    "docs/",
    "*.md",
]

TEST_PATTERNS = [
    "tests/",
    "test/",
    "__tests__/",
    "*.test.",
    "*.spec.",
    "test_",
]

INTERACTIVE_KEYWORDS = [
    "click", "tap", "navigate", "form", "submit", "button",
    "modal", "drawer", "panel", "filter", "search", "sort",
    "drag", "drop", "gesture", "scroll", "swipe",
    "interaction", "user flow", "multi-step", "wizard",
    "ui", "ux", "frontend", "web", "page", "browser", "client",
    "component", "react", "vue", "angular", "svelte",
]

VISUAL_KEYWORDS = [
    "animation", "visual", "canvas", "map", "render",
    "display", "style", "layout", "design", "theme",
]


@dataclass
class ClassificationResult:
    """Result of verification classification."""
    verification_type: VerificationType
    confidence: float
    detected_patterns: list[str]
    reasoning: str
    files_analyzed: int


def classify_files(files: list[str]) -> tuple[bool, bool, bool, bool]:
    """Classify file list into categories.
    
    Returns:
        Tuple of (has_frontend_component, has_frontend_page, has_frontend_style, has_backend)
    """
    has_frontend_component = False
    has_frontend_page = False
    has_frontend_style = False
    has_backend = False
    
    for file in files:
        file_lower = file.lower()
        
        for pattern in FRONTEND_COMPONENT_PATTERNS:
            if pattern in file_lower:
                has_frontend_component = True
                break
        
        for pattern in FRONTEND_PAGE_PATTERNS:
            if pattern in file_lower and not has_backend:
                if "api" not in file_lower:
                    has_frontend_page = True
                    break
        
        for pattern in FRONTEND_STYLE_PATTERNS:
            if pattern in file_lower or file_lower.endswith(".css") or file_lower.endswith(".scss"):
                has_frontend_style = True
                break
        
        for pattern in BACKEND_PATTERNS:
            if pattern in file_lower:
                has_backend = True
                break
        
        ext = Path(file).suffix.lower()
        if ext in FRONTEND_EXTENSIONS and not has_backend:
            if ext in [".css", ".scss", ".less"]:
                has_frontend_style = True
            else:
                has_frontend_page = True
        
        if ext in BACKEND_EXTENSIONS:
            is_frontend_dir = any(
                p in file_lower for p in FRONTEND_COMPONENT_PATTERNS + FRONTEND_PAGE_PATTERNS
            )
            if not is_frontend_dir:
                has_backend = True
    
    return has_frontend_component, has_frontend_page, has_frontend_style, has_backend


def classify_verification_type_from_files(
    files: list[str],
    feature_description: str = "",
) -> ClassificationResult:
    """Classify verification type based on file changes.
    
    Args:
        files: List of changed files
        feature_description: Feature/task description for keyword analysis
        
    Returns:
        ClassificationResult with type and reasoning
    """
    has_frontend_component, has_frontend_page, has_frontend_style, has_backend = classify_files(files)
    
    detected_patterns = []
    
    if not files:
        detected_patterns.append("no_files")
        return ClassificationResult(
            verification_type=VerificationType.BACKEND_ONLY,
            confidence=0.9,
            detected_patterns=detected_patterns,
            reasoning="No files provided",
            files_analyzed=0,
        )
    
    only_docs = all(
        any(p in f.lower() for p in DOC_PATTERNS) or f.lower().endswith(".md")
        for f in files
    )
    only_tests = all(
        any(p in f.lower() for p in TEST_PATTERNS) or
        ".test." in f.lower() or ".spec." in f.lower() or "test_" in f.lower()
        for f in files
    )
    
    if only_docs:
        detected_patterns.append("docs_only")
        return ClassificationResult(
            verification_type=VerificationType.BACKEND_ONLY,
            confidence=0.95,
            detected_patterns=detected_patterns,
            reasoning="Only documentation files changed",
            files_analyzed=len(files),
        )
    
    if only_tests:
        detected_patterns.append("tests_only")
        return ClassificationResult(
            verification_type=VerificationType.BACKEND_ONLY,
            confidence=0.95,
            detected_patterns=detected_patterns,
            reasoning="Only test files changed",
            files_analyzed=len(files),
        )
    
    if not (has_frontend_component or has_frontend_page or has_frontend_style):
        if has_backend:
            detected_patterns.append("backend_only_files")
            return ClassificationResult(
                verification_type=VerificationType.BACKEND_ONLY,
                confidence=0.9,
                detected_patterns=detected_patterns,
                reasoning="No frontend files detected",
                files_analyzed=len(files),
            )
    
    if (has_frontend_component or has_frontend_page or has_frontend_style) and has_backend:
        detected_patterns.append("mixed_frontend_backend")
        return ClassificationResult(
            verification_type=VerificationType.MIXED_APP_WORKFLOW,
            confidence=0.85,
            detected_patterns=detected_patterns,
            reasoning="Both frontend and backend files changed",
            files_analyzed=len(files),
        )
    
    desc_lower = feature_description.lower()
    
    has_interactive_keywords = any(kw in desc_lower for kw in INTERACTIVE_KEYWORDS)
    has_visual_keywords = any(kw in desc_lower for kw in VISUAL_KEYWORDS)
    
    if has_frontend_style and not (has_frontend_component or has_frontend_page):
        detected_patterns.append("frontend_style_only")
        return ClassificationResult(
            verification_type=VerificationType.FRONTEND_VISUAL_BEHAVIOR,
            confidence=0.8,
            detected_patterns=detected_patterns,
            reasoning="Only frontend style files changed",
            files_analyzed=len(files),
        )
    
    if has_frontend_component:
        detected_patterns.append("frontend_component")
        if has_interactive_keywords:
            return ClassificationResult(
                verification_type=VerificationType.FRONTEND_INTERACTIVE,
                confidence=0.9,
                detected_patterns=detected_patterns + ["interactive_keywords"],
                reasoning="Frontend components with interactive keywords",
                files_analyzed=len(files),
            )
        return ClassificationResult(
            verification_type=VerificationType.FRONTEND_INTERACTIVE,
            confidence=0.7,
            detected_patterns=detected_patterns,
            reasoning="Frontend components detected, assuming interactive",
            files_analyzed=len(files),
        )
    
    if has_frontend_page:
        detected_patterns.append("frontend_page")
        if has_interactive_keywords:
            return ClassificationResult(
                verification_type=VerificationType.FRONTEND_INTERACTIVE,
                confidence=0.9,
                detected_patterns=detected_patterns + ["interactive_keywords"],
                reasoning="Frontend pages with interactive keywords",
                files_analyzed=len(files),
            )
        return ClassificationResult(
            verification_type=VerificationType.FRONTEND_INTERACTIVE,
            confidence=0.75,
            detected_patterns=detected_patterns,
            reasoning="Frontend pages detected, assuming interactive",
            files_analyzed=len(files),
        )
    
    detected_patterns.append("frontend_generic")
    return ClassificationResult(
        verification_type=VerificationType.FRONTEND_NONINTERACTIVE,
        confidence=0.6,
        detected_patterns=detected_patterns,
        reasoning="Frontend files detected but no clear interactive indicators",
        files_analyzed=len(files),
    )


def classify_verification_type_from_context(
    feature_spec: dict[str, Any] | None = None,
    execution_pack: dict[str, Any] | None = None,
    changed_files: list[str] | None = None,
) -> ClassificationResult:
    """Classify verification type from multiple context sources.
    
    Args:
        feature_spec: FeatureSpec dict
        execution_pack: ExecutionPack dict
        changed_files: List of changed files
        
    Returns:
        ClassificationResult with best available classification
    """
    description = ""
    files_to_analyze = changed_files or []
    
    if feature_spec:
        description = feature_spec.get("description", "")
        if not description:
            description = feature_spec.get("name", "")
        
        scope = feature_spec.get("scope", {})
        in_scope = scope.get("in_scope", [])
        for item in in_scope:
            if isinstance(item, str):
                description += " " + item
                if "/" in item or "." in item:
                    files_to_analyze.append(item)
    
    if execution_pack:
        goal = execution_pack.get("goal", "")
        task_scope = execution_pack.get("task_scope", [])
        
        if goal:
            description += " " + goal
        
        for item in task_scope:
            if isinstance(item, str):
                description += " " + item
                if "/" in item or "." in item:
                    files_to_analyze.append(item)
    
    if changed_files:
        files_to_analyze = list(set(files_to_analyze + changed_files))
    
    return classify_verification_type_from_files(files_to_analyze, description)


def get_verification_type(
    files: list[str] | None = None,
    feature_description: str = "",
    feature_spec: dict[str, Any] | None = None,
    execution_pack: dict[str, Any] | None = None,
) -> VerificationType:
    """Get verification type from available context.
    
    Convenience function returning just the type.
    
    Args:
        files: List of changed files
        feature_description: Feature/task description
        feature_spec: FeatureSpec dict
        execution_pack: ExecutionPack dict
        
    Returns:
        VerificationType enum value
    """
    if files:
        result = classify_verification_type_from_files(files, feature_description)
    else:
        result = classify_verification_type_from_context(
            feature_spec=feature_spec,
            execution_pack=execution_pack,
        )
    
    return result.verification_type