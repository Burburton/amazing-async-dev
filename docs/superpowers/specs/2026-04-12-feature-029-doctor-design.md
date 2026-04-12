# Feature 029 - Workspace Doctor Design

**Date**: 2026-04-12
**Feature**: 029 - Workspace Doctor / Recommended Next Action
**Status**: Design Approved

---

## Overview

Add a lightweight operator guidance layer that provides workspace diagnosis and next-action recommendations. Users can run `asyncdev doctor` to understand:
- Is the workspace healthy?
- Is it blocked or needs attention?
- What should I do next (exact command)?
- Why is that recommended?

---

## Design Decisions

### 1. Health Model: Dual Layer

| Layer | Values | Purpose |
|-------|--------|---------|
| **Bottom (RunState)** | healthy, warning, blocked, failed | System internal factual signals |
| **Top (Doctor)** | HEALTHY, ATTENTION_NEEDED, BLOCKED, COMPLETED_PENDING_CLOSEOUT, UNKNOWN | User-facing interpretive status |

Doctor status is derived from RunState.health_status + phase + signals, not replacing it.

### 2. CLI Entry Point

```bash
asyncdev doctor                    # Diagnose current workspace
asyncdev doctor --project my-app   # Diagnose specific project
asyncdev doctor --format yaml      # Machine-readable output
```

Independent command, not a subcommand of `status` or `snapshot`.

### 3. Output Formats

- **markdown** (default): Human-readable with Rich formatting
- **yaml**: Machine-readable for CI integration

### 4. Verification Integration

Doctor **diagnoses** verification status but **does not trigger** verification. It recommends running verification when appropriate, preserving explicit operator control.

---

## Module Structure

```
runtime/workspace_doctor.py     # Core diagnosis logic
cli/commands/doctor.py          # CLI entry point
examples/doctor-output.md       # Output examples
docs/doctor.md                  # User documentation
tests/test_workspace_doctor.py  # Unit tests
```

---

## Data Structure

```python
@dataclass
class DoctorDiagnosis:
    """Workspace diagnosis result."""
    
    # Health classification (user-facing)
    doctor_status: str = "UNKNOWN"  # HEALTHY, ATTENTION_NEEDED, BLOCKED, COMPLETED_PENDING_CLOSEOUT, UNKNOWN
    
    # Bottom layer status reference
    health_status: str = "unknown"  # healthy, warning, blocked, failed
    
    # Initialization info (from snapshot)
    initialization_mode: str = "unknown"
    provider_linkage: dict[str, Any] = field(default_factory=dict)
    
    # Execution state
    product_id: str = ""
    feature_id: str = ""
    current_phase: str = ""
    
    # Signal summary
    verification_status: str = "not_run"
    pending_decisions: int = 0
    blocked_items_count: int = 0
    
    # Recommendation content
    recommended_action: str = ""      # Action description
    suggested_command: str = ""       # Exact command to run
    rationale: str = ""               # Why this recommendation
    warnings: list[str] = field(default_factory=list)  # Do-not-auto-proceed conditions
    
    workspace_path: str = ""
```

---

## Recommendation Rules (A-F)

Priority order (higher priority rules override lower):

### Rule B - Pending Decision (Highest)

```
Condition: pending_decisions > 0 OR current_phase == "blocked"
Status: BLOCKED
Recommended: Review decision status or resolve blockers
Command: asyncdev resume-next-day continue-loop --project {id}
Rationale: Human decision required before execution can proceed
Warning: Do not continue execution until decisions are resolved
```

### Rule C - Verification Failure

```
Condition: verification_status == "failed"
Status: ATTENTION_NEEDED
Recommended: Re-check initialization or re-run verification
Command: 
  - Direct mode: Check manual setup
  - Starter-pack mode: Re-check starter-pack compatibility
Rationale: Initialization verification failed, may need input correction
Warning: Do not proceed until verification passes
```

### Rule E - Completed Pending Closeout

```
Condition: current_phase in ["completed", "reviewing"] AND feature work done
Status: COMPLETED_PENDING_CLOSEOUT
Recommended: Archive completed feature
Command: asyncdev archive-feature create --project {id} --feature {fid}
Rationale: Feature work complete but not archived, leaving workspace in ambiguous state
```

### Rule A - No Current Feature

```
Condition: feature_id == "" AND product_id exists
Status: ATTENTION_NEEDED
Recommended: Create or select a feature
Command: asyncdev new-feature create --project {id} --feature {fid} --name "{name}"
Rationale: Product exists but no active feature selected
```

### Rule F - Missing State

```
Condition: product_id == "" OR current_phase == "unknown" OR no runstate
Status: UNKNOWN
Recommended: Initialize workspace first
Command: asyncdev init create
Rationale: Insufficient workspace metadata to make reliable recommendation
```

### Rule D - Healthy Active Flow

```
Condition: All above conditions false AND verification_status != "failed"
Status: HEALTHY
Recommended: Phase-appropriate next action
Command: 
  - planning: asyncdev plan-day create ...
  - executing: (continue or wait)
  - reviewing: asyncdev review-night generate ...
Rationale: Workspace is healthy, proceed with normal workflow
```

---

## Implementation Logic

