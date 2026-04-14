"""Tests for Feature 037 - Continuous Canonical Loop Continuation Semantics.

Test scenarios from spec Section 13:

1. Successful iteration with meaningful next step -> expected: continue
2. Successful iteration with no meaningful next step -> expected: stop with valid reason
3. Successful iteration with escalation trigger -> expected: escalate
4. Successful iteration with external blocker -> expected: stop as blocked
5. Commit/push checkpoint -> expected: not terminal unless stop condition applies
6. Dogfood-enabled product workflow -> expected: enter dogfood stage automatically
7. Resume from prior continuity artifact -> expected: next stage derived without vague human restatement

AC-8: The system no longer emits behavior equivalent to:
"successful implementation complete, next step known, no blocker, but stopping because this would be a new session"
"""

from runtime.continuation_types import (
    ExecutionState,
    CheckpointType,
    CanonicalStage,
    TerminalStopType,
    ContinuationDecision,
    StopCondition,
    ContinuityArtifact,
    is_valid_stop_reason,
)
from runtime.stop_conditions import (
    check_escalation_required,
    check_no_meaningful_next_step,
    check_external_blocker,
    check_integrity_safety_pause,
    check_policy_based_stop,
    evaluate_all_stop_conditions,
    resolve_next_canonical_stage,
    has_meaningful_next_step,
)
from runtime.continuation_evaluator import (
    evaluate_continuation,
    should_auto_proceed_to_next_stage,
    get_continuation_summary,
    validate_stop_reason,
    apply_continuation_decision_to_runstate,
)


class TestContinuationTypes:
    """Test continuation types and enums."""

    def test_execution_state_values(self):
        assert ExecutionState.CHECKPOINT.value == "checkpoint"
        assert ExecutionState.CONTINUE.value == "continue"
        assert ExecutionState.STOP.value == "stop"
        assert ExecutionState.ESCALATE.value == "escalate"
        assert ExecutionState.BLOCKED.value == "blocked"

    def test_checkpoint_type_values(self):
        assert CheckpointType.ITERATION_COMPLETED.value == "iteration_completed"
        assert CheckpointType.COMMIT_COMPLETED.value == "commit_completed"
        assert CheckpointType.PUSH_COMPLETED.value == "push_completed"

    def test_terminal_stop_type_values(self):
        assert TerminalStopType.ESCALATION_REQUIRED.value == "escalation_required"
        assert TerminalStopType.NO_MEANINGFUL_NEXT_STEP.value == "no_meaningful_next_step"
        assert TerminalStopType.EXTERNAL_BLOCKER.value == "external_blocker"

    def test_canonical_stage_values(self):
        assert CanonicalStage.DOGFOOD.value == "dogfood"
        assert CanonicalStage.NEXT_ITERATION_PLANNING.value == "next_iteration_planning"
        assert CanonicalStage.EXECUTION_PACK_GENERATION.value == "execution_pack_generation"

    def test_continuation_decision_to_dict(self):
        decision = ContinuationDecision(
            state=ExecutionState.CONTINUE,
            checkpoint_type=CheckpointType.ITERATION_COMPLETED,
            next_stage=CanonicalStage.EXECUTION_PACK_GENERATION,
            continuation_allowed=True,
            reason="Checkpoint reached. No stop conditions apply.",
        )
        result = decision.to_dict()
        assert result["state"] == "continue"
        assert result["checkpoint_type"] == "iteration_completed"
        assert result["continuation_allowed"] == True

    def test_continuation_decision_is_checkpoint(self):
        decision = ContinuationDecision(state=ExecutionState.CHECKPOINT)
        assert decision.is_checkpoint() == True

        decision = ContinuationDecision(state=ExecutionState.STOP)
        assert decision.is_checkpoint() == False

    def test_continuation_decision_should_continue(self):
        decision = ContinuationDecision(state=ExecutionState.CONTINUE)
        assert decision.should_continue() == True

        decision = ContinuationDecision(state=ExecutionState.STOP)
        assert decision.should_continue() == False

    def test_continuity_artifact_to_dict_and_from_dict(self):
        artifact = ContinuityArtifact(
            latest_checkpoint="exec-001",
            latest_checkpoint_type=CheckpointType.ITERATION_COMPLETED,
            continuation_allowed=True,
            next_intended_stage=CanonicalStage.EXECUTION_PACK_GENERATION,
        )
        data = artifact.to_dict()
        restored = ContinuityArtifact.from_dict(data)
        assert restored.latest_checkpoint == artifact.latest_checkpoint
        assert restored.continuation_allowed == artifact.continuation_allowed

    def test_is_valid_stop_reason_rejects_phase_boundary(self):
        assert is_valid_stop_reason("iteration ended cleanly") == False
        assert is_valid_stop_reason("commit was pushed") == False
        assert is_valid_stop_reason("next step is in a new logical phase") == False
        assert is_valid_stop_reason("work could be described as a new session") == False
        assert is_valid_stop_reason("phase boundary reached") == False

    def test_is_valid_stop_reason_accepts_valid_reasons(self):
        assert is_valid_stop_reason("external dependency missing") == True
        assert is_valid_stop_reason("human decision required on architecture") == True
        assert is_valid_stop_reason("execution failed with critical error") == True


