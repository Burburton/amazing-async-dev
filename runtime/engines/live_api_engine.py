"""Live API Engine - direct execution via BailianLLMAdapter.

Executes tasks by calling the LLM API directly,
parsing structured output into ExecutionResult.
"""

from typing import Any

from runtime.engines.base import ExecutionEngine
from runtime.adapters.llm_adapter import BailianLLMAdapter


class LiveAPIEngine(ExecutionEngine):
    """Execution engine that calls LLM API directly.

    Uses BailianLLMAdapter (OpenAI-compatible) to:
    1. Send ExecutionPack as structured prompt
    2. Receive LLM response
    3. Parse response into ExecutionResult

    Requires DASHSCOPE_API_KEY environment variable.
    """

    def __init__(self) -> None:
        self.adapter = BailianLLMAdapter()

    def run(
        self,
        execution_pack: dict[str, Any],
        feature_spec: dict[str, Any] | None = None,
        runstate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute via API and return ExecutionResult.

        Calls BailianLLMAdapter.execute() which:
        - Builds prompt from ExecutionPack
        - Calls qwen model
        - Parses output into ExecutionResult dict
        """
        return self.adapter.execute(execution_pack)

    def prepare(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """No preparation needed for live mode.

        Just validates the pack structure.
        """
        required_fields = ["execution_id", "goal", "task_scope", "deliverables"]
        missing = [f for f in required_fields if f not in execution_pack]

        return {
            "status": "ready" if not missing else "invalid",
            "missing_fields": missing,
            "mode": "live",
            "model": self.adapter.model,
        }

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return self.adapter.is_available()

    def get_mode_name(self) -> str:
        return "live"