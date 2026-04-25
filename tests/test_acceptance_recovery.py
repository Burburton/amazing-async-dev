"""Tests for Feature 072 - Acceptance Findings to Recovery."""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.acceptance_recovery import (
    RecoveryCategory,
    RecoveryPriority,
    RecoveryItem,
    AcceptanceRecoveryPack,
    categorize_failure,
    determine_priority,
    generate_recovery_item_id,
    convert_remediation_to_recovery_item,
    create_acceptance_recovery_pack,
    determine_next_action,
    attach_recovery_to_runstate,
    save_acceptance_recovery_pack,
    load_acceptance_recovery_pack,
    process_failed_acceptance,
    get_recovery_items_for_feature,
)
from runtime.acceptance_runner import (
    AcceptanceResult,
    AcceptanceTerminalState,
    RemediationGuidance,
    save_acceptance_result,
)
from runtime.acceptance_pack_builder import (
    AcceptancePack,
    VerificationSummary,
    save_acceptance_pack,
)


class TestRecoveryCategory:
    
    def test_all_categories_defined(self):
        assert RecoveryCategory.EVIDENCE_MISSING.value == "evidence_missing"
        assert RecoveryCategory.CRITERION_FAILED.value == "criterion_failed"
        assert RecoveryCategory.CONDITIONAL_ACCEPTANCE.value == "conditional_acceptance"
        assert RecoveryCategory.VALIDATION_ERROR.value == "validation_error"
        assert RecoveryCategory.IMPLEMENTATION_GAP.value == "implementation_gap"
        assert RecoveryCategory.ESCALATION_REQUIRED.value == "escalation_required"


class TestRecoveryPriority:
    
    def test_all_priorities_defined(self):
        assert RecoveryPriority.CRITICAL.value == "critical"
        assert RecoveryPriority.HIGH.value == "high"
        assert RecoveryPriority.MEDIUM.value == "medium"
        assert RecoveryPriority.LOW.value == "low"


class TestRecoveryItem:
    
    def test_recovery_item_creation(self):
        item = RecoveryItem(
            recovery_item_id="ri-001",
            category=RecoveryCategory.EVIDENCE_MISSING,
            priority=RecoveryPriority.HIGH,
            source_acceptance_result_id="ar-001",
            source_criterion_id="AC-001",
            issue_description="Missing evidence",
            suggested_action="Provide evidence",
        )
        assert item.recovery_item_id == "ri-001"
        assert item.category == RecoveryCategory.EVIDENCE_MISSING
    
    def test_recovery_item_to_dict(self):
        item = RecoveryItem(
            recovery_item_id="ri-001",
            category=RecoveryCategory.EVIDENCE_MISSING,
            priority=RecoveryPriority.HIGH,
            source_acceptance_result_id="ar-001",
            source_criterion_id="AC-001",
            issue_description="Missing evidence",
            suggested_action="Provide evidence",
        )
        d = item.to_dict()
        assert d["category"] == "evidence_missing"


class TestCategorizeFailure:
    
    def test_evidence_missing_category(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Provide evidence",
        )
        category = categorize_failure(remediation)
        assert category == RecoveryCategory.EVIDENCE_MISSING
    
    def test_criterion_failed_category(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="criterion_failed",
            suggested_fix="Fix implementation",
        )
        category = categorize_failure(remediation)
        assert category == RecoveryCategory.CRITERION_FAILED
    
    def test_unknown_issue_type_defaults_to_criterion_failed(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="unknown_type",
            suggested_fix="Fix",
        )
        category = categorize_failure(remediation)
        assert category == RecoveryCategory.CRITERION_FAILED


class TestDeterminePriority:
    
    def test_critical_priority(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Fix",
            priority="critical",
        )
        priority = determine_priority(remediation)
        assert priority == RecoveryPriority.CRITICAL
    
    def test_high_priority(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Fix",
            priority="high",
        )
        priority = determine_priority(remediation)
        assert priority == RecoveryPriority.HIGH
    
    def test_unknown_priority_defaults_to_medium(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Fix",
            priority="unknown",
        )
        priority = determine_priority(remediation)
        assert priority == RecoveryPriority.MEDIUM


