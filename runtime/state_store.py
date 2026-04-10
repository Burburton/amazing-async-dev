"""State store for file-based RunState and artifact management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from runtime.adapters.filesystem_adapter import FilesystemAdapter


class StateStore:
    """File-based state storage for RunState and other artifacts."""

    def __init__(self, project_path: Path | None = None):
        self.fs = FilesystemAdapter()
        self.project_path = project_path or Path("projects/demo-product")
        self.runstate_path = self.project_path / "runstate.md"
        self.execution_packs_path = self.project_path / "execution-packs"
        self.execution_results_path = self.project_path / "execution-results"
        self.reviews_path = self.project_path / "reviews"

    def load_runstate(self) -> dict[str, Any] | None:
        """Load RunState from markdown file with YAML block."""
        if not self.runstate_path.exists():
            return None

        content = self.fs.read_file(self.runstate_path)
        yaml_block = self._extract_yaml_block(content)

        if yaml_block:
            return yaml.safe_load(yaml_block)
        return None

    def save_runstate(self, runstate: dict[str, Any]) -> None:
        """Save RunState to markdown file."""
        runstate["updated_at"] = datetime.now().isoformat()

        self.fs.ensure_dir(self.project_path)
        self.fs.ensure_dir(self.execution_packs_path)
        self.fs.ensure_dir(self.execution_results_path)
        self.fs.ensure_dir(self.reviews_path)

        yaml_content = yaml.dump(runstate, default_flow_style=False, sort_keys=False)
        markdown_content = f"""# RunState

```yaml
{yaml_content}
```
"""
        self.fs.write_file(self.runstate_path, markdown_content)

    def load_execution_pack(self, execution_id: str) -> dict[str, Any] | None:
        """Load ExecutionPack by execution_id."""
        pack_path = self.execution_packs_path / f"{execution_id}.md"
        if not pack_path.exists():
            return None

        content = self.fs.read_file(pack_path)
        yaml_block = self._extract_yaml_block(content)

        if yaml_block:
            return yaml.safe_load(yaml_block)
        return None

    def save_execution_pack(self, execution_pack: dict[str, Any]) -> None:
        """Save ExecutionPack to markdown file."""
        execution_id = execution_pack["execution_id"]
        pack_path = self.execution_packs_path / f"{execution_id}.md"

        self.fs.ensure_dir(self.execution_packs_path)

        yaml_content = yaml.dump(execution_pack, default_flow_style=False, sort_keys=False)
        markdown_content = f"""# ExecutionPack

```yaml
{yaml_content}
```
"""
        self.fs.write_file(pack_path, markdown_content)

    def load_execution_result(self, execution_id: str) -> dict[str, Any] | None:
        """Load ExecutionResult by execution_id."""
        result_path = self.execution_results_path / f"{execution_id}.md"
        if not result_path.exists():
            return None

        content = self.fs.read_file(result_path)
        yaml_block = self._extract_yaml_block(content)

        if yaml_block:
            return yaml.safe_load(yaml_block)
        return None

    def save_execution_result(self, execution_result: dict[str, Any]) -> None:
        """Save ExecutionResult to markdown file."""
        execution_id = execution_result["execution_id"]
        result_path = self.execution_results_path / f"{execution_id}.md"

        self.fs.ensure_dir(self.execution_results_path)

        yaml_content = yaml.dump(execution_result, default_flow_style=False, sort_keys=False)
        markdown_content = f"""# ExecutionResult

```yaml
{yaml_content}
```
"""
        self.fs.write_file(result_path, markdown_content)

    def load_daily_review_pack(self, date: str) -> dict[str, Any] | None:
        """Load DailyReviewPack by date."""
        review_path = self.reviews_path / f"{date}-review.md"
        if not review_path.exists():
            return None

        content = self.fs.read_file(review_path)
        yaml_block = self._extract_yaml_block(content)

        if yaml_block:
            return yaml.safe_load(yaml_block)
        return None

    def save_daily_review_pack(self, review_pack: dict[str, Any]) -> None:
        """Save DailyReviewPack to markdown file."""
        date = review_pack["date"]
        review_path = self.reviews_path / f"{date}-review.md"

        self.fs.ensure_dir(self.reviews_path)

        yaml_content = yaml.dump(review_pack, default_flow_style=False, sort_keys=False)
        markdown_content = f"""# DailyReviewPack

```yaml
{yaml_content}
```
"""
        self.fs.write_file(review_path, markdown_content)

    def _extract_yaml_block(self, content: str) -> str | None:
        """Extract YAML block from markdown content."""
        lines = content.split("\n")
        yaml_start = None
        yaml_end = None

        for i, line in enumerate(lines):
            if line.strip() == "```yaml":
                yaml_start = i + 1
            elif yaml_start is not None and line.strip() == "```":
                yaml_end = i
                break

        if yaml_start is not None and yaml_end is not None:
            return "\n".join(lines[yaml_start:yaml_end])
        return None


def generate_execution_id() -> str:
    """Generate unique execution_id following pattern exec-YYYYMMDD-###."""
    date_str = datetime.now().strftime("%Y%m%d")
    counter = 1

    project_path = Path("projects/demo-product")
    execution_packs_path = project_path / "execution-packs"

    if execution_packs_path.exists():
        existing = list(execution_packs_path.glob(f"exec-{date_str}-*.md"))
        if existing:
            counter = len(existing) + 1

    return f"exec-{date_str}-{counter:03d}"


def update_runstate_from_result(
    runstate: dict[str, Any], execution_result: dict[str, Any]
) -> dict[str, Any]:
    """Update RunState fields from ExecutionResult."""
    runstate["completed_outputs"] = runstate.get("completed_outputs", []) + execution_result.get(
        "completed_items", []
    )

    runstate["blocked_items"] = runstate.get("blocked_items", []) + execution_result.get(
        "blocked_reasons", []
    )

    runstate["decisions_needed"] = runstate.get("decisions_needed", []) + execution_result.get(
        "decisions_required", []
    )

    runstate["next_recommended_action"] = execution_result.get("recommended_next_step", "")

    runstate["last_action"] = f"Completed execution {execution_result.get('execution_id', '')}"

    status = execution_result.get("status", "success")
    if status == "blocked":
        runstate["current_phase"] = "blocked"
    elif status == "success" or status == "partial":
        runstate["current_phase"] = "reviewing"
    else:
        runstate["current_phase"] = "executing"

    runstate["updated_at"] = datetime.now().isoformat()

    return runstate