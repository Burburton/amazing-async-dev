# tests/test_workspace_doctor.py

"""Tests for workspace doctor functionality (Feature 029)."""

import pytest
from runtime.workspace_doctor import DoctorDiagnosis


class TestDoctorDiagnosisDataclass:
    def test_default_values(self):
        """DoctorDiagnosis should have sensible defaults."""
        diagnosis = DoctorDiagnosis()
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.health_status == "unknown"
        assert diagnosis.initialization_mode == "unknown"
        assert diagnosis.provider_linkage == {}
        assert diagnosis.product_id == ""
        assert diagnosis.feature_id == ""
        assert diagnosis.current_phase == ""
        assert diagnosis.verification_status == "not_run"
        assert diagnosis.pending_decisions == 0
        assert diagnosis.blocked_items_count == 0
        assert diagnosis.recommended_action == ""
        assert diagnosis.suggested_command == ""
        assert diagnosis.rationale == ""
        assert diagnosis.warnings == []
        assert diagnosis.workspace_path == ""

    def test_custom_values(self):
        """DoctorDiagnosis should accept custom values."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            health_status="healthy",
            product_id="my-app",
            feature_id="feature-001",
            current_phase="planning",
            recommended_action="Plan a task",
            suggested_command="asyncdev plan-day create",
            rationale="Workspace is in planning phase"
        )
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.product_id == "my-app"
        assert diagnosis.recommended_action == "Plan a task"