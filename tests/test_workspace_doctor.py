# tests/test_workspace_doctor.py

"""Tests for workspace doctor functionality (Feature 029)."""

from pathlib import Path
import pytest
import yaml

from runtime.workspace_doctor import DoctorDiagnosis, diagnose_workspace, format_diagnosis_markdown, format_diagnosis_yaml


class TestDoctorDiagnosisDataclass:
    def test_default_values(self):
        """DoctorDiagnosis should have sensible defaults."""
        diagnosis = DoctorDiagnosis()
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.health_status == "unknown"
        assert diagnosis.initialization_mode == "unknown"
        assert diagnosis.provider_linkage == {}
        assert diagnosis.product_id == ""
        assert diagnosis.feature_id == ""
        assert diagnosis.current_phase == ""
        assert diagnosis.verification_status == "not_run"
        assert diagnosis.pending_decisions == 0
        assert diagnosis.blocked_items_count == 0
        assert diagnosis.recommended_action == ""
        assert diagnosis.suggested_command == ""
        assert diagnosis.rationale == ""
        assert diagnosis.warnings == []
        assert diagnosis.workspace_path == ""

    def test_custom_values(self):
        """DoctorDiagnosis should accept custom values."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            health_status="healthy",
            product_id="my-app",
            feature_id="feature-001",
            current_phase="planning",
            recommended_action="Plan a task",
            suggested_command="asyncdev plan-day create",
            rationale="Workspace is in planning phase"
        )
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.product_id == "my-app"
        assert diagnosis.recommended_action == "Plan a task"


class TestDiagnoseWorkspace:
    def test_empty_project_returns_unknown(self, tmp_path):
        """Empty project should return UNKNOWN status."""
        empty_project = tmp_path / "empty-project"
        empty_project.mkdir()
        
        diagnosis = diagnose_workspace(empty_project)
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.recommended_action != ""
        assert "init" in diagnosis.suggested_command.lower()

    def test_missing_project_returns_unknown(self, tmp_path):
        """Missing project path should return UNKNOWN."""
        missing = tmp_path / "nonexistent"
        
        diagnosis = diagnose_workspace(missing)
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.workspace_path == str(missing)

    def test_pending_decision_returns_blocked(self, tmp_path):
        """Pending decisions should return BLOCKED status."""
        project = tmp_path / "blocked-project"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: blocked-test
feature_id: feature-001
current_phase: reviewing
active_task: review-work
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed:
  - decision: architecture-choice
    options:
      - Option A
      - Option B
    impact: system design
last_action: Generated review pack
next_recommended_action: Respond to pending decision
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: blocked-test
name: Blocked Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.pending_decisions == 1
        assert "resume" in diagnosis.suggested_command.lower()
        assert len(diagnosis.warnings) >= 1

    def test_blocked_phase_returns_blocked(self, tmp_path):
        """Blocked phase should return BLOCKED status."""
        project = tmp_path / "blocked-phase-project"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: blocked-phase-test
feature_id: feature-001
current_phase: blocked
active_task: ""
task_queue: []
completed_outputs: []
open_questions: []
blocked_items:
  - item: external-api
    reason: API key pending
    since: 2026-04-12T09:00:00Z
decisions_needed: []
last_action: Hit blocker
next_recommended_action: Resolve blocker
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: blocked-phase-test
name: Blocked Phase Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.blocked_items_count >= 1
        assert "unblock" in diagnosis.suggested_command.lower()

    def test_verification_failed_returns_attention(self, tmp_path):
        """Verification failure should return ATTENTION_NEEDED."""
        project = tmp_path / "verify-failed-project"
        project.mkdir()
        
        results_dir = project / "execution-results"
        results_dir.mkdir()
        
        result_content = """---
```yaml
execution_id: exec-failed
status: failed
completed_items: []
issues_found:
  - Compatibility mismatch
```
---
"""
        (results_dir / "exec-001.md").write_text(result_content)
        
        runstate_content = """---
```yaml
project_id: verify-failed
feature_id: feature-001
current_phase: executing
active_task: verify
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Verification failed
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: verify-failed
name: Verify Failed Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.verification_status == "failed"

    def test_no_feature_returns_attention(self, tmp_path):
        """No active feature should return ATTENTION_NEEDED."""
        project = tmp_path / "no-feature-project"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: no-feature
feature_id: ""
current_phase: planning
active_task: ""
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Created product
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: no-feature
name: No Feature Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert "feature" in diagnosis.recommended_action.lower()

    def test_completed_returns_pending_closeout(self, tmp_path):
        """Completed feature should return COMPLETED_PENDING_CLOSEOUT."""
        project = tmp_path / "completed-project"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: completed-test
feature_id: feature-001
current_phase: completed
active_task: ""
task_queue: []
completed_outputs:
  - schemas/test.yaml
blocked_items: []
decisions_needed: []
last_action: Feature completed
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: completed-test
name: Completed Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"
        assert "archive" in diagnosis.suggested_command.lower()

    def test_archived_returns_pending_closeout(self, tmp_path):
        """Archived feature should return COMPLETED_PENDING_CLOSEOUT."""
        project = tmp_path / "archived-project"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: archived-test
feature_id: feature-001
current_phase: archived
active_task: ""
task_queue: []
completed_outputs:
  - schemas/test.yaml
blocked_items: []
decisions_needed: []
last_action: Feature archived
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: archived-test
name: Archived Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"

    def test_healthy_planning_returns_healthy(self, tmp_path):
        """Planning phase with no issues should return HEALTHY."""
        project = tmp_path / "healthy-planning"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: healthy-planning
feature_id: feature-001
current_phase: planning
active_task: ""
task_queue:
  - create-schema
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Created feature
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: healthy-planning
name: Healthy Planning Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert "plan" in diagnosis.suggested_command.lower()

    def test_healthy_executing_returns_healthy(self, tmp_path):
        """Executing phase should return HEALTHY."""
        project = tmp_path / "healthy-executing"
        project.mkdir()
        
        results_dir = project / "execution-results"
        results_dir.mkdir()
        
        result_content = """---
```yaml
execution_id: exec-001
status: success
completed_items:
  - Created schema
