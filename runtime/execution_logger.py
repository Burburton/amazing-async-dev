"""Execution lifecycle logger for structured event recording."""

from pathlib import Path
from typing import Any

from runtime.execution_event_types import ExecutionEventType
from runtime.sqlite_state_store import SQLiteStateStore


class ExecutionLogger:
    """Logger for execution lifecycle events.
    
    Provides a simple interface for logging workflow events to SQLite,
    supporting recovery diagnosis and operational debugging.
    """

    def __init__(self, project_path: Path | None = None):
        self.project_path = project_path or Path("projects/demo-product")
        self._store: SQLiteStateStore | None = None

    def _get_store(self) -> SQLiteStateStore:
        if self._store is None:
            self._store = SQLiteStateStore(self.project_path)
        return self._store

    def log_event(
        self,
        event_type: ExecutionEventType,
        feature_id: str | None = None,
        product_id: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> None:
        """Log an execution lifecycle event.
        
        Args:
            event_type: Type of event from ExecutionEventType enum
            feature_id: Feature ID (optional, will infer from runstate)
            product_id: Product ID (optional, will infer from runstate)
            event_data: Additional event metadata
        """
        store = self._get_store()
        
        data = event_data or {}
        data["event_type_enum"] = event_type.value
        
        store.log_event(
            event_type=event_type.value,
            feature_id=feature_id,
            product_id=product_id,
            event_data=data,
        )

    def log_transition(
        self,
        from_phase: str,
        to_phase: str,
        feature_id: str | None = None,
        product_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Log a phase transition.
        
        Args:
            from_phase: Phase before transition
            to_phase: Phase after transition
            feature_id: Feature ID (optional)
            product_id: Product ID (optional)
            reason: Reason for transition
        """
        store = self._get_store()
        store.log_transition(
            from_phase=from_phase,
            to_phase=to_phase,
            feature_id=feature_id,
            product_id=product_id,
            reason=reason,
        )

    def close(self) -> None:
        """Close the underlying store connection."""
        if self._store:
            self._store.close()
            self._store = None


def get_logger(project_path: Path | None = None) -> ExecutionLogger:
    """Get an execution logger instance."""
    return ExecutionLogger(project_path)