"""Webhook auto-polling module for Feature 058 - Automatic decision continuation.

Polls Cloudflare Worker for pending email replies and automatically
syncs them to RunState, enabling true async human decision channel.
"""

import json
import signal
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class PollingStatus(str, Enum):
    """Status of polling cycle."""
    SUCCESS = "success"
    NO_DECISIONS = "no_decisions"
    ERROR = "error"
    STOPPED = "stopped"


class ReplyType(str, Enum):
    """Type of reply detected."""
    DECISION = "DECISION"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DEFER = "DEFER"
    CONTINUE = "CONTINUE"
    PAUSE = "PAUSE"
    STOP = "STOP"
    UNKNOWN = "UNKNOWN"


@dataclass
class PendingDecision:
    """Decision pending in webhook KV."""
    id: str
    from_email: str
    option: str
    comment: str
    received_at: str
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PollResult:
    """Result of a polling cycle."""
    status: PollingStatus
    decisions_found: int = 0
    decisions_processed: int = 0
    decisions_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    processed_ids: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PollingConfig:
    """Configuration for polling behavior."""
    enabled: bool = True
    interval_seconds: int = 60
    max_retries: int = 3
    retry_backoff: float = 2.0
    timeout_seconds: int = 30
    auto_resume: bool = True


DEFAULT_POLLING_CONFIG = PollingConfig()


def get_polling_config(project_path: Path) -> PollingConfig:
    """Load polling configuration from resend-config.json.

    Args:
        project_path: Project directory path

    Returns:
        PollingConfig with settings
    """
    from runtime.resend_provider import load_resend_config, RESEND_CONFIG_FILE

    config_path = project_path / ".runtime" / "resend-config.json"
    if not config_path.exists():
        config_path = RESEND_CONFIG_FILE

    config = load_resend_config(config_path)
    if not config:
        return DEFAULT_POLLING_CONFIG

    polling = config.get("polling", {})

    return PollingConfig(
        enabled=polling.get("enabled", True),
        interval_seconds=polling.get("interval_seconds", 60),
        max_retries=polling.get("max_retries", 3),
        retry_backoff=polling.get("retry_backoff", 2.0),
        timeout_seconds=polling.get("timeout_seconds", 30),
        auto_resume=polling.get("auto_resume", True),
    )


def poll_pending_decisions(webhook_url: str, timeout: int = 30) -> list[PendingDecision]:
    """Poll webhook for pending decisions.

    Args:
        webhook_url: Webhook base URL
        timeout: Request timeout in seconds

    Returns:
        List of PendingDecision objects
    """
    pending_url = webhook_url.rstrip("/") + "/pending-decisions"

    try:
        req = urllib.request.Request(
            pending_url,
            headers={
                "User-Agent": "async-dev/1.0",
                "Accept": "application/json",
            },
            method="GET",
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))

        if not result.get("ok"):
            return []

        decisions = result.get("decisions", [])

        pending = []
        for d in decisions:
            pending.append(PendingDecision(
                id=d.get("id", ""),
                from_email=d.get("from", ""),
                option=d.get("option", ""),
                comment=d.get("comment", ""),
                received_at=d.get("receivedAt", ""),
                raw_data=d,
            ))

        return pending

    except urllib.error.URLError:
        return []
    except Exception:
        return []


def parse_reply_from_pending(decision: PendingDecision) -> dict[str, Any]:
    """Parse pending decision into reply format.

    Args:
        decision: PendingDecision from webhook

    Returns:
        Reply dict compatible with sync_reply_to_runstate
    """
    option = decision.option.upper() if decision.option else ""
    comment = decision.comment.strip()

    reply_value = ""
    command = ""
    argument = None

    if option in ["A", "B", "C", "D", "E", "F"]:
        reply_value = f"DECISION {option}"
        command = "DECISION"
        argument = option
    elif option in ["APPROVE", "YES", "OK", "CONFIRM"]:
        reply_value = "APPROVE"
        command = "APPROVE"
    elif option in ["REJECT", "NO", "DENY"]:
        reply_value = "REJECT"
        command = "REJECT"
    elif option in ["DEFER", "LATER", "WAIT"]:
        reply_value = "DEFER"
        command = "DEFER"
    elif option in ["CONTINUE", "PROCEED", "GO"]:
        reply_value = "CONTINUE"
        command = "CONTINUE"
    elif option in ["PAUSE", "HOLD", "STOP"]:
        reply_value = "PAUSE"
        command = "PAUSE"
    elif option in ["STOP", "ABORT", "CANCEL"]:
        reply_value = "STOP"
        command = "STOP"
    else:
        reply_value = option or comment.split()[0].upper() if comment else "UNKNOWN"
        command = reply_value

    return {
        "reply_value": reply_value,
        "parsed_result": {
            "command": command,
            "argument": argument,
            "is_valid": command != "UNKNOWN",
        },
        "received_at": decision.received_at,
        "from_email": decision.from_email,
        "comment": comment,
    }


