"""Audit trail store for end-to-end decision/reporting loop traceability (Feature 047).

Links: outbound request/report → inbound reply → parsed decision → applied action.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
import json


CHAIN_TYPES = ["decision_request_chain", "status_report_chain"]


class AuditTrailStore:
    """Store for decision/reporting audit trail."""

    DEFAULT_AUDIT_PATH = ".runtime/audit-trail"

    def __init__(self, runtime_path: Path) -> None:
        self.runtime_path = runtime_path
        self.audit_path = runtime_path / self.DEFAULT_AUDIT_PATH
        self.audit_path.mkdir(parents=True, exist_ok=True)

    def generate_audit_id(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        existing = list(self.audit_path.glob(f"audit-{today}-*.json"))
        next_num = len(existing) + 1
        return f"audit-{today}-{next_num:03d}"

    def record_outbound_request(
        self,
        request_id: str,
        project_id: str,
        channel: str,
        artifact_path: str | None = None,
    ) -> dict[str, Any]:
        """Record outbound decision request sent.

        Args:
            request_id: Decision request ID
            project_id: Project context
            channel: Delivery channel
            artifact_path: Path to sent artifact

        Returns:
            Audit record dict
        """
        audit_id = self.generate_audit_id()
        now = datetime.now().isoformat()

        audit = {
            "audit_id": audit_id,
            "chain_type": "decision_request_chain",
            "project_id": project_id,
            "created_at": now,
            "outbound_request_id": request_id,
            "outbound_sent_at": now,
            "outbound_channel": channel,
            "outbound_artifact_path": artifact_path,
        }

        self.save_audit(audit)
        return audit

    def record_outbound_report(
        self,
        report_id: str,
        project_id: str,
        channel: str,
        artifact_path: str | None = None,
        reply_required: bool = False,
    ) -> dict[str, Any]:
        """Record outbound status report sent.

        Args:
            report_id: Status report ID
            project_id: Project context
            channel: Delivery channel
            artifact_path: Path to sent artifact
            reply_required: Whether reply is expected

        Returns:
            Audit record dict
        """
        audit_id = self.generate_audit_id()
        now = datetime.now().isoformat()

        audit = {
            "audit_id": audit_id,
            "chain_type": "status_report_chain",
            "project_id": project_id,
            "created_at": now,
            "outbound_report_id": report_id,
            "outbound_sent_at": now,
            "outbound_channel": channel,
            "outbound_artifact_path": artifact_path,
            "inbound_reply_expected": reply_required,
        }

        self.save_audit(audit)
        return audit

    def record_inbound_reply(
        self,
        request_id: str,
        reply_raw: str,
        parsed_command: str | None = None,
        parsed_argument: str | None = None,
        validation_status: str = "valid",
    ) -> dict[str, Any] | None:
        """Record inbound reply received for a request.

        Args:
            request_id: Decision request ID
            reply_raw: Raw reply text
            parsed_command: Parsed command
            parsed_argument: Parsed argument
            validation_status: Validation result

        Returns:
            Updated audit record or None if not found
        """
        audit = self.find_audit_by_request_id(request_id)
        if not audit:
            return None

        now = datetime.now().isoformat()
        reply_id = f"reply-{datetime.now().strftime('%Y%m%d')}-{hash(reply_raw) % 1000:03d}"

        audit["inbound_reply_id"] = reply_id
        audit["inbound_received_at"] = now
        audit["inbound_reply_raw"] = reply_raw
        audit["inbound_parsed_command"] = parsed_command
        audit["inbound_parsed_argument"] = parsed_argument
        audit["inbound_validation_status"] = validation_status

        self.save_audit(audit)
        return audit

    def record_decision_applied(
        self,
        request_id: str,
        applied_action: str,
        runstate_before: dict[str, Any] | None = None,
        runstate_after: dict[str, Any] | None = None,
        continuation_phase: str | None = None,
    ) -> dict[str, Any] | None:
        """Record decision applied to RunState.

        Args:
            request_id: Decision request ID
            applied_action: Action taken
            runstate_before: RunState before
            runstate_after: RunState after
            continuation_phase: Phase for continuation

        Returns:
            Updated audit record or None if not found
        """
        audit = self.find_audit_by_request_id(request_id)
        if not audit:
            return None

        now = datetime.now().isoformat()

        audit["decision_applied_at"] = now
        audit["decision_applied_action"] = applied_action

        if runstate_before:
            audit["decision_runstate_before"] = {
                "phase": runstate_before.get("current_phase", ""),
                "decisions_needed_count": len(runstate_before.get("decisions_needed", [])),
            }

        if runstate_after:
            audit["decision_runstate_after"] = {
                "phase": runstate_after.get("current_phase", ""),
                "decisions_needed_count": len(runstate_after.get("decisions_needed", [])),
            }

        if continuation_phase:
            audit["decision_continuation_phase"] = continuation_phase

        self.save_audit(audit)
        return audit

    def save_audit(self, audit: dict[str, Any]) -> None:
        audit_id = audit.get("audit_id", "unknown")
        file_path = self.audit_path / f"{audit_id}.json"
        with open(file_path, "w") as f:
            json.dump(audit, f, indent=2)

    def load_audit(self, audit_id: str) -> dict[str, Any] | None:
        file_path = self.audit_path / f"{audit_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return json.load(f)

    def find_audit_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        for file_path in self.audit_path.glob("audit-*.json"):
            with open(file_path) as f:
                audit = json.load(f)
                if audit.get("outbound_request_id") == request_id:
                    return audit
        return None

    def find_audit_by_report_id(self, report_id: str) -> dict[str, Any] | None:
        for file_path in self.audit_path.glob("audit-*.json"):
            with open(file_path) as f:
                audit = json.load(f)
                if audit.get("outbound_report_id") == report_id:
                    return audit
        return None

    def list_audits(
        self,
        chain_type: str | None = None,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        audits = []
        for file_path in self.audit_path.glob("audit-*.json"):
            with open(file_path) as f:
                audit = json.load(f)
                if chain_type and audit.get("chain_type") != chain_type:
                    continue
                if project_id and audit.get("project_id") != project_id:
                    continue
                audits.append(audit)
        return sorted(audits, key=lambda a: a.get("created_at", ""))


def reconstruct_audit_trail(
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct full audit trail as readable summary.

    Args:
        audit: Audit record dict

    Returns:
        Reconstructed trail dict with stages
    """
    stages = []

    chain_type = audit.get("chain_type", "")

    if chain_type == "decision_request_chain":
        if audit.get("outbound_request_id"):
            stages.append({
                "stage": "request_sent",
                "request_id": audit["outbound_request_id"],
                "timestamp": audit.get("outbound_sent_at", ""),
                "channel": audit.get("outbound_channel", ""),
            })

        if audit.get("inbound_reply_id"):
            stages.append({
                "stage": "reply_received",
                "reply_id": audit["inbound_reply_id"],
                "timestamp": audit.get("inbound_received_at", ""),
                "raw": audit.get("inbound_reply_raw", ""),
                "parsed": f"{audit.get('inbound_parsed_command', '')} {audit.get('inbound_parsed_argument', '')}",
                "validation": audit.get("inbound_validation_status", ""),
            })

        if audit.get("decision_applied_at"):
            stages.append({
                "stage": "decision_applied",
                "timestamp": audit.get("decision_applied_at", ""),
                "action": audit.get("decision_applied_action", ""),
                "phase_change": f"{audit.get('decision_runstate_before', {}).get('phase', '')} → {audit.get('decision_runstate_after', {}).get('phase', '')}",
            })

    elif chain_type == "status_report_chain":
        if audit.get("outbound_report_id"):
            stages.append({
                "stage": "report_sent",
                "report_id": audit["outbound_report_id"],
                "timestamp": audit.get("outbound_sent_at", ""),
                "channel": audit.get("outbound_channel", ""),
            })

    return {
        "audit_id": audit.get("audit_id", ""),
        "chain_type": chain_type,
        "project_id": audit.get("project_id", ""),
        "stages": stages,
        "complete": len(stages) > 0,
    }


