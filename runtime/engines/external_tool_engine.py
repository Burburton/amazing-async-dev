"""External Tool Engine - generates ExecutionPack for external AI tools.

Primary execution mode for amazing-async-dev:
- Outputs ExecutionPack in YAML and Markdown formats
- Provides instructions for triggering external tools
- Awaits external execution and result consumption
"""

import yaml
from pathlib import Path
from typing import Any

from runtime.engines.base import ExecutionEngine


class ExternalToolEngine(ExecutionEngine):
    """Execution engine that delegates to external AI tools.

    This mode:
    1. Saves ExecutionPack in dual format (YAML + Markdown)
    2. Outputs execution instructions for human/operator
    3. Returns None (execution happens externally)
    4. ExecutionResult is consumed later via resume-next-day

    The external tool (OpenCode, Claude Code, etc.) reads the
    ExecutionPack.md and writes ExecutionResult.md per AGENTS.md convention.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("projects/default/execution-packs")

    def run(
        self,
        execution_pack: dict[str, Any],
        feature_spec: dict[str, Any] | None = None,
        runstate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Prepare ExecutionPack for external execution.

        Does not execute directly - saves pack and returns None.
        External tool will read the pack and execute.
        """
        self.prepare(execution_pack)
        return None

    def prepare(self, execution_pack: dict[str, Any]) -> dict[str, Any]:
        """Save ExecutionPack in dual format and return instructions.

        Outputs:
        - {execution_id}.yaml - Machine-readable format
        - {execution_id}.md - Human/AI-readable format (for external tools)

        Returns:
            dict with paths and execution instructions
        """
        execution_id = execution_pack.get("execution_id", "exec-unknown")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        yaml_path = self.output_dir / f"{execution_id}.yaml"
        md_path = self.output_dir / f"{execution_id}.md"

        self._save_yaml(execution_pack, yaml_path)
        self._save_markdown(execution_pack, md_path)

        return {
            "status": "prepared",
            "execution_id": execution_id,
            "yaml_path": str(yaml_path),
            "md_path": str(md_path),
            "mode": "external",
            "instructions": self._build_instructions(execution_pack, md_path),
        }

    def _save_yaml(self, pack: dict[str, Any], path: Path) -> None:
        """Save ExecutionPack as YAML."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(pack, f, default_flow_style=False, sort_keys=False)

    def _save_markdown(self, pack: dict[str, Any], path: Path) -> None:
        """Save ExecutionPack as Markdown for external tools.

        Format designed for easy reading by OpenCode/Claude Code etc.
        """
        lines = [
            f"# ExecutionPack: {pack.get('execution_id', 'unknown')}",
            "",
            "## Goal",
            pack.get("goal", "No goal specified"),
            "",
            "## Task Scope",
            "**You MUST stay within these boundaries:**",
        ]

        for item in pack.get("task_scope", []):
            lines.append(f"- {item}")

        lines.extend([
            "",
            "## Constraints",
            "**You MUST NOT violate these:**",
        ])
        for c in pack.get("constraints", []):
            lines.append(f"- {c}")

        lines.extend([
            "",
            "## Files to Read",
            "**Read these before starting:**",
        ])
        for f in pack.get("must_read", []):
            lines.append(f"- {f}")

        lines.extend([
            "",
            "## Deliverables",
            "**Complete all of these:**",
        ])
        for d in pack.get("deliverables", []):
            lines.append(f"- **{d.get('item', 'unknown')}** → `{d.get('path', 'path')}`")

        lines.extend([
            "",
            "## Verification Steps",
            "**Verify after completion:**",
        ])
        for v in pack.get("verification_steps", []):
            lines.append(f"- {v}")

        lines.extend([
            "",
            "## Stop Conditions",
            "**Stop immediately if any occur:**",
        ])
        for s in pack.get("stop_conditions", []):
            lines.append(f"- {s}")

        lines.extend([
            "",
            "---",
            "",
            "## Execution Rules",
            "",
            "### MUST",
            "- Stay inside task_scope",
            "- Read all must_read files first",
            "- Honor all constraints",
            "- Complete all deliverables",
            "- Run all verification_steps",
            "- Stop at any stop_condition",
            "- Leave evidence of work",
            "",
            "### MUST NOT",
            "- Expand scope without approval",
            "- Make architectural decisions alone",
            "- Skip verification steps",
            "- Proceed when blocked",
            "",
            "---",
            "",
            "**After completion, write ExecutionResult to:**",
            "`execution-results/{execution_id}.md`",
            "",
            "**Format (follow AGENTS.md convention):**",
            "```yaml",
            "execution_id: {execution_id}",
            "status: success|partial|blocked|failed",
            "completed_items:",
            "  - ...",
            "artifacts_created:",
            "  - name: ...",
            "    path: ...",
            "verification_result:",
            "  passed: N",
            "  failed: M",
            "issues_found:",
            "  - ...",
            "blocked_reasons:",
            "  - ...",
            "decisions_required:",
            "  - ...",
            "recommended_next_step: ...",
            "```",
        ])

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _build_instructions(self, pack: dict[str, Any], md_path: Path) -> str:
        """Build human-readable execution instructions."""
        return "\n".join([
            "## Next Steps (External Tool Mode)",
            "",
            "**Step 1:** Read the ExecutionPack",
            f"  Open: {md_path}",
            "",
            "**Step 2:** Execute with external tool",
            "  - OpenCode: Read the file and execute",
            "  - Claude Code: Paste the content",
            "  - Other: Follow the instructions in the pack",
            "",
            "**Step 3:** Write ExecutionResult",
            f"  Path: execution-results/{pack.get('execution_id', 'unknown')}.md",
            "  Format: See AGENTS.md convention",
            "",
            "**Step 4:** Continue the loop",
            "  Run: asyncdev resume-next-day",
        ])

    def is_available(self) -> bool:
        """External tool mode is always available."""
        return True

    def get_mode_name(self) -> str:
        return "external"