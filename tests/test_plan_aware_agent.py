"""Tests for Feature 017 - Archive-aware Plan Agent."""

import pytest
from pathlib import Path
import yaml

from runtime.plan_aware_agent import (
    gather_archive_context,
    get_applicable_lessons,
    get_applicable_patterns,
    extract_task_keywords,
    analyze_decision_constraints,
    get_decision_safe_alternatives,
    analyze_blocker_constraints,
    get_blocker_safe_alternatives,
    generate_planning_rationale,
    determine_safe_to_execute,
    generate_aware_execution_pack,
    estimate_task_scope,
    get_planning_context_summary,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create temp directory for tests."""
    return tmp_path


@pytest.fixture
def sample_runstate():
    """Sample RunState for testing."""
    return {
        "project_id": "test-product",
        "feature_id": "001-test-feature",
        "current_phase": "planning",
        "active_task": "",
        "task_queue": ["Implement archive query", "Add decision templates"],
        "completed_outputs": [],
        "open_questions": [],
        "blocked_items": [],
        "decisions_needed": [],
        "last_action": "Initialized",
        "next_recommended_action": "Plan next task",
        "updated_at": "2026-04-11T10:00:00Z",
    }


@pytest.fixture
def runstate_with_decisions():
    """RunState with pending decisions."""
    return {
        "project_id": "test-product",
        "feature_id": "002-decision-feature",
        "current_phase": "reviewing",
        "active_task": "Some task",
        "task_queue": ["Task A", "Task B"],
        "completed_outputs": [],
        "open_questions": [],
        "blocked_items": [],
        "decisions_needed": [
            {
                "decision": "Continue or change approach",
                "options": ["Continue", "Change"],
                "blocking_tomorrow": True,
                "urgency": "high",
            },
            {
                "decision": "Choose priority",
                "options": ["A", "B"],
                "blocking_tomorrow": False,
                "urgency": "low",
            },
        ],
        "last_action": "Execution completed",
        "next_recommended_action": "Make decision",
        "updated_at": "2026-04-11T12:00:00Z",
    }


@pytest.fixture
def runstate_with_blockers():
    """RunState with blockers."""
    return {
        "project_id": "test-product",
        "feature_id": "003-blocked-feature",
        "current_phase": "blocked",
        "active_task": "Blocked task",
        "task_queue": ["Blocked task", "Alternative task"],
        "completed_outputs": [],
        "open_questions": [],
        "blocked_items": [
            {
                "item": "external-api",
                "reason": "API key pending",
                "since": "2026-04-11T10:00:00Z",
            },
        ],
        "decisions_needed": [],
        "last_action": "Hit blocker",
        "next_recommended_action": "Resolve blocker",
        "updated_at": "2026-04-11T11:00:00Z",
    }


@pytest.fixture
def archive_setup(temp_dir):
    """Create sample archives for testing."""
    product_dir = temp_dir / "test-product"
    archive_dir = product_dir / "archive"
    
    feature1_dir = archive_dir / "001-core-objects"
    feature1_dir.mkdir(parents=True, exist_ok=True)
    
    archive_pack1 = {
        "feature_id": "001-core-objects",
        "product_id": "test-product",
        "title": "Core Objects",
        "final_status": "completed",
        "delivered_outputs": [],
        "acceptance_result": {"overall": "satisfied"},
        "unresolved_followups": [],
        "decisions_made": [],
        "lessons_learned": [
            {"lesson": "Small tasks work better", "context": "Day-sized tasks completed reliably"},
            {"lesson": "Keep CLI commands simple", "context": "Simple commands reduce friction"},
        ],
        "reusable_patterns": [
            {"pattern": "Schema + Template structure", "applicability": "All object definitions"},
            {"pattern": "Test fixtures in temp_dir", "applicability": "All test files"},
        ],
        "archived_at": "2026-04-10T18:00:00Z",
    }
    
    with open(feature1_dir / "archive-pack.yaml", "w") as f:
        yaml.dump(archive_pack1, f)
    
    feature2_dir = archive_dir / "002-cli-commands"
    feature2_dir.mkdir(parents=True, exist_ok=True)
    
    archive_pack2 = {
        "feature_id": "002-cli-commands",
        "product_id": "test-product",
        "title": "CLI Commands",
        "final_status": "completed",
        "delivered_outputs": [],
        "acceptance_result": {"overall": "satisfied"},
        "unresolved_followups": [],
        "decisions_made": [],
        "lessons_learned": [
            {"lesson": "CLI commands need tests", "context": "Each command should have tests"},
        ],
        "reusable_patterns": [
            {"pattern": "Runner.invoke pattern", "applicability": "All CLI tests"},
        ],
        "archived_at": "2026-04-09T18:00:00Z",
    }
    
    with open(feature2_dir / "archive-pack.yaml", "w") as f:
        yaml.dump(archive_pack2, f)
    
    yield temp_dir


class TestGatherArchiveContext:
    """Tests for gather_archive_context."""

    def test_gathers_from_archives(self, archive_setup):
        """Should gather context from existing archives."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        
        assert "recent_archives" in context
        assert "relevant_lessons" in context
        assert "relevant_patterns" in context
        assert "archive_summary" in context

    def test_includes_lessons_and_patterns(self, archive_setup):
        """Should include lessons and patterns from archives."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        
        lessons = context.get("relevant_lessons", [])
        patterns = context.get("relevant_patterns", [])
        
        assert len(lessons) >= 2
        assert len(patterns) >= 2

    def test_filters_by_product(self, archive_setup):
        """Should filter archives by product."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        
        summary = context.get("archive_summary", {})
        assert summary.get("total_archives", 0) >= 2

    def test_handles_empty_projects(self, temp_dir):
        """Should handle empty projects directory."""
        context = gather_archive_context(temp_dir)
        
        assert context.get("archive_summary", {}).get("total_archives", 0) == 0


class TestGetApplicableLessons:
    """Tests for get_applicable_lessons."""

    def test_matches_cli_keywords(self, archive_setup):
        """Should match lessons for CLI tasks."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        lessons = get_applicable_lessons(context, "Implement CLI commands")
        
        assert len(lessons) >= 1

    def test_matches_test_keywords(self, archive_setup):
        """Should match lessons for test tasks."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        lessons = get_applicable_lessons(context, "Add test fixtures")
        
        assert len(lessons) >= 1

    def test_returns_empty_for_no_matches(self, archive_setup):
        """Should return empty list for non-matching tasks."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        lessons = get_applicable_lessons(context, "Unrelated task xyz")
        
        assert len(lessons) == 0


class TestGetApplicablePatterns:
    """Tests for get_applicable_patterns."""

    def test_matches_schema_patterns(self, archive_setup):
        """Should match schema patterns."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        patterns = get_applicable_patterns(context, "Create schema files")
        
        assert len(patterns) >= 1

    def test_matches_test_patterns(self, archive_setup):
        """Should match test patterns."""
        context = gather_archive_context(archive_setup, product_id="test-product")
        patterns = get_applicable_patterns(context, "Write test fixtures")
        
        assert len(patterns) >= 1


class TestExtractTaskKeywords:
    """Tests for extract_task_keywords."""

    def test_extracts_cli_keyword(self):
        """Should extract 'cli' keyword."""
        keywords = extract_task_keywords("Implement CLI command")
        assert "cli" in keywords

    def test_extracts_test_keyword(self):
        """Should extract 'test' keyword."""
        keywords = extract_task_keywords("Add test cases")
        assert "test" in keywords

    def test_extracts_multiple_keywords(self):
        """Should extract multiple keywords."""
        keywords = extract_task_keywords("Create schema and template files")
        assert "schema" in keywords
        assert "template" in keywords


class TestAnalyzeDecisionConstraints:
    """Tests for analyze_decision_constraints."""

    def test_identifies_blocking_decisions(self, runstate_with_decisions):
        """Should identify blocking decisions."""
        constraints = analyze_decision_constraints(runstate_with_decisions)
        
        assert len(constraints.get("blocking_decisions", [])) == 1

    def test_counts_pending_decisions(self, runstate_with_decisions):
        """Should count all pending decisions."""
        constraints = analyze_decision_constraints(runstate_with_decisions)
        
        summary = constraints.get("decision_summary", {})
        assert summary.get("total_pending", 0) == 2

    def test_marks_safe_when_no_decisions(self, sample_runstate):
        """Should mark safe when no pending decisions."""
        constraints = analyze_decision_constraints(sample_runstate)
        
        assert constraints.get("safe_to_proceed", True) == True

    def test_marks_unsafe_when_blocking(self, runstate_with_decisions):
        """Should mark unsafe when blocking decisions exist."""
        constraints = analyze_decision_constraints(runstate_with_decisions)
        
        assert constraints.get("safe_to_proceed", True) == False


class TestGetDecisionSafeAlternatives:
    """Tests for get_decision_safe_alternatives."""

    def test_returns_all_when_safe(self, sample_runstate):
        """Should return all tasks when no blocking decisions."""
        constraints = analyze_decision_constraints(sample_runstate)
        alternatives = get_decision_safe_alternatives(
            constraints,
            sample_runstate.get("task_queue", []),
        )
        
        assert len(alternatives) == 2

    def test_filters_blocked_tasks(self, runstate_with_decisions):
        """Should filter tasks related to blocking decisions."""
        constraints = analyze_decision_constraints(runstate_with_decisions)
        alternatives = get_decision_safe_alternatives(
            constraints,
            ["Task related to continue approach", "Independent task"],
        )
        
        assert len(alternatives) >= 1


class TestAnalyzeBlockerConstraints:
    """Tests for analyze_blocker_constraints."""

    def test_identifies_active_blockers(self, runstate_with_blockers):
        """Should identify active blockers."""
        constraints = analyze_blocker_constraints(runstate_with_blockers)
        
        assert len(constraints.get("active_blockers", [])) == 1

    def test_provides_recovery_state(self, runstate_with_blockers):
        """Should provide recovery classification."""
        constraints = analyze_blocker_constraints(runstate_with_blockers)
        
        recovery = constraints.get("recovery_state", {})
        assert recovery.get("classification", "") == "blocked"

    def test_marks_safe_when_no_blockers(self, sample_runstate):
        """Should mark safe when no blockers."""
        constraints = analyze_blocker_constraints(sample_runstate)
        
        assert constraints.get("safe_to_proceed", True) == True


class TestGetBlockerSafeAlternatives:
    """Tests for get_blocker_safe_alternatives."""

    def test_returns_all_when_no_blockers(self, sample_runstate):
        """Should return all tasks when no blockers."""
        constraints = analyze_blocker_constraints(sample_runstate)
        alternatives = get_blocker_safe_alternatives(
            constraints,
            sample_runstate.get("task_queue", []),
        )
        
        assert len(alternatives) == 2

    def test_filters_blocked_tasks(self, runstate_with_blockers):
        """Should filter tasks related to blockers."""
        constraints = analyze_blocker_constraints(runstate_with_blockers)
        alternatives = get_blocker_safe_alternatives(
            constraints,
            ["Task using external-api", "Independent task"],
        )
        
        assert "Independent task" in alternatives


class TestGeneratePlanningRationale:
    """Tests for generate_planning_rationale."""

    def test_generates_primary_reason(self, sample_runstate, archive_setup):
        """Should generate primary reason."""
        archive_context = gather_archive_context(archive_setup, product_id="test-product")
        decision_constraints = analyze_decision_constraints(sample_runstate)
        blocker_constraints = analyze_blocker_constraints(sample_runstate)
        
        rationale = generate_planning_rationale(
            task="Implement CLI",
            archive_context=archive_context,
            decision_constraints=decision_constraints,
            blocker_constraints=blocker_constraints,
            applicable_lessons=[],
            applicable_patterns=[],
        )
        
        assert rationale.get("primary_reason", "") != ""

    def test_includes_warnings_for_blockers(self, runstate_with_blockers, archive_setup):
        """Should include warnings when blockers exist."""
        archive_context = gather_archive_context(archive_setup, product_id="test-product")
        decision_constraints = analyze_decision_constraints(runstate_with_blockers)
        blocker_constraints = analyze_blocker_constraints(runstate_with_blockers)
        
        rationale = generate_planning_rationale(
            task="Some task",
            archive_context=archive_context,
            decision_constraints=decision_constraints,
            blocker_constraints=blocker_constraints,
            applicable_lessons=[],
            applicable_patterns=[],
        )
        
        warnings = rationale.get("warnings", [])
        assert len(warnings) >= 1

    def test_high_confidence_when_safe(self, sample_runstate, archive_setup):
        """Should have high confidence when safe to proceed."""
        archive_context = gather_archive_context(archive_setup, product_id="test-product")
        decision_constraints = analyze_decision_constraints(sample_runstate)
        blocker_constraints = analyze_blocker_constraints(sample_runstate)
        
        rationale = generate_planning_rationale(
            task="Implement CLI",
            archive_context=archive_context,
            decision_constraints=decision_constraints,
            blocker_constraints=blocker_constraints,
            applicable_lessons=[],
            applicable_patterns=[],
        )
        
        assert rationale.get("confidence", "") == "high"


class TestDetermineSafeToExecute:
    """Tests for determine_safe_to_execute."""

    def test_safe_when_no_constraints(self, sample_runstate):
        """Should be safe when no constraints."""
        decision_constraints = analyze_decision_constraints(sample_runstate)
        blocker_constraints = analyze_blocker_constraints(sample_runstate)
        
        safe = determine_safe_to_execute(decision_constraints, blocker_constraints)
        
        assert safe == True

    def test_unsafe_when_blocking_decision(self, runstate_with_decisions):
        """Should be unsafe when blocking decision."""
        decision_constraints = analyze_decision_constraints(runstate_with_decisions)
        blocker_constraints = analyze_blocker_constraints(runstate_with_decisions)
        
        safe = determine_safe_to_execute(decision_constraints, blocker_constraints)
        
        assert safe == False

    def test_unsafe_when_blocker(self, runstate_with_blockers):
        """Should be unsafe when blocker."""
        decision_constraints = analyze_decision_constraints(runstate_with_blockers)
        blocker_constraints = analyze_blocker_constraints(runstate_with_blockers)
        
        safe = determine_safe_to_execute(decision_constraints, blocker_constraints)
        
        assert safe == False


class TestGenerateAwareExecutionPack:
    """Tests for generate_aware_execution_pack."""

    def test_generates_full_context(self, sample_runstate, archive_setup):
        """Should generate full planning context."""
        context = generate_aware_execution_pack(
            runstate=sample_runstate,
            projects_path=archive_setup,
        )
        
        assert "task" in context
        assert "safe_to_execute" in context
        assert "rationale" in context
        assert "archive_context" in context

    def test_includes_archive_references(self, sample_runstate, archive_setup):
        """Should include archive references."""
        context = generate_aware_execution_pack(
            runstate=sample_runstate,
            projects_path=archive_setup,
        )
        
        refs = context.get("archive_references", [])
        assert len(refs) >= 1

    def test_includes_estimated_scope(self, sample_runstate, archive_setup):
        """Should include estimated scope."""
        context = generate_aware_execution_pack(
            runstate=sample_runstate,
            projects_path=archive_setup,
        )
        
        assert context.get("estimated_scope", "") != ""

    def test_provides_alternatives_when_blocked(self, runstate_with_blockers, archive_setup):
        """Should provide alternatives when blocked."""
        context = generate_aware_execution_pack(
            runstate=runstate_with_blockers,
            projects_path=archive_setup,
        )
        
        alternatives = context.get("alternatives", [])
        assert len(alternatives) >= 1


class TestEstimateTaskScope:
    """Tests for estimate_task_scope."""

    def test_quick_for_simple_fix(self):
        """Should estimate quick for simple fix."""
        scope = estimate_task_scope("Fix typo in README", [])
        assert scope == "quick"

    def test_full_day_for_feature(self):
        """Should estimate full-day for feature."""
        scope = estimate_task_scope("Implement complete feature system", [])
        assert scope == "full-day"

    def test_half_day_default(self):
        """Should default to half-day."""
        scope = estimate_task_scope("Add module", [])
        assert scope == "half-day"


class TestGetPlanningContextSummary:
    """Tests for get_planning_context_summary."""

    def test_generates_human_readable_summary(self, sample_runstate, archive_setup):
        """Should generate human-readable summary."""
        context = generate_aware_execution_pack(
            runstate=sample_runstate,
            projects_path=archive_setup,
        )
        
        summary = get_planning_context_summary(context)
        
        assert "Task:" in summary
        assert "Safe to execute:" in summary


class TestIntegration:
    """Integration tests for Feature 017."""

    def test_full_planning_flow(self, sample_runstate, archive_setup):
        """Should complete full planning flow."""
        context = generate_aware_execution_pack(
            runstate=sample_runstate,
            projects_path=archive_setup,
            task="Implement CLI commands",
        )
        
        assert context.get("task") == "Implement CLI commands"
        assert context.get("safe_to_execute") == True
        assert len(context.get("archive_references", [])) >= 1

    def test_handles_concurrent_constraints(self, runstate_with_decisions, archive_setup):
        """Should handle concurrent decision and blocker constraints."""
        context = generate_aware_execution_pack(
            runstate=runstate_with_decisions,
            projects_path=archive_setup,
        )
        
        assert context.get("safe_to_execute") == False
        assert len(context.get("preconditions", [])) >= 1