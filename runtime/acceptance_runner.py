"""Acceptance Runner - Feature 071.

Runs acceptance validation in isolated context.
AcceptanceRunner consumes AcceptancePack and produces AcceptanceResult.

Integration with:
- Feature 069 (AcceptanceResult schema)
- Feature 070 (AcceptanceReadiness)
- Feature 071 (AcceptancePack builder)
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.acceptance_pack_builder import AcceptancePack, load_acceptance_pack
from runtime.validator_types import ValidatorType, ValidatorIdentity, create_ai_validator_identity


class AcceptanceTerminalState(str, Enum):
    """Terminal states for AcceptanceResult (Feature 069)."""
    
    ACCEPTED = "accepted"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
    ESCALATED = "escalated"


@dataclass
class AcceptanceFinding:
    """Single criterion evaluation result."""
    
    criterion_id: str
    criterion_text: str = ""
    result: str = "pending"
    evidence_found: bool = False
    evidence_path: str | None = None
    notes: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "criterion_text": self.criterion_text,
            "result": self.result,
            "evidence_found": self.evidence_found,
            "evidence_path": self.evidence_path,
            "notes": self.notes,
            "confidence": self.confidence,
        }


@dataclass
class RemediationGuidance:
    """Guidance for fixing rejected criteria."""
    
    criterion_id: str
    issue_type: str
    suggested_fix: str
    priority: str = "medium"
    related_artifacts: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "issue_type": self.issue_type,
            "suggested_fix": self.suggested_fix,
            "priority": self.priority,
            "related_artifacts": self.related_artifacts,
        }


@dataclass
class AcceptanceResult:
    """AcceptanceResult artifact (Feature 069/071).
    
    Output from validator containing evaluation results and terminal state.
    """
    
    acceptance_result_id: str
    acceptance_pack_id: str
    terminal_state: AcceptanceTerminalState
    
    findings: list[AcceptanceFinding] = field(default_factory=list)
    accepted_criteria: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)
    conditional_criteria: list[str] = field(default_factory=list)
    
    remediation_guidance: list[RemediationGuidance] = field(default_factory=list)
    
    validator_identity: ValidatorIdentity = field(default_factory=lambda: create_ai_validator_identity("unknown"))
    attempt_number: int = 1
    
    overall_summary: str = ""
    confidence_score: float = 0.0
    
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "acceptance_result_id": self.acceptance_result_id,
            "acceptance_pack_id": self.acceptance_pack_id,
            "terminal_state": self.terminal_state.value,
            "findings": [f.to_dict() for f in self.findings],
            "accepted_criteria": self.accepted_criteria,
            "failed_criteria": self.failed_criteria,
            "conditional_criteria": self.conditional_criteria,
            "remediation_guidance": [r.to_dict() for r in self.remediation_guidance],
            "validator_identity": self.validator_identity.to_dict(),
            "attempt_number": self.attempt_number,
            "overall_summary": self.overall_summary,
            "confidence_score": self.confidence_score,
            "validated_at": self.validated_at,
        }
    
    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
    
    def is_valid_for_completion(self) -> bool:
        """Check if result allows feature completion."""
        return self.terminal_state in [
            AcceptanceTerminalState.ACCEPTED,
            AcceptanceTerminalState.CONDITIONAL,
        ]
    
    def requires_rework(self) -> bool:
        """Check if result requires rework."""
        return self.terminal_state == AcceptanceTerminalState.REJECTED


class AcceptanceRunner:
    """Runner for isolated acceptance validation (Feature 071)."""
    
    VALIDATOR_TIMEOUT_SECONDS = 300
    
    def __init__(
        self,
        project_path: Path,
        validator_type: ValidatorType = ValidatorType.AI_SESSION,
        validator_id: str | None = None,
    ):
        self.project_path = project_path
        self.validator_type = validator_type
        self.validator_id = validator_id or f"validator-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def run(self, acceptance_pack: AcceptancePack) -> AcceptanceResult:
        """Run acceptance validation on AcceptancePack (Feature 071 AC-002).
        
        Args:
            acceptance_pack: Input package for validation
        
        Returns:
            AcceptanceResult with evaluation findings
        """
        validator_identity = create_ai_validator_identity(self.validator_id)
        
        findings: list[AcceptanceFinding] = []
        accepted_criteria: list[str] = []
        failed_criteria: list[str] = []
        conditional_criteria: list[str] = []
        
        for criterion in acceptance_pack.acceptance_criteria:
            criterion_id = criterion.get("criterion_id", criterion.get("id", ""))
            criterion_text = criterion.get("text", criterion.get("description", ""))
            
            finding = self._evaluate_criterion(
                criterion_id,
                criterion_text,
                acceptance_pack.implementation_summary,
                acceptance_pack.evidence_artifacts,
            )
            
            findings.append(finding)
            
            if finding.result == "passed":
                accepted_criteria.append(criterion_id)
            elif finding.result == "failed":
                failed_criteria.append(criterion_id)
            elif finding.result == "conditional":
                conditional_criteria.append(criterion_id)
        
        terminal_state = self._determine_terminal_state(
            accepted_criteria,
            failed_criteria,
            conditional_criteria,
        )
        
        remediation_guidance = self._generate_remediation(
            failed_criteria,
            findings,
            acceptance_pack.acceptance_criteria,
        )
        
        acceptance_result_id = self._generate_result_id()
        
        attempt_number = self._get_attempt_number(acceptance_pack.acceptance_pack_id)
        
        overall_summary = self._generate_summary(
            terminal_state,
            accepted_criteria,
            failed_criteria,
            conditional_criteria,
        )
        
        confidence_score = self._calculate_confidence(findings)
        
        return AcceptanceResult(
            acceptance_result_id=acceptance_result_id,
            acceptance_pack_id=acceptance_pack.acceptance_pack_id,
            terminal_state=terminal_state,
            findings=findings,
            accepted_criteria=accepted_criteria,
            failed_criteria=failed_criteria,
            conditional_criteria=conditional_criteria,
            remediation_guidance=remediation_guidance,
            validator_identity=validator_identity,
            attempt_number=attempt_number,
            overall_summary=overall_summary,
            confidence_score=confidence_score,
        )
    
    def _evaluate_criterion(
        self,
        criterion_id: str,
        criterion_text: str,
        implementation_summary: Any,
        evidence_artifacts: list[str],
    ) -> AcceptanceFinding:
        """Evaluate single criterion against evidence.
        
        Note: This is a placeholder implementation.
        Real implementation would invoke validator (AI session, script, etc.)
        """
        
        evidence_found = len(evidence_artifacts) > 0
        
        if evidence_found:
            result = "passed"
            confidence = 0.8
        else:
            result = "failed"
            confidence = 0.3
        
        return AcceptanceFinding(
            criterion_id=criterion_id,
            criterion_text=criterion_text,
            result=result,
            evidence_found=evidence_found,
            evidence_path=evidence_artifacts[0] if evidence_artifacts else None,
            notes=f"Evaluation of criterion {criterion_id}",
            confidence=confidence,
        )
    
    def _determine_terminal_state(
        self,
        accepted: list[str],
        failed: list[str],
        conditional: list[str],
    ) -> AcceptanceTerminalState:
        """Determine terminal state from criterion results."""
        if not failed and not conditional:
            return AcceptanceTerminalState.ACCEPTED
        
        if not failed and conditional:
            return AcceptanceTerminalState.CONDITIONAL
        
        if failed:
            return AcceptanceTerminalState.REJECTED
        
        return AcceptanceTerminalState.MANUAL_REVIEW
    
    def _generate_remediation(
        self,
        failed_criteria: list[str],
        findings: list[AcceptanceFinding],
        acceptance_criteria: list[dict[str, Any]],
    ) -> list[RemediationGuidance]:
        """Generate remediation guidance for failed criteria."""
        remediation: list[RemediationGuidance] = []
        
        for criterion_id in failed_criteria:
            criterion_text = ""
            for criterion in acceptance_criteria:
                if criterion.get("criterion_id", criterion.get("id", "")) == criterion_id:
                    criterion_text = criterion.get("text", criterion.get("description", ""))
                    break
            
            remediation.append(RemediationGuidance(
                criterion_id=criterion_id,
                issue_type="evidence_missing",
                suggested_fix=f"Provide evidence for criterion: {criterion_text}",
                priority="high",
                related_artifacts=[],
            ))
        
        return remediation
    
    def _generate_result_id(self) -> str:
        """Generate acceptance result ID."""
        date_str = datetime.now().strftime("%Y%m%d")
        return f"ar-{date_str}-001"
    
    def _get_attempt_number(self, acceptance_pack_id: str) -> int:
        """Get attempt number from previous results."""
        results_dir = self.project_path / "acceptance-results"
        
        if not results_dir.exists():
            return 1
        
        previous_results = list(results_dir.glob("*.md"))
        
        matching = [
            r for r in previous_results
            if acceptance_pack_id in r.read_text(encoding="utf-8")
        ]
        
        return len(matching) + 1
    
    def _generate_summary(
        self,
        terminal_state: AcceptanceTerminalState,
        accepted: list[str],
        failed: list[str],
        conditional: list[str],
    ) -> str:
        """Generate overall summary."""
        return f"Validation result: {terminal_state.value}. Accepted: {len(accepted)}, Failed: {len(failed)}, Conditional: {len(conditional)}"
    
    def _calculate_confidence(self, findings: list[AcceptanceFinding]) -> float:
        """Calculate overall confidence score."""
        if not findings:
            return 0.0
        
        return sum(f.confidence for f in findings) / len(findings)


def run_acceptance(
    project_path: Path,
    acceptance_pack_id: str,
    validator_type: ValidatorType = ValidatorType.AI_SESSION,
) -> AcceptanceResult | None:
    """Run acceptance validation by pack ID (convenience function)."""
    acceptance_pack = load_acceptance_pack(project_path, acceptance_pack_id)
    
    if acceptance_pack is None:
        return None
    
    runner = AcceptanceRunner(project_path, validator_type)
    return runner.run(acceptance_pack)


def run_acceptance_from_execution(
    project_path: Path,
    execution_result_id: str,
) -> AcceptanceResult | None:
    """Run acceptance from ExecutionResult ID (full flow)."""
    from runtime.acceptance_pack_builder import build_acceptance_pack, save_acceptance_pack
    
    acceptance_pack = build_acceptance_pack(project_path, execution_result_id)
    
    if acceptance_pack is None:
        return None
    
    save_acceptance_pack(project_path, acceptance_pack)
    
    runner = AcceptanceRunner(project_path)
    result = runner.run(acceptance_pack)
    
    save_acceptance_result(project_path, result)
    
    return result


def save_acceptance_result(project_path: Path, acceptance_result: AcceptanceResult) -> Path:
    """Save AcceptanceResult to markdown file (Feature 071 AC-004)."""
    results_dir = project_path / "acceptance-results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    result_path = results_dir / f"{acceptance_result.acceptance_result_id}.md"
    
    yaml_content = acceptance_result.to_yaml()
    markdown_content = f"""# AcceptanceResult

