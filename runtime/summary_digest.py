"""Summary digest modes for Feature 051 - Periodic report aggregation."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class DigestMode(str, Enum):
    """Digest aggregation modes."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MILESTONE = "milestone"
    QUIET = "quiet"


@dataclass
class DigestConfig:
    """Configuration for digest mode."""
    mode: DigestMode = DigestMode.DAILY
    enabled: bool = True
    send_time: str = "18:00"
    quiet_days: list[str] = field(default_factory=list)
    batch_threshold: int = 3


@dataclass
class DigestEntry:
    """Single entry in digest."""
    report_id: str
    report_type: str
    summary: str
    timestamp: str
    score: int = 0


@dataclass
class DigestReport:
    """Aggregated digest report."""
    digest_id: str
    digest_mode: DigestMode
    period_start: str
    period_end: str
    entries: list[DigestEntry]
    total_reports: int
    highlights: list[str]
    blockers_resolved: int
    milestones_completed: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


def get_digest_config(project_path: Path) -> DigestConfig:
    """Load digest configuration from project.

    Args:
        project_path: Project directory path

    Returns:
        DigestConfig with settings
    """
    config_path = project_path / ".runtime" / "digest-config.yaml"

    if not config_path.exists():
        return DigestConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    mode_str = data.get("mode", "daily")
    try:
        mode = DigestMode(mode_str)
    except ValueError:
        mode = DigestMode.DAILY

    return DigestConfig(
        mode=mode,
        enabled=data.get("enabled", True),
        send_time=data.get("send_time", "18:00"),
        quiet_days=data.get("quiet_days", []),
        batch_threshold=data.get("batch_threshold", 3),
    )


def should_send_digest(config: DigestConfig, reports_count: int) -> bool:
    """Determine if digest should be sent based on config.

    Args:
        config: Digest configuration
        reports_count: Number of reports in period

    Returns:
        True if digest should be sent
    """
    if not config.enabled:
        return False

    if config.mode == DigestMode.QUIET:
        return reports_count >= config.batch_threshold

    return True


def collect_reports_for_digest(
    project_path: Path,
    period_start: datetime,
    period_end: datetime,
) -> list[DigestEntry]:
    """Collect status reports for digest period.

    Args:
        project_path: Project directory
        period_start: Start of period
        period_end: End of period

    Returns:
        List of DigestEntry objects
    """
    reports_dir = project_path / ".runtime" / "email-outbox"
    entries = []

    if not reports_dir.exists():
        return entries

    for report_file in reports_dir.glob("sr-*.md"):
        try:
            with open(report_file, encoding="utf-8") as f:
                content = f.read()

            timestamp_str = report_file.stem.split("-")[1:3]
            if len(timestamp_str) >= 2:
                date_str = f"{timestamp_str[0]}-{timestamp_str[1]}"
                report_date = datetime.strptime(date_str, "%Y%m%d")

                if period_start <= report_date <= period_end:
                    report_id = report_file.stem
                    report_type = "progress"
                    summary = content.split("\n")[0][:80] if content else ""

                    entries.append(DigestEntry(
                        report_id=report_id,
                        report_type=report_type,
                        summary=summary,
                        timestamp=report_date.isoformat(),
                    ))
        except Exception:
            continue

    return entries


def build_daily_digest(
    project_path: Path,
    project_id: str,
) -> DigestReport:
    """Build daily digest report.

    Args:
        project_path: Project directory
        project_id: Project identifier

    Returns:
        DigestReport for daily period
    """
    now = datetime.now()
    period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = now

    entries = collect_reports_for_digest(project_path, period_start, period_end)

    digest_id = f"digest-{now.strftime('%Y%m%d')}-{len(entries):03d}"

    highlights = []
    for entry in entries:
        if "milestone" in entry.summary.lower() or "complete" in entry.summary.lower():
            highlights.append(entry.summary)

    blockers_resolved = sum(1 for e in entries if "resolved" in e.summary.lower())
    milestones_completed = sum(1 for e in entries if "milestone" in e.summary.lower())

    return DigestReport(
        digest_id=digest_id,
        digest_mode=DigestMode.DAILY,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        entries=entries,
        total_reports=len(entries),
        highlights=highlights[:5],
        blockers_resolved=blockers_resolved,
        milestones_completed=milestones_completed,
    )


