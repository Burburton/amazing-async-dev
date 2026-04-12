# tests/test_workspace_doctor.py

"""Tests for workspace doctor functionality (Feature 029)."""

from pathlib import Path
import pytest

from runtime.workspace_doctor import DoctorDiagnosis, diagnose_workspace


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