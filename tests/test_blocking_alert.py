"""Tests for blocking alert injection (Feature 065).

Tests for: generate_blocking_alert, save_runstate with alert, session-start CLI.
"""

import tempfile
from pathlib import Path

import pytest

from runtime.state_store import (
    StateStore,
    generate_blocking_alert,
    has_blocking_alert,
    remove_blocking_alert,
)


@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-project"
        project_path.mkdir(parents=True)
        yield project_path


class TestGenerateBlockingAlert:
    def test_generates_alert_when_blocked_with_request(self):
        runstate = {
            "current_phase": "blocked",
            "decision_request_pending": "dr-001",
            "decision_request_sent_at": "2026-04-23T00:00:00",
        }
        alert = generate_blocking_alert(runstate)
        assert "**[!WARNING] BLOCKING ALERT**" in alert
        assert "dr-001" in alert
        assert "BLOCKED - Waiting for human decision reply" in alert
    
    def test_generates_alert_when_pending_request_exists(self):
        runstate = {
            "current_phase": "planning",
            "decision_request_pending": "dr-002",
            "decision_request_sent_at": "2026-04-23T00:00:00",
        }
        alert = generate_blocking_alert(runstate)
        assert "**[!WARNING] BLOCKING ALERT**" in alert
        assert "dr-002" in alert
        assert "WAITING_DECISION" in alert
    
    def test_no_alert_when_clear(self):
        runstate = {
            "current_phase": "planning",
        }
        alert = generate_blocking_alert(runstate)
        assert alert == ""
    
    def test_no_alert_when_blocked_without_request(self):
        runstate = {
            "current_phase": "blocked",
        }
        alert = generate_blocking_alert(runstate)
        assert alert == ""
    
    def test_no_alert_when_completed(self):
        runstate = {
            "current_phase": "completed",
        }
        alert = generate_blocking_alert(runstate)
        assert alert == ""


class TestHasBlockingAlert:
    def test_detects_alert_in_content(self):
        content = "# RunState\n\n> **[!WARNING] BLOCKING ALERT**\n\n```yaml\n..."
        assert has_blocking_alert(content) is True
    
    def test_returns_false_without_alert(self):
        content = "# RunState\n\n```yaml\n...\n```"
        assert has_blocking_alert(content) is False


class TestRemoveBlockingAlert:
    def test_removes_alert_from_content(self):
        content = """# RunState

> **[!WARNING] BLOCKING ALERT**
> 
> **Status**: BLOCKED
> 
> **Reference**: AGENTS.md

```yaml
current_phase: blocked
```
"""
        cleaned = remove_blocking_alert(content)
        assert "**[!WARNING] BLOCKING ALERT**" not in cleaned
        assert "```yaml" in cleaned
    
    def test_preserves_content_without_alert(self):
        content = "# RunState\n\n```yaml\n...\n```"
        cleaned = remove_blocking_alert(content)
        assert cleaned == content


class TestStateStoreBlockingAlert:
    def test_save_injects_alert_when_blocked(self, temp_project):
        store = StateStore(temp_project)
        
        runstate = {
            "project_id": "test",
            "feature_id": "001",
            "current_phase": "blocked",
            "decision_request_pending": "dr-001",
            "decision_request_sent_at": "2026-04-23T00:00:00",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate)
        
        content = (temp_project / "runstate.md").read_text()
        assert has_blocking_alert(content) is True
        assert "dr-001" in content
    
    def test_save_no_alert_when_clear(self, temp_project):
        store = StateStore(temp_project)
        
        runstate = {
            "project_id": "test",
            "feature_id": "001",
            "current_phase": "planning",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate)
        
        content = (temp_project / "runstate.md").read_text()
        assert has_blocking_alert(content) is False
    
    def test_alert_removed_after_unblock(self, temp_project):
        store = StateStore(temp_project)
        
        runstate_blocked = {
            "project_id": "test",
            "feature_id": "001",
            "current_phase": "blocked",
            "decision_request_pending": "dr-001",
            "decision_request_sent_at": "2026-04-23T00:00:00",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate_blocked)
        
        content_blocked = (temp_project / "runstate.md").read_text()
        assert has_blocking_alert(content_blocked) is True
        
        runstate_clear = {
            "project_id": "test",
            "feature_id": "001",
            "current_phase": "planning",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "unblocked",
            "next_recommended_action": "continue",
        }
        
        store.save_runstate(runstate_clear)
        
        content_clear = (temp_project / "runstate.md").read_text()
        assert has_blocking_alert(content_clear) is False
    
    def test_load_preserves_yaml_data_with_alert(self, temp_project):
        store = StateStore(temp_project)
        
        runstate = {
            "project_id": "test",
            "feature_id": "001",
            "current_phase": "blocked",
            "decision_request_pending": "dr-001",
            "decision_request_sent_at": "2026-04-23T00:00:00",
            "active_task": "test",
            "task_queue": ["task1", "task2"],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate)
        
        loaded = store.load_runstate()
        
        assert loaded is not None
        assert loaded["project_id"] == "test"
        assert loaded["current_phase"] == "blocked"
        assert loaded["decision_request_pending"] == "dr-001"
        assert loaded["task_queue"] == ["task1", "task2"]


class TestSessionStartCLI:
    def test_check_returns_exit_2_when_blocked(self, temp_project):
        from typer.testing import CliRunner
        from cli.commands.session_start import app
        
        store = StateStore(temp_project)
        
        runstate = {
            "project_id": temp_project.name,
            "feature_id": "001",
            "current_phase": "blocked",
            "decision_request_pending": "dr-001",
            "decision_request_sent_at": "2026-04-23T00:00:00",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate)
        
        runner = CliRunner()
        result = runner.invoke(app, ["check", "--project", temp_project.name, "--path", str(temp_project.parent)])
        
        assert result.exit_code == 2
        assert "BLOCKING ALERT" in result.output
        assert "dr-001" in result.output
    
    def test_check_returns_exit_0_when_clear(self, temp_project):
        from typer.testing import CliRunner
        from cli.commands.session_start import app
        
        store = StateStore(temp_project)
        
        runstate = {
            "project_id": temp_project.name,
            "feature_id": "001",
            "current_phase": "planning",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate)
        
        runner = CliRunner()
        result = runner.invoke(app, ["check", "--project", temp_project.name, "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "CLEAR" in result.output
    
    def test_status_shows_blocking_summary(self, temp_project):
        from typer.testing import CliRunner
        from cli.commands.session_start import app
        
        store = StateStore(temp_project)
        
        runstate = {
            "project_id": temp_project.name,
            "feature_id": "001",
            "current_phase": "blocked",
            "decision_request_pending": "dr-001",
            "decision_request_sent_at": "2026-04-23T00:00:00",
            "active_task": "test",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "test",
            "next_recommended_action": "test",
        }
        
        store.save_runstate(runstate)
        
        runner = CliRunner()
        result = runner.invoke(app, ["status", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "BLOCKED" in result.output
        assert "1" in result.output