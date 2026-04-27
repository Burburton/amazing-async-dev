"""Tests for Feature 073 - Re-Acceptance Loop Orchestration."""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.reacceptance_loop import (
    ReAcceptanceState,
    ReAcceptancePolicy,
    AcceptanceAttempt,
    AcceptanceAttemptHistory,
    should_trigger_reacceptance,
    determine_reacceptance_state,
    get_or_create_attempt_history,
    save_attempt_history,
    load_attempt_history,
    trigger_reacceptance,
    get_acceptance_lineage,
    MAX_ATTEMPTS_DEFAULT,
)
from runtime.acceptance_runner import (
    AcceptanceResult,
    AcceptanceTerminalState,
    save_acceptance_result,
)
from runtime.acceptance_pack_builder import (
    AcceptancePack,
    VerificationSummary,
    save_acceptance_pack,
)
from runtime.state_store import StateStore


class TestReAcceptanceState:
    
    def test_all_states_defined(self):
        assert ReAcceptanceState.READY_FOR_REACCEPTANCE.value == "ready_for_reacceptance"
        assert ReAcceptanceState.RECOVERY_IN_PROGRESS.value == "recovery_in_progress"
        assert ReAcceptanceState.REACCEPTANCE_TRIGGERED.value == "reacceptance_triggered"
        assert ReAcceptanceState.TERMINAL_SUCCESS.value == "terminal_success"
        assert ReAcceptanceState.TERMINAL_FAILURE.value == "terminal_failure"
        assert ReAcceptanceState.TERMINAL_ESCALATION.value == "terminal_escalation"
        assert ReAcceptanceState.MAX_ATTEMPTS_REACHED.value == "max_attempts_reached"


class TestReAcceptancePolicy:
    
    def test_all_policies_defined(self):
        assert ReAcceptancePolicy.AUTO_RETRY.value == "auto_retry"
        assert ReAcceptancePolicy.MANUAL_TRIGGER.value == "manual_trigger"
        assert ReAcceptancePolicy.ESCALATE_AFTER_FAILURES.value == "escalate_after_failures"


class TestAcceptanceAttempt:
    
    def test_acceptance_attempt_creation(self):
        attempt = AcceptanceAttempt(
            attempt_number=1,
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state="rejected",
            triggered_at="2026-04-25T12:00:00",
        )
        assert attempt.attempt_number == 1
    
    def test_acceptance_attempt_to_dict(self):
        attempt = AcceptanceAttempt(
            attempt_number=1,
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state="rejected",
            triggered_at="2026-04-25T12:00:00",
        )
        d = attempt.to_dict()
        assert d["attempt_number"] == 1


class TestAcceptanceAttemptHistory:
    
    def test_history_creation(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
        )
        assert history.feature_id == "feat-001"
        assert history.total_attempts == 0
    
    def test_history_add_attempt(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
        )
        
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.REJECTED,
            attempt_number=1,
        )
        
        history.add_attempt(result)
        
        assert history.total_attempts == 1
        assert history.rejected_attempts == 1
    
    def test_history_is_terminal_success(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            current_state=ReAcceptanceState.TERMINAL_SUCCESS,
        )
        assert history.is_terminal()
    
    def test_history_is_terminal_failure(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            current_state=ReAcceptanceState.TERMINAL_FAILURE,
        )
        assert history.is_terminal()
    
    def test_history_can_retry_below_max(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            total_attempts=2,
            max_attempts=5,
        )
        assert history.can_retry()
    
    def test_history_cannot_retry_at_max(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            total_attempts=5,
            max_attempts=5,
        )
        assert not history.can_retry()
    
    def test_history_get_latest_result(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            attempts=[
                AcceptanceAttempt(
                    attempt_number=1,
                    acceptance_result_id="ar-001",
                    acceptance_pack_id="ap-001",
                    terminal_state="rejected",
                    triggered_at="2026-04-25T12:00:00",
                ),
                AcceptanceAttempt(
                    attempt_number=2,
                    acceptance_result_id="ar-002",
                    acceptance_pack_id="ap-002",
                    terminal_state="accepted",
                    triggered_at="2026-04-25T13:00:00",
                ),
            ],
        )
        
        latest = history.get_latest_result()
        
        assert latest is not None
        assert latest.attempt_number == 2
    
    def test_history_to_dict(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
        )
        d = history.to_dict()
        assert d["feature_id"] == "feat-001"


class TestShouldTriggerReacceptance:
    
    def test_not_trigger_if_terminal(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            current_state=ReAcceptanceState.TERMINAL_SUCCESS,
        )
        
        should = should_trigger_reacceptance(history)
        assert not should
    
    def test_not_trigger_if_max_attempts(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            total_attempts=5,
            max_attempts=5,
        )
        
        should = should_trigger_reacceptance(history)
        assert not should
    
    def test_not_trigger_if_manual_policy(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            total_attempts=1,
        )
        
        should = should_trigger_reacceptance(history, ReAcceptancePolicy.MANUAL_TRIGGER)
        assert not should
    
    def test_trigger_if_can_retry_and_auto(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            total_attempts=1,
            max_attempts=5,
            attempts=[
                AcceptanceAttempt(
                    attempt_number=1,
                    acceptance_result_id="ar-001",
                    acceptance_pack_id="ap-001",
                    terminal_state="rejected",
                    triggered_at="2026-04-25T12:00:00",
                )
            ],
        )
        
        should = should_trigger_reacceptance(history, ReAcceptancePolicy.AUTO_RETRY)
        assert should


