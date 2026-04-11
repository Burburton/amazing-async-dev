"""Tests for archive query commands - Feature 014."""

import pytest
from pathlib import Path
import yaml
from typer.testing import CliRunner

from runtime.archive_query import (
    discover_all_archives,
    filter_archives,
    get_archive_detail,
    load_archive_pack,
    get_lessons_summary,
    get_patterns_summary,
    list_archives_with_patterns,
    list_archives_with_lessons,
    get_recent_archives,
)

runner = CliRunner()


@pytest.fixture
def setup_archives(temp_dir):
    """Create multiple products with archived features."""
    product_a = temp_dir / "product-a"
    product_b = temp_dir / "product-b"
    
    product_a.mkdir(parents=True)
    product_b.mkdir(parents=True)
    
    archive_a1 = product_a / "archive" / "001-auth"
    archive_a2 = product_a / "archive" / "002-core"
    archive_b1 = product_b / "archive" / "003-api"
    
    archive_a1.mkdir(parents=True)
    archive_a2.mkdir(parents=True)
    archive_b1.mkdir(parents=True)
    
    pack_a1 = {
        "feature_id": "001-auth",
        "product_id": "product-a",
        "title": "Auth Feature",
        "final_status": "completed",
        "archived_at": "2026-04-01T10:00:00",
        "delivered_outputs": [{"name": "auth.py", "path": "auth.py"}],
        "lessons_learned": [{"lesson": "Keep scope small", "context": "Testing"}],
        "reusable_patterns": [{"pattern": "Schema-first", "applicability": "Objects"}],
        "decisions_made": [],
    }
    
    pack_a2 = {
        "feature_id": "002-core",
        "product_id": "product-a",
        "title": "Core Feature",
        "final_status": "partial",
        "archived_at": "2026-04-02T10:00:00",
        "delivered_outputs": [],
        "lessons_learned": [],
        "reusable_patterns": [{"pattern": "Template pattern", "applicability": "Docs"}],
        "decisions_made": [],
    }
    
    pack_b1 = {
        "feature_id": "003-api",
        "product_id": "product-b",
        "title": "API Feature",
        "final_status": "completed",
        "archived_at": "2026-04-03T10:00:00",
        "delivered_outputs": [{"name": "api.py"}],
        "lessons_learned": [{"lesson": "Test early", "context": "API"}],
        "reusable_patterns": [],
        "decisions_made": [],
    }
    
    with open(archive_a1 / "archive-pack.yaml", "w") as f:
        yaml.dump(pack_a1, f)
    
    with open(archive_a2 / "archive-pack.yaml", "w") as f:
        yaml.dump(pack_a2, f)
    
    with open(archive_b1 / "archive-pack.yaml", "w") as f:
        yaml.dump(pack_b1, f)
    
    yield temp_dir


class TestArchiveQueryRuntime:
    """Tests for runtime/archive_query.py functions."""

    def test_discover_all_archives(self, setup_archives):
        """discover_all_archives should find all archives."""
        archives = discover_all_archives(setup_archives)
        
        assert len(archives) == 3
        
        feature_ids = [a.get("feature_id") for a in archives]
        assert "001-auth" in feature_ids
        assert "002-core" in feature_ids
        assert "003-api" in feature_ids

    def test_discover_includes_metadata(self, setup_archives):
        """discover_all_archives should include pattern/lesson metadata."""
        archives = discover_all_archives(setup_archives)
        
        auth = next(a for a in archives if a.get("feature_id") == "001-auth")
        assert auth.get("has_patterns") == True
        assert auth.get("has_lessons") == True
        assert auth.get("patterns_count") == 1
        assert auth.get("lessons_count") == 1
        
        core = next(a for a in archives if a.get("feature_id") == "002-core")
        assert core.get("has_patterns") == True
        assert core.get("has_lessons") == False

    def test_filter_by_product(self, setup_archives):
        """filter_archives should filter by product."""
        archives = discover_all_archives(setup_archives)
        filtered = filter_archives(archives, product="product-a")
        
        assert len(filtered) == 2
        for a in filtered:
            assert a.get("product_id") == "product-a"

    def test_filter_by_has_patterns(self, setup_archives):
        """filter_archives should filter by patterns presence."""
        archives = discover_all_archives(setup_archives)
        filtered = filter_archives(archives, has_patterns=True)
        
        assert len(filtered) == 2
        for a in filtered:
            assert a.get("has_patterns") == True

    def test_filter_by_has_lessons(self, setup_archives):
        """filter_archives should filter by lessons presence."""
        archives = discover_all_archives(setup_archives)
        filtered = filter_archives(archives, has_lessons=True)
        
        assert len(filtered) == 2
        for a in filtered:
            assert a.get("has_lessons") == True

    def test_filter_by_recent(self, setup_archives):
        """filter_archives should sort by archived_at descending."""
        archives = discover_all_archives(setup_archives)
        filtered = filter_archives(archives, recent=True)
        
        assert filtered[0].get("feature_id") == "003-api"
        assert filtered[1].get("feature_id") == "002-core"
        assert filtered[2].get("feature_id") == "001-auth"

    def test_filter_by_limit(self, setup_archives):
        """filter_archives should respect limit."""
        archives = discover_all_archives(setup_archives)
        filtered = filter_archives(archives, limit=2)
        
        assert len(filtered) == 2

    def test_combined_filters(self, setup_archives):
        """filter_archives should combine multiple filters."""
        archives = discover_all_archives(setup_archives)
        filtered = filter_archives(
            archives,
            product="product-a",
            has_patterns=True,
        )
        
        assert len(filtered) == 2

    def test_get_archive_detail_with_product(self, setup_archives):
        """get_archive_detail should find archive with product specified."""
        detail = get_archive_detail(setup_archives, "001-auth", "product-a")
        
        assert detail is not None
        assert detail.get("feature_id") == "001-auth"
        assert detail.get("product_id") == "product-a"
        assert detail.get("title") == "Auth Feature"

    def test_get_archive_detail_without_product(self, setup_archives):
        """get_archive_detail should search all products if product not specified."""
        detail = get_archive_detail(setup_archives, "003-api")
        
        assert detail is not None
        assert detail.get("feature_id") == "003-api"
        assert detail.get("product_id") == "product-b"

    def test_get_archive_detail_includes_lessons(self, setup_archives):
        """get_archive_detail should include lessons_learned."""
        detail = get_archive_detail(setup_archives, "001-auth", "product-a")
        
        lessons = get_lessons_summary(detail)
        assert len(lessons) == 1
        assert lessons[0].get("lesson") == "Keep scope small"

    def test_get_archive_detail_includes_patterns(self, setup_archives):
        """get_archive_detail should include reusable_patterns."""
        detail = get_archive_detail(setup_archives, "001-auth", "product-a")
        
        patterns = get_patterns_summary(detail)
        assert len(patterns) == 1
        assert patterns[0].get("pattern") == "Schema-first"

    def test_get_archive_detail_not_found(self, setup_archives):
        """get_archive_detail should return None for non-existent."""
        detail = get_archive_detail(setup_archives, "999-unknown")
        
        assert detail is None

    def test_list_archives_with_patterns(self, setup_archives):
        """list_archives_with_patterns should return only pattern archives."""
        result = list_archives_with_patterns(setup_archives)
        
        assert len(result) == 2
        for a in result:
            assert a.get("has_patterns") == True

    def test_list_archives_with_lessons(self, setup_archives):
        """list_archives_with_lessons should return only lesson archives."""
        result = list_archives_with_lessons(setup_archives)
        
        assert len(result) == 2
        for a in result:
            assert a.get("has_lessons") == True

    def test_get_recent_archives(self, setup_archives):
        """get_recent_archives should return recent sorted."""
        result = get_recent_archives(setup_archives, limit=2)
        
        assert len(result) == 2
        assert result[0].get("feature_id") == "003-api"


