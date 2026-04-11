"""Workflow feedback store - file and SQLite storage for workflow issues with triage support.

Feature 019a: Workflow Feedback Capture
Feature 019b: Workflow Feedback Triage

Provides:
- File-based YAML storage for human readability
- SQLite integration for structured queries
- Feedback ID generation
- Triage layer with problem_domain, confidence, escalation
- List/query operations with triage filters
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from runtime.adapters.filesystem_adapter import FilesystemAdapter


class WorkflowFeedbackStore:
    """Store for workflow feedback records with dual persistence (file + SQLite) and triage."""

    ISSUE_TYPES = [
        "sequencing",
        "planning",
        "execution_pack",
        "state_mismatch",
        "summary_review",
        "archive_history",
        "repo_integration",
        "recovery_logic",
        "cli_behavior",
        "persistence",
        "runtime",
        "other",
    ]

    DETECTED_BY_VALUES = [
        "operator",
        "ai_executor",
        "review_process",
        "automated_check",
        "post_analysis",
    ]

    PROBLEM_DOMAIN_VALUES = ["async_dev", "product", "uncertain"]

    CONFIDENCE_VALUES = ["low", "medium", "high"]

    ESCALATION_VALUES = ["ignore", "track_only", "review_needed", "candidate_issue"]

    RESOLUTION_VALUES = ["none", "workaround", "fixed", "deferred", "escalated"]

    STATUS_VALUES = ["open", "investigating", "resolved", "closed", "archived"]

    PRIORITY_VALUES = ["high", "medium", "low"]

    ISSUE_TYPE_TO_DOMAIN_DEFAULT = {
        "cli_behavior": "async_dev",
        "persistence": "async_dev",
        "runtime": "async_dev",
        "recovery_logic": "async_dev",
        "planning": "async_dev",
        "execution_pack": "async_dev",
        "state_mismatch": "async_dev",
        "summary_review": "async_dev",
        "archive_history": "async_dev",
        "repo_integration": "uncertain",
        "sequencing": "uncertain",
        "other": "uncertain",
    }

    def __init__(
        self,
        project_path: Path | None = None,
        runtime_path: Path | None = None,
        use_sqlite: bool = True,
    ):
        """Initialize workflow feedback store.

        Args:
            project_path: Path to specific project (for product/uncertain domain)
            runtime_path: Path to global runtime directory (for async_dev domain)
            use_sqlite: Whether to use SQLite for structured queries
        """
        self.fs = FilesystemAdapter()
        self.project_path = project_path
        self.runtime_path = runtime_path or Path(".runtime")
        self.use_sqlite = use_sqlite

        self.async_dev_feedback_path = self.runtime_path / "workflow-feedback"
        self.product_feedback_path = (
            project_path / "workflow-feedback" if project_path else None
        )

        self._sqlite_store = None

    def _get_sqlite_store(self):
        """Get or create SQLite store reference."""
        if self._sqlite_store is None and self.use_sqlite:
            from runtime.sqlite_state_store import SQLiteStateStore

            if self.project_path:
                self._sqlite_store = SQLiteStateStore(self.project_path)
            else:
                db_path = self.runtime_path / "amazing_async_dev.db"
                self._sqlite_store = SQLiteStateStore(db_path=db_path)

        return self._sqlite_store

    def infer_problem_domain(self, issue_type: str) -> str:
        """Infer default problem_domain from issue_type."""
        return self.ISSUE_TYPE_TO_DOMAIN_DEFAULT.get(issue_type, "uncertain")

    def generate_feedback_id(self) -> str:
        """Generate unique feedback_id following pattern wf-YYYYMMDD-###."""
        date_str = datetime.now().strftime("%Y%m%d")
        existing_count = self._count_existing_feedback(date_str)
        return f"wf-{date_str}-{existing_count + 1:03d}"

    def _count_existing_feedback(self, date_str: str) -> int:
        """Count existing feedback files for given date."""
        count = 0

        if self.async_dev_feedback_path.exists():
            existing = list(self.async_dev_feedback_path.glob(f"wf-{date_str}-*.yaml"))
            count += len(existing)

        if self.product_feedback_path and self.product_feedback_path.exists():
            existing = list(self.product_feedback_path.glob(f"wf-{date_str}-*.yaml"))
            count += len(existing)

        if self.use_sqlite and self._sqlite_store:
            sqlite_count = self._sqlite_store.count_workflow_feedback_by_date(date_str)
            count = max(count, sqlite_count)

        return count

    def record_feedback(
        self,
        issue_type: str,
        detected_by: str,
        detected_in: str,
        description: str,
        self_corrected: bool,
        requires_followup: bool,
        problem_domain: str | None = None,
        product_id: str | None = None,
        feature_id: str | None = None,
        execution_id: str | None = None,
        impact: str | None = None,
        artifact_reference: dict[str, Any] | None = None,
        confidence: str | None = None,
        escalation_recommendation: str | None = None,
        triage_note: str | None = None,
        resolution: str = "none",
        resolution_note: str | None = None,
        status: str = "open",
        priority: str | None = None,
        detected_at: str | None = None,
    ) -> dict[str, Any]:
        """Record a workflow feedback item.

        Args:
            problem_domain: 'async_dev', 'product', or 'uncertain' (auto-inferred if None)
            issue_type: Issue category from ISSUE_TYPES
            detected_by: Who detected the issue
            detected_in: Context where detected
            description: Issue description
            self_corrected: Whether issue was self-corrected
            requires_followup: Whether followup is needed
            product_id: Product ID (required for product/uncertain domain)
            feature_id: Optional feature ID
            execution_id: Optional execution ID
            impact: Optional impact description
            artifact_reference: Optional artifact reference dict
            confidence: Confidence level (low/medium/high)
            escalation_recommendation: Escalation level
            triage_note: Optional triage explanation
            resolution: Resolution status (default: none)
            resolution_note: Optional resolution note
            status: Tracking status (default: open)
            priority: Optional priority
            detected_at: Detection time (default: now)

        Returns:
            The created feedback record
        """
        if issue_type not in self.ISSUE_TYPES:
            raise ValueError(f"Invalid issue_type: {issue_type}. Must be one of {self.ISSUE_TYPES}")

        if detected_by not in self.DETECTED_BY_VALUES:
            raise ValueError(f"Invalid detected_by: {detected_by}. Must be one of {self.DETECTED_BY_VALUES}")

        if problem_domain is None:
            problem_domain = self.infer_problem_domain(issue_type)

        if problem_domain not in self.PROBLEM_DOMAIN_VALUES:
            raise ValueError(f"Invalid problem_domain: {problem_domain}. Must be one of {self.PROBLEM_DOMAIN_VALUES}")

        if problem_domain in ("product", "uncertain") and not product_id:
            raise ValueError(f"product_id is required when problem_domain='{problem_domain}'")

        if confidence and confidence not in self.CONFIDENCE_VALUES:
            raise ValueError(f"Invalid confidence: {confidence}. Must be one of {self.CONFIDENCE_VALUES}")

        if escalation_recommendation and escalation_recommendation not in self.ESCALATION_VALUES:
            raise ValueError(f"Invalid escalation_recommendation: {escalation_recommendation}. Must be one of {self.ESCALATION_VALUES}")

        feedback_id = self.generate_feedback_id()

        if detected_at is None:
            detected_at = datetime.now().isoformat()

        feedback = {
            "feedback_id": feedback_id,
            "problem_domain": problem_domain,
            "issue_type": issue_type,
            "detected_by": detected_by,
            "detected_in": detected_in,
            "description": description,
            "self_corrected": self_corrected,
            "requires_followup": requires_followup,
            "detected_at": detected_at,
        }

        if product_id:
            feedback["product_id"] = product_id
        if feature_id:
            feedback["feature_id"] = feature_id
        if execution_id:
            feedback["execution_id"] = execution_id
        if impact:
            feedback["impact"] = impact
        if artifact_reference:
            feedback["artifact_reference"] = artifact_reference
        if confidence:
            feedback["confidence"] = confidence
        if escalation_recommendation:
            feedback["escalation_recommendation"] = escalation_recommendation
        if triage_note:
            feedback["triage_note"] = triage_note
            feedback["triaged_at"] = detected_at
        if resolution != "none":
            feedback["resolution"] = resolution
        if resolution_note:
            feedback["resolution_note"] = resolution_note
        if status != "open":
            feedback["status"] = status
        if priority:
            feedback["priority"] = priority

        self._save_feedback_file(feedback)

        if self.use_sqlite:
            self._save_feedback_sqlite(feedback)

        return feedback

    def triage_feedback(
        self,
        feedback_id: str,
        problem_domain: str | None = None,
        confidence: str | None = None,
        escalation_recommendation: str | None = None,
        triage_note: str | None = None,
    ) -> dict[str, Any] | None:
        """Add/update triage information for a feedback item.

        Args:
            feedback_id: The feedback ID to triage
            problem_domain: Override problem_domain classification
            confidence: Set confidence level
            escalation_recommendation: Set escalation recommendation
            triage_note: Optional explanation

        Returns:
            Updated feedback record or None if not found
        """
        feedback = self.load_feedback(feedback_id)
        if not feedback:
            return None

        if problem_domain is not None:
            if problem_domain not in self.PROBLEM_DOMAIN_VALUES:
                raise ValueError(f"Invalid problem_domain: {problem_domain}")
            feedback["problem_domain"] = problem_domain

        if confidence is not None:
            if confidence not in self.CONFIDENCE_VALUES:
                raise ValueError(f"Invalid confidence: {confidence}")
            feedback["confidence"] = confidence

        if escalation_recommendation is not None:
            if escalation_recommendation not in self.ESCALATION_VALUES:
                raise ValueError(f"Invalid escalation_recommendation: {escalation_recommendation}")
            feedback["escalation_recommendation"] = escalation_recommendation

        if triage_note is not None:
            feedback["triage_note"] = triage_note

        feedback["triaged_at"] = datetime.now().isoformat()

        self._save_feedback_file(feedback)

        if self.use_sqlite:
            self._save_feedback_sqlite(feedback)

        return feedback

    def _save_feedback_file(self, feedback: dict[str, Any]) -> Path:
        """Save feedback to YAML file."""
        feedback_id = feedback["feedback_id"]
        problem_domain = feedback["problem_domain"]

        if problem_domain == "async_dev":
            target_path = self.async_dev_feedback_path
        else:
            if not self.product_feedback_path:
                raise ValueError(f"project_path required for problem_domain='{problem_domain}'")
            target_path = self.product_feedback_path

        self.fs.ensure_dir(target_path)

        file_path = target_path / f"{feedback_id}.yaml"
        yaml_content = yaml.dump(feedback, default_flow_style=False, sort_keys=False)
        self.fs.write_file(file_path, yaml_content)

        return file_path

    def _save_feedback_sqlite(self, feedback: dict[str, Any]) -> None:
        """Save feedback to SQLite table."""
        sqlite_store = self._get_sqlite_store()
        if sqlite_store:
            sqlite_store.save_workflow_feedback(feedback)

    def load_feedback(
        self, feedback_id: str, problem_domain: str | None = None, product_id: str | None = None
    ) -> dict[str, Any] | None:
        """Load a specific feedback record.

        Args:
            feedback_id: The feedback ID to load
            problem_domain: Optional domain hint ('async_dev', 'product', 'uncertain')
            product_id: Optional product ID hint

        Returns:
            The feedback record or None if not found
        """
        if self.use_sqlite and self._sqlite_store:
            feedback = self._sqlite_store.load_workflow_feedback(feedback_id)
            if feedback:
                return feedback

        return self._load_feedback_file(feedback_id, problem_domain, product_id)

    def _load_feedback_file(
        self, feedback_id: str, problem_domain: str | None = None, product_id: str | None = None
    ) -> dict[str, Any] | None:
        """Load feedback from YAML file."""
        if problem_domain == "async_dev":
            file_path = self.async_dev_feedback_path / f"{feedback_id}.yaml"
            if file_path.exists():
                return self._read_yaml_file(file_path)
        elif problem_domain in ("product", "uncertain"):
            if product_id and self.product_feedback_path:
                file_path = self.product_feedback_path / f"{feedback_id}.yaml"
                if file_path.exists():
                    return self._read_yaml_file(file_path)

        async_dev_path = self.async_dev_feedback_path / f"{feedback_id}.yaml"
        if async_dev_path.exists():
            return self._read_yaml_file(async_dev_path)

        if self.product_feedback_path:
            product_path = self.product_feedback_path / f"{feedback_id}.yaml"
            if product_path.exists():
                return self._read_yaml_file(product_path)

        return None

    def _read_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """Read YAML file and return parsed content."""
        content = self.fs.read_file(file_path)
        return yaml.safe_load(content)

    def list_feedback(
        self,
        problem_domain: str | None = None,
        product_id: str | None = None,
        issue_type: str | None = None,
        confidence: str | None = None,
        escalation_recommendation: str | None = None,
        requires_followup: bool | None = None,
        self_corrected: bool | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List workflow feedback items with optional filters.

        Args:
            problem_domain: Filter by problem_domain ('async_dev', 'product', 'uncertain')
            product_id: Filter by product ID
            issue_type: Filter by issue type
            confidence: Filter by confidence level
            escalation_recommendation: Filter by escalation
            requires_followup: Filter by requires_followup flag
            self_corrected: Filter by self_corrected flag
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of feedback records matching filters
        """
        if self.use_sqlite and self._sqlite_store:
            return self._sqlite_store.list_workflow_feedback(
                problem_domain=problem_domain,
                product_id=product_id,
                issue_type=issue_type,
                confidence=confidence,
                escalation_recommendation=escalation_recommendation,
                requires_followup=requires_followup,
                self_corrected=self_corrected,
                status=status,
                limit=limit,
            )

        return self._list_feedback_files(
            problem_domain=problem_domain,
            product_id=product_id,
            issue_type=issue_type,
            confidence=confidence,
            escalation_recommendation=escalation_recommendation,
            requires_followup=requires_followup,
            self_corrected=self_corrected,
            status=status,
            limit=limit,
        )

    def _list_feedback_files(
        self,
        problem_domain: str | None = None,
        product_id: str | None = None,
        issue_type: str | None = None,
        confidence: str | None = None,
        escalation_recommendation: str | None = None,
        requires_followup: bool | None = None,
        self_corrected: bool | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List feedback from files (fallback when SQLite unavailable)."""
        results = []

        files_to_check = []

        if problem_domain is None or problem_domain == "async_dev":
            if self.async_dev_feedback_path.exists():
                files_to_check.extend(self.async_dev_feedback_path.glob("*.yaml"))

        if problem_domain is None or problem_domain in ("product", "uncertain"):
            if self.product_feedback_path and self.product_feedback_path.exists():
                files_to_check.extend(self.product_feedback_path.glob("*.yaml"))

        for file_path in files_to_check[:limit * 2]:
            feedback = self._read_yaml_file(file_path)

            if product_id and feedback.get("product_id") != product_id:
                continue
            if problem_domain and feedback.get("problem_domain") != problem_domain:
                continue
            if issue_type and feedback.get("issue_type") != issue_type:
                continue
            if confidence and feedback.get("confidence") != confidence:
                continue
            if escalation_recommendation and feedback.get("escalation_recommendation") != escalation_recommendation:
                continue
            if requires_followup is not None and feedback.get("requires_followup") != requires_followup:
                continue
            if self_corrected is not None and feedback.get("self_corrected") != self_corrected:
                continue
            if status and feedback.get("status") != status:
                continue

            feedback["_file_path"] = str(file_path)
            results.append(feedback)

            if len(results) >= limit:
                break

        results.sort(key=lambda x: x.get("detected_at", ""), reverse=True)

        return results[:limit]

    def update_feedback(
        self,
        feedback_id: str,
        resolution: str | None = None,
        resolution_note: str | None = None,
        status: str | None = None,
        requires_followup: bool | None = None,
    ) -> dict[str, Any] | None:
        """Update feedback record (resolution/status changes).

        Args:
            feedback_id: The feedback ID to update
            resolution: New resolution status
            resolution_note: Resolution note
            status: New tracking status
            requires_followup: Updated followup flag

        Returns:
            Updated feedback record or None if not found
        """
        feedback = self.load_feedback(feedback_id)
        if not feedback:
            return None

        if resolution is not None:
            if resolution not in self.RESOLUTION_VALUES:
                raise ValueError(f"Invalid resolution: {resolution}")
            feedback["resolution"] = resolution

        if resolution_note is not None:
            feedback["resolution_note"] = resolution_note

        if status is not None:
            if status not in self.STATUS_VALUES:
                raise ValueError(f"Invalid status: {status}")
            feedback["status"] = status

        if requires_followup is not None:
            feedback["requires_followup"] = requires_followup

        self._save_feedback_file(feedback)

        if self.use_sqlite:
            self._save_feedback_sqlite(feedback)

        return feedback

    def get_feedback_for_date(
        self, date: str, product_id: str | None = None, problem_domain: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all feedback detected on a specific date.

        Args:
            date: Date string (YYYY-MM-DD)
            product_id: Optional product filter
            problem_domain: Optional domain filter

        Returns:
            List of feedback records for that date
        """
        if self.use_sqlite and self._sqlite_store:
            return self._sqlite_store.get_workflow_feedback_by_date(
                date, product_id=product_id, problem_domain=problem_domain
            )

        results = self.list_feedback(problem_domain=problem_domain, product_id=product_id, limit=200)
        return [f for f in results if f.get("detected_at", "").startswith(date)]

    def get_followup_summary(self, product_id: str | None = None) -> dict[str, Any]:
        """Get summary of feedback requiring followup.

        Args:
            product_id: Optional product filter

        Returns:
            Summary dict with counts by issue_type and domain
        """
        feedbacks = self.list_feedback(
            product_id=product_id,
            requires_followup=True,
            limit=100,
        )

        by_type = {}
        by_domain = {}
        by_escalation = {}
        for fb in feedbacks:
            issue_type = fb.get("issue_type", "other")
            by_type[issue_type] = by_type.get(issue_type, 0) + 1

            domain = fb.get("problem_domain", "uncertain")
            by_domain[domain] = by_domain.get(domain, 0) + 1

            escalation = fb.get("escalation_recommendation", "track_only")
            by_escalation[escalation] = by_escalation.get(escalation, 0) + 1

        return {
            "total_followup_needed": len(feedbacks),
            "by_issue_type": by_type,
            "by_problem_domain": by_domain,
            "by_escalation": by_escalation,
            "self_corrected_count": sum(1 for fb in feedbacks if fb.get("self_corrected")),
            "open_count": sum(1 for fb in feedbacks if fb.get("status", "open") == "open"),
            "candidate_issue_count": sum(1 for fb in feedbacks if fb.get("escalation_recommendation") == "candidate_issue"),
        }

    def close(self) -> None:
        """Close SQLite connection if open."""
        if self._sqlite_store:
            self._sqlite_store.close()


def create_workflow_feedback_for_review(
    feedbacks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create workflow_feedback section for DailyReviewPack with triage info.

    Args:
        feedbacks: List of feedback records for the day

    Returns:
        Structured workflow_feedback section with triage info
    """
    if not feedbacks:
        return {
            "encountered_today": 0,
            "items": [],
            "followup_needed_count": 0,
            "self_corrected_count": 0,
            "async_dev_count": 0,
            "product_count": 0,
            "uncertain_count": 0,
            "candidate_issue_count": 0,
        }

    items = []
    for fb in feedbacks:
        items.append({
            "feedback_id": fb.get("feedback_id"),
            "problem_domain": fb.get("problem_domain"),
            "issue_type": fb.get("issue_type"),
            "confidence": fb.get("confidence"),
            "escalation_recommendation": fb.get("escalation_recommendation"),
            "self_corrected": fb.get("self_corrected", False),
            "requires_followup": fb.get("requires_followup", False),
            "summary": fb.get("description", "")[:100],
            "triaged": fb.get("triaged_at") is not None,
            "status": fb.get("status", "open"),
        })

    return {
        "encountered_today": len(feedbacks),
        "items": items,
        "followup_needed_count": sum(1 for fb in feedbacks if fb.get("requires_followup")),
        "self_corrected_count": sum(1 for fb in feedbacks if fb.get("self_corrected")),
        "async_dev_count": sum(1 for fb in feedbacks if fb.get("problem_domain") == "async_dev"),
        "product_count": sum(1 for fb in feedbacks if fb.get("problem_domain") == "product"),
        "uncertain_count": sum(1 for fb in feedbacks if fb.get("problem_domain") == "uncertain"),
        "candidate_issue_count": sum(1 for fb in feedbacks if fb.get("escalation_recommendation") == "candidate_issue"),
        "review_needed_count": sum(1 for fb in feedbacks if fb.get("escalation_recommendation") == "review_needed"),
    }