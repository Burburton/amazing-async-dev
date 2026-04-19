"""Browser Verification Orchestrator - Feature 060.

System-owned frontend verification orchestration that guarantees:
- Verification triggered automatically when required
- Browser verification executed by runtime, not agent-optional
- Structured results captured in execution state
- Success progression blocked without valid verification terminal state

Architecture:
- Feature 056 = capability layer (browser_verifier, dev_server_manager)
- Feature 059 = enforcement primitives (verification_session, verification_enforcer)
- Feature 060 = orchestration integration layer (this module)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.dev_server_manager import (
    DevServerManager,
    DevServerResult,
    DevServerStatus,
    DevServerFramework,
    detect_framework,
)
from runtime.browser_verifier import (
    BrowserVerificationResult,
    BrowserVerificationStatus,
    ExceptionReason,
    run_browser_verification,
    create_exception_result,
    to_execution_result_dict,
    check_playwright_available,
)
from runtime.verification_session import (
    VerificationSessionManager,
    VerificationSessionStatus,
    DEFAULT_TIMEOUT,
)
from runtime.verification_classifier import (
    VerificationType,
    get_verification_type,
    classify_verification_type_from_files,
)
from runtime.verification_gate import (
    requires_browser_verification,
    validate_browser_verification,
)


class OrchestrationTerminalState(str, Enum):
    """Terminal states for verification orchestration (Feature 060 section 7.5).
    
    These states eliminate ambiguous "unknown" completion semantics.
    Each state is a valid terminal - no intermediate states allowed at completion.
    """
    NOT_REQUIRED = "not_required"
    REQUIRED_NOT_STARTED = "required_not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    EXCEPTION_ACCEPTED = "exception_accepted"
    SKIPPED_BY_POLICY = "skipped_by_policy"


@dataclass
class OrchestrationResult:
    """Result of browser verification orchestration.
    
    Captures the complete lifecycle from determination to completion,
    suitable for ExecutionResult.browser_verification field.
    """
    terminal_state: OrchestrationTerminalState
    verification_required: bool
    verification_started: bool
    verification_completed: bool
    dev_server_started: bool
    dev_server_url: str | None = None
    browser_verification_result: BrowserVerificationResult | None = None
    exception_reason: ExceptionReason | None = None
    exception_details: str | None = None
    timeout_seconds: int = DEFAULT_TIMEOUT
    elapsed_seconds: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str | None = None
    session_id: str | None = None
    remediation_guidance: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for ExecutionResult.browser_verification field."""
        result = {
            "orchestration_terminal_state": self.terminal_state.value,
            "verification_required": self.verification_required,
            "verification_started": self.verification_started,
            "verification_completed": self.verification_completed,
            "dev_server_started": self.dev_server_started,
            "dev_server_url": self.dev_server_url,
            "timeout_seconds": self.timeout_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "session_id": self.session_id,
        }
        
        if self.browser_verification_result:
            bv_dict = to_execution_result_dict(self.browser_verification_result)
            result["browser_verification"] = bv_dict["browser_verification"]
        else:
            result["browser_verification"] = {
                "executed": False,
                "exception_reason": self.exception_reason.value if self.exception_reason else None,
                "exception_details": self.exception_details,
            }
        
        if self.exception_reason:
            result["exception_reason"] = self.exception_reason.value
            result["exception_details"] = self.exception_details
        
        if self.remediation_guidance:
            result["remediation_guidance"] = self.remediation_guidance
        
        return result
    
    def is_valid_terminal_state(self) -> bool:
        """Check if terminal state allows execution success progression."""
        valid_for_success = [
            OrchestrationTerminalState.NOT_REQUIRED,
            OrchestrationTerminalState.SUCCESS,
            OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            OrchestrationTerminalState.SKIPPED_BY_POLICY,
        ]
        return self.terminal_state in valid_for_success
    
    def get_gate_status(self) -> str:
        """Get completion gate status: 'allowed' or 'blocked'."""
        return "allowed" if self.is_valid_terminal_state() else "blocked"


