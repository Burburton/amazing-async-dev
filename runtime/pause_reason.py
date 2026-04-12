"""Structured pause reason model for workflow interruption display."""

from dataclasses import dataclass
from enum import Enum


class PauseCategory(str, Enum):
    """Categories of workflow pause reasons."""
    
    DECISION_REQUIRED = "decision_required"
    BLOCKER = "blocker"
    RISKY_ACTION = "risky_action"
    SCOPE_CHANGE = "scope_change"
    POLICY_BOUNDARY = "policy_boundary"


PAUSE_CATEGORY_DISPLAY = {
    PauseCategory.DECISION_REQUIRED: {
        "label": "Decision Required",
        "color": "yellow",
        "urgency": "high",
        "icon": "⚠",
    },
    PauseCategory.BLOCKER: {
        "label": "Blocked",
        "color": "red",
        "urgency": "critical",
        "icon": "🔴",
    },
    PauseCategory.RISKY_ACTION: {
        "label": "Risky Action",
        "color": "magenta",
        "urgency": "high",
        "icon": "⚡",
    },
    PauseCategory.SCOPE_CHANGE: {
        "label": "Scope Change",
        "color": "orange",
        "urgency": "medium",
        "icon": "↔",
    },
    PauseCategory.POLICY_BOUNDARY: {
        "label": "Policy Boundary",
        "color": "blue",
        "urgency": "low",
        "icon": "📋",
    },
}


@dataclass
class PauseReason:
    """Structured pause reason for workflow interruption.
    
    Required fields per Feature 020 spec:
    - category: PauseCategory enum
    - summary: Short description
    - why: Explanation of why pause happened
    - required_to_continue: What must happen before continuation
    - suggested_next_action: CLI command suggestion
    """
    
    category: PauseCategory
    summary: str
    why: str
    required_to_continue: str
    suggested_next_action: str
    
    def get_display_info(self) -> dict:
        """Get display information for this pause category."""
        return PAUSE_CATEGORY_DISPLAY.get(self.category, {
            "label": self.category.value,
            "color": "white",
            "urgency": "unknown",
            "icon": "?",
        })
    
    def format_for_cli(self) -> str:
        """Format pause reason for CLI display."""
        info = self.get_display_info()
        lines = [
            f"[{info['color']}]{info['icon']} {info['label']}[/{info['color']}]",
            f"  Summary: {self.summary}",
            f"  Why: {self.why}",
            f"  Required: {self.required_to_continue}",
            f"  Suggested: {self.suggested_next_action}",
        ]
        return "\n".join(lines)
    
    def format_for_yaml(self) -> dict:
        """Format pause reason for YAML artifact."""
        return {
            "category": self.category.value,
            "summary": self.summary,
            "why": self.why,
            "required_to_continue": self.required_to_continue,
            "suggested_next_action": self.suggested_next_action,
            "display": self.get_display_info(),
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "summary": self.summary,
            "why": self.why,
            "required_to_continue": self.required_to_continue,
            "suggested_next_action": self.suggested_next_action,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PauseReason":
        """Create from dictionary."""
        return cls(
            category=PauseCategory(data.get("category", "policy_boundary")),
            summary=data.get("summary", ""),
            why=data.get("why", ""),
            required_to_continue=data.get("required_to_continue", ""),
            suggested_next_action=data.get("suggested_next_action", ""),
        )


def format_pause_reasons_table(pause_reasons: list[PauseReason]) -> str:
    """Format multiple pause reasons as a table."""
    if not pause_reasons:
        return "No pause reasons"
    
    lines = ["[bold]Workflow Paused[bold]", ""]
    for reason in pause_reasons:
        info = reason.get_display_info()
        lines.append(f"[{info['color']}]{info['icon']} {info['label']}[/{info['color']}]")
        lines.append(f"  {reason.summary}")
        lines.append(f"  → {reason.suggested_next_action}")
        lines.append("")
    
    return "\n".join(lines)