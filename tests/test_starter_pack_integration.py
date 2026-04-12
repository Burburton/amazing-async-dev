"""Tests for starter pack consumer - advisor → async-dev integration."""

import pytest
import yaml
from pathlib import Path
from cli.starter_pack_consumer import (
    consume_starter_pack,
    format_product_brief_with_starter_pack,
    format_runstate_with_starter_pack,
    ConsumptionResult,
    SUPPORTED_CONTRACT_VERSIONS,
    MIN_ASYNCDEV_VERSION,
)


@pytest.fixture
def valid_starter_pack():
    return {
        "project_profile": {
            "summary": "solo AI tooling MVP - fast iteration",
            "product_type": "ai_tooling",
            "stage": "mvp",
            "team_mode": "solo",
        },
        "required_skills": ["nightly-summary", "decision-templates"],
        "optional_skills": ["limited-batch-ops"],
        "deferred_skills": ["multi-feature-concurrency"],
        "workflow_mode": {
            "execution": "external-tool-first",
            "review": "lightweight-summary",
            "planning": "archive-aware-planning",
            "archive": "minimal-archive",
            "ergonomics": "minimal-cli",
        },
        "workflow_defaults": {
            "policy_mode_hint": "balanced",
            "review_automation": True,
            "archive_on_complete": False,
            "decision_handling": "pause_for_human",
        },
        "rationale": ["Fast iteration matters.", "External tool mode critical."],
        "integration_metadata": {
            "contract_version": "1.0",
            "starter_pack_version": "2.0",
            "advisor_version": "v1.0.0",
            "generated_at": "2026-04-12T10:00:00Z",
        },
        "asyncdev_compatibility": {
            "compatible": True,
            "minimum_version": "v0.19.0",
            "recommended_version": "v0.21.0",
            "compatibility_notes": [],
            "incompatible_fields": [],
        },
        "notes": "Consider enabling batch-ops after MVP.",
    }


@pytest.fixture
def pilot_starter_pack_path():
    return Path("examples/pilot/pilot-starter-pack.yaml")


class TestConsumeStarterPack:
    """Tests for consume_starter_pack function."""

    def test_consume_valid_starter_pack(self, valid_starter_pack, tmp_path):
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        result = consume_starter_pack(str(pack_path))

        assert result.success is True
        assert result.error is None
        assert "problem_prefix" in result.product_brief_fields
        assert result.product_brief_fields["product_type"] == "ai_tooling"
        assert result.runstate_hints["policy_mode_hint"] == "balanced"

    def test_consume_missing_file(self):
        result = consume_starter_pack("/nonexistent/path.yaml")

        assert result.success is False
        assert "not found" in result.error

    def test_consume_invalid_yaml(self, tmp_path):
        pack_path = tmp_path / "invalid.yaml"
        pack_path.write_text("invalid: yaml: content:")

        result = consume_starter_pack(str(pack_path))

        assert result.success is False
        assert "Invalid YAML" in result.error

    def test_consume_empty_file(self, tmp_path):
        pack_path = tmp_path / "empty.yaml"
        pack_path.write_text("")

        result = consume_starter_pack(str(pack_path))

        assert result.success is False
        assert "Empty" in result.error

    def test_consume_unsupported_contract_version(self, valid_starter_pack, tmp_path):
        valid_starter_pack["integration_metadata"]["contract_version"] = "99.0"
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        result = consume_starter_pack(str(pack_path))

        assert result.success is False
        assert "Unsupported contract version" in result.error

    def test_consume_incompatible_pack(self, valid_starter_pack, tmp_path):
        valid_starter_pack["asyncdev_compatibility"]["compatible"] = False
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        result = consume_starter_pack(str(pack_path))

        assert result.success is False
        assert "incompatible" in result.error

    def test_consume_version_warning(self, valid_starter_pack, tmp_path):
        valid_starter_pack["asyncdev_compatibility"]["minimum_version"] = "v99.0.0"
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        result = consume_starter_pack(str(pack_path))

        assert result.success is True
        assert len(result.warnings) > 0
        assert "recommends" in result.warnings[0]

    def test_consume_incompatible_fields_warning(self, valid_starter_pack, tmp_path):
        valid_starter_pack["asyncdev_compatibility"]["incompatible_fields"] = [
            "future_field"
        ]
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        result = consume_starter_pack(str(pack_path))

        assert result.success is True
        assert len(result.warnings) > 0
        assert "not supported" in result.warnings[-1]

    def test_consume_pilot_starter_pack(self, pilot_starter_pack_path):
        if not pilot_starter_pack_path.exists():
            pytest.skip("Pilot starter pack not found")

        result = consume_starter_pack(str(pilot_starter_pack_path))

        assert result.success is True
        assert result.product_brief_fields["product_type"] == "ai_tooling"
        assert result.runstate_hints["policy_mode_hint"] == "balanced"
        assert result.advisory_context.get("rationale") is not None


