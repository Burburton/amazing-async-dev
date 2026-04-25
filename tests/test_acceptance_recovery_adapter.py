"""Tests for Feature 078 - Acceptance Recovery Console Integration."""

import tempfile
from pathlib import Path

import pytest

from runtime.acceptance_recovery_adapter import (
    AcceptanceRecoveryAdapter,
    AcceptanceRecoverySummary,
    AcceptanceRecoveryCategory,
    get_acceptance_recovery_for_project,
    is_acceptance_recovery_significant,
)
from runtime.recovery_data_adapter import (
    RecoveryDataAdapter,
    RecoveryItem,
)
from runtime.recovery_classifier import RecoveryClassification


class TestAcceptanceRecoverySummary:
    """Tests for AcceptanceRecoverySummary dataclass."""

    def test_summary_creation(self):
        summary = AcceptanceRecoverySummary(
            latest_status="rejected",
            attempt_count=2,
            latest_terminal_state="rejected",
            latest_failed_criteria=["AC-001", "AC-002"],
            is_blocking_completion=True,
        )
        
        assert summary.latest_status == "rejected"
        assert summary.attempt_count == 2
        assert summary.is_blocking_completion is True
        assert len(summary.latest_failed_criteria) == 2

    def test_summary_to_dict(self):
        summary = AcceptanceRecoverySummary(
            latest_status="rejected",
            attempt_count=1,
            latest_terminal_state="rejected",
        )
        
        data = summary.to_dict()
        
        assert data["latest_status"] == "rejected"
        assert data["attempt_count"] == 1
        assert data["latest_terminal_state"] == "rejected"


class TestAcceptanceRecoveryAdapter:
    """Tests for AcceptanceRecoveryAdapter."""

    @pytest.fixture
    def project_with_acceptance_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            acceptance_results_dir = project_path / "acceptance-results"
            acceptance_results_dir.mkdir()
            
            result_path = acceptance_results_dir / "ar-001.md"
            result_path.write_text("""# AcceptanceResult

```yaml
acceptance_result_id: ar-001
acceptance_pack_id: ap-001
terminal_state: rejected
attempt_number: 1
accepted_criteria: []
failed_criteria:
  - AC-001: Feature works correctly
  - AC-002: Tests pass
conditional_criteria: []
remediation_guidance:
  - criterion_id: AC-001
    issue_type: evidence_missing
    suggested_fix: Provide evidence for AC-001
    priority: high
  - criterion_id: AC-002
    issue_type: evidence_missing
    suggested_fix: Provide evidence for AC-002
    priority: high
validated_at: '2026-04-25T12:00:00'
```
""")
            
            acceptance_packs_dir = project_path / "acceptance-packs"
            acceptance_packs_dir.mkdir()
            
            pack_path = acceptance_packs_dir / "ap-001.md"
            pack_path.write_text("""# AcceptancePack

```yaml
acceptance_pack_id: ap-001
feature_id: feat-001
execution_result_id: exec-001
product_id: proj-001
acceptance_criteria:
  - criterion_id: AC-001
    text: Feature works correctly
  - criterion_id: AC-002
    text: Tests pass
verification_summary:
  orchestration_terminal_state: success
  closeout_terminal_state: success
```
""")
            
            docs_features_dir = project_path / "docs" / "features" / "feat-001"
            docs_features_dir.mkdir(parents=True)
            
            spec_path = docs_features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-001
acceptance_criteria:
  - criterion_id: AC-001
    text: Feature works correctly
  - criterion_id: AC-002
    text: Tests pass
```
""")
            
            runstate_dir = project_path / "state"
            runstate_dir.mkdir()
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "project_id": "proj-001",
                "feature_id": "feat-001",
                "current_phase": "blocked",
                "acceptance_terminal_state": "rejected",
                "acceptance_recovery_pending": True,
                "acceptance_recovery_pack_id": "arp-001",
            })
            
            yield project_path

    def test_get_acceptance_recovery_summary(self, project_with_acceptance_failure):
        adapter = AcceptanceRecoveryAdapter(project_with_acceptance_failure)
        summary = adapter.get_acceptance_recovery_summary("feat-001")
        
        assert summary is not None
        assert summary.latest_status != "no_acceptance"
        assert summary.latest_terminal_state == "rejected"

    def test_recovery_significant_for_rejected(self, project_with_acceptance_failure):
        adapter = AcceptanceRecoveryAdapter(project_with_acceptance_failure)
        summary = adapter.get_acceptance_recovery_summary("feat-001")
        
        assert summary.recovery_significant is True
        assert summary.recovery_category != ""

    def test_needs_reacceptance_for_rejected(self, project_with_acceptance_failure):
        adapter = AcceptanceRecoveryAdapter(project_with_acceptance_failure)
        summary = adapter.get_acceptance_recovery_summary("feat-001")
        
        assert summary.needs_reacceptance is True
        assert summary.reacceptance_required_reason != ""

    def test_failed_criteria_extracted(self, project_with_acceptance_failure):
        adapter = AcceptanceRecoveryAdapter(project_with_acceptance_failure)
        summary = adapter.get_acceptance_recovery_summary("feat-001")
        
        assert len(summary.latest_failed_criteria) >= 1

    def test_remediation_summary_extracted(self, project_with_acceptance_failure):
        adapter = AcceptanceRecoveryAdapter(project_with_acceptance_failure)
        summary = adapter.get_acceptance_recovery_summary("feat-001")
        
        assert len(summary.latest_remediation_summary) >= 1


class TestRecoveryDataAdapterAcceptanceIntegration:
    """Tests for RecoveryDataAdapter with acceptance recovery."""

    @pytest.fixture
    def project_with_awaiting_acceptance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            acceptance_results_dir = project_path / "acceptance-results"
            acceptance_results_dir.mkdir()
            
            result_path = acceptance_results_dir / "ar-002.md"
            result_path.write_text("""# AcceptanceResult

```yaml
acceptance_result_id: ar-002
acceptance_pack_id: ap-002
terminal_state: rejected
attempt_number: 1
failed_criteria:
  - AC-001
