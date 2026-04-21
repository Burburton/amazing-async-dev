"""Dev Server Manager - Feature 056.

Manages dev server lifecycle for frontend verification:
- Auto-start dev server (Vite, Next.js, React)
- Poll for server readiness
- Handle long-running processes
- Cleanup after verification
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.shell_config import get_shell_config, ShellConfig, BASH_CLEAN_FLAGS, windows_path_to_bash_path


class DevServerFramework(str, Enum):
    """Supported frontend frameworks."""
    VITE = "vite"
    NEXT_JS = "next"
    REACT = "react"
    NUXT = "nuxt"
    SVELTEKIT = "sveltekit"
    UNKNOWN = "unknown"


DEFAULT_PORTS = {
    DevServerFramework.VITE: 5173,
    DevServerFramework.NEXT_JS: 3000,
    DevServerFramework.REACT: 3000,
    DevServerFramework.NUXT: 3000,
    DevServerFramework.SVELTEKIT: 5173,
    DevServerFramework.UNKNOWN: 3000,
}

PORT_RANGE = [3000, 3001, 3002, 3003, 3004, 3005, 3006, 5173, 5174, 5175]

POLL_TIMEOUT_SECONDS = 60
POLL_INTERVAL_SECONDS = 2


@dataclass
class DevServerStatus:
    """Dev server status."""
    running: bool
    port: int | None
    url: str | None
    framework: DevServerFramework
    process_id: int | None
    started_at: str | None
    error_message: str | None


@dataclass
class DevServerResult:
    """Result of dev server operation."""
    success: bool
    status: DevServerStatus
    duration_seconds: float


def detect_framework(project_path: Path) -> DevServerFramework:
    """Detect frontend framework from project config files."""
    package_json = project_path / "package.json"
    
    if not package_json.exists():
        return DevServerFramework.UNKNOWN
    
    try:
        with open(package_json) as f:
            pkg = json.load(f)
    except (json.JSONDecodeError, IOError):
        return DevServerFramework.UNKNOWN
    
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}
    
    if "next" in all_deps:
        return DevServerFramework.NEXT_JS
    
    if "vite" in all_deps:
        return DevServerFramework.VITE
    
    if "react-scripts" in all_deps:
        return DevServerFramework.REACT
    
    if "nuxt" in all_deps:
        return DevServerFramework.NUXT
    
    if "@sveltejs/kit" in all_deps:
        return DevServerFramework.SVELTEKIT
    
    return DevServerFramework.UNKNOWN


def get_start_command(framework: DevServerFramework) -> list[str]:
    """Get dev server start command for framework."""
    commands = {
        DevServerFramework.VITE: ["npm", "run", "dev"],
        DevServerFramework.NEXT_JS: ["npm", "run", "dev"],
        DevServerFramework.REACT: ["npm", "start"],
        DevServerFramework.NUXT: ["npm", "run", "dev"],
        DevServerFramework.SVELTEKIT: ["npm", "run", "dev"],
        DevServerFramework.UNKNOWN: ["npm", "run", "dev"],
    }
    return commands.get(framework, ["npm", "run", "dev"])


def poll_server_ready(url: str, timeout: int = POLL_TIMEOUT_SECONDS) -> bool:
    """Poll server until ready or timeout."""
    import socket
    import urllib.request
    import urllib.error
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req, timeout=5)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, ConnectionError):
            time.sleep(POLL_INTERVAL_SECONDS)
    
    return False


def find_available_port() -> int:
    """Find an available port in the configured range."""
    import socket
    
    for port in PORT_RANGE:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    
    return PORT_RANGE[0]


def start_dev_server(
    project_path: Path,
    port: int | None = None,
    timeout: int = POLL_TIMEOUT_SECONDS,
) -> DevServerResult:
    """Start dev server and wait for readiness.
    
    Args:
        project_path: Project root directory
        port: Optional port to use (auto-detect if None)
        timeout: Timeout in seconds to wait for server
        
    Returns:
        DevServerResult with status
    """
    start_time = time.time()
    
    framework = detect_framework(project_path)
    
    if framework == DevServerFramework.UNKNOWN:
        return DevServerResult(
            success=False,
            status=DevServerStatus(
                running=False,
                port=None,
                url=None,
                framework=framework,
                process_id=None,
                started_at=None,
                error_message="Could not detect frontend framework",
            ),
            duration_seconds=0,
        )
    
    target_port = port or DEFAULT_PORTS.get(framework, 3000)
    url = f"http://localhost:{target_port}"
    
    command = get_start_command(framework)
    
    shell_config_path = project_path / ".runtime" / "shell-config.yaml"
    shell_config = ShellConfig(shell_config_path)
    executable = shell_config.get_executable()
    
    if sys.platform == "win32" and executable:
        bash_cwd = windows_path_to_bash_path(project_path)
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
            "cwd": project_path,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
    
    try:
        process = subprocess.Popen(popen_args, **popen_kwargs)
    except (subprocess.SubprocessError, OSError) as e:
        return DevServerResult(
            success=False,
            status=DevServerStatus(
                running=False,
                port=target_port,
                url=url,
                framework=framework,
                process_id=None,
                started_at=None,
                error_message=str(e),
            ),
            duration_seconds=time.time() - start_time,
        )
    
    ready = poll_server_ready(url, timeout)
    duration = time.time() - start_time
    
    if not ready:
        process.terminate()
        return DevServerResult(
            success=False,
            status=DevServerStatus(
                running=False,
                port=target_port,
                url=url,
                framework=framework,
                process_id=process.pid,
                started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                error_message=f"Server not ready after {timeout}s",
            ),
            duration_seconds=duration,
        )
    
    return DevServerResult(
        success=True,
        status=DevServerStatus(
            running=True,
            port=target_port,
            url=url,
            framework=framework,
            process_id=process.pid,
            started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            error_message=None,
        ),
        duration_seconds=duration,
    )


def stop_dev_server(process_id: int | None) -> bool:
    """Stop dev server by process ID."""
    if not process_id:
        return True
    
    try:
        import signal
        import os
        os.kill(process_id, signal.SIGTERM)
        time.sleep(2)
        return True
    except (ProcessLookupError, OSError):
        return False


class DevServerManager:
    """Dev server lifecycle manager."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self._process_id: int | None = None
        self._status: DevServerStatus | None = None
    
    def start(self, port: int | None = None, timeout: int = POLL_TIMEOUT_SECONDS) -> DevServerResult:
        """Start dev server."""
        result = start_dev_server(self.project_path, port, timeout)
        
        if result.success:
            self._process_id = result.status.process_id
            self._status = result.status
        
        return result
    
    def stop(self) -> bool:
        """Stop dev server."""
        success = stop_dev_server(self._process_id)
        
        if success:
            self._process_id = None
            self._status = None
        
        return success
    
    def get_status(self) -> DevServerStatus | None:
        """Get current dev server status."""
        return self._status
    
    def get_url(self) -> str | None:
        """Get dev server URL."""
        if self._status:
            return self._status.url
        return None
    
    def is_running(self) -> bool:
        """Check if dev server is running."""
        if self._status:
            return self._status.running
        return False