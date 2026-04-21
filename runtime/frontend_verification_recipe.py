"""Frontend Verification Recipe - Feature 062.

Controlled execution recipe for frontend verification that ensures:
- Dev server startup is controlled (not foreground-blocking)
- Port/URL discovery via stdout parsing (primary) + port probe (fallback)
- Readiness probe before browser verification
- Browser verification is mandatory (not stopping at "server ready")
- Structured result persistence for downstream orchestration
- Explicit failure handling at each stage

Architecture (per Feature 062):
- Feature 056 = capability (browser_verifier, dev_server_manager)
- Feature 059 = enforcement (verification_session, verification_enforcer)
- Feature 060 = orchestration (browser_verification_orchestrator)
- Feature 061 = closeout lifecycle (external_execution_closeout)
- Feature 062 = execution recipe (this module) - upstream hardening
"""

import re
import threading
import subprocess
import sys
import time
import socket
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.frontend_recipe_state import (
    FrontendRecipeStage,
    FrontendRecipeFailureReason,
    FrontendRecipeResult,
    ServerStartupInfo,
    ReadinessProbeInfo,
    PORT_PATTERNS,
    DEFAULT_SERVER_START_TIMEOUT_SECONDS,
    DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS,
    DEFAULT_READINESS_PROBE_INTERVAL_SECONDS,
    DEFAULT_BROWSER_VERIFICATION_TIMEOUT_SECONDS,
    DEFAULT_PORT_PROBE_TIMEOUT_SECONDS,
)
from runtime.dev_server_manager import (
    DevServerFramework,
    detect_framework,
    get_start_command,
    DEFAULT_PORTS,
    PORT_RANGE,
)
from runtime.browser_verifier import run_browser_verification, BrowserVerificationStatus
from runtime.shell_config import get_shell_config, ShellConfig, BASH_CLEAN_FLAGS, windows_path_to_bash_path


def parse_port_from_stdout(stdout: str, framework: str) -> int | None:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_stdout = ansi_escape.sub('', stdout)
    
    patterns = PORT_PATTERNS.get(framework, PORT_PATTERNS["generic"])
    
    for pattern in patterns:
        match = re.search(pattern, clean_stdout, re.IGNORECASE)
        if match:
            try:
                port = int(match.group(1))
                if 1 <= port <= 65535:
                    return port
            except (ValueError, IndexError):
                continue
    
    return None


