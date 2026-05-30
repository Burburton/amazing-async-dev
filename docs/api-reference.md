# API Reference

Developer documentation for `amazing-async-dev` runtime APIs.

---

## Overview

The runtime module provides programmatic access to all async-dev functionality:

```python
from runtime.state_store import StateStore, generate_execution_id
from runtime.recovery_classifier import RecoveryClassification, ResumeEligibility
from runtime.workspace_doctor import WorkspaceDoctor
from runtime.review_pack_builder import ReviewPackBuilder
```

---

## StateStore

File-based state storage for RunState and artifacts.

### Initialize

```python
from pathlib import Path
from runtime.state_store import StateStore

store = StateStore(project_path=Path("projects/my-app"))
```

### RunState Operations

```python
# Load current RunState
runstate = store.load_runstate()
# Returns: dict | None

# Save RunState
store.save_runstate(runstate)

# Load specific execution pack
pack = store.load_execution_pack("exec-20260501-001")

# Save execution pack
store.save_execution_pack(execution_pack)

# Load execution result
result = store.load_execution_result("exec-20260501-001")

# Save execution result
store.save_execution_result(execution_result)

# Load daily review pack
review = store.load_daily_review_pack("2026-05-01")

# Save daily review pack
store.save_daily_review_pack(review_pack)
```

### Utility Functions

```python
from runtime.state_store import generate_execution_id, update_runstate_from_result

# Generate unique execution ID
exec_id = generate_execution_id(project_path=Path("projects/my-app"))
# Returns: "exec-20260501-001"

# Update RunState from ExecutionResult
updated_runstate = update_runstate_from_result(runstate, execution_result)
```

### Project Link Operations

```python
from runtime.state_store import (
    load_project_link,
    get_ownership_mode,
    is_managed_external,
    get_product_repo_path
)

# Load project-link.yaml
link = load_project_link(project_path)
# Returns: dict | None

# Get ownership mode
mode = get_ownership_mode(project_path)
# Returns: "self_hosted" | "managed_external"

# Check if managed external
is_external = is_managed_external(project_path)

# Get product repo path (for managed_external mode)
repo_path = get_product_repo_path(project_path)
```

---

## RecoveryClassifier

Recovery classification for workflow state.

### RecoveryClassification Enum

```python
from runtime.recovery_classifier import RecoveryClassification

# Possible values:
RecoveryClassification.NORMAL_PAUSE       # Workflow stopped normally
RecoveryClassification.BLOCKED           # Blocked by external dependency
RecoveryClassification.FAILED            # Execution failed unexpectedly
RecoveryClassification.AWAITING_DECISION # Paused for human decision
RecoveryClassification.READY_TO_RESUME   # Safe to resume
RecoveryClassification.UNSAFE_TO_RESUME  # State inconsistent
RecoveryClassification.ALREADY_COMPLETED # Feature completed
RecoveryClassification.ALREADY_ARCHIVED  # Feature archived
RecoveryClassification.AWAITING_ACCEPTANCE # Acceptance failed
```

### ResumeEligibility Enum

```python
from runtime.recovery_classifier import ResumeEligibility

# Possible values:
ResumeEligibility.ELIGIBLE              # Safe to resume
ResumeEligibility.NEEDS_DECISION        # Blocked by pending decision
ResumeEligibility.NEEDS_UNBLOCK          # Blocked by blocker
ResumeEligibility.NEEDS_FAILURE_HANDLING # Blocked by failed state
ResumeEligibility.INCONSISTENT_STATE     # State inconsistent
ResumeEligibility.NOT_RESUMABLE          # Completed or archived
ResumeEligibility.NEEDS_ACCEPTANCE       # Blocked by acceptance failure
```

### Classifier Usage

```python
from runtime.recovery_classifier import RecoveryClassifier

classifier = RecoveryClassifier(project_path=Path("projects/my-app"))
result = classifier.classify()

# Result keys:
# - classification: RecoveryClassification
# - explanation: str
# - recommended_action: str
# - eligibility: ResumeEligibility
```

---

## WorkspaceDoctor

Diagnose workspace health and recommend next actions.

### Basic Usage

```python
from runtime.workspace_doctor import WorkspaceDoctor

doctor = WorkspaceDoctor(project_path=Path("projects/my-app"))
diagnosis = doctor.diagnose()

# Diagnosis keys:
# - is_healthy: bool
# - issues: list[dict]
# - recommendations: list[str]
# - next_action: str
```

---

## ReviewPackBuilder

Build nightly review packs.

### Basic Usage

