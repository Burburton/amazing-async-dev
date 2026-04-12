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
- Do not continue until decisions are resolved.
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
- Do not proceed until verification succeeds.
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