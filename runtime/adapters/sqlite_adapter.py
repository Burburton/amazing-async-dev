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

            CREATE TABLE IF NOT EXISTS workflow_feedback (
                feedback_id TEXT PRIMARY KEY,
                problem_domain TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                detected_by TEXT NOT NULL,
                detected_in TEXT NOT NULL,
                product_id TEXT,
                feature_id TEXT,
                description TEXT NOT NULL,
                context_summary TEXT NOT NULL,
                suspected_problem TEXT,
                temporary_fix TEXT,
                reproduction_hint TEXT,
                command_context TEXT,
                expected_behavior TEXT,
                actual_behavior TEXT,
                self_corrected INTEGER NOT NULL DEFAULT 0,
                requires_followup INTEGER NOT NULL DEFAULT 0,
                confidence TEXT,
                escalation_recommendation TEXT,
                triage_note TEXT,
                triaged_at TEXT,
                promotion_status TEXT DEFAULT 'none',
                promotion_id TEXT,
                resolution TEXT DEFAULT 'none',
                status TEXT DEFAULT 'open',
                priority TEXT,
                detected_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS promoted_feedback (
                promotion_id TEXT PRIMARY KEY,
                source_feedback_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                promotion_reason TEXT DEFAULT 'system_bug',
                promotion_note TEXT,
                source_problem_domain TEXT,
                source_confidence TEXT,
                source_escalation_recommendation TEXT,
                source_issue_type TEXT,
                source_description TEXT,
                followup_status TEXT DEFAULT 'open',
                candidate_feature_followup TEXT,
                artifact_type TEXT,
                artifact_path TEXT,
                promoted_at TEXT NOT NULL,
                addressed_at TEXT,
                addressed_note TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_events_feature ON execution_events(feature_id);
            CREATE INDEX IF NOT EXISTS idx_events_time ON execution_events(occurred_at);
            CREATE INDEX IF NOT EXISTS idx_transitions_feature ON lifecycle_transitions(feature_id);
            CREATE INDEX IF NOT EXISTS idx_snapshots_feature ON runstate_snapshots(feature_id);
            CREATE INDEX IF NOT EXISTS idx_feedback_date ON workflow_feedback(detected_at);
            CREATE INDEX IF NOT EXISTS idx_feedback_product ON workflow_feedback(product_id);
            CREATE INDEX IF NOT EXISTS idx_feedback_domain ON workflow_feedback(problem_domain);
            CREATE INDEX IF NOT EXISTS idx_feedback_followup ON workflow_feedback(requires_followup);
            CREATE INDEX IF NOT EXISTS idx_feedback_escalation ON workflow_feedback(escalation_recommendation);
            CREATE INDEX IF NOT EXISTS idx_feedback_promotion ON workflow_feedback(promotion_status);
            CREATE INDEX IF NOT EXISTS idx_promotion_feedback ON promoted_feedback(source_feedback_id);
            CREATE INDEX IF NOT EXISTS idx_promotion_status ON promoted_feedback(followup_status);
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

    def save_workflow_feedback(self, feedback: dict[str, Any]) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO workflow_feedback
            (feedback_id, problem_domain, issue_type, detected_by, detected_in, product_id, feature_id,
             description, context_summary, suspected_problem, temporary_fix, reproduction_hint,
             command_context, expected_behavior, actual_behavior,
             self_corrected, requires_followup, confidence, escalation_recommendation, triage_note, triaged_at,
             promotion_status, promotion_id, resolution, status, priority, detected_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback.get("feedback_id"),
                feedback.get("problem_domain"),
                feedback.get("issue_type"),
                feedback.get("detected_by"),
                feedback.get("detected_in"),
                feedback.get("product_id"),
                feedback.get("feature_id"),
                feedback.get("description"),
                feedback.get("context_summary"),
                feedback.get("suspected_problem"),
                feedback.get("temporary_fix"),
                feedback.get("reproduction_hint"),
                feedback.get("command_context"),
                feedback.get("expected_behavior"),
                feedback.get("actual_behavior"),
                1 if feedback.get("self_corrected") else 0,
                1 if feedback.get("requires_followup") else 0,
                feedback.get("confidence"),
                feedback.get("escalation_recommendation"),
                feedback.get("triage_note"),
                feedback.get("triaged_at"),
                feedback.get("promotion_status", "none"),
                feedback.get("promotion_id"),
                feedback.get("resolution", "none"),
                feedback.get("status", "open"),
                feedback.get("priority"),
                feedback.get("detected_at"),
                now,
                now,
            ),
        )
        conn.commit()

    def load_workflow_feedback(self, feedback_id: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflow_feedback WHERE feedback_id = ?", (feedback_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["self_corrected"] = bool(data.get("self_corrected", 0))
            data["requires_followup"] = bool(data.get("requires_followup", 0))
            return data
        return None

    def list_workflow_feedback(
        self,
        problem_domain: str | None = None,
        product_id: str | None = None,
        issue_type: str | None = None,
        confidence: str | None = None,
        escalation_recommendation: str | None = None,
        requires_followup: bool | None = None,
        self_corrected: bool | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM workflow_feedback WHERE 1=1"
        params: list[Any] = []

        if problem_domain:
            query += " AND problem_domain = ?"
            params.append(problem_domain)
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        if issue_type:
            query += " AND issue_type = ?"
            params.append(issue_type)
        if confidence:
            query += " AND confidence = ?"
            params.append(confidence)
        if escalation_recommendation:
            query += " AND escalation_recommendation = ?"
            params.append(escalation_recommendation)
        if requires_followup is not None:
            query += " AND requires_followup = ?"
            params.append(1 if requires_followup else 0)
        if self_corrected is not None:
            query += " AND self_corrected = ?"
            params.append(1 if self_corrected else 0)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY detected_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            data["self_corrected"] = bool(data.get("self_corrected", 0))
            data["requires_followup"] = bool(data.get("requires_followup", 0))
            results.append(data)
        return results

    def count_workflow_feedback_by_date(self, date_str: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM workflow_feedback WHERE feedback_id LIKE ?",
            (f"wf-{date_str}-%",),
        )
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_workflow_feedback_by_date(
        self,
        date: str,
        product_id: str | None = None,
        problem_domain: str | None = None,
    ) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM workflow_feedback WHERE detected_at LIKE ?"
        params: list[Any] = [f"{date}%"]

        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        if problem_domain:
            query += " AND problem_domain = ?"
            params.append(problem_domain)

        query += " ORDER BY detected_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            data = dict(row)
            data["self_corrected"] = bool(data.get("self_corrected", 0))
            data["requires_followup"] = bool(data.get("requires_followup", 0))
            results.append(data)
        return results

    def save_promotion(self, promotion: dict[str, Any]) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO promoted_feedback
            (promotion_id, source_feedback_id, summary, promotion_reason, promotion_note,
             source_problem_domain, source_confidence, source_escalation_recommendation,
             source_issue_type, source_description, followup_status, candidate_feature_followup,
             artifact_type, artifact_path, promoted_at, addressed_at, addressed_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                promotion.get("promotion_id"),
                promotion.get("source_feedback_id"),
                promotion.get("summary"),
                promotion.get("promotion_reason", "system_bug"),
                promotion.get("promotion_note"),
                promotion.get("source_problem_domain"),
                promotion.get("source_confidence"),
                promotion.get("source_escalation_recommendation"),
                promotion.get("source_issue_type"),
                promotion.get("source_description"),
                promotion.get("followup_status", "open"),
                promotion.get("candidate_feature_followup"),
                promotion.get("artifact_reference", {}).get("artifact_type"),
                promotion.get("artifact_reference", {}).get("artifact_path"),
                promotion.get("promoted_at", now),
                promotion.get("addressed_at"),
                promotion.get("addressed_note"),
            ),
        )
        conn.commit()

    def load_promotion(self, promotion_id: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM promoted_feedback WHERE promotion_id = ?", (promotion_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def list_promotions(
        self,
        followup_status: str | None = None,
        promotion_reason: str | None = None,
        source_domain: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM promoted_feedback WHERE 1=1"
        params: list[Any] = []

        if followup_status:
            query += " AND followup_status = ?"
            params.append(followup_status)
        if promotion_reason:
            query += " AND promotion_reason = ?"
            params.append(promotion_reason)
        if source_domain:
            query += " AND source_problem_domain = ?"
            params.append(source_domain)

        query += " ORDER BY promoted_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def count_promotions_by_date(self, date_str: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM promoted_feedback WHERE promotion_id LIKE ?",
            (f"promo-{date_str}-%",),
        )
        result = cursor.fetchone()
        return result[0] if result else 0

    def update_feedback_promotion_status(
        self,
        feedback_id: str,
        promotion_status: str,
        promotion_id: str | None = None,
    ) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if promotion_id:
            cursor.execute(
                "UPDATE workflow_feedback SET promotion_status = ?, promotion_id = ?, updated_at = ? WHERE feedback_id = ?",
                (promotion_status, promotion_id, now, feedback_id),
            )
        else:
            cursor.execute(
                "UPDATE workflow_feedback SET promotion_status = ?, updated_at = ? WHERE feedback_id = ?",
                (promotion_status, now, feedback_id),
            )
        conn.commit()