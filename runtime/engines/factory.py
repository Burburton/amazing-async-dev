"""ExecutionEngine factory - creates engine by mode.

Provides get_engine() function to select appropriate engine.
"""

from runtime.engines.base import ExecutionEngine
from runtime.engines.external_tool_engine import ExternalToolEngine
from runtime.engines.live_api_engine import LiveAPIEngine
from runtime.engines.mock_engine import MockEngine


def get_engine(mode: str = "external") -> ExecutionEngine:
    """Get execution engine for specified mode.

    Args:
        mode: Execution mode - 'external', 'live', or 'mock'
              Defaults to 'external' (primary mode per design doc)

    Returns:
        ExecutionEngine instance for the mode

    Raises:
        ValueError: If mode is not recognized

    Example:
        engine = get_engine("external")
        result = engine.prepare(execution_pack)
        # For external mode, run() returns None
        # Execution happens via external tool

        engine = get_engine("live")
        result = engine.run(execution_pack)
        # For live mode, returns ExecutionResult directly
    """
    if mode == "external":
        return ExternalToolEngine()
    elif mode == "live":
        return LiveAPIEngine()
    elif mode == "mock":
        return MockEngine()
    else:
        raise ValueError(
            f"Unknown execution mode: {mode}. "
            f"Valid modes: external, live, mock"
        )


def get_available_modes() -> dict[str, bool]:
    """Check availability of all execution modes.

    Returns:
        dict mapping mode name to availability status
    """
    return {
        "external": ExternalToolEngine().is_available(),
        "live": LiveAPIEngine().is_available(),
        "mock": MockEngine().is_available(),
    }