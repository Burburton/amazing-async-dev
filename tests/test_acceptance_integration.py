"""Integration Tests for Acceptance Flow - Features 069-076.

End-to-end tests for complete acceptance validation pipeline:
- ExecutionResult → AcceptancePack → AcceptanceResult → Recovery → ReAcceptance
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.state_store import StateStore
from runtime.acceptance_readiness import (
    check_acceptance_readiness,
    AcceptanceReadiness,
    AcceptanceTriggerPolicyMode,
)
from runtime.acceptance_pack_builder import (
    build_acceptance_pack,
    save_acceptance_pack,
    load_acceptance_pack,
)
from runtime.acceptance_runner import (
    AcceptanceRunner,
    run_acceptance_from_execution,
    save_acceptance_result,
    load_acceptance_result,
    AcceptanceTerminalState,
)
from runtime.acceptance_recovery import (
    process_failed_acceptance,
    load_acceptance_recovery_pack,
    get_recovery_items_for_feature,
)
from runtime.reacceptance_loop import (
    trigger_reacceptance,
    load_attempt_history,
    ReAcceptancePolicy,
)
from runtime.acceptance_console import (
    get_acceptance_summary,
    show_recovery_status,
)
from runtime.acceptance_gating import (
    check_completion_gate,
    validate_acceptance_for_completion,
    CompletionGateResult,
)


class TestFullAcceptanceFlow:
    """Test complete acceptance flow from execution to completion gate."""
    
    @pytest.fixture
    def project_full_flow(self):
        """Project with execution result ready for acceptance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            exec_path = execution_results_dir / "exec-flow.md"
            exec_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-flow
status: success
closeout_state: closeout_completed_success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items:
  - "Implement feature"
  - "Add tests"
artifacts_created:
  - name: "feature.py"
    path: "src/feature.py"
  - name: "test_feature.py"
    path: "tests/test_feature.py"
browser_verification:
  executed: true
  passed: 3
  failed: 0
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-flow"
            features_dir.mkdir(parents=True)
            
            spec_path = features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-flow
name: Integration Test Feature
acceptance_criteria:
  - criterion_id: AC-001
    text: Feature implements core functionality
  - criterion_id: AC-002
    text: Tests pass successfully
  - criterion_id: AC-003
    text: Code follows conventions
