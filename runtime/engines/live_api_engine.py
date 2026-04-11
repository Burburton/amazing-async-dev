"""Live API Engine - direct execution via BailianLLMAdapter.

Executes tasks by calling the LLM API directly,
parsing structured output into ExecutionResult.
"""

from pathlib import Path
from typing import Any

from runtime.engines.base import ExecutionEngine
from runtime.adapters.llm_adapter import BailianLLMAdapter
from runtime.execution_event_types import ExecutionEventType
from runtime.execution_logger import ExecutionLogger
from runtime.api_failure_types import APIFailureClassification


class LiveAPIEngine(ExecutionEngine):
    """Execution engine that calls LLM API directly.

    Uses BailianLLMAdapter (OpenAI-compatible) to:
    1. Send ExecutionPack as structured prompt
    2. Receive LLM response
    3. Parse response into ExecutionResult

    Requires DASHSCOPE_API_KEY environment variable.
    """

    def __init__(self, project_path: Path | None = None) -> None:
        self.adapter = BailianLLMAdapter()
        self.project_path = project_path or Path("projects/demo-product")
        self._logger: ExecutionLogger | None = None

    def _get_logger(self) -> ExecutionLogger:
        if self._logger is None:
            self._logger = ExecutionLogger(self.project_path)
        return self._logger

    def run(
        self,
        execution_pack: dict[str, Any],
        feature_spec: dict[str, Any] | None = None,
        runstate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute via API and return ExecutionResult."""
        logger = self._get_logger()
        
        feature_id = runstate.get("feature_id", "") if runstate else ""
        product_id = runstate.get("project_id", "") if runstate else ""
        
        logger.log_event(
            ExecutionEventType.RUN_DAY_STARTED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"execution_id": execution_pack.get("execution_id"), "mode": "live"},
        )

        result = self.adapter.execute(execution_pack)

        logger.log_event(
            ExecutionEventType.EXECUTION_RESULT_COLLECTED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={
                "execution_id": execution_pack.get("execution_id"),
                "status": result.get("status", "unknown"),
                "api_failure": result.get("api_failure_classification"),
            },
        )

        if result.get("api_failure_classification"):
            failure = APIFailureClassification(result["api_failure_classification"])
            logger.log_event(
                ExecutionEventType.FAILED_ENTERED,
                feature_id=feature_id,
                product_id=product_id,
                event_data={"failure_type": failure.value},
            )

        return result

    def prepare(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """Validate the pack structure for live mode."""
        required_fields = ["execution_id", "goal", "task_scope", "deliverables"]
        missing = [f for f in required_fields if f not in execution_pack]

        return {
            "status": "ready" if not missing else "invalid",
            "missing_fields": missing,
            "mode": "live",
            "model": self.adapter.model,
            "timeout": self.adapter.timeout,
            "max_retries": self.adapter.max_retries,
        }

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return self.adapter.is_available()

    def get_mode_name(self) -> str:
        return "live"

    def close(self) -> None:
        """Close logger connection."""
        if self._logger:
            self._logger.close()
            self._logger = None