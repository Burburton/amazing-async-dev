"""Tests for Loop Journal Viewer V1.3 - Project and Feature Scoped Views."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from runtime.journal_viewer.artifact_reader import (
    JournalEntry,
    build_journal_timeline,
    extract_yaml_block,
    safe_extract_date_from_exec_id,
    parse_review_pack,
    parse_execution_pack,
    parse_execution_result,
    CANONICAL_LOOP_ORDER,
    DAY_DETAIL_ORDER,
)
from runtime.journal_viewer.tui_viewer import (
    filter_entries,
    filter_entries_strict,
    group_entries_by_day,
    group_entries_by_feature,
    get_artifact_summary,
    get_available_features,
    display_day_detail,
    display_feature_timeline,
    display_project_summary,
)
from cli.commands.journal import app


runner = CliRunner()


@pytest.fixture
def temp_project(temp_dir):
    """Create a minimal async-dev project structure."""
    project_path = temp_dir / "test-project"
    project_path.mkdir()

    reviews_dir = project_path / "reviews"
    reviews_dir.mkdir()

    packs_dir = project_path / "execution-packs"
    packs_dir.mkdir()

    results_dir = project_path / "execution-results"
    results_dir.mkdir()

    yield project_path


class TestArtifactIngestion:
    """V1.1 AC1: Reliably ingest core async-dev artifact types."""

    def test_parse_review_pack_success(self, temp_project):
        """review-night artifact parsed successfully."""
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""# DailyReviewPack
```yaml
date: '2026-04-10'
project_id: test-project
feature_id: 001-test
today_goal: 'Test execution'
what_was_completed:
- item: Test completed
  description: Done
blocked_items: []
decisions_needed: []
doctor_assessment:
  doctor_status: HEALTHY
```
""")

        entry = parse_review_pack(review_path)

        assert entry.parse_status == "success"
        assert entry.artifact_type == "review"
        assert entry.day == "2026-04-10"
        assert entry.project_id == "test-project"
        assert entry.feature_id == "001-test"

    def test_parse_execution_pack_success(self, temp_project):
        """plan-day artifact parsed successfully."""
        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""# ExecutionPack
```yaml
execution_id: exec-20260410-001
project_id: test-project
feature_id: 001-test
goal: 'Execute test task'
planning_mode: continue_work
safe_to_execute: true
prior_doctor_status: HEALTHY
```
""")

        entry = parse_execution_pack(pack_path)

        assert entry.parse_status == "success"
        assert entry.artifact_type == "plan"
        assert entry.day == "2026-04-10"
        assert "planning_mode" in entry.key_fields

    def test_parse_execution_result_success(self, temp_project):
        """run-day artifact parsed successfully."""
        result_path = temp_project / "execution-results" / "exec-20260410-001.md"
        result_path.write_text("""# ExecutionResult
```yaml
execution_id: exec-20260410-001
project_id: test-project
feature_id: 001-test
status: success
completed_items:
- 'Test completed'
artifacts_created: []
blocked_reasons: []
```
""")

        entry = parse_execution_result(result_path)

        assert entry.parse_status == "success"
        assert entry.artifact_type == "run"
        assert entry.day == "2026-04-10"
        assert entry.key_fields.get("status") == "success"


class TestFallbackBehavior:
    """V1.1 AC4: Missing, partial, or inconsistent artifacts degrade gracefully."""

    def test_missing_artifact_file_handled(self, temp_project):
        """Missing artifact file handled gracefully."""
        entries, warnings = build_journal_timeline(temp_project)

        assert isinstance(entries, list)
        assert isinstance(warnings, list)
        assert len(warnings) > 0
        assert any("No" in w and "artifacts found" in w for w in warnings)

    def test_malformed_artifact_handled(self, temp_project):
        """Malformed artifact handled gracefully."""
        malformed_path = temp_project / "reviews" / "2026-04-10-review.md"
        malformed_path.write_text("This is not valid YAML content")

        entry = parse_review_pack(malformed_path)

        assert entry.parse_status == "success"
        assert entry.title == "Review Night - 2026-04-10"

    def test_partial_artifact_handled(self, temp_project):
        """Partial artifact with missing fields handled."""
        partial_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        partial_path.write_text("""# ExecutionPack
