"""Tests for Feature 051 - Summary Digest Modes."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from runtime.summary_digest import (
    DigestMode,
    DigestConfig,
    DigestEntry,
    DigestReport,
    get_digest_config,
    should_send_digest,
    build_daily_digest,
    build_weekly_digest,
    build_milestone_digest,
    format_digest_for_email,
    format_digest_subject,
)


class TestDigestMode:
    def test_digest_modes_defined(self):
        assert DigestMode.DAILY.value == "daily"
        assert DigestMode.WEEKLY.value == "weekly"
        assert DigestMode.MILESTONE.value == "milestone"
        assert DigestMode.QUIET.value == "quiet"


class TestDigestConfig:
    def test_default_config(self):
        config = DigestConfig()
        assert config.mode == DigestMode.DAILY
        assert config.enabled is True
        assert config.send_time == "18:00"

    def test_custom_config(self):
        config = DigestConfig(
            mode=DigestMode.WEEKLY,
            enabled=False,
            send_time="09:00",
            quiet_days=["saturday", "sunday"],
        )
        assert config.mode == DigestMode.WEEKLY
        assert config.enabled is False
        assert config.send_time == "09:00"
        assert len(config.quiet_days) == 2


class TestShouldSendDigest:
    def test_disabled_config_never_sends(self):
        config = DigestConfig(enabled=False)
        assert should_send_digest(config, 10) is False

    def test_daily_mode_always_sends(self):
        config = DigestConfig(mode=DigestMode.DAILY)
        assert should_send_digest(config, 1) is True

    def test_quiet_mode_threshold(self):
        config = DigestConfig(mode=DigestMode.QUIET, batch_threshold=5)
        assert should_send_digest(config, 3) is False
        assert should_send_digest(config, 5) is True

    def test_weekly_mode_sends(self):
        config = DigestConfig(mode=DigestMode.WEEKLY)
        assert should_send_digest(config, 1) is True


class TestDigestEntry:
    def test_entry_creation(self):
        entry = DigestEntry(
            report_id="sr-001",
            report_type="progress",
            summary="Test summary",
            timestamp="2026-04-19T10:00:00",
        )
        assert entry.report_id == "sr-001"
        assert entry.report_type == "progress"


class TestDigestReport:
    def test_report_creation(self):
        report = DigestReport(
            digest_id="digest-001",
            digest_mode=DigestMode.DAILY,
            period_start="2026-04-19",
            period_end="2026-04-19",
            entries=[],
            total_reports=0,
            highlights=["Test"],
            blockers_resolved=0,
            milestones_completed=0,
        )
        assert report.digest_id == "digest-001"
        assert report.total_reports == 0


class TestGetDigestConfig:
    def test_no_config_file_returns_default(self, tmp_path):
        config = get_digest_config(tmp_path)
        assert config.mode == DigestMode.DAILY
        assert config.enabled is True

    def test_load_config_from_file(self, tmp_path):
        runtime_dir = tmp_path / ".runtime"
        runtime_dir.mkdir()

        config_data = {
            "mode": "weekly",
            "enabled": True,
            "send_time": "09:00",
            "batch_threshold": 5,
        }

        config_file = runtime_dir / "digest-config.yaml"
        import yaml
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = get_digest_config(tmp_path)
        assert config.mode == DigestMode.WEEKLY
        assert config.send_time == "09:00"


class TestBuildDailyDigest:
    def test_empty_digest(self, tmp_path):
        digest = build_daily_digest(tmp_path, "test-project")
        assert digest.digest_mode == DigestMode.DAILY
        assert digest.total_reports == 0

    def test_digest_id_format(self, tmp_path):
        digest = build_daily_digest(tmp_path, "test-project")
        assert "digest-" in digest.digest_id


class TestBuildWeeklyDigest:
    def test_weekly_digest_structure(self, tmp_path):
        digest = build_weekly_digest(tmp_path, "test-project")
        assert digest.digest_mode == DigestMode.WEEKLY
        assert "weekly" in digest.digest_id


class TestBuildMilestoneDigest:
    def test_milestone_digest(self, tmp_path):
        milestone_reports = [
            {"report_id": "sr-001", "report_type": "milestone", "summary": "Phase 1 complete"},
        ]
        digest = build_milestone_digest(tmp_path, "test-project", "Phase 1", milestone_reports)
        assert digest.digest_mode == DigestMode.MILESTONE
        assert digest.milestones_completed == 1


class TestFormatDigestForEmail:
    def test_daily_digest_format(self):
        digest = DigestReport(
            digest_id="digest-001",
            digest_mode=DigestMode.DAILY,
            period_start="2026-04-19",
            period_end="2026-04-19",
            entries=[],
            total_reports=5,
            highlights=["Milestone completed"],
            blockers_resolved=2,
            milestones_completed=1,
        )
        body = format_digest_for_email(digest)
        assert "Daily Summary" in body
        assert "5" in body
        assert "Milestone" in body

    def test_weekly_digest_format(self):
        digest = DigestReport(
            digest_id="digest-weekly",
            digest_mode=DigestMode.WEEKLY,
            period_start="2026-04-12",
            period_end="2026-04-19",
            entries=[],
            total_reports=20,
            highlights=[],
            blockers_resolved=5,
            milestones_completed=2,
        )
        body = format_digest_for_email(digest)
        assert "Weekly Digest" in body


class TestFormatDigestSubject:
    def test_daily_subject(self):
        digest = DigestReport(
            digest_id="digest-001",
            digest_mode=DigestMode.DAILY,
            period_start="",
            period_end="",
            entries=[],
            total_reports=0,
            highlights=[],
            blockers_resolved=0,
            milestones_completed=0,
        )
        subject = format_digest_subject(digest, "my-project")
        assert "Daily" in subject
        assert "my-project" in subject

    def test_weekly_subject(self):
        digest = DigestReport(
            digest_id="digest-weekly",
            digest_mode=DigestMode.WEEKLY,
            period_start="",
            period_end="",
            entries=[],
            total_reports=0,
            highlights=[],
            blockers_resolved=0,
            milestones_completed=0,
        )
        subject = format_digest_subject(digest, "my-project")
        assert "Weekly" in subject