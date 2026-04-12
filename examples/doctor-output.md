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
`asyncdev plan-day create --project my-app --feature feature-001 --task 'Your task'`

## Why
Workspace is in planning phase. Create an ExecutionPack.

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
Human decision required (2 pending).

## Warnings
- Do not continue until decisions are resolved.

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
- Do not proceed until verification succeeds.

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
Feature work complete but not archived.

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
Project directory does not exist.

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
suggested_command: asyncdev plan-day create --project my-app --feature feature-001 --task 'Your task'
rationale: Workspace is in planning phase. Create an ExecutionPack.
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