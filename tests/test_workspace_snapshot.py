"""Tests for workspace snapshot (Feature 028)."""

import pytest
from pathlib import Path
import yaml

from runtime.workspace_snapshot import (
    WorkspaceSnapshot,
    generate_workspace_snapshot,
    format_snapshot_markdown,
)


@pytest.fixture
def direct_mode_project(tmp_path):
    project_dir = tmp_path / "direct-project"
    project_dir.mkdir()
    
    product_brief = {
        "product_id": "direct-001",
        "name": "Direct Project",
        "problem": "Test problem",
        "target_user": "Test user",
        "core_value": "Test value",
        "constraints": ["Test constraint"],
        "success_signal": "Test signal",
    }
    
    with open(project_dir / "product-brief.yaml", "w") as f:
        yaml.dump(product_brief, f)
    
    runstate_content = """# RunState

```yaml
product_id: direct-001
feature_id: feature-001
current_phase: planning
active_task: test task
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Created product
next_recommended_action: Plan a task
updated_at: '2026-04-12T10:00:00Z'
```
"""
    
    with open(project_dir / "runstate.md", "w") as f:
        f.write(runstate_content)
    
    return project_dir


@pytest.fixture
def starter_pack_mode_project(tmp_path):
    project_dir = tmp_path / "starter-pack-project"
    project_dir.mkdir()
    
    product_brief = {
        "product_id": "starter-001",
        "name": "Starter Pack Project",
        "problem": "[Test summary] Test problem",
        "target_user": "Test user",
        "core_value": "Test value",
        "constraints": ["Test constraint"],
        "success_signal": "Test signal",
        "starter_pack_context": [
            "Product type: ai_tooling",
            "Stage: mvp",
            "Team mode: solo",
            "Required skills: external-tool-mode",
        ],
    }
    
    with open(project_dir / "product-brief.yaml", "w") as f:
        yaml.dump(product_brief, f)
    
    runstate_content = """# RunState

```yaml
product_id: starter-001
feature_id: feature-002
current_phase: executing
active_task: test execution
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Started execution
next_recommended_action: Continue execution
updated_at: '2026-04-12T11:00:00Z'
workflow_hints:
  policy_mode: balanced
  execution: external-tool-first
```
"""
    
    with open(project_dir / "runstate.md", "w") as f:
        f.write(runstate_content)
    
    results_dir = project_dir / "execution-results"
    results_dir.mkdir()
    
    result_content = """```yaml
execution_id: exec-001
status: success
completed_items:
  - test item
artifacts_created: []
```
"""
    
    with open(results_dir / "exec-001.md", "w") as f:
        f.write(result_content)
    
    reviews_dir = project_dir / "reviews"
    reviews_dir.mkdir()
    
    with open(reviews_dir / "2026-04-12-review.md", "w") as f:
        f.write("# Review\n")
    
    return project_dir


@pytest.fixture
def blocked_project(tmp_path):
    project_dir = tmp_path / "blocked-project"
    project_dir.mkdir()
    
    product_brief = {
        "product_id": "blocked-001",
        "name": "Blocked Project",
        "problem": "Test problem",
        "target_user": "Test user",
        "core_value": "Test value",
        "constraints": ["Test constraint"],
        "success_signal": "Test signal",
    }
    
    with open(project_dir / "product-brief.yaml", "w") as f:
        yaml.dump(product_brief, f)
    
    runstate_content = """# RunState

```yaml
product_id: blocked-001
feature_id: feature-003
current_phase: blocked
active_task: blocked task
task_queue: []
completed_outputs: []
open_questions: []
blocked_items:
  - item: api-key
    reason: Missing API key
    since: '2026-04-12T10:00:00Z'
decisions_needed: []
last_action: Hit blocker
next_recommended_action: Resolve blocker
updated_at: '2026-04-12T10:00:00Z'
```
"""
    
    with open(project_dir / "runstate.md", "w") as f:
        f.write(runstate_content)
    
    return project_dir


@pytest.fixture
def pending_decision_project(tmp_path):
    project_dir = tmp_path / "decision-project"
    project_dir.mkdir()
    
    product_brief = {
        "product_id": "decision-001",
        "name": "Decision Project",
        "problem": "Test problem",
        "target_user": "Test user",
        "core_value": "Test value",
        "constraints": ["Test constraint"],
        "success_signal": "Test signal",
    }
    
    with open(project_dir / "product-brief.yaml", "w") as f:
        yaml.dump(product_brief, f)
    
    runstate_content = """# RunState

```yaml
product_id: decision-001
feature_id: feature-004
current_phase: reviewing
active_task: review task
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed:
  - decision: schema-format
    options:
      - YAML
      - JSON
    impact: all schema files
last_action: Generated review pack
next_recommended_action: Make decisions
updated_at: '2026-04-12T12:00:00Z'
```
"""
    
    with open(project_dir / "runstate.md", "w") as f:
        f.write(runstate_content)
    
    return project_dir


