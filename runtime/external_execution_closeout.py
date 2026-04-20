"""External Execution Closeout Orchestrator - Feature 061.

System-owned closeout orchestration layer that:
- Polls for external execution result readiness
- Detects missing frontend verification
- Invokes Feature 060 post-external verification when needed
- Classifies final closeout state
- Persists closeout-related status into execution artifacts

Architecture (per Feature 061):
- Feature 056 = capability layer (browser_verifier, dev_server_manager)
- Feature 059 = enforcement primitives (verification_session, verification_enforcer)
- Feature 060 = frontend verification orchestration (browser_verification_orchestrator)
- Feature 061 = external closeout lifecycle (this module)

Primary Path vs Fallback Path:
- Primary: run-day external closeout attempts to close out in same lifecycle
- Fallback: resume-next-day recovers interrupted/incomplete closeout
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.external_closeout_state import (
    CloseoutState,
    CloseoutTerminalClassification,
    CloseoutResult,
    DEFAULT_CLOSEOUT_TIMEOUT_SECONDS,
    DEFAULT_POLL_INTERVAL_SECONDS,
    MAX_POLL_ATTEMPTS,
)
from runtime.browser_verification_orchestrator import (
    orchestrate_post_external,
    OrchestrationResult,
    OrchestrationTerminalState,
)
from runtime.verification_gate import requires_browser_verification


class ExternalExecutionCloseoutOrchestrator:
    """Orchestrates external execution closeout lifecycle.
    
    Responsibilities (Feature 061 section 6.1):
    - Wait for external execution artifacts/result readiness
    - Determine whether valid execution result exists
    - Determine whether required frontend verification is missing
    - Invoke Feature 060 post-external verification when needed
    - Classify final closeout state
    - Persist closeout-related status into execution artifacts
    """
    
    def __init__(
        self,
        project_path: Path,
        timeout_seconds: int = DEFAULT_CLOSEOUT_TIMEOUT_SECONDS,
        poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
    ):
        self.project_path = project_path
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self._start_time: datetime | None = None
    
    def orchestrate_external_closeout(
        self,
        execution_id: str,
        execution_pack: dict[str, Any],
        project_id: str,
    ) -> CloseoutResult:
        """Canonical entry point for external execution closeout (Feature 061 section 7.1).
        
        Args:
            execution_id: Execution identifier
            execution_pack: ExecutionPack dict with task metadata
            project_id: Project identifier
            
        Returns:
            CloseoutResult with terminal closeout state and classification
        """
        self._start_time = datetime.now()
        
        result = CloseoutResult(
            closeout_state=CloseoutState.EXTERNAL_EXECUTION_TRIGGERED,
            timeout_seconds=self.timeout_seconds,
            started_at=self._start_time.isoformat(),
        )
        
        result.closeout_state = CloseoutState.EXTERNAL_EXECUTION_PENDING
        
        execution_result_path = self.project_path / "execution-results" / f"{execution_id}.md"
        
        detected_result = self._poll_for_execution_result(execution_result_path)
        
        result.poll_attempts = detected_result["poll_attempts"]
        result.execution_result_detected = detected_result["detected"]
        result.elapsed_seconds = (datetime.now() - self._start_time).total_seconds()
        
        if not detected_result["detected"]:
            return self._handle_timeout_or_stall(result)
        
        result.closeout_state = CloseoutState.EXTERNAL_EXECUTION_RESULT_DETECTED
        
        execution_result = detected_result["execution_result"]
        result.execution_result_valid = self._validate_execution_result(execution_result)
        
        if not result.execution_result_valid:
            return self._handle_invalid_result(result, execution_result)
        
        verification_type = execution_pack.get("verification_type", "backend_only")
        result.verification_required = requires_browser_verification(verification_type)
        
        if result.verification_required:
            result.closeout_state = CloseoutState.POST_EXTERNAL_VERIFICATION_REQUIRED
            
            bv_field = execution_result.get("browser_verification", {})
            if bv_field.get("executed", False):
                result.verification_completed = True
                result.verification_terminal_state = execution_result.get(
                    "orchestration_terminal_state", "unknown"
                )
            else:
                verification_result = self._run_post_external_verification(
                    execution_pack,
                    execution_result,
                    project_id,
                )
                result.verification_completed = verification_result.verification_completed
                result.verification_terminal_state = verification_result.terminal_state.value
                
                execution_result["browser_verification"] = verification_result.to_dict()["browser_verification"]
                execution_result["orchestration_terminal_state"] = verification_result.terminal_state.value
                
                self._persist_updated_execution_result(execution_id, execution_result)
        
        result.closeout_state = CloseoutState.POST_EXTERNAL_VERIFICATION_COMPLETED
        
        terminal_classification = self._determine_terminal_classification(result)
        result.terminal_classification = terminal_classification
        result.finished_at = datetime.now().isoformat()
        result.elapsed_seconds = (datetime.now() - self._start_time).total_seconds()
        
        result.closeout_state = self._map_classification_to_state(terminal_classification)
        result.recovery_required = result.closeout_state == CloseoutState.CLOSEOUT_RECOVERY_REQUIRED
        
        return result
    
    def check_closeout_recovery_needed(
        self,
        execution_id: str,
    ) -> dict[str, Any]:
        """Check if previous closeout needs recovery (for resume-next-day).
        
        Returns:
            dict with recovery_needed, closeout_state, and actions required
        """
        execution_result_path = self.project_path / "execution-results" / f"{execution_id}.md"
        
        if not execution_result_path.exists():
            return {
                "recovery_needed": True,
                "reason": "execution_result_not_found",
                "closeout_state": None,
                "recommended_action": "Run closeout orchestration",
            }
        
        execution_result = self._load_execution_result(execution_result_path)
        
        closeout_state_str = execution_result.get("closeout_state", "")
        
        if not closeout_state_str:
            return {
                "recovery_needed": True,
                "reason": "closeout_not_started",
                "closeout_state": None,
                "recommended_action": "Run closeout orchestration for missing verification",
            }
        
        try:
            closeout_state = CloseoutState(closeout_state_str)
        except ValueError:
            return {
                "recovery_needed": True,
                "reason": "invalid_closeout_state",
                "closeout_state": closeout_state_str,
                "recommended_action": "Re-run closeout orchestration",
            }
        
        if closeout_state.is_terminal() and closeout_state.is_success():
            return {
                "recovery_needed": False,
                "reason": "closeout_complete",
                "closeout_state": closeout_state.value,
                "recommended_action": "None - continue to planning",
            }
        
        if closeout_state.is_terminal():
            return {
                "recovery_needed": True,
                "reason": f"closeout_terminal_but_not_success: {closeout_state.value}",
                "closeout_state": closeout_state.value,
                "recommended_action": "Review failure and retry or alternative approach",
            }
        
        return {
            "recovery_needed": True,
            "reason": f"closeout_interrupted: {closeout_state.value}",
            "closeout_state": closeout_state.value,
            "recommended_action": "Resume closeout orchestration",
        }
    
    def _poll_for_execution_result(
        self,
        result_path: Path,
    ) -> dict[str, Any]:
        """Poll for execution result file existence (Feature 061 section 7.2).
        
        Polls every poll_interval_seconds up to timeout_seconds.
        
        Returns:
            dict with detected (bool), poll_attempts (int), execution_result (dict if detected)
        """
        poll_attempts = 0
        max_attempts = self.timeout_seconds // self.poll_interval_seconds
        
        while poll_attempts < max_attempts:
            poll_attempts += 1
            
            if result_path.exists():
                execution_result = self._load_execution_result(result_path)
                return {
                    "detected": True,
                    "poll_attempts": poll_attempts,
                    "execution_result": execution_result,
                }
            
            time.sleep(self.poll_interval_seconds)
        
        return {
            "detected": False,
            "poll_attempts": poll_attempts,
            "execution_result": None,
        }
    
    def _load_execution_result(self, path: Path) -> dict[str, Any]:
        """Load execution result from YAML file."""
        import yaml
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                yaml_start = content.find("```yaml")
                yaml_end = content.find("```", yaml_start + 7)
                if yaml_start != -1 and yaml_end != -1:
                    yaml_content = content[yaml_start + 7:yaml_end].strip()
                    return yaml.safe_load(yaml_content) or {}
                return yaml.safe_load(content) or {}
        except Exception:
            return {}
    
    def _validate_execution_result(self, execution_result: dict[str, Any]) -> bool:
        """Validate execution result structure (Feature 061 section 7.2).
        
        Checks:
        - execution_id present
        - status field present and valid
        - completed_items or artifacts_created present
        """
        if not execution_result:
            return False
        
        execution_id = execution_result.get("execution_id")
        if not execution_id:
            return False
        
        status = execution_result.get("status")
        valid_statuses = ["success", "partial", "blocked", "failed", "stopped"]
        if status not in valid_statuses:
            return False
        
        has_completed = execution_result.get("completed_items") is not None
        has_artifacts = execution_result.get("artifacts_created") is not None
        
        return has_completed or has_artifacts
    
    def _run_post_external_verification(
        self,
        execution_pack: dict[str, Any],
        execution_result: dict[str, Any],
        project_id: str,
    ) -> OrchestrationResult:
        """Invoke Feature 060 post-external verification (Feature 061 section 7.4).
        
        Reuses browser_verification_orchestrator.orchestrate_post_external.
        """
        return orchestrate_post_external(
            project_path=self.project_path,
            project_id=project_id,
            execution_pack=execution_pack,
            execution_result=execution_result,
        )
    
    def _persist_updated_execution_result(
        self,
        execution_id: str,
        execution_result: dict[str, Any],
    ) -> None:
        """Persist updated execution result with verification data."""
        import yaml
        
        result_path = self.project_path / "execution-results" / f"{execution_id}.md"
        
        content = f"""# ExecutionResult: {execution_id}