class TestArchiveListCommand:
    """Tests for archive list CLI command."""

    def test_lists_all_archives(self, setup_archives):
        """archive list should show all archives."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, ["list", "--path", str(setup_archives)])
        
        assert result.exit_code == 0
        assert "001-auth" in result.output
        assert "002-core" in result.output
        assert "003-api" in result.output

    def test_filters_by_product(self, setup_archives):
        """archive list --product should filter by product."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "list",
            "--product", "product-a",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "001-auth" in result.output
        assert "002-core" in result.output
        assert "003-api" not in result.output

    def test_filters_by_patterns(self, setup_archives):
        """archive list --has-patterns should filter."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "list",
            "--has-patterns",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "001-auth" in result.output
        assert "002-core" in result.output
        assert "003-api" not in result.output

    def test_filters_by_lessons(self, setup_archives):
        """archive list --has-lessons should filter."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "list",
            "--has-lessons",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "001-auth" in result.output
        assert "003-api" in result.output
        assert "002-core" not in result.output

    def test_sorts_by_recent(self, setup_archives):
        """archive list --recent should sort by date."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "list",
            "--recent",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0

    def test_respects_limit(self, setup_archives):
        """archive list --limit should limit results."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "list",
            "--limit", "1",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "Total: 1 archives" in result.output

    def test_shows_empty_message(self, temp_dir):
        """archive list should show message when no archives."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, ["list", "--path", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "No archived features found" in result.output


class TestArchiveShowCommand:
    """Tests for archive show CLI command."""

    def test_shows_archive_detail(self, setup_archives):
        """archive show should display full detail."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "show",
            "--feature", "001-auth",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "Auth Feature" in result.output
        assert "product-a" in result.output

    def test_shows_lessons(self, setup_archives):
        """archive show should display lessons."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "show",
            "--feature", "001-auth",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "Lessons Learned" in result.output
        assert "Keep scope small" in result.output

    def test_shows_patterns(self, setup_archives):
        """archive show should display patterns."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "show",
            "--feature", "001-auth",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "Reusable Patterns" in result.output
        assert "Schema-first" in result.output

    def test_with_product_option(self, setup_archives):
        """archive show --product should locate faster."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "show",
            "--feature", "003-api",
            "--product", "product-b",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "API Feature" in result.output

    def test_fails_on_not_found(self, setup_archives):
        """archive show should fail for non-existent."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "show",
            "--feature", "999-unknown",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 1
        assert "Archive not found" in result.output

    def test_shows_delivered_outputs(self, setup_archives):
        """archive show should display delivered outputs."""
        from cli.commands.archive import app
        
        result = runner.invoke(app, [
            "show",
            "--feature", "001-auth",
            "--path", str(setup_archives),
        ])
        
        assert result.exit_code == 0
        assert "Delivered Outputs" in result.output


class TestLoadArchivePack:
    """Tests for load_archive_pack function."""

    def test_loads_yaml_file(self, setup_archives):
        """load_archive_pack should load YAML."""
        archive_path = setup_archives / "product-a" / "archive" / "001-auth" / "archive-pack.yaml"
        
        pack = load_archive_pack(archive_path)
        
        assert pack is not None
        assert pack.get("feature_id") == "001-auth"

    def test_returns_none_for_missing(self, temp_dir):
        """load_archive_pack should return None for missing file."""
        pack = load_archive_pack(temp_dir / "nonexistent.yaml")
        
        assert pack is None