```yaml
{yaml_content}
```
"""
    
    result_path.write_text(markdown_content, encoding="utf-8")
    return result_path


def load_acceptance_result(project_path: Path, acceptance_result_id: str) -> AcceptanceResult | None:
    """Load AcceptanceResult from markdown file."""
    result_path = project_path / "acceptance-results" / f"{acceptance_result_id}.md"
    
    if not result_path.exists():
        return None
    
    content = result_path.read_text(encoding="utf-8")
    
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
        yaml_block = "\n".join(lines[yaml_start:yaml_end])
        data = yaml.safe_load(yaml_block)
        
        findings = [
            AcceptanceFinding(**f) for f in data.get("findings", [])
        ]
        
        remediation = [
            RemediationGuidance(**r) for r in data.get("remediation_guidance", [])
        ]
        
        validator_data = data.get("validator_identity", {})
        validator_identity = ValidatorIdentity.from_dict(validator_data)
        
        return AcceptanceResult(
            acceptance_result_id=data.get("acceptance_result_id", ""),
            acceptance_pack_id=data.get("acceptance_pack_id", ""),
            terminal_state=AcceptanceTerminalState(data.get("terminal_state", "manual_review")),
            findings=findings,
            accepted_criteria=data.get("accepted_criteria", []),
            failed_criteria=data.get("failed_criteria", []),
            conditional_criteria=data.get("conditional_criteria", []),
            remediation_guidance=remediation,
            validator_identity=validator_identity,
            attempt_number=data.get("attempt_number", 1),
            overall_summary=data.get("overall_summary", ""),
            confidence_score=data.get("confidence_score", 0.0),
            validated_at=data.get("validated_at", ""),
        )
    
    return None


def get_latest_acceptance_result(project_path: Path, feature_id: str) -> AcceptanceResult | None:
    """Get latest acceptance result for a feature."""
    results_dir = project_path / "acceptance-results"
    
    if not results_dir.exists():
        return None
    
    results = list(results_dir.glob("*.md"))
    
    if not results:
        return None
    
    results.sort(key=lambda r: r.stat().st_mtime, reverse=True)
    
    for result_path in results:
        result = load_acceptance_result(project_path, result_path.stem)
        if result:
            pack = load_acceptance_pack(project_path, result.acceptance_pack_id)
            if pack and pack.feature_id == feature_id:
                return result
    
    return None