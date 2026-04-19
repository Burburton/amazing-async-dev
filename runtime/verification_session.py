"""Verification Session Tracking - Feature 059.

Tracks browser verification sessions with timeout enforcement,
ensuring AI agents complete verification workflows instead of
stopping at "server started".
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
import json


class VerificationSessionStatus(str, Enum):
    """Status of verification session."""
    PENDING = "pending"
    SERVER_STARTED = "server_started"
    VERIFICATION_IN_PROGRESS = "verification_in_progress"
    COMPLETE = "complete"
    TIMEOUT = "timeout"
    EXCEPTION = "exception"


class TimeoutAction(str, Enum):
    """Action taken on timeout."""
    RECORD_EXCEPTION = "record_exception"
    FORCE_STOP = "force_stop"
    RETRY = "retry"


@dataclass
class VerificationSession:
    """Active browser verification session with timeout tracking."""
    session_id: str
    project_id: str
    started_at: datetime
    timeout_seconds: int = 120
    status: VerificationSessionStatus = VerificationSessionStatus.PENDING
    dev_server_url: str | None = None
    dev_server_port: int | None = None
    dev_server_pid: int | None = None
    verification_attempted: bool = False
    verification_complete: bool = False
    attempts: int = 0
    max_attempts: int = 3
    last_attempt_at: datetime | None = None
    exception_reason: str | None = None
    exception_details: str | None = None
    result: dict[str, Any] | None = None
    finished_at: datetime | None = None


@dataclass
class VerificationReminder:
    """Reminder to AI agent about pending verification."""
    session_id: str
    elapsed_seconds: float
    remaining_seconds: float
    dev_server_url: str | None
    must_action: str
    blocking_reason: str | None = None


DEFAULT_TIMEOUT = 120
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5


class VerificationSessionManager:
    """Manager for verification sessions with timeout enforcement."""

    SESSIONS_FILE = ".runtime/verification-sessions.json"

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.sessions_path = project_path / self.SESSIONS_FILE
        self.active_session: VerificationSession | None = None
        self._load_active_session()

    def _load_active_session(self) -> None:
        """Load active session from file if exists."""
        if not self.sessions_path.exists():
            return

        try:
            with open(self.sessions_path, encoding="utf-8") as f:
                data = json.load(f)

            if data.get("active_session"):
                session_data = data["active_session"]
                self.active_session = VerificationSession(
                    session_id=session_data.get("session_id", ""),
                    project_id=session_data.get("project_id", ""),
                    started_at=datetime.fromisoformat(session_data["started_at"]),
                    timeout_seconds=session_data.get("timeout_seconds", DEFAULT_TIMEOUT),
                    status=VerificationSessionStatus(session_data.get("status", "pending")),
                    dev_server_url=session_data.get("dev_server_url"),
                    dev_server_port=session_data.get("dev_server_port"),
                    dev_server_pid=session_data.get("dev_server_pid"),
                    verification_attempted=session_data.get("verification_attempted", False),
                    verification_complete=session_data.get("verification_complete", False),
                    attempts=session_data.get("attempts", 0),
                    max_attempts=session_data.get("max_attempts", DEFAULT_MAX_ATTEMPTS),
                    last_attempt_at=datetime.fromisoformat(session_data["last_attempt_at"]) if session_data.get("last_attempt_at") else None,
                    exception_reason=session_data.get("exception_reason"),
                    exception_details=session_data.get("exception_details"),
                    result=session_data.get("result"),
                    finished_at=datetime.fromisoformat(session_data["finished_at"]) if session_data.get("finished_at") else None,
                )
        except Exception:
            self.active_session = None

    def _save_session(self) -> None:
        """Save active session to file."""
        if not self.active_session:
            return

        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)

        session_data = {
            "session_id": self.active_session.session_id,
            "project_id": self.active_session.project_id,
            "started_at": self.active_session.started_at.isoformat(),
            "timeout_seconds": self.active_session.timeout_seconds,
            "status": self.active_session.status.value,
            "dev_server_url": self.active_session.dev_server_url,
            "dev_server_port": self.active_session.dev_server_port,
            "dev_server_pid": self.active_session.dev_server_pid,
            "verification_attempted": self.active_session.verification_attempted,
            "verification_complete": self.active_session.verification_complete,
            "attempts": self.active_session.attempts,
            "max_attempts": self.active_session.max_attempts,
            "last_attempt_at": self.active_session.last_attempt_at.isoformat() if self.active_session.last_attempt_at else None,
            "exception_reason": self.active_session.exception_reason,
            "exception_details": self.active_session.exception_details,
            "result": self.active_session.result,
            "finished_at": self.active_session.finished_at.isoformat() if self.active_session.finished_at else None,
        }

        with open(self.sessions_path, "w", encoding="utf-8") as f:
            json.dump({"active_session": session_data, "updated_at": datetime.now().isoformat()}, f)

    def create_session(
        self,
        project_id: str,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ) -> VerificationSession:
        """Create new verification session."""
        now = datetime.now()
        session_id = f"vs-{now.strftime('%Y%m%d%H%M%S')}-{project_id}"

        self.active_session = VerificationSession(
            session_id=session_id,
            project_id=project_id,
            started_at=now,
            timeout_seconds=timeout_seconds,
            status=VerificationSessionStatus.PENDING,
        )

        self._save_session()
        return self.active_session

    def start_dev_server(self, url: str, port: int, pid: int) -> None:
        """Record dev server startup."""
        if not self.active_session:
            return

        self.active_session.dev_server_url = url
        self.active_session.dev_server_port = port
        self.active_session.dev_server_pid = pid
        self.active_session.status = VerificationSessionStatus.SERVER_STARTED
        self._save_session()

    def start_verification(self) -> None:
        """Record verification attempt started."""
        if not self.active_session:
            return

        self.active_session.verification_attempted = True
        self.active_session.attempts += 1
        self.active_session.last_attempt_at = datetime.now()
        self.active_session.status = VerificationSessionStatus.VERIFICATION_IN_PROGRESS
        self._save_session()

    def complete_verification(self, result: dict[str, Any]) -> None:
        """Mark verification as complete with result."""
        if not self.active_session:
            return

        self.active_session.verification_complete = True
        self.active_session.result = result
        self.active_session.status = VerificationSessionStatus.COMPLETE
        self.active_session.finished_at = datetime.now()
        self._save_session()

    def record_exception(self, reason: str, details: str) -> None:
        """Record exception that blocked verification."""
        if not self.active_session:
            return

        self.active_session.exception_reason = reason
        self.active_session.exception_details = details
        self.active_session.status = VerificationSessionStatus.EXCEPTION
        self.active_session.finished_at = datetime.now()
        self._save_session()

    def check_timeout(self) -> bool:
        """Check if session has exceeded timeout."""
        if not self.active_session:
            return False

        elapsed = (datetime.now() - self.active_session.started_at).total_seconds()
        return elapsed > self.active_session.timeout_seconds

    def get_elapsed_seconds(self) -> float:
        """Get elapsed time since session started."""
        if not self.active_session:
            return 0.0

        return (datetime.now() - self.active_session.started_at).total_seconds()

    def get_remaining_seconds(self) -> float:
        """Get remaining time before timeout."""
        if not self.active_session:
            return 0.0

        elapsed = self.get_elapsed_seconds()
        return max(0, self.active_session.timeout_seconds - elapsed)

    def get_reminder(self) -> VerificationReminder | None:
        """Generate reminder for pending verification."""
        if not self.active_session:
            return None

        if self.active_session.verification_complete:
            return None

        elapsed = self.get_elapsed_seconds()
        remaining = self.get_remaining_seconds()

        must_action = "Continue browser verification"
        if self.active_session.status == VerificationSessionStatus.SERVER_STARTED:
            must_action = "Run browser verification: asyncdev browser-test --url {url}"
        elif self.active_session.status == VerificationSessionStatus.VERIFICATION_IN_PROGRESS:
            must_action = "Complete verification and record result"

        blocking_reason = None
        if self.active_session.attempts >= self.active_session.max_attempts:
            blocking_reason = "Max attempts reached"
        elif self.check_timeout():
            blocking_reason = "Timeout exceeded"

        return VerificationReminder(
            session_id=self.active_session.session_id,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining,
            dev_server_url=self.active_session.dev_server_url,
            must_action=must_action,
            blocking_reason=blocking_reason,
        )

    def enforce_timeout(self) -> dict[str, Any]:
        """Enforce timeout if exceeded, return result dict."""
        if not self.active_session:
            return {"status": "no_session"}

        if not self.check_timeout():
            return {"status": "pending", "timeout_not_reached": True}

        if not self.active_session.verification_complete:
            self.active_session.status = VerificationSessionStatus.TIMEOUT
            self.active_session.exception_reason = "verification_timeout"
            self.active_session.exception_details = (
                f"Dev server started at {self.active_session.started_at.isoformat()} "
                f"but no verification completed within {self.active_session.timeout_seconds}s"
            )
            self.active_session.finished_at = datetime.now()
            self._save_session()

        return {
            "status": "timeout",
            "executed": False,
            "exception_reason": self.active_session.exception_reason,
            "exception_details": self.active_session.exception_details,
            "elapsed_seconds": self.get_elapsed_seconds(),
        }

    def get_session_status(self) -> dict[str, Any]:
        """Get current session status for ExecutionResult."""
        if not self.active_session:
            return {"active": False}

        return {
            "active": True,
            "session_id": self.active_session.session_id,
            "status": self.active_session.status.value,
            "elapsed_seconds": self.get_elapsed_seconds(),
            "remaining_seconds": self.get_remaining_seconds(),
            "dev_server_url": self.active_session.dev_server_url,
            "verification_attempted": self.active_session.verification_attempted,
            "verification_complete": self.active_session.verification_complete,
            "attempts": self.active_session.attempts,
        }

    def clear_session(self) -> None:
        """Clear active session after completion."""
        if self.sessions_path.exists():
            self.sessions_path.unlink()
        self.active_session = None


def format_reminder(reminder: VerificationReminder) -> str:
    """Format reminder for display."""
    lines = []

    lines.append("[SYSTEM REMINDER - VERIFICATION PENDING]")
    lines.append("")
    lines.append(f"Dev server running at: {reminder.dev_server_url or 'unknown'}")
    lines.append(f"Elapsed: {reminder.elapsed_seconds:.0f}s")
    lines.append(f"Remaining: {reminder.remaining_seconds:.0f}s")
    lines.append("")
    lines.append("YOU MUST:")
    lines.append(f"  1. {reminder.must_action}")
    lines.append("  2. OR record exception if blocked")
    lines.append("  3. DO NOT stop until verification_complete OR timeout")
    lines.append("")

    if reminder.blocking_reason:
        lines.append(f"Blocking: {reminder.blocking_reason}")
        lines.append("Action: Record exception in ExecutionResult")
    else:
        lines.append("Current blocking: None detected")
        lines.append("Recommended action: Continue with browser verification")

    return "\n".join(lines)


def generate_session_id(project_id: str) -> str:
    """Generate unique session ID."""
    now = datetime.now()
    return f"vs-{now.strftime('%Y%m%d%H%M%S')}-{project_id}"