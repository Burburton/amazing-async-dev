r"""Shell configuration loader for cross-platform subprocess handling.

Provides configuration for forcing bash execution on Windows instead of cmd.exe.

Configuration priority:
1. Environment variables (ASYNCDEV_BASH_EXECUTABLE, ASYNCDEV_FORCE_BASH)
2. Config file (.runtime/shell-config.yaml)
3. Platform defaults (cmd.exe on Windows, bash on Unix)

Windows Bash Invocation:
- Uses direct bash invocation (--norc --noprofile -c) to avoid startup script issues
- Path conversion: Windows paths to Unix paths for bash
- Does NOT use shell=True + cwd combination (causes directory errors)
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union

import yaml


DEFAULT_CONFIG_PATH = Path(".runtime/shell-config.yaml")

BASH_CLEAN_FLAGS = ["--norc", "--noprofile"]


class ShellConfig:
    """Shell execution configuration.
    
    Handles loading and resolution of shell executable paths for subprocess calls.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config_data: dict = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file if exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    self._config_data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError):
                self._config_data = {}
    
    @property
    def windows_bash_executable(self) -> Optional[str]:
        """Get bash executable path for Windows.
        
        Priority: env var > config file
        """
        # Environment variable override
        env_path = os.getenv("ASYNCDEV_BASH_EXECUTABLE")
        if env_path:
            return env_path
        
        # Config file
        return self._config_data.get("windows_bash_executable")
    
    @property
    def force_bash(self) -> bool:
        """Check if bash should be forced on all platforms.
        
        Priority: env var > config file > default (false)
        """
        env_force = os.getenv("ASYNCDEV_FORCE_BASH")
        if env_force:
            return env_force.lower() == "true"
        
        return self._config_data.get("force_bash", False)
    
    @property
    def shell_type(self) -> str:
        """Get preferred shell type.
        
        Returns: "auto", "bash", or "sh"
        """
        return self._config_data.get("shell_type", "auto")
    
    def get_executable(self) -> Optional[str]:
        """Get the shell executable for subprocess.Popen.
        
        Returns:
            - On Windows with bash config: path to bash executable
            - On Windows without bash config: None (use cmd.exe default)
            - On Unix with force_bash: "bash" or configured path
            - On Unix without force_bash: None (use platform default)
        """
        # Unix platforms
        if sys.platform != "win32":
            if self.force_bash:
                return self.windows_bash_executable or "bash"
            return None
        
        # Windows platform
        if self.shell_type == "bash" or self.force_bash:
            return self.windows_bash_executable or "bash"
        
        if self.shell_type == "sh":
            return self.windows_bash_executable or "sh"
        
        # auto mode - check if bash executable configured
        if self.windows_bash_executable:
            return self.windows_bash_executable
        
        return None
    
    def should_use_shell(self) -> bool:
        """Determine if shell=True should be used.
        
        On Windows, shell=True is generally needed for npm commands.
        On Unix, shell=True is optional but may be needed for some commands.
        """
        if sys.platform == "win32":
            return True
        
        # Unix with force_bash
        if self.force_bash:
            return True
        
        return False
    
    def get_popen_kwargs(self, cwd: Path) -> dict:
        """Get subprocess.Popen kwargs for shell execution.
        
        Args:
            cwd: Working directory for subprocess
            
        Returns:
            dict with appropriate kwargs including executable if configured
        """
        kwargs = {
            "stdout": None,  # Will be overridden by caller
            "stderr": None,
            "text": True,
            "cwd": cwd,
        }
        
        executable = self.get_executable()
        
        if sys.platform == "win32":
            kwargs["shell"] = True
            if executable:
                kwargs["executable"] = executable
        elif self.force_bash or self.shell_type in ("bash", "sh"):
            kwargs["shell"] = True
            if executable:
                kwargs["executable"] = executable
        
        return kwargs


# Global instance for convenience
_shell_config: Optional[ShellConfig] = None


def get_shell_config(config_path: Optional[Path] = None) -> ShellConfig:
    """Get or create shell config instance.
    
    Args:
        config_path: Optional custom config path
        
    Returns:
        ShellConfig instance
    """
    global _shell_config
    
    if _shell_config is None or config_path is not None:
        _shell_config = ShellConfig(config_path)
    
    return _shell_config


def get_bash_executable() -> Optional[str]:
    """Convenience function to get bash executable path.
    
    Returns:
        Bash executable path if configured, None otherwise
    """
    return get_shell_config().get_executable()


def should_use_bash_on_windows() -> bool:
    """Check if bash should be used on Windows platform.
    
    Returns:
        True if bash executable is configured for Windows
    """
    config = get_shell_config()
    return sys.platform == "win32" and config.get_executable() is not None


def windows_path_to_bash_path(path: Union[str, Path]) -> str:
    path_str = str(path)
    path_str = path_str.replace(chr(92), '/')
    for drive in ['C:', 'D:', 'E:', 'F:', 'G:', 'H:', 'I:', 'J:', 'K:', 'L:', 'M:', 'N:', 'O:', 'P:', 'Q:', 'R:', 'S:', 'T:', 'U:', 'V:', 'W:', 'X:', 'Y:', 'Z:']:
        path_str = path_str.replace(drive, '/' + drive[0].lower())
    return path_str


class BashPopenBuilder:
    
    def __init__(self, shell_config: ShellConfig):
        self.config = shell_config
    
    def build(self, cwd: Path, command: list[str]) -> tuple[list[str], dict]:
        executable = self.config.get_executable()
        
        if sys.platform == "win32" and executable:
            bash_cwd = windows_path_to_bash_path(cwd)
            command_str = " ".join(command)
            bash_command = f"cd '{bash_cwd}' && {command_str}"
            
            args = [executable] + BASH_CLEAN_FLAGS + ["-c", bash_command]
            kwargs = {
                "stdout": None,
                "stderr": None,
                "text": True,
            }
            return args, kwargs
        
        return command, {
            "cwd": cwd,
            "stdout": None,
            "stderr": None,
            "text": True,
        }


def build_bash_popen(cwd: Path, command: list[str]) -> tuple[list[str], dict]:
    config = get_shell_config()
    builder = BashPopenBuilder(config)
    return builder.build(cwd, command)