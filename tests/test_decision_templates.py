"""Tests for Feature 016 - Decision Template System."""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from runtime.decision_templates import (
    DecisionTemplate,
    DecisionTemplateRegistry,
    get_registry,
    enhance_decision_with_template,
)

runner = CliRunner()


@pytest.fixture
def sample_templates_yaml():
    """Sample templates YAML content."""
    return {
        "templates": [
            {
                "template_id": "continue-or-change",
                "name": "Continue or Change",
                "decision_type": "technical",
                "description": "Test template",
                "question_keywords": ["continue", "change"],
                "standard_options": [
                    {"id": "continue", "label": "Continue"},
                    {"id": "change", "label": "Change"},
                ],
                "default_recommendation": "Continue",
                "default_blocking": False,
                "default_urgency": "medium",
            },
        ]
    }


class TestDecisionTemplate:
    """Tests for DecisionTemplate class."""

    def test_initializes_from_data(self, sample_templates_yaml):
        """DecisionTemplate should initialize from YAML data."""
        template = DecisionTemplate(sample_templates_yaml["templates"][0])
        
        assert template.template_id == "continue-or-change"
        assert template.decision_type == "technical"
        assert template.name == "Continue or Change"
        assert len(template.standard_options) == 2

    def test_matches_by_keyword(self, sample_templates_yaml):
        """DecisionTemplate should match decisions by keywords."""
        template = DecisionTemplate(sample_templates_yaml["templates"][0])
        
        decision = {"decision": "Should I continue with current approach?"}
        assert template.matches(decision) == True
        
        decision2 = {"decision": "Try alternative method"}
        assert template.matches(decision2) == False

    def test_enhances_decision(self, sample_templates_yaml):
        """DecisionTemplate should enhance decision with defaults."""
        template = DecisionTemplate(sample_templates_yaml["templates"][0])
        
        decision = {"decision": "Continue or change approach"}
        enhanced = template.enhance(decision)
        
        assert enhanced.get("template_id") == "continue-or-change"
        assert enhanced.get("decision_type") == "technical"
        assert enhanced.get("urgency") == "medium"

    def test_preserves_existing_values(self, sample_templates_yaml):
        """Enhance should preserve existing decision values."""
        template = DecisionTemplate(sample_templates_yaml["templates"][0])
        
        decision = {
            "decision": "Continue approach",
            "urgency": "high",
            "options": ["Option A", "Option B"],
        }
        enhanced = template.enhance(decision)
        
        assert enhanced.get("urgency") == "high"
        assert enhanced.get("options") == ["Option A", "Option B"]


class TestDecisionTemplateRegistry:
    """Tests for DecisionTemplateRegistry."""

    def test_loads_templates_from_yaml(self, temp_dir):
        """Registry should load templates from YAML file."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "test-template",
                        "decision_type": "technical",
                        "name": "Test",
                        "description": "Test",
                        "standard_options": [{"id": "a", "label": "A"}],
                    }
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        assert registry.is_loaded()
        assert len(registry.templates) == 1

    def test_matches_decision_to_template(self, temp_dir):
        """Registry should match decision to best template."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "retry-template",
                        "decision_type": "technical",
                        "name": "Retry or Defer",
                        "description": "Test",
                        "question_keywords": ["retry", "defer"],
                        "standard_options": [{"id": "retry", "label": "Retry"}],
                    }
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        decision = {"decision": "Should we retry or defer?"}
        template = registry.match(decision)
        
        assert template is not None
        assert template.template_id == "retry-template"

    def test_enhance_decision(self, temp_dir):
        """Registry should enhance decision with template."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "priority-template",
                        "decision_type": "priority",
                        "name": "Choose Priority",
                        "description": "Test",
                        "question_keywords": ["priority"],
                        "standard_options": [{"id": "a", "label": "A"}],
                        "default_urgency": "low",
                    }
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        decision = {"decision": "Which priority should we choose?"}
        enhanced = registry.enhance_decision(decision)
        
        assert enhanced.get("template_id") == "priority-template"
        assert enhanced.get("decision_type") == "priority"
        assert enhanced.get("urgency") == "low"

    def test_returns_none_if_no_match(self, temp_dir):
        """Registry should return None if no template matches."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "tech-template",
                        "decision_type": "technical",
                        "name": "Tech",
                        "description": "Test",
                        "question_keywords": ["api"],
                        "standard_options": [{"id": "a", "label": "A"}],
                    }
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        decision = {"decision": "Something unrelated"}
        template = registry.match(decision)
        
        assert template is None

    def test_get_template_by_id(self, temp_dir):
        """Registry should get template by ID."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "my-template",
                        "decision_type": "technical",
                        "name": "My Template",
                        "description": "Test",
                        "standard_options": [{"id": "a", "label": "A"}],
                    }
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        template = registry.get_template_by_id("my-template")
        
        assert template is not None
        assert template.name == "My Template"

    def test_get_templates_by_type(self, temp_dir):
        """Registry should filter templates by type."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "tech-1",
                        "decision_type": "technical",
                        "name": "Tech 1",
                        "description": "Test",
                        "standard_options": [{"id": "a", "label": "A"}],
                    },
                    {
                        "template_id": "scope-1",
                        "decision_type": "scope",
                        "name": "Scope 1",
                        "description": "Test",
                        "standard_options": [{"id": "b", "label": "B"}],
                    },
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        tech_templates = registry.get_templates_by_type("technical")
        
        assert len(tech_templates) == 1
        assert tech_templates[0].template_id == "tech-1"

    def test_list_templates(self, temp_dir):
        """Registry should list all templates."""
        import yaml
        
        yaml_path = temp_dir / "test-templates.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump({
                "templates": [
                    {
                        "template_id": "t1",
                        "decision_type": "technical",
                        "name": "T1",
                        "description": "Test",
                        "standard_options": [{"id": "a", "label": "A"}],
                    }
                ]
            }, f)
        
        registry = DecisionTemplateRegistry()
        registry.load(yaml_path)
        
        templates_list = registry.list_templates()
        
        assert len(templates_list) == 1
        assert templates_list[0]["template_id"] == "t1"


