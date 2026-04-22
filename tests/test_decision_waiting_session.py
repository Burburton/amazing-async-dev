"""Tests for Decision Waiting Session (Feature 064)."""

import pytest
from pathlib import Path
from runtime.decision_waiting_session import (
    check_blocking_state,
    should_block_todo_continuation,
    get_blocking_message,
    session_startup_check,
)


class TestCheckBlockingState:

    def test_returns_clear_when_no_runstate(self, temp_dir):
        status, request_id = check_blocking_state(temp_dir)
        assert status == "CLEAR"
        assert request_id is None

    def test_returns_blocked_when_phase_blocked(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
project_id: test-project
feature_id: feat-001
current_phase: blocked
blocked_items:
  - "Test blocker"
decisions_needed: []
decision_request_pending: dr-20260422-001
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        status, request_id = check_blocking_state(project_path)
        assert status == "BLOCKED"
        assert request_id == "dr-20260422-001"

    def test_returns_waiting_when_pending_exists(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
project_id: test-project
feature_id: feat-001
current_phase: planning
decisions_needed:
  - "Pending decision"
decision_request_pending: dr-20260422-002
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        status, request_id = check_blocking_state(project_path)
        assert status == "WAITING_DECISION"
        assert request_id == "dr-20260422-002"

    def test_returns_clear_when_planning_no_pending(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
project_id: test-project
feature_id: feat-001
current_phase: planning
decisions_needed: []
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        status, request_id = check_blocking_state(project_path)
        assert status == "CLEAR"
        assert request_id is None


class TestShouldBlockTodoContinuation:

    def test_returns_false_when_clear(self, temp_dir):
        result = should_block_todo_continuation(temp_dir)
        assert result is False

    def test_returns_true_when_blocked(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
current_phase: blocked
decision_request_pending: dr-test-001
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        result = should_block_todo_continuation(project_path)
        assert result is True

    def test_returns_true_when_waiting_decision(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
current_phase: planning
decision_request_pending: dr-test-002
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        result = should_block_todo_continuation(project_path)
        assert result is True


class TestGetBlockingMessage:

    def test_clear_message(self, temp_dir):
        message = get_blocking_message(temp_dir)
        assert "No blocking" in message

    def test_blocked_message(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
current_phase: blocked
decision_request_pending: dr-123
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        message = get_blocking_message(project_path)
        assert "blocked" in message.lower()
        assert "dr-123" in message


class TestSessionStartupCheck:

    def test_returns_continue_when_clear(self, temp_dir):
        result = session_startup_check(temp_dir)
        assert result["status"] == "CLEAR"
        assert result["action"] == "continue"
        assert result["should_poll"] is False

    def test_returns_poll_and_wait_when_blocked(self, temp_dir):
        project_path = temp_dir / "test-project"
        project_path.mkdir()
        (project_path / ".runtime").mkdir()
        
        runstate_content = """# RunState

```yaml
current_phase: blocked
decision_request_pending: dr-test-003
```
"""
        (project_path / "runstate.md").write_text(runstate_content)
        
        result = session_startup_check(project_path)
        assert result["status"] == "BLOCKED"
        assert result["action"] == "poll_and_wait"
        assert result["should_poll"] is True
        assert result["request_id"] == "dr-test-003"