class BrowserVerificationOrchestrator:
    """System-owned frontend verification orchestration.
    
    Responsibilities (Feature 060 section 6.1):
    - Determine whether frontend verification is required
    - Create and manage verification session state
    - Invoke dev server preparation/readiness handling
    - Invoke browser verification execution
    - Capture structured results
    - Apply timeout/stall/reminder policies
    - Return final orchestration result
    """
    
    def __init__(
        self,
        project_path: Path,
        timeout_seconds: int = DEFAULT_TIMEOUT,
        auto_start_server: bool = True,
    ):
        self.project_path = project_path
        self.timeout_seconds = timeout_seconds
        self.auto_start_server = auto_start_server
        
        self.session_manager = VerificationSessionManager(project_path)
        self.dev_server_manager: DevServerManager | None = None
        self._start_time: datetime | None = None
    
    def determine_verification_required(
        self,
        execution_pack: dict[str, Any] | None = None,
        changed_files: list[str] | None = None,
        feature_spec: dict[str, Any] | None = None,
    ) -> tuple[bool, VerificationType]:
        """Determine if frontend verification is required (Feature 060 section 7.1).
        
        Uses structured signals:
        - verification_type from ExecutionPack
        - task classification
        - changed file patterns
        - feature spec markers
        
        Returns:
            Tuple of (required, verification_type)
        """
        if execution_pack:
            verification_type_str = execution_pack.get("verification_type", "backend_only")
            try:
                verification_type = VerificationType(verification_type_str)
            except ValueError:
                verification_type = VerificationType.BACKEND_ONLY
            
            required = requires_browser_verification(verification_type_str)
            return required, verification_type
        
        # Fall back to file-based classification
        if changed_files:
            verification_type = get_verification_type(
                files=changed_files,
                feature_spec=feature_spec,
                execution_pack=execution_pack,
            )
            required = requires_browser_verification(verification_type.value)
            return required, verification_type
        
        # Default: not required
        return False, VerificationType.BACKEND_ONLY
    
    def orchestrate_frontend_verification(
        self,
        execution_pack: dict[str, Any],
        project_id: str,
        scenarios: list[str] | None = None,
        changed_files: list[str] | None = None,
    ) -> OrchestrationResult:
        """Execute full verification orchestration lifecycle.
        
        This is the main entry point that:
        1. Determines if verification is required
        2. Creates session
        3. Starts dev server (if needed)
        4. Runs browser verification
        5. Captures results
        6. Returns terminal state
        
        Args:
            execution_pack: ExecutionPack dict with task info
            project_id: Project identifier
            scenarios: Optional list of scenarios to run
            changed_files: Optional list of changed files for classification
            
        Returns:
            OrchestrationResult with terminal state
        """
        self._start_time = datetime.now()
        
        # Step 1: Determine if verification required
        required, verification_type = self.determine_verification_required(
            execution_pack=execution_pack,
            changed_files=changed_files,
        )
        
        if not required:
            return self._create_not_required_result()
        
        # Step 2: Create verification session
        session = self.session_manager.create_session(
            project_id=project_id,
            timeout_seconds=self.timeout_seconds,
        )
        dev_server_result = None
        if self.auto_start_server:
            dev_server_result = self._start_dev_server()
            
            if not dev_server_result.success:
                return self._create_server_failed_result(
                    session.session_id,
                    dev_server_result,
                )
            
            status = dev_server_result.status
            if status.url and status.port and status.process_id:
                self.session_manager.start_dev_server(
                    status.url,
                    status.port,
                    status.process_id,
                )
        
        self.session_manager.start_verification()
        
        verification_url = dev_server_result.status.url if dev_server_result else None
        if not verification_url:
            return self._create_no_url_result(session.session_id)
        
        bv_result = self._run_browser_verification(
            url=verification_url,
            project_name=project_id,
            scenarios=scenarios,
        )
        
        # Step 5: Complete session and capture results
        self.session_manager.complete_verification(
            to_execution_result_dict(bv_result)["browser_verification"]
        )
        
        elapsed = (datetime.now() - self._start_time).total_seconds()
        
        # Step 6: Determine terminal state
        terminal_state = self._determine_terminal_state(bv_result)
        
        # Cleanup: stop dev server
        if self.dev_server_manager:
            self.dev_server_manager.stop()
        
        return OrchestrationResult(
            terminal_state=terminal_state,
            verification_required=True,
            verification_started=True,
            verification_completed=True,
            dev_server_started=dev_server_result.success if dev_server_result else False,
            dev_server_url=verification_url,
            browser_verification_result=bv_result,
            timeout_seconds=self.timeout_seconds,
            elapsed_seconds=elapsed,
            started_at=self._start_time.isoformat(),
            finished_at=datetime.now().isoformat(),
            session_id=session.session_id,
        )
    
    def orchestrate_post_external_verification(
        self,
        project_id: str,
        execution_pack: dict[str, Any],
        execution_result: dict[str, Any],
    ) -> OrchestrationResult:
        """Post-external-execution verification phase (AC-003).
        
        Called after external tool returns control to trigger
        system-owned verification for frontend tasks.
        
        Args:
            project_id: Project identifier
            execution_pack: ExecutionPack dict
            execution_result: ExecutionResult from external execution
            
        Returns:
            OrchestrationResult with verification outcome
        """
        self._start_time = datetime.now()
        
        # Check if verification already completed by external tool
        bv_field = execution_result.get("browser_verification", {})
        if bv_field.get("executed", False):
            # External tool already ran verification
            return self._create_already_verified_result(bv_field)
        
        # Check if valid exception recorded
        exception_reason = bv_field.get("exception_reason")
        if exception_reason and exception_reason in [
            "playwright_unavailable",
            "environment_blocked",
            "browser_install_failed",
            "ci_container_limitation",
            "missing_credentials",
            "deterministic_blocker",
            "reclassified_noninteractive",
        ]:
            return self._create_exception_accepted_result(exception_reason, bv_field.get("exception_details", ""))
        
        # Verification required but not completed - run system-owned verification
        required, _ = self.determine_verification_required(execution_pack=execution_pack)
        
        if not required:
            return self._create_not_required_result()
        
        # Run full verification orchestration
        return self.orchestrate_frontend_verification(
            execution_pack=execution_pack,
            project_id=project_id,
        )
    
    def check_timeout_and_enforce(self) -> dict[str, Any]:
        """Check timeout and enforce if exceeded (AC-006 anti-stall).
        
        Returns enforcement result with action taken.
        """
        if not self.session_manager.active_session:
            return {"status": "no_session", "action": "none"}
        
        if self.session_manager.check_timeout():
            result = self.session_manager.enforce_timeout()
            elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
            return {
                "status": "timeout",
                "action": "recorded_timeout_exception",
                "elapsed_seconds": elapsed,
                "terminal_state": OrchestrationTerminalState.TIMEOUT.value,
                "result": result,
            }
        
        return {
            "status": "pending",
            "action": "continue_verification",
            "elapsed_seconds": self.session_manager.get_elapsed_seconds(),
            "remaining_seconds": self.session_manager.get_remaining_seconds(),
        }
    
    def get_success_gate_status(
        self,
        execution_result: dict[str, Any],
        verification_type: str,
    ) -> tuple[bool, str]:
        """Check if ExecutionResult can be marked as success (AC-005).
        
        Returns:
            Tuple of (can_mark_success, reason)
        """
        if not requires_browser_verification(verification_type):
            return True, "Browser verification not required for this verification_type"
        
        orchestration_state = execution_result.get("orchestration_terminal_state", "")
        valid_terminal_states = [
            OrchestrationTerminalState.NOT_REQUIRED,
            OrchestrationTerminalState.SUCCESS,
            OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            OrchestrationTerminalState.SKIPPED_BY_POLICY,
        ]
        
        try:
            terminal_state = OrchestrationTerminalState(orchestration_state)
            if terminal_state in valid_terminal_states:
                return True, f"Valid terminal state: {terminal_state.value}"
        except ValueError:
            pass
        
        validation = validate_browser_verification(verification_type, execution_result)
        
        if validation.get("valid", False):
            return True, validation.get("reason", "Browser verification valid")
        
        return False, (
            f"Browser verification required but not completed. "
            f"Terminal state: {orchestration_state or 'unknown'}. "
            f"Validation: {validation.get('reason', 'invalid')}"
        )
    
    def cleanup(self) -> None:
        """Cleanup resources after orchestration."""
        if self.dev_server_manager:
            self.dev_server_manager.stop()
        
        if self.session_manager.active_session:
            self.session_manager.clear_session()
    
    # --- Internal helper methods ---
    
    def _start_dev_server(self) -> DevServerResult:
        """Start dev server and wait for readiness."""
        self.dev_server_manager = DevServerManager(self.project_path)
        return self.dev_server_manager.start(timeout=self.timeout_seconds)
    
    def _run_browser_verification(
        self,
        url: str,
        project_name: str,
        scenarios: list[str] | None = None,
    ) -> BrowserVerificationResult:
        """Run browser verification via Playwright."""
        if not check_playwright_available():
            return create_exception_result(
                ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
                "Playwright not installed in environment",
            )
        
        return run_browser_verification(
            url=url,
            project_name=project_name,
            scenarios=scenarios,
            timeout=self.timeout_seconds,
        )
    
    def _determine_terminal_state(
        self,
        bv_result: BrowserVerificationResult,
    ) -> OrchestrationTerminalState:
        """Determine terminal state from browser verification result."""
        if bv_result.status == BrowserVerificationStatus.SUCCESS:
            return OrchestrationTerminalState.SUCCESS
        
        if bv_result.status == BrowserVerificationStatus.FAILED:
            return OrchestrationTerminalState.FAILURE
        
        if bv_result.status == BrowserVerificationStatus.EXCEPTION:
            if bv_result.exception_reason:
                return OrchestrationTerminalState.EXCEPTION_ACCEPTED
            return OrchestrationTerminalState.FAILURE
        
        if bv_result.status == BrowserVerificationStatus.SKIPPED:
            return OrchestrationTerminalState.SKIPPED_BY_POLICY
        
        return OrchestrationTerminalState.FAILURE
    
    def _create_not_required_result(self) -> OrchestrationResult:
        """Create result when verification not required."""
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        return OrchestrationResult(
            terminal_state=OrchestrationTerminalState.NOT_REQUIRED,
            verification_required=False,
            verification_started=False,
            verification_completed=False,
            dev_server_started=False,
            elapsed_seconds=elapsed,
            started_at=self._start_time.isoformat() if self._start_time else datetime.now().isoformat(),
            finished_at=datetime.now().isoformat(),
        )
    
    def _create_server_failed_result(
        self,
        session_id: str,
        dev_server_result: DevServerResult,
    ) -> OrchestrationResult:
        """Create result when dev server failed to start."""
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        self.session_manager.record_exception(
            "dev_server_failed",
            dev_server_result.status.error_message or "Dev server failed to start",
        )
        
        return OrchestrationResult(
            terminal_state=OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            verification_required=True,
            verification_started=True,
            verification_completed=False,
            dev_server_started=False,
            exception_reason=ExceptionReason.ENVIRONMENT_BLOCKED,
            exception_details=dev_server_result.status.error_message,
            elapsed_seconds=elapsed,
            started_at=self._start_time.isoformat() if self._start_time else datetime.now().isoformat(),
            finished_at=datetime.now().isoformat(),
            session_id=session_id,
            remediation_guidance="Check dev server configuration and port availability",
        )
    
    def _create_no_url_result(self, session_id: str) -> OrchestrationResult:
        """Create result when no dev server URL available."""
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        self.session_manager.record_exception(
            "no_dev_server_url",
            "No dev server URL available for verification",
        )
        
        return OrchestrationResult(
            terminal_state=OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            verification_required=True,
            verification_started=True,
            verification_completed=False,
            dev_server_started=False,
            exception_reason=ExceptionReason.ENVIRONMENT_BLOCKED,
            exception_details="No dev server URL available for verification",
            elapsed_seconds=elapsed,
            started_at=self._start_time.isoformat() if self._start_time else datetime.now().isoformat(),
            finished_at=datetime.now().isoformat(),
            session_id=session_id,
            remediation_guidance="Ensure dev server is running or provide explicit URL",
        )
    
    def _create_already_verified_result(self, bv_field: dict[str, Any]) -> OrchestrationResult:
        """Create result when verification already completed."""
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        # Create synthetic BrowserVerificationResult from field
        bv_result = BrowserVerificationResult(
            executed=bv_field.get("executed", False),
            status=BrowserVerificationStatus.SUCCESS if bv_field.get("passed", 0) > bv_field.get("failed", 0) else BrowserVerificationStatus.FAILED,
            passed=bv_field.get("passed", 0),
            failed=bv_field.get("failed", 0),
            scenarios_run=bv_field.get("scenarios_run", []),
            screenshots=bv_field.get("screenshots", []),
        )
        
        terminal_state = self._determine_terminal_state(bv_result)
        
        return OrchestrationResult(
            terminal_state=terminal_state,
            verification_required=True,
            verification_started=True,
            verification_completed=True,
            dev_server_started=True,  # Assumed since verification ran
            browser_verification_result=bv_result,
            elapsed_seconds=elapsed,
            started_at=self._start_time.isoformat() if self._start_time else datetime.now().isoformat(),
            finished_at=datetime.now().isoformat(),
        )
    
    def _create_exception_accepted_result(
        self,
        exception_reason: str,
        exception_details: str,
    ) -> OrchestrationResult:
        """Create result when valid exception recorded."""
        elapsed = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        try:
            reason_enum = ExceptionReason(exception_reason)
        except ValueError:
            reason_enum = ExceptionReason.ENVIRONMENT_BLOCKED
        
        return OrchestrationResult(
            terminal_state=OrchestrationTerminalState.EXCEPTION_ACCEPTED,
            verification_required=True,
            verification_started=True,
            verification_completed=False,
            dev_server_started=False,
            exception_reason=reason_enum,
            exception_details=exception_details,
            elapsed_seconds=elapsed,
            started_at=self._start_time.isoformat() if self._start_time else datetime.now().isoformat(),
            finished_at=datetime.now().isoformat(),
        )


