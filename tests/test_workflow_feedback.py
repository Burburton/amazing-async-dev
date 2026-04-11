"""Tests for workflow feedback - Feature 019a + 019b (Triage).

Feature 019a: Workflow Feedback Capture
Feature 019b: Workflow Feedback Triage
"""

import pytest
from pathlib import Path
import yaml
from datetime import datetime
from typer.testing import CliRunner

from runtime.workflow_feedback_store import (
    WorkflowFeedbackStore,
    create_workflow_feedback_for_review,
)
from cli.commands.feedback import app

runner = CliRunner()


@pytest.fixture
def setup_feedback_store(temp_dir):
    """Create feedback store with both system and product paths."""
    product_path = temp_dir / "test-product"
    product_path.mkdir(parents=True)
    
    runtime_path = temp_dir / ".runtime"
    runtime_path.mkdir(parents=True)
    
    store = WorkflowFeedbackStore(project_path=product_path, runtime_path=runtime_path)
    yield store
    store.close()


@pytest.fixture
def setup_feedback_files(temp_dir):
    """Create sample feedback files for testing."""
    product_path = temp_dir / "test-product"
    product_path.mkdir(parents=True)
    
    runtime_path = temp_dir / ".runtime"
    runtime_path.mkdir(parents=True)
    
    store = WorkflowFeedbackStore(project_path=product_path, runtime_path=runtime_path, use_sqlite=True)
    
    async_dev_fb = store.record_feedback(
        problem_domain="async_dev",
        issue_type="cli_behavior",
        detected_by="operator",
        detected_in="status command",
        description="asyncdev status showed wrong phase",
        self_corrected=False,
        requires_followup=True,
        confidence="high",
        escalation_recommendation="candidate_issue",
        detected_at="2026-04-10T10:00:00",
    )
    
    product_fb = store.record_feedback(
        problem_domain="product",
        issue_type="execution_pack",
        detected_by="operator",
        detected_in="plan-day create",
        description="ExecutionPack referenced wrong feature",
        self_corrected=True,
        requires_followup=True,
        product_id="test-product",
        feature_id="001-core",
        detected_at="2026-04-10T11:00:00",
    )
    
    uncertain_fb = store.record_feedback(
        problem_domain="uncertain",
        issue_type="repo_integration",
        detected_by="operator",
        detected_in="git operations",
        description="Git integration issue, unclear source",
        self_corrected=False,
        requires_followup=True,
        product_id="test-product",
        detected_at="2026-04-10T12:00:00",
    )
    
    store.close()
    
    yield {
        "temp_dir": temp_dir,
        "async_dev_id": async_dev_fb["feedback_id"],
        "product_id": product_fb["feedback_id"],
        "uncertain_id": uncertain_fb["feedback_id"],
    }