```
""")
            
            acceptance_packs_dir = project_path / "acceptance-packs"
            acceptance_packs_dir.mkdir()
            
            pack_path = acceptance_packs_dir / "ap-002.md"
            pack_path.write_text("""# AcceptancePack

```yaml
acceptance_pack_id: ap-002
feature_id: feat-002
execution_result_id: exec-002
product_id: proj-002
verification_summary:
  orchestration_terminal_state: success
  closeout_terminal_state: success
```
""")
            
            docs_features_dir = project_path / "docs" / "features" / "feat-002"
            docs_features_dir.mkdir(parents=True)
            
            spec_path = docs_features_dir / "feature-spec.md"
            spec_path.write_text("""# FeatureSpec

```yaml
feature_id: feat-002
acceptance_criteria:
  - AC-001
```
""")
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "project_id": "proj-002",
                "feature_id": "feat-002",
                "current_phase": "blocked",
                "acceptance_terminal_state": "rejected",
                "acceptance_recovery_pending": True,
                "blocked_items": [],
                "decisions_needed": [],
            })
            
            yield project_path

    def test_awaiting_acceptance_classification_included(self, project_with_awaiting_acceptance):
        adapter = RecoveryDataAdapter(project_with_awaiting_acceptance)
        item = adapter.get_recovery_item()
        
        assert item is not None
        assert item.status == "awaiting_acceptance"

    def test_acceptance_recovery_summary_populated(self, project_with_awaiting_acceptance):
        adapter = RecoveryDataAdapter(project_with_awaiting_acceptance)
        item = adapter.get_recovery_item()
        
        assert item.acceptance_recovery_summary is not None

    def test_acceptance_fields_populated(self, project_with_awaiting_acceptance):
        adapter = RecoveryDataAdapter(project_with_awaiting_acceptance)
        item = adapter.get_recovery_item()
        
        assert item.acceptance_status != ""
        assert item.acceptance_blocking is True or item.reacceptance_required is True


class TestAcceptanceRecoveryCategories:
    """Tests for acceptance recovery categories."""

    def test_all_categories_defined(self):
        assert AcceptanceRecoveryCategory.ACCEPTANCE_FAILED == "acceptance_failed"
        assert AcceptanceRecoveryCategory.AWAITING_ACCEPTANCE == "awaiting_acceptance"
        assert AcceptanceRecoveryCategory.REACCEPTANCE_REQUIRED == "reacceptance_required"

    def test_category_count(self):
        categories = [
            AcceptanceRecoveryCategory.ACCEPTANCE_FAILED,
            AcceptanceRecoveryCategory.ACCEPTANCE_BLOCKED,
            AcceptanceRecoveryCategory.AWAITING_ACCEPTANCE,
            AcceptanceRecoveryCategory.REACCEPTANCE_REQUIRED,
            AcceptanceRecoveryCategory.ACCEPTANCE_ESCALATION_NEEDED,
            AcceptanceRecoveryCategory.CONDITIONAL_ACCEPTANCE,
        ]
        assert len(categories) == 6


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "project_id": "proj-empty",
                "feature_id": "feat-empty",
                "current_phase": "planning",
            })
            
            yield project_path

    def test_get_acceptance_recovery_for_project_no_acceptance(self, empty_project):
        summary = get_acceptance_recovery_for_project(empty_project, "feat-empty")
        
        assert summary is None

    def test_is_acceptance_recovery_significant_empty(self, empty_project):
        significant = is_acceptance_recovery_significant(empty_project, "feat-empty")
        
        assert significant is False