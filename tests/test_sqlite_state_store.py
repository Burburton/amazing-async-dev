"""Tests for SQLite state store and adapter."""

import pytest
from pathlib import Path
import tempfile
import shutil

from runtime.adapters.sqlite_adapter import SQLiteAdapter
from runtime.sqlite_state_store import SQLiteStateStore


@pytest.fixture
def temp_db_dir():
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    try:
        shutil.rmtree(dir_path)
    except PermissionError:
        pass


@pytest.fixture
def sqlite_adapter(temp_db_dir):
    db_path = temp_db_dir / "test.db"
    adapter = SQLiteAdapter(db_path)
    yield adapter
    adapter.close()


@pytest.fixture
def sqlite_state_store(temp_db_dir):
    project_path = temp_db_dir / "test-product"
    project_path.mkdir()
    db_path = project_path / ".runtime" / "test.db"
    store = SQLiteStateStore(project_path, db_path)
    yield store
    store.close()


class TestSQLiteAdapter:
    """Tests for SQLiteAdapter."""

    def test_initializes_database(self, sqlite_adapter):
        """SQLiteAdapter should create database with schema."""
        sqlite_adapter._get_connection()
        assert sqlite_adapter.db_path.exists()

    def test_inserts_product(self, sqlite_adapter):
        """insert_product should add product record."""
        sqlite_adapter.insert_product("test-product-001", "Test Product")

        products = sqlite_adapter.list_products()
        assert len(products) == 1
        assert products[0]["product_id"] == "test-product-001"

    def test_inserts_feature(self, sqlite_adapter):
        """insert_feature should add feature record."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test Feature")

        features = sqlite_adapter.list_features("test-product-001")
        assert len(features) == 1
        assert features[0]["feature_id"] == "001-test"

    def test_updates_feature_phase(self, sqlite_adapter):
        """update_feature_phase should change phase."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test Feature", "planning")

        sqlite_adapter.update_feature_phase("001-test", "executing", "task-1")

        feature = sqlite_adapter.get_feature("001-test")
        assert feature["current_phase"] == "executing"
        assert feature["active_task"] == "task-1"

    def test_logs_event(self, sqlite_adapter):
        """log_event should record execution event."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test")

        sqlite_adapter.log_event("001-test", "test-product-001", "plan-day", {"task": "task-1"})

        events = sqlite_adapter.get_recent_events("001-test", limit=10)
        assert len(events) == 1
        assert events[0]["event_type"] == "plan-day"

    def test_logs_transition(self, sqlite_adapter):
        """log_transition should record phase change."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test")

        sqlite_adapter.log_transition("001-test", "test-product-001", "planning", "executing", "Task started")

        transitions = sqlite_adapter.get_transitions("001-test")
        assert len(transitions) == 1
        assert transitions[0]["from_phase"] == "planning"
        assert transitions[0]["to_phase"] == "executing"

    def test_saves_runstate_snapshot(self, sqlite_adapter):
        """save_runstate_snapshot should record state."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test")

        runstate = {
            "current_phase": "executing",
            "active_task": "task-1",
            "task_queue": ["task-2", "task-3"],
            "completed_outputs": ["output-1"],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Started task-1",
            "next_recommended_action": "Complete task-1",
        }

        sqlite_adapter.save_runstate_snapshot(runstate, "001-test", "test-product-001")

        snapshot = sqlite_adapter.get_latest_snapshot("001-test")
        assert snapshot is not None
        assert snapshot["phase"] == "executing"
        assert len(snapshot["task_queue"]) == 2

    def test_get_recovery_info(self, sqlite_adapter):
        """get_recovery_info should return complete recovery data."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test")

        runstate = {"current_phase": "blocked", "active_task": "task-1"}
        sqlite_adapter.save_runstate_snapshot(runstate, "001-test", "test-product-001")
        sqlite_adapter.log_event("001-test", "test-product-001", "blocked", {"reason": "API down"})
        sqlite_adapter.log_transition("001-test", "test-product-001", "executing", "blocked", "Blocked")

        info = sqlite_adapter.get_recovery_info("001-test")

        assert info["latest_snapshot"] is not None
        assert len(info["recent_events"]) >= 1
        assert len(info["transitions"]) >= 1
        assert info["can_resume"] is True

    def test_archive_record(self, sqlite_adapter):
        """insert_archive_record should mark feature archived."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test")

        sqlite_adapter.insert_archive_record("001-test", "test-product-001", "completed", "archive/001-test/")

        record = sqlite_adapter.get_archive_record("001-test")
        assert record is not None
        assert record["final_status"] == "completed"

    def test_list_archived_features(self, sqlite_adapter):
        """list_archived_features should return archived features."""
        sqlite_adapter.insert_product("test-product-001", "Test")
        sqlite_adapter.insert_feature("001-test", "test-product-001", "Test")
        sqlite_adapter.insert_feature("002-test", "test-product-001", "Test 2")

        sqlite_adapter.insert_archive_record("001-test", "test-product-001", "completed", "archive/001/")
        sqlite_adapter.insert_archive_record("002-test", "test-product-001", "partial", "archive/002/")

        archived = sqlite_adapter.list_archived_features("test-product-001")
        assert len(archived) == 2


class TestSQLiteStateStore:
    """Tests for SQLiteStateStore."""

    def test_mirrors_file_store_interface(self, sqlite_state_store):
        """SQLiteStateStore should have same methods as StateStore."""
        assert hasattr(sqlite_state_store, "load_runstate")
        assert hasattr(sqlite_state_store, "save_runstate")
        assert hasattr(sqlite_state_store, "load_execution_pack")
        assert hasattr(sqlite_state_store, "save_execution_pack")

    def test_initializes_product(self, sqlite_state_store):
        """initialize_product should register product in SQLite."""
        sqlite_state_store.initialize_product("test-product-001", "Test Product")

        products = sqlite_state_store.sqlite.list_products()
        assert len(products) == 1

    def test_initializes_feature(self, sqlite_state_store):
        """initialize_feature should register feature with event."""
        sqlite_state_store.initialize_product("test-product-001", "Test")
        sqlite_state_store.initialize_feature("001-test", "test-product-001", "Test Feature")

        feature = sqlite_state_store.sqlite.get_feature("001-test")
        assert feature is not None

        events = sqlite_state_store.sqlite.get_recent_events("001-test")
        assert len(events) == 1
        assert events[0]["event_type"] == "new-feature"

    def test_logs_event_on_save_runstate(self, sqlite_state_store):
        """save_runstate should create snapshot in SQLite."""
        sqlite_state_store.initialize_product("test-product-001", "Test")
        sqlite_state_store.initialize_feature("001-test", "test-product-001", "Test")

        from runtime.state_store import StateStore
        file_store = StateStore(sqlite_state_store.project_path)
        runstate = file_store.load_runstate() or {}
        runstate["feature_id"] = "001-test"
        runstate["project_id"] = "test-product-001"
        runstate["current_phase"] = "executing"
        runstate["active_task"] = "task-1"
        runstate["task_queue"] = []
        runstate["completed_outputs"] = []
        runstate["blocked_items"] = []
        runstate["decisions_needed"] = []
        file_store.save_runstate(runstate)

        sqlite_state_store.save_runstate(runstate)

        snapshot = sqlite_state_store.get_latest_snapshot("001-test")
        assert snapshot is not None
        assert snapshot["phase"] == "executing"

    def test_get_recovery_info_returns_data(self, sqlite_state_store):
        """get_recovery_info should return structured recovery info."""
        sqlite_state_store.initialize_product("test-product-001", "Test")
        sqlite_state_store.initialize_feature("001-test", "test-product-001", "Test")

        info = sqlite_state_store.get_recovery_info("001-test")

        assert "latest_snapshot" in info
        assert "recent_events" in info
        assert "transitions" in info
        assert "can_resume" in info

    def test_log_transition_records_phase_change(self, sqlite_state_store):
        """log_transition should record phase change."""
        sqlite_state_store.initialize_product("test-product-001", "Test")
        sqlite_state_store.initialize_feature("001-test", "test-product-001", "Test")

        sqlite_state_store.sqlite.log_transition("001-test", "test-product-001", "planning", "executing", "Started")

        transitions = sqlite_state_store.get_transitions("001-test")
        assert len(transitions) == 1
        assert transitions[0]["from_phase"] == "planning"
        assert transitions[0]["to_phase"] == "executing"

    def test_archive_feature_updates_state(self, sqlite_state_store):
        """archive_feature should mark feature archived in SQLite."""
        sqlite_state_store.initialize_product("test-product-001", "Test")
        sqlite_state_store.initialize_feature("001-test", "test-product-001", "Test")

        sqlite_state_store.archive_feature("001-test", "test-product-001", "completed", "archive/001-test/")

        record = sqlite_state_store.sqlite.get_archive_record("001-test")
        assert record is not None

        feature = sqlite_state_store.sqlite.get_feature("001-test")
        assert feature["current_phase"] == "archived"


class TestSQLiteCLI:
    """Tests for SQLite CLI commands."""

    def test_history_command_works(self, temp_db_dir):
        """sqlite history should display events."""
        from typer.testing import CliRunner
        from cli.commands.sqlite_status import app

        runner = CliRunner()
        project_path = temp_db_dir / "test-product"
        project_path.mkdir()

        store = SQLiteStateStore(project_path)
        store.initialize_product("test-product", "Test")
        store.initialize_feature("001-test", "test-product", "Test Feature")
        store.close()

        result = runner.invoke(app, [
            "history",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_db_dir),
        ])

        assert result.exit_code == 0

    def test_features_command_works(self, temp_db_dir):
        """sqlite features should list features."""
        from typer.testing import CliRunner
        from cli.commands.sqlite_status import app

        runner = CliRunner()
        project_path = temp_db_dir / "test-product"
        project_path.mkdir()

        store = SQLiteStateStore(project_path)
        store.initialize_product("test-product", "Test")
        store.initialize_feature("001-test", "test-product", "Test Feature")
        store.close()

        result = runner.invoke(app, [
            "features",
            "--project", "test-product",
            "--path", str(temp_db_dir),
        ])

        assert result.exit_code == 0
        assert "001-test" in result.output

    def test_recovery_command_works(self, temp_db_dir):
        """sqlite recovery should show recovery info."""
        from typer.testing import CliRunner
        from cli.commands.sqlite_status import app

        runner = CliRunner()
        project_path = temp_db_dir / "test-product"
        project_path.mkdir()

        store = SQLiteStateStore(project_path)
        store.initialize_product("test-product", "Test")
        store.initialize_feature("001-test", "test-product", "Test Feature")
        store.close()

        result = runner.invoke(app, [
            "recovery",
            "--project", "test-product",
            "--feature", "001-test",
            "--path", str(temp_db_dir),
        ])

        assert result.exit_code == 0
        assert "Recovery Info" in result.output