class TestWorkflowFeedbackStore:
    """Tests for runtime/workflow_feedback_store.py."""

    def test_generate_feedback_id(self, setup_feedback_store):
        """generate_feedback_id should create valid ID pattern."""
        store = setup_feedback_store
        
        feedback_id = store.generate_feedback_id()
        
        assert feedback_id.startswith("wf-")
        assert len(feedback_id) == 15
        
        store.close()
        
    def test_generate_feedback_id_unique(self, setup_feedback_store):
        """generate_feedback_id should create unique IDs when recorded."""
        store = setup_feedback_store
        
        fb1 = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test 1",
            self_corrected=False,
            requires_followup=True,
        )
        
        fb2 = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test 2",
            self_corrected=False,
            requires_followup=True,
        )
        
        assert fb1["feedback_id"] != fb2["feedback_id"]
        store.close()

    def test_record_feedback_product_domain(self, setup_feedback_store):
        """record_feedback should create product-domain feedback."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="product",
            issue_type="execution_pack",
            detected_by="operator",
            detected_in="plan-day",
            description="Test feedback",
            self_corrected=False,
            requires_followup=True,
            product_id="test-product",
        )
        
        assert feedback["feedback_id"].startswith("wf-")
        assert feedback["problem_domain"] == "product"
        assert feedback["issue_type"] == "execution_pack"
        assert feedback["product_id"] == "test-product"

    def test_record_feedback_async_dev_domain(self, setup_feedback_store):
        """record_feedback should create async_dev-domain feedback."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="status command",
            description="CLI bug",
            self_corrected=True,
            requires_followup=False,
        )
        
        assert feedback["problem_domain"] == "async_dev"
        assert feedback["issue_type"] == "cli_behavior"

    def test_record_feedback_uncertain_domain(self, setup_feedback_store):
        """record_feedback should create uncertain-domain feedback."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="uncertain",
            issue_type="repo_integration",
            detected_by="operator",
            detected_in="git ops",
            description="Unclear issue source",
            self_corrected=False,
            requires_followup=True,
            product_id="test-product",
        )
        
        assert feedback["problem_domain"] == "uncertain"
        assert feedback["issue_type"] == "repo_integration"

    def test_record_feedback_requires_product_id_for_product_domain(self, setup_feedback_store):
        """record_feedback should require product_id when problem_domain=product."""
        store = setup_feedback_store
        
        with pytest.raises(ValueError, match="product_id is required"):
            store.record_feedback(
                problem_domain="product",
                issue_type="execution_pack",
                detected_by="operator",
                detected_in="plan-day",
                description="Test",
                self_corrected=False,
                requires_followup=True,
            )

    def test_record_feedback_requires_product_id_for_uncertain_domain(self, setup_feedback_store):
        """record_feedback should require product_id when problem_domain=uncertain."""
        store = setup_feedback_store
        
        with pytest.raises(ValueError, match="product_id is required"):
            store.record_feedback(
                problem_domain="uncertain",
                issue_type="repo_integration",
                detected_by="operator",
                detected_in="git ops",
                description="Test",
                self_corrected=False,
                requires_followup=True,
            )

    def test_record_feedback_validates_issue_type(self, setup_feedback_store):
        """record_feedback should validate issue_type."""
        store = setup_feedback_store
        
        with pytest.raises(ValueError, match="Invalid issue_type"):
            store.record_feedback(
                problem_domain="async_dev",
                issue_type="invalid_type",
                detected_by="operator",
                detected_in="test",
                description="Test",
                self_corrected=False,
                requires_followup=True,
            )

    def test_record_feedback_validates_problem_domain(self, setup_feedback_store):
        """record_feedback should validate problem_domain."""
        store = setup_feedback_store
        
        with pytest.raises(ValueError, match="Invalid problem_domain"):
            store.record_feedback(
                problem_domain="invalid_domain",
                issue_type="cli_behavior",
                detected_by="operator",
                detected_in="test",
                description="Test",
                self_corrected=False,
                requires_followup=True,
            )

    def test_record_feedback_with_triage_params(self, setup_feedback_store):
        """record_feedback should accept triage params during record."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="status",
            description="CLI bug with triage",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
            triage_note="Confirmed bug in CLI",
        )
        
        assert feedback["confidence"] == "high"
        assert feedback["escalation_recommendation"] == "candidate_issue"
        assert feedback["triage_note"] == "Confirmed bug in CLI"
        assert feedback["triaged_at"] is not None

    def test_record_feedback_auto_infers_domain(self, setup_feedback_store):
        """record_feedback should auto-infer problem_domain when not specified."""
        store = setup_feedback_store
        
        # cli_behavior should auto-infer to async_dev
        feedback = store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test auto-inference",
            self_corrected=False,
            requires_followup=True,
        )
        
        assert feedback["problem_domain"] == "async_dev"

    def test_load_feedback(self, setup_feedback_files):
        """load_feedback should load existing feedback."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedback = store.load_feedback(setup_feedback_files["async_dev_id"])
        
        assert feedback is not None
        assert feedback["problem_domain"] == "async_dev"
        assert feedback["issue_type"] == "cli_behavior"
        store.close()

    def test_load_feedback_not_found(self, setup_feedback_store):
        """load_feedback should return None for missing feedback."""
        store = setup_feedback_store
        
        feedback = store.load_feedback("wf-99999999-999")
        
        assert feedback is None

    def test_list_feedback_no_filters(self, setup_feedback_files):
        """list_feedback should return all feedback."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedbacks = store.list_feedback()
        
        assert len(feedbacks) == 3
        store.close()

    def test_list_feedback_filter_by_domain(self, setup_feedback_files):
        """list_feedback should filter by problem_domain."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        async_dev_feedbacks = store.list_feedback(problem_domain="async_dev")
        product_feedbacks = store.list_feedback(problem_domain="product")
        uncertain_feedbacks = store.list_feedback(problem_domain="uncertain")
        
        assert len(async_dev_feedbacks) == 1
        assert len(product_feedbacks) == 1
        assert len(uncertain_feedbacks) == 1
        store.close()

    def test_list_feedback_filter_by_issue_type(self, setup_feedback_files):
        """list_feedback should filter by issue_type."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedbacks = store.list_feedback(issue_type="cli_behavior")
        
        assert len(feedbacks) == 1
        assert feedbacks[0]["issue_type"] == "cli_behavior"
        store.close()

    def test_list_feedback_filter_by_requires_followup(self, setup_feedback_files):
        """list_feedback should filter by requires_followup."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedbacks = store.list_feedback(requires_followup=True)
        
        assert len(feedbacks) == 3
        store.close()

    def test_list_feedback_filter_by_confidence(self, setup_feedback_files):
        """list_feedback should filter by confidence."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedbacks = store.list_feedback(confidence="high")
        
        assert len(feedbacks) == 1
        assert feedbacks[0]["confidence"] == "high"
        store.close()

    def test_list_feedback_filter_by_escalation(self, setup_feedback_files):
        """list_feedback should filter by escalation_recommendation."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedbacks = store.list_feedback(escalation_recommendation="candidate_issue")
        
        assert len(feedbacks) == 1
        assert feedbacks[0]["escalation_recommendation"] == "candidate_issue"
        store.close()

    def test_update_feedback(self, setup_feedback_files):
        """update_feedback should update feedback fields."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        updated = store.update_feedback(
            setup_feedback_files["async_dev_id"],
            resolution="fixed",
            status="resolved",
        )
        
        assert updated is not None
        assert updated["resolution"] == "fixed"
        assert updated["status"] == "resolved"
        store.close()

    def test_update_feedback_validates_resolution(self, setup_feedback_files):
        """update_feedback should validate resolution."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        with pytest.raises(ValueError, match="Invalid resolution"):
            store.update_feedback(
                setup_feedback_files["async_dev_id"],
                resolution="invalid",
            )
        store.close()

    def test_get_feedback_for_date(self, setup_feedback_files):
        """get_feedback_for_date should filter by date."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        feedbacks = store.get_feedback_for_date("2026-04-10")
        
        assert len(feedbacks) == 3
        
        other_date_feedbacks = store.get_feedback_for_date("2026-04-11")
        assert len(other_date_feedbacks) == 0
        store.close()

    def test_get_followup_summary(self, setup_feedback_files):
        """get_followup_summary should return summary counts with triage info."""
        store = WorkflowFeedbackStore(
            project_path=setup_feedback_files["temp_dir"] / "test-product",
            runtime_path=setup_feedback_files["temp_dir"] / ".runtime",
            use_sqlite=True,
        )
        
        summary = store.get_followup_summary()
        
        assert summary["total_followup_needed"] == 3
        assert summary["self_corrected_count"] == 1
        assert "by_issue_type" in summary
        assert "by_problem_domain" in summary
        assert "by_escalation" in summary
        assert summary["candidate_issue_count"] == 1
        store.close()