```
""")
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-flow",
                "project_id": "proj-flow",
                "blocked_items": [],
                "decisions_needed": [],
            })
            
            yield project_path

    def test_step1_check_acceptance_readiness(self, project_full_flow):
        """Step 1: Check if execution is ready for acceptance."""
        readiness_result = check_acceptance_readiness(
            project_full_flow,
            "exec-flow",
        )
        
        assert readiness_result.readiness == AcceptanceReadiness.READY
        assert readiness_result.trigger_allowed
        assert all(p.satisfied for p in readiness_result.prerequisites_checked)

    def test_step2_build_acceptance_pack(self, project_full_flow):
        """Step 2: Build AcceptancePack from ExecutionResult."""
        pack = build_acceptance_pack(project_full_flow, "exec-flow")
        
        assert pack is not None
        assert pack.feature_id == "feat-flow"
        assert len(pack.acceptance_criteria) == 3
        
        pack_path = save_acceptance_pack(project_full_flow, pack)
        assert pack_path.exists()

    def test_step3_run_acceptance(self, project_full_flow):
        """Step 3: Run acceptance validation."""
        result = run_acceptance_from_execution(project_full_flow, "exec-flow")
        
        assert result is not None
        assert result.terminal_state in [
            AcceptanceTerminalState.ACCEPTED,
            AcceptanceTerminalState.CONDITIONAL,
        ]
        
        results_dir = project_full_flow / "acceptance-results"
        assert results_dir.exists()

    def test_step4_verify_acceptance_result(self, project_full_flow):
        """Step 4: Verify AcceptanceResult persisted correctly."""
        result = run_acceptance_from_execution(project_full_flow, "exec-flow")
        
        loaded = load_acceptance_result(project_full_flow, result.acceptance_result_id)
        
        assert loaded is not None
        assert loaded.terminal_state == result.terminal_state

    def test_step5_get_acceptance_summary(self, project_full_flow):
        """Step 5: Get acceptance summary for feature."""
        run_acceptance_from_execution(project_full_flow, "exec-flow")
        
        summary = get_acceptance_summary(project_full_flow, "feat-flow")
        
        assert summary["status"] in ["accepted", "conditional"]
        assert summary["accepted_criteria"] >= 0

    def test_step6_check_completion_gate(self, project_full_flow):
        """Step 6: Check completion gate for accepted feature."""
        run_acceptance_from_execution(project_full_flow, "exec-flow")
        
        gate_check = check_completion_gate(project_full_flow, "feat-flow")
        
        assert gate_check.is_allowed()
        assert gate_check.result in [
            CompletionGateResult.ALLOWED,
            CompletionGateResult.BYPASS_ALLOWED,
        ]

    def test_full_flow_success(self, project_full_flow):
        """Complete flow: readiness → pack → result → gate."""
        
        readiness = check_acceptance_readiness(project_full_flow, "exec-flow")
        assert readiness.readiness == AcceptanceReadiness.READY
        
        pack = build_acceptance_pack(project_full_flow, "exec-flow")
        assert pack is not None
        save_acceptance_pack(project_full_flow, pack)
        
        result = run_acceptance_from_execution(project_full_flow, "exec-flow")
        assert result is not None
        
        summary = get_acceptance_summary(project_full_flow, "feat-flow")
        assert summary["status"] in ["accepted", "conditional", "rejected"]
        
        gate = check_completion_gate(project_full_flow, "feat-flow")
        
        if result.terminal_state in [AcceptanceTerminalState.ACCEPTED, AcceptanceTerminalState.CONDITIONAL]:
            assert gate.is_allowed()


class TestAcceptanceRecoveryFlow:
    """Test flow when acceptance fails."""
    
    @pytest.fixture
    def project_with_recovery(self):
        """Project setup for recovery flow testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            exec_path = execution_results_dir / "exec-recovery.md"
            exec_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-recovery
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items:
  - "Partial implementation"
artifacts_created: []
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-recovery"
            features_dir.mkdir(parents=True)
            
            spec_path = features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-recovery
acceptance_criteria:
  - criterion_id: AC-001
    text: Must have evidence
```
""")
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-recovery",
                "project_id": "proj-recovery",
                "blocked_items": [],
                "decisions_needed": [],
            })
            
            yield project_path

    def test_recovery_flow(self, project_with_recovery):
        """Test recovery creation when acceptance fails."""
        
        result = run_acceptance_from_execution(project_with_recovery, "exec-recovery")
        
        if result.terminal_state == AcceptanceTerminalState.REJECTED:
            recovery_pack = process_failed_acceptance(
                project_with_recovery,
                result.acceptance_result_id,
            )
            
            assert recovery_pack is not None
            assert len(recovery_pack.recovery_items) > 0
            
            recovery_dir = project_with_recovery / "acceptance-recovery"
            assert recovery_dir.exists()
            
            items = get_recovery_items_for_feature(project_with_recovery, "feat-recovery")
            assert len(items) > 0

    def test_gate_blocked_if_failed(self, project_with_recovery):
        """Completion gate should block if acceptance failed."""
        result = run_acceptance_from_execution(project_with_recovery, "exec-recovery")
        
        if result.terminal_state == AcceptanceTerminalState.REJECTED:
            process_failed_acceptance(project_with_recovery, result.acceptance_result_id)
            
            gate = check_completion_gate(project_with_recovery, "feat-recovery")
            
            assert not gate.is_allowed()
            assert gate.result == CompletionGateResult.BLOCKED_ACCEPTANCE_FAILED


class TestReAcceptanceLoopFlow:
    """Test re-acceptance loop after recovery."""
    
    @pytest.fixture
    def project_for_loop(self):
        """Project for re-acceptance loop testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            exec_path = execution_results_dir / "exec-loop.md"
            exec_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-loop
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items:
  - "Implement"
