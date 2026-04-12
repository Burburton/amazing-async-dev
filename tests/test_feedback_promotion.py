"""Tests for feedback promotion - Feature 019c."""

import pytest
from pathlib import Path
from datetime import datetime
from typer.testing import CliRunner

from runtime.feedback_promotion_store import FeedbackPromotionStore, create_promotions_for_review
from runtime.workflow_feedback_store import WorkflowFeedbackStore
from cli.commands.feedback import app

runner = CliRunner()


@pytest.fixture
def temp_dir(tmp_path):
    """Create temp directory for tests."""
    return tmp_path


@pytest.fixture
def setup_promotion_store(temp_dir):
    """Create promotion store."""
    runtime_path = temp_dir / ".runtime"
    runtime_path.mkdir(parents=True)
    
    store = FeedbackPromotionStore(runtime_path=runtime_path)
    yield store
    store.close()


@pytest.fixture
def setup_feedback_and_promotion(temp_dir):
    """Create feedback store and promotion store together."""
    runtime_path = temp_dir / ".runtime"
    runtime_path.mkdir(parents=True)
    
    feedback_store = WorkflowFeedbackStore(runtime_path=runtime_path)
    promotion_store = FeedbackPromotionStore(runtime_path=runtime_path)
    
    yield {"feedback": feedback_store, "promotion": promotion_store, "runtime": runtime_path}
    
    feedback_store.close()
    promotion_store.close()


class TestFeedbackPromotionStore:
    """Tests for FeedbackPromotionStore."""

    def test_generate_promotion_id(self, setup_promotion_store):
        """generate_promotion_id should create valid ID pattern."""
        store = setup_promotion_store
        
        promo_id = store.generate_promotion_id()
        
        assert promo_id.startswith("promo-")
        assert len(promo_id) == 18

    def test_promote_feedback(self, setup_feedback_and_promotion):
        """promote_feedback should create promotion from triaged feedback."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="status",
            description="CLI bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promotion = promotion_store.promote_feedback(
            source_feedback=feedback,
            promotion_reason="system_bug",
            promotion_note="Confirmed async-dev bug",
        )
        
        assert promotion["promotion_id"].startswith("promo-")
        assert promotion["source_feedback_id"] == feedback["feedback_id"]
        assert promotion["promotion_reason"] == "system_bug"
        assert promotion["promotion_note"] == "Confirmed async-dev bug"
        assert promotion["followup_status"] == "open"
        assert promotion["source_problem_domain"] == "async_dev"
        assert promotion["source_confidence"] == "high"

    def test_promote_feedback_requires_triage(self, setup_feedback_and_promotion):
        """promote_feedback should require source feedback to be triaged."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Not triaged",
            self_corrected=False,
            requires_followup=True,
        )
        
        with pytest.raises(ValueError, match="must be triaged"):
            promotion_store.promote_feedback(source_feedback=feedback)

    def test_promote_feedback_prevents_duplicates(self, setup_feedback_and_promotion):
        """promote_feedback should prevent duplicate promotion."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
            confidence="medium",
            escalation_recommendation="review_needed",
        )
        
        promo1 = promotion_store.promote_feedback(source_feedback=feedback)
        
        feedback["promotion_status"] = "promoted"
        feedback["promotion_id"] = promo1["promotion_id"]
        
        with pytest.raises(ValueError, match="already been promoted"):
            promotion_store.promote_feedback(source_feedback=feedback)

    def test_promote_feedback_validates_reason(self, setup_feedback_and_promotion):
        """promote_feedback should validate promotion_reason."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
            confidence="medium",
            escalation_recommendation="review_needed",
        )
        
        with pytest.raises(ValueError, match="Invalid promotion_reason"):
            promotion_store.promote_feedback(
                source_feedback=feedback,
                promotion_reason="invalid_reason",
            )

    def test_load_promotion(self, setup_feedback_and_promotion):
        """load_promotion should load promotion by ID."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Test",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promotion = promotion_store.promote_feedback(source_feedback=feedback)
        
        loaded = promotion_store.load_promotion(promotion["promotion_id"])
        
        assert loaded is not None
        assert loaded["promotion_id"] == promotion["promotion_id"]
        assert loaded["source_feedback_id"] == feedback["feedback_id"]

    def test_load_promotion_not_found(self, setup_promotion_store):
        """load_promotion should return None for missing promotion."""
        store = setup_promotion_store
        
        loaded = store.load_promotion("promo-99999999-999")
        
        assert loaded is None

    def test_list_promotions(self, setup_feedback_and_promotion):
        """list_promotions should return promotions."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback1 = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug 1",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        feedback2 = feedback_store.record_feedback(
            issue_type="persistence",
            detected_by="operator",
            detected_in="test",
            description="Bug 2",
            self_corrected=False,
            requires_followup=True,
            confidence="medium",
            escalation_recommendation="review_needed",
        )
        
        promo1 = promotion_store.promote_feedback(source_feedback=feedback1)
        promo2 = promotion_store.promote_feedback(source_feedback=feedback2)
        
        promotions = promotion_store.list_promotions()
        
        assert len(promotions) == 2

    def test_list_promotions_filter_by_status(self, setup_feedback_and_promotion):
        """list_promotions should filter by followup_status."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promo = promotion_store.promote_feedback(source_feedback=feedback)
        
        promotion_store.update_promotion(promo["promotion_id"], followup_status="reviewed")
        
        open_promos = promotion_store.list_promotions(followup_status="open")
        reviewed_promos = promotion_store.list_promotions(followup_status="reviewed")
        
        assert len(open_promos) == 0
        assert len(reviewed_promos) == 1

    def test_update_promotion(self, setup_feedback_and_promotion):
        """update_promotion should change followup_status."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promo = promotion_store.promote_feedback(source_feedback=feedback)
        
        updated = promotion_store.update_promotion(
            promo["promotion_id"],
            followup_status="addressed",
            addressed_note="Fixed in commit abc123",
        )
        
        assert updated["followup_status"] == "addressed"
        assert updated["addressed_note"] == "Fixed in commit abc123"
        assert updated["addressed_at"] is not None

    def test_update_promotion_validates_status(self, setup_feedback_and_promotion):
        """update_promotion should validate followup_status."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promo = promotion_store.promote_feedback(source_feedback=feedback)
        
        with pytest.raises(ValueError, match="Invalid followup_status"):
            promotion_store.update_promotion(promo["promotion_id"], followup_status="invalid")

    def test_get_promotion_summary(self, setup_feedback_and_promotion):
        """get_promotion_summary should return summary counts."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        promotion_store = setup_feedback_and_promotion["promotion"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promotion_store.promote_feedback(source_feedback=feedback)
        
        summary = promotion_store.get_promotion_summary()
        
        assert summary["total_promotions"] == 1
        assert summary["open_count"] == 1
        assert "by_followup_status" in summary
        assert "by_promotion_reason" in summary


