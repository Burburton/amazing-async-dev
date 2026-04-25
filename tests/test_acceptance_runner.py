"""Tests for Feature 071 - Isolated Acceptance Runner."""

import tempfile
from pathlib import Path

import pytest
import yaml

from runtime.validator_types import (
    ValidatorType,
    ValidatorContext,
    ValidatorIdentity,
    create_ai_validator_identity,
    create_human_validator_identity,
    create_script_validator_identity,
)
from runtime.acceptance_pack_builder import (
    AcceptancePack,
    VerificationSummary,
    ImplementationSummary,
    build_acceptance_pack,
    save_acceptance_pack,
    load_acceptance_pack,
    generate_acceptance_pack_id,
    extract_verification_summary,
    extract_implementation_summary,
)
from runtime.acceptance_runner import (
    AcceptanceRunner,
    AcceptanceResult,
    AcceptanceTerminalState,
    AcceptanceFinding,
    RemediationGuidance,
    run_acceptance,
    run_acceptance_from_execution,
    save_acceptance_result,
    load_acceptance_result,
    get_latest_acceptance_result,
)


class TestValidatorTypes:
    
    def test_all_validator_types_defined(self):
        assert ValidatorType.AI_SESSION.value == "ai_session"
        assert ValidatorType.HUMAN_REVIEW.value == "human_review"
        assert ValidatorType.AUTOMATED_SCRIPT.value == "automated_script"
    
    def test_validator_context_defined(self):
        assert ValidatorContext.INDEPENDENT.value == "independent"
        assert ValidatorContext.DEFAULT.value == "default"
    
    def test_validator_identity_creation(self):
        identity = ValidatorIdentity(
            validator_type=ValidatorType.AI_SESSION,
            validator_id="ses-001",
            validator_context=ValidatorContext.INDEPENDENT,
        )
        assert identity.validator_type == ValidatorType.AI_SESSION
        assert identity.validator_id == "ses-001"
    
    def test_validator_identity_to_dict(self):
        identity = create_ai_validator_identity("ses-001")
        d = identity.to_dict()
        
        assert d["validator_type"] == "ai_session"
        assert d["validator_id"] == "ses-001"
        assert d["validator_context"] == "independent"
    
    def test_create_ai_validator_identity(self):
        identity = create_ai_validator_identity("ses-ai-001")
        assert identity.validator_type == ValidatorType.AI_SESSION
    
    def test_create_human_validator_identity(self):
        identity = create_human_validator_identity("john@example.com")
        assert identity.validator_type == ValidatorType.HUMAN_REVIEW
    
    def test_create_script_validator_identity(self):
        identity = create_script_validator_identity("test_runner.py")
        assert identity.validator_type == ValidatorType.AUTOMATED_SCRIPT


class TestVerificationSummary:
    
    def test_verification_summary_creation(self):
        summary = VerificationSummary(
            orchestration_terminal_state="success",
            browser_verification_executed=True,
            browser_verification_passed=3,
            browser_verification_failed=0,
            closeout_terminal_state="success",
        )
        assert summary.orchestration_terminal_state == "success"
    
    def test_verification_summary_to_dict(self):
        summary = VerificationSummary(
            orchestration_terminal_state="success",
            browser_verification_executed=True,
        )
        d = summary.to_dict()
        assert d["orchestration_terminal_state"] == "success"


class TestImplementationSummary:
    
    def test_implementation_summary_creation(self):
        summary = ImplementationSummary(
            completed_items=["item-1", "item-2"],
            artifacts_created=[{"name": "artifact-1", "path": "/path"}],
        )
        assert len(summary.completed_items) == 2
    
    def test_implementation_summary_to_dict(self):
        summary = ImplementationSummary(completed_items=["item-1"])
        d = summary.to_dict()
        assert d["completed_items"] == ["item-1"]


class TestAcceptancePack:
    
    def test_acceptance_pack_id_format(self):
        pack_id = generate_acceptance_pack_id("20260425")
        assert pack_id == "ap-20260425-001"
    
    def test_acceptance_pack_creation(self):
        pack = AcceptancePack(
            acceptance_pack_id="ap-20260425-001",
            feature_id="feat-001",
            execution_result_id="exec-001",
            product_id="proj-001",
            acceptance_criteria=[{"criterion_id": "AC-001", "text": "Works"}],
        )
        assert pack.acceptance_pack_id == "ap-20260425-001"
    
    def test_acceptance_pack_to_dict(self):
        pack = AcceptancePack(
            acceptance_pack_id="ap-001",
            feature_id="feat-001",
            execution_result_id="exec-001",
            product_id="proj-001",
            acceptance_criteria=[],
        )
        d = pack.to_dict()
        assert d["acceptance_pack_id"] == "ap-001"
    
    def test_acceptance_pack_to_yaml(self):
        pack = AcceptancePack(
            acceptance_pack_id="ap-001",
            feature_id="feat-001",
            execution_result_id="exec-001",
            product_id="proj-001",
            acceptance_criteria=[],
        )
        yaml_str = pack.to_yaml()
        assert "acceptance_pack_id: ap-001" in yaml_str