```python
def diagnose_workspace(project_path: Path) -> DoctorDiagnosis:
    """Generate workspace diagnosis."""
    
    # 1. Gather snapshot data (reuse Feature 028)
    snapshot = generate_workspace_snapshot(project_path)
    
    # 2. Load runstate for additional signals
    runstate = _load_runstate(project_path)
    
    # 3. Apply recommendation rules
    diagnosis = _apply_rules(snapshot, runstate)
    
    # 4. Build suggested command
    diagnosis.suggested_command = _build_command(diagnosis)
    
    return diagnosis


def _apply_rules(snapshot, runstate) -> DoctorDiagnosis:
    """Apply recommendation rules in priority order."""
    
    diagnosis = DoctorDiagnosis()
    _copy_snapshot_fields(snapshot, diagnosis)
    
    # Rule F: Missing state (lowest priority baseline)
    if not snapshot.product_id or snapshot.current_phase in ["unknown", "none"]:
        return _apply_rule_missing(diagnosis)
    
    # Rule B: Blocked/pending decision (highest)
    if snapshot.pending_decisions > 0:
        return _apply_rule_pending_decision(diagnosis)
    if snapshot.current_phase == "blocked":
        return _apply_rule_blocked(diagnosis, runstate)
    
    # Rule C: Verification failure
    if snapshot.verification_status == "failed":
        return _apply_rule_verification_failed(diagnosis)
    
    # Rule E: Completed pending closeout
    if snapshot.current_phase in ["completed", "archived"]:
        return _apply_rule_closeout(diagnosis)
    
    # Rule A: No feature
    if not snapshot.feature_id:
        return _apply_rule_no_feature(diagnosis)
    
    # Rule D: Healthy
    return _apply_rule_healthy(diagnosis, runstate)
```

---

## CLI Implementation

```python
# cli/commands/doctor.py

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from runtime.workspace_doctor import diagnose_workspace, format_diagnosis_markdown, format_diagnosis_yaml

app = typer.Typer(name="doctor", help="Diagnose workspace health and recommend next action")
console = Console()


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
        
        # Show next step panel
        if diagnosis.suggested_command:
            console.print(Panel(
                diagnosis.suggested_command,
                title="Suggested Command",
                border_style="green"
            ))
```

---

## Starter-Pack Mode Awareness

When `initialization_mode == "starter-pack"`, doctor:

1. **Surfaces provider linkage** in diagnosis (provider context, policy mode)
2. **Adjusts recommendations** for verification failure:
   - Mention "starter-pack/provider/input issue"
   - Recommend re-checking starter-pack compatibility
   - Do NOT assume advisor is the only provider

Provider-neutral wording by default. Advisor-specific wording only when confidently known from metadata.

---

## Mode Awareness Examples

### Direct Mode - Healthy

```text
Workspace Health: HEALTHY
Initialization: direct

Recommended Action: Plan a bounded task for execution.
Suggested Command: asyncdev plan-day create --project my-app ...
Why: Workspace is in planning phase with no active task.
```

### Starter-Pack Mode - Healthy

```text
Workspace Health: HEALTHY
Initialization: starter-pack
  Provider Context: ai_tooling
  Policy Mode: balanced

Recommended Action: Continue execution or wait for completion.
Suggested Command: (continue current task)
Why: Feature is executing, no blockers or decisions pending.
```

### Starter-Pack Mode - Verification Failed

```text
Workspace Health: ATTENTION_NEEDED
Initialization: starter-pack
  Provider Context: ai_tooling

Verification Status: failed (compatibility mismatch)

Recommended Action: Re-check starter-pack compatibility and re-run verification.
Suggested Command: Check starter-pack.yaml for contract_version and asyncdev_compatibility
Why: Workspace initialized from starter-pack but recorded compatibility does not match expected version.
Warning: Do not proceed until initialization verification succeeds.
```

---

## No State Mutation

Doctor command is **read-only**:
- Only reads: product-brief.yaml, runstate.md, execution-results, reviews
- Does NOT write any files
- Does NOT modify runstate
- Does NOT trigger verification

---

## Test Coverage

| Test Case | doctor_status | Verification |
|-----------|---------------|--------------|
| Empty projects dir | UNKNOWN | Returns diagnosis without error |
| No product | UNKNOWN | Suggests init create |
| No feature | ATTENTION_NEEDED | Suggests new-feature create |
| Pending decision | BLOCKED | Suggests resume-next-day |
| Blocked phase | BLOCKED | Suggests unblock |
| Verification failed | ATTENTION_NEEDED | Suggests verification steps |
| Healthy planning | HEALTHY | Suggests plan-day create |
| Healthy executing | HEALTHY | Suggests continue/wait |
| Healthy reviewing | HEALTHY | Suggests review-night |
| Completed feature | COMPLETED_PENDING_CLOSEOUT | Suggests archive-feature |
| Archived feature | COMPLETED_PENDING_CLOSEOUT | Suggests start new feature |
| Starter-pack healthy | HEALTHY | Surfaces provider linkage |
| Starter-pack verify failed | ATTENTION_NEEDED | Mentions provider/input issue |
| YAML format | HEALTHY | Valid YAML output |
| Markdown format | HEALTHY | Proper formatting |

---

## Documentation Deliverables

1. `docs/doctor.md` - User guide for doctor command
2. `examples/doctor-output.md` - Output examples for all scenarios
3. README.md link in Learn More section
4. Cross-link from docs/verify.md and docs/operating-model.md

---

## Success Metrics

After implementation:
- User can run one command and understand next safe step
- Blocked vs healthy vs closeout-needed states are obvious
- Starter-pack issues are easier to route
- No hidden state mutation