class TestInferProblemDomain:
    """Tests for infer_problem_domain method."""

    def test_infer_async_dev_types(self, setup_feedback_store):
        """infer_problem_domain should return async_dev for known async-dev issue types."""
        store = setup_feedback_store
        
        async_dev_types = [
            "cli_behavior",
            "persistence",
            "runtime",
            "recovery_logic",
            "planning",
            "execution_pack",
            "state_mismatch",
            "summary_review",
            "archive_history",
        ]
        
        for issue_type in async_dev_types:
            inferred = store.infer_problem_domain(issue_type)
            assert inferred == "async_dev", f"Expected async_dev for {issue_type}"
        
        store.close()

    def test_infer_uncertain_types(self, setup_feedback_store):
        """infer_problem_domain should return uncertain for uncertain issue types."""
        store = setup_feedback_store
        
        uncertain_types = ["repo_integration", "sequencing", "other"]
        
        for issue_type in uncertain_types:
            inferred = store.infer_problem_domain(issue_type)
            assert inferred == "uncertain", f"Expected uncertain for {issue_type}"
        
        store.close()

    def test_infer_unknown_type_defaults_to_uncertain(self, setup_feedback_store):
        """infer_problem_domain should default to uncertain for unknown types."""
        store = setup_feedback_store
        
        inferred = store.infer_problem_domain("unknown_type")
        
        assert inferred == "uncertain"
        store.close()