class TestDetermineReacceptanceState:
    
    def test_success_if_accepted(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
        )
        
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.ACCEPTED,
        )
        
        state = determine_reacceptance_state(history, result)
        assert state == ReAcceptanceState.TERMINAL_SUCCESS
    
    def test_success_if_conditional(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
        )
        
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.CONDITIONAL,
        )
        
        state = determine_reacceptance_state(history, result)
        assert state == ReAcceptanceState.TERMINAL_SUCCESS
    
    def test_escalation_if_escalated(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
        )
        
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.ESCALATED,
        )
        
        state = determine_reacceptance_state(history, result)
        assert state == ReAcceptanceState.TERMINAL_ESCALATION
    
    def test_recovery_in_progress_if_rejected(self):
        history = AcceptanceAttemptHistory(
            feature_id="feat-001",
            execution_result_id="exec-001",
            total_attempts=1,
        )
        
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.REJECTED,
        )
        
        state = determine_reacceptance_state(history, result)
        assert state == ReAcceptanceState.RECOVERY_IN_PROGRESS


class TestSaveLoadHistory:
    
    def test_save_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            history = AcceptanceAttemptHistory(
                feature_id="feat-001",
                execution_result_id="exec-001",
            )
            
            history_path = save_attempt_history(project_path, history)
            
            assert history_path.exists()
    
    def test_load_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            history = AcceptanceAttemptHistory(
                feature_id="feat-001",
                execution_result_id="exec-001",
                attempts=[
                    AcceptanceAttempt(
                        attempt_number=1,
                        acceptance_result_id="ar-001",
                        acceptance_pack_id="ap-001",
                        terminal_state="rejected",
                        triggered_at="2026-04-25T12:00:00",
                    )
                ],
                total_attempts=1,
            )
            
            save_attempt_history(project_path, history)
            
            loaded = load_attempt_history(project_path, "feat-001", "exec-001")
            
            assert loaded is not None
            assert loaded.feature_id == "feat-001"
            assert loaded.total_attempts == 1
    
    def test_get_or_create_returns_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            history = AcceptanceAttemptHistory(
                feature_id="feat-get",
                execution_result_id="exec-get",
                total_attempts=3,
            )
            save_attempt_history(project_path, history)
            
            loaded = get_or_create_attempt_history(project_path, "feat-get", "exec-get")
            
            assert loaded.total_attempts == 3
    
    def test_get_or_create_creates_new(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            history = get_or_create_attempt_history(project_path, "feat-new", "exec-new")
            
            assert history.feature_id == "feat-new"
            assert history.total_attempts == 0


class TestTriggerReacceptance:
    
    @pytest.fixture
    def project_with_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            exec_path = execution_results_dir / "exec-trigger.md"
            exec_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-trigger
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items:
  - "Implement"
artifacts_created:
  - name: "artifact"
    path: "artifacts/a.md"
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-trigger"
            features_dir.mkdir(parents=True)
            
            spec_path = features_dir / "feature-spec.md"
            spec_content = """# FeatureSpec

```yaml
feature_id: feat-trigger
acceptance_criteria:
  - criterion_id: AC-001
    text: Works
```
"""
            spec_path.write_text(spec_content)
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-trigger",
                "project_id": "proj-trigger",
            })
            
            history = AcceptanceAttemptHistory(
                feature_id="feat-trigger",
                execution_result_id="exec-trigger",
                attempts=[
                    AcceptanceAttempt(
                        attempt_number=1,
                        acceptance_result_id="ar-prev",
                        acceptance_pack_id="ap-prev",
                        terminal_state="rejected",
                        triggered_at="2026-04-25T11:00:00",
                    )
                ],
                total_attempts=1,
            )
            save_attempt_history(project_path, history)
            
            yield project_path

    def test_trigger_reacceptance_creates_result(self, project_with_history):
        result = trigger_reacceptance(
            project_with_history,
            "exec-trigger",
            "feat-trigger",
            ReAcceptancePolicy.AUTO_RETRY,
        )
        
        assert result is not None
    
    def test_trigger_reacceptance_updates_history(self, project_with_history):
        trigger_reacceptance(
            project_with_history,
            "exec-trigger",
            "feat-trigger",
            ReAcceptancePolicy.AUTO_RETRY,
        )
        
        history = load_attempt_history(project_with_history, "feat-trigger", "exec-trigger")
        
        assert history is not None
        assert history.total_attempts == 2


class TestGetAcceptanceLineage:
    
    def test_get_lineage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            history_dir = project_path / "acceptance-history"
            history_dir.mkdir(parents=True)
            
            history1 = AcceptanceAttemptHistory(
                feature_id="feat-line",
                execution_result_id="exec-1",
                total_attempts=1,
                current_state=ReAcceptanceState.TERMINAL_SUCCESS,
            )
            save_attempt_history(project_path, history1)
            
            history2 = AcceptanceAttemptHistory(
                feature_id="feat-line",
                execution_result_id="exec-2",
                total_attempts=3,
                current_state=ReAcceptanceState.TERMINAL_FAILURE,
            )
            save_attempt_history(project_path, history2)
            
            lineage = get_acceptance_lineage(project_path, "feat-line")
            
            assert len(lineage) == 2
    
    def test_empty_lineage_if_no_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            lineage = get_acceptance_lineage(project_path, "feat-none")
            
            assert len(lineage) == 0