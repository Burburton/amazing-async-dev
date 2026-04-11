"""SQLite adapter for structured state persistence."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


DB_FILENAME = "amazing_async_dev.db"


class SQLiteAdapter:
    """SQLite persistence adapter for state and events."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path(".runtime") / DB_FILENAME

        self.db_path = Path(db_path)
        self._ensure_db_dir()
        self._connection: sqlite3.Connection | None = None

    def _ensure_db_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            self._initialize_schema()
        return self._connection

    def _initialize_schema(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS features (
                feature_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                name TEXT NOT NULL,
                current_phase TEXT NOT NULL,
                active_task TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS runstate_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                active_task TEXT,
                task_queue TEXT,
                completed_outputs TEXT,
                blocked_items TEXT,
                decisions_needed TEXT,
                last_action TEXT,
                next_recommended_action TEXT,
                snapshot_at TEXT NOT NULL,
                FOREIGN KEY (feature_id) REFERENCES features(feature_id)
            );

            CREATE TABLE IF NOT EXISTS execution_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                occurred_at TEXT NOT NULL,
                FOREIGN KEY (feature_id) REFERENCES features(feature_id)
            );

            CREATE TABLE IF NOT EXISTS lifecycle_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                from_phase TEXT NOT NULL,
                to_phase TEXT NOT NULL,
                reason TEXT,
                transitioned_at TEXT NOT NULL,
                FOREIGN KEY (feature_id) REFERENCES features(feature_id)
            );

            CREATE TABLE IF NOT EXISTS archive_records (
                feature_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                archived_at TEXT NOT NULL,
                final_status TEXT NOT NULL,
                archive_path TEXT NOT NULL,
                FOREIGN KEY (feature_id) REFERENCES features(feature_id)
            );

            CREATE INDEX IF NOT EXISTS idx_events_feature ON execution_events(feature_id);
            CREATE INDEX IF NOT EXISTS idx_events_time ON execution_events(occurred_at);
            CREATE INDEX IF NOT EXISTS idx_transitions_feature ON lifecycle_transitions(feature_id);
            CREATE INDEX IF NOT EXISTS idx_snapshots_feature ON runstate_snapshots(feature_id);
        """)
        conn.commit()

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def insert_product(self, product_id: str, name: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT OR REPLACE INTO products (product_id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (product_id, name, now, now),
        )
        conn.commit()

    def insert_feature(
        self,
        feature_id: str,
        product_id: str,
        name: str,
        current_phase: str = "planning",
        active_task: str | None = None,
    ) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT OR REPLACE INTO features (feature_id, product_id, name, current_phase, active_task, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (feature_id, product_id, name, current_phase, active_task, now, now),
        )
        conn.commit()

    def update_feature_phase(
        self,
        feature_id: str,
        new_phase: str,
        active_task: str | None = None,
    ) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE features SET current_phase = ?, active_task = ?, updated_at = ? WHERE feature_id = ?",
            (new_phase, active_task, now, feature_id),
        )
        conn.commit()

    def get_feature(self, feature_id: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM features WHERE feature_id = ?", (feature_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_active_feature(self, product_id: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM features WHERE product_id = ? AND current_phase NOT IN ('archived') ORDER BY updated_at DESC LIMIT 1",
            (product_id,),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def save_runstate_snapshot(
        self,
        runstate: dict[str, Any],
        feature_id: str,
        product_id: str,
    ) -> None:
        import json

        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO runstate_snapshots
            (feature_id, product_id, phase, active_task, task_queue, completed_outputs, blocked_items, decisions_needed, last_action, next_recommended_action, snapshot_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feature_id,
                product_id,
                runstate.get("current_phase", "planning"),
                runstate.get("active_task", ""),
                json.dumps(runstate.get("task_queue", [])),
                json.dumps(runstate.get("completed_outputs", [])),
                json.dumps(runstate.get("blocked_items", [])),
                json.dumps(runstate.get("decisions_needed", [])),
                runstate.get("last_action", ""),
                runstate.get("next_recommended_action", ""),
                now,
            ),
        )
        conn.commit()

    def get_latest_snapshot(self, feature_id: str) -> dict[str, Any] | None:
        import json

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM runstate_snapshots WHERE feature_id = ? ORDER BY snapshot_at DESC LIMIT 1",
            (feature_id,),
        )
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["task_queue"] = json.loads(data.get("task_queue", "[]"))
            data["completed_outputs"] = json.loads(data.get("completed_outputs", "[]"))
            data["blocked_items"] = json.loads(data.get("blocked_items", "[]"))
            data["decisions_needed"] = json.loads(data.get("decisions_needed", "[]"))
            return data
        return None

    def log_event(
        self,
        feature_id: str,
        product_id: str,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> None:
        import json

        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO execution_events (feature_id, product_id, event_type, event_data, occurred_at) VALUES (?, ?, ?, ?, ?)",
            (feature_id, product_id, event_type, json.dumps(event_data or {}), now),
        )
        conn.commit()

    def get_recent_events(
        self,
        feature_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        import json

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM execution_events WHERE feature_id = ? ORDER BY occurred_at DESC LIMIT ?",
            (feature_id, limit),
        )
        rows = cursor.fetchall()
        events = []
        for row in rows:
            data = dict(row)
            data["event_data"] = json.loads(data.get("event_data", "{}"))
            events.append(data)
        return events

    def log_transition(
        self,
        feature_id: str,
        product_id: str,
        from_phase: str,
        to_phase: str,
        reason: str | None = None,
    ) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO lifecycle_transitions (feature_id, product_id, from_phase, to_phase, reason, transitioned_at) VALUES (?, ?, ?, ?, ?, ?)",
            (feature_id, product_id, from_phase, to_phase, reason, now),
        )
        conn.commit()

    def get_transitions(self, feature_id: str) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM lifecycle_transitions WHERE feature_id = ? ORDER BY transitioned_at DESC",
            (feature_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_archive_record(
        self,
        feature_id: str,
        product_id: str,
        final_status: str,
        archive_path: str,
    ) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            "INSERT OR REPLACE INTO archive_records (feature_id, product_id, archived_at, final_status, archive_path) VALUES (?, ?, ?, ?, ?)",
            (feature_id, product_id, now, final_status, archive_path),
        )
        conn.commit()

    def get_archive_record(self, feature_id: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM archive_records WHERE feature_id = ?", (feature_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def list_archived_features(self, product_id: str) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM archive_records WHERE product_id = ? ORDER BY archived_at DESC",
            (product_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_recovery_info(self, feature_id: str) -> dict[str, Any]:
        snapshot = self.get_latest_snapshot(feature_id)
        events = self.get_recent_events(feature_id, limit=10)
        transitions = self.get_transitions(feature_id)

        return {
            "latest_snapshot": snapshot,
            "recent_events": events,
            "transitions": transitions,
            "can_resume": snapshot is not None and snapshot.get("phase") not in ("archived"),
        }

    def list_products(self) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def list_features(self, product_id: str) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM features WHERE product_id = ? ORDER BY updated_at DESC",
            (product_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]