class TestGenerateWorkspaceSnapshot:
    """Tests for generate_workspace_snapshot function."""
    
    def test_direct_mode_detection(self, direct_mode_project):
        snapshot = generate_workspace_snapshot(direct_mode_project)
        
        assert snapshot.initialization_mode == "direct"
        assert snapshot.product_id == "direct-001"
        assert snapshot.product_name == "Direct Project"
        assert snapshot.current_phase == "planning"
        assert snapshot.feature_id == "feature-001"
    
    def test_starter_pack_mode_detection(self, starter_pack_mode_project):
        snapshot = generate_workspace_snapshot(starter_pack_mode_project)
        
        assert snapshot.initialization_mode == "starter-pack"
        assert snapshot.provider_linkage.get("detected") is True
        assert snapshot.provider_linkage.get("product_type") == "ai_tooling"
        assert snapshot.provider_linkage.get("workflow_hints", {}).get("policy_mode") == "balanced"
    
    def test_verification_signal_success(self, starter_pack_mode_project):
        snapshot = generate_workspace_snapshot(starter_pack_mode_project)
        
        assert snapshot.verification_status == "success"
        assert "execution-results" in snapshot.verification_artifact
        assert "exec-001.md" in snapshot.verification_artifact
    
    def test_verification_signal_not_run(self, direct_mode_project):
        snapshot = generate_workspace_snapshot(direct_mode_project)
        
        assert snapshot.verification_status == "not_run"
    
    def test_review_signal_present(self, starter_pack_mode_project):
        snapshot = generate_workspace_snapshot(starter_pack_mode_project)
        
        assert snapshot.review_status == "present"
        assert "reviews" in snapshot.review_artifact
        assert "2026-04-12-review.md" in snapshot.review_artifact
    
    def test_review_signal_missing(self, direct_mode_project):
        snapshot = generate_workspace_snapshot(direct_mode_project)
        
        assert snapshot.review_status == "missing"
    
    def test_pending_decisions_zero(self, direct_mode_project):
        snapshot = generate_workspace_snapshot(direct_mode_project)
        
        assert snapshot.pending_decisions == 0
    
    def test_pending_decisions_count(self, pending_decision_project):
        snapshot = generate_workspace_snapshot(pending_decision_project)
        
        assert snapshot.pending_decisions == 1
    
    def test_blocked_phase_next_step(self, blocked_project):
        snapshot = generate_workspace_snapshot(blocked_project)
        
        assert snapshot.current_phase == "blocked"
        assert "Resolve blockers" in snapshot.recommended_next_step
    
    def test_pending_decision_next_step(self, pending_decision_project):
        snapshot = generate_workspace_snapshot(pending_decision_project)
        
        assert snapshot.pending_decisions > 0
        assert "decisions" in snapshot.recommended_next_step.lower()
    
    def test_empty_project(self, tmp_path):
        empty_project = tmp_path / "empty-project"
        empty_project.mkdir()
        
        snapshot = generate_workspace_snapshot(empty_project)
        
        assert snapshot.initialization_mode == "unknown"
        assert snapshot.current_phase == "none" or snapshot.current_phase == ""


class TestFormatSnapshotMarkdown:
    """Tests for format_snapshot_markdown function."""
    
    def test_format_direct_mode(self, direct_mode_project):
        snapshot = generate_workspace_snapshot(direct_mode_project)
        output = format_snapshot_markdown(snapshot)
        
        assert "Mode: **direct**" in output
        assert "Product: direct-001" in output
        assert "Phase: **planning**" in output
    
    def test_format_starter_pack_mode(self, starter_pack_mode_project):
        snapshot = generate_workspace_snapshot(starter_pack_mode_project)
        output = format_snapshot_markdown(snapshot)
        
        assert "Mode: **starter-pack**" in output
        assert "Provider Context:" in output
        assert "Policy Mode: balanced" in output
    
    def test_format_verification_success(self, starter_pack_mode_project):
        snapshot = generate_workspace_snapshot(starter_pack_mode_project)
        output = format_snapshot_markdown(snapshot)
        
        assert "Verification: success" in output
    
    def test_format_verification_not_run(self, direct_mode_project):
        snapshot = generate_workspace_snapshot(direct_mode_project)
        output = format_snapshot_markdown(snapshot)
        
        assert "Verification: not_run" in output
    
    def test_format_pending_decisions(self, pending_decision_project):
        snapshot = generate_workspace_snapshot(pending_decision_project)
        output = format_snapshot_markdown(snapshot)
        
        assert "Pending Decisions: 1" in output


class TestWorkspaceSnapshotDataclass:
    """Tests for WorkspaceSnapshot dataclass."""
    
    def test_default_values(self):
        snapshot = WorkspaceSnapshot()
        
        assert snapshot.initialization_mode == "unknown"
        assert snapshot.provider_linkage == {}
        assert snapshot.product_id == ""
        assert snapshot.pending_decisions == 0
    
    def test_custom_values(self):
        snapshot = WorkspaceSnapshot(
            initialization_mode="starter-pack",
            product_id="test-001",
            pending_decisions=5,
        )
        
        assert snapshot.initialization_mode == "starter-pack"
        assert snapshot.product_id == "test-001"
        assert snapshot.pending_decisions == 5