class TestStopConditions:
    """Test stop condition evaluation."""

    def test_check_escalation_required_with_high_urgency_decision(self):
        runstate = {"decisions_needed": [{"decision": "Architecture choice", "urgency": "high"}]}
        execution_result = {}
        result = check_escalation_required(runstate, execution_result)
        assert result is not None
        assert result.stop_type == TerminalStopType.ESCALATION_REQUIRED

    def test_check_escalation_required_with_medium_urgency_no_escalate(self):
        runstate = {"decisions_needed": [{"decision": "Minor tweak", "urgency": "low"}]}
        execution_result = {}
        result = check_escalation_required(runstate, execution_result)
        assert result is None

    def test_check_no_meaningful_next_step_with_empty_queue(self):
        runstate = {
            "task_queue": [],
            "completed_outputs": ["output1"],
            "next_recommended_action": "",
        }
        execution_result = {"recommended_next_step": ""}
        result = check_no_meaningful_next_step(runstate, execution_result)
        assert result is not None
        assert result.stop_type == TerminalStopType.NO_MEANINGFUL_NEXT_STEP

    def test_check_no_meaningful_next_step_with_queue_no_stop(self):
        runstate = {"task_queue": ["task1"], "completed_outputs": []}
        execution_result = {"recommended_next_step": ""}
        result = check_no_meaningful_next_step(runstate, execution_result)
        assert result is None

    def test_check_external_blocker_with_credential_issue(self):
        runstate = {
            "blocked_items": [{"item": "API key", "reason": "credential not available"}]
        }
        result = check_external_blocker(runstate)
        assert result is not None
        assert result.stop_type == TerminalStopType.EXTERNAL_BLOCKER

    def test_check_external_blocker_with_internal_issue_no_stop(self):
        runstate = {"blocked_items": [{"item": "logic bug", "reason": "implementation issue"}]}
        result = check_external_blocker(runstate)
        assert result is None

    def test_check_integrity_safety_pause_with_failed_execution(self):
        runstate = {}
        execution_result = {"status": "failed"}
        result = check_integrity_safety_pause(runstate, execution_result)
        assert result is not None
        assert result.stop_type == TerminalStopType.INTEGRITY_SAFETY_PAUSE

    def test_check_integrity_safety_pause_with_critical_issue(self):
        runstate = {}
        execution_result = {
            "status": "success",
            "issues_found": [
                {"description": "security vulnerability", "severity": "high", "resolution": "pending"}
            ],
        }
        result = check_integrity_safety_pause(runstate, execution_result)
        assert result is not None

    def test_check_policy_based_stop_with_conservative_mode(self):
        runstate = {"policy_mode": "conservative"}
        execution_result = {"status": "success"}
        result = check_policy_based_stop(runstate, execution_result)
        assert result is not None
        assert result.stop_type == TerminalStopType.POLICY_BASED_STOP

    def test_check_policy_based_stop_with_scope_change_flag(self):
        runstate = {"scope_change_flag": True}
        execution_result = {}
        result = check_policy_based_stop(runstate, execution_result)
        assert result is not None

    def test_evaluate_all_stop_conditions_priority_order(self):
        runstate = {
            "blocked_items": [{"item": "API", "reason": "credential missing"}],
            "decisions_needed": [{"decision": "Architecture", "urgency": "high"}],
            "policy_mode": "conservative",
        }
        execution_result = {"status": "failed"}
        result = evaluate_all_stop_conditions(runstate, execution_result)
        assert result is not None
        assert result.stop_type == TerminalStopType.INTEGRITY_SAFETY_PAUSE

    def test_resolve_next_canonical_stage_with_blocked_status(self):
        runstate = {}
        execution_result = {"status": "blocked"}
        result = resolve_next_canonical_stage(runstate, execution_result)
        assert result == CanonicalStage.REPAIR_LOOP

    def test_resolve_next_canonical_stage_with_unresolved_issues(self):
        runstate = {}
        execution_result = {
            "status": "success",
            "issues_found": [{"description": "bug", "resolution": "pending"}],
        }
        result = resolve_next_canonical_stage(runstate, execution_result)
        assert result == CanonicalStage.REPAIR_LOOP

    def test_resolve_next_canonical_stage_with_task_queue(self):
        runstate = {"task_queue": ["task1"]}
        execution_result = {"status": "success"}
        result = resolve_next_canonical_stage(runstate, execution_result)
        assert result == CanonicalStage.EXECUTION_PACK_GENERATION


