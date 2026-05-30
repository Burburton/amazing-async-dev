"""Unified Blocking State - Phase 4 Feature 081.

Aggregates blocking states from all surfaces:
- Session start blocking (pending decisions)
- Acceptance escalation
- Verification exceptions

Per feature-081-unified-platform-shell.md Section 3.3:
- Provides unified view of all blocking conditions
- Enables prominent display in home overview
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.decision_waiting_session import check_blocking_state, get_blocking_message
from runtime.decision_request_store import DecisionRequestStore, DecisionRequestStatus
from runtime.state_store import StateStore


@dataclass
class SessionBlockingState:
    """Session blocking from decision request."""
    status: str  # BLOCKED, WAITING_DECISION, CLEAR
    request_id: str | None
    message: str
    project_id: str


@dataclass
class AcceptanceEscalation:
    """Acceptance escalation blocking."""
    project_id: str
    feature_id: str
    escalation_reason: str
    terminal_state: str
    attempt_count: int
    destination: str


@dataclass
class VerificationException:
    """Verification exception blocking."""
    project_id: str
    execution_id: str
    exception_reason: str
    occurred_at: str
    destination: str


@dataclass
class UnifiedBlockingState:
    """Complete unified blocking state across all surfaces."""
    
    # Session blocking (decisions)
    session_blocking: list[SessionBlockingState] = field(default_factory=list)
    
    # Acceptance escalation
    acceptance_escalations: list[AcceptanceEscalation] = field(default_factory=list)
    
    # Verification exceptions
    verification_exceptions: list[VerificationException] = field(default_factory=list)
    
    # Computed properties
    is_blocked: bool = False
    total_blocking_count: int = 0
    blocking_summary: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_blocking": [
                {
                    "status": sb.status,
                    "request_id": sb.request_id,
                    "message": sb.message,
                    "project_id": sb.project_id,
                }
                for sb in self.session_blocking
            ],
            "acceptance_escalations": [
                {
                    "project_id": ae.project_id,
                    "feature_id": ae.feature_id,
                    "escalation_reason": ae.escalation_reason,
                    "terminal_state": ae.terminal_state,
                    "attempt_count": ae.attempt_count,
                    "destination": ae.destination,
                }
                for ae in self.acceptance_escalations
            ],
            "verification_exceptions": [
                {
                    "project_id": ve.project_id,
                    "execution_id": ve.execution_id,
                    "exception_reason": ve.exception_reason,
                    "occurred_at": ve.occurred_at,
                    "destination": ve.destination,
                }
                for ve in self.verification_exceptions
            ],
            "is_blocked": self.is_blocked,
            "total_blocking_count": self.total_blocking_count,
            "blocking_summary": self.blocking_summary,
            "updated_at": self.updated_at,
        }
    
    def is_calm(self) -> bool:
        """Check if no blocking conditions exist."""
        return self.total_blocking_count == 0


def get_session_blocking_for_project(project_path: Path) -> SessionBlockingState | None:
    """Get session blocking state for a single project."""
    status, request_id = check_blocking_state(project_path)
    
    if status == "CLEAR":
        return None
    
    message = get_blocking_message(project_path)
    
    return SessionBlockingState(
        status=status,
        request_id=request_id,
        message=message,
        project_id=project_path.name,
    )


def get_acceptance_escalations_for_project(project_path: Path) -> list[AcceptanceEscalation]:
    """Get acceptance escalations for a project.
    
    Currently returns empty list - acceptance escalation detection
    would need acceptance store integration.
    """
    # TODO: Integrate with acceptance store when acceptance escalation exists
    # For now, this is a placeholder for the full implementation
    return []


def get_verification_exceptions_for_project(project_path: Path) -> list[VerificationException]:
    """Get verification exceptions for a project.
    
    Currently returns empty list - verification exception detection
    would need verification store integration.
    """
    # TODO: Integrate with verification store when exception tracking exists
    # For now, this is a placeholder for the full implementation
    return []


def get_unified_blocking_state(projects_path: Path) -> UnifiedBlockingState:
    """Get unified blocking state across all projects.
    
    Aggregates:
    - Session blocking (pending decisions)
    - Acceptance escalations
    - Verification exceptions
    """
    state = UnifiedBlockingState()
    
    if not projects_path.exists():
        return state
    
    project_dirs = [
        p for p in projects_path.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ]
    
    for project_path in project_dirs:
        project_id = project_path.name
        
        # Session blocking
        session_blocking = get_session_blocking_for_project(project_path)
        if session_blocking:
            state.session_blocking.append(session_blocking)
        
        # Acceptance escalations
        acceptance_escalations = get_acceptance_escalations_for_project(project_path)
        state.acceptance_escalations.extend(acceptance_escalations)
        
        # Verification exceptions
        verification_exceptions = get_verification_exceptions_for_project(project_path)
        state.verification_exceptions.extend(verification_exceptions)
    
    # Compute totals
    state.total_blocking_count = (
        len(state.session_blocking)
        + len(state.acceptance_escalations)
        + len(state.verification_exceptions)
    )
    
    # Determine if blocked
    state.is_blocked = (
        any(sb.status == "BLOCKED" for sb in state.session_blocking)
        or len(state.session_blocking) > 0
        or len(state.acceptance_escalations) > 0
        or len(state.verification_exceptions) > 0
    )
    
    # Generate summary
    if state.is_blocked:
        parts = []
        if state.session_blocking:
            blocked = sum(1 for sb in state.session_blocking if sb.status == "BLOCKED")
            waiting = sum(1 for sb in state.session_blocking if sb.status == "WAITING_DECISION")
            if blocked > 0:
                parts.append(f"{blocked} blocked")
            if waiting > 0:
                parts.append(f"{waiting} waiting")
        if state.acceptance_escalations:
            parts.append(f"{len(state.acceptance_escalations)} acceptance")
        if state.verification_exceptions:
            parts.append(f"{len(state.verification_exceptions)} verification")
        state.blocking_summary = ", ".join(parts)
    else:
        state.blocking_summary = "All clear"
    
    return state


def get_unified_blocking_for_project(project_path: Path) -> UnifiedBlockingState:
    """Get unified blocking state for a single project."""
    projects_path = project_path.parent
    return get_unified_blocking_state(projects_path)
