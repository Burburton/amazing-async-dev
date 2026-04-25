"""Tests for Feature 070 - Observer-Triggered Acceptance Readiness."""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.acceptance_readiness import (
    AcceptanceReadiness,
    AcceptanceTriggerPolicyMode,
    AcceptanceReadinessResult,
    PrerequisiteCheck,
    check_acceptance_readiness,
    check_prerequisite_execution_complete,
    check_prerequisite_closeout_success,
    check_prerequisite_verification_pass,
    check_prerequisite_no_blockers,
    check_prerequisite_no_pending_decisions,
    check_prerequisite_feature_spec_has_criteria,
    is_acceptance_triggerable,
    should_auto_trigger_acceptance,
)


class TestAcceptanceReadinessStates:
    
    def test_all_states_defined(self):
        assert AcceptanceReadiness.READY.value == "ready"
        assert AcceptanceReadiness.NOT_READY.value == "not_ready"
        assert AcceptanceReadiness.BLOCKED.value == "blocked"
        assert AcceptanceReadiness.POLICY_SKIPPED.value == "policy_skipped"
        assert AcceptanceReadiness.NO_CRITERIA.value == "no_criteria"

    def test_state_count(self):
        assert len(list(AcceptanceReadiness)) == 5


class TestPolicyModes:
    
    def test_all_modes_defined(self):
        assert AcceptanceTriggerPolicyMode.ALWAYS_TRIGGER.value == "always_trigger"
        assert AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY.value == "feature_completion_only"
        assert AcceptanceTriggerPolicyMode.MANUAL_ONLY.value == "manual_only"

    def test_default_mode_is_feature_completion(self):
        assert AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY.value == "feature_completion_only"


class TestPrerequisiteChecks:
    
    def test_execution_complete_success(self):
        result = check_prerequisite_execution_complete({"status": "success"})
        assert result.satisfied
        assert result.name == "execution_complete"

    def test_execution_complete_failure(self):
        result = check_prerequisite_execution_complete({"status": "failed"})
        assert not result.satisfied
        assert result.failure_reason is not None

    def test_closeout_success_passes(self):
        result = check_prerequisite_closeout_success({
            "closeout_state": "closeout_completed_success",
            "closeout_terminal_state": "success",
        })
        assert result.satisfied

    def test_closeout_success_fails(self):
        result = check_prerequisite_closeout_success({
            "closeout_terminal_state": "failure",
        })
        assert not result.satisfied

    def test_verification_pass_success(self):
        result = check_prerequisite_verification_pass({
            "orchestration_terminal_state": "success",
        })
        assert result.satisfied

    def test_verification_pass_not_required(self):
        result = check_prerequisite_verification_pass({
            "orchestration_terminal_state": "not_required",
        })
        assert result.satisfied

    def test_verification_pass_failure(self):
        result = check_prerequisite_verification_pass({
            "orchestration_terminal_state": "failure",
        })
        assert not result.satisfied

    def test_verification_pass_browser_failed(self):
        result = check_prerequisite_verification_pass({
            "orchestration_terminal_state": "success",
            "browser_verification": {"executed": True, "passed": 2, "failed": 1},
        })
        assert not result.satisfied

    def test_no_blockers_passes(self):
        result = check_prerequisite_no_blockers({"blocked_items": []})
        assert result.satisfied

    def test_no_blockers_fails(self):
        result = check_prerequisite_no_blockers({"blocked_items": ["blocker-1"]})
        assert not result.satisfied

    def test_no_pending_decisions_passes(self):
        result = check_prerequisite_no_pending_decisions({"decisions_needed": []})
        assert result.satisfied

    def test_no_pending_decisions_fails(self):
        result = check_prerequisite_no_pending_decisions({"decisions_needed": ["decision-1"]})
        assert not result.satisfied

    def test_feature_spec_has_criteria_passes(self):
        result = check_prerequisite_feature_spec_has_criteria({
            "acceptance_criteria": ["AC-001: System works"],
        })
        assert result.satisfied

    def test_feature_spec_has_criteria_fails_empty(self):
        result = check_prerequisite_feature_spec_has_criteria({
            "acceptance_criteria": [],
        })
        assert not result.satisfied

    def test_feature_spec_has_criteria_fails_none(self):
        result = check_prerequisite_feature_spec_has_criteria(None)
        assert not result.satisfied


class TestCheckAcceptanceReadiness:
    
    @pytest.fixture
    def ready_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            execution_result_path = execution_results_dir / "exec-test-001.md"
            execution_result_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-test-001
status: success
closeout_state: closeout_completed_success
closeout_terminal_state: success
orchestration_terminal_state: success
browser_verification:
  executed: true
  passed: 3
  failed: 0
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-001"
            features_dir.mkdir(parents=True)
            
            feature_spec_path = features_dir / "feature-spec.md"
            feature_spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-001
name: Test Feature
acceptance_criteria:
  - AC-001: Works correctly
