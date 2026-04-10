"""LLM adapter interface - defines interface for AI execution."""

from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    """Abstract interface for LLM/AI execution adapters."""

    @abstractmethod
    def execute(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """Execute task defined in ExecutionPack and return ExecutionResult.

        Args:
            execution_pack: Bounded task definition

        Returns:
            ExecutionResult with completion status, artifacts, and decisions
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if adapter is available and configured."""
        pass


class MockLLMAdapter(LLMAdapter):
    """Mock adapter for testing and demonstration."""

    def execute(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """Return mock ExecutionResult."""
        return {
            "execution_id": execution_pack.get("execution_id", "mock-exec"),
            "status": "success",
            "completed_items": execution_pack.get("deliverables", []),
            "artifacts_created": [
                {
                    "name": d.get("item", ""),
                    "path": d.get("path", ""),
                    "type": d.get("type", "file"),
                }
                for d in execution_pack.get("deliverables", [])
            ],
            "verification_result": {
                "passed": len(execution_pack.get("verification_steps", [])),
                "failed": 0,
                "skipped": 0,
                "details": execution_pack.get("verification_steps", []),
            },
            "issues_found": [],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": "Mock execution completed. Ready for next task.",
            "metrics": {
                "files_read": len(execution_pack.get("must_read", [])),
                "files_written": len(execution_pack.get("deliverables", [])),
                "actions_taken": 5,
                "decisions_made": 0,
            },
            "notes": "Mock execution - no real AI processing",
            "duration": "0h5m",
        }

    def is_available(self) -> bool:
        """Mock adapter is always available."""
        return True


class PlaceholderLLMAdapter(LLMAdapter):
    """Placeholder adapter - raises error when called."""

    def execute(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """Raise error - not implemented yet."""
        raise NotImplementedError(
            "LLM adapter not implemented. "
            "Use --mock mode for testing, or implement a real adapter."
        )

    def is_available(self) -> bool:
        """Placeholder is never available."""
        return False


def get_adapter(mock: bool = False) -> LLMAdapter:
    """Get appropriate LLM adapter based on mode.

    Args:
        mock: If True, return MockLLMAdapter for testing

    Returns:
        LLMAdapter instance
    """
    if mock:
        return MockLLMAdapter()
    return PlaceholderLLMAdapter()