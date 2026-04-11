"""Tests for asyncdev init command."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from cli.commands.init import app


runner = CliRunner()


class TestInitCreate:
    """Tests for init create command."""

    def test_creates_projects_directory(self, temp_dir):
        """init create should create the projects root directory."""
        result = runner.invoke(app, ["create", "--path", str(temp_dir / "projects"), "--force"])

        assert result.exit_code == 0
        assert (temp_dir / "projects").exists()

    def test_fails_if_directory_exists_without_force(self, temp_dir):
        """init create should fail if directory exists without --force."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        result = runner.invoke(app, ["create", "--path", str(existing_dir)])

        assert result.exit_code == 1
        assert "exists" in result.output

    def test_overwrites_with_force(self, temp_dir):
        """init create should overwrite existing directory with --force."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()
        (existing_dir / "old_file.txt").write_text("old")

        result = runner.invoke(app, ["create", "--path", str(existing_dir), "--force"])

        assert result.exit_code == 0

    def test_outputs_next_steps(self, temp_dir):
        """init create should output next steps guidance."""
        result = runner.invoke(app, ["create", "--path", str(temp_dir / "projects"), "--force"])

        assert "new-product" in result.output
        assert "new-feature" in result.output


class TestInitStatus:
    """Tests for init status command."""

    def test_shows_no_projects_message_when_empty(self, temp_dir):
        """init status should show message when no projects exist."""
        result = runner.invoke(app, ["status", "--path", str(temp_dir)])

        assert "No projects" in result.output

    def test_lists_existing_projects(self, temp_dir):
        """init status should list existing projects."""
        projects_dir = temp_dir / "projects"
        projects_dir.mkdir()
        (projects_dir / "project-001").mkdir()

        result = runner.invoke(app, ["status", "--path", str(projects_dir)])

        assert "project-001" in result.output