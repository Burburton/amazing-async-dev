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
- **No auto-execution**: Doctor never triggers verify, feedback capture, or issue escalation

---

## Recovery Playbooks

When the workspace is in a problematic state, doctor provides **recovery hints** to help you diagnose and resolve issues.

### What Recovery Hints Include

For problematic scenarios, doctor adds:
- **Likely Cause**: Why this state likely occurred
- **What To Check**: Items to inspect first
- **Recovery Steps**: Ordered actions to resolve
- **If This Fails, Try Next**: Fallback if primary recovery fails

### Supported Recovery Scenarios

| Scenario | Trigger | Recovery Focus |
|----------|---------|----------------|
| BLOCKED + pending decision | `pending_decisions > 0` | Decision resolution |
| BLOCKED phase | `current_phase = blocked` | Blocker removal |
| ATTENTION_NEEDED + not_run | `verification_status = not_run` | Validation |
| ATTENTION_NEEDED + failed | `verification_status = failed` | Compatibility fix |
| COMPLETED_PENDING_CLOSEOUT | `current_phase = completed/archived` | Archive/closeout |
| UNKNOWN | Missing or unreadable state | State restoration |

### When Recovery Hints Appear

- Only for problematic states (BLOCKED, ATTENTION_NEEDED, COMPLETED_PENDING_CLOSEOUT, UNKNOWN)
- HEALTHY workspaces get no recovery hints (clean output)
- Hints are deterministic, derived from current state

### Recovery vs Feedback Mechanism

| Feature | Purpose |
|---------|---------|
| **Doctor Recovery** (030) | Immediate operator guidance for current state |
| **Feedback Capture** (019) | System improvement, recurring issue tracking |
| **Feedback Handoff** (031) | Bridge between diagnosis and feedback |

- Doctor helps you **recover now**
- Feedback helps you **improve later**
- Feedback handoff suggests **when to capture**

---

## Feedback Handoff

For scenarios that may indicate **systemic friction** or **recurring issues**, doctor may suggest capturing the problem as workflow feedback.

### What Feedback Handoff Includes

When appropriate, doctor adds:
- **Feedback Suggestion**: "This may be worth capturing as workflow feedback"
- **Why**: Explanation of why this issue may be systemic
- **Suggested Feedback Command**: Recommended `asyncdev feedback record` command

### When Feedback Handoff Appears

Doctor suggests feedback handoff only for scenarios that often indicate **tooling, process, or documentation friction**:

| Scenario | Why It May Be Systemic |
|----------|------------------------|
| Verification failed | Contract mismatch, tooling friction, documentation gaps |
| Unknown state | Missing state, artifact corruption, initialization gaps |

**Not all problematic states trigger feedback suggestion:**
- BLOCKED (pending decision) → Local recovery, not systemic
- COMPLETED_PENDING_CLOSEOUT → Normal workflow end, not friction
- ATTENTION_NEEDED + not_run → One-time setup issue, not recurring

### Feedback Handoff is Explicit and Optional

- **No auto-capture**: Doctor never creates feedback records
- **No auto-triage**: Doctor never triggers feedback workflows
- **User-invoked**: You must run the suggested command manually
- **Conservative**: Doctor under-suggests rather than over-suggests

### Example with Feedback Handoff

```bash
asyncdev doctor show
```

Output for ATTENTION_NEEDED + verification failed:

```
# Workspace Health: ATTENTION_NEEDED

**Initialization**: direct

## Execution State
- Product: my-app
- Feature: feature-001
- Phase: **executing**

## Signals
- Verification: failed
- Pending Decisions: 0
- Blocked Items: 0

## Recommended Action
Re-check initialization or re-run verification.

## Suggested Command
`asyncdev verify`

## Why
Direct mode initialization verification failed. Check manual setup.

## Warnings
- Do not proceed until verification succeeds.

## Recovery Hints

**Likely Cause**: Contract mismatch, missing artifact, invalid initialization, or configuration drift.

**What To Check**:
- latest verification output
- starter-pack compatibility (if applicable)
- required workspace files

**Recovery Steps**:
1. Inspect verification failure details
2. Correct mismatch or missing inputs
3. Rerun verification

**If This Fails, Try Next**: Compare current workspace state with expected example or docs

## Feedback Suggestion

This may be worth capturing as workflow feedback.

**Why**: Verification failure often indicates contract mismatch, tooling friction, or documentation gaps.

## Suggested Feedback Command
`asyncdev feedback record --scope product --project my-app --description 'Verification failure pattern'
```

---

### How to Use Feedback Handoff

1. See the feedback suggestion in doctor output
2. Decide if this issue is worth capturing for improvement
3. If yes, run the suggested `asyncdev feedback record` command manually
4. If no, continue with recovery steps

---

## Example with Recovery Hints

```bash
asyncdev doctor show
```

Output for BLOCKED state:

```
# Workspace Health: BLOCKED

**Initialization**: direct

## Execution State
- Product: my-app
- Feature: feature-002
- Phase: **reviewing**

## Signals
- Verification: success
- Pending Decisions: 2
- Blocked Items: 0

## Recommended Action
Respond to pending decisions before resuming.

## Suggested Command
`asyncdev resume-next-day continue-loop --project my-app`

## Why
Human decision required (2 pending).

## Warnings
- Do not continue until decisions are resolved.

## Recovery Hints

**Likely Cause**: Workflow cannot safely continue until human decision is resolved.

**What To Check**:
- decision request details
- blocking phase context
- latest review artifacts

**Recovery Steps**:
1. Inspect pending decision request
2. Confirm required human input
3. Resolve decision or resume with explicit command

**If This Fails, Try Next**: Review latest nightly pack or unblock instructions
```

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