def probe_port_availability(port: int, host: str = "localhost") -> bool:
    """Check if port is responding (fallback port discovery strategy)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(DEFAULT_PORT_PROBE_TIMEOUT_SECONDS)
            s.connect((host, port))
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def probe_url_readiness(url: str, timeout: int = DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS) -> tuple[bool, int | None]:
    """Probe URL for HTTP readiness with timeout (Feature 062 section 6.3).
    
    Returns:
        Tuple of (ready, status_code)
    """
    start_time = time.time()
    status_code = None
    
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, method="HEAD")
            response = urllib.request.urlopen(req, timeout=5)
            status_code = response.status
            return True, status_code
        except urllib.error.HTTPError as e:
            status_code = e.code
            if e.code < 500:
                return True, status_code
            time.sleep(DEFAULT_READINESS_PROBE_INTERVAL_SECONDS)
        except (urllib.error.URLError, socket.timeout, ConnectionError):
            time.sleep(DEFAULT_READINESS_PROBE_INTERVAL_SECONDS)
    
    return False, status_code


def find_port_by_probe(framework: DevServerFramework) -> int | None:
    """Find responding port by probing known ports (fallback strategy)."""
    default_port = DEFAULT_PORTS.get(framework, 3000)
    
    # Try default port first
    if probe_port_availability(default_port):
        return default_port
    
    # Probe other common ports
    for port in PORT_RANGE:
        if port != default_port and probe_port_availability(port):
            return port
    
    return None


class FrontendVerificationRecipe:
    """Controlled frontend verification execution recipe (Feature 062 section 7.1).
    
    Canonical entry point for frontend verification work that enforces:
    - Stage sequence: startup -> readiness -> verification -> result
    - No stopping at "server ready"
    - Structured result persistence
    - Explicit failure outcomes
    """
    
    def __init__(
        self,
        project_path: Path,
        execution_id: str,
        server_start_timeout: int = DEFAULT_SERVER_START_TIMEOUT_SECONDS,
        readiness_probe_timeout: int = DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS,
        browser_verification_timeout: int = DEFAULT_BROWSER_VERIFICATION_TIMEOUT_SECONDS,
    ):
        self.project_path = project_path
        self.execution_id = execution_id
        self.server_start_timeout = server_start_timeout
        self.readiness_probe_timeout = readiness_probe_timeout
        self.browser_verification_timeout = browser_verification_timeout
        
        self._shell_config = ShellConfig(project_path / ".runtime" / "shell-config.yaml")
        
        self._start_time: datetime | None = None
        self._process: subprocess.Popen | None = None
        self._result: FrontendRecipeResult | None = None
    
    def execute(self) -> FrontendRecipeResult:
        """Execute controlled frontend verification recipe.
        
        Stage transitions:
        - INITIALIZING -> SERVER_STARTING
        - SERVER_STARTING -> READINESS_PROBING
        - READINESS_PROBING -> BROWSER_VERIFICATION
        - BROWSER_VERIFICATION -> RESULT_PERSISTING
        - RESULT_PERSISTING -> COMPLETED_SUCCESS
        - any stage -> COMPLETED_FAILURE
        
        Returns:
            FrontendRecipeResult with terminal outcome
        """
        self._start_time = datetime.now()
        
        result = FrontendRecipeResult(
            stage=FrontendRecipeStage.INITIALIZING,
            execution_id=self.execution_id,
            project_path=str(self.project_path),
            started_at=self._start_time.isoformat(),
        )
        
        framework_enum = detect_framework(self.project_path)
        result.framework = framework_enum.value
        
        if framework_enum == DevServerFramework.UNKNOWN:
            return self._handle_failure(
                result,
                FrontendRecipeFailureReason.FRAMEWORK_UNKNOWN,
                "Could not detect frontend framework from package.json",
            )
        
        # Stage 1: SERVER_STARTING
        result.stage = FrontendRecipeStage.SERVER_STARTING
        startup_info = self._start_dev_server(framework_enum)
        result.server_startup = startup_info
        
        if not startup_info.process_id:
            return self._handle_failure(
                result,
                FrontendRecipeFailureReason.SERVER_START_FAILED,
                startup_info.stderr_capture or "Server failed to start",
            )
        
        # Port discovery: stdout parsing (primary) + probe (fallback)
        detected_port = startup_info.detected_port
        detected_url = startup_info.detected_url
        
        if not detected_port:
            detected_port = find_port_by_probe(framework_enum)
            if detected_port:
                detected_url = f"http://localhost:{detected_port}"
        
        if not detected_port or not detected_url:
            return self._handle_failure(
                result,
                FrontendRecipeFailureReason.PORT_DISCOVERY_FAILED,
                "Could not determine dev server port",
            )
        
        # Stage 2: READINESS_PROBING
        result.stage = FrontendRecipeStage.READINESS_PROBING
        readiness_info = self._probe_readiness(detected_url)
        result.readiness_probe = readiness_info
        
        if not readiness_info.successful_probe:
            self._stop_server()
            return self._handle_failure(
                result,
                FrontendRecipeFailureReason.READINESS_TIMEOUT,
                f"Server not ready after {self.readiness_probe_timeout}s at {detected_url}",
            )
        
        # Stage 3: BROWSER_VERIFICATION
        result.stage = FrontendRecipeStage.BROWSER_VERIFICATION
        
        try:
            bv_result = run_browser_verification(
                url=detected_url,
                project_name=self.project_path.name,
                timeout=self.browser_verification_timeout,
                screenshot_dir=self.project_path / "screenshots" / self.execution_id,
            )
            result.browser_verification_executed = True
            result.browser_verification_result = {
                "executed": bv_result.executed,
                "status": bv_result.status.value,
                "passed": bv_result.passed,
                "failed": bv_result.failed,
                "scenarios_run": bv_result.scenarios_run,
            }
            
            if bv_result.status == BrowserVerificationStatus.FAILED:
                self._stop_server()
                return self._handle_failure(
                    result,
                    FrontendRecipeFailureReason.BROWSER_VERIFICATION_FAILED,
                    f"Browser verification failed: {bv_result.failed} scenarios failed",
                )
            
            if bv_result.status == BrowserVerificationStatus.EXCEPTION:
                # Accept exception as success (per Feature 060 exception_accepted rule)
                pass
                
        except Exception as e:
            result.browser_verification_executed = False
            self._stop_server()
            return self._handle_failure(
                result,
                FrontendRecipeFailureReason.BROWSER_VERIFICATION_FAILED,
                f"Browser verification error: {e}",
            )
        
        # Stage 4: RESULT_PERSISTING
        result.stage = FrontendRecipeStage.RESULT_PERSISTING
        result_path = self._persist_result(result)
        
        if result_path:
            result.result_persisted = True
            result.result_artifact_path = result_path
        else:
            return self._handle_failure(
                result,
                FrontendRecipeFailureReason.RESULT_PERSISTENCE_FAILED,
                "Failed to persist execution result",
            )
        
        # Cleanup
        self._stop_server()
        
        # Terminal: COMPLETED_SUCCESS
        result.stage = FrontendRecipeStage.COMPLETED_SUCCESS
        result.success = True
        result.finished_at = datetime.now().isoformat()
        result.total_duration_seconds = (datetime.now() - self._start_time).total_seconds()
        
        self._result = result
        return result
    
    def _start_dev_server(self, framework: DevServerFramework) -> ServerStartupInfo:
        startup_start = datetime.now()
        stdout_capture = ""
        stderr_capture = ""
        
        command = get_start_command(framework)
        executable = self._shell_config.get_executable()
        
        if sys.platform == "win32" and executable:
            bash_cwd = windows_path_to_bash_path(self.project_path)
            command_str = " ".join(command)
            bash_command = f"cd '{bash_cwd}' && {command_str}"
            popen_args = [executable] + BASH_CLEAN_FLAGS + ["-c", bash_command]
            popen_kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
            }
        else:
            popen_args = command
            popen_kwargs = {
                "cwd": self.project_path,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
            }
        
        try:
            self._process = subprocess.Popen(popen_args, **popen_kwargs)
            
            output_buffer = []
            detected_port = None
            
            def read_output():
                while True:
                    line = self._process.stdout.readline()
                    if not line:
                        break
                    output_buffer.append(line)
            
            reader_thread = threading.Thread(target=read_output, daemon=True)
            reader_thread.start()
            
            poll_start = time.time()
            while time.time() - poll_start < self.server_start_timeout:
                stdout_capture = "".join(output_buffer)
                detected_port = parse_port_from_stdout(stdout_capture, framework.value)
                if detected_port:
                    break
                
                if self._process.poll() is not None:
                    break
                
                time.sleep(0.2)
            
            stdout_capture = "".join(output_buffer)
            if not detected_port:
                detected_port = parse_port_from_stdout(stdout_capture, framework.value)
            
            detected_url = f"http://localhost:{detected_port}" if detected_port else None
            
            return ServerStartupInfo(
                command=command,
                detected_port=detected_port,
                detected_url=detected_url,
                stdout_capture=stdout_capture,
                stderr_capture=stderr_capture,
                process_id=self._process.pid if self._process else None,
                startup_duration_seconds=(datetime.now() - startup_start).total_seconds(),
            )
            
        except (subprocess.SubprocessError, OSError) as e:
            return ServerStartupInfo(
                command=command,
                stderr_capture=str(e),
                startup_duration_seconds=(datetime.now() - startup_start).total_seconds(),
            )
    
    def _probe_readiness(self, url: str) -> ReadinessProbeInfo:
        """Probe server readiness with timeout (Feature 062 section 6.3)."""
        probe_start = datetime.now()
        probe_attempts = 0
        
        ready, status_code = probe_url_readiness(url, self.readiness_probe_timeout)
        probe_attempts = int(self.readiness_probe_timeout / DEFAULT_READINESS_PROBE_INTERVAL_SECONDS)
        
        return ReadinessProbeInfo(
            target_url=url,
            probe_attempts=probe_attempts,
            successful_probe=ready,
            probe_duration_seconds=(datetime.now() - probe_start).total_seconds(),
            http_status_code=status_code,
        )
    
    def _persist_result(self, result: FrontendRecipeResult) -> str | None:
        """Persist structured execution result (Feature 062 section 6.5)."""
        import yaml
        
        results_dir = self.project_path / "execution-results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        result_path = results_dir / f"{self.execution_id}.md"
        
        execution_result = {
            "execution_id": self.execution_id,
            "status": "success" if result.success else "failed",
            "completed_items": ["frontend_verification_recipe_executed"],
            "artifacts_created": [],
            "verification_result": {
                "passed": result.browser_verification_result.get("passed", 0) if result.browser_verification_result else 0,
                "failed": result.browser_verification_result.get("failed", 0) if result.browser_verification_result else 0,
            },
            "browser_verification": result.browser_verification_result or {},
            "frontend_recipe": result.to_dict(),
            "issues_found": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Review frontend verification results",
        }
        
        content = f"""# ExecutionResult: {self.execution_id}