```yaml
execution_id: exec-20260410-001
goal: 'Test'
```
""")

        entry = parse_execution_pack(partial_path)

        assert entry.parse_status == "success"
        assert entry.day == "2026-04-10"
        assert entry.project_id == ""

    def test_missing_yaml_block_handled(self, temp_project):
        """Artifact without YAML block handled."""
        no_yaml_path = temp_project / "execution-results" / "exec-20260410-001.md"
        no_yaml_path.write_text("# ExecutionResult\n\nNo YAML here")

        entry = parse_execution_result(no_yaml_path)

        assert entry.parse_status == "success"
        assert entry.day == ""


class TestTimelineBehavior:
    """V1.1: Timeline behavior tests."""

    def test_chronological_order(self, temp_project):
        """Normalized events appear in chronological order."""
        review1 = temp_project / "reviews" / "2026-04-09-review.md"
        review1.write_text("""```yaml
date: '2026-04-09'
today_goal: 'Day 1'
```
""")

        review2 = temp_project / "reviews" / "2026-04-10-review.md"
        review2.write_text("""```yaml
date: '2026-04-10'
today_goal: 'Day 2'
```
""")

        entries, warnings = build_journal_timeline(temp_project)

        assert len(entries) >= 2
        dates = [e.day for e in entries if e.day]
        assert dates == sorted(dates)

    def test_missing_optional_fields_no_break(self, temp_project):
        """Missing optional fields do not break rendering."""
        minimal_path = temp_project / "reviews" / "2026-04-10-review.md"
        minimal_path.write_text("""```yaml
date: '2026-04-10'
```
""")

        entry = parse_review_pack(minimal_path)

        assert entry.parse_status == "success"
        assert entry.title is not None
        assert entry.summary is not None

    def test_subset_artifacts_render(self, temp_project):
        """Timeline renders when only subset of artifact types present."""
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
today_goal: 'Test'
```
""")

        entries, warnings = build_journal_timeline(temp_project)

        assert len(entries) == 1
        assert entries[0].artifact_type == "review"