def detect_missing_links(
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Detect missing links in audit trail.

    Args:
        audit: Audit record dict

    Returns:
        Dict with missing_links_detected and details
    """
    missing = []
    chain_type = audit.get("chain_type", "")

    if chain_type == "decision_request_chain":
        if audit.get("outbound_request_id") and not audit.get("inbound_reply_id"):
            sent_at = audit.get("outbound_sent_at")
            if sent_at:
                sent_dt = datetime.fromisoformat(sent_at)
                hours_since = (datetime.now() - sent_dt).total_seconds() / 3600
                if hours_since > 24:
                    missing.append({
                        "stage": "inbound_reply",
                        "expected": "Reply should be recorded after request sent",
                        "actual": f"No reply recorded after {hours_since:.1f} hours",
                        "severity": "warning",
                    })

        if audit.get("inbound_reply_id") and audit.get("inbound_validation_status") == "valid":
            if not audit.get("decision_applied_at"):
                missing.append({
                    "stage": "decision_applied",
                    "expected": "Decision should be applied after valid reply",
                    "actual": "Valid reply but no application recorded",
                    "severity": "error",
                })

    return {
        "missing_links_detected": len(missing) > 0,
        "missing_links_details": missing,
    }


def format_audit_summary(
    audit: dict[str, Any],
) -> str:
    """Format audit trail as readable summary.

    Args:
        audit: Audit record dict

    Returns:
        Human-readable summary string
    """
    reconstructed = reconstruct_audit_trail(audit)
    missing = detect_missing_links(audit)

    lines = []

    lines.append(f"## Audit Trail: {audit.get('audit_id', 'unknown')}")
    lines.append("")
    lines.append(f"**Chain:** {audit.get('chain_type', '')}")
    lines.append(f"**Project:** {audit.get('project_id', '')}")
    lines.append(f"**Created:** {audit.get('created_at', '')}")
    lines.append("")
    lines.append("**Stages:**")

    for stage in reconstructed.get("stages", []):
        stage_name = stage.get("stage", "unknown")
        timestamp = stage.get("timestamp", "")
        lines.append(f"  1. {stage_name}: {timestamp}")

        if "request_id" in stage:
            lines.append(f"     Request: {stage['request_id']}")
        if "reply_id" in stage:
            lines.append(f"     Reply: {stage['reply_id']}")
            lines.append(f"     Raw: {stage.get('raw', '')}")
            lines.append(f"     Parsed: {stage.get('parsed', '')}")
        if "action" in stage:
            lines.append(f"     Action: {stage['action']}")

    lines.append("")

    if missing.get("missing_links_detected"):
        lines.append("**⚠ Missing Links:**")
        for detail in missing.get("missing_links_details", []):
            lines.append(f"  • {detail.get('stage', '')}: {detail.get('actual', '')}")

    return "\n".join(lines)