class TestWorkflowFeedbackPromotion:
    """Tests for workflow feedback promotion integration."""

    def test_promote_feedback_via_feedback_store(self, setup_feedback_and_promotion):
        """promote_feedback on WorkflowFeedbackStore should work."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug to promote",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promotion = feedback_store.promote_feedback(
            feedback_id=feedback["feedback_id"],
            promotion_reason="system_bug",
            promotion_note="Priority fix needed",
        )
        
        assert promotion["promotion_id"].startswith("promo-")
        assert promotion["source_feedback_id"] == feedback["feedback_id"]

    def test_promote_updates_feedback_promotion_status(self, setup_feedback_and_promotion):
        """Promotion should update feedback's promotion_status."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promotion = feedback_store.promote_feedback(feedback_id=feedback["feedback_id"])
        
        updated_feedback = feedback_store.load_feedback(feedback["feedback_id"])
        
        assert updated_feedback["promotion_status"] == "promoted"
        assert updated_feedback["promotion_id"] == promotion["promotion_id"]

    def test_promote_feedback_not_found(self, setup_feedback_and_promotion):
        """promote_feedback should raise for missing feedback."""
        feedback_store = setup_feedback_and_promotion["feedback"]
        
        with pytest.raises(ValueError, match="Feedback not found"):
            feedback_store.promote_feedback(feedback_id="wf-99999999-999")


