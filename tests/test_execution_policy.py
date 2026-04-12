"""Tests for execution policy engine (Feature 020)."""

import pytest
from pathlib import Path
import tempfile
import shutil

from runtime.execution_policy import (
    PolicyMode,
    ActionType,
    should_auto_continue,
    check_must_pause_conditions,
    get_policy_mode,
    set_policy_mode,
    set_scope_change_flag,
    register_risky_action,
    clear_risky_action,
    is_risky_action,
    can_auto_proceed_after_execution,
    RISKY_ACTION_TYPES,
    DEFAULT_POLICY_MODE,
)
from runtime.pause_reason import PauseReason, PauseCategory


class TestPolicyMode:
    """Tests for PolicyMode enum."""

    def test_policy_mode_values(self):
        """PolicyMode should have expected values."""
        assert PolicyMode.CONSERVATIVE.value == "conservative"
        assert PolicyMode.BALANCED.value == "balanced"
        assert PolicyMode.LOW_INTERRUPTION.value == "low_interruption"

    def test_default_policy_mode(self):
        """Default policy mode should be balanced."""
        assert DEFAULT_POLICY_MODE == PolicyMode.BALANCED


class TestGetSetPolicyMode:
    """Tests for get_policy_mode and set_policy_mode."""

    def test_get_default_policy_mode(self):
        """get_policy_mode should return default for empty runstate."""
        runstate = {}
        mode = get_policy_mode(runstate)
        assert mode == DEFAULT_POLICY_MODE

    def test_get_policy_mode_from_runstate(self):
        """get_policy_mode should return mode from runstate."""
        runstate = {"policy_mode": "balanced"}
        mode = get_policy_mode(runstate)
        assert mode == PolicyMode.BALANCED

    def test_set_policy_mode(self):
        """set_policy_mode should update runstate."""
        runstate = {}
        updated = set_policy_mode(runstate, PolicyMode.LOW_INTERRUPTION)
        assert updated["policy_mode"] == "low_interruption"

    def test_invalid_policy_mode_returns_default(self):
        """Invalid policy mode should return default."""
        runstate = {"policy_mode": "invalid"}
        mode = get_policy_mode(runstate)
        assert mode == DEFAULT_POLICY_MODE


class TestScopeChangeFlag:
    """Tests for scope_change_flag."""

    def test_set_scope_change_flag_true(self):
        """set_scope_change_flag should set true."""
        runstate = {}
        updated = set_scope_change_flag(runstate, True)
        assert updated["scope_change_flag"] == True

    def test_set_scope_change_flag_false(self):
        """set_scope_change_flag should set false."""
        runstate = {"scope_change_flag": True}
        updated = set_scope_change_flag(runstate, False)
        assert updated["scope_change_flag"] == False


class TestRiskyActions:
    """Tests for risky action handling."""

    def test_is_risky_action_for_git_push(self):
        """git_push should be risky."""
        assert is_risky_action(ActionType.GIT_PUSH) == True

    def test_is_risky_action_for_archive_irreversible(self):
        """archive_irreversible should be risky."""
        assert is_risky_action(ActionType.ARCHIVE_IRREVERSIBLE) == True

    def test_is_risky_action_for_internal_artifact(self):
        """internal_artifact should not be risky."""
        assert is_risky_action(ActionType.INTERNAL_ARTIFACT) == False

    def test_register_risky_action(self):
        """register_risky_action should add to pending list."""
        runstate = {}
        updated = register_risky_action(runstate, ActionType.GIT_PUSH, "origin/main")
        assert len(updated["pending_risky_actions"]) == 1
        assert updated["pending_risky_actions"][0]["action_type"] == "git_push"

    def test_clear_risky_action(self):
        """clear_risky_action should remove from pending list."""
        runstate = {"pending_risky_actions": [{"action_type": "git_push", "target": "origin/main"}]}
        updated = clear_risky_action(runstate, ActionType.GIT_PUSH)
        assert len(updated["pending_risky_actions"]) == 0

    def test_risky_action_types_constant(self):
        """RISKY_ACTION_TYPES should contain expected types."""
        assert ActionType.GIT_PUSH in RISKY_ACTION_TYPES
        assert ActionType.EXTERNAL_API_MUTATION in RISKY_ACTION_TYPES
        assert ActionType.INTERNAL_ARTIFACT not in RISKY_ACTION_TYPES