class TestConvertRemediationToRecoveryItem:
    
    def test_conversion(self):
        remediation = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Provide evidence",
            priority="high",
        )
        
        item = convert_remediation_to_recovery_item(remediation, "ar-001", 1)
        
        assert item.source_criterion_id == "AC-001"
        assert item.category == RecoveryCategory.EVIDENCE_MISSING
        assert item.priority == RecoveryPriority.HIGH


class TestDetermineNextAction:
    
    def test_escalated_action(self):
        action = determine_next_action(
            AcceptanceTerminalState.ESCALATED,
            [],
        )
        assert "escalation" in action.lower()
    
    def test_manual_review_action(self):
        action = determine_next_action(
            AcceptanceTerminalState.MANUAL_REVIEW,
            [],
        )
        assert "manual review" in action.lower()
    
    def test_critical_items_action(self):
        items = [
            RecoveryItem(
                recovery_item_id="ri-001",
                category=RecoveryCategory.EVIDENCE_MISSING,
                priority=RecoveryPriority.CRITICAL,
                source_acceptance_result_id="ar-001",
                source_criterion_id="AC-001",
                issue_description="Critical issue",
                suggested_action="Fix",
            )
        ]
        
        action = determine_next_action(AcceptanceTerminalState.REJECTED, items)
        assert "critical" in action.lower()


class TestAcceptanceRecoveryPack:
    
    def test_recovery_pack_creation(self):
        pack = AcceptanceRecoveryPack(
            acceptance_recovery_pack_id="arp-001",
            acceptance_result_id="ar-001",
            feature_id="feat-001",
            recovery_items=[],
            total_items=0,
        )
        assert pack.acceptance_recovery_pack_id == "arp-001"
    
    def test_recovery_pack_to_dict(self):
        pack = AcceptanceRecoveryPack(
            acceptance_recovery_pack_id="arp-001",
            acceptance_result_id="ar-001",
            feature_id="feat-001",
            recovery_items=[],
            total_items=0,
        )
        d = pack.to_dict()
        assert d["acceptance_recovery_pack_id"] == "arp-001"


class TestSaveLoadRecoveryPack:
    
    def test_save_recovery_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptanceRecoveryPack(
                acceptance_recovery_pack_id="arp-001",
                acceptance_result_id="ar-001",
                feature_id="feat-001",
                recovery_items=[],
                total_items=0,
            )
            
            pack_path = save_acceptance_recovery_pack(project_path, pack)
            
            assert pack_path.exists()
            assert pack_path.name == "arp-001.md"
    
    def test_load_recovery_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptanceRecoveryPack(
                acceptance_recovery_pack_id="arp-001",
                acceptance_result_id="ar-001",
                feature_id="feat-001",
                recovery_items=[
                    RecoveryItem(
                        recovery_item_id="ri-001",
                        category=RecoveryCategory.EVIDENCE_MISSING,
                        priority=RecoveryPriority.HIGH,
                        source_acceptance_result_id="ar-001",
                        source_criterion_id="AC-001",
                        issue_description="Issue",
                        suggested_action="Fix",
                    )
                ],
                total_items=1,
            )
            
            save_acceptance_recovery_pack(project_path, pack)
            
            loaded = load_acceptance_recovery_pack(project_path, "arp-001")
            
            assert loaded is not None
            assert loaded.acceptance_recovery_pack_id == "arp-001"
            assert len(loaded.recovery_items) == 1


class TestCreateAcceptanceRecoveryPack:
    
    @pytest.fixture
    def project_with_failed_acceptance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-fail",
                feature_id="feat-fail",
                execution_result_id="exec-fail",
                product_id="proj-fail",
                acceptance_criteria=[{"criterion_id": "AC-001", "text": "Works"}],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-fail",
                acceptance_pack_id="ap-fail",
                terminal_state=AcceptanceTerminalState.REJECTED,
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

    def test_create_recovery_pack_from_failed(self, project_with_failed_acceptance):
        pack = create_acceptance_recovery_pack(project_with_failed_acceptance, "ar-fail")
        
        assert pack is not None
        assert pack.feature_id == "feat-fail"
        assert len(pack.recovery_items) > 0
    
    def test_create_recovery_pack_skips_accepted(self):
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
            
            recovery_pack = create_acceptance_recovery_pack(project_path, "ar-accepted")
            
            assert recovery_pack is None


