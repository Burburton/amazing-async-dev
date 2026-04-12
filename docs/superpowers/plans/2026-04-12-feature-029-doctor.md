# Feature 029 - Workspace Doctor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add workspace diagnosis command that provides health classification and recommended next action with exact command suggestion.

**Architecture:** Reuse Feature 028 snapshot data structures, apply recommendation rules (A-F) to classify health, generate operator-facing guidance. Dual-layer health model: bottom (RunState.health_status) + top (doctor_status).

**Tech Stack:** Python 3.10+, typer, pyyaml, rich, pytest

---

## File Structure

| File | Responsibility |
|------|---------------|
| `runtime/workspace_doctor.py` | Core diagnosis logic - rules, classification, formatting |
| `cli/commands/doctor.py` | CLI entry point with typer |
| `tests/test_workspace_doctor.py` | Unit tests for all scenarios |
| `examples/doctor-output.md` | Output examples for documentation |
| `docs/doctor.md` | User guide |
| `cli/asyncdev.py` | Register doctor app |
| `README.md` | Add link to doctor docs |

---

### Task 1: DoctorDiagnosis Dataclass

**Files:**
- Create: `runtime/workspace_doctor.py`

- [ ] **Step 1: Write the failing test for DoctorDiagnosis defaults**

```python
# tests/test_workspace_doctor.py

import pytest
from runtime.workspace_doctor import DoctorDiagnosis


class TestDoctorDiagnosisDataclass:
    def test_default_values(self):
        """DoctorDiagnosis should have sensible defaults."""
        diagnosis = DoctorDiagnosis()
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.health_status == "unknown"
        assert diagnosis.initialization_mode == "unknown"
        assert diagnosis.provider_linkage == {}
        assert diagnosis.product_id == ""
        assert diagnosis.feature_id == ""
        assert diagnosis.current_phase == ""
        assert diagnosis.verification_status == "not_run"
        assert diagnosis.pending_decisions == 0
        assert diagnosis.blocked_items_count == 0
        assert diagnosis.recommended_action == ""
        assert diagnosis.suggested_command == ""
        assert diagnosis.rationale == ""
        assert diagnosis.warnings == []
        assert diagnosis.workspace_path == ""

    def test_custom_values(self):
        """DoctorDiagnosis should accept custom values."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            health_status="healthy",
            product_id="my-app",
            feature_id="feature-001",
            current_phase="planning",
            recommended_action="Plan a task",
            suggested_command="asyncdev plan-day create",
            rationale="Workspace is in planning phase"
        )
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.product_id == "my-app"
        assert diagnosis.recommended_action == "Plan a task"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDoctorDiagnosisDataclass -v`
Expected: FAIL with "cannot import name 'DoctorDiagnosis'"

- [ ] **Step 3: Write minimal DoctorDiagnosis dataclass**

```python
# runtime/workspace_doctor.py

"""Workspace Doctor - health diagnosis and next-action recommendations (Feature 029)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DoctorDiagnosis:
    """Workspace diagnosis result."""
    
    doctor_status: str = "UNKNOWN"
    health_status: str = "unknown"
    
    initialization_mode: str = "unknown"
    provider_linkage: dict[str, Any] = field(default_factory=dict)
    
    product_id: str = ""
    feature_id: str = ""
    current_phase: str = ""
    
    verification_status: str = "not_run"
    pending_decisions: int = 0
    blocked_items_count: int = 0
    
    recommended_action: str = ""
    suggested_command: str = ""
    rationale: str = ""
    warnings: list[str] = field(default_factory=list)
    
    workspace_path: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDoctorDiagnosisDataclass -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_workspace_doctor.py runtime/workspace_doctor.py
git commit -m "feat(029): add DoctorDiagnosis dataclass"
```

---

### Task 2: diagnose_workspace Function

**Files:**
- Modify: `runtime/workspace_doctor.py`
- Modify: `tests/test_workspace_doctor.py`

- [ ] **Step 1: Write the failing test for diagnose_workspace with empty project**

```python
# tests/test_workspace_doctor.py (append to file)

from pathlib import Path
from runtime.workspace_snapshot import generate_workspace_snapshot


class TestDiagnoseWorkspace:
    def test_empty_project_returns_unknown(self, tmp_path):
        """Empty project should return UNKNOWN status."""
        empty_project = tmp_path / "empty-project"
        empty_project.mkdir()
        
        diagnosis = diagnose_workspace(empty_project)
        
        assert diagnosis.doctor_status == "UNKNOWN"
        assert diagnosis.recommended_action != ""
        assert "init" in diagnosis.suggested_command.lower() or "no" in diagnosis.recommended_action.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_empty_project_returns_unknown -v`
Expected: FAIL with "cannot import name 'diagnose_workspace'"

- [ ] **Step 3: Write minimal diagnose_workspace function**