```python
from runtime.review_pack_builder import ReviewPackBuilder

builder = ReviewPackBuilder(project_path=Path("projects/my-app"))
review = builder.build()

# Review keys:
# - date: str
# - project_id: str
# - completed_items: list[str]
# - blocked_items: list[str]
# - decisions_needed: list[dict]
# - recommendations: list[str]
```

---

## ExecutionPolicy

Policy-based execution control.

### Policy Modes

```python
from runtime.execution_policy import PolicyMode, get_policy_mode, set_policy_mode

# Get current policy mode
mode = get_policy_mode(project_path)
# Returns: PolicyMode

# Set policy mode
set_policy_mode(project_path, PolicyMode.CONSERVATIVE)
set_policy_mode(project_path, PolicyMode.BALANCED)
set_policy_mode(project_path, PolicyMode.LOW_INTERRUPTION)

# Policy modes:
# - CONSERVATIVE: Pause for any risk
# - BALANCED: Pause for significant risk only
# - LOW_INTERRUPTION: Only pause for critical issues
```

---

## Blocking Alert Management

Handle blocking alerts in RunState content.

```python
from runtime.state_store import (
    generate_blocking_alert,
    has_blocking_alert,
    remove_blocking_alert
)

# Generate blocking alert for RunState
alert = generate_blocking_alert(runstate)

# Check if content has blocking alert
has_blocking = has_blocking_alert(content)

# Remove blocking alert from content
clean_content = remove_blocking_alert(content)
```

---

## Path Structure

Standard project path structure:

```
projects/{product_id}/
├── product-brief.yaml
├── runstate.md
├── project-link.yaml           # Optional
├── features/
│   └── {feature_id}/
│       └── feature-spec.yaml
├── execution-packs/
│   └── exec-YYYYMMDD-###.md
├── execution-results/
│   └── exec-YYYYMMDD-###.md
└── reviews/
    └── YYYY-MM-DD-review.md
```

---

## Schema Validation

Artifact schemas are in `schemas/` directory:

```python
import yaml
from pathlib import Path

# Load schema
schema_path = Path("schemas/runstate.schema.yaml")
with open(schema_path) as f:
    schema = yaml.safe_load(f)

# Validate artifact against schema
from runtime.validators import validate_artifact
errors = validate_artifact(artifact, schema)
```

---

## Engine Interface

Execution engines are in `runtime/engines/`:

```python
from runtime.engines import ExternalToolEngine, LiveApiEngine, MockEngine

# External tool mode
engine = ExternalToolEngine(project_path=Path("projects/my-app"))
result = engine.execute(execution_pack)

# Live API mode
engine = LiveApiEngine(project_path=Path("projects/my-app"))
result = engine.execute(execution_pack)

# Mock mode (testing)
engine = MockEngine(project_path=Path("projects/my-app"))
result = engine.execute(execution_pack)
```

---

## Event Types

Execution event types for logging:

```python
from runtime.execution_event_types import ExecutionEventType

# Event types:
ExecutionEventType.EXECUTION_STARTED
ExecutionEventType.EXECUTION_COMPLETED
ExecutionEventType.EXECUTION_FAILED
ExecutionEventType.EXECUTION_BLOCKED
ExecutionEventType.DECISION_REQUESTED
ExecutionEventType.PHASE_TRANSITION
```

---

## Archive Operations

Query and inspect archived features:

```python
from runtime.archive_query import ArchiveQuery

query = ArchiveQuery(project_path=Path("projects/my-app"))

# List archives
archives = query.list_archives(product_id="my-app")

# Get archive details
archive = query.get_archive(feature_id="feature-001")

# Get delivered outputs
outputs = query.get_delivered_outputs(feature_id="feature-001")
```

---

## Notification Store

Manage notifications:

```python
from runtime.notification_store import NotificationStore

store = NotificationStore()

# Create notification
store.create(
    project_id="my-app",
    event_type="execution_completed",
    message="Execution completed successfully"
)

# List notifications
notifications = store.list(project_id="my-app")

# Mark as read
store.mark_read(notification_id)
```

---

## Further Reference

| Module | Purpose |
|--------|---------|
| `runtime/state_store.py` | File-based RunState and artifact storage |
| `runtime/recovery_classifier.py` | Recovery state classification |
| `runtime/workspace_doctor.py` | Health diagnosis |
| `runtime/review_pack_builder.py` | Nightly review pack builder |
| `runtime/execution_policy.py` | Policy-based execution control |
| `runtime/archive_query.py` | Archive querying |
| `runtime/notification_store.py` | Notification management |
| `runtime/execution_observer.py` | Execution supervision |
| `runtime/acceptance_runner.py` | Acceptance validation |
| `runtime/engines/` | Execution engines |
