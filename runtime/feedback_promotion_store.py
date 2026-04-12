"""Feedback promotion store - formalized follow-up from triaged workflow feedback.

Feature 019c: Feedback Promotion / Issue Escalation

Provides:
- File-based YAML storage for human readability
- SQLite integration for structured queries
- Promotion ID generation
- Linkage preservation to source feedback
- Duplicate prevention
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from runtime.adapters.filesystem_adapter import FilesystemAdapter


class FeedbackPromotionStore:
    """Store for promoted feedback records with dual persistence (file + SQLite)."""

    PROMOTION_REASON_VALUES = [
        "system_bug",
        "ux_issue",
        "workflow_improvement",
        "documentation_gap",
        "integration_issue",
        "other",
    ]

    FOLLOWUP_STATUS_VALUES = [
        "open",
        "reviewed",
        "in_progress",
        "addressed",
        "closed",
    ]

    def __init__(
        self,
        runtime_path: Path | None = None,
        use_sqlite: bool = True,
    ):
        """Initialize promotion store.

        Args:
            runtime_path: Path to global runtime directory
            use_sqlite: Whether to use SQLite for structured queries
        """
        self.fs = FilesystemAdapter()
        self.runtime_path = runtime_path or Path(".runtime")
        self.use_sqlite = use_sqlite

        self.promotions_path = self.runtime_path / "feedback-promotions"
        self._sqlite_store = None

    def _get_sqlite_store(self):
        """Get or create SQLite store reference."""
        if self._sqlite_store is None and self.use_sqlite:
            from runtime.sqlite_state_store import SQLiteStateStore

            db_path = self.runtime_path / "amazing_async_dev.db"
            self._sqlite_store = SQLiteStateStore(db_path=db_path)

        return self._sqlite_store

    def generate_promotion_id(self) -> str:
        """Generate unique promotion_id following pattern promo-YYYYMMDD-###."""
        date_str = datetime.now().strftime("%Y%m%d")
        existing_count = self._count_existing_promotions(date_str)
        return f"promo-{date_str}-{existing_count + 1:03d}"

    def _count_existing_promotions(self, date_str: str) -> int:
        """Count existing promotions for given date."""
        count = 0

        if self.promotions_path.exists():
            existing = list(self.promotions_path.glob(f"promo-{date_str}-*.yaml"))
            count += len(existing)

        if self.use_sqlite and self._sqlite_store:
            sqlite_count = self._sqlite_store.count_promotions_by_date(date_str)
            count = max(count, sqlite_count)

        return count

    def promote_feedback(
        self,
        source_feedback: dict[str, Any],
        summary: str | None = None,
        promotion_reason: str = "system_bug",
        promotion_note: str | None = None,
        candidate_feature: str | None = None,
        artifact_reference: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Promote a triaged workflow feedback to formal follow-up.

        Args:
            source_feedback: The source workflow feedback record (must be triaged)
            summary: Summary for follow-up (defaults to source description)
            promotion_reason: Reason for promotion
            promotion_note: Optional explanation
            candidate_feature: Optional feature ID for addressing
            artifact_reference: Optional artifact reference

        Returns:
            The created promotion record

        Raises:
            ValueError: If source feedback is not triaged or already promoted
        """
        source_id = source_feedback.get("feedback_id")

        if not source_id:
            raise ValueError("source_feedback must have feedback_id")

        if not source_feedback.get("triaged_at"):
            raise ValueError("source_feedback must be triaged before promotion")

        if source_feedback.get("promotion_status") == "promoted":
            raise ValueError(f"Feedback {source_id} has already been promoted")

        if promotion_reason not in self.PROMOTION_REASON_VALUES:
            raise ValueError(f"Invalid promotion_reason: {promotion_reason}")

        promotion_id = self.generate_promotion_id()

        if summary is None:
            summary = source_feedback.get("description", "")

        promotion = {
            "promotion_id": promotion_id,
            "source_feedback_id": source_id,
            "summary": summary,
            "promotion_reason": promotion_reason,
            "promoted_at": datetime.now().isoformat(),
            "followup_status": "open",
        }

        if promotion_note:
            promotion["promotion_note"] = promotion_note

        if source_feedback.get("problem_domain"):
            promotion["source_problem_domain"] = source_feedback["problem_domain"]
        if source_feedback.get("confidence"):
            promotion["source_confidence"] = source_feedback["confidence"]
        if source_feedback.get("escalation_recommendation"):
            promotion["source_escalation_recommendation"] = source_feedback["escalation_recommendation"]
        if source_feedback.get("issue_type"):
            promotion["source_issue_type"] = source_feedback["issue_type"]
        if source_feedback.get("description"):
            promotion["source_description"] = source_feedback["description"]

        if candidate_feature:
            promotion["candidate_feature_followup"] = candidate_feature
        if artifact_reference:
            promotion["artifact_reference"] = artifact_reference

        self._save_promotion_file(promotion)

        if self.use_sqlite:
            self._save_promotion_sqlite(promotion)

        return promotion

    def _save_promotion_file(self, promotion: dict[str, Any]) -> None:
        """Save promotion to YAML file."""
        self.promotions_path.mkdir(parents=True, exist_ok=True)

        file_path = self.promotions_path / f"{promotion['promotion_id']}.yaml"

        yaml_content = yaml.dump(promotion, default_flow_style=False, sort_keys=False)

        self.fs.write_file(file_path, yaml_content)

    def _save_promotion_sqlite(self, promotion: dict[str, Any]) -> None:
        """Save promotion to SQLite."""
        sqlite_store = self._get_sqlite_store()
        if sqlite_store:
            sqlite_store.save_promotion(promotion)

    def load_promotion(self, promotion_id: str) -> dict[str, Any] | None:
        """Load a promotion record by ID.

        Args:
            promotion_id: The promotion ID

        Returns:
            Promotion record or None if not found
        """
        if self.use_sqlite:
            sqlite_store = self._get_sqlite_store()
            if sqlite_store:
                promotion = sqlite_store.load_promotion(promotion_id)
                if promotion:
                    return promotion

        file_path = self.promotions_path / f"{promotion_id}.yaml"
        if not file_path.exists():
            return None

        content = self.fs.read_file(file_path)
        return yaml.safe_load(content)

    def list_promotions(
        self,
        followup_status: str | None = None,
        promotion_reason: str | None = None,
        source_domain: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List promotion records with optional filters.

        Args:
            followup_status: Filter by followup status
            promotion_reason: Filter by promotion reason
            source_domain: Filter by source problem domain
            limit: Maximum number to return

        Returns:
            List of promotion records
        """
        if self.use_sqlite:
            sqlite_store = self._get_sqlite_store()
            if sqlite_store:
                return sqlite_store.list_promotions(
                    followup_status=followup_status,
                    promotion_reason=promotion_reason,
                    source_domain=source_domain,
                    limit=limit,
                )

        promotions = []
        if not self.promotions_path.exists():
            return promotions

        for yaml_file in sorted(self.promotions_path.glob("promo-*.yaml"), reverse=True):
            content = self.fs.read_file(yaml_file)
            promotion = yaml.safe_load(content)

            if followup_status and promotion.get("followup_status") != followup_status:
                continue
            if promotion_reason and promotion.get("promotion_reason") != promotion_reason:
                continue
            if source_domain and promotion.get("source_problem_domain") != source_domain:
                continue

            promotions.append(promotion)
            if len(promotions) >= limit:
                break

        return promotions

    def update_promotion(
        self,
        promotion_id: str,
        followup_status: str | None = None,
        addressed_note: str | None = None,
    ) -> dict[str, Any] | None:
        """Update promotion followup status.

        Args:
            promotion_id: The promotion ID
            followup_status: New followup status
            addressed_note: Note on how addressed

        Returns:
            Updated promotion or None if not found
        """
        promotion = self.load_promotion(promotion_id)
        if not promotion:
            return None

        if followup_status:
            if followup_status not in self.FOLLOWUP_STATUS_VALUES:
                raise ValueError(f"Invalid followup_status: {followup_status}")
            promotion["followup_status"] = followup_status

            if followup_status == "addressed":
                promotion["addressed_at"] = datetime.now().isoformat()

        if addressed_note:
            promotion["addressed_note"] = addressed_note

        self._save_promotion_file(promotion)

        if self.use_sqlite:
            self._save_promotion_sqlite(promotion)

        return promotion

    def get_promotion_summary(self) -> dict[str, Any]:
        """Get summary statistics for promotions.

        Returns:
            Summary with counts by status and reason
        """
        promotions = self.list_promotions(limit=1000)

        summary = {
            "total_promotions": len(promotions),
            "by_followup_status": {},
            "by_promotion_reason": {},
            "by_source_domain": {},
            "open_count": 0,
            "addressed_count": 0,
        }

        for promotion in promotions:
            status = promotion.get("followup_status", "open")
            summary["by_followup_status"][status] = summary["by_followup_status"].get(status, 0) + 1

            reason = promotion.get("promotion_reason", "system_bug")
            summary["by_promotion_reason"][reason] = summary["by_promotion_reason"].get(reason, 0) + 1

            domain = promotion.get("source_problem_domain", "unknown")
            summary["by_source_domain"][domain] = summary["by_source_domain"].get(domain, 0) + 1

            if status == "open":
                summary["open_count"] += 1
            elif status == "addressed":
                summary["addressed_count"] += 1

        return summary

    def close(self) -> None:
        """Close SQLite connection if open."""
        if self._sqlite_store:
            self._sqlite_store.sqlite.close()
            self._sqlite_store = None


def create_promotions_for_review(promotions: list[dict[str, Any]]) -> dict[str, Any]:
    """Create workflow_feedback.promotions section for DailyReviewPack.

    Args:
        promotions: List of promotion records

    Returns:
        Section with count, ids, and optional summaries
    """
    open_promotions = [p for p in promotions if p.get("followup_status") in ("open", "reviewed", "in_progress")]

    return {
        "promoted_count": len(promotions),
        "open_count": len(open_promotions),
        "promotion_ids": [p["promotion_id"] for p in open_promotions[:5]],
        "summaries": [p.get("summary", "")[:60] for p in open_promotions[:3]],
    }