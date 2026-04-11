"""LLM adapter interface - defines interface for AI execution."""

import os
import time
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from runtime.api_failure_types import (
    APIFailureClassification,
    classify_api_error,
    is_retryable,
    get_recovery_hint,
)


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


class BailianLLMAdapter(LLMAdapter):
    """Real adapter using Alibaba Cloud Bailian API via OpenAI-compatible interface.

    Uses DASHSCOPE_API_KEY environment variable for authentication.
    Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
    Default model: qwen-plus (can be overridden via DASHSCOPE_MODEL env var)
    """

    DEFAULT_TIMEOUT = 120
    DEFAULT_MAX_RETRIES = 2
    DEFAULT_RETRY_DELAY = 30

    def __init__(
        self,
        timeout: int | None = None,
        max_retries: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        """Initialize Bailian adapter with OpenAI-compatible client."""
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.model = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self.retry_delay = retry_delay or self.DEFAULT_RETRY_DELAY

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        else:
            self.client = None

    def execute(
        self,
        execution_pack: dict[str, Any],
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """Execute task via Bailian API with retry logic."""
        if not self.client:
            return self._create_failure_result(
                execution_pack,
                APIFailureClassification.AUTH_CONFIG_FAILURE,
                "DASHSCOPE_API_KEY not configured",
            )

        system_prompt = self._build_system_prompt(execution_pack)
        user_prompt = self._build_user_prompt(execution_pack)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            llm_output = response.choices[0].message.content or ""
            return self._parse_llm_output(execution_pack, llm_output)

        except Exception as e:
            failure = classify_api_error(e)

            if is_retryable(failure) and retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self.execute(execution_pack, retry_count + 1)

            return self._create_failure_result(
                execution_pack,
                failure,
                str(e),
                retry_count,
            )

    def _create_failure_result(
        self,
        execution_pack: dict[str, Any],
        failure: APIFailureClassification,
        error_message: str,
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """Create ExecutionResult for API failure."""
        recovery_hint = get_recovery_hint(failure)

        return {
            "execution_id": execution_pack.get("execution_id", "unknown"),
            "status": "failed",
            "completed_items": [],
            "artifacts_created": [],
            "verification_result": {"passed": 0, "failed": 1, "skipped": 0, "details": []},
            "issues_found": [error_message],
            "blocked_reasons": [],
            "decisions_required": [],
            "recommended_next_step": recovery_hint,
            "metrics": {
                "files_read": 0,
                "files_written": 0,
                "actions_taken": 0,
                "api_retries": retry_count,
            },
            "notes": f"API failure: {failure.value}",
            "duration": "0h0m",
            "api_failure_classification": failure.value,
        }

    def _build_system_prompt(self, execution_pack: dict[str, Any]) -> str:
        """Build system prompt from ExecutionPack constraints."""
        goal = execution_pack.get("goal", "Execute the assigned task")
        scope = execution_pack.get("task_scope", [])
        stop_conditions = execution_pack.get("stop_conditions", [])
        constraints = execution_pack.get("constraints", [])

        prompt_parts = [
            "You are an AI execution agent within the amazing-async-dev system.",
            "Your role is to execute bounded tasks and return structured results.",
            "",
            f"## Goal\n{goal}",
        ]

        if scope:
            prompt_parts.append(f"\n## Task Scope\nYou MUST stay within these boundaries:\n{self._format_list(scope)}")

        if stop_conditions:
            prompt_parts.append(f"\n## Stop Conditions\nYou MUST stop if any of these occur:\n{self._format_list(stop_conditions)}")

        if constraints:
            prompt_parts.append(f"\n## Constraints\n{self._format_list(constraints)}")

        prompt_parts.append(
            "\n## Output Format\n"
            "After completing your task, provide your results in this format:\n"
            "```\n"
            "COMPLETED_ITEMS:\n"
            "- [list what you completed]\n"
            "\n"
            "ARTIFACTS_CREATED:\n"
            "- name: [artifact name]\n"
            "- path: [where it would be saved]\n"
            "- type: file/document/code/etc\n"
            "\n"
            "ISSUES_FOUND:\n"
            "- [any problems encountered]\n"
            "\n"
            "BLOCKED_REASONS:\n"
            "- [if blocked, why]\n"
            "\n"
            "DECISIONS_REQUIRED:\n"
            "- [any decisions needed from human]\n"
            "\n"
            "NEXT_STEP:\n"
            "[recommended next action]\n"
            "```"
        )

        return "\n".join(prompt_parts)

    def _build_user_prompt(self, execution_pack: dict[str, Any]) -> str:
        """Build user prompt with deliverables and verification steps."""
        deliverables = execution_pack.get("deliverables", [])
        verification_steps = execution_pack.get("verification_steps", [])
        must_read = execution_pack.get("must_read", [])

        prompt_parts = ["## Your Task\nExecute the following deliverables:"]

        if deliverables:
            for d in deliverables:
                prompt_parts.append(f"- {d.get('item', 'unknown')}: {d.get('path', 'path not specified')}")

        if must_read:
            prompt_parts.append("\n## Files to Read\nYou should read these files for context:")
            for f in must_read:
                prompt_parts.append(f"- {f}")

        if verification_steps:
            prompt_parts.append("\n## Verification\nAfter completion, verify:")
            for v in verification_steps:
                prompt_parts.append(f"- {v}")

        prompt_parts.append("\nPlease execute and provide your results in the specified format.")

        return "\n".join(prompt_parts)

    def _format_list(self, items: list[Any]) -> str:
        """Format a list for prompt display."""
        if not items:
            return "(none specified)"
        return "\n".join(f"- {item}" for item in items)

    def _filter_empty(self, items: list[str]) -> list[str]:
        """Filter out empty/placeholder values like 'None', '(none)', ''."""
        empty_values = {"none", "(none)", "", "-", "n/a", "null"}
        return [i for i in items if i.lower().strip() not in empty_values]

    def _parse_llm_output(self, execution_pack: dict[str, Any], llm_output: str) -> dict[str, Any]:
        """Parse LLM output into ExecutionResult structure."""
        completed_items = self._extract_section(llm_output, "COMPLETED_ITEMS")
        artifacts = self._extract_artifacts(llm_output)
        issues = self._filter_empty(self._extract_section(llm_output, "ISSUES_FOUND"))
        blocked = self._filter_empty(self._extract_section(llm_output, "BLOCKED_REASONS"))
        decisions = self._filter_empty(self._extract_section(llm_output, "DECISIONS_REQUIRED"))
        next_step = self._extract_section(llm_output, "NEXT_STEP", single_line=True)

        status = "success"
        if blocked:
            status = "blocked"
        elif issues:
            status = "partial"

        return {
            "execution_id": execution_pack.get("execution_id", "unknown"),
            "status": status,
            "completed_items": completed_items if completed_items else execution_pack.get("deliverables", []),
            "artifacts_created": artifacts if artifacts else [],
            "verification_result": {
                "passed": len(completed_items) if completed_items else 0,
                "failed": len(issues) if issues else 0,
                "skipped": 0,
                "details": execution_pack.get("verification_steps", []),
            },
            "issues_found": issues if issues else [],
            "blocked_reasons": blocked if blocked else [],
            "decisions_required": decisions if decisions else [],
            "recommended_next_step": next_step if next_step else "Continue with next task",
            "metrics": {
                "files_read": len(execution_pack.get("must_read", [])),
                "files_written": len(artifacts) if artifacts else 0,
                "actions_taken": len(completed_items) if completed_items else 0,
            },
            "notes": llm_output[:500] if llm_output else "No LLM output",
            "duration": "estimated",
        }

    def _extract_section(self, text: str, section_name: str, single_line: bool = False) -> list[str] | str:
        """Extract a section from formatted LLM output."""
        lines = text.split("\n")
        result: list[str] = []
        in_section = False

        for line in lines:
            if line.strip().startswith(section_name):
                in_section = True
                continue
            if in_section:
                if line.strip() and not line.strip().startswith("-"):
                    # End of section (next section header)
                    if single_line:
                        return " ".join(result) if result else ""
                    return result if result else []
                if line.strip().startswith("-"):
                    result.append(line.strip()[1:].strip())

        if single_line:
            return " ".join(result) if result else ""
        return result if result else []

    def _extract_artifacts(self, text: str) -> list[dict[str, str]]:
        """Extract artifacts section from LLM output."""
        lines = text.split("\n")
        artifacts: list[dict[str, str]] = []
        in_artifacts = False
        current_artifact: dict[str, str] = {}

        for line in lines:
            if line.strip().startswith("ARTIFACTS_CREATED"):
                in_artifacts = True
                continue
            if in_artifacts:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped and not stripped.startswith("-") and not stripped.startswith("name:"):
                    # End of artifacts section
                    break
                if stripped.startswith("- name:"):
                    if current_artifact:
                        artifacts.append(current_artifact)
                    current_artifact = {"name": stripped[7:].strip()}
                elif stripped.startswith("- path:"):
                    current_artifact["path"] = stripped[7:].strip()
                elif stripped.startswith("- type:"):
                    current_artifact["type"] = stripped[7:].strip()

        if current_artifact:
            artifacts.append(current_artifact)

        return artifacts

    def is_available(self) -> bool:
        """Check if Bailian API is configured."""
        return self.api_key is not None and self.client is not None


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
        LLMAdapter instance (BailianLLMAdapter or MockLLMAdapter)
    """
    if mock:
        return MockLLMAdapter()
    return BailianLLMAdapter()