```python
# runtime/workspace_doctor.py (append after dataclass)

from runtime.workspace_snapshot import generate_workspace_snapshot


def diagnose_workspace(project_path: Path) -> DoctorDiagnosis:
    """Generate workspace diagnosis with health classification and recommendations.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        DoctorDiagnosis with health classification and recommended action
    """
    diagnosis = DoctorDiagnosis()
    diagnosis.workspace_path = str(project_path)
    
    if not project_path.exists():
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "No project directory found."
        return diagnosis
    
    # Gather snapshot data (reuse Feature 028)
    snapshot = generate_workspace_snapshot(project_path)
    
    # Copy snapshot fields to diagnosis
    diagnosis.initialization_mode = snapshot.initialization_mode
    diagnosis.provider_linkage = snapshot.provider_linkage
    diagnosis.product_id = snapshot.product_id
    diagnosis.feature_id = snapshot.feature_id
    diagnosis.current_phase = snapshot.current_phase
    diagnosis.verification_status = snapshot.verification_status
    diagnosis.pending_decisions = snapshot.pending_decisions
    
    # Apply recommendation rules (implement next task)
    _apply_rules(diagnosis, snapshot)
    
    return diagnosis


def _apply_rules(diagnosis: DoctorDiagnosis, snapshot) -> None:
    """Apply recommendation rules to determine doctor_status."""
    # Rule F: Missing state (baseline)
    if not snapshot.product_id or snapshot.current_phase in ["unknown", "none", ""]:
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "Insufficient workspace metadata to make reliable recommendation."
        return
    
    # Placeholder for other rules (implement in Task 3)
    diagnosis.doctor_status = "HEALTHY"
    diagnosis.recommended_action = "Check workspace state and continue workflow."
    diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
    diagnosis.rationale = "Workspace has sufficient metadata."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_empty_project_returns_unknown -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_workspace_doctor.py runtime/workspace_doctor.py
git commit -m "feat(029): add diagnose_workspace function with Rule F"
```

---

### Task 3: Recommendation Rules B (Pending Decision)

**Files:**
- Modify: `runtime/workspace_doctor.py`
- Modify: `tests/test_workspace_doctor.py`

- [ ] **Step 1: Write the failing test for pending decision**

```python
# tests/test_workspace_doctor.py (append to TestDiagnoseWorkspace class)

    def test_pending_decision_returns_blocked(self, tmp_path):
        """Pending decisions should return BLOCKED status."""
        project = tmp_path / "blocked-project"
        project.mkdir()
        
        # Create runstate with pending decision
        runstate_content = '''---
```yaml
project_id: blocked-test
feature_id: feature-001
current_phase: reviewing
active_task: review-work
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed:
  - decision: architecture-choice
    options:
      - Option A
      - Option B
    impact: system design
last_action: Generated review pack
next_recommended_action: Respond to pending decision
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        # Create minimal product-brief
        brief_content = '''product_id: blocked-test
name: Blocked Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.pending_decisions == 1
        assert "decision" in diagnosis.recommended_action.lower() or "resume" in diagnosis.suggested_command.lower()
        assert len(diagnosis.warnings) >= 1

    def test_blocked_phase_returns_blocked(self, tmp_path):
        """Blocked phase should return BLOCKED status."""
        project = tmp_path / "blocked-phase-project"
        project.mkdir()
        
        runstate_content = '''---
```yaml
project_id: blocked-phase-test
feature_id: feature-001
current_phase: blocked
active_task: ""
task_queue: []
completed_outputs: []
open_questions: []
blocked_items:
  - item: external-api
    reason: API key pending
    since: 2026-04-12T09:00:00Z
decisions_needed: []
last_action: Hit blocker
next_recommended_action: Resolve blocker
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: blocked-phase-test
name: Blocked Phase Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "BLOCKED"
        assert diagnosis.blocked_items_count >= 1
        assert "blocker" in diagnosis.recommended_action.lower() or "unblock" in diagnosis.suggested_command.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_pending_decision_returns_blocked tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_blocked_phase_returns_blocked -v`
Expected: FAIL (status should be BLOCKED but is HEALTHY)

- [ ] **Step 3: Implement Rule B in _apply_rules**

