"""ExecutionEngine abstract base class.

Defines the interface that all execution engines must implement.
"""

from abc import ABC, abstractmethod
from typing import Any


class ExecutionEngine(ABC):
    """Abstract interface for execution engines.

    All engines (external, live, mock) must implement this interface
    to ensure consistent behavior across execution modes.

    The engine is responsible for:
    - Consuming ExecutionPack, FeatureSpec, RunState
    - Producing ExecutionResult (or None for external mode)
    - Maintaining consistent input/output contracts
    """

    @abstractmethod
    def run(
        self,
        execution_pack: dict[str, Any],
        feature_spec: dict[str, Any] | None = None,
        runstate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute the task defined in ExecutionPack.

        Args:
            execution_pack: Bounded task definition with constraints
            feature_spec: Optional feature context for execution
            runstate: Optional current state for context

        Returns:
            ExecutionResult dict for live/mock modes
            None for external mode (awaiting external execution)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is available and configured.

        Returns:
            True if engine can execute, False otherwise
        """
        pass

    @abstractmethod
    def get_mode_name(self) -> str:
        """Get the mode name for this engine.

        Returns:
            Mode identifier: 'external', 'live', or 'mock'
        """
        pass

    @abstractmethod
    def prepare(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """Prepare execution environment before run.

        Args:
            execution_pack: Task definition to prepare for

        Returns:
            Preparation result with paths, status, instructions
        """
        pass