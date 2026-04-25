"""Tests for Feature 074 - Acceptance Console Operator Visibility."""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.acceptance_console import (
    list_acceptance_results,
    show_acceptance_result,
    show_acceptance_history,
    show_recovery_status,
    get_acceptance_summary,
    format_acceptance_console_output,
)
from runtime.acceptance_runner import (
    AcceptanceResult,
    AcceptanceTerminalState,
    AcceptanceFinding,
    RemediationGuidance,
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
from runtime.reacceptance_loop import (
    AcceptanceAttempt,
    AcceptanceAttemptHistory,
    ReAcceptanceState,
    save_attempt_history,
)


class TestListAcceptanceResults:
    
    @pytest.fixture
    def project_with_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack1 = AcceptancePack(
                acceptance_pack_id="ap-list-1",
                feature_id="feat-list",
                execution_result_id="exec-1",
                product_id="proj-list",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack1)
            
            result1 = AcceptanceResult(
                acceptance_result_id="ar-list-1",
                acceptance_pack_id="ap-list-1",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
                attempt_number=1,
                accepted_criteria=["AC-001"],
            )
            save_acceptance_result(project_path, result1)
            
            pack2 = AcceptancePack(
                acceptance_pack_id="ap-list-2",
                feature_id="feat-list",
                execution_result_id="exec-2",
                product_id="proj-list",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack2)
            
            result2 = AcceptanceResult(
                acceptance_result_id="ar-list-2",
                acceptance_pack_id="ap-list-2",
                terminal_state=AcceptanceTerminalState.REJECTED,
                attempt_number=1,
                failed_criteria=["AC-001"],
            )
            save_acceptance_result(project_path, result2)
            
            yield project_path

    def test_list_all_results(self, project_with_results):
        results = list_acceptance_results(project_with_results)
        
        assert len(results) == 2
    
    def test_list_with_status_filter(self, project_with_results):
        accepted = list_acceptance_results(project_with_results, status_filter="accepted")
        
        assert len(accepted) == 1
        assert accepted[0]["terminal_state"] == "accepted"
    
    def test_list_empty_if_no_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = list_acceptance_results(Path(tmpdir))
            assert len(results) == 0


class TestShowAcceptanceResult:
    
    @pytest.fixture
    def project_with_detailed_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-show",
                feature_id="feat-show",
                execution_result_id="exec-show",
                product_id="proj-show",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-show",
                acceptance_pack_id="ap-show",
                terminal_state=AcceptanceTerminalState.REJECTED,
                attempt_number=1,
                findings=[
                    AcceptanceFinding(
                        criterion_id="AC-001",
                        criterion_text="Feature works correctly",
                        result="failed",
                        evidence_found=False,
                        notes="No evidence found",
                    )
                ],
                failed_criteria=["AC-001"],
                remediation_guidance=[
                    RemediationGuidance(
                        criterion_id="AC-001",
                        issue_type="evidence_missing",
                        suggested_fix="Provide evidence",
                        priority="high",
                    )
                ],
            )
            save_acceptance_result(project_path, result)
            
            yield project_path

    def test_show_result(self, project_with_detailed_result):
        details = show_acceptance_result(project_with_detailed_result, "ar-show")
        
        assert details is not None
        assert details["terminal_state"] == "rejected"
        assert len(details["findings"]) == 1
        assert len(details["remediation_guidance"]) == 1
    
    def test_show_result_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            details = show_acceptance_result(Path(tmpdir), "ar-missing")
            assert details is None