```python
# runtime/workspace_doctor.py (replace _apply_rules function)

def _apply_rules(diagnosis: DoctorDiagnosis, snapshot) -> None:
    """Apply recommendation rules in priority order."""
    
    # Load runstate for additional signals
    runstate = _load_runstate(Path(diagnosis.workspace_path))
    
    # Count blocked items
    blocked_items = runstate.get("blocked_items", [])
    diagnosis.blocked_items_count = len(blocked_items) if blocked_items else 0
    
    # Rule F: Missing state (baseline - lowest priority)
    if not snapshot.product_id or snapshot.current_phase in ["unknown", "none", ""]:
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "Insufficient workspace metadata to make reliable recommendation."
        return
    
    # Rule B: Pending decision (highest priority)
    if snapshot.pending_decisions > 0:
        diagnosis.doctor_status = "BLOCKED"
        diagnosis.health_status = "blocked"
        diagnosis.recommended_action = "Respond to pending decisions before resuming."
        diagnosis.suggested_command = f"asyncdev resume-next-day continue-loop --project {snapshot.product_id}"
        diagnosis.rationale = f"Human decision required ({snapshot.pending_decisions} pending) before execution can proceed."
        diagnosis.warnings = ["Do not continue execution until decisions are resolved."]
        return
    
    # Rule B variant: Blocked phase
    if snapshot.current_phase == "blocked":
        diagnosis.doctor_status = "BLOCKED"
        diagnosis.health_status = "blocked"
        diagnosis.recommended_action = "Resolve blockers before resuming execution."
        diagnosis.suggested_command = f"asyncdev resume-next-day unblock --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is explicitly blocked, requires manual intervention."
        diagnosis.warnings = ["Do not continue until blockers are resolved."]
        return
    
    # Placeholder for remaining rules (Task 4)
    diagnosis.doctor_status = "HEALTHY"
    diagnosis.health_status = "healthy"
    diagnosis.recommended_action = "Check workspace state."
    diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
    diagnosis.rationale = "Workspace has no pending decisions or blockers."


def _load_runstate(project_path: Path) -> dict:
    """Load runstate.yaml block from runstate.md."""
    runstate_path = project_path / "runstate.md"
    
    if not runstate_path.exists():
        return {}
    
    with open(runstate_path, encoding="utf-8") as f:
        content = f.read()
    
    yaml_block_start = content.find("```yaml")
    yaml_block_end = content.find("```", yaml_block_start + 7)
    
    if yaml_block_start == -1 or yaml_block_end == -1:
        return {}
    
    yaml_content = content[yaml_block_start + 7:yaml_block_end].strip()
    return yaml.safe_load(yaml_content) or {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_pending_decision_returns_blocked tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_blocked_phase_returns_blocked -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_workspace_doctor.py runtime/workspace_doctor.py
git commit -m "feat(029): implement Rule B - pending decision and blocked phase"
```

---

### Task 4: Recommendation Rules C, E, A, D

**Files:**
- Modify: `runtime/workspace_doctor.py`
- Modify: `tests/test_workspace_doctor.py`

- [ ] **Step 1: Write failing tests for remaining rules**

```python
# tests/test_workspace_doctor.py (append to TestDiagnoseWorkspace class)

    def test_verification_failed_returns_attention(self, tmp_path):
        """Verification failure should return ATTENTION_NEEDED."""
        project = tmp_path / "verify-failed-project"
        project.mkdir()
        
        # Create execution-result with failed status
        results_dir = project / "execution-results"
        results_dir.mkdir()
        
        result_content = '''---
```yaml
execution_id: exec-failed
status: failed
completed_items: []
artifacts_created: []
verification_result:
  passed: 0
  failed: 1
issues_found:
  - Compatibility mismatch
```
---
'''
        (results_dir / "exec-001.md").write_text(result_content)
        
        runstate_content = '''---
```yaml
project_id: verify-failed
feature_id: feature-001
current_phase: executing
active_task: verify
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Verification failed
next_recommended_action: Check compatibility
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: verify-failed
name: Verify Failed Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert "verification" in diagnosis.recommended_action.lower() or "compatibility" in diagnosis.rationale.lower()

    def test_no_feature_returns_attention(self, tmp_path):
        """No active feature should return ATTENTION_NEEDED."""
        project = tmp_path / "no-feature-project"
        project.mkdir()
        
        runstate_content = '''---
```yaml
project_id: no-feature
feature_id: ""
current_phase: planning
active_task: ""
task_queue: []
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Created product
next_recommended_action: Create feature
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: no-feature
name: No Feature Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert "feature" in diagnosis.recommended_action.lower()

    def test_completed_returns_pending_closeout(self, tmp_path):
        """Completed feature should return COMPLETED_PENDING_CLOSEOUT."""
        project = tmp_path / "completed-project"
        project.mkdir()
        
        runstate_content = '''---
```yaml
project_id: completed-test
feature_id: feature-001
current_phase: completed
active_task: ""
task_queue: []
completed_outputs:
  - schemas/test.yaml
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Feature completed
next_recommended_action: Archive feature
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: completed-test
name: Completed Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"
        assert "archive" in diagnosis.suggested_command.lower()

    def test_archived_returns_pending_closeout(self, tmp_path):
        """Archived feature should return COMPLETED_PENDING_CLOSEOUT."""
        project = tmp_path / "archived-project"
        project.mkdir()
        
        runstate_content = '''---
```yaml
project_id: archived-test
feature_id: feature-001
current_phase: archived
active_task: ""
task_queue: []
completed_outputs:
  - schemas/test.yaml
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Feature archived
next_recommended_action: Start new feature
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: archived-test
name: Archived Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "COMPLETED_PENDING_CLOSEOUT"
        assert "new feature" in diagnosis.recommended_action.lower() or "feature" in diagnosis.suggested_command.lower()

    def test_healthy_planning_returns_healthy(self, tmp_path):
        """Planning phase with no issues should return HEALTHY."""
        project = tmp_path / "healthy-planning"
        project.mkdir()
        
        runstate_content = '''---
```yaml
project_id: healthy-planning
feature_id: feature-001
current_phase: planning
active_task: ""
task_queue:
  - create-schema
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Created feature
next_recommended_action: Plan task
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: healthy-planning
name: Healthy Planning Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert "plan" in diagnosis.suggested_command.lower()

    def test_healthy_executing_returns_healthy(self, tmp_path):
        """Executing phase should return HEALTHY."""
        project = tmp_path / "healthy-executing"
        project.mkdir()
        
        # Create successful execution result
        results_dir = project / "execution-results"
        results_dir.mkdir()
        
        result_content = '''---
```yaml
execution_id: exec-001
status: success
completed_items:
  - Created schema
artifacts_created:
  - name: schema
    path: schemas/test.yaml
verification_result:
  passed: 1
  failed: 0
```
---
'''
        (results_dir / "exec-001.md").write_text(result_content)
        
        runstate_content = '''---
```yaml
project_id: healthy-executing
feature_id: feature-001
current_phase: executing
active_task: create-schema
task_queue: []
completed_outputs:
  - schemas/test.yaml
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Started execution
next_recommended_action: Continue
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: healthy-executing
name: Healthy Executing Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.verification_status == "success"

    def test_healthy_reviewing_returns_healthy(self, tmp_path):
        """Reviewing phase should return HEALTHY."""
        project = tmp_path / "healthy-reviewing"
        project.mkdir()
        
        # Create review artifact
        reviews_dir = project / "reviews"
        reviews_dir.mkdir()
        
        review_content = '''---
```yaml
review_id: review-001
status: pending_review
completed_items:
  - Implementation done
decisions_needed: []
```
---
'''
        (reviews_dir / "2026-04-12-review.md").write_text(review_content)
        
        runstate_content = '''---
```yaml
project_id: healthy-reviewing
feature_id: feature-001
current_phase: reviewing
active_task: ""
task_queue: []
completed_outputs:
  - schemas/test.yaml
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Generated review pack
next_recommended_action: Review artifacts
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: healthy-reviewing
name: Healthy Reviewing Test
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace -v -k "test_verification_failed or test_no_feature or test_completed or test_archived or test_healthy"`
Expected: FAIL (multiple tests fail because rules not implemented)

- [ ] **Step 3: Implement remaining rules in _apply_rules**

```python
# runtime/workspace_doctor.py (replace _apply_rules function completely)

def _apply_rules(diagnosis: DoctorDiagnosis, snapshot) -> None:
    """Apply recommendation rules in priority order (B > C > E > A > F > D)."""
    
    # Load runstate for additional signals
    runstate = _load_runstate(Path(diagnosis.workspace_path))
    
    # Count blocked items
    blocked_items = runstate.get("blocked_items", [])
    diagnosis.blocked_items_count = len(blocked_items) if blocked_items else 0
    
    # Rule F: Missing state (baseline - lowest priority)
    if not snapshot.product_id or snapshot.current_phase in ["unknown", "none", ""]:
        diagnosis.doctor_status = "UNKNOWN"
        diagnosis.recommended_action = "Initialize workspace first."
        diagnosis.suggested_command = "asyncdev init create"
        diagnosis.rationale = "Insufficient workspace metadata to make reliable recommendation."
        return
    
    # Rule B: Pending decision (highest priority)
    if snapshot.pending_decisions > 0:
        diagnosis.doctor_status = "BLOCKED"
        diagnosis.health_status = "blocked"
        diagnosis.recommended_action = "Respond to pending decisions before resuming."
        diagnosis.suggested_command = f"asyncdev resume-next-day continue-loop --project {snapshot.product_id}"
        diagnosis.rationale = f"Human decision required ({snapshot.pending_decisions} pending) before execution can proceed."
        diagnosis.warnings = ["Do not continue execution until decisions are resolved."]
        return
    
    # Rule B variant: Blocked phase
    if snapshot.current_phase == "blocked":
        diagnosis.doctor_status = "BLOCKED"
        diagnosis.health_status = "blocked"
        diagnosis.recommended_action = "Resolve blockers before resuming execution."
        diagnosis.suggested_command = f"asyncdev resume-next-day unblock --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is explicitly blocked, requires manual intervention."
        diagnosis.warnings = ["Do not continue until blockers are resolved."]
        return
    
    # Rule C: Verification failure
    if snapshot.verification_status == "failed":
        diagnosis.doctor_status = "ATTENTION_NEEDED"
        diagnosis.health_status = "warning"
        diagnosis.recommended_action = "Re-check initialization or re-run verification."
        
        if snapshot.initialization_mode == "starter-pack":
            diagnosis.suggested_command = "Check starter-pack.yaml for contract_version and asyncdev_compatibility"
            diagnosis.rationale = "Starter-pack initialization verification failed. Check provider/input compatibility."
            diagnosis.warnings = ["Do not proceed until initialization verification succeeds."]
        else:
            diagnosis.suggested_command = f"asyncdev new-product create --project {snapshot.product_id} --name 'Retry'"
            diagnosis.rationale = "Direct mode initialization verification failed. Check manual setup."
            diagnosis.warnings = ["Do not proceed until initialization verification succeeds."]
        return
    
    # Rule E: Completed pending closeout
    if snapshot.current_phase == "completed":
        diagnosis.doctor_status = "COMPLETED_PENDING_CLOSEOUT"
        diagnosis.health_status = "healthy"
        diagnosis.recommended_action = "Archive completed feature."
        diagnosis.suggested_command = f"asyncdev archive-feature create --project {snapshot.product_id} --feature {snapshot.feature_id}"
        diagnosis.rationale = "Feature work complete but not archived, leaving workspace in ambiguous state."
        return
    
    if snapshot.current_phase == "archived":
        diagnosis.doctor_status = "COMPLETED_PENDING_CLOSEOUT"
        diagnosis.health_status = "healthy"
        diagnosis.recommended_action = "Start a new feature."
        diagnosis.suggested_command = f"asyncdev new-feature create --project {snapshot.product_id} --feature feature-new --name 'New Feature'"
        diagnosis.rationale = "Previous feature archived. Ready to start new work."
        return
    
    # Rule A: No current feature
    if not snapshot.feature_id:
        diagnosis.doctor_status = "ATTENTION_NEEDED"
        diagnosis.health_status = "warning"
        diagnosis.recommended_action = "Create or select a feature."
        diagnosis.suggested_command = f"asyncdev new-feature create --project {snapshot.product_id} --feature feature-001 --name 'First Feature'"
        diagnosis.rationale = "Product exists but no active feature selected."
        return
    
    # Rule D: Healthy active flow
    diagnosis.doctor_status = "HEALTHY"
    diagnosis.health_status = "healthy"
    
    if snapshot.current_phase == "planning":
        diagnosis.recommended_action = "Plan a bounded task for execution."
        diagnosis.suggested_command = f"asyncdev plan-day create --project {snapshot.product_id} --feature {snapshot.feature_id} --task 'Your task description'"
        diagnosis.rationale = "Workspace is in planning phase with no active task. Create an ExecutionPack to start execution."
    elif snapshot.current_phase == "executing":
        diagnosis.recommended_action = "Continue execution or wait for completion."
        diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
        diagnosis.rationale = "Feature is executing, no blockers or decisions pending."
    elif snapshot.current_phase == "reviewing":
        diagnosis.recommended_action = "Review latest artifacts and make decisions."
        diagnosis.suggested_command = f"asyncdev review-night show --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is in reviewing phase. Review artifacts before resuming."
    else:
        diagnosis.recommended_action = "Check workspace state and continue workflow."
        diagnosis.suggested_command = f"asyncdev status --project {snapshot.product_id}"
        diagnosis.rationale = "Workspace is healthy with no immediate actions required."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_workspace_doctor.py runtime/workspace_doctor.py
git commit -m "feat(029): implement all recommendation rules (A-F)"
```

---

### Task 5: Starter-Pack Mode Tests

**Files:**
- Modify: `tests/test_workspace_doctor.py`

- [ ] **Step 1: Write failing tests for starter-pack mode**

```python
# tests/test_workspace_doctor.py (append to TestDiagnoseWorkspace class)

    def test_starter_pack_healthy_returns_healthy(self, tmp_path):
        """Starter-pack mode healthy should return HEALTHY with provider linkage."""
        project = tmp_path / "starter-pack-healthy"
        project.mkdir()
        
        runstate_content = '''---
```yaml
project_id: starter-healthy
feature_id: feature-001
current_phase: planning
active_task: ""
task_queue:
  - create-schema
completed_outputs: []
open_questions: []
blocked_items: []
decisions_needed: []
last_action: Created feature
next_recommended_action: Plan task
updated_at: 2026-04-12T10:00:00Z
workflow_hints:
  policy_mode: balanced
  execution: external-tool-first
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: starter-healthy
name: Starter Pack Healthy Test
starter_pack_context:
  - 'Product type: ai_tooling'
  - 'Stage: mvp'
  - 'Team mode: solo'
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "HEALTHY"
        assert diagnosis.initialization_mode == "starter-pack"
        assert diagnosis.provider_linkage.get("detected") == True
        assert diagnosis.provider_linkage.get("product_type") == "ai_tooling"

    def test_starter_pack_verify_failed_mentions_provider(self, tmp_path):
        """Starter-pack verification failed should mention provider/input issue."""
        project = tmp_path / "starter-pack-verify-failed"
        project.mkdir()
        
        # Create failed execution result
        results_dir = project / "execution-results"
        results_dir.mkdir()
        
        result_content = '''---
```yaml
execution_id: exec-failed
status: failed
completed_items: []
issues_found:
  - Contract version mismatch
```
---
'''
        (results_dir / "exec-001.md").write_text(result_content)
        
        runstate_content = '''---
```yaml
project_id: starter-verify-failed
feature_id: feature-001
current_phase: executing
active_task: verify
task_queue: []
completed_outputs: []
blocked_items: []
decisions_needed: []
last_action: Verification failed
updated_at: 2026-04-12T10:00:00Z
```
---
'''
        (project / "runstate.md").write_text(runstate_content)
        
        brief_content = '''product_id: starter-verify-failed
name: Starter Pack Verify Failed Test
starter_pack_context:
  - 'Product type: web_app'
'''
        (project / "product-brief.yaml").write_text(brief_content)
        
        diagnosis = diagnose_workspace(project)
        
        assert diagnosis.doctor_status == "ATTENTION_NEEDED"
        assert diagnosis.initialization_mode == "starter-pack"
        assert "starter-pack" in diagnosis.suggested_command.lower() or "compatibility" in diagnosis.rationale.lower()
        assert len(diagnosis.warnings) >= 1
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_starter_pack_healthy_returns_healthy tests/test_workspace_doctor.py::TestDiagnoseWorkspace::test_starter_pack_verify_failed_mentions_provider -v`
Expected: PASS (starter-pack logic already implemented in Task 4)

- [ ] **Step 3: Commit**

```bash
git add tests/test_workspace_doctor.py
git commit -m "test(029): add starter-pack mode tests"
```

---

### Task 6: Output Formatting

**Files:**
- Modify: `runtime/workspace_doctor.py`
- Modify: `tests/test_workspace_doctor.py`

- [ ] **Step 1: Write failing tests for formatting**

```python
# tests/test_workspace_doctor.py (append new test class)

class TestFormatDiagnosis:
    def test_format_markdown_contains_all_fields(self):
        """Markdown format should contain all key fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="my-app",
            feature_id="feature-001",
            current_phase="planning",
            recommended_action="Plan a task",
            suggested_command="asyncdev plan-day create",
            rationale="Workspace is healthy"
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "HEALTHY" in output
        assert "my-app" in output
        assert "feature-001" in output
        assert "planning" in output
        assert "Plan a task" in output
        assert "asyncdev plan-day create" in output
        assert "Workspace is healthy" in output

    def test_format_yaml_contains_all_fields(self):
        """YAML format should contain all key fields."""
        diagnosis = DoctorDiagnosis(
            doctor_status="BLOCKED",
            product_id="blocked-app",
            pending_decisions=2,
            recommended_action="Respond to decisions",
            suggested_command="asyncdev resume",
            rationale="2 decisions pending"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        assert "doctor_status: BLOCKED" in output
        assert "product_id: blocked-app" in output
        assert "pending_decisions: 2" in output
        assert "recommended_action: Respond to decisions" in output

    def test_format_markdown_with_warnings(self):
        """Markdown format should include warnings."""
        diagnosis = DoctorDiagnosis(
            doctor_status="BLOCKED",
            warnings=["Do not proceed", "Contact admin"]
        )
        
        output = format_diagnosis_markdown(diagnosis)
        
        assert "Do not proceed" in output
        assert "Contact admin" in output

    def test_format_yaml_valid_yaml(self):
        """YAML format should be valid YAML."""
        diagnosis = DoctorDiagnosis(
            doctor_status="HEALTHY",
            product_id="test-app"
        )
        
        output = format_diagnosis_yaml(diagnosis)
        
        # Should be parseable as YAML
        parsed = yaml.safe_load(output)
        assert parsed["doctor_status"] == "HEALTHY"
        assert parsed["product_id"] == "test-app"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_doctor.py::TestFormatDiagnosis -v`
Expected: FAIL with "cannot import name 'format_diagnosis_markdown'"

- [ ] **Step 3: Implement formatting functions**

```python
# runtime/workspace_doctor.py (append at end of file)


def format_diagnosis_markdown(diagnosis: DoctorDiagnosis) -> str:
    """Format diagnosis as human-readable markdown."""
    lines = [
        f"# Workspace Health: {diagnosis.doctor_status}",
        "",
        f"**Initialization**: {diagnosis.initialization_mode}",
    ]
    
    # Add provider linkage if starter-pack mode
    if diagnosis.initialization_mode == "starter-pack" and diagnosis.provider_linkage.get("detected"):
        if diagnosis.provider_linkage.get("product_type"):
            lines.append(f"  Provider Context: {diagnosis.provider_linkage.get('product_type')}")
        hints = diagnosis.provider_linkage.get("workflow_hints", {})
        if hints.get("policy_mode"):
            lines.append(f"  Policy Mode: {hints.get('policy_mode')}")
    
    lines.extend([
        "",
        "## Execution State",
        f"- Product: {diagnosis.product_id or 'N/A'}",
        f"- Feature: {diagnosis.feature_id or 'N/A'}",
        f"- Phase: **{diagnosis.current_phase or 'N/A'}**",
        "",
        "## Signals",
        f"- Verification: {diagnosis.verification_status}",
        f"- Pending Decisions: {diagnosis.pending_decisions}",
        f"- Blocked Items: {diagnosis.blocked_items_count}",
        "",
        "## Recommended Action",
        f"{diagnosis.recommended_action}",
        "",
        "## Suggested Command",
        f"`{diagnosis.suggested_command}`",
        "",
        "## Why",
        f"{diagnosis.rationale}",
    ])
    
    if diagnosis.warnings:
        lines.extend([
            "",
            "## Warnings",
        ])
        for warning in diagnosis.warnings:
            lines.append(f"- {warning}")
    
    lines.extend([
        "",
        f"[dim]Workspace: {diagnosis.workspace_path}[/dim]",
    ])
    
    return "\n".join(lines)


def format_diagnosis_yaml(diagnosis: DoctorDiagnosis) -> str:
    """Format diagnosis as YAML for machine consumption."""
    data = {
        "doctor_status": diagnosis.doctor_status,
        "health_status": diagnosis.health_status,
        "initialization_mode": diagnosis.initialization_mode,
        "provider_linkage": diagnosis.provider_linkage,
        "execution_state": {
            "product_id": diagnosis.product_id,
            "feature_id": diagnosis.feature_id,
            "current_phase": diagnosis.current_phase,
        },
        "signals": {
            "verification_status": diagnosis.verification_status,
            "pending_decisions": diagnosis.pending_decisions,
            "blocked_items_count": diagnosis.blocked_items_count,
        },
        "recommended_action": diagnosis.recommended_action,
        "suggested_command": diagnosis.suggested_command,
        "rationale": diagnosis.rationale,
        "warnings": diagnosis.warnings,
        "workspace_path": diagnosis.workspace_path,
    }
    
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestFormatDiagnosis -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_workspace_doctor.py runtime/workspace_doctor.py
git commit -m "feat(029): add diagnosis formatting functions"
```

---

### Task 7: CLI Doctor Command

**Files:**
- Create: `cli/commands/doctor.py`
- Modify: `cli/asyncdev.py`

- [ ] **Step 1: Write failing test for CLI command**

```python
# tests/test_workspace_doctor.py (append new test class)

from typer.testing import CliRunner
from cli.asyncdev import app as asyncdev_app


runner = CliRunner()


class TestDoctorCLI:
    def test_doctor_help_works(self):
        """Doctor command help should work."""
        result = runner.invoke(asyncdev_app, ["doctor", "--help"])
        
        assert result.exit_code == 0
        assert "diagnose" in result.output.lower() or "health" in result.output.lower()

    def test_doctor_show_empty_workspace(self):
        """Doctor show on empty workspace should return UNKNOWN."""
        result = runner.invoke(asyncdev_app, ["doctor", "show", "--path", "nonexistent"])
        
        assert result.exit_code == 0
        assert "UNKNOWN" in result.output

    def test_doctor_yaml_format(self):
        """Doctor with --format yaml should output YAML."""
        result = runner.invoke(asyncdev_app, ["doctor", "show", "--format", "yaml", "--path", "nonexistent"])
        
        assert result.exit_code == 0
        assert "doctor_status:" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDoctorCLI -v`
Expected: FAIL with "No such command 'doctor'"

- [ ] **Step 3: Create doctor CLI command**

```python
# cli/commands/doctor.py

"""Workspace Doctor CLI command (Feature 029)."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from runtime.workspace_doctor import diagnose_workspace, format_diagnosis_markdown, format_diagnosis_yaml

app = typer.Typer(name="doctor", help="Diagnose workspace health and recommend next action")
console = Console()


def _resolve_project_path(project_id: Optional[str], projects_path: Path) -> Path:
    """Resolve project path from project ID or find active project."""
    if project_id:
        return projects_path / project_id
    
    # Find most recently updated project
    if not projects_path.exists():
        return Path("nonexistent")
    
    project_dirs = sorted(
        projects_path.iterdir(),
        key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
        reverse=True
    )
    
    for project_dir in project_dirs:
        if project_dir.is_dir() and (project_dir / "runstate.md").exists():
            return project_dir
    
    return Path("nonexistent")


@app.command()
def show(
    project: str = typer.Option(None, "--project", "-p", help="Project ID to diagnose"),
    path: Path = typer.Option("projects", "--path", help="Projects root path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, yaml"),
):
    """Show workspace diagnosis with health classification and recommended next action.
    
    The diagnosis includes:
    - Overall health status (HEALTHY, ATTENTION_NEEDED, BLOCKED, etc.)
    - Current execution state
    - Signal summary (verification, decisions, blockers)
    - Recommended action with exact command
    - Rationale and warnings
    
    This command does NOT mutate workspace state.
    """
    project_path = _resolve_project_path(project, path)
    
    diagnosis = diagnose_workspace(project_path)
    
    if format == "yaml":
        output = format_diagnosis_yaml(diagnosis)
        console.print(output)
    else:
        output = format_diagnosis_markdown(diagnosis)
        console.print(output)
        
        # Show suggested command in panel
        if diagnosis.suggested_command:
            console.print(Panel(
                diagnosis.suggested_command,
                title="Suggested Command",
                border_style="green"
            ))
```

- [ ] **Step 4: Register doctor app in asyncdev.py**

Read `cli/asyncdev.py` to find registration pattern, then add:

```python
# cli/asyncdev.py (add import and registration)

from cli.commands.doctor import app as doctor_app

# Add to app registration section:
asyncdev_app.add_typer(doctor_app, name="doctor")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_doctor.py::TestDoctorCLI -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add cli/commands/doctor.py cli/asyncdev.py tests/test_workspace_doctor.py
git commit -m "feat(029): add doctor CLI command"
```

---

### Task 8: Examples Documentation

**Files:**
- Create: `examples/doctor-output.md`

- [ ] **Step 1: Create examples file**

```markdown
# Doctor Output Examples

Example outputs from `asyncdev doctor show` command.

---

## HEALTHY - Planning Phase

```
# Workspace Health: HEALTHY

**Initialization**: direct

## Execution State
- Product: my-app
- Feature: feature-001
- Phase: **planning**

## Signals
- Verification: not_run
- Pending Decisions: 0
- Blocked Items: 0

## Recommended Action
Plan a bounded task for execution.

## Suggested Command
`asyncdev plan-day create --project my-app --feature feature-001 --task 'Your task description'`

## Why
Workspace is in planning phase with no active task. Create an ExecutionPack to start execution.

[dim]Workspace: projects/my-app[/dim]
```

---

## BLOCKED - Pending Decision

```
# Workspace Health: BLOCKED

**Initialization**: direct

## Execution State
- Product: blocked-app
- Feature: feature-002
- Phase: **reviewing**

## Signals
- Verification: success
- Pending Decisions: 2
- Blocked Items: 0

## Recommended Action
Respond to pending decisions before resuming.

## Suggested Command
`asyncdev resume-next-day continue-loop --project blocked-app`

## Why
Human decision required (2 pending) before execution can proceed.

## Warnings
- Do not continue execution until decisions are resolved.

[dim]Workspace: projects/blocked-app[/dim]
```

---

## ATTENTION_NEEDED - Verification Failed (Starter-Pack)

```
# Workspace Health: ATTENTION_NEEDED

**Initialization**: starter-pack
  Provider Context: ai_tooling
  Policy Mode: balanced

## Execution State
- Product: verify-failed
- Feature: feature-001
- Phase: **executing**

## Signals
- Verification: failed
- Pending Decisions: 0
- Blocked Items: 0

## Recommended Action
Re-check initialization or re-run verification.

## Suggested Command
`Check starter-pack.yaml for contract_version and asyncdev_compatibility`

## Why
Starter-pack initialization verification failed. Check provider/input compatibility.

## Warnings
- Do not proceed until initialization verification succeeds.

[dim]Workspace: projects/verify-failed[/dim]
```

---

## COMPLETED_PENDING_CLOSEOUT

```
# Workspace Health: COMPLETED_PENDING_CLOSEOUT

**Initialization**: direct

## Execution State
- Product: completed-app
- Feature: feature-003
- Phase: **completed**

## Signals
- Verification: success
- Pending Decisions: 0
- Blocked Items: 0

## Recommended Action
Archive completed feature.

## Suggested Command
`asyncdev archive-feature create --project completed-app --feature feature-003`

## Why
Feature work complete but not archived, leaving workspace in ambiguous state.

[dim]Workspace: projects/completed-app[/dim]
```

---

## UNKNOWN - Empty Workspace

```
# Workspace Health: UNKNOWN

**Initialization**: unknown

## Execution State
- Product: N/A
- Feature: N/A
- Phase: **N/A**

## Signals
- Verification: not_run
- Pending Decisions: 0
- Blocked Items: 0

## Recommended Action
Initialize workspace first.

## Suggested Command
`asyncdev init create`

## Why
Insufficient workspace metadata to make reliable recommendation.

[dim]Workspace: nonexistent[/dim]
```

---

## YAML Format Example

Use `--format yaml` for machine-readable output:

```yaml
doctor_status: HEALTHY
health_status: healthy
initialization_mode: direct
provider_linkage:
  detected: false
execution_state:
  product_id: my-app
  feature_id: feature-001
  current_phase: planning
signals:
  verification_status: not_run
  pending_decisions: 0
  blocked_items_count: 0
recommended_action: Plan a bounded task for execution.
suggested_command: asyncdev plan-day create --project my-app --feature feature-001 --task 'Your task description'
rationale: Workspace is in planning phase with no active task.
warnings: []
workspace_path: projects/my-app
```

---

## Usage

```bash
# Show diagnosis for active project
asyncdev doctor show

# Show diagnosis for specific project
asyncdev doctor show --project my-app

# YAML format
asyncdev doctor show --format yaml
```

---

## Health Status Reference

| Status | Meaning | Typical Next Step |
|--------|---------|-------------------|
| HEALTHY | No blockers, active feature | Phase-appropriate command |
| ATTENTION_NEEDED | Needs attention but not blocked | Fix issue or create feature |
| BLOCKED | Requires human decision/intervention | Resolve blocker first |
| COMPLETED_PENDING_CLOSEOUT | Feature done, needs archive | Archive or start new feature |
| UNKNOWN | Cannot determine state | Initialize workspace |

---

## Related Docs

- [docs/doctor.md](../docs/doctor.md) - Full user guide
- [docs/verify.md](../docs/verify.md) - Initialization verification
- [examples/snapshot-output.md](snapshot-output.md) - Workspace snapshot examples
```

- [ ] **Step 2: Commit**

```bash
git add examples/doctor-output.md
git commit -m "docs(029): add doctor output examples"
```

---

### Task 9: User Documentation

**Files:**
- Create: `docs/doctor.md`

- [ ] **Step 1: Create user documentation**

```markdown
# Workspace Doctor Guide

The `asyncdev doctor` command provides workspace diagnosis and next-action recommendations.

---

## Quick Start

```bash
# Diagnose your current workspace
asyncdev doctor show

# Diagnose a specific project
asyncdev doctor show --project my-app

# Get machine-readable output
asyncdev doctor show --format yaml
```

---

## What It Does

Doctor answers these questions:
1. Is my workspace healthy?
2. Is it blocked or needs attention?
3. What should I do next?
4. What exact command should I run?
5. Why is that recommended?
6. When should I not proceed automatically?

---

## Health Statuses

| Status | Meaning |
|--------|---------|
| HEALTHY | Active feature, no blockers, verification passed |
| ATTENTION_NEEDED | Issue detected but not critically blocked |
| BLOCKED | Human decision or intervention required |
| COMPLETED_PENDING_CLOSEOUT | Feature done, needs archive/closeout |
| UNKNOWN | Insufficient metadata to diagnose |

---

## Recommendation Rules

Doctor follows priority rules:

1. **Pending Decision** → BLOCKED, recommend resolving decisions first
2. **Blocked Phase** → BLOCKED, recommend unblock action
3. **Verification Failed** → ATTENTION_NEEDED, recommend checking compatibility
4. **Completed Feature** → COMPLETED_PENDING_CLOSEOUT, recommend archive
5. **No Feature** → ATTENTION_NEEDED, recommend creating feature
6. **Healthy** → HEALTHY, recommend phase-appropriate next step

---

## Starter-Pack Mode

When your workspace was initialized from a starter pack, doctor:
- Shows provider context (product type, policy mode)
- Adjusts verification failure recommendations
- Never assumes advisor is required

---

## Safety Guarantees

- **No state mutation**: Doctor only reads, never writes
- **Explicit commands**: Every suggestion is a real CLI command
- **Clear warnings**: When you shouldn't auto-proceed, doctor tells you

---

## Example Scenarios

### Scenario: Just Created a Product

```bash
asyncdev doctor show
```

Output:
```
# Workspace Health: ATTENTION_NEEDED

Recommended Action: Create or select a feature.

Suggested Command: asyncdev new-feature create --project my-app --feature feature-001 --name 'First Feature'

Why: Product exists but no active feature selected.
```

### Scenario: Pending Decision

```bash
asyncdev doctor show
```

Output:
```
# Workspace Health: BLOCKED

Recommended Action: Respond to pending decisions before resuming.

Warnings:
- Do not continue execution until decisions are resolved.
```

### Scenario: Verification Failed

```bash
asyncdev doctor show
```

Output (starter-pack mode):
```
# Workspace Health: ATTENTION_NEEDED

Recommended Action: Re-check initialization or re-run verification.

Suggested Command: Check starter-pack.yaml for contract_version and asyncdev_compatibility

Warnings:
- Do not proceed until initialization verification succeeds.
```

---

## Integration with Other Commands

| Command | Relationship |
|---------|-------------|
| `asyncdev snapshot show` | Shows state; doctor interprets it |
| `asyncdev status` | Shows current phase; doctor recommends next action |
| `asyncdev verify` | Confirms setup; doctor diagnoses if failed |

---

## Next Steps

After running doctor:
1. If HEALTHY → proceed with suggested command
2. If BLOCKED → resolve blocker first
3. If ATTENTION_NEEDED → fix the issue before continuing
4. If COMPLETED_PENDING_CLOSEOUT → archive or start new feature

---

See [examples/doctor-output.md](../examples/doctor-output.md) for more output examples.
```

- [ ] **Step 2: Commit**

```bash
git add docs/doctor.md
git commit -m "docs(029): add doctor user guide"
```

---

### Task 10: README Integration

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add doctor link to README**

In the Learn More section (around line 140), add entry:

```markdown
| [examples/doctor-output.md](examples/doctor-output.md) | Workspace diagnosis examples for all health states |
```

Also update Project Status section (around line 355):

```markdown
| Features Complete | 29 (001-029) |
| Tests Passing | 551 + doctor tests |
```

And update Roadmap section (around line 377):

```markdown
| UX Docs | ✅ Done | First-run, drift repair, onboarding, positioning, verification, snapshot, doctor (023-029) |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(029): add doctor to README links and status"
```

---

### Task 11: Final Verification

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests pass (551 + ~20 new doctor tests)

- [ ] **Step 2: Run LSP diagnostics**

Run: Check for type errors in new files
Expected: No new errors

- [ ] **Step 3: Test CLI manually**

```bash
python cli/asyncdev.py doctor show --help
python cli/asyncdev.py doctor show
python cli/asyncdev.py doctor show --format yaml
```

Expected: All commands work correctly

- [ ] **Step 4: Commit and push**

```bash
git push origin main
```

---

## Self-Review

**Spec coverage:**
- ✅ AC1 (single-command) - Task 7
- ✅ AC2 (health state explicit) - Task 3-4
- ✅ AC3 (next action explicit) - Task 3-4
- ✅ AC4 (rationale present) - Task 3-4
- ✅ AC5 (blocked safe) - Task 3
- ✅ AC6 (direct mode) - Task 4-5
- ✅ AC7 (starter-pack mode) - Task 5
- ✅ AC8 (examples) - Task 8
- ✅ AC9 (no mutation) - Doctor only reads

**Placeholder scan:** No TBD, TODO, or vague instructions. All code shown.

**Type consistency:** DoctorDiagnosis fields match across all tasks.