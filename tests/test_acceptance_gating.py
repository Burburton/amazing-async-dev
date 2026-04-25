"""Tests for Feature 075 - Policy and Gating Integration."""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.acceptance_gating import (
    CompletionGateResult,
    AcceptancePolicyMode,
    CompletionGateCheck,
    check_completion_gate,
    validate_acceptance_for_completion,
    get_acceptance_gate_summary,
    is_valid_terminal_state_for_completion,
    get_feature_completion_requirements,
    BYPASS_SCENARIOS,
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
from runtime.acceptance_recovery import (
    AcceptanceRecoveryPack,
    RecoveryItem,
    RecoveryCategory,
    RecoveryPriority,
    save_acceptance_recovery_pack,
)


class TestCompletionGateResult:
    
    def test_all_results_defined(self):
        assert CompletionGateResult.ALLOWED.value == "allowed"
        assert CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED.value == "blocked_acceptance_required"
        assert CompletionGateResult.BLOCKED_ACCEPTANCE_FAILED.value == "blocked_acceptance_failed"
        assert CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING.value == "blocked_acceptance_pending"
        assert CompletionGateResult.BLOCKED_RECOVERY_ITEMS.value == "blocked_recovery_items"
        assert CompletionGateResult.BYPASS_ALLOWED.value == "bypass_allowed"


class TestAcceptancePolicyMode:
    
    def test_all_modes_defined(self):
        assert AcceptancePolicyMode.STRICT.value == "strict"
        assert AcceptancePolicyMode.RELAXED.value == "relaxed"
        assert AcceptancePolicyMode.OPTIONAL.value == "optional"
        assert AcceptancePolicyMode.BYPASS_ALLOWED.value == "bypass_allowed"


class TestCompletionGateCheck:
    
    def test_check_creation(self):
        check = CompletionGateCheck(
            result=CompletionGateResult.ALLOWED,
            feature_id="feat-001",
        )
        assert check.result == CompletionGateResult.ALLOWED
    
    def test_check_is_allowed(self):
        allowed = CompletionGateCheck(
            result=CompletionGateResult.ALLOWED,
            feature_id="feat-001",
        )
        assert allowed.is_allowed()
        
        blocked = CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED,
            feature_id="feat-001",
        )
        assert not blocked.is_allowed()
    
    def test_check_requires_acceptance(self):
        required = CompletionGateCheck(
            result=CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED,
            feature_id="feat-001",
        )
        assert required.requires_acceptance()
        
        allowed = CompletionGateCheck(
            result=CompletionGateResult.ALLOWED,
            feature_id="feat-001",
        )
        assert not allowed.requires_acceptance()
    
    def test_check_to_dict(self):
        check = CompletionGateCheck(
            result=CompletionGateResult.ALLOWED,
            feature_id="feat-001",
        )
        d = check.to_dict()
        assert d["result"] == "allowed"