```
""")
            
            runstate_dir = project_path / "state"
            runstate_dir.mkdir()
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "blocked_items": [],
                "decisions_needed": [],
                "feature_id": "feat-001",
            })
            
            yield project_path

    @pytest.fixture
    def blocked_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            execution_result_path = execution_results_dir / "exec-test-002.md"
            execution_result_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-test-002
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
```
""")
            
            yield project_path

    @pytest.fixture
    def no_criteria_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            execution_result_path = execution_results_dir / "exec-test-003.md"
            execution_result_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-test-003
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-002"
            features_dir.mkdir(parents=True)
            
            feature_spec_path = features_dir / "feature-spec.md"
            feature_spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-002
name: No Criteria Feature
acceptance_criteria: []
```
""")
            
            yield project_path

    def test_all_prerequisites_satisfied(self, ready_project):
        result = check_acceptance_readiness(ready_project, "exec-test-001")
        assert result.readiness == AcceptanceReadiness.READY
        assert all(p.satisfied for p in result.prerequisites_checked)

    def test_blocked_state_detected(self, blocked_project):
        from runtime.state_store import StateStore
        
        store = StateStore(blocked_project)
        store.save_runstate({
            "blocked_items": ["blocker-1"],
            "decisions_needed": [],
            "feature_id": "feat-001",
        })
        
        result = check_acceptance_readiness(blocked_project, "exec-test-002")
        assert result.readiness == AcceptanceReadiness.BLOCKED

    def test_no_criteria_detected(self, no_criteria_project):
        from runtime.state_store import StateStore
        
        store = StateStore(no_criteria_project)
        store.save_runstate({
            "blocked_items": [],
            "decisions_needed": [],
            "feature_id": "feat-002",
        })
        
        result = check_acceptance_readiness(no_criteria_project, "exec-test-003")
        assert result.readiness == AcceptanceReadiness.NO_CRITERIA

    def test_policy_always_trigger(self, ready_project):
        result = check_acceptance_readiness(
            ready_project,
            "exec-test-001",
            AcceptanceTriggerPolicyMode.ALWAYS_TRIGGER,
        )
        assert result.trigger_recommended

    def test_policy_manual_only(self, ready_project):
        result = check_acceptance_readiness(
            ready_project,
            "exec-test-001",
            AcceptanceTriggerPolicyMode.MANUAL_ONLY,
        )
        assert not result.trigger_recommended
        assert result.readiness == AcceptanceReadiness.POLICY_SKIPPED

    def test_prerequisites_recorded(self, ready_project):
        result = check_acceptance_readiness(ready_project, "exec-test-001")
        
        expected_prerequisites = [
            "execution_complete",
            "closeout_success",
            "verification_pass",
            "no_blockers",
            "no_pending_decisions",
            "feature_spec_has_criteria",
        ]
        
        checked_names = [p.name for p in result.prerequisites_checked]
        for prereq in expected_prerequisites:
            assert prereq in checked_names

    def test_blocking_reasons_recorded(self, blocked_project):
        from runtime.state_store import StateStore
        
        store = StateStore(blocked_project)
        store.save_runstate({
            "blocked_items": ["blocker-1"],
            "decisions_needed": [],
        })
        
        result = check_acceptance_readiness(blocked_project, "exec-test-002")
        assert len(result.blocking_reasons) > 0

    def test_trigger_allowed_when_ready(self, ready_project):
        result = check_acceptance_readiness(ready_project, "exec-test-001")
        assert result.trigger_allowed

    def test_trigger_not_allowed_when_blocked(self, blocked_project):
        from runtime.state_store import StateStore
        
        store = StateStore(blocked_project)
        store.save_runstate({
            "blocked_items": ["blocker-1"],
        })
        
        result = check_acceptance_readiness(blocked_project, "exec-test-002")
        assert not result.trigger_allowed


class TestConvenienceFunctions:
    
    @pytest.fixture
    def ready_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            execution_result_path = execution_results_dir / "exec-conv-001.md"
            execution_result_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-conv-001
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-001"
            features_dir.mkdir(parents=True)
            
            feature_spec_path = features_dir / "feature-spec.md"
            feature_spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-001
acceptance_criteria:
  - AC-001
```
""")
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "blocked_items": [],
                "decisions_needed": [],
                "feature_id": "feat-001",
            })
            
            yield project_path

    def test_is_acceptance_triggerable(self, ready_project):
        triggerable = is_acceptance_triggerable(ready_project, "exec-conv-001")
        assert triggerable

    def test_should_auto_trigger_acceptance(self, ready_project):
        should_trigger = should_auto_trigger_acceptance(
            ready_project,
            "exec-conv-001",
            AcceptanceTriggerPolicyMode.ALWAYS_TRIGGER,
        )
        assert should_trigger

    def test_should_not_auto_trigger_manual(self, ready_project):
        should_trigger = should_auto_trigger_acceptance(
            ready_project,
            "exec-conv-001",
            AcceptanceTriggerPolicyMode.MANUAL_ONLY,
        )
        assert not should_trigger


class TestAcceptanceReadinessResult:
    
    def test_to_dict(self):
        result = AcceptanceReadinessResult(
            readiness=AcceptanceReadiness.READY,
            execution_result_id="exec-test",
            feature_id="feat-001",
            product_id="proj-001",
            prerequisites_checked=[
                PrerequisiteCheck("test", "Test check", True),
            ],
            prerequisites_satisfied=["test"],
            prerequisites_failed=[],
            blocking_reasons=[],
            trigger_allowed=True,
            trigger_recommended=True,
            policy_mode=AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY,
            policy_decision="Test decision",
        )
        
        d = result.to_dict()
        
        assert d["readiness"] == "ready"
        assert d["execution_result_id"] == "exec-test"
        assert d["trigger_allowed"] is True

    def test_is_triggerable(self):
        ready_result = AcceptanceReadinessResult(
            readiness=AcceptanceReadiness.READY,
            execution_result_id="exec-test",
            trigger_allowed=True,
        )
        assert ready_result.is_triggerable()
        
        blocked_result = AcceptanceReadinessResult(
            readiness=AcceptanceReadiness.BLOCKED,
            execution_result_id="exec-test",
            trigger_allowed=False,
        )
        assert not blocked_result.is_triggerable()

    def test_should_auto_trigger(self):
        result = AcceptanceReadinessResult(
            readiness=AcceptanceReadiness.READY,
            execution_result_id="exec-test",
            trigger_allowed=True,
            trigger_recommended=True,
        )
        assert result.should_auto_trigger()