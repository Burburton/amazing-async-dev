"""Tests for Recovery Classifier - Kernel stabilization.

Tests for:
- RecoveryClassification enum validation
- ResumeEligibility enum validation
- classify_recovery function
- check_resume_eligibility function
- get_recovery_guidance function
"""

import pytest

from runtime.recovery_classifier import (
    RecoveryClassification,
    ResumeEligibility,
    classify_recovery,
    check_resume_eligibility,
    get_recovery_guidance,
)


class TestRecoveryClassification:
    def test_classification_enum_values(self):
        assert RecoveryClassification.NORMAL_PAUSE.value == "normal_pause"
        assert RecoveryClassification.BLOCKED.value == "blocked"
        assert RecoveryClassification.FAILED.value == "failed"
        assert RecoveryClassification.AWAITING_DECISION.value == "awaiting_decision"
        assert RecoveryClassification.READY_TO_RESUME.value == "ready_to_resume"
        assert RecoveryClassification.UNSAFE_TO_RESUME.value == "unsafe_to_resume"
        assert RecoveryClassification.ALREADY_COMPLETED.value == "already_completed"
        assert RecoveryClassification.ALREADY_ARCHIVED.value == "already_archived"
    
    def test_classification_from_string(self):
        classification = RecoveryClassification("blocked")
        assert classification == RecoveryClassification.BLOCKED


class TestResumeEligibility:
    def test_eligibility_enum_values(self):
        assert ResumeEligibility.ELIGIBLE.value == "eligible"
        assert ResumeEligibility.NEEDS_DECISION.value == "needs_decision"
        assert ResumeEligibility.NEEDS_UNBLOCK.value == "needs_unblock"
        assert ResumeEligibility.NEEDS_FAILURE_HANDLING.value == "needs_failure_handling"
        assert ResumeEligibility.INCONSISTENT_STATE.value == "inconsistent_state"
        assert ResumeEligibility.NOT_RESUMABLE.value == "not_resumable"


class TestClassifyRecovery:
    def test_classify_archived_phase(self):
        runstate = {"current_phase": "archived"}
        assert classify_recovery(runstate) == RecoveryClassification.ALREADY_ARCHIVED
    
    def test_classify_completed_phase(self):
        runstate = {"current_phase": "completed"}
        assert classify_recovery(runstate) == RecoveryClassification.ALREADY_COMPLETED
    
    def test_classify_blocked_phase(self):
        runstate = {"current_phase": "blocked"}
        assert classify_recovery(runstate) == RecoveryClassification.BLOCKED
    
    def test_classify_blocked_items(self):
        runstate = {
            "current_phase": "executing",
            "blocked_items": ["network error"],
        }
        assert classify_recovery(runstate) == RecoveryClassification.BLOCKED
    
    def test_classify_awaiting_decision(self):
        runstate = {
            "current_phase": "planning",
            "decisions_needed": [{"question": "Use A or B?"}],
        }
        assert classify_recovery(runstate) == RecoveryClassification.AWAITING_DECISION
    
    def test_classify_failed_state(self):
        runstate = {
            "current_phase": "executing",
            "last_action": "Execution failed with error",
        }
        assert classify_recovery(runstate) == RecoveryClassification.FAILED
    
    def test_classify_reviewing_phase(self):
        runstate = {"current_phase": "reviewing"}
        assert classify_recovery(runstate) == RecoveryClassification.NORMAL_PAUSE
    
    def test_classify_planning_phase(self):
        runstate = {"current_phase": "planning"}
        assert classify_recovery(runstate) == RecoveryClassification.READY_TO_RESUME
    
    def test_classify_executing_with_active_task(self):
        runstate = {
            "current_phase": "executing",
            "active_task": "Running frontend verification",
        }
        assert classify_recovery(runstate) == RecoveryClassification.UNSAFE_TO_RESUME
    
    def test_classify_executing_without_active_task(self):
        runstate = {"current_phase": "executing"}
        assert classify_recovery(runstate) == RecoveryClassification.NORMAL_PAUSE