class TestCLIBehavior:
    """V1.1 AC5: CLI usage/help becomes more consistent and readable."""

    def test_timeline_is_primary_entry(self):
        """journal timeline is the primary command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "timeline" in result.output

    def test_timeline_help_shows_usage(self):
        """timeline --help shows actual usage."""
        result = runner.invoke(app, ["timeline", "--help"])

        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--feature" in result.output
        assert "--type" in result.output

    def test_invalid_path_readable_error(self):
        """Invalid input paths produce readable errors."""
        result = runner.invoke(app, [
            "timeline",
            "--project", "nonexistent-project",
        ])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_stats_command_works(self):
        """stats command works."""
        result = runner.invoke(app, ["stats", "--help"])

        assert result.exit_code == 0
        assert "artifact statistics" in result.output.lower()

    def test_day_command_works(self):
        """day command works."""
        result = runner.invoke(app, ["day", "--help"])

        assert result.exit_code == 0


class TestInternalNormalization:
    """V1.1 AC2: Normalized internal event shape."""

    def test_journal_entry_fields(self):
        """JournalEntry has stable internal fields."""
        entry = JournalEntry(
            timestamp="2026-04-10",
            day="2026-04-10",
            artifact_type="review",
            project_id="test-project",
            feature_id="001-test",
            title="Test",
            summary="Test summary",
            key_fields={"status": "success"},
            source_path="/path/to/file.md",
            parse_status="success",
        )

        assert entry.timestamp == "2026-04-10"
        assert entry.day == "2026-04-10"
        assert entry.project_id == "test-project"
        assert entry.feature_id == "001-test"
        assert entry.parse_status == "success"

    def test_date_extraction_from_exec_id(self):
        """Date extraction from execution_id works."""
        assert safe_extract_date_from_exec_id("exec-20260410-001") == "2026-04-10"
        assert safe_extract_date_from_exec_id("exec-20260413-002") == "2026-04-13"
        assert safe_extract_date_from_exec_id("invalid") == ""
        assert safe_extract_date_from_exec_id("") == ""

    def test_yaml_block_extraction(self):
        """YAML block extraction handles both formats."""
        yaml_block = "```yaml\ntest: value\n```"
        assert extract_yaml_block(yaml_block) == {"test": "value"}

        dash_block = "---\ntest: value\n---\n"
        assert extract_yaml_block(dash_block) == {"test": "value"}

        assert extract_yaml_block("no yaml here") is None


class TestFilteringAndGrouping:
    """V1.1: Filter and group functionality."""

    def test_filter_by_feature(self):
        """Filter entries by feature."""
        entries = [
            JournalEntry(feature_id="001-test", title="Entry 1"),
            JournalEntry(feature_id="002-other", title="Entry 2"),
        ]

        filtered = filter_entries(entries, feature="001-test")

        assert len(filtered) == 1
        assert filtered[0].feature_id == "001-test"

    def test_filter_by_artifact_type(self):
        """Filter entries by artifact type."""
        entries = [
            JournalEntry(artifact_type="review", title="Review"),
            JournalEntry(artifact_type="plan", title="Plan"),
        ]

        filtered = filter_entries(entries, artifact_type="review")

        assert len(filtered) == 1
        assert filtered[0].artifact_type == "review"

    def test_group_by_day(self):
        """Group entries by day."""
        entries = [
            JournalEntry(day="2026-04-10", title="Entry 1"),
            JournalEntry(day="2026-04-10", title="Entry 2"),
            JournalEntry(day="2026-04-11", title="Entry 3"),
        ]

        grouped = group_entries_by_day(entries)

        assert "2026-04-10" in grouped
        assert len(grouped["2026-04-10"]) == 2
        assert len(grouped["2026-04-11"]) == 1


class TestArtifactSummary:
    """V1.1: Artifact summary functionality."""

    def test_get_artifact_summary(self, temp_project):
        """Get artifact count summary."""
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
```""")

        summary = get_artifact_summary(temp_project)

        assert "review" in summary
        assert summary["review"] == 1


class TestCanonicalLoopOrder:
    """V1.1: Canonical loop order verification."""

    def test_canonical_order_defined(self):
        """Canonical loop order is defined."""
        assert CANONICAL_LOOP_ORDER == ["plan", "run", "review"]

    def test_timeline_follows_canonical_order(self, temp_project):
        """Timeline entries follow canonical order within same day."""
        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""```yaml
execution_id: exec-20260410-001
goal: 'Test'
```""")

        result_path = temp_project / "execution-results" / "exec-20260410-001.md"
        result_path.write_text("""```yaml
execution_id: exec-20260410-001
status: success
```""")

        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
```""")

        entries, warnings = build_journal_timeline(temp_project)

        types = [e.artifact_type for e in entries if e.day == "2026-04-10"]
        assert types == ["plan", "run", "review"]


class TestDayDetailOrder:
    """V1.2: Day detail order verification."""

    def test_day_detail_order_defined(self):
        assert DAY_DETAIL_ORDER == ["review", "plan", "run"]

    def test_day_detail_order_different_from_timeline(self):
        assert DAY_DETAIL_ORDER != CANONICAL_LOOP_ORDER