class TestExtractFunctions:
    
    def test_extract_verification_summary(self):
        execution_result = {
            "orchestration_terminal_state": "success",
            "browser_verification": {"executed": True, "passed": 3, "failed": 0},
            "closeout_terminal_state": "success",
        }
        summary = extract_verification_summary(execution_result)
        assert summary.orchestration_terminal_state == "success"
        assert summary.browser_verification_executed is True
    
    def test_extract_implementation_summary(self):
        execution_result = {
            "completed_items": ["item-1"],
            "artifacts_created": [{"name": "artifact-1", "path": "/path"}],
            "files_modified": ["file-1.py"],
            "notes": "Key changes made",
        }
        summary = extract_implementation_summary(execution_result)
        assert summary.completed_items == ["item-1"]
        assert summary.key_changes == "Key changes made"


class TestBuildAcceptancePack:
    
    @pytest.fixture
    def project_with_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            execution_result_path = execution_results_dir / "exec-001.md"
            execution_result_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-001
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items:
  - "Implement feature"
artifacts_created:
  - name: "artifact-1"
    path: "artifacts/artifact-1.md"
browser_verification:
  executed: true
  passed: 3
  failed: 0
```
""")
            
            features_dir = project_path / "features" / "feat-001"
            features_dir.mkdir(parents=True)
            
            feature_spec_path = features_dir / "feature-spec.yaml"
            feature_spec_path.write_text(yaml.dump({
                "feature_id": "feat-001",
                "name": "Test Feature",
                "acceptance_criteria": [
                    {"criterion_id": "AC-001", "text": "Feature works correctly"},
                    {"criterion_id": "AC-002", "text": "Edge cases handled"},
                ],
            }))
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-001",
                "project_id": "proj-001",
            })
            
            yield project_path

    def test_build_acceptance_pack_success(self, project_with_execution):
        pack = build_acceptance_pack(project_with_execution, "exec-001")
        
        assert pack is not None
        assert pack.feature_id == "feat-001"
        assert pack.execution_result_id == "exec-001"
        assert len(pack.acceptance_criteria) == 2
    
    def test_build_acceptance_pack_missing_execution(self, project_with_execution):
        pack = build_acceptance_pack(project_with_execution, "exec-missing")
        assert pack is None
    
    def test_build_acceptance_pack_includes_verification(self, project_with_execution):
        pack = build_acceptance_pack(project_with_execution, "exec-001")
        
        assert pack.verification_summary.orchestration_terminal_state == "success"
    
    def test_build_acceptance_pack_includes_evidence(self, project_with_execution):
        pack = build_acceptance_pack(project_with_execution, "exec-001")
        
        assert len(pack.evidence_artifacts) > 0


class TestSaveLoadAcceptancePack:
    
    def test_save_acceptance_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-001",
                feature_id="feat-001",
                execution_result_id="exec-001",
                product_id="proj-001",
                acceptance_criteria=[],
            )
            
            pack_path = save_acceptance_pack(project_path, pack)
            
            assert pack_path.exists()
            assert pack_path.name == "ap-001.md"
    
    def test_load_acceptance_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            pack = AcceptancePack(
                acceptance_pack_id="ap-001",
                feature_id="feat-001",
                execution_result_id="exec-001",
                product_id="proj-001",
                acceptance_criteria=[{"criterion_id": "AC-001", "text": "Test"}],
            )
            
            save_acceptance_pack(project_path, pack)
            
            loaded = load_acceptance_pack(project_path, "ap-001")
            
            assert loaded is not None
            assert loaded.acceptance_pack_id == "ap-001"
            assert loaded.feature_id == "feat-001"


class TestAcceptanceTerminalState:
    
    def test_all_terminal_states_defined(self):
        assert AcceptanceTerminalState.ACCEPTED.value == "accepted"
        assert AcceptanceTerminalState.CONDITIONAL.value == "conditional"
        assert AcceptanceTerminalState.REJECTED.value == "rejected"
        assert AcceptanceTerminalState.MANUAL_REVIEW.value == "manual_review"
        assert AcceptanceTerminalState.ESCALATED.value == "escalated"


class TestAcceptanceFinding:
    
    def test_acceptance_finding_creation(self):
        finding = AcceptanceFinding(
            criterion_id="AC-001",
            criterion_text="Feature works",
            result="passed",
            evidence_found=True,
            confidence=0.8,
        )
        assert finding.criterion_id == "AC-001"
        assert finding.result == "passed"
    
    def test_acceptance_finding_to_dict(self):
        finding = AcceptanceFinding(criterion_id="AC-001", result="passed")
        d = finding.to_dict()
        assert d["criterion_id"] == "AC-001"


class TestRemediationGuidance:
    
    def test_remediation_guidance_creation(self):
        guidance = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Provide evidence",
            priority="high",
        )
        assert guidance.criterion_id == "AC-001"
    
    def test_remediation_guidance_to_dict(self):
        guidance = RemediationGuidance(
            criterion_id="AC-001",
            issue_type="evidence_missing",
            suggested_fix="Provide evidence",
        )
        d = guidance.to_dict()
        assert d["criterion_id"] == "AC-001"


class TestAcceptanceResult:
    
    def test_acceptance_result_creation(self):
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.ACCEPTED,
        )
        assert result.acceptance_result_id == "ar-001"
    
    def test_acceptance_result_is_valid_for_completion(self):
        accepted = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.ACCEPTED,
        )
        assert accepted.is_valid_for_completion()
        
        rejected = AcceptanceResult(
            acceptance_result_id="ar-002",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.REJECTED,
        )
        assert not rejected.is_valid_for_completion()
    
    def test_acceptance_result_requires_rework(self):
        rejected = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.REJECTED,
        )
        assert rejected.requires_rework()
        
        accepted = AcceptanceResult(
            acceptance_result_id="ar-002",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.ACCEPTED,
        )
        assert not accepted.requires_rework()
    
    def test_acceptance_result_to_dict(self):
        result = AcceptanceResult(
            acceptance_result_id="ar-001",
            acceptance_pack_id="ap-001",
            terminal_state=AcceptanceTerminalState.ACCEPTED,
            accepted_criteria=["AC-001"],
        )
        d = result.to_dict()
        assert d["terminal_state"] == "accepted"


class TestAcceptanceRunner:
    
    @pytest.fixture
    def pack_with_criteria(self):
        return AcceptancePack(
            acceptance_pack_id="ap-001",
            feature_id="feat-001",
            execution_result_id="exec-001",
            product_id="proj-001",
            acceptance_criteria=[
                {"criterion_id": "AC-001", "text": "Works"},
                {"criterion_id": "AC-002", "text": "Handles edge cases"},
            ],
            evidence_artifacts=["artifact-1.md"],
        )
    
    def test_acceptance_runner_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = AcceptanceRunner(Path(tmpdir))
            assert runner.validator_type == ValidatorType.AI_SESSION
    
    def test_acceptance_runner_run(self, pack_with_criteria):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = AcceptanceRunner(Path(tmpdir))
            result = runner.run(pack_with_criteria)
            
            assert result is not None
            assert result.acceptance_pack_id == "ap-001"
    
    def test_acceptance_runner_evaluates_criteria(self, pack_with_criteria):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = AcceptanceRunner(Path(tmpdir))
            result = runner.run(pack_with_criteria)
            
            assert len(result.findings) == 2
            assert len(result.accepted_criteria) > 0
    
    def test_acceptance_runner_terminal_state_accepted(self, pack_with_criteria):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = AcceptanceRunner(Path(tmpdir))
            result = runner.run(pack_with_criteria)
            
            assert result.terminal_state == AcceptanceTerminalState.ACCEPTED


class TestSaveLoadAcceptanceResult:
    
    def test_save_acceptance_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-001",
                acceptance_pack_id="ap-001",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
            )
            
            result_path = save_acceptance_result(project_path, result)
            
            assert result_path.exists()
            assert result_path.name == "ar-001.md"
    
    def test_load_acceptance_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            result = AcceptanceResult(
                acceptance_result_id="ar-001",
                acceptance_pack_id="ap-001",
                terminal_state=AcceptanceTerminalState.ACCEPTED,
                accepted_criteria=["AC-001"],
            )
            
            save_acceptance_result(project_path, result)
            
            loaded = load_acceptance_result(project_path, "ar-001")
            
            assert loaded is not None
            assert loaded.acceptance_result_id == "ar-001"
            assert loaded.terminal_state == AcceptanceTerminalState.ACCEPTED


class TestConvenienceFunctions:
    
    @pytest.fixture
    def full_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            execution_results_dir = project_path / "execution-results"
            execution_results_dir.mkdir()
            
            execution_result_path = execution_results_dir / "exec-full.md"
            execution_result_path.write_text("""# ExecutionResult

```yaml
execution_id: exec-full
status: success
closeout_terminal_state: success
orchestration_terminal_state: success
completed_items:
  - "Implement feature"
