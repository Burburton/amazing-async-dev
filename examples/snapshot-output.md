# Workspace Snapshot Output Examples

Example outputs from `asyncdev snapshot show` command.

---

## Direct Mode Example

```
Workspace Snapshot

Initialization: direct

Execution State
  Product: my-app
  Feature: feature-001
  Phase: planning
  Last Checkpoint: Created product

Signals
  Verification: not_run
  Review: missing
  Pending Decisions: 0

Recommended Next Step
  Plan a bounded task for execution.

[dim]Workspace: projects/my-app[/dim]
```

---

## Starter-Pack Mode Example

```
Workspace Snapshot

Initialization: starter-pack
  Provider Context: ai_tooling
  Policy Mode: balanced

Execution State
  Product: ai-tool-001
  Feature: feature-002
  Phase: executing
  Last Checkpoint: Started execution

Signals
  Verification: success
    Latest: execution-results/exec-20260412-001.md
  Review: present
    Latest: reviews/2026-04-12-review.md
  Pending Decisions: 0

Recommended Next Step
  Continue execution or wait for completion.

[dim]Workspace: projects/ai-tool-001[/dim]
```

---

## Blocked State Example

```
Workspace Snapshot

Initialization: direct

Execution State
  Product: blocked-app
  Feature: feature-003
  Phase: blocked
  Last Checkpoint: Hit blocker

Signals
  Verification: success
  Review: present
  Pending Decisions: 0

Recommended Next Step
  Resolve blockers before resuming execution.

[dim]Workspace: projects/blocked-app[/dim]
```

---

## Pending Decision Example

```
Workspace Snapshot

Initialization: starter-pack
  Provider Context: web_app
  Policy Mode: conservative

Execution State
  Product: decision-app
  Feature: feature-004
  Phase: reviewing
  Last Checkpoint: Generated review pack

Signals
  Verification: success
  Review: present
  Pending Decisions: 2

Recommended Next Step
  Respond to pending decisions before resuming.

[dim]Workspace: projects/decision-app[/dim]
```

---

## YAML Format Example

Use `--format yaml` for machine-readable output:

```yaml
initialization_mode: starter-pack
provider_linkage:
  detected: true
  product_type: ai_tooling
  workflow_hints:
    policy_mode: balanced
execution_state:
  product_id: ai-tool-001
  product_name: AI Tool
  feature_id: feature-002
  current_phase: executing
  last_checkpoint: Started execution
signals:
  verification:
    status: success
    artifact: execution-results/exec-20260412-001.md
  review:
    status: present
    artifact: reviews/2026-04-12-review.md
  pending_decisions: 0
recommended_next_step: Continue execution or wait for completion.
workspace_path: projects/ai-tool-001
```

---

## Usage

```bash
# Show snapshot for active project
python cli/asyncdev.py snapshot show

# Show snapshot for specific project
python cli/asyncdev.py snapshot show --project my-app

# YAML format
python cli/asyncdev.py snapshot show --format yaml
```

---

## Key Fields

| Field | Purpose |
|-------|---------|
| `Initialization Mode` | Direct or starter-pack |
| `Provider Context` | Optional starter-pack metadata |
| `Product/Feature/Phase` | Current execution state |
| `Verification` | Latest execution result status |
| `Review` | Latest review artifact status |
| `Pending Decisions` | Count of decisions needing response |
| `Recommended Next Step` | Heuristic action suggestion |

---

## Related Docs

- [docs/verify.md](../docs/verify.md) - Initialization verification
- [docs/operating-model.md](../docs/operating-model.md) - Workflow phases