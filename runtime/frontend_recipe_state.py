"""Frontend Verification Recipe State Model - Feature 062.

Defines the controlled execution recipe state for frontend verification:
- Explicit stage transitions (server_starting -> readiness_probing -> browser_verification -> result_persisting)
- Structured result persistence for downstream orchestration
- Failure handling at each stage with terminal outcomes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FrontendRecipeStage(str, Enum):
    """Execution stages for controlled frontend verification recipe (Feature 062 section 7.5).
    
    Stages represent explicit transitions:
    - server_starting -> readiness_probing
    - readiness_probing -> browser_verification
    - browser_verification -> result_persisting
    - result_persisting -> completed_success
    - any stage -> completed_failure
    """
    # Execution stages
    INITIALIZING = "initializing"
    SERVER_STARTING = "server_starting"
    READINESS_PROBING = "readiness_probing"
    BROWSER_VERIFICATION = "browser_verification"
    RESULT_PERSISTING = "result_persisting"
    
    # Terminal states
    COMPLETED_SUCCESS = "completed_success"
    COMPLETED_FAILURE = "completed_failure"
    COMPLETED_TIMEOUT = "completed_timeout"
    
    @classmethod
    def terminal_stages(cls) -> list[FrontendRecipeStage]:
        """Return stages that are valid terminal states."""
        return [
            cls.COMPLETED_SUCCESS,
            cls.COMPLETED_FAILURE,
            cls.COMPLETED_TIMEOUT,
        ]
    
    @classmethod
    def success_terminal(cls) -> list[FrontendRecipeStage]:
        """Return terminal stages that indicate successful completion."""
        return [cls.COMPLETED_SUCCESS]
    
    def is_terminal(self) -> bool:
        """Check if this stage is terminal."""
        return self in FrontendRecipeStage.terminal_stages()
    
    def is_success(self) -> bool:
        """Check if this terminal stage indicates success."""
        return self in FrontendRecipeStage.success_terminal()


class FrontendRecipeFailureReason(str, Enum):
    """Failure reasons for frontend verification recipe."""
    FRAMEWORK_UNKNOWN = "framework_unknown"
    SERVER_START_FAILED = "server_start_failed"
    SERVER_TIMEOUT = "server_timeout"
    PORT_DISCOVERY_FAILED = "port_discovery_failed"
    READINESS_TIMEOUT = "readiness_timeout"
    BROWSER_VERIFICATION_FAILED = "browser_verification_failed"
    RESULT_PERSISTENCE_FAILED = "result_persistence_failed"
    UNEXPECTED_ERROR = "unexpected_error"


@dataclass
class ServerStartupInfo:
    """Information captured from dev server startup."""
    command: list[str]
    detected_port: int | None = None
    detected_url: str | None = None
    stdout_capture: str = ""
    stderr_capture: str = ""
    process_id: int | None = None
    startup_duration_seconds: float = 0.0


@dataclass
class ReadinessProbeInfo:
    """Information from readiness probe stage."""
    target_url: str
    probe_attempts: int = 0
    successful_probe: bool = False
    probe_duration_seconds: float = 0.0
    http_status_code: int | None = None


@dataclass
class FrontendRecipeResult:
    """Result of controlled frontend verification recipe execution (Feature 062 section 7.1).
    
    Captures complete lifecycle from initialization to terminal outcome,
    suitable for ExecutionResult frontend_recipe field.
    """
    stage: FrontendRecipeStage
    execution_id: str
    project_path: str
    framework: str = "unknown"
    
    # Stage details
    server_startup: ServerStartupInfo | None = None
    readiness_probe: ReadinessProbeInfo | None = None
    browser_verification_executed: bool = False
    browser_verification_result: dict[str, Any] | None = None
    
    # Timing
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str | None = None
    total_duration_seconds: float = 0.0
    
    # Terminal outcome
    success: bool = False
    failure_reason: FrontendRecipeFailureReason | None = None
    error_message: str | None = None
    
    # Result persistence
    result_artifact_path: str | None = None
    result_persisted: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for ExecutionResult frontend_recipe field."""
        result = {
            "stage": self.stage.value,
            "execution_id": self.execution_id,
            "project_path": self.project_path,
            "framework": self.framework,
            "browser_verification_executed": self.browser_verification_executed,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_duration_seconds": self.total_duration_seconds,
            "success": self.success,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "error_message": self.error_message,
            "result_persisted": self.result_persisted,
            "result_artifact_path": self.result_artifact_path,
        }
        
        if self.server_startup:
            result["server_startup"] = {
                "command": self.server_startup.command,
                "detected_port": self.server_startup.detected_port,
                "detected_url": self.server_startup.detected_url,
                "process_id": self.server_startup.process_id,
                "startup_duration_seconds": self.server_startup.startup_duration_seconds,
            }
        
        if self.readiness_probe:
            result["readiness_probe"] = {
                "target_url": self.readiness_probe.target_url,
                "probe_attempts": self.readiness_probe.probe_attempts,
                "successful_probe": self.readiness_probe.successful_probe,
                "probe_duration_seconds": self.readiness_probe.probe_duration_seconds,
            }
        
        if self.browser_verification_result:
            result["browser_verification_result"] = self.browser_verification_result
        
        return result
    
    def is_complete(self) -> bool:
        """Check if recipe reached a valid terminal stage."""
        return self.stage.is_terminal()
    
    def allows_success_progression(self) -> bool:
        """Check if recipe allows execution success progression."""
        return self.is_complete() and self.success
    
    def get_gate_status(self) -> str:
        """Get completion gate status: 'allowed' or 'blocked'."""
        return "allowed" if self.allows_success_progression() else "blocked"


# Default timeout constants
DEFAULT_SERVER_START_TIMEOUT_SECONDS = 30
DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS = 60
DEFAULT_READINESS_PROBE_INTERVAL_SECONDS = 2
DEFAULT_BROWSER_VERIFICATION_TIMEOUT_SECONDS = 120
DEFAULT_PORT_PROBE_TIMEOUT_SECONDS = 10

# Port patterns for stdout parsing (common frameworks)
PORT_PATTERNS = {
    "vite": [
        r"Local:\s+http://localhost:(\d+)",
        r"running at http://localhost:(\d+)",
        r"port:\s*(\d+)",
    ],
    "next": [
        r"Local:\s+http://localhost:(\d+)",
        r"started server on port (\d+)",
        r"ready on http://localhost:(\d+)",
    ],
    "react": [
        r"running on http://localhost:(\d+)",
        r"On Your Network:\s+http://localhost:(\d+)",
    ],
    "nuxt": [
        r"Local:\s+http://localhost:(\d+)",
        r"listening on http://localhost:(\d+)",
    ],
    "sveltekit": [
        r"Local:\s+http://localhost:(\d+)",
        r"running at http://localhost:(\d+)",
    ],
    "generic": [
        r"localhost:(\d+)",
        r"http://127\.0\.0\.1:(\d+)",
        r"port\s+(\d+)",
    ],
}