class TestContinuationEvaluator:
    """Test continuation evaluation logic."""

    def test_scenario_1_successful_iteration_with_next_step_continues(self):
        runstate = {
            "task_queue": ["task1", "task2"],
            "blocked_items": [],
            "decisions_needed": [],
            "completed_outputs": ["output1"],
        }
        execution_result = {
            "status": "success",
            "recommended_next_step": "Continue with task2",
        }
        decision = evaluate_continuation(runstate, execution_result)
        assert decision.state == ExecutionState.CONTINUE
        assert decision.continuation_allowed == True

    def test_scenario_2_no_meaningful_next_step_stops(self):
        runstate = {
            "task_queue": [],
            "blocked_items": [],
            "decisions_needed": [],
            "completed_outputs": ["output1", "output2"],
            "next_recommended_action": "",
        }
        execution_result = {
            "status": "success",
            "recommended_next_step": "",
        }
        decision = evaluate_continuation(runstate, execution_result)
        assert decision.state == ExecutionState.STOP
        assert decision.continuation_allowed == False

    def test_scenario_3_escalation_trigger_escalates(self):
        runstate = {
            "task_queue": ["task1"],
            "blocked_items": [],
            "decisions_needed": [{"decision": "Major architecture change", "urgency": "high"}],
        }
        execution_result = {
            "status": "success",
            "recommended_next_step": "Continue",
        }
        decision = evaluate_continuation(runstate, execution_result)
        assert decision.state == ExecutionState.ESCALATE
        assert decision.escalation_required == True

    def test_scenario_4_external_blocker_blocked(self):
        runstate = {
            "task_queue": [],
            "blocked_items": [{"item": "API key", "reason": "credential not available"}],
            "decisions_needed": [],
        }
        execution_result = {"status": "success"}
        decision = evaluate_continuation(runstate, execution_result)
        assert decision.state == ExecutionState.BLOCKED
        assert decision.continuation_allowed == False

    def test_scenario_5_commit_push_not_terminal(self):
        runstate = {
            "task_queue": ["task1"],
            "blocked_items": [],
            "decisions_needed": [],
        }
        execution_result = {
            "status": "success",
            "recommended_next_step": "Continue with next task",
        }
        decision = evaluate_continuation(runstate, execution_result, CheckpointType.COMMIT_COMPLETED)
        assert decision.state == ExecutionState.CONTINUE
        assert decision.checkpoint_type == CheckpointType.COMMIT_COMPLETED

    def test_scenario_7_resume_from_continuity_artifact(self):
        runstate = {
            "continuity_context": {
                "latest_checkpoint": "exec-001",
                "continuation_allowed": True,
                "next_intended_stage": "execution_pack_generation",
                "candidate_next_actions": ["asyncdev plan-day create"],
            },
            "task_queue": ["task1"],
            "blocked_items": [],
            "decisions_needed": [],
        }
        execution_result = {
            "status": "success",
            "execution_id": "exec-001",
        }
        decision = evaluate_continuation(runstate, execution_result)
        assert decision.state == ExecutionState.CONTINUE
        assert len(decision.candidate_next_actions) > 0

    def test_should_auto_proceed_to_next_stage(self):
        runstate = {"task_queue": ["task1"], "blocked_items": [], "decisions_needed": []}
        execution_result = {"status": "success"}
        should_proceed, reason = should_auto_proceed_to_next_stage(runstate, execution_result)
        assert should_proceed == True

    def test_should_auto_proceed_blocked_false(self):
        runstate = {
            "task_queue": [],
            "blocked_items": [{"item": "API", "reason": "missing"}],
            "decisions_needed": [],
        }
        execution_result = {"status": "success"}
        should_proceed, reason = should_auto_proceed_to_next_stage(runstate, execution_result)
        assert should_proceed == False

    def test_validate_stop_reason_invalid_rejected(self):
        valid, reason = validate_stop_reason("this would be a new session")
        assert valid == False

    def test_validate_stop_reason_valid_accepted(self):
        valid, reason = validate_stop_reason("external blocker prevents progress")
        assert valid == True

    def test_get_continuation_summary_continue(self):
        decision = ContinuationDecision(
            state=ExecutionState.CONTINUE,
            checkpoint_type=CheckpointType.ITERATION_COMPLETED,
            next_stage=CanonicalStage.EXECUTION_PACK_GENERATION,
            reason="Checkpoint reached. No stop conditions apply.",
        )
        summary = get_continuation_summary(decision)
        assert "Continuing" in summary

    def test_get_continuation_summary_stop(self):
        decision = ContinuationDecision(
            state=ExecutionState.STOP,
            stop_condition=StopCondition(
                stop_type=TerminalStopType.NO_MEANINGFUL_NEXT_STEP,
                summary="No next step available",
                reason="All tasks completed",
                required_to_continue="Add new tasks",
                suggested_action="Review and plan",
            ),
        )
        summary = get_continuation_summary(decision)
        assert "Stopping" in summary

    def test_apply_continuation_decision_to_runstate_continue(self):
        runstate = {"current_phase": "reviewing"}
        decision = ContinuationDecision(state=ExecutionState.CONTINUE)
        execution_result = {"execution_id": "exec-001"}
        updated = apply_continuation_decision_to_runstate(runstate, decision, execution_result)
        assert updated["current_phase"] == "planning"
        assert updated["continuation_allowed"] == True
        assert "continuity_context" in updated

    def test_apply_continuation_decision_to_runstate_blocked(self):
        runstate = {"current_phase": "reviewing"}
        decision = ContinuationDecision(state=ExecutionState.BLOCKED)
        execution_result = {"execution_id": "exec-001"}
        updated = apply_continuation_decision_to_runstate(runstate, decision, execution_result)
        assert updated["current_phase"] == "blocked"
        assert updated["continuation_allowed"] == False

    def test_ac8_no_session_style_stop_reason(self):
        runstate = {
            "task_queue": ["task1"],
            "blocked_items": [],
            "decisions_needed": [],
        }
        execution_result = {
            "status": "success",
            "recommended_next_step": "Continue with task1",
        }
        decision = evaluate_continuation(runstate, execution_result)
        assert decision.state == ExecutionState.CONTINUE
        invalid_phrases = ["new session", "phase boundary", "session"]
        for phrase in invalid_phrases:
            assert phrase not in decision.reason.lower()


