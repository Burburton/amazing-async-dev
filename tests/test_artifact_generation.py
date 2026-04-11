"""Tests for artifact generation and file formats."""

import pytest
from pathlib import Path
import yaml
from runtime.state_store import StateStore
from runtime.review_pack_builder import build_daily_review_pack


@pytest.fixture
def temp_store(temp_dir):
    """Create a StateStore with temp project path."""
    from runtime.adapters.filesystem_adapter import FilesystemAdapter
    
    fs = FilesystemAdapter()
    project_path = temp_dir / "test-product"
    fs.ensure_dir(project_path)
    fs.ensure_dir(project_path / "execution-packs")
    fs.ensure_dir(project_path / "execution-results")
    fs.ensure_dir(project_path / "reviews")
    
    yield StateStore(project_path)


class TestExecutionPackFormat:
    """Tests for ExecutionPack YAML/Markdown format."""

    def test_saves_with_yaml_block(self, temp_store):
        """ExecutionPack should be saved with YAML block in markdown."""
        execution_pack = {
            "execution_id": "exec-20240101-001",
            "feature_id": "001-test",
            "task_id": "test-task",
            "goal": "Test goal",
            "task_scope": ["test"],
            "deliverables": [{"item": "output", "path": "out.md", "type": "file"}],
            "verification_steps": ["Check output"],
            "stop_conditions": ["Complete"],
        }

        temp_store.save_execution_pack(execution_pack)

        pack_path = temp_store.execution_packs_path / "exec-20240101-001.md"
        assert pack_path.exists()

        content = pack_path.read_text()
        assert "# ExecutionPack" in content
        assert "```yaml" in content
        assert "```" in content

    def test_yaml_block_contains_all_fields(self, temp_store):
        """ExecutionPack YAML should contain all required fields."""
        execution_pack = {
            "execution_id": "exec-20240101-001",
            "feature_id": "001-test",
            "task_id": "test-task",
            "goal": "Test goal",
            "task_scope": ["task1", "task2"],
            "deliverables": [{"item": "output", "path": "out.md", "type": "file"}],
            "verification_steps": ["Step 1", "Step 2"],
            "stop_conditions": ["Complete"],
        }

        temp_store.save_execution_pack(execution_pack)

        loaded = temp_store.load_execution_pack("exec-20240101-001")
        assert loaded["execution_id"] == "exec-20240101-001"
        assert loaded["feature_id"] == "001-test"
        assert loaded["task_id"] == "test-task"
        assert loaded["goal"] == "Test goal"
        assert len(loaded["task_scope"]) == 2

    def test_load_returns_none_if_not_found(self, temp_store):
        """load_execution_pack should return None for missing file."""
        result = temp_store.load_execution_pack("nonexistent-id")
        assert result is None

    def test_file_naming_follows_pattern(self, temp_store):
        """ExecutionPack files should follow exec-YYYYMMDD-### pattern."""
        execution_pack = {
            "execution_id": "exec-20240415-001",
            "feature_id": "001-test",
            "task_id": "test",
            "goal": "Test",
        }

        temp_store.save_execution_pack(execution_pack)

        pack_path = temp_store.execution_packs_path / "exec-20240415-001.md"
        assert pack_path.exists()


class TestExecutionResultFormat:
    """Tests for ExecutionResult YAML/Markdown format."""

    def test_saves_with_yaml_block(self, temp_store):
        """ExecutionResult should be saved with YAML block in markdown."""
        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "success",
            "completed_items": ["Item 1"],
            "artifacts_created": [],
            "verification_result": {"passed": 1, "failed": 0},
            "issues_found": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Continue",
        }

        temp_store.save_execution_result(execution_result)

        result_path = temp_store.execution_results_path / "exec-20240101-001.md"
        assert result_path.exists()

        content = result_path.read_text()
        assert "# ExecutionResult" in content
        assert "```yaml" in content

    def test_yaml_block_contains_all_fields(self, temp_store):
        """ExecutionResult YAML should contain all required fields."""
        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "success",
            "completed_items": ["Task completed"],
            "artifacts_created": [
                {"name": "output.md", "path": "output.md", "type": "file"}
            ],
            "verification_result": {"passed": 2, "failed": 0, "skipped": 1},
            "issues_found": ["Minor issue"],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Next task",
        }

        temp_store.save_execution_result(execution_result)

        loaded = temp_store.load_execution_result("exec-20240101-001")
        assert loaded["execution_id"] == "exec-20240101-001"
        assert loaded["status"] == "success"
        assert len(loaded["completed_items"]) == 1
        assert len(loaded["artifacts_created"]) == 1
        assert loaded["verification_result"]["passed"] == 2

    def test_load_returns_none_if_not_found(self, temp_store):
        """load_execution_result should return None for missing file."""
        result = temp_store.load_execution_result("nonexistent-id")
        assert result is None