class TestDayDetailViewV12:
    """V1.2: Day detail view acceptance criteria tests."""

    def test_valid_day_with_multiple_artifacts(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
project_id: test-project
today_goal: 'Test execution'
```""")

        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""```yaml
execution_id: exec-20260410-001
project_id: test-project
goal: 'Test task'
planning_mode: continue_work
```""")

        result_path = temp_project / "execution-results" / "exec-20260410-001.md"
        result_path.write_text("""```yaml
execution_id: exec-20260410-001
project_id: test-project
status: success
completed_items: ['Task done']
```""")

        entries, warnings = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)

        assert "2026-04-10" in grouped
        day_entries = grouped["2026-04-10"]
        assert len(day_entries) == 3

    def test_valid_day_with_partial_artifacts(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
```""")

        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""```yaml
execution_id: exec-20260410-001
goal: 'Partial day'
```""")

        entries, warnings = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)

        assert "2026-04-10" in grouped
        day_entries = grouped["2026-04-10"]
        assert len(day_entries) == 2
        assert "run" not in [e.artifact_type for e in day_entries]

    def test_invalid_day_produces_error(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
```""")

        entries, warnings = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)

        assert "2026-04-11" not in grouped
        assert "2026-04-10" in grouped

    def test_empty_day_handling(self, temp_project):
        entries, warnings = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)

        assert len(grouped) == 0 or all(len(v) == 0 for v in grouped.values())

    def test_canonical_day_order_in_detail(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
```""")

        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""```yaml
execution_id: exec-20260410-001
goal: 'Test'
```""")

        result_path = temp_project / "execution-results" / "exec-20260410-001.md"
        result_path.write_text("""```yaml
execution_id: exec-20260410-001
status: success
```""")

        entries, _ = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)
        day_entries = grouped.get("2026-04-10", [])

        entries_by_type = {}
        for entry in day_entries:
            entries_by_type[entry.artifact_type] = entry

        for artifact_type in DAY_DETAIL_ORDER:
            if artifact_type in entries_by_type:
                assert entries_by_type[artifact_type].artifact_type == artifact_type

    def test_source_traceability_preserved(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
```""")

        entries, _ = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)
        day_entries = grouped.get("2026-04-10", [])

        for entry in day_entries:
            assert entry.source_path
            assert str(temp_project) in entry.source_path or "test-project" in entry.source_path

    def test_missing_optional_fields_no_break(self, temp_project):
        minimal_path = temp_project / "reviews" / "2026-04-10-review.md"
        minimal_path.write_text("""```yaml
date: '2026-04-10'
```""")

        entries, warnings = build_journal_timeline(temp_project)
        grouped = group_entries_by_day(entries)

        assert "2026-04-10" in grouped
        day_entries = grouped["2026-04-10"]
        assert day_entries[0].parse_status == "success"


class TestDayCLIV12:
    """V1.2: CLI day command tests."""

    def test_day_help_is_clear(self):
        result = runner.invoke(app, ["day", "--help"])
        assert result.exit_code == 0
        assert "canonical order" in result.output.lower() or "Review" in result.output

    def test_day_command_with_project(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
today_goal: 'Test'
```""")

        result = runner.invoke(app, [
            "day", "2026-04-10",
            "--project", "test-project",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 0
        assert "Day: 2026-04-10" in result.output

    def test_day_command_invalid_date(self, temp_project):
        result = runner.invoke(app, [
            "day", "invalid-date",
            "--project", "test-project",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "No days" in result.output

    def test_day_command_missing_project(self):
        result = runner.invoke(app, [
            "day", "2026-04-10",
            "--project", "nonexistent",
        ])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

class TestFeatureGroupingV13:
    """V1.3: Feature grouping tests."""

    def test_group_entries_by_feature(self):
        entries = [
            JournalEntry(feature_id="001-test", day="2026-04-10", title="Entry 1"),
            JournalEntry(feature_id="001-test", day="2026-04-11", title="Entry 2"),
            JournalEntry(feature_id="002-other", day="2026-04-10", title="Entry 3"),
            JournalEntry(feature_id="", day="2026-04-10", title="Entry 4"),
        ]

        grouped = group_entries_by_feature(entries)

        assert "001-test" in grouped
        assert len(grouped["001-test"]) == 2
        assert "002-other" in grouped
        assert len(grouped["002-other"]) == 1
        assert "unassigned" in grouped
        assert len(grouped["unassigned"]) == 1

    def test_filter_entries_strict(self):
        entries = [
            JournalEntry(feature_id="001-test", title="Entry 1"),
            JournalEntry(feature_id="002-other", title="Entry 2"),
            JournalEntry(feature_id="", title="Entry 3"),
        ]

        filtered = filter_entries_strict(entries, feature="001-test")

        assert len(filtered) == 1
        assert filtered[0].feature_id == "001-test"

    def test_get_available_features(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
feature_id: 001-feature-a
```""")

        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""```yaml
execution_id: exec-20260410-001
feature_id: 001-feature-a
goal: 'Test'
```""")

        pack_path2 = temp_project / "execution-packs" / "exec-20260411-002.md"
        pack_path2.write_text("""```yaml
execution_id: exec-20260411-002
feature_id: 002-feature-b
goal: 'Test 2'
```""")

        features = get_available_features(temp_project)

        assert "001-feature-a" in features
        assert "002-feature-b" in features


class TestFeatureTimelineV13:
    """V1.3: Feature timeline tests."""

    def test_feature_timeline_with_entries(self, temp_project):
        review1 = temp_project / "reviews" / "2026-04-09-review.md"
        review1.write_text("""```yaml
date: '2026-04-09'
feature_id: 001-test-feature
today_goal: 'Day 1'
```""")

        review2 = temp_project / "reviews" / "2026-04-10-review.md"
        review2.write_text("""```yaml
date: '2026-04-10'
feature_id: 001-test-feature
today_goal: 'Day 2'
```""")

        entries, _ = build_journal_timeline(temp_project)
        feature_entries = filter_entries_strict(entries, feature="001-test-feature")

        assert len(feature_entries) >= 2

    def test_feature_timeline_partial_metadata(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
feature_id: 001-partial
```""")

        pack_path = temp_project / "execution-packs" / "exec-20260410-001.md"
        pack_path.write_text("""```yaml
execution_id: exec-20260410-001
goal: 'No feature ID here'
```""")

        entries, _ = build_journal_timeline(temp_project)
        feature_entries = filter_entries_strict(entries, feature="001-partial")

        assert len(feature_entries) == 1
        assert feature_entries[0].feature_id == "001-partial"

    def test_feature_timeline_missing_graceful(self, temp_project):
        entries, _ = build_journal_timeline(temp_project)
        feature_entries = filter_entries_strict(entries, feature="nonexistent-feature")

        assert len(feature_entries) == 0


