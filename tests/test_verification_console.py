"""Tests for Verification Console CLI (Priority 2 operator surface).

Tests for: list, show, classify, gate, retry commands.
"""

import tempfile
from pathlib import Path
import yaml

import pytest

from runtime.verification_classifier import VerificationType, classify_verification_type_from_files
from runtime.verification_gate import requires_browser_verification, get_completion_gate_status
from runtime.state_store import StateStore


@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-project"
        project_path.mkdir(parents=True)
        (project_path / "execution-results").mkdir(parents=True)
        yield project_path


@pytest.fixture
def temp_projects_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        project_a = root / "project-a"
        project_a.mkdir(parents=True)
        (project_a / "execution-results").mkdir(parents=True)
        
        project_b = root / "project-b"
        project_b.mkdir(parents=True)
        (project_b / "execution-results").mkdir(parents=True)
        
        yield root


class TestClassifyCommand:
    def test_classify_frontend_component(self):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["classify", "--files", "src/components/Button.tsx"])
        
        assert result.exit_code == 0
        assert "frontend_interactive" in result.output
        assert "Browser Verification Required: True" in result.output
    
    def test_classify_backend_file(self):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["classify", "--files", "src/api/auth.py"])
        
        assert result.exit_code == 0
        assert "backend_only" in result.output
    
    def test_classify_multiple_files(self):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["classify", "--files", "src/components/Button.tsx,src/api/auth.py"])
        
        assert result.exit_code == 0
        assert "mixed_app_workflow" in result.output or "frontend_interactive" in result.output
    
    def test_classify_with_description(self):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "classify",
            "--files", "src/pages/Home.tsx",
            "--description", "Add click handler for navigation button"
        ])
        
        assert result.exit_code == 0
        assert "frontend_interactive" in result.output


class TestListCommand:
    def test_list_empty_projects(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--all", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 0
        assert "No execution results found" in result.output or "No projects found" in result.output
    
    def test_list_with_execution_result(self, temp_project):
        store = StateStore(temp_project)
        
        execution_result = {
            "execution_id": "exec-test-001",
            "status": "success",
            "verification_type": "frontend_interactive",
            "browser_verification": {
                "executed": True,
                "passed": 3,
                "failed": 0,
            },
        }
        
        result_path = temp_project / "execution-results" / "exec-test-001.md"
        content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result, default_flow_style=False)}