class TestDailyReviewPackFormat:
    """Tests for DailyReviewPack YAML/Markdown format."""

    def test_saves_with_yaml_block(self, temp_store):
        """DailyReviewPack should be saved with YAML block in markdown."""
        review_pack = {
            "date": "2024-01-01",
            "project_id": "test-project",
            "feature_id": "001-test",
            "today_goal": "Complete task",
            "what_was_completed": ["Item 1"],
            "evidence": [],
            "problems_found": [],
            "blocked_items": [],
            "decisions_needed": [],
            "recommended_options": [],
            "tomorrow_plan": "Continue",
        }

        temp_store.save_daily_review_pack(review_pack)

        review_path = temp_store.reviews_path / "2024-01-01-review.md"
        assert review_path.exists()

        content = review_path.read_text()
        assert "# DailyReviewPack" in content
        assert "```yaml" in content

    def test_yaml_block_contains_all_fields(self, temp_store):
        """DailyReviewPack YAML should contain all required fields."""
        review_pack = {
            "date": "2024-01-01",
            "project_id": "test-project",
            "feature_id": "001-test",
            "today_goal": "Complete feature",
            "what_was_completed": ["Task A", "Task B"],
            "evidence": [{"item": "output.md", "path": "output.md", "verified": True}],
            "problems_found": ["Minor issue"],
            "blocked_items": [],
            "decisions_needed": [
                {"decision": "Choose A", "options": ["Option 1", "Option 2"]}
            ],
            "recommended_options": [],
            "tomorrow_plan": "Continue with Task C",
        }

        temp_store.save_daily_review_pack(review_pack)

        loaded = temp_store.load_daily_review_pack("2024-01-01")
        assert loaded["date"] == "2024-01-01"
        assert loaded["project_id"] == "test-project"
        assert len(loaded["what_was_completed"]) == 2
        assert len(loaded["decisions_needed"]) == 1

    def test_load_returns_none_if_not_found(self, temp_store):
        """load_daily_review_pack should return None for missing file."""
        result = temp_store.load_daily_review_pack("nonexistent-date")
        assert result is None

    def test_file_naming_follows_pattern(self, temp_store):
        """DailyReviewPack files should follow YYYY-MM-DD-review pattern."""
        review_pack = {
            "date": "2024-04-15",
            "project_id": "test",
            "feature_id": "001",
            "today_goal": "Test",
        }

        temp_store.save_daily_review_pack(review_pack)

        review_path = temp_store.reviews_path / "2024-04-15-review.md"
        assert review_path.exists()


class TestRunStateFormat:
    """Tests for RunState YAML/Markdown format."""

    def test_saves_with_yaml_block(self, temp_store):
        """RunState should be saved with YAML block in markdown."""
        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
            "current_phase": "planning",
            "active_task": "Task 1",
            "task_queue": ["Task 1", "Task 2"],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Started",
            "next_recommended_action": "Plan day",
            "updated_at": "2024-01-01",
        }

        temp_store.save_runstate(runstate)

        runstate_path = temp_store.runstate_path
        assert runstate_path.exists()

        content = runstate_path.read_text()
        assert "# RunState" in content
        assert "```yaml" in content

    def test_yaml_block_contains_all_fields(self, temp_store):
        """RunState YAML should contain all required fields."""
        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
            "current_phase": "executing",
            "active_task": "Implement feature",
            "task_queue": ["Task A", "Task B", "Task C"],
            "completed_outputs": ["Output 1"],
            "open_questions": ["Question 1"],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Executed task",
            "next_recommended_action": "Review results",
            "updated_at": "",
        }

        temp_store.save_runstate(runstate)

        loaded = temp_store.load_runstate()
        assert loaded["project_id"] == "test-project"
        assert loaded["current_phase"] == "executing"
        assert len(loaded["task_queue"]) == 3
        assert loaded["active_task"] == "Implement feature"

    def test_load_returns_none_if_not_found(self, temp_store):
        """load_runstate should return None for missing file."""
        result = temp_store.load_runstate()
        assert result is None

    def test_sets_updated_at_on_save(self, temp_store):
        """save_runstate should set updated_at timestamp."""
        runstate = {
            "project_id": "test",
            "feature_id": "001",
            "current_phase": "planning",
            "updated_at": "",
        }

        temp_store.save_runstate(runstate)

        loaded = temp_store.load_runstate()
        assert loaded["updated_at"] != ""


