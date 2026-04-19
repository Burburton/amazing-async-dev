"""Channel adapter abstraction for Feature 052 - Future Adapter Readiness.

Provides abstract base for decision/report channels, allowing future
extensions to Slack, Telegram, mobile push, etc., while preserving
email as the canonical first implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ChannelType(str, Enum):
    """Supported channel types."""
    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    PUSH = "push"
    CONSOLE = "console"


@dataclass
class ChannelConfig:
    """Configuration for a decision/report channel."""
    channel_type: ChannelType = ChannelType.EMAIL
    enabled: bool = True
    priority: int = 1
    config_path: Path | None = None
    extra_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelMessage:
    """Message to send through channel."""
    message_id: str
    message_type: str  # decision_request, status_report, digest, blocker
    subject: str
    body: str
    recipient: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ChannelResult:
    """Result of channel send operation."""
    success: bool
    channel_type: ChannelType
    message_id: str | None = None
    error_message: str | None = None
    provider_response: dict[str, Any] = field(default_factory=dict)
    sent_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ChannelAdapter(ABC):
    """Abstract base class for decision/report channels.

    This abstraction allows future channels (Slack, Telegram, etc.)
    to be added without changing core decision/report artifacts.
    Email remains the canonical first implementation.
    """

    @abstractmethod
    def get_channel_type(self) -> ChannelType:
        """Return the channel type."""
        pass

    @abstractmethod
    def send_message(self, message: ChannelMessage) -> ChannelResult:
        """Send a message through this channel.

        Args:
            message: ChannelMessage to send

        Returns:
            ChannelResult with outcome
        """
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate channel configuration.

        Returns:
            Tuple of (is_valid, issues_list)
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Get channel status (enabled, healthy, etc).

        Returns:
            Dict with status info
        """
        pass


class ChannelRegistry:
    """Registry for available channel adapters.

    Allows runtime registration of new channel types.
    Email is registered by default.
    """

    _adapters: dict[ChannelType, type[ChannelAdapter]] = {}

    @classmethod
    def register(cls, channel_type: ChannelType, adapter_class: type[ChannelAdapter]) -> None:
        """Register a channel adapter class.

        Args:
            channel_type: Channel type
            adapter_class: Adapter class to register
        """
        cls._adapters[channel_type] = adapter_class

    @classmethod
    def get_adapter(cls, channel_type: ChannelType, config: ChannelConfig) -> ChannelAdapter | None:
        """Get adapter instance for channel type.

        Args:
            channel_type: Channel type
            config: Channel configuration

        Returns:
            ChannelAdapter instance or None if not registered
        """
        adapter_class = cls._adapters.get(channel_type)
        if adapter_class:
            return adapter_class()
        return None

    @classmethod
    def list_available(cls) -> list[ChannelType]:
        """List available channel types.

        Returns:
            List of registered channel types
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, channel_type: ChannelType) -> bool:
        """Check if channel type is registered.

        Args:
            channel_type: Channel type to check

        Returns:
            True if registered
        """
        return channel_type in cls._adapters


def get_message_for_channel(
    decision_request: dict[str, Any] | None = None,
    status_report: dict[str, Any] | None = None,
    digest: dict[str, Any] | None = None,
) -> ChannelMessage:
    """Create ChannelMessage from decision/report/digest.

    Args:
        decision_request: Decision request dict
        status_report: Status report dict
        digest: Digest report dict

    Returns:
        ChannelMessage ready for sending
    """
    if decision_request:
        return ChannelMessage(
            message_id=decision_request.get("decision_request_id", "unknown"),
            message_type="decision_request",
            subject=f"Decision Required: {decision_request.get('question', '')[:50]}",
            body=format_decision_request_body(decision_request),
            recipient=decision_request.get("delivery_recipient", ""),
            metadata={"decision_type": decision_request.get("decision_type", "technical")},
        )

    if status_report:
        return ChannelMessage(
            message_id=status_report.get("report_id", "unknown"),
            message_type="status_report",
            subject=f"Status: {status_report.get('summary', '')[:50]}",
            body=format_status_report_body(status_report),
            recipient="",
            metadata={"report_type": status_report.get("report_type", "progress")},
        )

    if digest:
        return ChannelMessage(
            message_id=digest.get("digest_id", "unknown"),
            message_type="digest",
            subject=f"Digest: {digest.get('digest_mode', 'daily')}",
            body=digest.get("body", ""),
            recipient="",
            metadata={"digest_mode": digest.get("digest_mode", "daily")},
        )

    return ChannelMessage(
        message_id="empty",
        message_type="empty",
        subject="Empty message",
        body="",
        recipient="",
    )


def format_decision_request_body(request: dict[str, Any]) -> str:
    """Format decision request for channel body."""
    lines = []
    lines.append(f"## {request.get('question', 'Decision Required')}")
    lines.append("")
    lines.append(f"**Category:** {request.get('pause_reason_category', 'decision_required')}")
    lines.append("")
    options = request.get("options", [])
    if options:
        lines.append("**Options:**")
        for opt in options:
            opt_label = opt.get("label", str(opt)) if isinstance(opt, dict) else str(opt)
            lines.append(f"  • {opt_label}")
    lines.append("")
    recommendation = request.get("recommendation", "")
    if recommendation:
        lines.append(f"**Recommended:** {recommendation}")
    return "\n".join(lines)


def format_status_report_body(report: dict[str, Any]) -> str:
    """Format status report for channel body."""
    lines = []
    lines.append(f"## {report.get('summary', 'Status Update')}")
    lines.append("")
    lines.append(f"**State:** {report.get('current_state', 'active')}")
    lines.append("")
    what_changed = report.get("what_changed", [])
    if what_changed:
        lines.append("**What Changed:**")
        for item in what_changed[:5]:
            lines.append(f"  • {item}")
    return "\n".join(lines)


def is_channel_portable(artifact: dict[str, Any]) -> bool:
    """Check if artifact is portable across channels.

    Decision requests and status reports are designed to be
    channel-agnostic. This function validates portability.

    Args:
        artifact: Decision request or status report dict

    Returns:
        True if artifact can be sent through any registered channel
    """
    required_fields = ["message_type"]
    return all(f in artifact for f in required_fields)


def get_canonical_channel() -> ChannelType:
    """Get the canonical first channel (email).

    As per roadmap: Email is the canonical first channel.
    Other channels may come later as adapters.

    Returns:
        ChannelType.EMAIL
    """
    return ChannelType.EMAIL