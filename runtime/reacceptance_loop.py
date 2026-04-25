"""Re-Acceptance Loop Orchestration - Feature 073.

Supports repeated acceptance cycles until work is accepted or escalated.
Tracks attempt history and prevents endless loops.

Integration with:
- Feature 071 (AcceptanceRunner)
- Feature 072 (AcceptanceRecovery)
- Feature 070 (AcceptanceReadiness)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.acceptance_runner import (
    AcceptanceResult,
    AcceptanceTerminalState,
    run_acceptance_from_execution,
    load_acceptance_result,
    save_acceptance_result,
)
from runtime.acceptance_pack_builder import (
    AcceptancePack,
    build_acceptance_pack,
    load_acceptance_pack,
    save_acceptance_pack,
)
from runtime.acceptance_recovery import (
    AcceptanceRecoveryPack,
    process_failed_acceptance,
    load_acceptance_recovery_pack,
)
from runtime.acceptance_readiness import check_acceptance_readiness, AcceptanceReadiness


class ReAcceptanceState(str, Enum):
    """States for re-acceptance loop."""
    
    READY_FOR_REACCEPTANCE = "ready_for_reacceptance"
    RECOVERY_IN_PROGRESS = "recovery_in_progress"
    REACCEPTANCE_TRIGGERED = "reacceptance_triggered"
    TERMINAL_SUCCESS = "terminal_success"
    TERMINAL_FAILURE = "terminal_failure"
    TERMINAL_ESCALATION = "terminal_escalation"
    MAX_ATTEMPTS_REACHED = "max_attempts_reached"


class ReAcceptancePolicy(str, Enum):
    """Policy for re-acceptance triggering."""
    
    AUTO_RETRY = "auto_retry"
    MANUAL_TRIGGER = "manual_trigger"
    ESCALATE_AFTER_FAILURES = "escalate_after_failures"


@dataclass
class AcceptanceAttempt:
    """Single acceptance attempt record."""
    
    attempt_number: int
    acceptance_result_id: str
    acceptance_pack_id: str
    terminal_state: str
    triggered_at: str
    triggered_by: str = "auto"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "acceptance_result_id": self.acceptance_result_id,
            "acceptance_pack_id": self.acceptance_pack_id,
            "terminal_state": self.terminal_state,
            "triggered_at": self.triggered_at,
            "triggered_by": self.triggered_by,
        }


@dataclass
class AcceptanceAttemptHistory:
    """History of acceptance attempts for a feature (Feature 073)."""
    
    feature_id: str
    execution_result_id: str
    
    attempts: list[AcceptanceAttempt] = field(default_factory=list)
    total_attempts: int = 0
    accepted_attempts: int = 0
    rejected_attempts: int = 0
    conditional_attempts: int = 0
    
    current_state: ReAcceptanceState = ReAcceptanceState.RECOVERY_IN_PROGRESS
    max_attempts: int = 5
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "execution_result_id": self.execution_result_id,
            "attempts": [a.to_dict() for a in self.attempts],
            "total_attempts": self.total_attempts,
            "accepted_attempts": self.accepted_attempts,
            "rejected_attempts": self.rejected_attempts,
            "conditional_attempts": self.conditional_attempts,
            "current_state": self.current_state.value,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def add_attempt(self, result: AcceptanceResult) -> None:
        self.attempts.append(AcceptanceAttempt(
            attempt_number=result.attempt_number,
            acceptance_result_id=result.acceptance_result_id,
            acceptance_pack_id=result.acceptance_pack_id,
            terminal_state=result.terminal_state.value,
            triggered_at=result.validated_at,
        ))
        
        self.total_attempts = len(self.attempts)
        
        if result.terminal_state == AcceptanceTerminalState.ACCEPTED:
            self.accepted_attempts += 1
        elif result.terminal_state == AcceptanceTerminalState.REJECTED:
            self.rejected_attempts += 1
        elif result.terminal_state == AcceptanceTerminalState.CONDITIONAL:
            self.conditional_attempts += 1
        
        self.updated_at = datetime.now().isoformat()
    
    def is_terminal(self) -> bool:
        return self.current_state in [
            ReAcceptanceState.TERMINAL_SUCCESS,
            ReAcceptanceState.TERMINAL_FAILURE,
            ReAcceptanceState.TERMINAL_ESCALATION,
            ReAcceptanceState.MAX_ATTEMPTS_REACHED,
        ]
    
    def can_retry(self) -> bool:
        return self.total_attempts < self.max_attempts and not self.is_terminal()
    
    def get_latest_result(self) -> AcceptanceAttempt | None:
        if self.attempts:
            return self.attempts[-1]
        return None


MAX_ATTEMPTS_DEFAULT = 5
ESCALATE_AFTER_FAILURES_DEFAULT = 3


def should_trigger_reacceptance(
    history: AcceptanceAttemptHistory,
    policy: ReAcceptancePolicy = ReAcceptancePolicy.AUTO_RETRY,
) -> bool:
    """Determine if re-acceptance should be triggered."""
    if history.is_terminal():
        return False
    
    if not history.can_retry():
        return False
    
    if policy == ReAcceptancePolicy.MANUAL_TRIGGER:
        return False
    
    latest = history.get_latest_result()
    if latest and latest.terminal_state in ["accepted", "conditional"]:
        return False
    
    return True


def determine_reacceptance_state(
    history: AcceptanceAttemptHistory,
    latest_result: AcceptanceResult | None,
) -> ReAcceptanceState:
    """Determine current state from history and latest result."""
    if not latest_result:
        return ReAcceptanceState.RECOVERY_IN_PROGRESS
    
    if latest_result.terminal_state == AcceptanceTerminalState.ACCEPTED:
        return ReAcceptanceState.TERMINAL_SUCCESS
    
    if latest_result.terminal_state == AcceptanceTerminalState.CONDITIONAL:
        return ReAcceptanceState.TERMINAL_SUCCESS
    
    if latest_result.terminal_state == AcceptanceTerminalState.ESCALATED:
        return ReAcceptanceState.TERMINAL_ESCALATION
    
    if history.total_attempts >= history.max_attempts:
        return ReAcceptanceState.MAX_ATTEMPTS_REACHED
    
    if history.rejected_attempts >= ESCALATE_AFTER_FAILURES_DEFAULT:
        return ReAcceptanceState.TERMINAL_ESCALATION
    
    return ReAcceptanceState.RECOVERY_IN_PROGRESS


def get_or_create_attempt_history(
    project_path: Path,
    feature_id: str,
    execution_result_id: str,
) -> AcceptanceAttemptHistory:
    """Get existing history or create new one."""
    history_path = project_path / "acceptance-history" / f"{feature_id}--{execution_result_id}.md"
    
    if history_path.exists():
        return load_attempt_history(project_path, feature_id, execution_result_id) or AcceptanceAttemptHistory(
            feature_id=feature_id,
            execution_result_id=execution_result_id,
        )
    
    return AcceptanceAttemptHistory(
        feature_id=feature_id,
        execution_result_id=execution_result_id,
    )


def save_attempt_history(
    project_path: Path,
    history: AcceptanceAttemptHistory,
) -> Path:
    """Save attempt history to file."""
    import yaml
    
    history_dir = project_path / "acceptance-history"
    history_dir.mkdir(parents=True, exist_ok=True)
    
    history_path = history_dir / f"{history.feature_id}--{history.execution_result_id}.md"
    
    yaml_content = yaml.dump(history.to_dict(), default_flow_style=False, sort_keys=False)
    markdown_content = f"""# AcceptanceAttemptHistory