class TestTriageFeedback:
    """Tests for triage_feedback method."""

    def test_triage_feedback_adds_domain(self, setup_feedback_store):
        """triage_feedback should update problem_domain."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="uncertain",
            issue_type="repo_integration",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
            product_id="test-product",
        )
        
        triaged = store.triage_feedback(
            feedback["feedback_id"],
            problem_domain="async_dev",
        )
        
        assert triaged["problem_domain"] == "async_dev"
        assert triaged["triaged_at"] is not None
        store.close()

    def test_triage_feedback_adds_confidence(self, setup_feedback_store):
        """triage_feedback should update confidence."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
        )
        
        triaged = store.triage_feedback(
            feedback["feedback_id"],
            confidence="high",
        )
        
        assert triaged["confidence"] == "high"
        assert triaged["triaged_at"] is not None
        store.close()

    def test_triage_feedback_adds_escalation(self, setup_feedback_store):
        """triage_feedback should update escalation_recommendation."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
        )
        
        triaged = store.triage_feedback(
            feedback["feedback_id"],
            escalation_recommendation="candidate_issue",
        )
        
        assert triaged["escalation_recommendation"] == "candidate_issue"
        assert triaged["triaged_at"] is not None
        store.close()

    def test_triage_feedback_adds_note(self, setup_feedback_store):
        """triage_feedback should add triage_note."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
        )
        
        triaged = store.triage_feedback(
            feedback["feedback_id"],
            triage_note="This is confirmed as a CLI bug",
        )
        
        assert triaged["triage_note"] == "This is confirmed as a CLI bug"
        assert triaged["triaged_at"] is not None
        store.close()

    def test_triage_feedback_combines_params(self, setup_feedback_store):
        """triage_feedback should allow combining all triage params."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="uncertain",
            issue_type="repo_integration",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
            product_id="test-product",
        )
        
        triaged = store.triage_feedback(
            feedback["feedback_id"],
            problem_domain="async_dev",
            confidence="high",
            escalation_recommendation="candidate_issue",
            triage_note="Confirmed async-dev issue",
        )
        
        assert triaged["problem_domain"] == "async_dev"
        assert triaged["confidence"] == "high"
        assert triaged["escalation_recommendation"] == "candidate_issue"
        assert triaged["triage_note"] == "Confirmed async-dev issue"
        assert triaged["triaged_at"] is not None
        store.close()

    def test_triage_feedback_validates_domain(self, setup_feedback_store):
        """triage_feedback should validate problem_domain."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
        )
        
        with pytest.raises(ValueError, match="Invalid problem_domain"):
            store.triage_feedback(
                feedback["feedback_id"],
                problem_domain="invalid_domain",
            )
        store.close()

    def test_triage_feedback_validates_confidence(self, setup_feedback_store):
        """triage_feedback should validate confidence."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
        )
        
        with pytest.raises(ValueError, match="Invalid confidence"):
            store.triage_feedback(
                feedback["feedback_id"],
                confidence="invalid",
            )
        store.close()

    def test_triage_feedback_validates_escalation(self, setup_feedback_store):
        """triage_feedback should validate escalation_recommendation."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
        )
        
        with pytest.raises(ValueError, match="Invalid escalation_recommendation"):
            store.triage_feedback(
                feedback["feedback_id"],
                escalation_recommendation="invalid",
            )
        store.close()

    def test_triage_feedback_not_found(self, setup_feedback_store):
        """triage_feedback should return None for missing feedback."""
        store = setup_feedback_store
        
        triaged = store.triage_feedback("wf-99999999-999", problem_domain="async_dev")
        
        assert triaged is None
        store.close()


