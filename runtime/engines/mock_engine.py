"""Mock Engine - testing and demonstration execution.

Returns fake ExecutionResult without calling any API.
"""

from typing import Any

from runtime.engines.base import ExecutionEngine


class MockEngine(ExecutionEngine):
    """Execution engine for testing and demonstration.

    Generates fake ExecutionResult:
    - Pretends all deliverables were completed
    - No real execution or API calls
    - Useful for testing the workflow flow
    """

    def run(
        self,
        execution_pack: dict[str, Any],
        feature_spec: dict[str, Any] | None = None,
        runstate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return mock ExecutionResult.

        Pretends execution succeeded with all deliverables.
        """
        execution_id = execution_pack.get("execution_id", "mock-exec")

        deliverables = execution_pack.get("deliverables", [])
        artifacts = [
            {
                "name": d.get("item", "unknown"),
                "path": d.get("path", "unknown"),
                "type": d.get("type", "file"),
            }
            for d in deliverables
        ]

        return {
            "execution_id": execution_id,
            "status": "success",
            "completed_items": [d.get("item", "unknown") for d in deliverables],
            "artifacts_created": artifacts,
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
                "files_written": len(artifacts),
                "actions_taken": 5,
            },
            "notes": "Mock execution - no real processing",
            "duration": "0h5m",
        }

    def prepare(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """No preparation needed for mock."""
        return {
            "status": "ready",
            "mode": "mock",
        }

    def is_available(self) -> bool:
        """Mock engine is always available."""
        return True

    def get_mode_name(self) -> str:
        return "mock"