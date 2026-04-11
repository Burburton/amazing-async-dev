"""Decision template registry for structured decision handling.

Feature 016: Decision Template System

This module provides:
- DecisionTemplateRegistry: Load and match decision templates
- Template-based decision enhancement
- Consistent decision structure for common scenarios
"""

from pathlib import Path
from typing import Any

import yaml


class DecisionTemplate:
    """Represents a reusable decision template."""

    def __init__(self, template_data: dict[str, Any]) -> None:
        self.template_id = template_data.get("template_id", "")
        self.decision_type = template_data.get("decision_type", "technical")
        self.name = template_data.get("name", "")
        self.description = template_data.get("description", "")
        self.question_pattern = template_data.get("question_pattern", "")
        self.question_keywords = template_data.get("question_keywords", [])
        self.standard_options = template_data.get("standard_options", [])
        self.default_recommendation = template_data.get("default_recommendation", "")
        self.recommendation_logic = template_data.get("recommendation_logic", "")
        self.default_blocking = template_data.get("default_blocking", False)
        self.default_defer_impact = template_data.get("default_defer_impact", "")
        self.default_urgency = template_data.get("default_urgency", "medium")

    def matches(self, decision: dict[str, Any]) -> bool:
        """Check if this template matches a decision."""
        decision_text = decision.get("decision", "").lower()
        context = decision.get("context", "").lower()

        if self.question_keywords:
            for kw in self.question_keywords:
                if kw.lower() in decision_text or kw.lower() in context:
                    return True

        if self.question_pattern:
            pattern_lower = self.question_pattern.lower()
            if pattern_lower in decision_text:
                return True

        return False

    def enhance(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Enhance a decision with template defaults."""
        enhanced = decision.copy()

        enhanced["template_id"] = self.template_id
        enhanced["template_name"] = self.name

        if not decision.get("decision_type"):
            enhanced["decision_type"] = self.decision_type

        if not decision.get("options") and self.standard_options:
            enhanced["options"] = [opt.get("label", opt.get("id", "")) for opt in self.standard_options]

        if not decision.get("recommendation"):
            enhanced["recommendation"] = self.default_recommendation

        if not decision.get("urgency"):
            enhanced["urgency"] = self.default_urgency

        if "blocking_tomorrow" not in decision:
            enhanced["blocking_tomorrow"] = self.default_blocking

        if not decision.get("defer_impact"):
            enhanced["defer_impact"] = self.default_defer_impact

        return enhanced


class DecisionTemplateRegistry:
    """Registry for loading and matching decision templates."""

    def __init__(self, templates_path: Path | None = None) -> None:
        self.templates: list[DecisionTemplate] = []
        self._loaded = False

        if templates_path:
            self.load(templates_path)

    def load(self, templates_path: Path) -> None:
        """Load templates from YAML file."""
        if not templates_path.exists():
            return

        with open(templates_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        templates_data = data.get("templates", [])
        for template_data in templates_data:
            self.templates.append(DecisionTemplate(template_data))

        self._loaded = True

    def load_default(self) -> None:
        """Load default templates from templates/decision-templates.yaml."""
        default_path = Path("templates/decision-templates.yaml")
        if default_path.exists():
            self.load(default_path)

    def match(self, decision: dict[str, Any]) -> DecisionTemplate | None:
        """Find best matching template for a decision."""
        for template in self.templates:
            if template.matches(decision):
                return template

        return None

    def enhance_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Enhance a decision with matching template."""
        template = self.match(decision)

        if template:
            return template.enhance(decision)

        return decision

    def enhance_decisions(self, decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enhance multiple decisions with templates."""
        return [self.enhance_decision(d) for d in decisions]

    def get_template_by_id(self, template_id: str) -> DecisionTemplate | None:
        """Get template by ID."""
        for template in self.templates:
            if template.template_id == template_id:
                return template

        return None

    def get_templates_by_type(self, decision_type: str) -> list[DecisionTemplate]:
        """Get all templates of a specific type."""
        return [t for t in self.templates if t.decision_type == decision_type]

    def list_templates(self) -> list[dict[str, Any]]:
        """List all templates with summary info."""
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "decision_type": t.decision_type,
                "description": t.description,
            }
            for t in self.templates
        ]

    def is_loaded(self) -> bool:
        """Check if templates have been loaded."""
        return self._loaded


_default_registry: DecisionTemplateRegistry | None = None


def get_registry() -> DecisionTemplateRegistry:
    """Get the default template registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = DecisionTemplateRegistry()
        _default_registry.load_default()

    return _default_registry


def enhance_decision_with_template(decision: dict[str, Any]) -> dict[str, Any]:
    """Enhance a single decision using default registry."""
    global _default_registry
    registry = get_registry()
    return registry.enhance_decision(decision)


def enhance_decisions_with_templates(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enhance multiple decisions using default registry."""
    global _default_registry
    registry = get_registry()
    return registry.enhance_decisions(decisions)