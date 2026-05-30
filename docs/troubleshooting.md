# Troubleshooting Guide

Common issues and solutions for `amazing-async-dev`.

---

## Quick Diagnostics

Before troubleshooting, run these commands to identify the issue:

```bash
# Check workspace health
python cli/asyncdev.py doctor --project <id>

# Check platform status
python cli/asyncdev.py home status

# Check blocking states
python cli/asyncdev.py home blocking --project <id>
```

---

## Common Errors

### "Project not found"

**Cause**: The project doesn't exist or path is incorrect.

**Solution**:
```bash
# List available projects
python cli/asyncdev.py new-product list

# Check if project directory exists
ls projects/<id>/
```

---

### "Product already exists"

**Cause**: Trying to create a product with an ID that already exists.

**Solution**: Use a different product ID, or delete the existing one:
```bash
rm -rf projects/<id>
```

---

### "Feature not found"

**Cause**: Feature doesn't exist or hasn't been created yet.

**Solution**:
```bash
# List features for the product
python cli/asyncdev.py new-feature list --product-id <id>

# Create the feature first
python cli/asyncdev.py new-feature create --product-id <id> --feature-id <fid> --name "<name>"
```

---

### "RunState not in executing phase"

**Cause**: Trying to run `run-day` before `plan-day`, or RunState is in wrong phase.

**Solution**:
```bash
# Check current state
python cli/asyncdev.py plan-day show --project <id>

# Plan a task first
python cli/asyncdev.py plan-day create --product-id <id> --feature-id <fid> --task "<task>"
```

---

### "No execution packs to run"

**Cause**: Running `run-day` without first creating an ExecutionPack.

**Solution**:
```bash
# Plan a task first
python cli/asyncdev.py plan-day create --product-id <id> --feature-id <fid> --task "<task>"

# Then run
python cli/asyncdev.py run-day --project <id> --mode external
```

---

### "Archive not found"

**Cause**: Feature hasn't been archived yet.

**Solution**:
```bash
# List available archives
python cli/asyncdev.py archive list --product <id>

# Archive the feature first
python cli/asyncdev.py archive-feature create --product-id <id> --feature-id <fid>
```

---

### "No acceptance result found"

**Cause**: Running acceptance commands before running acceptance validation.

**Solution**:
```bash
# Run acceptance validation first
python cli/asyncdev.py acceptance run --project <id>

# Then check results
python cli/asyncdev.py acceptance status --project <id>
```

---

### "Feature archived. Cannot resume."

**Cause**: Trying to resume execution on an archived feature.

**Solution**:
```bash
# Create a new feature for continued work
python cli/asyncdev.py new-feature create --product-id <id> --feature-id <fid>-v2 --name "<name v2>"
```

---

### "Config already exists"

**Cause**: Trying to configure email when config already exists.

**Solution**:
```bash
# Use --force to overwrite
python cli/asyncdev.py gmail-auth --force
# or
python cli/asyncdev.py resend-auth --force
```

---

## Phase Transition Issues

### Blocked State

**Symptom**: `run-day` fails with "RunState is blocked"

**Cause**: System is waiting for human decision or input.

**Solution**:
```bash
# Check blocking reason
python cli/asyncdev.py session-start check --project <id>

# List pending decisions
python cli/asyncdev.py decision list --project <id>

# Process decision if pending
python cli/asyncdev.py decision reply --request <request-id> --command "DECISION A"

# Or unblock if appropriate
python cli/asyncdev.py resume-next-day unblock --project <id>
```

---

### Failed Execution

**Symptom**: Execution ended with `status: failed`

**Solution**:
```bash
# Check recovery options
python cli/asyncdev.py recovery list --project <id>

# Show detailed recovery info
python cli/asyncdev.py recovery show --execution <exec-id>

# Execute recovery action
python cli/asyncdev.py recovery resume --execution <exec-id> --action <action> --execute
```

---

### Review Night Issues

**Symptom**: `review-night generate` fails or produces incomplete output

**Solution**:
```bash
# Check execution results exist
ls projects/<id>/execution-results/

# Generate review
python cli/asyncdev.py review-night generate --project <id>

# Show latest review
python cli/asyncdev.py review-night show --project <id>
```

---

## Email Configuration Issues

### "No config found"

**Cause**: Email provider not configured.

**Solution**:
```bash
# Configure Gmail
python cli/asyncdev.py gmail-auth

# Or configure Resend
python cli/asyncdev.py resend-auth
```

---

### "No webhook URL configured"

**Cause**: Webhook not set up for receiving email replies.

**Solution**:
```bash
# Check inbox for pending decisions
python cli/asyncdev.py check-inbox pending
```

---

## Workspace Health Issues

### Doctor Reports Issues

**Solution**:
```bash
# Run with repair hints
python cli/asyncdev.py doctor --project <id> --repair

# Check summary
python cli/asyncdev.py summary today --project <id>
```

---

### Missing Artifacts

**Symptom**: Required files are missing

**Solution**:
```bash
# Take a snapshot to see current state
python cli/asyncdev.py snapshot --project <id>

# Check what artifacts exist
ls projects/<id>/
ls projects/<id>/features/<fid>/
```

---

## Recovery Actions

| Action | When to Use |
|--------|-------------|
| `unblock` | Resume from blocked state after resolving blocker |
| `abort` | Stop execution and mark as aborted |
| `continue` | Resume interrupted execution |
| `retry` | Re-run failed execution from beginning |
| `reset` | Reset to planning phase |

---

## Getting Help

| Resource | Purpose |
|----------|---------|
| `python cli/asyncdev.py home status` | Overall platform health |
| `python cli/asyncdev.py doctor --project <id>` | Detailed diagnosis |
| `python cli/asyncdev.py recovery list --project <id>` | List recovery options |
| [docs/cli-reference.md](cli-reference.md) | Full command reference |
| [docs/operating-model.md](operating-model.md) | Workflow documentation |