class TestCheckMustPauseConditions:
    """Tests for check_must_pause_conditions."""

    def test_no_pause_needed_empty_runstate(self):
        """Empty runstate should not need pause."""
        runstate = {}
        result = check_must_pause_conditions(runstate)
        assert result is None

    def test_pause_needed_for_blocked_items(self):
        """Blocked items should cause pause."""
        runstate = {
            "blocked_items": [{"item": "external-api", "reason": "API key pending", "since": "2024-01-15"}]
        }
        pause_reason = check_must_pause_conditions(runstate)
        assert pause_reason is not None
        assert pause_reason.category == PauseCategory.BLOCKER

    def test_pause_needed_for_decisions_conservative(self):
        """Decisions should cause pause in conservative mode."""
        runstate = {
            "decisions_needed": [{"decision": "schema-format", "options": ["YAML", "JSON"]}],
            "policy_mode": "conservative",
        }
        pause_reason = check_must_pause_conditions(runstate)
        assert pause_reason is not None
        assert pause_reason.category == PauseCategory.DECISION_REQUIRED

    def test_pause_needed_for_decisions_balanced(self):
        """Decisions should cause pause in balanced mode."""
        runstate = {
            "decisions_needed": [{"decision": "schema-format", "options": ["YAML", "JSON"]}],
            "policy_mode": "balanced",
        }
        pause_reason = check_must_pause_conditions(runstate)
        assert pause_reason is not None
        assert pause_reason.category == PauseCategory.DECISION_REQUIRED

    def test_no_pause_for_decisions_low_interruption(self):
        """Decisions should not cause pause in low_interruption mode."""
        runstate = {
            "decisions_needed": [{"decision": "schema-format", "options": ["YAML", "JSON"]}],
            "policy_mode": "low_interruption",
        }
        pause_reason = check_must_pause_conditions(runstate)
        assert pause_reason is None

    def test_pause_needed_for_scope_change(self):
        """Scope change flag should cause pause."""
        runstate = {"scope_change_flag": True}
        pause_reason = check_must_pause_conditions(runstate)
        assert pause_reason is not None
        assert pause_reason.category == PauseCategory.SCOPE_CHANGE

    def test_pause_needed_for_risky_action(self):
        """Pending risky action should cause pause."""
        runstate = {
            "pending_risky_actions": [
                {"action_type": "git_push", "target": "origin/main", "requires_confirmation": True}
            ]
        }
        pause_reason = check_must_pause_conditions(runstate)
        assert pause_reason is not None
        assert pause_reason.category == PauseCategory.RISKY_ACTION


class TestShouldAutoContinue:
    """Tests for should_auto_continue."""

    def test_conservative_mode_execution_success(self):
        """Conservative mode should auto-continue execution success."""
        runstate = {"policy_mode": "conservative"}
        result = should_auto_continue(runstate, "execution_success_to_review")
        assert result == True

    def test_conservative_mode_other_transitions(self):
        """Conservative mode should not auto-continue other transitions."""
        runstate = {"policy_mode": "conservative"}
        result = should_auto_continue(runstate, "review_pack_generated")
        assert result == False

    def test_balanced_mode_safe_transitions(self):
        """Balanced mode should auto-continue safe transitions."""
        runstate = {"policy_mode": "balanced", "next_recommended_action": "Execute next task"}
        execution_result = {"status": "success"}
        assert should_auto_continue(runstate, "execution_success_to_review", execution_result) == True
        assert should_auto_continue(runstate, "review_pack_generated", execution_result) == True
        assert should_auto_continue(runstate, "safe_state_advance") == True

    def test_low_interruption_mode_more_transitions(self):
        """Low-interruption mode should auto-continue more transitions."""
        runstate = {"policy_mode": "low_interruption"}
        assert should_auto_continue(runstate, "execution_success_to_review") == True
        assert should_auto_continue(runstate, "routine_cli_commands") == True

    def test_blocked_items_override_policy(self):
        """Blocked items should override policy mode."""
        runstate = {
            "policy_mode": "low_interruption",
            "blocked_items": [{"item": "test", "reason": "test", "since": "2024-01-01"}],
        }
        result = should_auto_continue(runstate, "execution_success_to_review")
        assert result == False


