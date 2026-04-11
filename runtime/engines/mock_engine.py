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
    - Can simulate failure/blocked scenarios for testing
    """

    def __init__(self, simulate: str = "success") -> None:
        self.simulate_mode = simulate

    def run(
        self,
        execution_pack: dict[str, Any],
        feature_spec: dict[str, Any] | None = None,
        runstate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Return mock ExecutionResult with configurable scenario.

        Scenarios:
        - "success": Normal completion
        - "blocked": Blocked state with blocker reason
        - "failed": Failed execution
        - "decision": Decision needed
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

        if self.simulate_mode == "blocked":
            return {
                "execution_id": execution_id,
                "status": "blocked",
                "completed_items": [],
                "artifacts_created": [],
                "verification_result": {"passed": 0, "failed": 1, "skipped": 0, "details": []},
                "issues_found": ["Simulated blocker"],
                "blocked_reasons": [{
                    "reason": "Missing dependency: external-service",
                    "resolution": "Wait for external service to be available",
                    "options": ["Retry in 1 hour", "Use fallback", "Escalate"],
                }],
                "decisions_required": [],
                "recommended_next_step": "Use 'asyncdev resume-next-day unblock' to resolve",
                "metrics": {"files_read": 0, "files_written": 0, "actions_taken": 1},
                "notes": "Mock blocked scenario for testing",
                "duration": "0h1m",
            }

        elif self.simulate_mode == "failed":
            return {
                "execution_id": execution_id,
                "status": "failed",
                "completed_items": [],
                "artifacts_created": [],
                "verification_result": {"passed": 0, "failed": 3, "skipped": 0, "details": []},
                "issues_found": [
                    "File not found: required-config.yaml",
                    "Permission denied: cannot write to output/",
                    "Unexpected error: runtime crash",
                ],
                "blocked_reasons": [],
                "decisions_required": [],
                "recommended_next_step": "Use 'asyncdev resume-next-day handle-failed' to manage",
                "metrics": {"files_read": 0, "files_written": 0, "actions_taken": 0},
                "notes": "Mock failed scenario for testing",
                "duration": "0h0m",
            }

        elif self.simulate_mode == "decision":
            return {
                "execution_id": execution_id,
                "status": "partial",
                "completed_items": ["Partial deliverable"],
                "artifacts_created": artifacts[:1] if artifacts else [],
                "verification_result": {"passed": 1, "failed": 1, "skipped": 1, "details": []},
                "issues_found": ["Scope ambiguity detected"],
                "blocked_reasons": [],
                "decisions_required": [{
                    "decision": "Choose implementation approach",
                    "options": ["Simple solution (fast)", "Robust solution (slower)", "Defer to next iteration"],
                    "recommendation": "Simple solution for MVP",
                    "impact": "Affects delivery timeline",
                    "urgency": "medium",
                }],
                "recommended_next_step": "Run 'asyncdev resume-next-day continue-loop --decision approve'",
                "metrics": {"files_read": 1, "files_written": 1, "actions_taken": 2},
                "notes": "Mock decision scenario for testing",
                "duration": "0h2m",
            }

        else:
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