```yaml
{yaml_content}
```
"""
    
    history_path.write_text(markdown_content, encoding="utf-8")
    return history_path


def load_attempt_history(
    project_path: Path,
    feature_id: str,
    execution_result_id: str,
) -> AcceptanceAttemptHistory | None:
    """Load attempt history from file."""
    import yaml
    
    history_path = project_path / "acceptance-history" / f"{feature_id}--{execution_result_id}.md"
    
    if not history_path.exists():
        return None
    
    content = history_path.read_text(encoding="utf-8")
    
    lines = content.split("\n")
    yaml_start = None
    yaml_end = None
    
    for i, line in enumerate(lines):
        if line.strip() == "```yaml":
            yaml_start = i + 1
        elif yaml_start is not None and line.strip() == "```":
            yaml_end = i
            break
    
    if yaml_start is not None and yaml_end is not None:
        yaml_block = "\n".join(lines[yaml_start:yaml_end])
        data = yaml.safe_load(yaml_block)
        
        attempts = [
            AcceptanceAttempt(**a) for a in data.get("attempts", [])
        ]
        
        return AcceptanceAttemptHistory(
            feature_id=data.get("feature_id", ""),
            execution_result_id=data.get("execution_result_id", ""),
            attempts=attempts,
            total_attempts=data.get("total_attempts", 0),
            accepted_attempts=data.get("accepted_attempts", 0),
            rejected_attempts=data.get("rejected_attempts", 0),
            conditional_attempts=data.get("conditional_attempts", 0),
            current_state=ReAcceptanceState(data.get("current_state", "recovery_in_progress")),
            max_attempts=data.get("max_attempts", 5),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
    
    return None


def trigger_reacceptance(
    project_path: Path,
    execution_result_id: str,
    feature_id: str,
    policy: ReAcceptancePolicy = ReAcceptancePolicy.AUTO_RETRY,
) -> AcceptanceResult | None:
    """Trigger re-acceptance for a feature (Feature 073)."""
    history = get_or_create_attempt_history(project_path, feature_id, execution_result_id)
    
    if not should_trigger_reacceptance(history, policy):
        return None
    
    if history.rejected_attempts > 0:
        recovery_pack = load_acceptance_recovery_pack(
            project_path,
            f"arp-{execution_result_id}",
        )
        
        if recovery_pack:
            pending_items = [r for r in recovery_pack.recovery_items if r.status == "pending"]
            if pending_items:
                return None
    
    result = run_acceptance_from_execution(project_path, execution_result_id)
    
    if result is None:
        return None
    
    history.add_attempt(result)
    history.current_state = determine_reacceptance_state(history, result)
    
    save_attempt_history(project_path, history)
    
    if result.terminal_state in [
        AcceptanceTerminalState.REJECTED,
        AcceptanceTerminalState.MANUAL_REVIEW,
    ]:
        process_failed_acceptance(project_path, result.acceptance_result_id)
    
    return result


def run_acceptance_loop(
    project_path: Path,
    execution_result_id: str,
    feature_id: str,
    max_attempts: int = MAX_ATTEMPTS_DEFAULT,
) -> AcceptanceAttemptHistory:
    """Run full acceptance loop until terminal state (Feature 073)."""
    history = get_or_create_attempt_history(project_path, feature_id, execution_result_id)
    history.max_attempts = max_attempts
    
    while not history.is_terminal() and history.can_retry():
        result = trigger_reacceptance(
            project_path,
            execution_result_id,
            feature_id,
            ReAcceptancePolicy.AUTO_RETRY,
        )
        
        if result is None:
            break
        
        history.current_state = determine_reacceptance_state(history, result)
        
        if history.is_terminal():
            break
    
    save_attempt_history(project_path, history)
    return history


def get_acceptance_lineage(
    project_path: Path,
    feature_id: str,
) -> list[dict[str, Any]]:
    """Get lineage of all acceptance attempts for a feature."""
    history_dir = project_path / "acceptance-history"
    
    if not history_dir.exists():
        return []
    
    lineage: list[dict[str, Any]] = []
    
    for history_file in history_dir.glob(f"{feature_id}--*.md"):
        parts = history_file.stem.split("--")
        execution_result_id = parts[1] if len(parts) > 1 else ""
        
        history = load_attempt_history(
            project_path,
            feature_id,
            execution_result_id,
        )
        
        if history:
            lineage.append({
                "execution_result_id": history.execution_result_id,
                "total_attempts": history.total_attempts,
                "final_state": history.current_state.value,
                "accepted": history.accepted_attempts > 0,
                "attempts": [a.to_dict() for a in history.attempts],
            })
    
    return lineage