class TestIntegration:
    """Integration tests for continuation semantics."""

    def test_full_flow_success_to_continue(self):
        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
            "current_phase": "reviewing",
            "task_queue": ["task2", "task3"],
            "completed_outputs": ["task1_output"],
            "blocked_items": [],
            "decisions_needed": [],
        }
        execution_result = {
            "execution_id": "exec-001",
            "status": "success",
            "completed_items": ["task1_output"],
            "recommended_next_step": "Continue with task2",
        }
        
        decision = evaluate_continuation(runstate, execution_result)
        updated_runstate = apply_continuation_decision_to_runstate(runstate, decision, execution_result)
        
        assert decision.state == ExecutionState.CONTINUE
        assert updated_runstate["current_phase"] == "planning"
        assert updated_runstate["continuity_context"]["continuation_allowed"] == True

    def test_full_flow_blocked_to_blocked_phase(self):
        runstate = {
            "project_id": "test-project",
            "feature_id": "001-test",
            "current_phase": "reviewing",
            "task_queue": [],
            "blocked_items": [{"item": "API", "reason": "credential missing"}],
            "decisions_needed": [],
        }
        execution_result = {
            "execution_id": "exec-001",
            "status": "success",
        }
        
        decision = evaluate_continuation(runstate, execution_result)
        updated_runstate = apply_continuation_decision_to_runstate(runstate, decision, execution_result)
        
        assert decision.state == ExecutionState.BLOCKED
        assert updated_runstate["current_phase"] == "blocked"
        assert updated_runstate["continuation_allowed"] == False