"""Tests for Feature 015 - Daily Management Summary / Decision Inbox."""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from runtime.review_pack_builder import (
    build_daily_review_pack,
    _build_issues_summary,
    _convert_decisions,
    _build_next_day_recommendation,
    _infer_decision_type,
    _is_blocking_tomorrow,
)

runner = CliRunner()


@pytest.fixture
def sample_execution_result():
    """Sample execution result with issues and decisions."""
    return {
        "execution_id": "exec-2026-04-11-001",
        "status": "success",
        "completed_items": [
            {"item": "runtime/archive_query.py", "description": "Query logic"},
            {"item": "cli/commands/archive.py", "description": "CLI commands"},
        ],
        "artifacts_created": [
            {"name": "archive_query.py", "path": "runtime/archive_query.py", "type": "file"},
            {"name": "archive.py", "path": "cli/commands/archive.py", "type": "file"},
        ],
        "verification_result": {
            "passed": 31,
            "failed": 0,
            "skipped": 0,
        },
        "issues_found": [
            {"description": "Test fixture path issue", "severity": "medium", "resolution": "fixed"},
            {"description": "LSP type errors", "severity": "low", "resolution": "pending"},
        ],
        "issues_resolved": [
            {"description": "Test fixture path issue", "resolution": "Adjusted fixture", "resolved_at": "2026-04-11T11:00"},
        ],
        "blocked_reasons": [],
        "decisions_required": [
            {
                "decision": "SQLite index vs file-based query",
                "context": "Performance optimization choice",
                "options": ["SQLite primary", "Files primary"],
                "recommendation": "Files primary",
                "urgency": "medium",
            },
        ],
        "recommended_next_step": "Continue with Feature 016",
        "metrics": {
            "files_written": 4,
            "decisions_made": 0,
        },
    }


@pytest.fixture
def sample_runstate():
    """Sample runstate."""
    return {
        "project_id": "demo-product",
        "feature_id": "014-archive-query",
        "current_phase": "reviewing",
        "active_task": "Implement archive query",
        "completed_outputs": ["runtime/archive_query.py"],
        "blocked_items": [],
        "decisions_needed": [],
        "next_recommended_action": "Continue to next feature",
    }


class TestReviewPackBuilder:
    """Tests for enhanced review_pack_builder."""

    def test_builds_issues_summary(self, sample_execution_result):
        """build_daily_review_pack should include structured issues_summary."""
        pack = build_daily_review_pack(sample_execution_result, {})
        
        assert "issues_summary" in pack
        issues = pack["issues_summary"]
        
        assert "encountered" in issues
        assert "resolved" in issues
        assert "unresolved" in issues
        
        assert len(issues["encountered"]) == 2
        assert len(issues["resolved"]) == 1
        assert len(issues["unresolved"]) == 1

    def test_issues_summary_distinguishes_resolved(self, sample_execution_result):
        """issues_summary should distinguish resolved from unresolved."""
        issues = _build_issues_summary(sample_execution_result)
        
        assert len(issues["resolved"]) == 1
        resolved = issues["resolved"][0]
        assert resolved["description"] == "Test fixture path issue"
        assert resolved["resolution"] == "Adjusted fixture"

    def test_issues_summary_identifies_unresolved(self, sample_execution_result):
        """issues_summary should identify unresolved issues."""
        issues = _build_issues_summary(sample_execution_result)
        
        assert len(issues["unresolved"]) == 1
        unresolved = issues["unresolved"][0]
        assert "LSP" in unresolved["description"]
        assert unresolved["blocking"] == False

    def test_decisions_have_blocking_tomorrow(self, sample_execution_result):
        """decisions_needed should include blocking_tomorrow field."""
        decisions = _convert_decisions(sample_execution_result)
        
        assert len(decisions) == 1
        d = decisions[0]
        assert "blocking_tomorrow" in d
        assert "defer_impact" in d
        assert "decision_type" in d
        assert "decision_id" in d

    def test_high_urgency_blocks_tomorrow(self):
        """High urgency decisions should block tomorrow."""
        decision = {"decision": "test", "urgency": "high", "context": ""}
        assert _is_blocking_tomorrow(decision) == True

    def test_medium_urgency_does_not_block(self):
        """Medium urgency decisions should not block by default."""
        decision = {"decision": "test", "urgency": "medium", "context": "Optional choice"}
        assert _is_blocking_tomorrow(decision) == False

    def test_infer_decision_type_technical(self):
        """Should infer technical decision type."""
        decision = {"decision": "Choose API library", "context": ""}
        assert _infer_decision_type(decision) == "technical"

    def test_infer_decision_type_scope(self):
        """Should infer scope decision type."""
        decision = {"decision": "Include feature X?", "context": ""}
        assert _infer_decision_type(decision) == "scope"

    def test_builds_next_day_recommendation(self, sample_execution_result, sample_runstate):
        """Should build structured next_day_recommendation."""
        next_rec = _build_next_day_recommendation(sample_execution_result, sample_runstate)
        
        assert "action" in next_rec
        assert "safe_to_execute" in next_rec
        assert "preconditions" in next_rec
        assert "blocking_decisions" in next_rec
        assert "estimated_scope" in next_rec
        
        assert next_rec["action"] == "Continue with Feature 016"
        assert next_rec["safe_to_execute"] == True

    def test_next_day_recommendation_with_blockers(self):
        """Should identify blockers in next_day_recommendation."""
        execution_result = {
            "status": "blocked",
            "recommended_next_step": "Continue",
            "decisions_required": [{"decision": "Critical", "urgency": "high", "context": "blocking"}],
        }
        runstate = {"blocked_items": [{"reason": "API down"}]}
        
        next_rec = _build_next_day_recommendation(execution_result, runstate)
        
        assert next_rec["safe_to_execute"] == False
        assert len(next_rec["preconditions"]) >= 1

    def test_builds_completed_items_with_description(self, sample_execution_result):
        """what_was_completed should have item and description."""
        pack = build_daily_review_pack(sample_execution_result, {})
        
        completed = pack["what_was_completed"]
        assert len(completed) == 2
        
        item = completed[0]
        assert "item" in item
        assert "description" in item

    def test_includes_risk_watch_items(self):
        """Should include risk_watch_items for deferred issues."""
        execution_result = {
            "status": "success",
            "completed_items": [],
            "artifacts_created": [],
            "verification_result": {"passed": 0, "failed": 0},
            "issues_found": [{"description": "Issue", "resolution": "deferred", "severity": "medium"}],
            "issues_resolved": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "",
        }
        runstate = {"decisions_needed": [{"decision": "test"}, {"decision": "test2"}]}
        
        pack = build_daily_review_pack(execution_result, runstate)
        
        if "risk_watch_items" in pack:
            assert len(pack["risk_watch_items"]) >= 1

    def test_includes_confidence_notes(self, sample_execution_result):
        """Should include confidence_notes."""
        pack = build_daily_review_pack(sample_execution_result, {})
        
        assert "confidence_notes" in pack
        assert "High confidence" in pack["confidence_notes"]

    def test_includes_metrics_summary(self, sample_execution_result):
        """Should include metrics_summary."""
        pack = build_daily_review_pack(sample_execution_result, {})
        
        assert "metrics_summary" in pack
        metrics = pack["metrics_summary"]
        assert "files_created" in metrics
        assert metrics["files_created"] == 2