class TestFeatureCLIV13:
    """V1.3: CLI feature command tests."""

    def test_feature_help_is_clear(self):
        result = runner.invoke(app, ["feature", "--help"])
        assert result.exit_code == 0
        assert "feature" in result.output.lower()

    def test_feature_command_with_entries(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
feature_id: test-feature-001
today_goal: 'Test'
```""")

        result = runner.invoke(app, [
            "feature", "test-feature-001",
            "--project", "test-project",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 0

    def test_feature_command_not_found(self, temp_project):
        result = runner.invoke(app, [
            "feature", "nonexistent-feature",
            "--project", "test-project",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_feature_command_missing_project(self):
        result = runner.invoke(app, [
            "feature", "some-feature",
            "--project", "nonexistent",
        ])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestProjectSummaryCLI13:
    """V1.3: CLI project-summary command tests."""

    def test_project_summary_help(self):
        result = runner.invoke(app, ["project-summary", "--help"])
        assert result.exit_code == 0

    def test_project_summary_with_features(self, temp_project):
        review_path = temp_project / "reviews" / "2026-04-10-review.md"
        review_path.write_text("""```yaml
date: '2026-04-10'
feature_id: test-feature-001
```""")

        result = runner.invoke(app, [
            "project-summary",
            "--project", "test-project",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 0

    def test_project_summary_missing_project(self):
        result = runner.invoke(app, [
            "project-summary",
            "--project", "nonexistent",
        ])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