class TestAttachRecoveryToRunstate:
    
    def test_attach_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({"blocked_items": []})
            
            pack = AcceptanceRecoveryPack(
                acceptance_recovery_pack_id="arp-001",
                acceptance_result_id="ar-001",
                feature_id="feat-001",
                recovery_items=[
                    RecoveryItem(
                        recovery_item_id="ri-001",
                        category=RecoveryCategory.EVIDENCE_MISSING,
                        priority=RecoveryPriority.HIGH,
                        source_acceptance_result_id="ar-001",
                        source_criterion_id="AC-001",
                        issue_description="Issue",
                        suggested_action="Fix",
                    )
                ],
                total_items=1,
            )
            
            attach_recovery_to_runstate(project_path, pack)
            
            runstate = store.load_runstate()
            
            assert runstate is not None
            assert "blocked_items" in runstate
            assert len(runstate["blocked_items"]) == 1
            assert runstate.get("acceptance_recovery_pending") is True


class TestProcessFailedAcceptance:
    
    @pytest.fixture
    def full_failed_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-process",
                feature_id="feat-process",
                execution_result_id="exec-process",
                product_id="proj-process",
                acceptance_criteria=[{"criterion_id": "AC-001", "text": "Works"}],
                verification_summary=VerificationSummary(orchestration_terminal_state="success"),
            )
            save_acceptance_pack(project_path, pack)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-process",
                acceptance_pack_id="ap-process",
                terminal_state=AcceptanceTerminalState.REJECTED,
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
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "blocked_items": [],
                "feature_id": "feat-process",
            })
            
            yield project_path

    def test_process_failed_acceptance_full_flow(self, full_failed_project):
        pack = process_failed_acceptance(full_failed_project, "ar-process")
        
        assert pack is not None
        assert len(pack.recovery_items) > 0
        
        recovery_dir = full_failed_project / "acceptance-recovery"
        assert recovery_dir.exists()
        
        from runtime.state_store import StateStore
        store = StateStore(full_failed_project)
        runstate = store.load_runstate()
        
        assert runstate.get("acceptance_recovery_pending") is True


class TestGetRecoveryItemsForFeature:
    
    def test_get_pending_items(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptanceRecoveryPack(
                acceptance_recovery_pack_id="arp-001",
                acceptance_result_id="ar-001",
                feature_id="feat-get",
                recovery_items=[
                    RecoveryItem(
                        recovery_item_id="ri-001",
                        category=RecoveryCategory.EVIDENCE_MISSING,
                        priority=RecoveryPriority.HIGH,
                        source_acceptance_result_id="ar-001",
                        source_criterion_id="AC-001",
                        issue_description="Issue",
                        suggested_action="Fix",
                        status="pending",
                    )
                ],
                total_items=1,
            )
            save_acceptance_recovery_pack(project_path, pack)
            
            items = get_recovery_items_for_feature(project_path, "feat-get")
            
            assert len(items) == 1
    
    def test_excludes_completed_items(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptanceRecoveryPack(
                acceptance_recovery_pack_id="arp-002",
                acceptance_result_id="ar-002",
                feature_id="feat-exclude",
                recovery_items=[
                    RecoveryItem(
                        recovery_item_id="ri-002",
                        category=RecoveryCategory.EVIDENCE_MISSING,
                        priority=RecoveryPriority.HIGH,
                        source_acceptance_result_id="ar-002",
                        source_criterion_id="AC-001",
                        issue_description="Issue",
                        suggested_action="Fix",
                        status="completed",
                    )
                ],
                total_items=1,
            )
            save_acceptance_recovery_pack(project_path, pack)
            
            items = get_recovery_items_for_feature(project_path, "feat-exclude")
            
            assert len(items) == 0