```
---
"""
        (results_dir / "exec-001.md").write_text(result_content)
        
        runstate_content = """---
```yaml
project_id: healthy-executing
feature_id: feature-001
current_phase: executing
active_task: create-schema
task_queue: []
completed_outputs:
  - schemas/test.yaml
blocked_items: []
decisions_needed: []
last_action: Started execution
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: healthy-executing
name: Healthy Executing Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.verification_status == "success"

    def test_healthy_reviewing_returns_healthy(self, tmp_path):
        """Reviewing phase should return HEALTHY."""
        project = tmp_path / "healthy-reviewing"
        project.mkdir()
        
        reviews_dir = project / "reviews"
        reviews_dir.mkdir()
        
        review_content = """---
```yaml
review_id: review-001
status: pending_review
```
---
"""
        (reviews_dir / "2026-04-12-review.md").write_text(review_content)
        
        runstate_content = """---
```yaml
project_id: healthy-reviewing
feature_id: feature-001
current_phase: reviewing
active_task: ""
task_queue: []
completed_outputs:
  - schemas/test.yaml
blocked_items: []
decisions_needed: []
last_action: Generated review pack
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: healthy-reviewing
name: Healthy Reviewing Test
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"

    def test_starter_pack_healthy_returns_healthy(self, tmp_path):
        """Starter-pack mode healthy should return HEALTHY with provider linkage."""
        project = tmp_path / "starter-pack-healthy"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: starter-healthy
feature_id: feature-001
current_phase: planning
active_task: ""
task_queue:
  - create-schema
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Created feature
updated_at: 2026-04-12T10:00:00Z
workflow_hints:
  policy_mode: balanced
  execution: external-tool-first
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: starter-healthy
name: Starter Pack Healthy Test
starter_pack_context:
  - 'Product type: ai_tooling'
  - 'Stage: mvp'
  - 'Team mode: solo'
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.initialization_mode == "starter-pack"
        assert diagnosis.provider_linkage.get("detected") == True
        assert diagnosis.provider_linkage.get("product_type") == "ai_tooling"

    def test_starter_pack_verify_failed_mentions_provider(self, tmp_path):
        """Starter-pack verification failed should mention provider issue."""
        project = tmp_path / "starter-pack-verify-failed"
        project.mkdir()
        
        results_dir = project / "execution-results"
        results_dir.mkdir()
        
        result_content = """---
```yaml
execution_id: exec-failed
status: failed
completed_items: []
issues_found:
  - Contract version mismatch
```
---
"""
        (results_dir / "exec-001.md").write_text(result_content)
        
        runstate_content = """---
```yaml
project_id: starter-verify-failed
feature_id: feature-001
current_phase: executing
active_task: verify
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Verification failed
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = """product_id: starter-verify-failed
name: Starter Pack Verify Failed Test
starter_pack_context:
  - 'Product type: web_app'
"""
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.initialization_mode == "starter-pack"
        assert "starter-pack" in diagnosis.suggested_command.lower() or "compatibility" in diagnosis.rationale.lower()
        assert len(diagnosis.warnings) >= 1


class TestFormatDiagnosis:
    def test_format_markdown_contains_all_fields(self):
        """Markdown format should contain all key fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="my-app",
            feature_id="feature-001",
            current_phase="planning",
            recommended_action="Plan a task",
            suggested_command="asyncdev plan-day create",
            rationale="Workspace is healthy"
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "HEALTHY" in output
        assert "my-app" in output
        assert "feature-001" in output
        assert "planning" in output
        assert "Plan a task" in output
        assert "asyncdev plan-day create" in output

    def test_format_yaml_contains_all_fields(self):
        """YAML format should contain all key fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="BLOCKED",
            product_id="blocked-app",
            pending_decisions=2,
            recommended_action="Respond to decisions",
            suggested_command="asyncdev resume",
            rationale="2 decisions pending"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "doctor_status: BLOCKED" in output
        assert "product_id: blocked-app" in output
        assert "pending_decisions: 2" in output

    def test_format_markdown_with_warnings(self):
        """Markdown format should include warnings."""
        diagnosis = DoctorDiagnosis(
            doctor_status="BLOCKED",
            warnings=["Do not proceed", "Contact admin"]
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "Do not proceed" in output
        assert "Contact admin" in output

    def test_format_yaml_valid_yaml(self):
        """YAML format should be valid YAML."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="test-app"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        parsed = yaml.safe_load(output)
        assert parsed["doctor_status"] == "HEALTHY"
        assert parsed["execution_state"]["product_id"] == "test-app"