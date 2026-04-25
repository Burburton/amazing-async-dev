"""Tests for Operator Home Adapter - Minimal Platform Overview."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from runtime.operator_home_adapter import (
    ActiveRunItem,
    AttentionItem,
    AcceptanceQueueItem,
    ObserverHighlight,
    QuickLink,
    OperatorHomeOverview,
    build_operator_home_overview,
)
from runtime.state_store import StateStore


class TestOperatorHomeOverview:
    def test_overview_creation(self):
        overview = OperatorHomeOverview(
            total_projects=3,
            healthy_count=2,
            blocked_count=1,
        )
        
        assert overview.total_projects == 3
        assert overview.healthy_count == 2
        assert overview.blocked_count == 1
    
    def test_overview_to_dict(self):
        overview = OperatorHomeOverview(
            total_projects=5,
            attention_items=[AttentionItem(
                category="recovery",
                title="test",
                severity="high",
                reason="blocked",
                suggested_action="fix",
                destination="recovery",
            )],
        )
        
        data = overview.to_dict()
        
        assert data["total_projects"] == 5
        assert len(data["attention_items"]) == 1
    
    def test_is_calm(self):
        calm = OperatorHomeOverview(attention_items=[], blocked_items=[], blocked_count=0)
        active = OperatorHomeOverview(
            attention_items=[AttentionItem(
                category="recovery",
                title="test",
                severity="high",
                reason="blocked",
                suggested_action="fix",
                destination="recovery",
            )],
            blocked_count=1,
        )
        
        assert calm.is_calm() is True
        assert active.is_calm() is False
    
    def test_has_critical(self):
        critical = OperatorHomeOverview(
            attention_items=[AttentionItem(
                category="recovery",
                title="test",
                severity="critical",
                reason="blocked",
                suggested_action="fix",
                destination="recovery",
            )],
        )
        normal = OperatorHomeOverview(
            attention_items=[AttentionItem(
                category="recovery",
                title="test",
                severity="high",
                reason="blocked",
                suggested_action="fix",
                destination="recovery",
            )],
        )
        
        assert critical.has_critical() is True
        assert normal.has_critical() is False


class TestActiveRunItem:
    def test_item_creation(self):
        item = ActiveRunItem(
            project_id="test-project",
            feature_id="001-test",
            status="active",
            phase="executing",
            last_updated="2026-04-25T10:00",
            health_summary="healthy",
            detail_path="asyncdev evidence summary",
        )
        
        assert item.project_id == "test-project"
        assert item.health_summary == "healthy"
    
    def test_item_to_dict(self):
        item = ActiveRunItem(
            project_id="test",
            feature_id="001",
            status="active",
            phase="planning",
            last_updated="",
            health_summary="healthy",
            detail_path="cmd",
        )
        
        data = item.to_dict()
        
        assert data["project_id"] == "test"
        assert data["phase"] == "planning"


class TestAttentionItem:
    def test_item_creation(self):
        item = AttentionItem(
            category="recovery",
            title="blocked-feature",
            severity="high",
            reason="acceptance failed",
            suggested_action="asyncdev recovery list",
            destination="recovery show",
        )
        
        assert item.category == "recovery"
        assert item.severity == "high"


class TestAcceptanceQueueItem:
    def test_item_creation(self):
        item = AcceptanceQueueItem(
            project_id="test",
            feature_id="001",
            acceptance_status="rejected",
            terminal_state="rejected",
            completion_blocked=True,
            attempt_count=2,
            destination="acceptance status",
        )
        
        assert item.completion_blocked is True
        assert item.attempt_count == 2


class TestObserverHighlight:
    def test_highlight_creation(self):
        item = ObserverHighlight(
            finding_type="blocked_state",
            severity="high",
            summary="Execution blocked",
            recommended_action="resolve blocker",
            project_id="test",
            destination="observer",
        )
        
        assert item.finding_type == "blocked_state"
        assert item.severity == "high"


class TestQuickLink:
    def test_link_creation(self):
        link = QuickLink(
            label="Recovery Console",
            command="asyncdev recovery list",
            description="View executions needing recovery",
        )
        
        assert link.label == "Recovery Console"
        assert link.command == "asyncdev recovery list"


class TestBuildOperatorHomeOverview:
    def test_empty_projects_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_path = Path(tmpdir) / "projects"
            projects_path.mkdir()
            
            overview = build_operator_home_overview(projects_path)
            
            assert overview.total_projects == 0
            assert overview.is_calm() is True
    
    def test_single_project_no_runstate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_path = Path(tmpdir) / "projects"
            project_dir = projects_path / "test-project"
            project_dir.mkdir(parents=True)
            
            overview = build_operator_home_overview(projects_path)
            
            assert overview.total_projects == 1
            assert len(overview.active_runs) == 0
    
    def test_single_project_with_runstate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_path = Path(tmpdir) / "projects"
            project_dir = projects_path / "test-project"
            project_dir.mkdir(parents=True)
            
            store = StateStore(project_dir)
            store.save_runstate({
                "project_id": "test-project",
                "feature_id": "001-test",
                "current_phase": "executing",
                "updated_at": datetime.now().isoformat(),
            })
            
            overview = build_operator_home_overview(projects_path)
            
            assert overview.total_projects == 1
            assert len(overview.active_runs) == 1
            assert overview.active_runs[0].feature_id == "001-test"
    
    def test_quick_links_populated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_path = Path(tmpdir) / "projects"
            projects_path.mkdir()
            
            overview = build_operator_home_overview(projects_path)
            
            assert len(overview.quick_links) == 5
            assert overview.quick_links[0].label == "Recovery Console"


class TestHomeIntegration:
    def test_aggregates_from_multiple_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_path = Path(tmpdir) / "projects"
            
            for i in range(3):
                project_dir = projects_path / f"project-{i}"
                project_dir.mkdir(parents=True)
                
                store = StateStore(project_dir)
                store.save_runstate({
                    "project_id": f"project-{i}",
                    "feature_id": f"feature-{i}",
                    "current_phase": "planning",
                    "updated_at": datetime.now().isoformat(),
                })
            
            overview = build_operator_home_overview(projects_path)
            
            assert overview.total_projects == 3
            assert len(overview.active_runs) == 3