artifacts_created:
  - name: "artifact"
    path: "artifact.md"
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-loop"
            features_dir.mkdir(parents=True)
            
            spec_path = features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-loop
acceptance_criteria:
  - criterion_id: AC-001
    text: Works
```
""")
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-loop",
                "project_id": "proj-loop",
                "blocked_items": [],
                "decisions_needed": [],
            })
            
            yield project_path

    def test_attempt_history_tracking(self, project_for_loop):
        """Test that attempt history is tracked."""
        
        result1 = run_acceptance_from_execution(project_for_loop, "exec-loop")
        
        if result1.terminal_state == AcceptanceTerminalState.REJECTED:
            history = load_attempt_history(project_for_loop, "feat-loop", "exec-loop")
            
            if history is None:
                trigger_reacceptance(
                    project_for_loop,
                    "exec-loop",
                    "feat-loop",
                    ReAcceptancePolicy.AUTO_RETRY,
                )
                
                history = load_attempt_history(project_for_loop, "feat-loop", "exec-loop")
            
            if history:
                assert history.total_attempts >= 1


class TestAcceptanceConsoleIntegration:
    """Test acceptance console functions with real data."""
    
    @pytest.fixture
    def project_for_console(self):
        """Project for console testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            exec_path = execution_results_dir / "exec-console.md"
            exec_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-console
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items: ["Implement"]
artifacts_created: [{"name": "a", "path": "a.py"}]
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-console"
            features_dir.mkdir(parents=True)
            
            spec_path = features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-console
acceptance_criteria:
  - criterion_id: AC-001
    text: Works
```
""")
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-console",
                "project_id": "proj-console",
                "blocked_items": [],
                "decisions_needed": [],
            })
            
            yield project_path

    def test_console_summary_after_acceptance(self, project_for_console):
        """Console should show correct summary after acceptance."""
        run_acceptance_from_execution(project_for_console, "exec-console")
        
        summary = get_acceptance_summary(project_for_console, "feat-console")
        
        assert summary["feature_id"] == "feat-console"
        assert "status" in summary
        assert "next_action" in summary

    def test_console_recovery_status(self, project_for_console):
        """Console should show recovery status if applicable."""
        result = run_acceptance_from_execution(project_for_console, "exec-console")
        
        if result.terminal_state == AcceptanceTerminalState.REJECTED:
            process_failed_acceptance(project_for_console, result.acceptance_result_id)
            
            recovery = show_recovery_status(project_for_console, "feat-console")
            
            assert recovery["pending_items"] >= 0


class TestPolicyModeIntegration:
    """Test different policy modes in full flow."""
    
    @pytest.fixture
    def project_for_policy(self):
        """Project for policy testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            exec_path = execution_results_dir / "exec-policy.md"
            exec_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-policy
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items: ["Implement"]
artifacts_created: []
```
""")
            
            features_dir = project_path / "docs" / "features" / "feat-policy"
            features_dir.mkdir(parents=True)
            
            spec_path = features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-policy
acceptance_criteria:
  - criterion_id: AC-001
    text: Works
```
""")
            
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-policy",
                "project_id": "proj-policy",
                "blocked_items": [],
                "decisions_needed": [],
            })
            
            yield project_path

    def test_optional_policy_bypasses_acceptance(self, project_for_policy):
        """Optional policy should allow completion without acceptance."""
        from runtime.acceptance_gating import AcceptancePolicyMode
        
        gate = check_completion_gate(
            project_for_policy,
            "feat-policy",
            AcceptancePolicyMode.OPTIONAL,
        )
        
        assert gate.is_allowed()
        assert not gate.required_acceptance

    def test_relaxed_policy_allows(self, project_for_policy):
        """Relaxed policy should allow completion."""
        from runtime.acceptance_gating import AcceptancePolicyMode
        
        gate = check_completion_gate(
            project_for_policy,
            "feat-policy",
            AcceptancePolicyMode.RELAXED,
        )
        
        assert gate.is_allowed()