class TestCheckCompletionGate:
    
    def test_blocked_if_no_acceptance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            check = check_completion_gate(Path(tmpdir), "feat-no-acceptance")
            
            assert check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_REQUIRED
            assert check.required_acceptance
    
    def test_allowed_if_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-accepted",
                feature_id="feat-accepted",
                execution_result_id="exec-accepted",
                product_id="proj-accepted",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-accepted",
                acceptance_pack_id="ap-accepted",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
            )
            save_acceptance_result(project_path, result)
            
            check = check_completion_gate(project_path, "feat-accepted")
            
            assert check.result == CompletionGateResult.ALLOWED
    
    def test_allowed_if_conditional(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-cond",
                feature_id="feat-cond",
                execution_result_id="exec-cond",
                product_id="proj-cond",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-cond",
                acceptance_pack_id="ap-cond",
                terminal_state=AcceptanceTerminalState.CONDITIONAL,
            )
            save_acceptance_result(project_path, result)
            
            check = check_completion_gate(project_path, "feat-cond")
            
            assert check.result == CompletionGateResult.ALLOWED
    
    def test_blocked_if_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-rejected",
                feature_id="feat-rejected",
                execution_result_id="exec-rejected",
                product_id="proj-rejected",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-rejected",
                acceptance_pack_id="ap-rejected",
                terminal_state=AcceptanceTerminalState.REJECTED,
                failed_criteria=["AC-001"],
            )
            save_acceptance_result(project_path, result)
            
            check = check_completion_gate(project_path, "feat-rejected")
            
            assert check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_FAILED
    
    def test_blocked_if_manual_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-review",
                feature_id="feat-review",
                execution_result_id="exec-review",
                product_id="proj-review",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-review",
                acceptance_pack_id="ap-review",
                terminal_state=AcceptanceTerminalState.MANUAL_REVIEW,
            )
            save_acceptance_result(project_path, result)
            
            check = check_completion_gate(project_path, "feat-review")
            
            assert check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING
    
    def test_blocked_if_escalated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-escalated",
                feature_id="feat-escalated",
                execution_result_id="exec-escalated",
                product_id="proj-escalated",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-escalated",
                acceptance_pack_id="ap-escalated",
                terminal_state=AcceptanceTerminalState.ESCALATED,
            )
            save_acceptance_result(project_path, result)
            
            check = check_completion_gate(project_path, "feat-escalated")
            
            assert check.result == CompletionGateResult.BLOCKED_ACCEPTANCE_PENDING
    
    def test_optional_policy_allows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            check = check_completion_gate(
                Path(tmpdir),
                "feat-optional",
                AcceptancePolicyMode.OPTIONAL,
            )
            
            assert check.result == CompletionGateResult.ALLOWED
            assert not check.required_acceptance
    
    def test_relaxed_policy_allows_no_acceptance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            check = check_completion_gate(
                Path(tmpdir),
                "feat-relaxed",
                AcceptancePolicyMode.RELAXED,
            )
            
            assert check.result == CompletionGateResult.ALLOWED
    
    def test_bypass_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            check = check_completion_gate(
                Path(tmpdir),
                "feat-bypass",
                AcceptancePolicyMode.BYPASS_ALLOWED,
                bypass_requested=True,
                bypass_reason="no_acceptance_criteria",
            )
            
            assert check.result == CompletionGateResult.BYPASS_ALLOWED
            assert check.bypass_allowed


class TestValidateAcceptanceForCompletion:
    
    def test_validate_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-val",
                feature_id="feat-val",
                execution_result_id="exec-val",
                product_id="proj-val",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-val",
                acceptance_pack_id="ap-val",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
            )
            save_acceptance_result(project_path, result)
            
            allowed, reason = validate_acceptance_for_completion(project_path, "feat-val")
            
            assert allowed
            assert "Ready" in reason


class TestGetAcceptanceGateSummary:
    
    def test_gate_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = get_acceptance_gate_summary(Path(tmpdir), "feat-summary")
            
            assert "feature_id" in summary
            assert "completion_allowed" in summary
            assert "gate_result" in summary


class TestIsValidTerminalStateForCompletion:
    
    def test_accepted_is_valid(self):
        assert is_valid_terminal_state_for_completion("accepted")
        assert is_valid_terminal_state_for_completion(AcceptanceTerminalState.ACCEPTED)
    
    def test_conditional_is_valid(self):
        assert is_valid_terminal_state_for_completion("conditional")
        assert is_valid_terminal_state_for_completion(AcceptanceTerminalState.CONDITIONAL)
    
    def test_rejected_is_not_valid(self):
        assert not is_valid_terminal_state_for_completion("rejected")
        assert not is_valid_terminal_state_for_completion(AcceptanceTerminalState.REJECTED)


class TestGetFeatureCompletionRequirements:
    
    def test_no_requirements_if_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-req",
                feature_id="feat-req",
                execution_result_id="exec-req",
                product_id="proj-req",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-req",
                acceptance_pack_id="ap-req",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
            )
            save_acceptance_result(project_path, result)
            
            requirements = get_feature_completion_requirements(project_path, "feat-req")
            
            assert len(requirements) == 0
    
    def test_requirements_if_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements = get_feature_completion_requirements(Path(tmpdir), "feat-blocked")
            
            assert len(requirements) > 0


class TestBypassScenarios:
    
    def test_bypass_scenarios_defined(self):
        assert "no_acceptance_criteria" in BYPASS_SCENARIOS
        assert "feature_spec_missing" in BYPASS_SCENARIOS
        assert "manual_override" in BYPASS_SCENARIOS