# --- Convenience functions for CLI integration ---

def orchestrate_for_run_day(
    project_path: Path,
    execution_pack: dict[str, Any],
    project_id: str,
) -> OrchestrationResult:
    """Convenience function for run_day integration.
    
    Automatically determines verification requirement and
    runs full orchestration if needed.
    """
    orchestrator = BrowserVerificationOrchestrator(project_path)
    
    required, _ = orchestrator.determine_verification_required(execution_pack=execution_pack)
    
    if not required:
        return orchestrator._create_not_required_result()
    
    return orchestrator.orchestrate_frontend_verification(
        execution_pack=execution_pack,
        project_id=project_id,
    )


def orchestrate_post_external(
    project_path: Path,
    project_id: str,
    execution_pack: dict[str, Any],
    execution_result: dict[str, Any],
) -> OrchestrationResult:
    """Convenience function for post-external verification (AC-003)."""
    orchestrator = BrowserVerificationOrchestrator(project_path)
    return orchestrator.orchestrate_post_external_verification(
        project_id=project_id,
        execution_pack=execution_pack,
        execution_result=execution_result,
    )


def can_mark_execution_success_with_orchestration(
    project_path: Path,
    execution_result: dict[str, Any],
    verification_type: str,
) -> tuple[bool, str]:
    """Convenience function for success gate check (AC-005)."""
    orchestrator = BrowserVerificationOrchestrator(project_path)
    return orchestrator.get_success_gate_status(execution_result, verification_type)