def build_weekly_digest(
    project_path: Path,
    project_id: str,
) -> DigestReport:
    """Build weekly digest report.

    Args:
        project_path: Project directory
        project_id: Project identifier

    Returns:
        DigestReport for weekly period
    """
    now = datetime.now()
    period_end = now
    period_start = now - timedelta(days=7)

    entries = collect_reports_for_digest(project_path, period_start, period_end)

    digest_id = f"digest-weekly-{now.strftime('%Y%m%d')}"

    highlights = []
    blockers = []
    for entry in entries:
        if "milestone" in entry.summary.lower():
            highlights.append(f"✓ {entry.summary}")
        if "blocker" in entry.summary.lower():
            blockers.append(entry.summary)

    blockers_resolved = sum(1 for e in entries if "resolved" in e.summary.lower())
    milestones_completed = sum(1 for e in entries if "milestone" in e.summary.lower())

    return DigestReport(
        digest_id=digest_id,
        digest_mode=DigestMode.WEEKLY,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        entries=entries[:10],
        total_reports=len(entries),
        highlights=highlights + blockers[:5],
        blockers_resolved=blockers_resolved,
        milestones_completed=milestones_completed,
    )


def build_milestone_digest(
    project_path: Path,
    project_id: str,
    milestone_name: str,
    milestone_reports: list[dict[str, Any]],
) -> DigestReport:
    """Build milestone summary digest.

    Args:
        project_path: Project directory
        project_id: Project identifier
        milestone_name: Milestone name
        milestone_reports: Reports for this milestone

    Returns:
        DigestReport for milestone
    """
    now = datetime.now()
    digest_id = f"digest-milestone-{milestone_name[:20].replace(' ', '-')}"

    entries = []
    for report in milestone_reports:
        entries.append(DigestEntry(
            report_id=report.get("report_id", "unknown"),
            report_type=report.get("report_type", "progress"),
            summary=report.get("summary", ""),
            timestamp=report.get("created_at", now.isoformat()),
        ))

    highlights = [f"Milestone: {milestone_name} completed"]

    return DigestReport(
        digest_id=digest_id,
        digest_mode=DigestMode.MILESTONE,
        period_start=entries[0].timestamp if entries else now.isoformat(),
        period_end=now.isoformat(),
        entries=entries,
        total_reports=len(entries),
        highlights=highlights,
        blockers_resolved=0,
        milestones_completed=1,
    )


def format_digest_for_email(digest: DigestReport) -> str:
    """Format digest report for email body.

    Args:
        digest: DigestReport to format

    Returns:
        Email body text
    """
    lines = []

    mode_labels = {
        DigestMode.DAILY: "Daily Summary",
        DigestMode.WEEKLY: "Weekly Digest",
        DigestMode.MILESTONE: "Milestone Summary",
        DigestMode.QUIET: "Quiet Mode Digest",
    }

    lines.append(f"## {mode_labels.get(digest.digest_mode, 'Digest')}")
    lines.append("")
    lines.append(f"**Period:** {digest.period_start[:10]} to {digest.period_end[:10]}")
    lines.append(f"**Reports:** {digest.total_reports}")
    lines.append("")

    if digest.highlights:
        lines.append("**Highlights:**")
        for h in digest.highlights[:5]:
            lines.append(f"  {h}")
        lines.append("")

    if digest.milestones_completed > 0:
        lines.append(f"**Milestones:** {digest.milestones_completed} completed")

    if digest.blockers_resolved > 0:
        lines.append(f"**Blockers Resolved:** {digest.blockers_resolved}")

    lines.append("")

    if digest.entries:
        lines.append("**Recent Reports:**")
        for entry in digest.entries[:5]:
            lines.append(f"  • [{entry.timestamp[:10]}] {entry.summary[:60]}")

    lines.append("")
    lines.append("---")
    lines.append(f"Digest: {digest.digest_id}")

    return "\n".join(lines)


def format_digest_subject(digest: DigestReport, project_id: str) -> str:
    """Format email subject for digest.

    Args:
        digest: DigestReport
        project_id: Project identifier

    Returns:
        Email subject string
    """
    mode_labels = {
        DigestMode.DAILY: "Daily",
        DigestMode.WEEKLY: "Weekly",
        DigestMode.MILESTONE: "Milestone",
        DigestMode.QUIET: "Digest",
    }

    mode_label = mode_labels.get(digest.digest_mode, "Digest")

    return f"[async-dev] {mode_label} Digest: {project_id} [{digest.digest_id}]"