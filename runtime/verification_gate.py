"""Verification Gate - Interactive Frontend Verification Gate (Feature 038).

Provides classification and validation for browser-level verification requirements.
"""

from typing import Any

BROWSER_REQUIRED_TYPES = [
    "frontend_interactive",
    "frontend_visual_behavior",
    "mixed_app_workflow",
]

VALID_EXCEPTION_REASONS = [
    "playwright_unavailable",
    "environment_blocked",
    "browser_install_failed",
    "ci_container_limitation",
    "missing_credentials",
    "deterministic_blocker",
    "reclassified_noninteractive",
]


def requires_browser_verification(verification_type: str) -> bool:
    """Check if verification_type requires browser-level verification."""
    return verification_type in BROWSER_REQUIRED_TYPES


def is_valid_exception_reason(reason: str) -> bool:
    """Check if exception_reason is valid."""
    return reason in VALID_EXCEPTION_REASONS


def validate_browser_verification(
    verification_type: str,
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    """Validate browser_verification field for interactive frontend tasks.

    Returns validation result with status and details.
    """
    if not requires_browser_verification(verification_type):
        return {
            "valid": True,
            "reason": "Browser verification not required for this verification_type",
            "browser_required": False,
        }

    browser_verification = execution_result.get("browser_verification", {})
    executed = browser_verification.get("executed", False)
    exception_reason = browser_verification.get("exception_reason")

    if executed:
        return {
            "valid": True,
            "reason": "Browser verification executed",
            "browser_required": True,
            "passed": browser_verification.get("passed", 0),
            "failed": browser_verification.get("failed", 0),
        }

    if exception_reason and is_valid_exception_reason(exception_reason):
        return {
            "valid": True,
            "reason": f"Valid exception recorded: {exception_reason}",
            "browser_required": True,
            "exception": exception_reason,
        }

    return {
        "valid": False,
        "reason": "Browser verification required but not executed and no valid exception recorded",
        "browser_required": True,
        "missing": ["browser_verification.executed or browser_verification.exception_reason"],
    }


def get_completion_gate_status(
    verification_type: str,
    execution_result: dict[str, Any],
) -> str:
    """Get completion gate status for frontend-interactive tasks.

    Returns 'allowed' or 'blocked' based on FR-7 requirements.
    """
    validation = validate_browser_verification(verification_type, execution_result)

    if validation["valid"]:
        return "allowed"

    return "blocked"


def classify_verification_type(
    feature_description: str,
    task_scope: list[str],
) -> str:
    """Classify verification type based on feature/task characteristics.

    Heuristic classification for plan-day workflow.
    """
    frontend_keywords = [
        "ui", "ux", "frontend", "web", "page", "browser", "client",
        "component", "react", "vue", "angular", "svelte", "html", "css",
        "navigation", "click", "form", "button", "modal", "drawer",
        "animation", "visual", "interaction", "canvas", "map",
    ]

    interactive_keywords = [
        "click", "tap", "navigate", "form", "submit", "button",
        "modal", "drawer", "panel", "filter", "search", "sort",
        "drag", "drop", "gesture", "scroll", "swipe",
        "interaction", "user flow", "multi-step", "wizard",
    ]

    all_text = feature_description.lower()
    for scope_item in task_scope:
        all_text += " " + scope_item.lower()

    has_frontend = any(kw in all_text for kw in frontend_keywords)
    has_interactive = any(kw in all_text for kw in interactive_keywords)

    if not has_frontend:
        return "backend_only"

    if has_interactive:
        return "frontend_interactive"

    return "frontend_noninteractive"