```
"""
        result_path.write_text(content)
        
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "exec-test-001" in result.output or "success" in result.output
    
    def test_list_filter_by_status(self, temp_project):
        store = StateStore(temp_project)
        
        for i, status in enumerate(["success", "failed", "pending"], 1):
            execution_result = {
                "execution_id": f"exec-test-{i:03d}",
                "status": "success" if status == "success" else "failed",
                "verification_type": "frontend_interactive",
                "browser_verification": {
                    "executed": status != "pending",
                    "passed": 3 if status == "success" else 0,
                    "failed": 2 if status == "failed" else 0,
                } if status != "pending" else {},
            }
            
            result_path = temp_project / "execution-results" / f"exec-test-{i:03d}.md"
            content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result, default_flow_style=False)}
```
"""
            result_path.write_text(content)
        
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["list", "--status", "success", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0


class TestShowCommand:
    def test_show_nonexistent_execution(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["show", "--execution", "exec-nonexistent", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 1
        assert "Execution not found" in result.output
    
    def test_show_existing_execution(self, temp_project):
        execution_result = {
            "execution_id": "exec-show-001",
            "status": "success",
            "verification_type": "frontend_interactive",
            "browser_verification": {
                "executed": True,
                "passed": 5,
                "failed": 0,
                "scenarios_run": ["scenario1", "scenario2"],
            },
            "frontend_recipe": {
                "stage": "COMPLETED_SUCCESS",
                "framework": "vite",
                "success": True,
            },
        }
        
        result_path = temp_project / "execution-results" / "exec-show-001.md"
        content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result, default_flow_style=False)}
```
"""
        result_path.write_text(content)
        
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["show", "--execution", "exec-show-001", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "frontend_interactive" in result.output
        assert "Browser Required" in result.output


class TestGateCommand:
    def test_gate_nonexistent_execution(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["gate", "--execution", "exec-nonexistent", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 1
    
    def test_gate_allowed_backend_only(self, temp_project):
        execution_result = {
            "execution_id": "exec-gate-001",
            "status": "success",
            "verification_type": "backend_only",
        }
        
        result_path = temp_project / "execution-results" / "exec-gate-001.md"
        content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result, default_flow_style=False)}
```
"""
        result_path.write_text(content)
        
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["gate", "--execution", "exec-gate-001", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "ALLOWED" in result.output
    
    def test_gate_blocked_frontend_without_verification(self, temp_project):
        execution_result = {
            "execution_id": "exec-gate-002",
            "status": "failed",
            "verification_type": "frontend_interactive",
            "browser_verification": {
                "executed": False,
            },
        }
        
        result_path = temp_project / "execution-results" / "exec-gate-002.md"
        content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result, default_flow_style=False)}
```
"""
        result_path.write_text(content)
        
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["gate", "--execution", "exec-gate-002", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "BLOCKED" in result.output


class TestVerificationClassifierIntegration:
    def test_frontend_interactive_classification(self):
        files = ["src/components/Button.tsx"]
        result = classify_verification_type_from_files(files, "Add click handler")
        
        assert result.verification_type == VerificationType.FRONTEND_INTERACTIVE
        assert result.confidence >= 0.7
    
    def test_backend_only_classification(self):
        files = ["src/api/auth.py", "tests/test_auth.py"]
        result = classify_verification_type_from_files(files, "Update authentication")
        
        assert result.verification_type == VerificationType.BACKEND_ONLY
    
    def test_mixed_workflow_classification(self):
        files = ["src/components/Button.tsx", "src/api/auth.py"]
        result = classify_verification_type_from_files(files, "Update auth and button")
        
        assert result.verification_type == VerificationType.MIXED_APP_WORKFLOW
    
    def test_docs_only_classification(self):
        files = ["docs/README.md", "docs/api.md"]
        result = classify_verification_type_from_files(files, "Update documentation")
        
        assert result.verification_type == VerificationType.BACKEND_ONLY
        assert result.confidence >= 0.9


class TestVerificationGateIntegration:
    def test_backend_only_no_browser_required(self):
        assert requires_browser_verification("backend_only") is False
    
    def test_frontend_interactive_browser_required(self):
        assert requires_browser_verification("frontend_interactive") is True
    
    def test_frontend_visual_browser_required(self):
        assert requires_browser_verification("frontend_visual_behavior") is True
    
    def test_mixed_app_browser_required(self):
        assert requires_browser_verification("mixed_app_workflow") is True
    
    def test_frontend_noninteractive_optional(self):
        assert requires_browser_verification("frontend_noninteractive") is False


class TestRetryCommand:
    def test_retry_nonexistent_execution(self, temp_projects_root):
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["retry", "--execution", "exec-nonexistent", "--path", str(temp_projects_root)])
        
        assert result.exit_code == 1
        assert "Execution not found" in result.output
    
    def test_retry_backend_only_execution(self, temp_project):
        execution_result = {
            "execution_id": "exec-retry-001",
            "status": "success",
            "verification_type": "backend_only",
        }
        
        result_path = temp_project / "execution-results" / "exec-retry-001.md"
        content = f"""# ExecutionResult

```yaml
{yaml.dump(execution_result, default_flow_style=False)}
```
"""
        result_path.write_text(content)
        
        from typer.testing import CliRunner
        from cli.commands.verification import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["retry", "--execution", "exec-retry-001", "--path", str(temp_project.parent)])
        
        assert result.exit_code == 0
        assert "Browser verification not required" in result.output