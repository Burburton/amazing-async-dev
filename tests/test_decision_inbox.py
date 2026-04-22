"""Tests for Decision Inbox CLI (Phase 3 operator surface).

Tests for: list, show, reply, wait, history commands.
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from runtime.decision_request_store import (
    DecisionRequestStore,
    DecisionRequestStatus,
    DecisionType,
    DeliveryChannel,
)
from runtime.state_store import StateStore
from runtime.decision_sync import sync_decision_to_runstate
from cli.commands.decision import _get_all_projects, _get_decisions_for_project


@pytest.fixture
def temp_project():
    """Create a temporary project with decision request."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-project"
        project_path.mkdir(parents=True)
        
        (project_path / ".runtime").mkdir(parents=True)
        (project_path / "features").mkdir(parents=True)
        
        yield project_path


@pytest.fixture
def temp_projects_root():
    """Create a temporary projects root with multiple projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        project_a = root / "project-a"
        project_a.mkdir(parents=True)
        (project_a / ".runtime").mkdir(parents=True)
        
        project_b = root / "project-b"
        project_b.mkdir(parents=True)
        (project_b / ".runtime").mkdir(parents=True)
        
        yield root


@pytest.fixture
def decision_store(temp_project):
    """Create a decision request store."""
    return DecisionRequestStore(temp_project)


@pytest.fixture
def state_store(temp_project):
    """Create a state store."""
    return StateStore(temp_project)


@pytest.fixture
def sample_decision_request(decision_store):
    """Create a sample decision request."""
    return decision_store.create_request(
        product_id="test-project",
        feature_id="feature-001",
        pause_reason_category="decision_required",
        decision_type=DecisionType.TECHNICAL,
        question="Which approach should we use?",
        options=[
            {"id": "A", "label": "Option A", "description": "First approach"},
            {"id": "B", "label": "Option B", "description": "Second approach"},
        ],
        recommendation="A",
        delivery_channel=DeliveryChannel.MOCK_FILE,
    )


class TestGetAllProjects:
    """Tests for _get_all_projects helper."""
    
    def test_returns_empty_for_nonexistent_path(self):
        result = _get_all_projects(Path("/nonexistent"))
        assert result == []
    
    def test_returns_project_directories(self, temp_projects_root):
        result = _get_all_projects(temp_projects_root)
        assert len(result) == 2
        names = [p.name for p in result]
        assert "project-a" in names
        assert "project-b" in names
    
    def test_excludes_dot_directories(self, temp_projects_root):
        (temp_projects_root / ".hidden").mkdir()
        result = _get_all_projects(temp_projects_root)
        names = [p.name for p in result]
        assert ".hidden" not in names


class TestGetDecisionsForProject:
    """Tests for _get_decisions_for_project helper."""
    
    def test_returns_empty_for_no_requests(self, temp_project):
        result = _get_decisions_for_project(temp_project)
        assert result == []
    
    def test_returns_requests_with_blocking_status(self, temp_project, decision_store, sample_decision_request):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        result = _get_decisions_for_project(temp_project)
        assert len(result) == 1
        assert result[0]["decision_request_id"] == sample_decision_request["decision_request_id"]
        assert result[0]["blocking_status"] == "CLEAR"
        assert result[0]["project_id"] == temp_project.name
    
    def test_filters_by_status(self, temp_project, decision_store, sample_decision_request):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        result = _get_decisions_for_project(temp_project, DecisionRequestStatus.SENT)
        assert len(result) == 1
        
        result = _get_decisions_for_project(temp_project, DecisionRequestStatus.RESOLVED)
        assert len(result) == 0
    
    def test_shows_blocked_status_when_blocking(self, temp_project, decision_store, sample_decision_request, state_store):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        runstate = state_store.load_runstate() or {}
        runstate = sync_decision_to_runstate(sample_decision_request, runstate)
        state_store.save_runstate(runstate)
        
        result = _get_decisions_for_project(temp_project)
        assert result[0]["blocking_status"] == "BLOCKED"


class TestDecisionList:
    """Tests for decision list command."""
    
    def test_list_empty_projects(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--all", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 0
        assert "No decision requests found" in result.output or "No projects found" in result.output
    
    def test_list_with_pending_decision(self, temp_projects_root, decision_store):
        project_a = temp_projects_root / "project-a"
        store_a = DecisionRequestStore(project_a)
        
        request = store_a.create_request(
            product_id="project-a",
            feature_id="feature-001",
            pause_reason_category="decision_required",
            decision_type=DecisionType.TECHNICAL,
            question="Test question?",
            options=[{"id": "A", "label": "Option A"}],
            recommendation="A",
            delivery_channel=DeliveryChannel.MOCK_FILE,
        )
        store_a.mark_sent(request["decision_request_id"])
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--all", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 0
        assert request["decision_request_id"] in result.output or "decision requests" in result.output.lower()


class TestDecisionShow:
    """Tests for decision show command."""
    
    def test_show_nonexistent_request(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["show", "--request", "dr-nonexistent", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 1
        assert "Request not found" in result.output
    
    def test_show_existing_request(self, temp_project, decision_store, sample_decision_request):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "show",
            "--request", sample_decision_request["decision_request_id"],
            "--path", str(temp_project.parent),
        ])
        
        assert result.exit_code == 0
        assert sample_decision_request["decision_request_id"] in result.output
        assert sample_decision_request["question"] in result.output


class TestDecisionReply:
    """Tests for decision reply command."""
    
    def test_reply_valid_decision(self, temp_project, decision_store, sample_decision_request, state_store):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        runstate = state_store.load_runstate() or {}
        runstate["project_id"] = "test-project"
        runstate["feature_id"] = "feature-001"
        state_store.save_runstate(runstate)
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "reply",
            "--request", sample_decision_request["decision_request_id"],
            "--command", "DECISION A",
            "--path", str(temp_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "resolved" in result.output.lower()
        
        updated = decision_store.load_request(sample_decision_request["decision_request_id"])
        assert updated["status"] == DecisionRequestStatus.RESOLVED.value
    
    def test_reply_invalid_syntax(self, temp_project, decision_store, sample_decision_request):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "reply",
            "--request", sample_decision_request["decision_request_id"],
            "--command", "INVALID",
            "--path", str(temp_project.parent),
        ])
        
        assert result.exit_code == 1
        assert "Invalid reply syntax" in result.output
    
    def test_reply_invalid_option(self, temp_project, decision_store, sample_decision_request):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "reply",
            "--request", sample_decision_request["decision_request_id"],
            "--command", "DECISION C",
            "--path", str(temp_project.parent),
        ])
        
        assert result.exit_code == 1


class TestDecisionHistory:
    """Tests for decision history command."""
    
    def test_history_empty(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["history", "--all", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 0
        assert "No resolved decisions found" in result.output
    
    def test_history_with_resolved(self, temp_project, decision_store, sample_decision_request):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        decision_store.mark_resolved(
            sample_decision_request["decision_request_id"],
            resolution="DECISION A",
        )
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "history",
            "--all",
            "--path", str(temp_project.parent),
        ])
        
        assert result.exit_code == 0
        assert sample_decision_request["decision_request_id"] in result.output


class TestBlockingStateIntegration:
    """Tests for blocking state integration in decision commands."""
    
    def test_list_shows_blocked_state(self, temp_project, decision_store, sample_decision_request, state_store):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        runstate = state_store.load_runstate() or {}
        runstate["current_phase"] = "blocked"
        runstate["decision_request_pending"] = sample_decision_request["decision_request_id"]
        state_store.save_runstate(runstate)
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "BLOCKED" in result.output or "Blocking Alert" in result.output
    
    def test_reply_clears_blocking_state(self, temp_project, decision_store, sample_decision_request, state_store):
        decision_store.mark_sent(sample_decision_request["decision_request_id"])
        
        runstate = state_store.load_runstate() or {}
        runstate["project_id"] = "test-project"
        runstate["feature_id"] = "feature-001"
        runstate["current_phase"] = "blocked"
        runstate["decision_request_pending"] = sample_decision_request["decision_request_id"]
        state_store.save_runstate(runstate)
        
        from typer.testing import CliRunner
        from cli.commands.decision import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "reply",
            "--request", sample_decision_request["decision_request_id"],
            "--command", "DECISION A",
            "--path", str(temp_project.parent),
        ])
        
        assert result.exit_code == 0
        assert "no longer blocked" in result.output.lower() or "unblocked" in result.output.lower()