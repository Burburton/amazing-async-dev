"""Tests for error handling across CLI commands."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from runtime.state_store import StateStore


runner = CliRunner()


@pytest.fixture
def temp_project(temp_dir):
    """Create empty project directory."""
    project_path = temp_dir / "test-product"
    project_path.mkdir()
    yield project_path


class TestMissingRunStateHandling:
    """Tests for handling missing RunState."""

    def test_plan_day_show_handles_missing_runstate(self, temp_project):
        """plan-day show should handle missing RunState gracefully."""
        from cli.commands.plan_day import app as plan_app
        
        result = runner.invoke(plan_app, [
            "show",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert "No RunState found" in result.output

    def test_review_night_generate_fails_without_runstate(self, temp_project):
        """review-night generate should fail if RunState missing."""
        from cli.commands.review_night import app as review_app
        
        result = runner.invoke(review_app, [
            "generate",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output

    def test_resume_continue_loop_fails_without_runstate(self, temp_project):
        """continue-loop should fail if RunState missing."""
        from cli.commands.resume_next_day import app as resume_app
        
        result = runner.invoke(resume_app, [
            "continue-loop",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output

    def test_resume_unblock_fails_without_runstate(self, temp_project):
        """unblock should fail if RunState missing."""
        from cli.commands.resume_next_day import app as resume_app
        
        result = runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output

    def test_resume_handle_failed_fails_without_runstate(self, temp_project):
        """handle-failed should fail if RunState missing."""
        from cli.commands.resume_next_day import app as resume_app
        
        result = runner.invoke(resume_app, [
            "handle-failed",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "No RunState found" in result.output

    def test_resume_status_handles_missing_runstate(self, temp_project):
        """resume status should handle missing RunState gracefully."""
        from cli.commands.resume_next_day import app as resume_app
        
        result = runner.invoke(resume_app, [
            "status",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert "No RunState found" in result.output


class TestMissingExecutionResultHandling:
    """Tests for handling missing ExecutionResult."""

    def test_review_night_generate_fails_without_execution_result(self, temp_project):
        """review-night generate should fail if no ExecutionResult."""
        from cli.commands.review_night import app as review_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "current_phase": "reviewing",
        }
        store.save_runstate(runstate)

        result = runner.invoke(review_app, [
            "generate",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "No ExecutionResult found" in result.output

    def test_review_night_generate_fails_for_nonexistent_execution_id(self, temp_project):
        """review-night generate should fail for nonexistent execution_id."""
        from cli.commands.review_night import app as review_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
        }
        store.save_runstate(runstate)

        result = runner.invoke(review_app, [
            "generate",
            "--project", "test-product",
            "--execution-id", "nonexistent-exec",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "ExecutionResult not found" in result.output


class TestMissingExecutionPackHandling:
    """Tests for handling missing ExecutionPack."""

    def test_plan_day_create_fails_without_task_queue(self, temp_project):
        """plan-day create should fail if no task and empty queue."""
        from cli.commands.plan_day import app as plan_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "current_phase": "planning",
            "task_queue": [],
            "active_task": "",
        }
        store.save_runstate(runstate)

        result = runner.invoke(plan_app, [
            "create",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "No tasks in queue" in result.output


class TestInvalidPhaseTransition:
    """Tests for invalid phase transitions."""

    def test_unblock_fails_when_not_blocked(self, temp_project):
        """unblock should fail if not in blocked phase."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "current_phase": "planning",
        }
        store.save_runstate(runstate)

        result = runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "only for blocked state" in result.output

    def test_unblock_fails_when_executing(self, temp_project):
        """unblock should fail if in executing phase."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "current_phase": "executing",
        }
        store.save_runstate(runstate)

        result = runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1

    def test_unblock_fails_when_reviewing(self, temp_project):
        """unblock should fail if in reviewing phase."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "current_phase": "reviewing",
        }
        store.save_runstate(runstate)

        result = runner.invoke(resume_app, [
            "unblock",
            "--project", "test-product",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1


class TestInvalidInputValidation:
    """Tests for invalid input validation."""

    def test_revise_requires_revise_choice(self, temp_project):
        """continue-loop with revise decision requires --revise-choice."""
        from cli.commands.resume_next_day import app as resume_app
        
        store = StateStore(temp_project)
        runstate = {
            "project_id": "test-product",
            "feature_id": "001-test",
            "current_phase": "reviewing",
            "decisions_needed": [
                {"decision": "Choose approach", "options": ["A", "B"]}
            ],
        }
        store.save_runstate(runstate)

        result = runner.invoke(resume_app, [
            "continue-loop",
            "--project", "test-product",
            "--decision", "revise",
            "--path", str(temp_project.parent),
        ])

        assert result.exit_code == 1
        assert "Must specify --revise-choice" in result.output

    def test_new_product_fails_if_exists(self, temp_dir):
        """new-product should fail if product already exists."""
        from cli.commands.new_product import app as new_product_app
        
        existing_path = temp_dir / "existing-product"
        existing_path.mkdir()

        result = runner.invoke(new_product_app, [
            "create",
            "--product-id", "existing-product",
            "--name", "Existing",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_new_feature_fails_if_product_not_found(self, temp_dir):
        """new-feature should fail if product doesn't exist."""
        from cli.commands.new_feature import app as new_feature_app
        
        result = runner.invoke(new_feature_app, [
            "create",
            "--product-id", "nonexistent-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_new_feature_fails_if_feature_exists(self, temp_dir):
        """new-feature should fail if feature already exists."""
        from cli.commands.new_product import app as new_product_app
        from cli.commands.new_feature import app as new_feature_app
        
        runner.invoke(new_product_app, [
            "create",
            "--product-id", "test-product",
            "--name", "Test Product",
            "--path", str(temp_dir),
        ])
        
        runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])

        result = runner.invoke(new_feature_app, [
            "create",
            "--product-id", "test-product",
            "--feature-id", "001-test",
            "--name", "Test Feature",
            "--path", str(temp_dir),
        ])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_fails_if_exists_without_force(self, temp_dir):
        """init should fail if projects directory exists without --force."""
        from cli.commands.init import app as init_app
        
        projects_path = temp_dir / "projects"
        projects_path.mkdir()

        result = runner.invoke(init_app, [
            "create",
            "--path", str(projects_path),
        ])

        assert result.exit_code == 1
        assert "exists" in result.output


class TestCorruptedStateHandling:
    """Tests for handling corrupted state files."""

    def test_load_handles_missing_yaml_block(self, temp_project):
        """load_runstate should return None if no YAML block."""
        store = StateStore(temp_project)
        
        content_without_block = """# RunState

No YAML block here.
"""
        store.fs.write_file(store.runstate_path, content_without_block)

        result = store.load_runstate()
        assert result is None

    def test_yaml_parser_raises_on_invalid_yaml(self, temp_project):
        """Invalid YAML should raise ParserError."""
        import yaml
        
        invalid_yaml = "this is not valid yaml: ["
        
        with pytest.raises(yaml.parser.ParserError):
            yaml.safe_load(invalid_yaml)

    def test_load_returns_none_for_empty_file(self, temp_project):
        """load_runstate should return None for empty file."""
        store = StateStore(temp_project)
        
        store.fs.write_file(store.runstate_path, "")

        result = store.load_runstate()
        assert result is None

    def test_load_execution_pack_returns_none_for_missing_block(self, temp_project):
        """load_execution_pack should return None for missing YAML block."""
        store = StateStore(temp_project)
        store.fs.ensure_dir(store.execution_packs_path)
        
        pack_path = store.execution_packs_path / "exec-noblock.md"
        content_without_block = """# ExecutionPack

No YAML block.
"""
        store.fs.write_file(pack_path, content_without_block)

        result = store.load_execution_pack("exec-noblock")
        assert result is None