```yaml
{yaml.dump(execution_result, default_flow_style=False, sort_keys=False)}
```
"""
        
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _handle_timeout_or_stall(self, result: CloseoutResult) -> CloseoutResult:
        """Handle timeout/stall during polling (Feature 061 section 6.6).
        
        Returns structured timeout state instead of hanging.
        """
        result.closeout_state = CloseoutState.CLOSEOUT_TIMEOUT
        result.stall_detected = True
        result.terminal_classification = CloseoutTerminalClassification.CLOSEOUT_TIMEOUT
        result.recovery_required = True
        result.recovery_reason = "External execution did not produce result within timeout"
        result.finished_at = datetime.now().isoformat()
        return result
    
    def _handle_invalid_result(
        self,
        result: CloseoutResult,
        execution_result: dict[str, Any],
    ) -> CloseoutResult:
        """Handle invalid/partial execution result."""
        result.closeout_state = CloseoutState.CLOSEOUT_RECOVERY_REQUIRED
        result.terminal_classification = CloseoutTerminalClassification.RECOVERY_REQUIRED
        result.recovery_required = True
        result.recovery_reason = f"Execution result invalid: missing required fields"
        result.closeout_error = f"Invalid result: {execution_result.get('status', 'unknown')}"
        result.finished_at = datetime.now().isoformat()
        return result
    
    def _determine_terminal_classification(
        self,
        result: CloseoutResult,
    ) -> CloseoutTerminalClassification:
        """Determine terminal classification from closeout result."""
        if not result.execution_result_valid:
            return CloseoutTerminalClassification.RECOVERY_REQUIRED
        
        if result.stall_detected:
            return CloseoutTerminalClassification.STALLED
        
        if result.verification_required and not result.verification_completed:
            return CloseoutTerminalClassification.RECOVERY_REQUIRED
        
        if result.verification_required:
            terminal_state = result.verification_terminal_state
            if terminal_state in [
                OrchestrationTerminalState.NOT_REQUIRED.value,
                OrchestrationTerminalState.SUCCESS.value,
                OrchestrationTerminalState.EXCEPTION_ACCEPTED.value,
                OrchestrationTerminalState.SKIPPED_BY_POLICY.value,
            ]:
                return CloseoutTerminalClassification.SUCCESS
            
            if terminal_state == OrchestrationTerminalState.FAILURE.value:
                return CloseoutTerminalClassification.VERIFICATION_FAILURE
            
            if terminal_state == OrchestrationTerminalState.TIMEOUT.value:
                return CloseoutTerminalClassification.CLOSEOUT_TIMEOUT
        
        return CloseoutTerminalClassification.SUCCESS
    
    def _map_classification_to_state(
        self,
        classification: CloseoutTerminalClassification,
    ) -> CloseoutState:
        """Map terminal classification to closeout state."""
        mapping = {
            CloseoutTerminalClassification.SUCCESS: CloseoutState.CLOSEOUT_COMPLETED_SUCCESS,
            CloseoutTerminalClassification.FAILURE: CloseoutState.CLOSEOUT_COMPLETED_FAILURE,
            CloseoutTerminalClassification.VERIFICATION_FAILURE: CloseoutState.CLOSEOUT_COMPLETED_FAILURE,
            CloseoutTerminalClassification.CLOSEOUT_TIMEOUT: CloseoutState.CLOSEOUT_TIMEOUT,
            CloseoutTerminalClassification.STALLED: CloseoutState.EXTERNAL_EXECUTION_STALLED,
            CloseoutTerminalClassification.RECOVERY_REQUIRED: CloseoutState.CLOSEOUT_RECOVERY_REQUIRED,
        }
        return mapping.get(classification, CloseoutState.CLOSEOUT_RECOVERY_REQUIRED)


def orchestrate_external_closeout(
    project_path: Path,
    execution_id: str,
    execution_pack: dict[str, Any],
    project_id: str,
    timeout_seconds: int = DEFAULT_CLOSEOUT_TIMEOUT_SECONDS,
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
) -> CloseoutResult:
    """Convenience function for run_day integration (Feature 061 AC-002)."""
    orchestrator = ExternalExecutionCloseoutOrchestrator(
        project_path=project_path,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    return orchestrator.orchestrate_external_closeout(
        execution_id=execution_id,
        execution_pack=execution_pack,
        project_id=project_id,
    )


def check_closeout_recovery_needed(
    project_path: Path,
    execution_id: str,
) -> dict[str, Any]:
    """Convenience function for resume-next-day fallback (Feature 061 AC-006)."""
    orchestrator = ExternalExecutionCloseoutOrchestrator(project_path=project_path)
    return orchestrator.check_closeout_recovery_needed(execution_id)