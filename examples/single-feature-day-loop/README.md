# Single Feature Day Loop Demo

This example demonstrates the complete async development workflow: a bounded task executed through all four day loop phases.

---

## What This Demo Shows

The day loop workflow in action:

```
plan-day → run-day → review-night → resume-next-day
```

Each phase produces structured artifacts:

| Phase | Artifact Produced |
|-------|-------------------|
| plan-day | ExecutionPack |
| run-day | ExecutionResult + output file |
| review-night | DailyReviewPack |
| resume-next-day | RunState updated |

---

## Quick Start

### Option 1: Python Script (Recommended)

```bash
cd examples/single-feature-day-loop
python demo-day-loop.py --verbose
```

### Option 2: Shell Script

```bash
cd examples/single-feature-day-loop
bash demo-day-loop.sh
```

### Option 3: Manual CLI Commands

```bash
# From repository root
python -m cli.asyncdev run-day mock-quick
python -m cli.asyncdev review-night generate
python -m cli.asyncdev resume-next-day continue-loop --decision approve
```

---

## Demo Project Structure

```
demo-product/
├─ product-brief.yaml       # Product definition
├─ feature-spec.yaml        # Feature definition
├─ execution-packs/
│  └─ exec-20260410-001.md  # Generated ExecutionPack
├─ execution-results/
│  └─ exec-20260410-001.md  # Generated ExecutionResult
├─ reviews/
│  └─ 2026-04-10-review.md  # Generated DailyReviewPack
├─ runstate.md              # Current state
├─ hello-world.txt          # Output file created
└─ logs/
```

---

## Phase-by-Phase Walkthrough

### Phase 1: plan-day

Creates bounded ExecutionPack:

```yaml
execution_id: exec-20260410-001
task_id: create-hello-world-file
goal: Create hello-world.txt with greeting message
task_scope:
  - Create hello-world.txt
  - Write greeting message
  - Verify file content
deliverables:
  - item: hello-world.txt
    path: hello-world.txt
    type: file
```

### Phase 2: run-day (Mock Mode)

MockLLMAdapter executes:

```yaml
status: success
completed_items: [hello-world.txt]
artifacts_created:
  - name: hello-world.txt
    path: hello-world.txt
verification_result:
  passed: 2
  failed: 0
```

Output file created:
```
Hello from async dev day loop!
```

### Phase 3: review-night

DailyReviewPack generated:

```yaml
date: 2026-04-10
today_goal: Execution exec-20260410-001 completed with status: success
what_was_completed:
  - Created hello-world.txt with greeting message
  - Verified file content
evidence:
  - item: hello-world.txt
    verified: true
risk_summary: No risks. Simple task completed successfully.
```

### Phase 4: resume-next-day

RunState updated:

```yaml
current_phase: completed
last_action: Day loop completed - feature done
next_recommended_action: Feature complete. Start new feature or project.
health_status: healthy
```

---

## Key Concepts Demonstrated

### Bounded Execution

ExecutionPack constrains AI:
- `task_scope`: What to do
- `constraints`: What NOT to do
- `stop_conditions`: When to stop

### Evidence-Based Progress

DailyReviewPack requires evidence:
- `verified: true` for each deliverable
- `verification_note` explaining how verified

### State-Based Resume

RunState enables next-day continuation:
- `current_phase`: Where we are
- `completed_outputs`: What done
- `next_recommended_action`: What next

---

## Customizing This Demo

To run a different demo:

1. Edit `product-brief.yaml` with your product
2. Edit `feature-spec.yaml` with your feature
3. Modify `demo-day-loop.py` to change task scope
4. Run with `--verbose` to see details

---

## Verification Checklist

After running demo, verify:

- [ ] ExecutionPack saved to execution-packs/
- [ ] ExecutionResult saved to execution-results/
- [ ] DailyReviewPack saved to reviews/
- [ ] RunState phase = completed
- [ ] Output file (hello-world.txt) exists
- [ ] All artifacts have valid YAML blocks

---

## Next Steps

After this demo:

1. Try with real feature (Feature 001/002)
2. Add blocked scenario test
3. Add decision-needed scenario
4. Test with real AI execution (requires adapter impl)