def process_pending_decision(
    project_path: Path,
    decision: PendingDecision,
) -> tuple[bool, str]:
    """Process a single pending decision.

    Args:
        project_path: Project directory
        decision: PendingDecision to process

    Returns:
        Tuple of (success, message)
    """
    from runtime.decision_request_store import DecisionRequestStore, DecisionRequestStatus
    from runtime.decision_sync import sync_reply_to_runstate
    from runtime.state_store import StateStore
    from runtime.resend_provider import load_resend_config, RESEND_CONFIG_FILE

    request_id = decision.id

    store = DecisionRequestStore(project_path)
    request = store.load_request(request_id)

    if not request:
        return False, f"Request not found: {request_id}"

    if request.get("status") == DecisionRequestStatus.RESOLVED.value:
        return False, f"Already resolved: {request_id}"

    reply = parse_reply_from_pending(decision)

    state_store = StateStore(project_path)
    runstate = state_store.load_runstate()

    if not runstate:
        return False, "No RunState found"

    runstate = sync_reply_to_runstate(request_id, reply, runstate)

    state_store.save_runstate(runstate)

    resolution = reply.get("reply_value", "")
    store.mark_resolved(request_id, resolution=resolution)

    config_path = project_path / ".runtime" / "resend-config.json"
    if not config_path.exists():
        config_path = RESEND_CONFIG_FILE

    config = load_resend_config(config_path)
    webhook_url = config.get("webhook_url", "") if config else ""

    if webhook_url:
        clear_url = webhook_url.rstrip("/") + f"/pending-decisions/{request_id}"
        try:
            req = urllib.request.Request(
                clear_url,
                headers={
                    "User-Agent": "async-dev/1.0",
                    "Accept": "application/json",
                },
                method="DELETE",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    return True, f"Processed {request_id}: {resolution}"


def run_poll_cycle(
    project_path: Path,
    webhook_url: str,
    config: PollingConfig,
) -> PollResult:
    """Run a single polling cycle.

    Args:
        project_path: Project directory
        webhook_url: Webhook base URL
        config: Polling configuration

    Returns:
        PollResult with outcome
    """
    result = PollResult(status=PollingStatus.SUCCESS)

    pending = poll_pending_decisions(webhook_url, config.timeout_seconds)
    result.decisions_found = len(pending)

    if not pending:
        result.status = PollingStatus.NO_DECISIONS
        return result

    for decision in pending:
        success, message = process_pending_decision(project_path, decision)

        if success:
            result.decisions_processed += 1
            result.processed_ids.append(decision.id)
        else:
            result.decisions_skipped += 1
            result.errors.append(message)

    return result


def get_reply_type(reply: dict[str, Any]) -> ReplyType:
    """Get reply type from parsed reply.

    Args:
        reply: Parsed reply dict

    Returns:
        ReplyType enum
    """
    command = reply.get("parsed_result", {}).get("command", "")

    try:
        return ReplyType(command.upper())
    except ValueError:
        return ReplyType.UNKNOWN


def should_resume_execution(reply_type: ReplyType) -> bool:
    """Determine if execution should resume after reply.

    Args:
        reply_type: Type of reply

    Returns:
        True if execution should resume
    """
    resume_types = {
        ReplyType.DECISION,
        ReplyType.APPROVE,
        ReplyType.CONTINUE,
    }

    return reply_type in resume_types


def get_continuation_phase(reply_type: ReplyType) -> str:
    """Get phase to set after reply processing.

    Args:
        reply_type: Type of reply

    Returns:
        Phase name string
    """
    phase_map = {
        ReplyType.DECISION: "planning",
        ReplyType.APPROVE: "planning",
        ReplyType.REJECT: "planning",
        ReplyType.DEFER: "planning",
        ReplyType.CONTINUE: "executing",
        ReplyType.PAUSE: "blocked",
        ReplyType.STOP: "stopped",
        ReplyType.UNKNOWN: "executing",
    }

    return phase_map.get(reply_type, "executing")


class PollingDaemon:
    """Daemon for continuous webhook polling."""

    def __init__(
        self,
        project_path: Path,
        webhook_url: str,
        config: PollingConfig = DEFAULT_POLLING_CONFIG,
    ):
        self.project_path = project_path
        self.webhook_url = webhook_url
        self.config = config
        self.running = False
        self.poll_count = 0
        self.last_poll_time: str | None = None
        self._stop_signal_received = False

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_stop_signal)
        signal.signal(signal.SIGTERM, self._handle_stop_signal)

    def _handle_stop_signal(self, signum: int, frame: Any) -> None:
        """Handle stop signal."""
        self._stop_signal_received = True
        self.running = False

    def start(self) -> None:
        """Start polling daemon."""
        self.running = True
        self._setup_signal_handlers()

        while self.running and not self._stop_signal_received:
            self.poll_count += 1
            self.last_poll_time = datetime.now().isoformat()

            result = run_poll_cycle(
                self.project_path,
                self.webhook_url,
                self.config,
            )

            if result.decisions_processed > 0:
                pass

            if not self.running:
                break

            time.sleep(self.config.interval_seconds)

    def stop(self) -> None:
        """Stop polling daemon."""
        self.running = False

    def run_once(self) -> PollResult:
        """Run a single poll cycle and return result."""
        self.poll_count += 1
        self.last_poll_time = datetime.now().isoformat()

        return run_poll_cycle(
            self.project_path,
            self.webhook_url,
            self.config,
        )

    def get_status(self) -> dict[str, Any]:
        """Get daemon status."""
        return {
            "running": self.running,
            "poll_count": self.poll_count,
            "last_poll_time": self.last_poll_time,
            "interval_seconds": self.config.interval_seconds,
            "auto_resume": self.config.auto_resume,
        }