class TestCreatePromotionsForReview:
    """Tests for create_promotions_for_review helper."""

    def test_create_section_empty(self):
        """Should return empty section for no promotions."""
        section = create_promotions_for_review([])
        
        assert section["promoted_count"] == 0
        assert section["open_count"] == 0
        assert section["promotion_ids"] == []

    def test_create_section_with_promotions(self):
        """Should return section with promotion info."""
        promotions = [
            {
                "promotion_id": "promo-20260412-001",
                "summary": "CLI bug needs fixing",
                "followup_status": "open",
            },
            {
                "promotion_id": "promo-20260412-002",
                "summary": "Persistence issue",
                "followup_status": "reviewed",
            },
        ]
        
        section = create_promotions_for_review(promotions)
        
        assert section["promoted_count"] == 2
        assert section["open_count"] == 2
        assert len(section["promotion_ids"]) == 2
        assert len(section["summaries"]) == 2


class TestPromotionCLI:
    """Tests for promotion CLI commands."""

    def test_promote_command(self, temp_dir):
        """promote command should create promotion."""
        runtime_path = temp_dir / ".runtime"
        runtime_path.mkdir(parents=True)
        
        feedback_store = WorkflowFeedbackStore(runtime_path=runtime_path)
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="CLI bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        feedback_store.close()
        
        result = runner.invoke(
            app,
            [
                "promote",
                "--feedback-id", feedback["feedback_id"],
                "--reason", "system_bug",
                "--note", "Priority fix",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 0
        assert "Feedback Promoted" in result.output
        assert "promo-" in result.output

    def test_promote_command_not_triaged(self, temp_dir):
        """promote command should fail for untriaged feedback."""
        runtime_path = temp_dir / ".runtime"
        runtime_path.mkdir(parents=True)
        
        feedback_store = WorkflowFeedbackStore(runtime_path=runtime_path)
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Not triaged",
            self_corrected=False,
            requires_followup=True,
        )
        
        feedback_store.close()
        
        result = runner.invoke(
            app,
            [
                "promote",
                "--feedback-id", feedback["feedback_id"],
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 1
        assert "must be triaged" in result.output

    def test_promotions_list(self, temp_dir):
        """promotions list should show promotions."""
        runtime_path = temp_dir / ".runtime"
        runtime_path.mkdir(parents=True)
        
        feedback_store = WorkflowFeedbackStore(runtime_path=runtime_path)
        promotion_store = FeedbackPromotionStore(runtime_path=runtime_path)
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promotion_store.promote_feedback(source_feedback=feedback)
        feedback_store.close()
        promotion_store.close()
        
        result = runner.invoke(
            app,
            ["promotions", "list", "--path", str(temp_dir)],
        )
        
        assert result.exit_code == 0
        assert "Promoted Feedback" in result.output

    def test_promotions_show(self, temp_dir):
        """promotions show should display promotion details."""
        runtime_path = temp_dir / ".runtime"
        runtime_path.mkdir(parents=True)
        
        feedback_store = WorkflowFeedbackStore(runtime_path=runtime_path)
        promotion_store = FeedbackPromotionStore(runtime_path=runtime_path)
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="CLI bug description",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promo = promotion_store.promote_feedback(source_feedback=feedback)
        feedback_store.close()
        promotion_store.close()
        
        result = runner.invoke(
            app,
            ["promotions", "show", "--promotion-id", promo["promotion_id"], "--path", str(temp_dir)],
        )
        
        assert result.exit_code == 0
        assert "Promoted Feedback" in result.output
        assert "Source Triage Information" in result.output

    def test_promotions_update(self, temp_dir):
        """promotions update should change status."""
        runtime_path = temp_dir / ".runtime"
        runtime_path.mkdir(parents=True)
        
        feedback_store = WorkflowFeedbackStore(runtime_path=runtime_path)
        promotion_store = FeedbackPromotionStore(runtime_path=runtime_path)
        
        feedback = feedback_store.record_feedback(
            issue_type="cli_behavior",
            detected_by="operator",
            detected_in="test",
            description="Bug",
            self_corrected=False,
            requires_followup=True,
            confidence="high",
            escalation_recommendation="candidate_issue",
        )
        
        promo = promotion_store.promote_feedback(source_feedback=feedback)
        feedback_store.close()
        promotion_store.close()
        
        result = runner.invoke(
            app,
            [
                "promotions", "update",
                "--promotion-id", promo["promotion_id"],
                "--status", "addressed",
                "--note", "Fixed",
                "--path", str(temp_dir),
            ],
        )
        
        assert result.exit_code == 0
        assert "Promotion Updated" in result.output