class TestFieldMapping:
    """Tests for field mapping functions."""

    def test_format_product_brief_with_starter_pack(self, valid_starter_pack, tmp_path):
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        consumption = consume_starter_pack(str(pack_path))

        base_brief = {
            "product_id": "test-product",
            "name": "Test Product",
            "problem": "Test problem statement",
        }

        enhanced = format_product_brief_with_starter_pack(base_brief, consumption)

        assert consumption.success
        assert "solo AI tooling MVP" in enhanced["problem"]
        assert "starter_pack_context" in enhanced
        assert "Product type: ai_tooling" in enhanced["starter_pack_context"]

    def test_format_product_brief_without_summary(self, valid_starter_pack, tmp_path):
        valid_starter_pack["project_profile"]["summary"] = ""
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        consumption = consume_starter_pack(str(pack_path))
        base_brief = {"problem": "Original problem"}

        enhanced = format_product_brief_with_starter_pack(base_brief, consumption)

        assert enhanced["problem"] == "Original problem"

    def test_format_runstate_with_starter_pack(self, valid_starter_pack, tmp_path):
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        consumption = consume_starter_pack(str(pack_path))

        base_runstate = {
            "product_id": "test",
            "current_phase": "planning",
        }

        enhanced = format_runstate_with_starter_pack(base_runstate, consumption)

        assert consumption.success
        assert "workflow_hints" in enhanced
        assert enhanced["workflow_hints"]["policy_mode"] == "balanced"
        assert enhanced["workflow_hints"]["execution"] == "external-tool-first"

    def test_format_runstate_preserves_base_fields(
        self, valid_starter_pack, tmp_path
    ):
        pack_path = tmp_path / "starter-pack.yaml"
        with open(pack_path, "w") as f:
            yaml.dump(valid_starter_pack, f)

        consumption = consume_starter_pack(str(pack_path))

        base_runstate = {
            "product_id": "test",
            "current_phase": "executing",
            "last_action": "custom action",
        }

        enhanced = format_runstate_with_starter_pack(base_runstate, consumption)

        assert enhanced["product_id"] == "test"
        assert enhanced["current_phase"] == "executing"
        assert enhanced["last_action"] == "custom action"


class TestContractValidation:
    """Tests for contract version validation."""

    def test_supported_contract_versions(self):
        assert "1.0" in SUPPORTED_CONTRACT_VERSIONS

    def test_min_asyncdev_version_defined(self):
        assert MIN_ASYNCDEV_VERSION.startswith("v")


class TestIntegrationEndToEnd:
    """End-to-end integration tests using pilot artifacts."""

    def test_pilot_starter_pack_consumption(self, pilot_starter_pack_path):
        if not pilot_starter_pack_path.exists():
            pytest.skip("Pilot starter pack not found")

        result = consume_starter_pack(str(pilot_starter_pack_path))

        assert result.success is True

        assert result.product_brief_fields["product_type"] == "ai_tooling"
        assert result.product_brief_fields["stage"] == "mvp"
        assert result.product_brief_fields["team_mode"] == "solo"

        assert result.runstate_hints["policy_mode_hint"] == "balanced"
        assert result.runstate_hints["execution_mode"] == "external-tool-first"
        assert result.runstate_hints["review_mode"] == "lightweight-summary"

        assert len(result.advisory_context.get("rationale", [])) >= 1

    def test_pilot_product_brief_enhancement(self, pilot_starter_pack_path):
        if not pilot_starter_pack_path.exists():
            pytest.skip("Pilot starter pack not found")

        consumption = consume_starter_pack(str(pilot_starter_pack_path))

        base_brief = {
            "product_id": "pilot-ai-tool",
            "name": "Pilot AI Tool",
            "problem": "Building an AI workflow tool",
            "target_user": "Solo builders",
            "core_value": "Fast iteration",
            "constraints": ["Limited time"],
            "success_signal": "Working MVP",
        }

        enhanced = format_product_brief_with_starter_pack(base_brief, consumption)

        assert "AI tooling" in enhanced["problem"]
        assert "starter_pack_context" in enhanced
        assert any("ai_tooling" in ctx for ctx in enhanced["starter_pack_context"])

    def test_pilot_runstate_enhancement(self, pilot_starter_pack_path):
        if not pilot_starter_pack_path.exists():
            pytest.skip("Pilot starter pack not found")

        consumption = consume_starter_pack(str(pilot_starter_pack_path))

        base_runstate = {
            "product_id": "pilot-ai-tool",
            "current_phase": "planning",
        }

        enhanced = format_runstate_with_starter_pack(base_runstate, consumption)

        assert enhanced["workflow_hints"]["policy_mode"] == "balanced"
        assert enhanced["workflow_hints"]["execution"] == "external-tool-first"
        assert enhanced["workflow_hints"]["planning"] == "archive-aware-planning"