class TestShowAcceptanceHistory:
    
    def test_show_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            history = AcceptanceAttemptHistory(
                feature_id="feat-history",
                execution_result_id="exec-hist",
                attempts=[
                    AcceptanceAttempt(
                        attempt_number=1,
                        acceptance_result_id="ar-hist-1",
                        acceptance_pack_id="ap-hist-1",
                        terminal_state="rejected",
                        triggered_at="2026-04-25T12:00:00",
                    ),
                    AcceptanceAttempt(
                        attempt_number=2,
                        acceptance_result_id="ar-hist-2",
                        acceptance_pack_id="ap-hist-2",
                        terminal_state="accepted",
                        triggered_at="2026-04-25T13:00:00",
                    ),
                ],
                total_attempts=2,
            )
            save_attempt_history(project_path, history)
            
            details = show_acceptance_history(project_path, "feat-history")
            
            assert details["total_executions"] == 1
            assert details["total_attempts"] == 2
    
    def test_show_history_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            details = show_acceptance_history(Path(tmpdir), "feat-none")
            
            assert details["total_executions"] == 0


class TestShowRecoveryStatus:
    
    def test_show_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptanceRecoveryPack(
                acceptance_recovery_pack_id="arp-recovery",
                acceptance_result_id="ar-recovery",
                feature_id="feat-recovery",
                recovery_items=[
                    RecoveryItem(
                        recovery_item_id="ri-001",
                        category=RecoveryCategory.EVIDENCE_MISSING,
                        priority=RecoveryPriority.HIGH,
                        source_acceptance_result_id="ar-recovery",
                        source_criterion_id="AC-001",
                        issue_description="Missing evidence",
                        suggested_action="Provide evidence",
                        status="pending",
                    )
                ],
                total_items=1,
            )
            save_acceptance_recovery_pack(project_path, pack)
            
            details = show_recovery_status(project_path, "feat-recovery")
            
            assert details["pending_items"] == 1
            assert len(details["items"]) == 1
    
    def test_show_recovery_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            details = show_recovery_status(Path(tmpdir), "feat-none")
            
            assert details["pending_items"] == 0


class TestGetAcceptanceSummary:
    
    @pytest.fixture
    def project_for_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-summary",
                feature_id="feat-summary",
                execution_result_id="exec-summary",
                product_id="proj-summary",
                acceptance_criteria=[],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-summary",
                acceptance_pack_id="ap-summary",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
                attempt_number=1,
                accepted_criteria=["AC-001"],
            )
            save_acceptance_result(project_path, result)
            
            yield project_path

    def test_get_summary_accepted(self, project_for_summary):
        summary = get_acceptance_summary(project_for_summary, "feat-summary")
        
        assert summary["status"] == "accepted"
        assert summary["next_action"] == "Feature ready for completion"
    
    def test_get_summary_no_acceptance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = get_acceptance_summary(Path(tmpdir), "feat-none")
            
            assert summary["status"] == "no_acceptance"


class TestFormatConsoleOutput:
    
    def test_format_basic(self):
        summary = {
            "feature_id": "feat-format",
            "status": "accepted",
            "latest_result_id": "ar-001",
            "latest_terminal_state": "accepted",
            "attempt_number": 1,
            "total_attempts": 1,
            "accepted_criteria": 2,
            "failed_criteria": 0,
            "pending_recovery_items": 0,
            "next_action": "Feature ready for completion",
        }
        
        output = format_acceptance_console_output(summary)
        
        assert "ACCEPTANCE CONSOLE" in output
        assert "feat-format" in output
        assert "accepted" in output
        assert "Feature ready for completion" in output
    
    def test_format_with_details(self):
        summary = {
            "feature_id": "feat-details",
            "status": "rejected",
            "latest_result_id": "ar-002",
            "latest_terminal_state": "rejected",
            "attempt_number": 2,
            "total_attempts": 2,
            "accepted_criteria": 0,
            "failed_criteria": 1,
            "pending_recovery_items": 1,
            "next_action": "Address recovery items",
            "findings": [
                {"criterion_id": "AC-001", "result": "failed", "criterion_text": "Works"}
            ],
        }
        
        output = format_acceptance_console_output(summary, include_details=True)
        
        assert "Details:" in output
        assert "[failed] AC-001" in output