class TestReviewPackBuilder:
    """Tests for build_daily_review_pack function."""

    def test_builds_review_pack_from_execution_result(self, temp_store):
        """build_daily_review_pack should create review pack from result."""
        execution_result = {
            "execution_id": "exec-20240101-001",
            "status": "success",
            "completed_items": ["Item 1", "Item 2"],
            "artifacts_created": [
                {"name": "output.md", "path": "output.md", "type": "file"}
            ],
            "verification_result": {"passed": 2, "failed": 0},
            "issues_found": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Continue",
        }

        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
        }

        review_pack = build_daily_review_pack(execution_result, runstate)

        assert review_pack["project_id"] == "test-project"
        assert review_pack["feature_id"] == "001-test"
        assert len(review_pack["what_was_completed"]) == 2
        assert "today_goal" in review_pack
        assert "tomorrow_plan" in review_pack

    def test_converts_blocked_reasons(self, temp_store):
        """build_daily_review_pack should convert blocked_reasons."""
        execution_result = {
            "execution_id": "exec-001",
            "status": "blocked",
            "blocked_reasons": [
                {"reason": "API unavailable", "impact": "Cannot call service"}
            ],
            "decisions_required": [],
        }

        runstate = {"project_id": "test", "feature_id": "001"}

        review_pack = build_daily_review_pack(execution_result, runstate)

        assert len(review_pack["blocked_items"]) == 1
        assert review_pack["blocked_items"][0]["status"] == "waiting"

    def test_converts_decisions_required(self, temp_store):
        """build_daily_review_pack should convert decisions_required."""
        execution_result = {
            "execution_id": "exec-001",
            "status": "blocked",
            "blocked_reasons": [],
            "decisions_required": [
                {
                    "decision": "Choose approach",
                    "options": ["A", "B"],
                    "recommendation": "A",
                    "context": "Need to pick",
                    "urgency": "high",
                }
            ],
        }

        runstate = {"project_id": "test", "feature_id": "001"}

        review_pack = build_daily_review_pack(execution_result, runstate)

        assert len(review_pack["decisions_needed"]) == 1
        assert review_pack["decisions_needed"][0]["decision"] == "Choose approach"
        assert review_pack["decisions_needed"][0]["urgency"] == "high"

    def test_builds_risk_summary(self, temp_store):
        """build_daily_review_pack should generate risk summary."""
        execution_result = {
            "execution_id": "exec-001",
            "status": "success",
        }

        runstate = {"project_id": "test", "feature_id": "001"}

        review_pack = build_daily_review_pack(execution_result, runstate)

        assert "risk_summary" in review_pack
        assert "success" in review_pack["risk_summary"].lower()

    def test_builds_confidence_notes(self, temp_store):
        """build_daily_review_pack should generate confidence notes."""
        execution_result = {
            "execution_id": "exec-001",
            "status": "success",
            "verification_result": {"passed": 3, "failed": 0},
        }

        runstate = {"project_id": "test", "feature_id": "001"}

        review_pack = build_daily_review_pack(execution_result, runstate)

        assert "confidence_notes" in review_pack
        assert "High confidence" in review_pack["confidence_notes"]


class TestYamlBlockExtraction:
    """Tests for YAML block extraction from markdown."""

    def test_extracts_valid_yaml_block(self, temp_store):
        """_extract_yaml_block should parse valid YAML."""
        content = """# Test

```yaml
key: value
list:
  - item1
  - item2
```
"""

        yaml_block = temp_store._extract_yaml_block(content)
        assert yaml_block is not None

        data = yaml.safe_load(yaml_block)
        assert data["key"] == "value"
        assert len(data["list"]) == 2

    def test_returns_none_for_missing_yaml_block(self, temp_store):
        """_extract_yaml_block should return None if no block."""
        content = """# Test

No YAML block here.
"""

        yaml_block = temp_store._extract_yaml_block(content)
        assert yaml_block is None

    def test_handles_multiline_yaml(self, temp_store):
        """_extract_yaml_block should handle multiline YAML."""
        content = """# RunState

```yaml
project_id: test
feature_id: 001
task_queue:
  - Task 1
  - Task 2
  - Task 3
current_phase: planning
```
"""

        yaml_block = temp_store._extract_yaml_block(content)
        data = yaml.safe_load(yaml_block)

        assert len(data["task_queue"]) == 3
        assert data["current_phase"] == "planning"