# tests/test_workspace_doctor.py

"""Tests for workspace doctor functionality (Feature 029)."""

from pathlib import Path
import pytest
import yaml
from typer.testing import CliRunner

from runtime.workspace_doctor import DoctorDiagnosis, diagnose_workspace, format_diagnosis_markdown, format_diagnosis_yaml
from cli.asyncdev import app as asyncdev_app


runner = CliRunner()


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


class TestDoctorCLI:
    def test_doctor_help_works(self):
        """Doctor command help should work."""
        result = runner.invoke(asyncdev_app, ["doctor", "--help"])
        
        assert result.exit_code == 0
        assert "diagnose" in result.output.lower() or "health" in result.output.lower()

    def test_doctor_show_empty_workspace(self):
        """Doctor show on empty workspace should return UNKNOWN."""
        result = runner.invoke(asyncdev_app, ["doctor", "show", "--path", "nonexistent"])
        
        assert result.exit_code == 0
        assert "UNKNOWN" in result.output

    def test_doctor_yaml_format(self):
        """Doctor with --format yaml should output YAML."""
        result = runner.invoke(asyncdev_app, ["doctor", "show", "--format", "yaml", "--path", "nonexistent"])
        
        assert result.exit_code == 0
        assert "doctor_status:" in result.output


class TestRecoveryPlaybooks:
    def test_blocked_pending_decision_recovery_hints(self, tmp_path):
        """BLOCKED + pending decision should include recovery hints."""
        project = tmp_path / "blocked-decision"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: blocked-decision
feature_id: feature-001
current_phase: reviewing
active_task: review-work
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed:
  - decision: architecture-choice
    options:
      - Option A
      - Option B