class TestWorkflowFeedbackSQLite:
    """Tests for SQLite integration."""

    def test_save_and_load_via_sqlite(self, setup_feedback_store):
        """Feedback should be saved to SQLite and loadable."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="product",
            issue_type="execution_pack",
            detected_by="operator",
            detected_in="plan-day",
            description="SQLite test",
            self_corrected=False,
            requires_followup=True,
            product_id="test-product",
        )
        
        loaded = store.load_feedback(feedback["feedback_id"])
        
        assert loaded is not None
        assert loaded["description"] == "SQLite test"
        
        store.close()

    def test_list_via_sqlite_with_filters(self, setup_feedback_store):
        """SQLite list should apply filters."""
        store = setup_feedback_store
        
        store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Feedback 1",
            self_corrected=True,
            requires_followup=False,
        )
        
        store.record_feedback(
            problem_domain="async_dev",
            issue_type="persistence",
            detected_by="operator",
            detected_in="test",
            description="Feedback 2",
            self_corrected=False,
            requires_followup=True,
        )
        
        feedbacks = store.list_feedback(problem_domain="async_dev", issue_type="cli_behavior")
        
        assert len(feedbacks) == 1
        
        store.close()

    def test_triage_via_sqlite(self, setup_feedback_store):
        """Triage should update SQLite record."""
        store = setup_feedback_store
        
        feedback = store.record_feedback(
            problem_domain="async_dev",
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="SQLite triage test",
            self_corrected=False,
            requires_followup=True,
        )
        
        triaged = store.triage_feedback(
            feedback["feedback_id"],
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        loaded = store.load_feedback(feedback["feedback_id"])
        
        assert loaded["confidence"] == "high"
        assert loaded["escalation_recommendation"] == "candidate_issue"
        
        store.close()


class TestCreateWorkflowFeedbackForReview:
    """Tests for create_workflow_feedback_for_review helper."""

    def test_create_section_empty_feedbacks(self):
        """Should create section with zero counts for empty list."""
        section = create_workflow_feedback_for_review([])
        
        assert section["encountered_today"] == 0
        assert section["items"] == []
        assert section["followup_needed_count"] == 0
        assert section["self_corrected_count"] == 0
        assert section["async_dev_count"] == 0
        assert section["product_count"] == 0
        assert section["uncertain_count"] == 0
        assert section["candidate_issue_count"] == 0

    def test_create_section_with_feedbacks(self):
        """Should create section with proper counts and triage info."""
        feedbacks = [
            {
                "feedback_id": "wf-20260410-001",
                "issue_type": "execution_pack",
                "problem_domain": "async_dev",
                "description": "Test issue",
                "self_corrected": True,
                "requires_followup": True,
                "confidence": "high",
                "escalation_recommendation": "candidate_issue",
                "triaged_at": "2026-04-10T10:00:00",
                "resolution": "workaround",
                "status": "open",
            },
            {
                "feedback_id": "wf-20260410-002",
                "issue_type": "cli_behavior",
                "problem_domain": "async_dev",
                "description": "Another issue",
                "self_corrected": False,
                "requires_followup": True,
                "resolution": "none",
                "status": "open",
            },
        ]
        
        section = create_workflow_feedback_for_review(feedbacks)
        
        assert section["encountered_today"] == 2
        assert section["followup_needed_count"] == 2
        assert section["self_corrected_count"] == 1
        assert section["async_dev_count"] == 2
        assert section["product_count"] == 0
        assert section["uncertain_count"] == 0
        assert section["candidate_issue_count"] == 1
        assert section["review_needed_count"] == 0
        assert len(section["items"]) == 2

    def test_create_section_with_mixed_domains(self):
        """Should count domains correctly."""
        feedbacks = [
            {"feedback_id": "wf-001", "problem_domain": "async_dev", "issue_type": "cli_behavior", "description": "1", "self_corrected": False, "requires_followup": True},
            {"feedback_id": "wf-002", "problem_domain": "product", "issue_type": "execution_pack", "description": "2", "self_corrected": False, "requires_followup": True},
            {"feedback_id": "wf-003", "problem_domain": "uncertain", "issue_type": "repo_integration", "description": "3", "self_corrected": False, "requires_followup": True},
        ]
        
        section = create_workflow_feedback_for_review(feedbacks)
        
        assert section["async_dev_count"] == 1
        assert section["product_count"] == 1
        assert section["uncertain_count"] == 1

    def test_create_section_items_have_triage_info(self):
        """Items should include triage fields."""
        feedbacks = [
            {
                "feedback_id": "wf-001",
                "problem_domain": "async_dev",
                "issue_type": "cli_behavior",
                "description": "Test",
                "self_corrected": False,
                "requires_followup": True,
                "confidence": "high",
                "escalation_recommendation": "candidate_issue",
                "triaged_at": "2026-04-10T10:00:00",
            },
        ]
        
        section = create_workflow_feedback_for_review(feedbacks)
        
        item = section["items"][0]
        assert item["confidence"] == "high"
        assert item["escalation_recommendation"] == "candidate_issue"
        assert item["triaged"] == True


class TestFeedbackCLI:
    """Tests for CLI commands."""

    def test_feedback_record_product_domain(self, temp_dir):
        """feedback record should create product-domain feedback."""
        project_path = temp_dir / "test-product"
        project_path.mkdir(parents=True)
        
        result = runner.invoke(
            app,
            [
                "record",
                "--domain", "product",
                "--product", "test-product",
                "--type", "execution_pack",
                "--in", "plan-day",
                "--description", "Test feedback",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Recorded" in result.output

    def test_feedback_record_async_dev_domain(self, temp_dir):
        """feedback record should create async_dev-domain feedback."""
        result = runner.invoke(
            app,
            [
                "record",
                "--domain", "async_dev",
                "--type", "cli_behavior",
                "--in", "status",
                "--description", "CLI bug",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Recorded" in result.output

    def test_feedback_record_auto_inferred_domain(self, temp_dir):
        """feedback record should auto-infer domain when not specified."""
        result = runner.invoke(
            app,
            [
                "record",
                "--type", "cli_behavior",
                "--in", "status",
                "--description", "Auto-inferred",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Recorded" in result.output
        assert "async_dev" in result.output

    def test_feedback_record_with_triage_params(self, temp_dir):
        """feedback record should accept triage params."""
        result = runner.invoke(
            app,
            [
                "record",
                "--domain", "async_dev",
                "--type", "cli_behavior",
                "--in", "status",
                "--description", "CLI bug with triage",
                "--confidence", "high",
                "--escalation", "candidate_issue",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Recorded" in result.output
        assert "candidate_issue" in result.output

    def test_feedback_record_requires_product_for_product_domain(self, temp_dir):
        """feedback record should require --product for product domain."""
        result = runner.invoke(
            app,
            [
                "record",
                "--domain", "product",
                "--type", "execution_pack",
                "--in", "plan-day",
                "--description", "Test",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 1
        assert "product_id is required" in result.output

    def test_feedback_list(self, setup_feedback_files):
        """feedback list should show all feedback."""
        result = runner.invoke(
            app,
            ["list", "--product", "test-product", "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 0
        assert "wf-" in result.output

    def test_feedback_list_filter_followup_needed(self, setup_feedback_files):
        """feedback list --followup-needed should filter."""
        result = runner.invoke(
            app,
            ["list", "--followup-needed", "--product", "test-product", "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 0

    def test_feedback_list_filter_domain(self, setup_feedback_files):
        """feedback list --domain should filter."""
        result = runner.invoke(
            app,
            ["list", "--domain", "async_dev", "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 0
        assert "async_dev" in result.output

    def test_feedback_list_filter_escalation(self, setup_feedback_files):
        """feedback list --escalation should filter."""
        result = runner.invoke(
            app,
            ["list", "--escalation", "candidate_issue", "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 0
        assert "candidate_issue" in result.output

    def test_feedback_show(self, setup_feedback_files):
        """feedback show should display feedback details."""
        feedback_id = setup_feedback_files["async_dev_id"]
        result = runner.invoke(
            app,
            ["show", "--feedback-id", feedback_id, "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 0
        assert "Workflow Feedback:" in result.output
        assert "Triage Information" in result.output

    def test_feedback_show_not_found(self, setup_feedback_files):
        """feedback show should handle missing feedback."""
        result = runner.invoke(
            app,
            ["show", "--feedback-id", "wf-99999999-999", "--product", "test-product", "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 1
        assert "Feedback not found" in result.output

    def test_feedback_triage(self, setup_feedback_files):
        """feedback triage should update triage info."""
        feedback_id = setup_feedback_files["product_id"]
        result = runner.invoke(
            app,
            [
                "triage",
                "--feedback-id", feedback_id,
                "--domain", "async_dev",
                "--confidence", "high",
                "--escalation", "candidate_issue",
                "--note", "Confirmed async-dev bug",
                "--product", "test-product",
                "--path", str(setup_feedback_files["temp_dir"]),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Triage Updated" in result.output
        assert "candidate_issue" in result.output

    def test_feedback_triage_not_found(self, setup_feedback_files):
        """feedback triage should handle missing feedback."""
        result = runner.invoke(
            app,
            [
                "triage",
                "--feedback-id", "wf-99999999-999",
                "--domain", "async_dev",
                "--product", "test-product",
                "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 1
        assert "Feedback not found" in result.output

    def test_feedback_update(self, setup_feedback_files):
        """feedback update should modify feedback."""
        feedback_id = setup_feedback_files["async_dev_id"]
        result = runner.invoke(
            app,
            [
                "update",
                "--feedback-id", feedback_id,
                "--resolution", "fixed",
                "--status", "resolved",
                "--path", str(setup_feedback_files["temp_dir"]),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Updated" in result.output

    def test_feedback_summary(self, setup_feedback_files):
        """feedback summary should show counts with domain breakdown."""
        result = runner.invoke(
            app,
            ["summary", "--product", "test-product", "--path", str(setup_feedback_files["temp_dir"])],
        )
        
        assert result.exit_code == 0
        assert "Workflow Feedback Summary" in result.output
        assert "By Problem Domain" in result.output
        assert "By Escalation" in result.output