artifacts_created:
  - name: "artifact"
    path: "artifacts/artifact.md"
```
""")
            
            features_dir = project_path / "features" / "feat-full"
            features_dir.mkdir(parents=True)
            
            feature_spec_path = features_dir / "feature-spec.yaml"
            feature_spec_path.write_text(yaml.dump({
                "feature_id": "feat-full",
                "acceptance_criteria": [
                    {"criterion_id": "AC-001", "text": "Works"},
                ],
            }))
            
            from runtime.state_store import StateStore
            store = StateStore(project_path)
            store.save_runstate({
                "feature_id": "feat-full",
                "project_id": "proj-full",
            })
            
            yield project_path

    def test_run_acceptance_from_execution(self, full_project):
        result = run_acceptance_from_execution(full_project, "exec-full")
        
        assert result is not None
        assert result.terminal_state in [
            AcceptanceTerminalState.ACCEPTED,
            AcceptanceTerminalState.CONDITIONAL,
        ]
    
    def test_run_acceptance_from_execution_persists_result(self, full_project):
        result = run_acceptance_from_execution(full_project, "exec-full")
        
        results_dir = full_project / "acceptance-results"
        assert results_dir.exists()
        
        result_files = list(results_dir.glob("*.md"))
        assert len(result_files) > 0