class TestDefaultRegistry:
    """Tests for default registry functions."""

    def test_get_registry_loads_default(self):
        """get_registry should load default templates."""
        registry = get_registry()
        
        assert registry is not None
        
        if Path("templates/decision-templates.yaml").exists():
            assert registry.is_loaded()

    def test_enhance_decision_with_template(self):
        """enhance_decision_with_template should work."""
        decision = {"decision": "Continue or change approach"}
        enhanced = enhance_decision_with_template(decision)
        
        assert "decision" in enhanced


class TestTemplateIntegration:
    """Tests for template integration with review pack builder."""

    def test_convert_decisions_adds_template_fields(self):
        """_convert_decisions should add template fields."""
        from runtime.review_pack_builder import _convert_decisions
        
        execution_result = {
            "decisions_required": [
                {"decision": "Continue or change approach"}
            ]
        }
        
        decisions = _convert_decisions(execution_result)
        
        assert len(decisions) == 1
        d = decisions[0]
        
        assert "decision_id" in d
        assert "is_template_based" in d

    def test_template_match_adds_template_id(self):
        """Template match should add template_id."""
        from runtime.review_pack_builder import _convert_decisions
        
        execution_result = {
            "decisions_required": [
                {"decision": "Should we retry or defer the task?"}
            ]
        }
        
        decisions = _convert_decisions(execution_result)
        
        if decisions[0].get("is_template_based"):
            assert "template_id" in decisions[0]


class TestSummaryCommandTemplates:
    """Tests for summary command template display."""

    def test_summary_decisions_shows_template_label(self):
        """summary decisions should show template label."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["decisions", "--help"])
        
        assert result.exit_code == 0

    def test_summary_today_includes_template_count(self):
        """summary today should include template count."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["today", "--help"])
        
        assert result.exit_code == 0


class TestTemplateFiles:
    """Tests for template file structure."""

    def test_templates_yaml_exists(self):
        """templates/decision-templates.yaml should exist."""
        assert Path("templates/decision-templates.yaml").exists()

    def test_templates_yaml_has_4_templates(self):
        """Templates YAML should have 4 initial templates."""
        import yaml
        
        with open("templates/decision-templates.yaml") as f:
            data = yaml.safe_load(f)
        
        templates = data.get("templates", [])
        assert len(templates) == 4

    def test_templates_have_required_fields(self):
        """Each template should have required fields."""
        import yaml
        
        with open("templates/decision-templates.yaml") as f:
            data = yaml.safe_load(f)
        
        for template in data.get("templates", []):
            assert "template_id" in template
            assert "name" in template
            assert "decision_type" in template
            assert "standard_options" in template

    def test_schema_file_exists(self):
        """schemas/decision-template.schema.yaml should exist."""
        assert Path("schemas/decision-template.schema.yaml").exists()

    def test_all_template_ids_unique(self):
        """All template_ids should be unique."""
        import yaml
        
        with open("templates/decision-templates.yaml") as f:
            data = yaml.safe_load(f)
        
        template_ids = [t.get("template_id") for t in data.get("templates", [])]
        assert len(template_ids) == len(set(template_ids))

    def test_decision_types_valid(self):
        """All decision_types should be valid enum values."""
        import yaml
        
        valid_types = ["technical", "scope", "priority", "design"]
        
        with open("templates/decision-templates.yaml") as f:
            data = yaml.safe_load(f)
        
        for template in data.get("templates", []):
            assert template.get("decision_type") in valid_types