"""SQLite-backed state store for structured persistence."""

from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.adapters.sqlite_adapter import SQLiteAdapter
from runtime.state_store import StateStore


class SQLiteStateStore:
    """SQLite-backed state store that mirrors StateStore interface."""

    def __init__(self, project_path: Path | None = None, db_path: Path | None = None):
        self.project_path = project_path or Path("projects/demo-product")
        self.db_path = db_path or self.project_path / ".runtime" / "amazing_async_dev.db"
        self.sqlite = SQLiteAdapter(self.db_path)
        self.file_store = StateStore(self.project_path)

    def initialize_product(self, product_id: str, name: str) -> None:
        self.sqlite.insert_product(product_id, name)

    def initialize_feature(
        self,
        feature_id: str,
        product_id: str,
        name: str,
        phase: str = "planning",
    ) -> None:
        self.sqlite.insert_feature(feature_id, product_id, name, phase)
        self.sqlite.log_event(feature_id, product_id, "new-feature", {"name": name})

    def load_runstate(self) -> dict[str, Any] | None:
        return self.file_store.load_runstate()

    def save_runstate(self, runstate: dict[str, Any]) -> None:
        self.file_store.save_runstate(runstate)

        feature_id = runstate.get("feature_id", "")
        product_id = runstate.get("project_id", "")

        if feature_id and product_id:
            self.sqlite.save_runstate_snapshot(runstate, feature_id, product_id)
            self.sqlite.update_feature_phase(
                feature_id,
                runstate.get("current_phase", "planning"),
                runstate.get("active_task"),
            )

    def log_event(
        self,
        event_type: str,
        feature_id: str | None = None,
        product_id: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> None:
        runstate = self.load_runstate()
        fid = feature_id or runstate.get("feature_id", "") if runstate else ""
        pid = product_id or runstate.get("project_id", "") if runstate else ""

        if fid and pid:
            self.sqlite.log_event(fid, pid, event_type, event_data)

    def log_transition(
        self,
        from_phase: str,
        to_phase: str,
        feature_id: str | None = None,
        product_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        runstate = self.load_runstate()
        fid = feature_id or runstate.get("feature_id", "") if runstate else ""
        pid = product_id or runstate.get("project_id", "") if runstate else ""

        if fid and pid:
            self.sqlite.log_transition(fid, pid, from_phase, to_phase, reason)
            self.sqlite.log_event(fid, pid, "phase-transition", {"from": from_phase, "to": to_phase, "reason": reason})

    def get_recovery_info(self, feature_id: str | None = None) -> dict[str, Any]:
        fid = feature_id
        if not fid:
            runstate = self.load_runstate()
            fid = runstate.get("feature_id", "") if runstate else ""

        if fid:
            return self.sqlite.get_recovery_info(fid)
        return {"can_resume": False, "latest_snapshot": None, "recent_events": [], "transitions": []}

    def get_latest_snapshot(self, feature_id: str) -> dict[str, Any] | None:
        return self.sqlite.get_latest_snapshot(feature_id)

    def get_recent_events(self, feature_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return self.sqlite.get_recent_events(feature_id, limit)

    def get_transitions(self, feature_id: str) -> list[dict[str, Any]]:
        return self.sqlite.get_transitions(feature_id)

    def get_active_feature(self, product_id: str) -> dict[str, Any] | None:
        return self.sqlite.get_active_feature(product_id)

    def list_features(self, product_id: str) -> list[dict[str, Any]]:
        return self.sqlite.list_features(product_id)

    def archive_feature(
        self,
        feature_id: str,
        product_id: str,
        final_status: str,
        archive_path: str,
    ) -> None:
        self.sqlite.update_feature_phase(feature_id, "archived")
        self.sqlite.insert_archive_record(feature_id, product_id, final_status, archive_path)
        self.sqlite.log_event(feature_id, product_id, "archived", {"status": final_status})
        self.sqlite.log_transition("completed", "archived", feature_id, product_id, "Feature archived")

    def load_execution_pack(self, execution_id: str) -> dict[str, Any] | None:
        return self.file_store.load_execution_pack(execution_id)

    def save_execution_pack(self, execution_pack: dict[str, Any]) -> None:
        self.file_store.save_execution_pack(execution_pack)

        feature_id = execution_pack.get("feature_id", "")
        product_id = ""
        runstate = self.load_runstate()
        if runstate:
            product_id = runstate.get("project_id", "")

        if feature_id and product_id:
            self.sqlite.log_event(
                feature_id, product_id, "execution-pack-created", {"execution_id": execution_pack.get("execution_id")}
            )

    def load_execution_result(self, execution_id: str) -> dict[str, Any] | None:
        return self.file_store.load_execution_result(execution_id)

    def save_execution_result(self, execution_result: dict[str, Any]) -> None:
        self.file_store.save_execution_result(execution_result)

        feature_id = ""
        product_id = ""
        runstate = self.load_runstate()
        if runstate:
            feature_id = runstate.get("feature_id", "")
            product_id = runstate.get("project_id", "")

        if feature_id and product_id:
            self.sqlite.log_event(
                feature_id, product_id, "execution-result", {"execution_id": execution_result.get("execution_id"), "status": execution_result.get("status")}
            )

    def load_daily_review_pack(self, date: str) -> dict[str, Any] | None:
        return self.file_store.load_daily_review_pack(date)

    def save_daily_review_pack(self, review_pack: dict[str, Any]) -> None:
        self.file_store.save_daily_review_pack(review_pack)

        feature_id = ""
        product_id = ""
        runstate = self.load_runstate()
        if runstate:
            feature_id = runstate.get("feature_id", "")
            product_id = runstate.get("project_id", "")

        if feature_id and product_id:
            self.sqlite.log_event(
                feature_id, product_id, "daily-review-pack", {"date": review_pack.get("date")}
            )

    def close(self) -> None:
        self.sqlite.close()


def get_sqlite_state_store(project_path: Path | None = None) -> SQLiteStateStore:
    return SQLiteStateStore(project_path)