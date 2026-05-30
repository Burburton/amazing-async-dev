"""Cross-Surface Links - Phase 4 Feature 081.

Provides links between operator surfaces when relevant relationships exist.
Per feature-081-unified-platform-shell.md Section 3.2.

Cross-links enable operators to navigate between related surfaces
without manually stitching together context.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SurfaceType(str, Enum):
    RECOVERY = "recovery"
    DECISION = "decision"
    ACCEPTANCE = "acceptance"
    OBSERVER = "observer"
    VERIFICATION = "verification"
    EVIDENCE = "evidence"


@dataclass
class CrossSurfaceLink:
    source_type: SurfaceType
    source_id: str
    target_type: SurfaceType
    target_id: str
    link_reason: str
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "link_reason": self.link_reason,
            "suggested_action": self.suggested_action,
        }


def get_recovery_to_decision_link(
    project_id: str,
    execution_id: str,
    decision_request_id: str | None,
    reason: str,
) -> CrossSurfaceLink | None:
    """Link from Recovery to Decision Inbox when blocked by pending decision."""
    if not decision_request_id:
        return None

    return CrossSurfaceLink(
        source_type=SurfaceType.RECOVERY,
        source_id=execution_id,
        target_type=SurfaceType.DECISION,
        target_id=decision_request_id,
        link_reason=reason,
        suggested_action=f"asyncdev decision show --request {decision_request_id}",
    )


def get_recovery_to_acceptance_link(
    project_id: str,
    feature_id: str,
    execution_id: str,
    reason: str,
) -> CrossSurfaceLink | None:
    """Link from Recovery to Acceptance when acceptance retry needed."""
    return CrossSurfaceLink(
        source_type=SurfaceType.RECOVERY,
        source_id=execution_id,
        target_type=SurfaceType.ACCEPTANCE,
        target_id=feature_id,
        link_reason=reason,
        suggested_action=f"asyncdev acceptance status --project {project_id}",
    )


def get_decision_to_recovery_link(
    project_id: str,
    decision_request_id: str,
    unblocked_execution_id: str | None,
    reason: str,
) -> CrossSurfaceLink | None:
    """Link from Decision to Recovery when decision unblocks an execution."""
    if not unblocked_execution_id:
        return None

    return CrossSurfaceLink(
        source_type=SurfaceType.DECISION,
        source_id=decision_request_id,
        target_type=SurfaceType.RECOVERY,
        target_id=unblocked_execution_id,
        link_reason=reason,
        suggested_action=f"asyncdev recovery show --execution {unblocked_execution_id}",
    )


def get_acceptance_to_recovery_link(
    project_id: str,
    feature_id: str,
    acceptance_result_id: str,
    reason: str,
) -> CrossSurfaceLink | None:
    """Link from Acceptance to Recovery when acceptance failure suggests recovery."""
    return CrossSurfaceLink(
        source_type=SurfaceType.ACCEPTANCE,
        source_id=acceptance_result_id,
        target_type=SurfaceType.RECOVERY,
        target_id=f"{project_id}:{feature_id}",
        link_reason=reason,
        suggested_action=f"asyncdev recovery list --project {project_id}",
    )


def get_observer_to_recovery_link(
    project_id: str,
    finding_type: str,
    reason: str,
) -> CrossSurfaceLink | None:
    """Link from Observer to Recovery when findings indicate recovery needed."""
    return CrossSurfaceLink(
        source_type=SurfaceType.OBSERVER,
        source_id=finding_type,
        target_type=SurfaceType.RECOVERY,
        target_id=project_id,
        link_reason=reason,
        suggested_action=f"asyncdev recovery list --project {project_id}",
    )


def get_observer_to_decision_link(
    project_id: str,
    finding_type: str,
    decision_request_id: str | None,
    reason: str,
) -> CrossSurfaceLink | None:
    """Link from Observer to Decision when findings require human decision."""
    if not decision_request_id:
        return None

    return CrossSurfaceLink(
        source_type=SurfaceType.OBSERVER,
        source_id=finding_type,
        target_type=SurfaceType.DECISION,
        target_id=decision_request_id,
        link_reason=reason,
        suggested_action=f"asyncdev decision show --request {decision_request_id}",
    )


def format_cross_link(links: list[CrossSurfaceLink]) -> list[str]:
    """Format cross-surface links for display."""
    if not links:
        return []

    formatted = []
    for link in links:
        formatted.append(
            f"[cyan]{link.target_type.value}[/cyan]: {link.link_reason} → {link.suggested_action}"
        )

    return formatted