last_action: Generated review pack
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        (project / "product-brief.yaml").write_text("product_id: blocked-decision\nname: Blocked Decision\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.likely_cause != ""
        assert len(diagnosis.what_to_check) >= 1
        assert len(diagnosis.recovery_steps) >= 1
        assert diagnosis.fallback_next_step != ""
        assert "decision" in diagnosis.likely_cause.lower()

    def test_blocked_phase_recovery_hints(self, tmp_path):
        """BLOCKED phase should include recovery hints."""
        project = tmp_path / "blocked-phase"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: blocked-phase
feature_id: feature-001
current_phase: blocked
active_task: ""
task_queue: []
completed_outputs: []
blocked_items:
  - item: external-api
    reason: API key pending
decisions_needed: []
last_action: Hit blocker
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        (project / "product-brief.yaml").write_text("product_id: blocked-phase\nname: Blocked Phase\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.likely_cause != ""
        assert len(diagnosis.what_to_check) >= 1
        assert len(diagnosis.recovery_steps) >= 1
        assert diagnosis.fallback_next_step != ""
        assert "block" in diagnosis.likely_cause.lower()

    def test_attention_not_run_recovery_hints(self, tmp_path):
        """ATTENTION_NEEDED + verification not_run should include recovery hints."""
        project = tmp_path / "attention-not-run"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: attention-not-run
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
        (project / "product-brief.yaml").write_text("product_id: attention-not-run\nname: Attention Not Run\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.verification_status == "not_run"
        assert diagnosis.likely_cause != ""
        assert len(diagnosis.what_to_check) >= 1
        assert len(diagnosis.recovery_steps) >= 1
        assert diagnosis.fallback_next_step != ""
        assert "validat" in diagnosis.likely_cause.lower()

    def test_attention_failed_recovery_hints(self, tmp_path):
        """ATTENTION_NEEDED + verification failed should include recovery hints."""
        project = tmp_path / "attention-failed"
        project.mkdir()
        
        (project / "execution-results").mkdir()
        (project / "execution-results" / "exec-001.md").write_text("""---
```yaml
execution_id: exec-001
status: failed
completed_items: []
issues_found:
  - Compatibility mismatch
```
---
""")
        
        runstate_content = """---
```yaml
project_id: attention-failed
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
        (project / "product-brief.yaml").write_text("product_id: attention-failed\nname: Attention Failed\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.verification_status == "failed"
        assert diagnosis.likely_cause != ""
        assert len(diagnosis.what_to_check) >= 1
        assert len(diagnosis.recovery_steps) >= 1
        assert diagnosis.fallback_next_step != ""
        assert "mismatch" in diagnosis.likely_cause.lower() or "missing" in diagnosis.likely_cause.lower()

    def test_completed_closeout_recovery_hints(self, tmp_path):
        """COMPLETED_PENDING_CLOSEOUT should include recovery hints."""
        project = tmp_path / "completed-closeout"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: completed-closeout
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
        (project / "product-brief.yaml").write_text("product_id: completed-closeout\nname: Completed Closeout\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"
        assert diagnosis.likely_cause != ""
        assert len(diagnosis.what_to_check) >= 1
        assert len(diagnosis.recovery_steps) >= 1
        assert diagnosis.fallback_next_step != ""
        assert "closure" in diagnosis.likely_cause.lower() or "closeout" in diagnosis.likely_cause.lower()

    def test_unknown_recovery_hints(self, tmp_path):
        """UNKNOWN status should include recovery hints."""
        project = tmp_path / "unknown-state"
        project.mkdir()
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.likely_cause != ""
        assert len(diagnosis.what_to_check) >= 1
        assert len(diagnosis.recovery_steps) >= 1
        assert diagnosis.fallback_next_step != ""
        assert "missing" in diagnosis.likely_cause.lower()

    def test_healthy_no_recovery_hints(self, tmp_path):
        """HEALTHY status should NOT include recovery hints."""
        project = tmp_path / "healthy-no-hints"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: healthy-no-hints
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
        (project / "product-brief.yaml").write_text("product_id: healthy-no-hints\nname: Healthy No Hints\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.likely_cause == ""
        assert diagnosis.what_to_check == []
        assert diagnosis.recovery_steps == []
        assert diagnosis.fallback_next_step == ""


class TestRecoveryOutputIntegration:
    def test_markdown_includes_recovery_hints(self):
        """Markdown output should include recovery hints section."""
        diagnosis = DoctorDiagnosis(
            doctor_status="BLOCKED",
            likely_cause="Decision pending",
            what_to_check=["decision request", "review context"],
            recovery_steps=["Inspect decision", "Resolve"],
            fallback_next_step="Check nightly pack"
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "Recovery Hints" in output
        assert "Likely Cause" in output
        assert "What To Check" in output
        assert "Recovery Steps" in output
        assert "If This Fails, Try Next" in output
        assert "decision pending" in output.lower()

    def test_yaml_includes_recovery_fields(self):
        """YAML output should include recovery fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="ATTENTION_NEEDED",
            likely_cause="Verification failed",
            what_to_check=["verification output", "compatibility"],
            recovery_steps=["Inspect failure", "Fix mismatch"],
            fallback_next_step="Check docs"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "likely_cause:" in output
        assert "what_to_check:" in output
        assert "recovery_steps:" in output
        assert "fallback_next_step:" in output
        assert "Verification failed" in output

    def test_yaml_without_recovery_fields_clean(self):
        """YAML output without recovery hints should not have recovery keys."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="healthy-app"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "likely_cause:" not in output
        assert "what_to_check:" not in output
        assert "recovery_steps:" not in output


class TestRecoveryBoundary:
    def test_doctor_does_not_mutate_state(self, tmp_path):
        """Doctor should not modify any workspace state."""
        project = tmp_path / "boundary-no-mutate"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: boundary-no-mutate
feature_id: feature-001
current_phase: executing
active_task: test
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Started
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        (project / "product-brief.yaml").write_text("product_id: boundary-no-mutate\nname: Boundary\n")
        
        original_mtime = (project / "runstate.md").stat().st_mtime
        
        diagnose_workspace(project)
        
        new_mtime = (project / "runstate.md").stat().st_mtime
        assert original_mtime == new_mtime


class TestFeedbackHandoff:
    def test_verification_failed_feedback_suggestion(self, tmp_path):
        """ATTENTION_NEEDED + verification failed should suggest feedback handoff."""
        project = tmp_path / "feedback-verify-failed"
        project.mkdir()
        
        (project / "execution-results").mkdir()
        (project / "execution-results" / "exec-001.md").write_text("""---
```yaml
execution_id: exec-001
status: failed
completed_items: []
issues_found:
  - Compatibility mismatch
```
---
""")
        
        runstate_content = """---
```yaml
project_id: feedback-verify-failed
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
        (project / "product-brief.yaml").write_text("product_id: feedback-verify-failed\nname: Feedback Verify Failed\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.verification_status == "failed"
        assert diagnosis.feedback_suggestion != ""
        assert diagnosis.feedback_reason != ""
        assert diagnosis.suggested_feedback_command != ""
        assert "feedback" in diagnosis.feedback_suggestion.lower()
        assert "feedback record" in diagnosis.suggested_feedback_command.lower()

    def test_unknown_feedback_suggestion(self, tmp_path):
        """UNKNOWN status should suggest feedback handoff."""
        project = tmp_path / "feedback-unknown"
        project.mkdir()
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.feedback_suggestion != ""
        assert diagnosis.feedback_reason != ""
        assert diagnosis.suggested_feedback_command != ""
        assert "feedback" in diagnosis.feedback_suggestion.lower()
        assert "feedback record" in diagnosis.suggested_feedback_command.lower()

    def test_healthy_no_feedback_suggestion(self, tmp_path):
        """HEALTHY status should NOT suggest feedback handoff."""
        project = tmp_path / "feedback-healthy"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: feedback-healthy
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
        (project / "product-brief.yaml").write_text("product_id: feedback-healthy\nname: Feedback Healthy\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.feedback_suggestion == ""
        assert diagnosis.feedback_reason == ""
        assert diagnosis.suggested_feedback_command == ""

    def test_completed_no_feedback_suggestion(self, tmp_path):
        """COMPLETED_PENDING_CLOSEOUT should NOT suggest feedback handoff."""
        project = tmp_path / "feedback-completed"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: feedback-completed
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
        (project / "product-brief.yaml").write_text("product_id: feedback-completed\nname: Feedback Completed\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"
        assert diagnosis.feedback_suggestion == ""
        assert diagnosis.feedback_reason == ""
        assert diagnosis.suggested_feedback_command == ""

    def test_blocked_no_feedback_suggestion(self, tmp_path):
        """BLOCKED status should NOT suggest feedback handoff (one-off blocker)."""
        project = tmp_path / "feedback-blocked"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: feedback-blocked
feature_id: feature-001
current_phase: blocked
active_task: ""
task_queue: []
completed_outputs: []
blocked_items:
  - item: external-api
    reason: API key pending
decisions_needed: []
last_action: Hit blocker
updated_at: 2026-04-12T10:00:00Z
```
---
"""
        (project / "runstate.md").write_text(runstate_content)
        (project / "product-brief.yaml").write_text("product_id: feedback-blocked\nname: Feedback Blocked\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.feedback_suggestion == ""
        assert diagnosis.feedback_reason == ""
        assert diagnosis.suggested_feedback_command == ""

    def test_attention_not_run_no_feedback_suggestion(self, tmp_path):
        """ATTENTION_NEEDED + not_run should NOT suggest feedback handoff."""
        project = tmp_path / "feedback-not-run"
        project.mkdir()
        
        runstate_content = """---
```yaml
project_id: feedback-not-run
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
        (project / "product-brief.yaml").write_text("product_id: feedback-not-run\nname: Feedback Not Run\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.verification_status == "not_run"
        assert diagnosis.feedback_suggestion == ""
        assert diagnosis.feedback_reason == ""
        assert diagnosis.suggested_feedback_command == ""


class TestFeedbackHandoffOutput:
    def test_markdown_includes_feedback_suggestion(self):
        """Markdown output should include feedback suggestion section."""
        diagnosis = DoctorDiagnosis(
            doctor_status="ATTENTION_NEEDED",
            verification_status="failed",
            feedback_suggestion="This may be worth capturing as workflow feedback.",
            feedback_reason="Verification failure often indicates systemic friction.",
            suggested_feedback_command="asyncdev feedback record --scope product --description 'Verification failure'"
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "Feedback Suggestion" in output
        assert "This may be worth capturing" in output
        assert "**Why**" in output
        assert "Suggested Feedback Command" in output
        assert "feedback record" in output.lower()

    def test_yaml_includes_feedback_fields(self):
        """YAML output should include feedback fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="UNKNOWN",
            feedback_suggestion="This may be worth capturing as workflow feedback.",
            feedback_reason="Unknown state often indicates missing artifacts.",
            suggested_feedback_command="asyncdev feedback record --scope system --description 'Unknown state'"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "feedback_suggestion:" in output
        assert "feedback_reason:" in output
        assert "suggested_feedback_command:" in output
        assert "workflow feedback" in output

    def test_yaml_without_feedback_fields_clean(self):
        """YAML output without feedback suggestion should not have feedback keys."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="healthy-app"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "feedback_suggestion:" not in output
        assert "feedback_reason:" not in output
        assert "suggested_feedback_command:" not in output

    def test_doctor_does_not_auto_create_feedback(self, tmp_path):
        """Doctor should not automatically create feedback records."""
        project = tmp_path / "feedback-no-auto-create"
        project.mkdir()
        
        (project / "execution-results").mkdir()
        (project / "execution-results" / "exec-001.md").write_text("""---
```yaml
execution_id: exec-001
status: failed
completed_items: []
```
---
""")
        
        (project / "runstate.md").write_text("""---
```yaml
project_id: feedback-no-auto
feature_id: feature-001
current_phase: executing
decisions_needed: []
updated_at: 2026-04-12T10:00:00Z
```
---
""")
        (project / "product-brief.yaml").write_text("product_id: feedback-no-auto\nname: No Auto\n")
        
        feedback_dir = project / "feedback"
        feedback_dir.mkdir()
        (feedback_dir / "existing.yaml").write_text("feedback_id: existing-001\n")
        
        diagnose_workspace(project)
        
        feedback_files = list(feedback_dir.glob("*.yaml"))
        assert len(feedback_files) == 1
        assert feedback_files[0].name == "existing.yaml"


class TestFeedbackDraft:
    def test_verification_failed_draft_summary(self, tmp_path):
        """ATTENTION_NEEDED + verification failed should include draft summary."""
        project = tmp_path / "draft-verify-failed"
        project.mkdir()
        
        (project / "execution-results").mkdir()
        (project / "execution-results" / "exec-001.md").write_text("""---
```yaml
execution_id: exec-001
status: failed
completed_items: []
issues_found:
  - Compatibility mismatch
```
---
""")
        
        (project / "runstate.md").write_text("""---
```yaml
project_id: draft-verify-failed
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
""")
        (project / "product-brief.yaml").write_text("product_id: draft-verify-failed\nname: Draft Verify Failed\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.verification_status == "failed"
        assert diagnosis.feedback_draft_summary != ""
        assert diagnosis.feedback_draft_fields != {}
        assert "Verification failure" in diagnosis.feedback_draft_summary
        assert diagnosis.feedback_draft_fields.get("source") == "doctor"
        assert diagnosis.feedback_draft_fields.get("suggested_tags") is not None

    def test_unknown_draft_summary(self, tmp_path):
        """UNKNOWN status should include draft summary."""
        project = tmp_path / "draft-unknown"
        project.mkdir()
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.feedback_draft_summary != ""
        assert diagnosis.feedback_draft_fields != {}
        assert "Unknown workspace state" in diagnosis.feedback_draft_summary
        assert diagnosis.feedback_draft_fields.get("source") == "doctor"
        assert diagnosis.feedback_draft_fields.get("suggested_category") == "persistence"

    def test_healthy_no_draft_summary(self, tmp_path):
        """HEALTHY status should NOT include draft summary."""
        project = tmp_path / "draft-healthy"
        project.mkdir()
        
        (project / "runstate.md").write_text("""---
```yaml
project_id: draft-healthy
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
""")
        (project / "product-brief.yaml").write_text("product_id: draft-healthy\nname: Draft Healthy\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.feedback_draft_summary == ""
        assert diagnosis.feedback_draft_fields == {}

    def test_completed_no_draft_summary(self, tmp_path):
        """COMPLETED_PENDING_CLOSEOUT should NOT include draft summary."""
        project = tmp_path / "draft-completed"
        project.mkdir()
        
        (project / "runstate.md").write_text("""---
```yaml
project_id: draft-completed
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
""")
        (project / "product-brief.yaml").write_text("product_id: draft-completed\nname: Draft Completed\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"
        assert diagnosis.feedback_draft_summary == ""
        assert diagnosis.feedback_draft_fields == {}

    def test_blocked_no_draft_summary(self, tmp_path):
        """BLOCKED status should NOT include draft summary."""
        project = tmp_path / "draft-blocked"
        project.mkdir()
        
        (project / "runstate.md").write_text("""---
```yaml
project_id: draft-blocked
feature_id: feature-001
current_phase: blocked
active_task: ""
task_queue: []
completed_outputs: []
blocked_items:
  - item: external-api
    reason: API key pending
decisions_needed: []
last_action: Hit blocker
updated_at: 2026-04-12T10:00:00Z
```
---
""")
        (project / "product-brief.yaml").write_text("product_id: draft-blocked\nname: Draft Blocked\n")
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.feedback_draft_summary == ""
        assert diagnosis.feedback_draft_fields == {}


class TestFeedbackDraftOutput:
    def test_markdown_includes_draft_summary(self):
        """Markdown output should include draft summary section."""
        diagnosis = DoctorDiagnosis(
            doctor_status="ATTENTION_NEEDED",
            verification_status="failed",
            feedback_suggestion="This may be worth capturing as workflow feedback.",
            feedback_reason="Verification failure often indicates systemic friction.",
            feedback_draft_summary="Verification failure in direct initialization - likely contract mismatch",
            suggested_feedback_command='asyncdev feedback record --scope product --project my-app --description "Verification failure in direct initialization" --tags verification,contract-mismatch'
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "Feedback Suggestion" in output
        assert "Feedback Draft Summary" in output
        assert "Verification failure in direct initialization" in output
        assert "Suggested Feedback Command" in output
        assert "--tags verification" in output

    def test_yaml_includes_draft_fields(self):
        """YAML output should include draft fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="UNKNOWN",
            feedback_suggestion="This may be worth capturing as workflow feedback.",
            feedback_reason="Unknown state often indicates missing artifacts.",
            feedback_draft_summary="Unknown workspace state - missing artifacts",
            feedback_draft_fields={
                "source": "doctor",
                "doctor_status": "UNKNOWN",
                "suggested_category": "persistence",
                "suggested_tags": ["state-missing", "artifact-corruption"]
            },
            suggested_feedback_command='asyncdev feedback record --scope system --description "Unknown workspace state" --tags state-missing,artifact-corruption'
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "feedback_draft_summary:" in output
        assert "feedback_draft_fields:" in output
        assert "suggested_tags:" in output
        assert "state-missing" in output

    def test_yaml_without_draft_fields_clean(self):
        """YAML output without draft should not have draft keys."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="healthy-app"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "feedback_draft_summary:" not in output
        assert "feedback_draft_fields:" not in output

    def test_command_includes_prefilled_tags(self):
        """Suggested command should include prefilled tags."""
        diagnosis = DoctorDiagnosis(
            doctor_status="ATTENTION_NEEDED",
            verification_status="failed",
            product_id="test-app",
            initialization_mode="starter-pack",
            feedback_suggestion="This may be worth capturing.",
            feedback_reason="Verification failure.",
            feedback_draft_summary="Verification failure in starter-pack initialization",
            feedback_draft_fields={
                "source": "doctor",
                "suggested_tags": ["verification", "contract-mismatch", "tooling-friction"]
            },
            suggested_feedback_command='asyncdev feedback record --scope product --project test-app --description "Verification failure" --tags verification,contract-mismatch,tooling-friction'
        )
        
        assert "--tags verification,contract-mismatch,tooling-friction" in diagnosis.suggested_feedback_command
        assert "--description" in diagnosis.suggested_feedback_command
        assert "--project test-app" in diagnosis.suggested_feedback_command

    def test_draft_fields_contain_expected_keys(self, tmp_path):
        """Draft fields should contain all expected keys."""
        project = tmp_path / "draft-keys-test"
        project.mkdir()
        
        (project / "execution-results").mkdir()
        (project / "execution-results" / "exec-001.md").write_text("""---
```yaml
execution_id: exec-001
status: failed
```
---
""")
        (project / "runstate.md").write_text("""---
```yaml
project_id: draft-keys
feature_id: feature-001
current_phase: executing
decisions_needed: []
updated_at: 2026-04-12T10:00:00Z
```
---
""")
        (project / "product-brief.yaml").write_text("product_id: draft-keys\nname: Draft Keys\n")
        
        diagnosis = diagnose_workspace(project)
        
        draft = diagnosis.feedback_draft_fields
        
        assert draft.get("source") == "doctor"
        assert draft.get("doctor_status") == "ATTENTION_NEEDED"
        assert draft.get("verification_status") == "failed"
        assert draft.get("suggested_category") == "execution_pack"
        assert draft.get("suggested_tags") is not None
        assert len(draft.get("suggested_tags", [])) >= 2