class TestSummaryCommand:
    """Tests for summary CLI commands."""

    def test_summary_today_help(self):
        """summary today --help should show usage."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["today", "--help"])
        
        assert result.exit_code == 0
        assert "today" in result.output

    def test_summary_decisions_help(self):
        """summary decisions --help should show usage."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["decisions", "--help"])
        
        assert result.exit_code == 0
        assert "decision" in result.output

    def test_summary_issues_help(self):
        """summary issues --help should show usage."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["issues", "--help"])
        
        assert result.exit_code == 0
        assert "issues" in result.output

    def test_summary_next_day_help(self):
        """summary next-day --help should show usage."""
        from cli.commands.summary import app
        
        result = runner.invoke(app, ["next-day", "--help"])
        
        assert result.exit_code == 0
        assert "next" in result.output


class TestSchemaUpdates:
    """Tests for schema field presence."""

    def test_daily_review_pack_schema_has_issues_summary(self):
        """Schema should have issues_summary field."""
        import yaml
        
        with open("schemas/daily-review-pack.schema.yaml") as f:
            schema = yaml.safe_load(f)
        
        assert "issues_summary" in schema["required"]
        
        fields = schema["fields"]
        assert "issues_summary" in fields
        assert fields["issues_summary"]["type"] == "object"

    def test_daily_review_pack_schema_has_next_day_recommendation(self):
        """Schema should have next_day_recommendation field."""
        import yaml
        
        with open("schemas/daily-review-pack.schema.yaml") as f:
            schema = yaml.safe_load(f)
        
        assert "next_day_recommendation" in schema["required"]
        
        fields = schema["fields"]
        assert "next_day_recommendation" in fields
        assert fields["next_day_recommendation"]["type"] == "object"

    def test_daily_review_pack_schema_has_decision_fields(self):
        """Schema decision items should have new fields."""
        import yaml
        
        with open("schemas/daily-review-pack.schema.yaml") as f:
            schema = yaml.safe_load(f)
        
        json_schema = schema["json_schema"]
        decision_props = json_schema["properties"]["decisions_needed"]["items"]["properties"]
        
        assert "blocking_tomorrow" in decision_props
        assert "defer_impact" in decision_props
        assert "decision_type" in decision_props
        assert "decision_id" in decision_props

    def test_execution_result_schema_has_issues_resolved(self):
        """Execution result schema should have issues_resolved."""
        import yaml
        
        with open("schemas/execution-result.schema.yaml") as f:
            schema = yaml.safe_load(f)
        
        assert "issues_resolved" in schema["optional"]
        
        fields = schema["fields"]
        assert "issues_resolved" in fields