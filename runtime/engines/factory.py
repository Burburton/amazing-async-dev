"""ExecutionEngine factory - creates engine by mode.

Provides get_engine() function to select appropriate engine.
"""

from pathlib import Path

from runtime.engines.base import ExecutionEngine
from runtime.engines.external_tool_engine import ExternalToolEngine
from runtime.engines.live_api_engine import LiveAPIEngine
from runtime.engines.mock_engine import MockEngine


def get_engine(
    mode: str = "external",
    simulate: str = "success",
    project_path: Path | None = None,
) -> ExecutionEngine:
    """Get execution engine for specified mode.

    Args:
        mode: Execution mode - 'external', 'live', or 'mock'
              Defaults to 'external' (primary mode per design doc)
        simulate: Simulation scenario for mock mode
              'success' (default), 'blocked', 'failed', 'decision'
        project_path: Project path for persistence (live mode)

    Returns:
        ExecutionEngine instance for the mode

    Raises:
        ValueError: If mode is not recognized
    """
    if mode == "external":
        return ExternalToolEngine()
    elif mode == "live":
        return LiveAPIEngine(project_path)
    elif mode == "mock":
        return MockEngine(simulate=simulate)
    else:
        raise ValueError(
            f"Unknown execution mode: {mode}. "
            f"Valid modes: external, live, mock"
        )


def get_available_modes(project_path: Path | None = None) -> dict[str, bool]:
    """Check availability of all execution modes.

    Returns:
        dict mapping mode name to availability status
    """
    return {
        "external": ExternalToolEngine().is_available(),
        "live": LiveAPIEngine(project_path).is_available(),
        "mock": MockEngine().is_available(),
    }