```yaml
{yaml.dump(execution_result, default_flow_style=False, sort_keys=False)}
```
"""
        
        try:
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(content)
            return str(result_path)
        except IOError:
            return None
    
    def _stop_server(self) -> None:
        """Stop dev server process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    self._process.kill()
                except ProcessLookupError:
                    pass
            self._process = None
    
    def _handle_failure(
        self,
        result: FrontendRecipeResult,
        reason: FrontendRecipeFailureReason,
        message: str,
    ) -> FrontendRecipeResult:
        """Handle failure at any stage with terminal outcome."""
        result.stage = FrontendRecipeStage.COMPLETED_FAILURE
        result.success = False
        result.failure_reason = reason
        result.error_message = message
        result.finished_at = datetime.now().isoformat()
        result.total_duration_seconds = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        # Still try to persist result for debugging
        self._persist_result(result)
        
        return result
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self._stop_server()


def execute_frontend_verification_recipe(
    project_path: Path,
    execution_id: str,
    server_start_timeout: int = DEFAULT_SERVER_START_TIMEOUT_SECONDS,
    readiness_probe_timeout: int = DEFAULT_READINESS_PROBE_TIMEOUT_SECONDS,
    browser_verification_timeout: int = DEFAULT_BROWSER_VERIFICATION_TIMEOUT_SECONDS,
) -> FrontendRecipeResult:
    """Convenience function for CLI integration (Feature 062 AC-001)."""
    recipe = FrontendVerificationRecipe(
        project_path=project_path,
        execution_id=execution_id,
        server_start_timeout=server_start_timeout,
        readiness_probe_timeout=readiness_probe_timeout,
        browser_verification_timeout=browser_verification_timeout,
    )
    
    result = recipe.execute()
    recipe.cleanup()
    
    return result