class TestCanAutoProceedAfterExecution:
    """Tests for can_auto_proceed_after_execution."""

    def test_can_proceed_success_execution(self):
        """Successful execution should allow proceed."""
        runstate = {"policy_mode": "balanced"}
        execution_result = {"status": "success"}
        can_proceed, pause_reason = can_auto_proceed_after_execution(runstate, execution_result)
        assert can_proceed == True
        assert pause_reason is None

    def test_cannot_proceed_failed_execution(self):
        """Failed execution should not allow proceed."""
        runstate = {"policy_mode": "balanced"}
        execution_result = {"status": "failed"}
        can_proceed, pause_reason = can_auto_proceed_after_execution(runstate, execution_result)
        assert can_proceed == False
        assert pause_reason.category == PauseCategory.POLICY_BOUNDARY

    def test_cannot_proceed_with_blockers(self):
        """Blockers should prevent proceed."""
        runstate = {
            "policy_mode": "balanced",
            "blocked_items": [{"item": "test", "reason": "test", "since": "2024-01-01"}],
        }
        execution_result = {"status": "success"}
        can_proceed, pause_reason = can_auto_proceed_after_execution(runstate, execution_result)
        assert can_proceed == False
        assert pause_reason.category == PauseCategory.BLOCKER


class TestPauseReason:
    """Tests for PauseReason dataclass."""

    def test_pause_reason_creation(self):
        """PauseReason should create with required fields."""
        reason = PauseReason(
            category=PauseCategory.DECISION_REQUIRED,
            summary="Pending decision",
            why="RunState contains unresolved decision",
            required_to_continue="Make decision or use --force",
            suggested_next_action="asyncdev resume-next-day continue-loop --decision approve",
        )
        assert reason.category == PauseCategory.DECISION_REQUIRED
        assert reason.summary == "Pending decision"

    def test_pause_reason_format_for_cli(self):
        """format_for_cli should produce readable output."""
        reason = PauseReason(
            category=PauseCategory.BLOCKER,
            summary="API blocked",
            why="API key missing",
            required_to_continue="Resolve blocker",
            suggested_next_action="asyncdev resume-next-day unblock",
        )
        formatted = reason.format_for_cli()
        assert "Blocked" in formatted
        assert "API blocked" in formatted

    def test_pause_reason_to_dict(self):
        """to_dict should convert to dictionary."""
        reason = PauseReason(
            category=PauseCategory.RISKY_ACTION,
            summary="Git push pending",
            why="Requires confirmation",
            required_to_continue="Confirm push",
            suggested_next_action="asyncdev --confirm-push",
        )
        data = reason.to_dict()
        assert data["category"] == "risky_action"
        assert data["summary"] == "Git push pending"

    def test_pause_reason_from_dict(self):
        """from_dict should create from dictionary."""
        data = {
            "category": "scope_change",
            "summary": "Scope changed",
            "why": "scope_change_flag set",
            "required_to_continue": "Acknowledge",
            "suggested_next_action": "asyncdev --acknowledge-scope",
        }
        reason = PauseReason.from_dict(data)
        assert reason.category == PauseCategory.SCOPE_CHANGE
        assert reason.summary == "Scope changed"

    def test_get_display_info(self):
        """get_display_info should return category display info."""
        reason = PauseReason(
            category=PauseCategory.DECISION_REQUIRED,
            summary="test",
            why="test",
            required_to_continue="test",
            suggested_next_action="test",
        )
        info = reason.get_display_info()
        assert info["label"] == "Decision Required"
        assert info["color"] == "yellow"


class TestPauseCategory:
    """Tests for PauseCategory enum."""

    def test_pause_category_values(self):
        """PauseCategory should have expected values."""
        assert PauseCategory.DECISION_REQUIRED.value == "decision_required"
        assert PauseCategory.BLOCKER.value == "blocker"
        assert PauseCategory.RISKY_ACTION.value == "risky_action"
        assert PauseCategory.SCOPE_CHANGE.value == "scope_change"
        assert PauseCategory.POLICY_BOUNDARY.value == "policy_boundary"


class TestPolicyCLI:
    """Tests for policy CLI commands."""

    def test_policy_show_default(self, temp_dir):
        """policy show should display current policy."""
        from typer.testing import CliRunner
        from cli.commands.policy import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["show", "--path", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "Policy Mode" in result.output

    def test_policy_modes(self):
        """policy modes should list available modes."""
        from typer.testing import CliRunner
        from cli.commands.policy import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["modes"])
        
        assert result.exit_code == 0
        assert "conservative" in result.output
        assert "balanced" in result.output
        assert "low_interruption" in result.output

    def test_policy_scope_flag_show(self, temp_dir):
        """policy scope-flag should show current flag."""
        from typer.testing import CliRunner
        from cli.commands.policy import app
        from runtime.state_store import StateStore
        
        runner = CliRunner()
        
        project_path = Path(temp_dir) / "demo-product-001"
        project_path.mkdir(parents=True)
        store = StateStore(project_path)
        store.save_runstate({"project_id": "demo-product-001", "scope_change_flag": False})
        
        result = runner.invoke(app, ["scope-flag", "--path", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "scope_change_flag" in result.output.lower() or "False" in result.output


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)