class TestCheckResumeEligibility:
    def test_eligible_from_ready_to_resume(self):
        runstate = {"current_phase": "planning"}
        assert check_resume_eligibility(runstate) == ResumeEligibility.ELIGIBLE
    
    def test_eligible_from_normal_pause(self):
        runstate = {"current_phase": "reviewing"}
        assert check_resume_eligibility(runstate) == ResumeEligibility.ELIGIBLE
    
    def test_needs_decision(self):
        runstate = {
            "current_phase": "planning",
            "decisions_needed": [{"question": "Choose option"}],
        }
        assert check_resume_eligibility(runstate) == ResumeEligibility.NEEDS_DECISION
    
    def test_needs_unblock(self):
        runstate = {"current_phase": "blocked"}
        assert check_resume_eligibility(runstate) == ResumeEligibility.NEEDS_UNBLOCK
    
    def test_needs_failure_handling(self):
        runstate = {
            "current_phase": "executing",
            "last_action": "failed to complete",
        }
        assert check_resume_eligibility(runstate) == ResumeEligibility.NEEDS_FAILURE_HANDLING
    
    def test_inconsistent_state(self):
        runstate = {
            "current_phase": "executing",
            "active_task": "Running task",
        }
        assert check_resume_eligibility(runstate) == ResumeEligibility.INCONSISTENT_STATE
    
    def test_not_resumable_completed(self):
        runstate = {"current_phase": "completed"}
        assert check_resume_eligibility(runstate) == ResumeEligibility.NOT_RESUMABLE
    
    def test_not_resumable_archived(self):
        runstate = {"current_phase": "archived"}
        assert check_resume_eligibility(runstate) == ResumeEligibility.NOT_RESUMABLE


class TestGetRecoveryGuidance:
    def test_guidance_ready_to_resume(self):
        runstate = {"current_phase": "planning"}
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "ready_to_resume"
        assert guidance["eligibility"] == "eligible"
        assert "plan-day" in guidance["recommended_action"]
    
    def test_guidance_normal_pause(self):
        runstate = {"current_phase": "reviewing"}
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "normal_pause"
        assert "resume-next-day" in guidance["recommended_action"]
    
    def test_guidance_blocked(self):
        runstate = {
            "current_phase": "blocked",
            "blocked_items": ["Network unavailable"],
        }
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "blocked"
        assert guidance["blocked_count"] == 1
        assert len(guidance["warnings"]) > 0
    
    def test_guidance_awaiting_decision(self):
        runstate = {
            "current_phase": "planning",
            "decisions_needed": [{"question": "A or B?"}],
        }
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "awaiting_decision"
        assert guidance["decisions_count"] == 1
        assert "decision" in guidance["recommended_action"].lower()
    
    def test_guidance_failed(self):
        runstate = {
            "current_phase": "executing",
            "last_action": "Execution failed",
        }
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "failed"
        assert "handle-failed" in guidance["recommended_action"]
    
    def test_guidance_completed(self):
        runstate = {"current_phase": "completed"}
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "already_completed"
        assert "archive" in guidance["recommended_action"].lower()
    
    def test_guidance_archived(self):
        runstate = {"current_phase": "archived"}
        guidance = get_recovery_guidance(runstate)
        
        assert guidance["classification"] == "already_archived"
        assert guidance["recommended_action"] == "No action needed"


class TestRecoveryStateIntegration:
    def test_blocked_to_unblocked_transition(self):
        runstate = {
            "current_phase": "blocked",
            "blocked_items": ["Network error"],
        }
        assert classify_recovery(runstate) == RecoveryClassification.BLOCKED
        
        runstate["current_phase"] = "planning"
        runstate["blocked_items"] = []
        assert classify_recovery(runstate) == RecoveryClassification.READY_TO_RESUME
    
    def test_decision_to_resolved_transition(self):
        runstate = {
            "current_phase": "planning",
            "decisions_needed": [{"question": "A or B?"}],
        }
        assert classify_recovery(runstate) == RecoveryClassification.AWAITING_DECISION
        
        runstate["decisions_needed"] = []
        assert classify_recovery(runstate) == RecoveryClassification.READY_TO_RESUME
    
    def test_failed_to_retry_transition(self):
        runstate = {
            "current_phase": "executing",
            "last_action": "failed",
        }
        assert classify_recovery(runstate) == RecoveryClassification.FAILED
        
        runstate["last_action"] = "Retrying after failure"
        assert classify_recovery(runstate) == RecoveryClassification.NORMAL_PAUSE