def listen_for_decisions(
    project_path: Path,
    interval: int = 60,
    once: bool = False,
) -> PollResult | None:
    """Listen for pending decisions.

    Args:
        project_path: Project directory
        interval: Polling interval in seconds
        once: Run single cycle only

    Returns:
        PollResult if once=True, None for continuous mode
    """
    from runtime.resend_provider import load_resend_config, RESEND_CONFIG_FILE

    config_path = project_path / ".runtime" / "resend-config.json"
    if not config_path.exists():
        config_path = RESEND_CONFIG_FILE

    config = load_resend_config(config_path)
    if not config:
        return PollResult(
            status=PollingStatus.ERROR,
            errors=["No resend config found"],
        )

    webhook_url = config.get("webhook_url", "")
    if not webhook_url:
        return PollResult(
            status=PollingStatus.ERROR,
            errors=["No webhook URL configured"],
        )

    polling_config = PollingConfig(interval_seconds=interval)

    if once:
        daemon = PollingDaemon(project_path, webhook_url, polling_config)
        return daemon.run_once()

    daemon = PollingDaemon(project_path, webhook_url, polling_config)
    daemon.start()

    return None


def format_poll_result(result: PollResult) -> str:
    """Format poll result for display.

    Args:
        result: PollResult to format

    Returns:
        Formatted string
    """
    lines = []

    lines.append(f"## Poll Result [{result.timestamp}]")
    lines.append(f"**Status:** {result.status.value}")
    lines.append(f"**Found:** {result.decisions_found}")
    lines.append(f"**Processed:** {result.decisions_processed}")
    lines.append(f"**Skipped:** {result.decisions_skipped}")

    if result.processed_ids:
        lines.append("**Processed IDs:**")
        for id in result.processed_ids:
            lines.append(f"  - {id}")

    if result.errors:
        lines.append("**Errors:**")
        for err in result.errors:
            lines.append(f"  - {err}")

    return "\n".join(lines)